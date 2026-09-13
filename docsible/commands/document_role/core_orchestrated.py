"""Implementation of doc_the_role using RoleOrchestrator.

This module is the single implementation of doc_the_role, using the
orchestrator pattern via RoleOrchestrator.
"""

import logging
import os
import sys
from pathlib import Path
from typing import Any

import click

from docsible.commands.document_role.helpers import apply_minimal_flag
from docsible.commands.document_role.models import (
    AnalysisConfig,
    ContentFlags,
    DiagramConfig,
    PathConfig,
    ProcessingConfig,
    RepositoryConfig,
    RoleCommandContext,
    TemplateConfig,
    ValidationConfig,
)
from docsible.commands.document_role.orchestrators import RoleOrchestrator
from docsible.commands.role_info_loader import RoleInfoLoader
from docsible.exceptions import CollectionNotFoundError

logger = logging.getLogger(__name__)


def extract_playbook_role_dependencies(
    playbook_content: str | None, current_role_name: str
) -> list[str]:
    """Extract role names from playbook that differ from the current role name.

    Searches for roles in:
    - roles: section
    - include_role/import_role tasks in pre_tasks, tasks, post_tasks

    Args:
        playbook_content: YAML content of the playbook as string
        current_role_name: Name of the current role being documented

    Returns:
        List of role names (excluding current role)

    Example:
        >>> content = '''
        ... - hosts: all
        ...   roles:
        ...     - common
        ...     - webserver
        ... '''
        >>> extract_playbook_role_dependencies(content, 'webserver')
        ['common']
    """
    return RoleInfoLoader()._playbook_dependencies(playbook_content, current_role_name)


def build_role_info(
    role_path: Path,
    playbook_content: str | None,
    generate_graph: bool,
    no_docsible: bool,
    comments: bool,
    task_line: bool,
    belongs_to_collection: dict | None,
    repository_url: str | None,
    repo_type: str | None,
    repo_branch: str | None,
) -> dict:
    """Build comprehensive role information dictionary.

    Args:
        role_path: Path to role directory
        playbook_content: Optional playbook YAML content
        generate_graph: Whether to generate Mermaid graphs
        no_docsible: Skip .docsible file handling
        comments: Extract comments from task files
        task_line: Extract line numbers from tasks
        belongs_to_collection: Collection info if role is part of collection
        repository_url: Repository URL (or 'detect' for auto-detection)
        repo_type: Repository type (github, gitlab, gitea)
        repo_branch: Repository branch name

    Returns:
        Dictionary with complete role information
    """
    return RoleInfoLoader().load(
        role_path,
        playbook_content=playbook_content,
        generate_graph=generate_graph,
        comments=comments,
        task_line=task_line,
        belongs_to_collection=belongs_to_collection,
        repository_url=repository_url,
        repo_type=repo_type,
        repo_branch=repo_branch,
        read_docsible=not no_docsible,
    )

