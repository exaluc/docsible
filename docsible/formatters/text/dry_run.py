"""Formatter for dry-run output display.

Extracts and formats the dry-run summary logic from core.py.
"""

from datetime import datetime
from pathlib import Path


class DryRunFormatter:
    """Formats dry-run output for display."""

    def __init__(self, width: int = 70):
        """Initialize DryRunFormatter.

        Args:
            width: Width of separator lines
        """
        self.width = width

    def format_summary(
        self,
        role_info: dict,
        role_path: Path,
        output: str,
        analysis_report,
        diagrams: dict,
        dependency_matrix: str | None,
        flags: dict,
    ) -> str:
        """Generate formatted dry-run summary.

        Args:
            role_info: Role information dictionary
            role_path: Path to role directory
            output: Output filename
            analysis_report: Complexity analysis report
            diagrams: Dictionary of all generated diagrams
            dependency_matrix: Dependency matrix
            flags: Active configuration flags

        Returns:
            Formatted summary string
        """
        sections = [
            self._format_header(),
            self._format_role_info(role_info, role_path),
            self._format_complexity(analysis_report, role_info),
            self._format_diagrams(diagrams, dependency_matrix, analysis_report),
            self._format_files(role_path, output, flags),
            self._format_flags(flags),
            self._format_footer(),
        ]
        return "\n".join(sections)

    def _format_header(self) -> str:
        """Format header section."""
        return "\n".join(
            [
                "",
                "=" * self.width,
                "🔍 DRY RUN MODE - No files will be modified",
                "=" * self.width,
            ]
        )

    def _format_role_info(self, role_info: dict, role_path: Path) -> str:
        """Format role information section.

        Args:
            role_info: Role information dictionary
            role_path: Path to role directory

        Returns:
            Formatted role info section
        """
        return "\n".join(
            [
                "",
                "📁 Analysis Complete:",
                f"   Role: {role_info.get('name', 'unknown')}",
                f"   Path: {role_path}",
            ]
        )

    def _format_complexity(self, analysis_report, role_info: dict) -> str:
        """Format complexity analysis section.

        Args:
            analysis_report: Complexity analysis report
            role_info: Role information dictionary

        Returns:
            Formatted complexity section
        """
        lines = [
            "",
            "📊 Complexity Analysis:",
            f"   Category: {analysis_report.category.value.upper()}",
            f"   Total Tasks: {analysis_report.metrics.total_tasks}",
            f"   Task Files: {analysis_report.metrics.task_files}",
        ]

        # Variables count
        defaults_count = sum(len(df.get("data", {})) for df in role_info.get("defaults", []))
        vars_count = sum(len(vf.get("data", {})) for vf in role_info.get("vars", []))
        lines.append(
            f"   Variables: {defaults_count + vars_count} ({defaults_count} defaults, {vars_count} vars)"
        )

        # Handlers count
        handlers_count = len(role_info.get("handlers", []))
        if handlers_count > 0:
            lines.append(f"   Handlers: {handlers_count}")

        metrics = analysis_report.metrics
        lines.append(f"   Collections: {metrics.collection_dependencies}")
        lines.append(f"   Conditional decision points: {metrics.conditional_decision_points}")
        lines.append(
            "   Execution graph: "
            f"{metrics.static_reachable_task_files} static files, "
            f"{metrics.dynamically_reachable_task_files} dynamic-only, "
            f"{metrics.dynamic_boundaries} dynamic boundaries, "
            f"{metrics.unreachable_task_files} unreachable"
        )

        return "\n".join(lines)

    def _format_diagrams(
        self, diagrams: dict, dependency_matrix: str | None, analysis_report
    ) -> str:
        """Format diagrams section.

        Args:
            diagrams: Dictionary of all generated diagrams
            dependency_matrix: Dependency matrix
            analysis_report: Complexity analysis report

        Returns:
            Formatted diagrams section
        """
        lines = ["", "📈 Would Generate:"]

        generate_graph = diagrams.get("generate_graph", False)

        if generate_graph:
            # Task flowcharts
            mermaid_code_per_file = diagrams.get("mermaid_code_per_file", {})
            if mermaid_code_per_file:
                lines.append(f"   ✓ Task flowcharts ({len(mermaid_code_per_file)} files)")

            # Sequence diagrams
            if diagrams.get("sequence_diagram_high_level"):
                lines.append("   ✓ Sequence diagram (high-level)")
            if diagrams.get("sequence_diagram_detailed"):
                lines.append("   ✓ Sequence diagram (detailed)")

            # State diagram
            if diagrams.get("state_diagram"):
                lines.append("   ✓ State transition diagram")

            # Integration boundary diagram
            if diagrams.get("integration_boundary_diagram"):
                integration_count = len(analysis_report.integration_points)
                lines.append(
                    f"   ✓ Integration boundary diagram ({integration_count} external systems)"
                )

            # Architecture diagram
            if diagrams.get("architecture_diagram"):
                lines.append("   ✓ Component architecture diagram")

        # Dependency matrix
        if dependency_matrix:
            lines.append("   ✓ Dependency matrix")

        # No diagrams message
        if not generate_graph and not dependency_matrix:
            lines.append("   (No diagrams or matrices - use --graph for visualizations)")

        return "\n".join(lines)

    def _format_files(self, role_path: Path, output: str, flags: dict) -> str:
        """Format files section.

        Args:
            role_path: Path to role directory
            output: Output filename
            flags: Active configuration flags

        Returns:
            Formatted files section
        """
        lines = ["", "📝 Files That Would Be Created/Modified:"]
        readme_path = role_path / output

        if readme_path.exists():
            lines.append(f"   → {output} (existing file would be updated)")
            if not flags.get("no_backup", False):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_name = (
                    f"{output.rsplit('.', 1)[0]}_backup_{timestamp}."
                    f"{output.rsplit('.', 1)[1] if '.' in output else 'md'}"
                )
                lines.append(f"   → {backup_name} (backup of existing)")
        else:
            lines.append(f"   → {output} (new file)")

        if not flags.get("no_docsible", False):
            docsible_path = role_path / ".docsible"
            if docsible_path.exists():
                lines.append("   → .docsible (metadata file - would be updated)")
            else:
                lines.append("   → .docsible (metadata file - new)")

        return "\n".join(lines)

    def _format_flags(self, flags: dict) -> str:
        """Format active flags section.

        Args:
            flags: Active configuration flags

        Returns:
            Formatted flags section
        """
        return "\n".join(
            [
                "",
                "⚙️  Active Flags:",
                f"   --graph: {'✓' if flags.get('generate_graph', False) else '✗'}",
                f"   --hybrid: {'✓' if flags.get('hybrid', False) else '✗'}",
                f"   --no-backup: {'✓' if flags.get('no_backup', False) else '✗'}",
                f"   --minimal: {'✓' if flags.get('minimal', False) else '✗'}",
            ]
        )

    def _format_footer(self) -> str:
        """Format footer section."""
        return "\n".join(
            [
                "",
                "💡 To generate documentation, run without --dry-run",
                "=" * self.width + "\n",
            ]
        )
