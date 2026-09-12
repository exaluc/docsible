"""Helper functions for document_role command to improve readability and maintainability."""

import logging
from pathlib import Path
from typing import Any

import click
import yaml

from docsible.diagrams.mermaid import (
    generate_mermaid_role_tasks_per_file,
)
from docsible.diagrams.sequence import (
    generate_mermaid_sequence_playbook_high_level,
    generate_mermaid_sequence_role_detailed,
)

logger = logging.getLogger(__name__)


def apply_minimal_flag(
    minimal: bool,
    no_vars: bool,
    no_tasks: bool,
    no_diagrams: bool,
    no_examples: bool,
    no_metadata: bool,
    no_handlers: bool,
    simplify_diagrams: bool,
) -> tuple[bool, bool, bool, bool, bool, bool, bool]:
    """Apply minimal flag settings to enable all --no-* flags.

    Args:
        minimal: Whether minimal mode is enabled
        no_vars: Current no_vars setting
        no_tasks: Current no_tasks setting
        no_diagrams: Current no_diagrams setting
        no_examples: Current no_examples setting
        no_metadata: Current no_metadata setting
        no_handlers: Current no_handlers setting
        simplify_diagrams: Current simplify_diagrams setting

    Returns:
        Tuple of (no_vars, no_tasks, no_diagrams, no_examples, no_metadata, no_handlers, simplify_diagrams)
    """
    if minimal:
        no_vars = True
        no_tasks = True
        no_diagrams = True
        no_examples = True
        no_metadata = True
        no_handlers = True

    # If --no-diagrams is set, it overrides --simplify-diagrams
    if no_diagrams:
        simplify_diagrams = False

    return (
        no_vars,
        no_tasks,
        no_diagrams,
        no_examples,
        no_metadata,
        no_handlers,
        simplify_diagrams,
    )


def validate_role_path(role_path: str | None) -> Path:
    """Validate and resolve role path.

    Args:
        role_path: Path to role directory as string

    Returns:
        Resolved Path object

    Raises:
        click.UsageError: If role_path is None
        click.ClickException: If path doesn't exist or is not a directory
    """
    if not role_path:
        raise click.UsageError("Either --role or --collection must be specified.")

    assert isinstance(role_path, str), "Please provide a path, nothing provided."
    resolved_path = Path(role_path).resolve()

    if not resolved_path.exists():
        raise click.ClickException(f"Role directory does not exist: {resolved_path}")

    if not resolved_path.is_dir():
        raise click.ClickException(f"Path is not a directory: {role_path}")

    return resolved_path


def load_playbook_content(playbook: str | None) -> str | None:
    """Load playbook content from file.

    Args:
        playbook: Path to playbook file

    Returns:
        Playbook content as string, or None if no playbook specified or file not found
    """
    if not playbook:
        return None

    playbook_path = Path(playbook)
    if playbook_path.exists():
        with open(playbook_path, encoding="utf-8") as f:
            return f.read()
    else:
        logger.warning(f"Playbook file not found: {playbook}")
        return None


def handle_analyze_only_mode(role_info: dict[str, Any], role_name: str) -> None:
    """Display analysis summary in analyze-only mode and exit.

    Args:
        role_info: Role information dictionary
        role_name: Name of the role being analyzed
    """
    click.echo("\n" + "=" * 60)
    click.echo("📊 ANALYSIS COMPLETE")
    click.echo("=" * 60)

    # Show dependency statistics if available
    if role_info.get("tasks"):
        from docsible.diagrams.types.dependency_matrix import (
            analyze_task_dependencies,
            generate_dependency_summary,
        )

        all_deps = []
        for task_file_info in role_info.get("tasks", []):
            file_name = task_file_info.get("file", "unknown")
            tasks = task_file_info.get("tasks", [])
            all_deps.extend(analyze_task_dependencies(tasks, file_name))

        if all_deps:
            summary = generate_dependency_summary(all_deps)
            click.echo("\n📋 Task Dependencies:")
            click.echo(
                f"   - Tasks with variable dependencies: {summary['tasks_with_requirements']}/{summary['total_tasks']}"
            )
            click.echo(f"   - Tasks triggering handlers: {summary['tasks_with_triggers']}")
            click.echo(f"   - Tasks with error handling: {summary['error_handling_count']}")
            click.echo(f"   - Tasks setting facts: {summary['tasks_setting_facts']}")

    click.echo("\n✓ Analysis complete. Use without --analyze-only to generate documentation.\n")