def _display_dry_run_summary(
    role_info: dict,
    role_path: Path,
    output: str,
    analysis_report,
    mermaid_code_per_file: dict,
    sequence_diagram_high_level: str | None,
    sequence_diagram_detailed: str | None,
    state_diagram: str | None,
    integration_boundary_diagram: str | None,
    architecture_diagram: str | None,
    dependency_matrix: str | None,
    no_backup: bool,
    no_docsible: bool,
    generate_graph: bool,
    hybrid: bool,
    minimal: bool,
) -> None:
    """Display dry-run summary without writing files.

    Args:
        role_info: Role information dictionary
        role_path: Path to role directory
        output: Output filename
        analysis_report: Complexity analysis report
        mermaid_code_per_file: Generated task flowcharts
        sequence_diagram_high_level: High-level sequence diagram
        sequence_diagram_detailed: Detailed sequence diagram
        state_diagram: State transition diagram
        integration_boundary_diagram: Integration boundary diagram
        architecture_diagram: Component architecture diagram
        dependency_matrix: Dependency matrix
        no_backup: Whether backup is disabled
        no_docsible: Whether .docsible file is disabled
        generate_graph: Whether diagrams are generated
        hybrid: Whether hybrid template is used
        minimal: Whether minimal mode is enabled
    """
    click.echo("\n" + "=" * 70)
    click.echo("🔍 DRY RUN MODE - No files will be modified")
    click.echo("=" * 70)

    # Role information
    click.echo("\n📁 Analysis Complete:")
    click.echo(f"   Role: {role_info.get('name', 'unknown')}")
    click.echo(f"   Path: {role_path}")

    # Complexity analysis
    click.echo("\n📊 Complexity Analysis:")
    click.echo(f"   Category: {analysis_report.category.value.upper()}")
    click.echo(f"   Total Tasks: {analysis_report.metrics.total_tasks}")
    click.echo(f"   Task Files: {analysis_report.metrics.task_files}")

    # Variables
    defaults_count = sum(len(df.get("data", {})) for df in role_info.get("defaults", []))
    vars_count = sum(len(vf.get("data", {})) for vf in role_info.get("vars", []))
    click.echo(
        f"   Variables: {defaults_count + vars_count} ({defaults_count} defaults, {vars_count} vars)"
    )

    # Handlers
    handlers_count = len(role_info.get("handlers", []))
    if handlers_count > 0:
        click.echo(f"   Handlers: {handlers_count}")

    # What would be generated
    click.echo("\n📈 Would Generate:")

    if generate_graph:
        if mermaid_code_per_file:
            click.echo(f"   ✓ Task flowcharts ({len(mermaid_code_per_file)} files)")
        if sequence_diagram_high_level:
            click.echo("   ✓ Sequence diagram (high-level)")
        if sequence_diagram_detailed:
            click.echo("   ✓ Sequence diagram (detailed)")
        if state_diagram:
            click.echo("   ✓ State transition diagram")
        if integration_boundary_diagram:
            integration_count = len(analysis_report.integration_points)
            click.echo(f"   ✓ Integration boundary diagram ({integration_count} external systems)")
        if architecture_diagram:
            click.echo("   ✓ Component architecture diagram")

    if dependency_matrix:
        click.echo("   ✓ Dependency matrix")

    if not generate_graph and not dependency_matrix:
        click.echo("   (No diagrams or matrices - use --graph for visualizations)")

    # Files that would be created/modified
    click.echo("\n📝 Files That Would Be Created/Modified:")
    readme_path = role_path / output

    if readme_path.exists():
        # Estimate new content size
        click.echo(f"   → {output} (existing file would be updated)")
        if not no_backup:
            from datetime import datetime

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{output.rsplit('.', 1)[0]}_backup_{timestamp}.{output.rsplit('.', 1)[1] if '.' in output else 'md'}"
            click.echo(f"   → {backup_name} (backup of existing)")
    else:
        click.echo(f"   → {output} (new file)")

    if not no_docsible:
        docsible_path = role_path / ".docsible"
        if docsible_path.exists():
            click.echo("   → .docsible (metadata file - would be updated)")
        else:
            click.echo("   → .docsible (metadata file - new)")

    # Active flags
    click.echo("\n⚙️  Active Flags:")
    click.echo(f"   --graph: {'✓' if generate_graph else '✗'}")
    click.echo(f"   --hybrid: {'✓' if hybrid else '✗'}")
    click.echo(f"   --no-backup: {'✓' if no_backup else '✗'}")
    click.echo(f"   --minimal: {'✓' if minimal else '✗'}")

    click.echo("\n💡 To generate documentation, run without --dry-run")
    click.echo("=" * 70 + "\n")


def _optional_path(value: str | None) -> Path | None:
    return Path(value) if value else None


def _ensure_str(value: Path | str | None, default: str = "") -> str:
    """Convert Path | str | None to str, with default for None.

    Args:
        value: The value to convert (Path, str, or None)
        default: Default value to return if value is None

    Returns:
        String representation of value, or default if value is None
    """
    if value is None:
        return default
    return str(value)


