"""Role documentation generation orchestrator.

Coordinates the workflow for generating role documentation by orchestrating
builders, formatters, and renderers.
"""

import logging
from pathlib import Path

import click

from docsible.analyzers.recommendations import generate_all_recommendations
from docsible.commands.document_role.builders.role_info_builder import RoleInfoBuilder
from docsible.commands.document_role.models import RoleCommandContext
from docsible.formatters.text.dry_run import DryRunFormatter
from docsible.models.recommendation import Recommendation

logger = logging.getLogger(__name__)


class RoleOrchestrator:
    """Orchestrates role documentation generation process.

    This class coordinates the entire workflow:
    1. Validate paths
    2. Load playbook content
    3. Build role information
    4. Analyze complexity
    5. Generate diagrams
    6. Handle dry-run or generate documentation
    """

    def __init__(self, context: RoleCommandContext):
        """Initialize RoleOrchestrator.

        Args:
            context: Complete role command context with all configuration
        """
        self.context = context
        self.role_info_builder = RoleInfoBuilder()
        self.dry_run_formatter = DryRunFormatter()

    def execute(self) -> None:
        """Execute the documentation generation workflow.

        This is the main entry point that coordinates all steps.
        Designed to eventually replace the main function logic in core.py.
        """
        # Building role data initializes .docsible unless explicitly disabled.
        if self.context.processing.dry_run:
            self.context.processing.no_docsible = True

        # Step 1: Validate paths
        role_path = self._validate_paths()

        # Step 2: Load playbook content
        playbook_content = self._load_playbook()

        # Step 3: Build role info
        role_info = self._build_role_info(role_path, playbook_content)

        # Step 4: Analyze complexity
        analysis_report = self._analyze_complexity(role_info)

        if (
            self.context.analysis.recommendations_only
            and self.context.analysis.complexity_report
            and self.context.analysis.output_format != "json"
        ):
            from docsible.utils.console import display_complexity_report

            display_complexity_report(analysis_report, role_name=role_info.get("name"))

        # Step 5: Handle analyze-only mode
        if self.context.analysis.analyze_only:
            self._display_analysis_and_exit(analysis_report, role_info)
            return

        # Step 6: Generate diagrams
        diagrams = self._generate_diagrams(role_info, analysis_report, playbook_content)

        # Step 7: Generate dependency matrix
        dependency_data = self._generate_dependencies(role_info, analysis_report)

        # Validate intent and validating dry runs must render before recommendation gates can exit.
        if self.context.validation.validate_only or (
            self.context.processing.dry_run and self.context.validation.validate_markdown
        ):
            self._validate_documentation(role_info, analysis_report, diagrams, dependency_data)

        # Step 7.5: Generate recommendations (use validated role_path from step 1)
        recommendations = generate_all_recommendations(role_path)

        if self.context.analysis.apply_suppressions:
            from docsible.suppression.engine import apply_suppressions

            recommendations, suppressed = apply_suppressions(
                recommendations,
                base_path=role_path,
            )
            if suppressed and self.context.analysis.output_format != "json":
                click.echo(
                    f"  ({len(suppressed)} recommendation(s) suppressed"
                    f" — see 'docsible suppress list')"
                )
        else:
            suppressed = []

        if recommendations or self.context.analysis.output_format == "json":
            self._display_recommendations(recommendations)

        # Recommendation strictness applies to documentation generation only.
        # Validate intent reserves strictness for markdown validation below.
        if (
            self.context.validation.strict_validation
            and not self.context.validation.validate_markdown
            and recommendations
        ):
            from docsible.models.severity import Severity

            blocking = [
                r for r in recommendations if r.severity in (Severity.WARNING, Severity.CRITICAL)
            ]
            if blocking:
                click.echo(
                    f"\n✗ Strict validation failed: {len(blocking)} WARNING/CRITICAL finding(s) found.",
                    err=True,
                )
                raise SystemExit(1)

        # CI exit code gate — checked against full list (before display cap)
        fail_on = self.context.analysis.fail_on
        if fail_on != "none" and recommendations:
            _severity_rank = {"none": 0, "info": 1, "warning": 2, "critical": 3}
            threshold = _severity_rank[fail_on]
            failing = [
                r
                for r in recommendations
                if _severity_rank.get(r.severity.value.lower(), 0) >= threshold
            ]
            if failing:
                click.echo(
                    f"\n✗ Exiting with code 1: {len(failing)} finding(s) at '{fail_on}' level or above.",
                    err=True,
                )
                raise SystemExit(1)

        # Step 7.6: Handle recommendations-only mode
        if self.context.analysis.recommendations_only:
            # Only show recommendations, don't generate documentation
            return

        # Step 8: Handle dry-run mode
        if self.context.processing.dry_run:
            self._display_dry_run(role_info, role_path, analysis_report, diagrams, dependency_data)
            return

        # Step 9: Render documentation
        self._render_documentation(role_info, role_path, analysis_report, diagrams, dependency_data)

    def _validate_paths(self) -> Path:
        """Validate and return role path.

        Returns:
            Validated role path

        Raises:
            click.ClickException: If role path is invalid
        """
        from docsible.commands.document_role.helpers import validate_role_path

        if self.context.paths.role_path is None:
            raise click.ClickException("Role path is required")

        # Convert Path to str for validate_role_path
        role_path_str = str(self.context.paths.role_path)
        return validate_role_path(role_path_str)

    def _load_playbook(self) -> str | None:
        """Load playbook content if provided.

        Returns:
            Playbook content or None
        """
        from docsible.commands.document_role.helpers import load_playbook_content

        # Convert Path to str for load_playbook_content
        playbook_path = self.context.paths.playbook
        if playbook_path is None:
            return None
        return load_playbook_content(str(playbook_path))

    def _build_role_info(self, role_path: Path, playbook_content: str | None) -> dict:
        """Build comprehensive role information.

        Args:
            role_path: Path to role directory
            playbook_content: Optional playbook YAML content

        Returns:
            Role information dictionary
        """
        processing = self.context.processing.model_copy(
            update={"no_docsible": True}
        ) if self.context.processing.dry_run else self.context.processing
        return self.role_info_builder.build(
            role_path=role_path,
            playbook_content=playbook_content,
            processing=processing,
            repository=self.context.repository,
        )

    def _analyze_complexity(self, role_info: dict):
        """Analyze role complexity.

        Reuses cached analysis from smart defaults if available to avoid
        duplicate analysis.

        Args:
            role_info: Role information dictionary

        Returns:
            Complexity analysis report
        """
        # Check if we have a cached report from smart defaults
        if self.context.analysis.cached_complexity_report:
            logger.debug("Reusing complexity analysis from smart defaults (avoiding duplicate)")
            return self.context.analysis.cached_complexity_report

        # No cached report available, perform fresh analysis
        from docsible.analyzers import analyze_role_complexity

        logger.debug("Performing fresh complexity analysis")
        return analyze_role_complexity(
            role_info,
            include_patterns=self.context.analysis.simplification_report,
            min_confidence=0.7,
        )

    def _display_analysis_and_exit(self, analysis_report, role_info: dict) -> None:
        """Display analysis report and exit.

        Args:
            analysis_report: Complexity analysis report
            role_info: Role information dictionary
        """
        from docsible.commands.document_role.helpers import handle_analyze_only_mode
        from docsible.utils.console import display_complexity_report

        if self.context.analysis.complexity_report:
            display_complexity_report(analysis_report, role_name=role_info.get("name"))

        handle_analyze_only_mode(role_info, role_info.get("name", "unknown"))

    def _generate_diagrams(
        self, role_info: dict, analysis_report, playbook_content: str | None
    ) -> dict:
        """Generate all Mermaid diagrams.

        Args:
            role_info: Role information dictionary
            analysis_report: Complexity analysis report
            playbook_content: Optional playbook content

        Returns:
            Dictionary of generated diagrams
        """
        from docsible.commands.document_role.helpers import (
            generate_integration_and_architecture_diagrams,
            generate_mermaid_diagrams,
        )

        # Generate task diagrams
        diagrams = generate_mermaid_diagrams(
            generate_graph=self.context.diagrams.generate_graph,
            role_info=role_info,
            playbook_content=playbook_content,
            analysis_report=analysis_report,
            minimal=self.context.content.minimal,
            simplify_diagrams=self.context.content.simplify_diagrams,
        )

        # Add generate_graph flag for formatter
        diagrams["generate_graph"] = self.context.diagrams.generate_graph

        # Generate integration and architecture diagrams
        integration_boundary, architecture = generate_integration_and_architecture_diagrams(
            generate_graph=self.context.diagrams.generate_graph,
            role_info=role_info,
            analysis_report=analysis_report,
        )

        diagrams["integration_boundary_diagram"] = integration_boundary
        diagrams["architecture_diagram"] = architecture

        return diagrams

    def _generate_dependencies(self, role_info: dict, analysis_report) -> dict:
        """Generate dependency matrix and summary.

        Args:
            role_info: Role information dictionary
            analysis_report: Complexity analysis report

        Returns:
            Dictionary with dependency_matrix, dependency_summary, show_matrix
        """
        from docsible.commands.document_role.helpers import generate_dependency_matrix

        dependency_matrix, dependency_summary, show_dependency_matrix = generate_dependency_matrix(
            show_dependencies=self.context.diagrams.show_dependencies,
            role_info=role_info,
            analysis_report=analysis_report,
        )

        return {
            "dependency_matrix": dependency_matrix,
            "dependency_summary": dependency_summary,
            "show_matrix": show_dependency_matrix,
        }

    def _display_dry_run(
        self,
        role_info: dict,
        role_path: Path,
        analysis_report,
        diagrams: dict,
        dependency_data: dict,
    ) -> None:
        """Display dry-run summary.

        Args:
            role_info: Role information dictionary
            role_path: Path to role directory
            analysis_report: Complexity analysis report
            diagrams: Generated diagrams dictionary
            dependency_data: Dependency matrix data
        """
        flags = {
            "generate_graph": self.context.diagrams.generate_graph,
            "hybrid": self.context.template.hybrid,
            "no_backup": self.context.processing.no_backup,
            "no_docsible": self.context.processing.no_docsible,
            "minimal": self.context.content.minimal,
        }

        summary = self.dry_run_formatter.format_summary(
            role_info=role_info,
            role_path=role_path,
            output=self.context.paths.output,
            analysis_report=analysis_report,
            diagrams=diagrams,
            dependency_matrix=dependency_data["dependency_matrix"],
            flags=flags,
        )

        click.echo(summary)

    def _display_recommendations(self, recommendations: list[Recommendation]) -> None:
        """Display recommendations to user"""
        all_recs = recommendations

        # JSON format: always show full list, no cap
        if self.context.analysis.output_format == "json":
            from docsible.formatters.text.json_formatter import JsonRecommendationFormatter

            role_name = ""
            if self.context.paths.role_path is not None:
                role_name = self.context.paths.role_path.name

            json_output = JsonRecommendationFormatter().format(
                all_recs,
                role_name=role_name,
                truncated=False,
                total_count=len(all_recs),
            )
            click.echo(json_output)
            return

        # Text format: apply filtering and capping unless --advanced-patterns
        from docsible.formatters.text.recommendation import RecommendationFormatter
        from docsible.models.severity import Severity

        if not self.context.analysis.advanced_patterns:
            # Filter out INFO unless show_info is explicitly set
            if not self.context.analysis.show_info:
                display_recs = [r for r in all_recs if r.severity != Severity.INFO]
            else:
                display_recs = list(all_recs)

            # Cap to max_recommendations
            max_recs = self.context.analysis.max_recommendations
            if max_recs is not None and len(display_recs) > max_recs:
                display_recs = display_recs[:max_recs]
                hidden_count = len(all_recs) - len(display_recs)
                click.echo(
                    f"  ({hidden_count} more findings hidden"
                    " — run with --advanced-patterns to see all)"
                )
        else:
            display_recs = list(all_recs)

        formatter = RecommendationFormatter()
        output = formatter.format_recommendations(
            recommendations=display_recs,
            show_info=self.context.analysis.show_info,
        )

        click.echo(output)

    def _validate_documentation(
        self,
        role_info: dict,
        analysis_report,
        diagrams: dict,
        dependency_data: dict,
    ) -> None:
        """Render generated markdown in memory and validate it without writing files."""
        from docsible.renderers.readme_renderer import ReadmeRenderer

        template_type, custom_template, render_options = self._render_options(
            role_info, analysis_report, diagrams, dependency_data
        )
        template = ReadmeRenderer().template_processor.get_role_template(
            template_type=template_type,
            custom_path=custom_template,
        )
        markdown = template.render(**render_options)
        renderer = ReadmeRenderer(
            validate=True,
            auto_fix=self.context.validation.auto_fix,
            strict_validation=self.context.validation.strict_validation,
        )
        renderer.markdown_processor.process(renderer.tag_processor.add_tags(markdown))

    def _render_options(
        self, role_info: dict, analysis_report, diagrams: dict, dependency_data: dict
    ) -> tuple[str, str | None, dict]:
        """Build the template inputs shared by normal rendering and validation."""
        template_type = "hybrid" if self.context.template.hybrid else "standard_modular"
        custom_template = self.context.template.md_role_template
        include_complexity = self.context.analysis.include_complexity or self.context.template.hybrid
        return template_type, str(custom_template) if custom_template else None, {
            "role": role_info,
            "mermaid_code_per_file": diagrams.get("mermaid_code_per_file", {}),
            "sequence_diagram_high_level": diagrams.get("sequence_diagram_high_level"),
            "sequence_diagram_detailed": diagrams.get("sequence_diagram_detailed"),
            "state_diagram": diagrams.get("state_diagram"),
            "integration_boundary_diagram": diagrams.get("integration_boundary_diagram"),
            "architecture_diagram": diagrams.get("architecture_diagram"),
            "complexity_report": analysis_report,
            "include_complexity": include_complexity,
            "dependency_matrix": dependency_data["dependency_matrix"],
            "dependency_summary": dependency_data["dependency_summary"],
            "show_dependency_matrix": dependency_data["show_matrix"],
            "no_vars": self.context.content.no_vars,
            "no_tasks": self.context.content.no_tasks,
            "no_diagrams": self.context.content.no_diagrams,
            "simplify_diagrams": self.context.content.simplify_diagrams,
            "no_examples": self.context.content.no_examples,
            "no_metadata": self.context.content.no_metadata,
            "no_handlers": self.context.content.no_handlers,
        }

    def _render_documentation(
        self,
        role_info: dict,
        role_path: Path,
        analysis_report,
        diagrams: dict,
        dependency_data: dict,
    ) -> None:
        """Render final documentation.

        Args:
            role_info: Role information dictionary
            role_path: Path to role directory
            analysis_report: Complexity analysis report
            diagrams: Generated diagrams dictionary
            dependency_data: Dependency matrix data
        """
        from docsible.renderers.readme_renderer import ReadmeRenderer

        template_type, custom_template, render_options = self._render_options(
            role_info, analysis_report, diagrams, dependency_data
        )

        # Create renderer
        renderer = ReadmeRenderer(
            backup=not self.context.processing.no_backup,
            validate=self.context.validation.validate_markdown,
            auto_fix=self.context.validation.auto_fix,
            strict_validation=self.context.validation.strict_validation,
        )

        # Render documentation
        readme_path = role_path / self.context.paths.output

        renderer.render_role(
            role_info=role_info,
            output_path=readme_path,
            template_type=template_type,
            custom_template_path=custom_template,
            append=self.context.processing.append,
            **{name: value for name, value in render_options.items() if name != "role"},
        )

        # Display positive or neutral success message
        if self.context.analysis.positive_framing:
            from docsible.formatters.text.positive import PositiveFormatter

            formatter = PositiveFormatter()
            success_msg = formatter.format_success(
                output_file=readme_path,
                complexity=analysis_report,
                recommendations=[],  # recommendations already shown separately above
            )
            click.echo("\n" + success_msg)
        else:
            click.echo(f"✓ Role documentation generated: {readme_path}")