def generate_mermaid_diagrams(
    generate_graph: bool,
    role_info: dict[str, Any],
    playbook_content: str | None,
    analysis_report: Any,
    minimal: bool,
    simplify_diagrams: bool,
) -> dict[str, Any]:
    """Generate all Mermaid diagrams for role visualization.

    Args:
        generate_graph: Whether to generate diagrams
        role_info: Role information dictionary
        playbook_content: Optional playbook content
        analysis_report: Complexity analysis report
        minimal: Whether minimal mode is enabled
        simplify_diagrams: Whether to simplify diagrams

    Returns:
        Dictionary containing all generated diagrams
    """
    result: dict[str, str | dict[Any, Any] | None] = {
        "mermaid_code_per_file": {},
        "sequence_diagram_high_level": None,
        "sequence_diagram_detailed": None,
        "state_diagram": None,
    }

    if not generate_graph:
        return result

    # Generate per-file task flowcharts
    raw_diagrams = generate_mermaid_role_tasks_per_file(role_info["tasks"])

    # Extract diagram strings from the dictionary structure
    # The function returns {'paginated': bool, 'diagram': str} or {'paginated': True, 'pages': [...]}
    extracted_diagrams = {}
    for file_name, diagram_data in raw_diagrams.items():
        if isinstance(diagram_data, dict):
            if diagram_data.get("paginated"):
                # For paginated diagrams, include all pages
                if "pages" in diagram_data:
                    # Create separate entries for each page
                    for idx, page in enumerate(diagram_data["pages"]):
                        page_key = f"{file_name} (Page {idx + 1}/{len(diagram_data['pages'])})"
                        extracted_diagrams[page_key] = page["diagram"]
                elif "diagram" in diagram_data:
                    # Non-paginated, extract the diagram
                    extracted_diagrams[file_name] = diagram_data["diagram"]
            else:
                # Non-paginated, extract the diagram
                extracted_diagrams[file_name] = diagram_data.get("diagram", diagram_data)
        else:
            # Already a string
            extracted_diagrams[file_name] = diagram_data

    result["mermaid_code_per_file"] = extracted_diagrams

    # High-level sequence diagram (playbook → roles)
    if playbook_content:
        try:
            playbook_parsed = yaml.safe_load(playbook_content)
            result["sequence_diagram_high_level"] = generate_mermaid_sequence_playbook_high_level(
                playbook_parsed, role_meta=role_info.get("meta")
            )
        except Exception as e:
            logger.warning(f"Could not generate high-level sequence diagram: {e}")

    # Detailed sequence diagram (role → tasks → handlers)
    try:
        should_simplify = minimal or simplify_diagrams
        result["sequence_diagram_detailed"] = generate_mermaid_sequence_role_detailed(
            role_info,
            include_handlers=len(role_info.get("handlers", [])) > 0,
            simplify_large=should_simplify,
            max_lines=20,
        )
    except Exception as e:
        logger.warning(f"Could not generate detailed sequence diagram: {e}")

    # State transition diagram for MEDIUM complexity roles
    try:
        from docsible.utils.state_diagram import (
            generate_state_diagram,
            should_generate_state_diagram,
        )

        if should_generate_state_diagram(role_info, analysis_report.category.value):
            result["state_diagram"] = generate_state_diagram(
                role_info, role_name=role_info.get("name")
            )
            logger.info("Generated state transition diagram for MEDIUM complexity role")
    except Exception as e:
        logger.warning(f"Could not generate state diagram: {e}")

    return result


def generate_integration_and_architecture_diagrams(
    generate_graph: bool,
    role_info: dict[str, Any],
    analysis_report: Any,
    execution_graph: Any | None = None,
) -> tuple[str | None, str | None]:
    """Generate integration boundary and component architecture diagrams.

    Args:
        generate_graph: Whether to generate diagrams
        analysis_report: Complexity analysis report

    Returns:
        Tuple of (integration_boundary_diagram, architecture_diagram)
    """
    integration_boundary_diagram = None
    architecture_diagram = None

    if not generate_graph:
        return integration_boundary_diagram, architecture_diagram

    # Integration boundary diagram
    if analysis_report.integration_points:
        try:
            from docsible.diagrams.types.integration import (
                generate_integration_boundary,
                should_generate_integration_diagram,
            )

            if should_generate_integration_diagram(analysis_report.integration_points):
                integration_boundary_diagram = generate_integration_boundary(
                    analysis_report.integration_points
                )
                logger.info(
                    f"Generated integration boundary diagram ({len(analysis_report.integration_points)} integrations)"
                )
        except Exception as e:
            logger.warning(f"Could not generate integration boundary diagram: {e}")

    # Component architecture diagram for complex roles
    try:
        from docsible.diagrams.types.architecture import (
            generate_component_architecture,
            should_generate_architecture_diagram,
        )

        if should_generate_architecture_diagram(analysis_report):
            architecture_diagram = generate_component_architecture(
                role_info=role_info,
                complexity_report=analysis_report,
                execution_graph=execution_graph,
            )
            logger.info(
                f"Generated component architecture diagram for {analysis_report.category.value.upper()} role"
            )
    except Exception as e:
        logger.warning(f"Could not generate architecture diagram: {e}")

    return integration_boundary_diagram, architecture_diagram


def generate_dependency_matrix(
    show_dependencies: bool, role_info: dict[str, Any], analysis_report: Any
) -> tuple[str | None, dict | None, bool]:
    """Generate dependency matrix and summary.

    Args:
        show_dependencies: Whether user requested dependency matrix
        role_info: Role information dictionary
        analysis_report: Complexity analysis report

    Returns:
        Tuple of (dependency_matrix, dependency_summary, show_dependency_matrix)
    """
    dependency_matrix = None
    dependency_summary = None
    show_dependency_matrix = False

    try:
        from docsible.diagrams.types.dependency_matrix import (
            analyze_task_dependencies,
            generate_dependency_matrix_markdown,
            generate_dependency_summary,
            should_generate_dependency_matrix,
        )

        # Force show dependencies if user requested it, otherwise use heuristic
        if show_dependencies or should_generate_dependency_matrix(role_info, analysis_report):
            dependency_matrix = generate_dependency_matrix_markdown(role_info)
            if dependency_matrix:
                show_dependency_matrix = True
                # Generate summary statistics
                all_deps = []
                for task_file_info in role_info.get("tasks", []):
                    file_name = task_file_info.get("file", "unknown")
                    tasks = task_file_info.get("tasks", [])
                    all_deps.extend(analyze_task_dependencies(tasks, file_name))
                dependency_summary = generate_dependency_summary(all_deps)
                logger.info(
                    f"Generated dependency matrix for {analysis_report.category.value.upper()} role"
                )
    except Exception as e:
        logger.warning(f"Could not generate dependency matrix: {e}")

    return dependency_matrix, dependency_summary, show_dependency_matrix