def doc_the_role(**kwargs: Any) -> None:
    """Generate documentation for an Ansible role using orchestrator pattern.

    Args:
        **kwargs: All CLI parameters passed as keyword arguments matching
                  the Click command signature.

    All parameters are passed via **kwargs to match the Click command signature.
    """
    # Import here to avoid circular imports
    from docsible.commands.document_collection import document_collection_roles
    from docsible.commands.document_role.smart_defaults_integration import (
        apply_smart_defaults,
    )

    # In JSON mode, redirect logging to stderr so stdout carries only valid JSON
    if kwargs.get("output_format") == "json":
        for handler in logging.root.handlers:
            if isinstance(handler, logging.StreamHandler) and handler.stream is sys.stdout:
                handler.stream = sys.stderr

    # SMART DEFAULTS INTEGRATION
    # Apply smart defaults based on role complexity (if enabled)
    enable_smart_defaults = os.getenv("DOCSIBLE_ENABLE_SMART_DEFAULTS", "true").lower() == "true"

    role_path = kwargs.get("role_path")
    collection_path = kwargs.get("collection_path")

    # Smart-default analysis uses legacy role loading; dry runs must be strictly read-only.
    if enable_smart_defaults and role_path and not collection_path and not kwargs.get("dry_run", False):
        try:
            from docsible.commands.document_role.helpers import validate_role_path

            # Validate role path first to ensure it exists
            temp_validated_path = validate_role_path(role_path)

            explicit_options = kwargs.get("_explicit_options", {})
            user_overrides = {
                name: explicit_options[name]
                for name in ("generate_graph", "minimal", "show_dependencies")
                if name in explicit_options
            }
            if kwargs.get("_minimal_explicit", False):
                user_overrides["minimal"] = kwargs.get("minimal", False)

            # Apply smart defaults for non-overridden options
            smart_graph, smart_minimal, smart_deps, complexity_report = apply_smart_defaults(
                temp_validated_path, user_overrides
            )

            # Store complexity report for reuse by orchestrator (avoid duplicate analysis)
            if complexity_report:
                kwargs["_complexity_report"] = complexity_report
                logger.debug("Cached complexity analysis for reuse by orchestrator")

            # Use smart defaults only if user didn't override
            if "generate_graph" not in user_overrides:
                kwargs["generate_graph"] = smart_graph
                if smart_graph:
                    logger.info("Smart default: Enabling graph generation for this role")

            if smart_minimal and "minimal" not in user_overrides:
                logger.info("Smart default: Minimal documentation is suggested for this role")

            if "show_dependencies" not in user_overrides:
                kwargs["show_dependencies"] = smart_deps
                if smart_deps:
                    logger.info("Smart default: Including dependency information")

        except Exception as e:
            logger.warning(f"Smart defaults failed: {e}")
            logger.warning("Continuing with manual configuration")
            # Continue with original values

    # Apply minimal settings after smart defaults so derived flags use the final value.
    minimal = kwargs.get("minimal", False)
    if minimal:
        (
            kwargs["no_vars"],
            kwargs["no_tasks"],
            kwargs["no_diagrams"],
            kwargs["no_examples"],
            kwargs["no_metadata"],
            kwargs["no_handlers"],
            kwargs["simplify_diagrams"],
        ) = apply_minimal_flag(
            minimal,
            kwargs.get("no_vars", False),
            kwargs.get("no_tasks", False),
            kwargs.get("no_diagrams", False),
            kwargs.get("no_examples", False),
            kwargs.get("no_metadata", False),
            kwargs.get("no_handlers", False),
            kwargs.get("simplify_diagrams", False),
        )

    # Build context from parameters
    context = RoleCommandContext(
        paths=PathConfig(
            role_path=_optional_path(kwargs.get("role_path")),
            collection_path=_optional_path(kwargs.get("collection_path")),
            playbook=_optional_path(kwargs.get("playbook")),
            output=kwargs.get("output", "README.md"),
        ),
        template=TemplateConfig(
            hybrid=kwargs.get("hybrid", False),
            md_role_template=_optional_path(kwargs.get("md_role_template")),
            md_collection_template=_optional_path(kwargs.get("md_collection_template")),
        ),
        content=ContentFlags(
            no_vars=kwargs.get("no_vars", False),
            no_tasks=kwargs.get("no_tasks", False),
            no_diagrams=kwargs.get("no_diagrams", False),
            simplify_diagrams=kwargs.get("simplify_diagrams", False),
            no_examples=kwargs.get("no_examples", False),
            no_metadata=kwargs.get("no_metadata", False),
            no_handlers=kwargs.get("no_handlers", False),
            minimal=minimal,
        ),
        diagrams=DiagramConfig(
            generate_graph=kwargs.get("generate_graph", False),
            show_dependencies=kwargs.get("show_dependencies", False),
        ),
        analysis=AnalysisConfig(
            complexity_report=kwargs.get("complexity_report", False),
            include_complexity=kwargs.get("include_complexity", False),
            simplification_report=kwargs.get("simplification_report", False),
            analyze_only=kwargs.get("analyze_only", False),
            show_info=kwargs.get("show_info", False),
            recommendations_only=kwargs.get("recommendations_only", False),
            positive_framing=kwargs.get("positive_framing", True),
            fail_on=kwargs.get("fail_on", "none"),
            essential_only=kwargs.get("essential_only", True),
            max_recommendations=kwargs.get("max_recommendations", 5),
            advanced_patterns=kwargs.get("advanced_patterns", False),
            output_format=kwargs.get("output_format", "text"),
            apply_suppressions=not kwargs.get("no_suppress", False),
            cached_complexity_report=kwargs.get("_complexity_report"),  # From smart defaults
        ),
        processing=ProcessingConfig(
            comments=kwargs.get("comments", False),
            task_line=kwargs.get("task_line", False),
            no_backup=kwargs.get("no_backup", False),
            no_docsible=kwargs.get("no_docsible", False) or kwargs.get("dry_run", False),
            dry_run=kwargs.get("dry_run", False),
            append=kwargs.get("append", False),
        ),
        validation=ValidationConfig(
            validate_markdown=kwargs.get("validate_markdown", False),
            auto_fix=kwargs.get("auto_fix", False),
            strict_validation=kwargs.get("strict_validation", False),
            validate_only=kwargs.get("validate_only", False),
        ),
        repository=RepositoryConfig(
            repository_url=kwargs.get("repository_url"),
            repo_type=kwargs.get("repo_type"),
            repo_branch=kwargs.get("repo_branch"),
        ),
    )

    # Handle collection vs role
    if context.paths.collection_path:
        try:
            # Keep existing collection handling (not yet modularized)
            document_collection_roles(
                collection_path=str(context.paths.collection_path),
                playbook=_ensure_str(context.paths.playbook),
                graph=context.diagrams.generate_graph,
                no_backup=context.processing.no_backup,
                no_docsible=context.processing.no_docsible,
                comments=context.processing.comments,
                task_line=context.processing.task_line,
                md_collection_template=_ensure_str(context.template.md_collection_template),
                md_role_template=_ensure_str(context.template.md_role_template),
                hybrid=context.template.hybrid,
                no_vars=context.content.no_vars,
                no_tasks=context.content.no_tasks,
                no_diagrams=context.content.no_diagrams,
                simplify_diagrams=context.content.simplify_diagrams,
                no_examples=context.content.no_examples,
                no_metadata=context.content.no_metadata,
                no_handlers=context.content.no_handlers,
                minimal=context.content.minimal,
                append=context.processing.append,
                output=context.paths.output,
                repository_url=context.repository.repository_url or "",
                repo_type=context.repository.repo_type or "",
                repo_branch=context.repository.repo_branch or "",
                dry_run=context.processing.dry_run,
            )
        except CollectionNotFoundError as e:
            raise click.ClickException(str(e)) from e
        return

    # Use orchestrator for role documentation
    orchestrator = RoleOrchestrator(context)

    try:
        orchestrator.execute()
    except CollectionNotFoundError as e:
        raise click.ClickException(str(e)) from e
    except Exception as e:
        from docsible.formatters.help.contextual import ContextualHelpProvider

        help_msg = ContextualHelpProvider.format_error_with_help(e)
        logger.error(help_msg)
        raise
