"""
Component architecture diagram generator for complex Ansible roles.

Generates Mermaid diagrams showing internal role structure and data flow.
"""

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

_DETAILED_FILE_BUDGET = 20
_DETAILED_EDGE_BUDGET = 35
_DETAILED_FANOUT_BUDGET = 8


def generate_component_architecture(
    role_info: dict[str, Any] | None, complexity_report: Any, execution_graph: Any | None = None
) -> str | None:
    """
    Generate component architecture diagram for complex roles.

    Shows:
    - Role structure (defaults, vars, tasks, handlers)
    - Data flow between components
    - External integrations
    - Handler notification paths

    Args:
        role_info: Role information dictionary
        complexity_report: ComplexityReport object with metrics

    Returns:
        Mermaid diagram code as string, or None if not applicable

    Example:
        >>> diagram = generate_component_architecture(role_info, complexity_report)
        >>> print(diagram)
        graph TB
            subgraph Variables
                defaults[Defaults: 15 vars]
                vars[Vars: 8 vars]
            end
            subgraph Tasks
                tasks_install[install.yml: 12 tasks]
                tasks_config[configure.yml: 18 tasks]
            end
            defaults --> tasks_install
            vars --> tasks_config
            tasks_config -.notify.-> handlers
    """
    if not role_info:
        return None

    lines = ["graph TB"]

    # Component counters
    defaults_count = sum(len(df.get("data", {})) for df in role_info.get("defaults", []))
    vars_count = sum(len(vf.get("data", {})) for vf in role_info.get("vars", []))
    handlers_count = len(role_info.get("handlers", []))

    # Variables subgraph
    has_variables = defaults_count > 0 or vars_count > 0
    if has_variables:
        lines.append("    subgraph Variables")
        if defaults_count > 0:
            lines.append(
                f'        defaults["📋 Defaults<br/>{defaults_count} variable{"s" if defaults_count != 1 else ""}"]'
            )
        if vars_count > 0:
            lines.append(
                f'        vars["📌 Vars<br/>{vars_count} variable{"s" if vars_count != 1 else ""}"]'
            )
        lines.append("    end")
        lines.append("")

    # Tasks subgraph with file breakdown
    task_files = role_info.get("tasks", [])
    if execution_graph is not None and _should_group_execution_graph(execution_graph, task_files):
        return _generate_grouped_architecture(role_info, execution_graph)
    if task_files:
        lines.append("    subgraph Tasks")
        for idx, task_file in enumerate(task_files):
            file_name = task_file.get("file", f"file{idx}")
            task_count = len(task_file.get("tasks", []))
            safe_id = f"tasks_{file_name.replace('.', '_').replace('/', '_')}"
            lines.append(
                f'        {safe_id}["⚙️ {file_name}<br/>{task_count} task{"s" if task_count != 1 else ""}"]'
            )
        lines.append("    end")
        lines.append("")

    # Handlers node
    if handlers_count > 0:
        lines.append(
            f'    handlers["🔔 Handlers<br/>{handlers_count} handler{"s" if handlers_count != 1 else ""}"]'
        )
        lines.append("")

    # External integrations node
    if complexity_report and complexity_report.integration_points:
        integration_count = len(complexity_report.integration_points)
        integration_names = [ip.system_name for ip in complexity_report.integration_points[:2]]
        if integration_count > 2:
            integration_names.append("...")
        integration_label = "<br/>".join(integration_names)
        lines.append(f'    external["🌐 External Systems<br/>{integration_label}"]')
        lines.append("")

    # Data flow connections
    lines.append("    %% Data Flow")

    # Variables flow only to files with source-backed variable references.
    if execution_graph is not None:
        variable_edges: set[tuple[str, str]] = set()
        for edge in execution_graph.edges:
            if edge.kind.value != "uses_variable" or edge.target_id is None:
                continue
            task = execution_graph.nodes.get(edge.source_id)
            variable = execution_graph.nodes.get(edge.target_id)
            if not task or not variable:
                continue
            variable_node = "defaults" if variable.metadata.get("scope") == "defaults" else "vars"
            task_id = f"tasks_{task.metadata['file'].replace('.', '_').replace('/', '_')}"
            variable_edges.add((variable_node, task_id))
        for variable_node, task_id in sorted(variable_edges):
            lines.append(f"    {variable_node} --> {task_id}")
    elif has_variables and task_files:
        first_task_id = (
            f"tasks_{task_files[0].get('file', 'file0').replace('.', '_').replace('/', '_')}"
        )
        if defaults_count > 0:
            lines.append(f"    defaults --> {first_task_id}")
        if vars_count > 0:
            lines.append(f"    vars --> {first_task_id}")

    # Include/import flow between task files (statically resolvable targets only;
    # templated targets are dynamic and are deliberately not drawn as edges)
    task_file_ids = {
        task_file.get("file", f"file{idx}"): (
            f"tasks_{task_file.get('file', f'file{idx}').replace('.', '_').replace('/', '_')}"
        )
        for idx, task_file in enumerate(task_files)
    }
    task_file_ids_by_basename: dict[str, str] = {}
    for file_name, node_id in task_file_ids.items():
        task_file_ids_by_basename.setdefault(file_name.split("/")[-1], node_id)
    added_include_edges: set[tuple[str, str]] = set()
    for task_file in task_files:
        file_name = task_file.get("file", "")
        source_id = task_file_ids.get(file_name)
        if not source_id:
            continue
        for task in task_file.get("tasks", []):
            target = task.get("include_target")
            if not target or "{{" in target:
                continue
            target_id = task_file_ids.get(target) or task_file_ids_by_basename.get(
                target.split("/")[-1]
            )
            if (
                target_id
                and target_id != source_id
                and (source_id, target_id) not in added_include_edges
            ):
                lines.append(f'    {source_id} -."includes".-> {target_id}')
                added_include_edges.add((source_id, target_id))

    # Tasks to handlers use source-backed notify relationships when available.
    if execution_graph is not None:
        notifying_files: set[str] = set()
        for edge in execution_graph.edges:
            if edge.kind.value == "notifies_handler" and edge.target_id:
                task = execution_graph.nodes.get(edge.source_id)
                if task:
                    notifying_files.add(task.metadata["file"])
        for file_name in sorted(notifying_files):
            task_id = f"tasks_{file_name.replace('.', '_').replace('/', '_')}"
            lines.append(f'    {task_id} -."notify".-> handlers')
    elif task_files and handlers_count > 0:
        last_task_id = (
            f"tasks_{task_files[-1].get('file', 'fileN').replace('.', '_').replace('/', '_')}"
        )
        lines.append(f'    {last_task_id} -."notify".-> handlers')

    # Tasks to external systems
    if task_files and complexity_report and complexity_report.integration_points:
        # Find which task files have integrations
        for task_file in task_files:
            task_id = f"tasks_{task_file.get('file', 'file').replace('.', '_').replace('/', '_')}"
            # Check if this file has integration modules
            has_integration = any(
                task.get("module", "").startswith(
                    ("uri", "get_url", "mysql", "postgresql", "mongodb", "hashi_vault")
                )
                for task in task_file.get("tasks", [])
            )
            if has_integration:
                lines.append(f"    {task_id} --> external")
                break  # Only show one connection to avoid clutter

    # Styling
    lines.append("")
    lines.append("    %% Styling")
    lines.append("    classDef varStyle fill:#e3f2fd,stroke:#1976d2,stroke-width:2px")
    lines.append("    classDef taskStyle fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px")
    lines.append("    classDef handlerStyle fill:#fff3e0,stroke:#f57c00,stroke-width:2px")
    lines.append("    classDef externalStyle fill:#ffebee,stroke:#c62828,stroke-width:2px")
    lines.append("")

    if defaults_count > 0:
        lines.append("    class defaults varStyle")
    if vars_count > 0:
        lines.append("    class vars varStyle")
    if handlers_count > 0:
        lines.append("    class handlers handlerStyle")
    if complexity_report and complexity_report.integration_points:
        lines.append("    class external externalStyle")

    # Apply task styling to all task nodes
    for task_file in task_files:
        safe_id = f"tasks_{task_file.get('file', 'file').replace('.', '_').replace('/', '_')}"
        lines.append(f"    class {safe_id} taskStyle")

    return "\n".join(lines)


def _should_group_execution_graph(execution_graph: Any, task_files: list[dict[str, Any]]) -> bool:
    include_edges = [
        edge
        for edge in execution_graph.edges
        if edge.kind.value in {"includes_task_file", "imports_task_file"}
    ]
    fanout: dict[str, int] = {}
    for edge in include_edges:
        fanout[edge.source_id] = fanout.get(edge.source_id, 0) + 1
    return (
        len(task_files) > _DETAILED_FILE_BUDGET
        or len(include_edges) > _DETAILED_EDGE_BUDGET
        or max(fanout.values(), default=0) > _DETAILED_FANOUT_BUDGET
    )


def _generate_grouped_architecture(role_info: dict[str, Any], execution_graph: Any) -> str:
    """Render a bounded directory-level overview from graph facts."""
    task_nodes = [node for node in execution_graph.nodes.values() if node.kind.value == "task_file"]
    groups: dict[str, list[str]] = {}
    for node in task_nodes:
        file_name = node.metadata["file"]
        group = "entry point" if file_name == "main.yml" else file_name.split("/", 1)[0]
        groups.setdefault(group, []).append(file_name)

    def node_id(group: str) -> str:
        return "group_" + re.sub(r"[^A-Za-z0-9_]", "_", group)

    file_group = {file_name: group for group, files in groups.items() for file_name in files}
    lines = ["graph TB", '    overview["Grouped execution overview"]']
    for group, files in sorted(groups.items()):
        label = "main.yml" if group == "entry point" else f"{group}<br/>{len(files)} task files"
        lines.append(f'    {node_id(group)}["{label}"]')
        lines.append(f"    overview --> {node_id(group)}")

    task_to_file = {
        edge.target_id: edge.source_id
        for edge in execution_graph.edges
        if edge.kind.value == "contains" and edge.source_id.startswith("task_file:")
    }
    file_by_id = {node.id: node.metadata["file"] for node in task_nodes}
    grouped_edges: dict[tuple[str, str], int] = {}
    uncertain_sources: set[str] = set()
    notify_sources: set[str] = set()
    for edge in execution_graph.edges:
        if edge.kind.value in {"includes_task_file", "imports_task_file"}:
            source_file_id = task_to_file.get(edge.source_id)
            source_file = file_by_id.get(source_file_id)
            target_file = file_by_id.get(edge.target_id)
            if source_file and target_file:
                key = (file_group[source_file], file_group[target_file])
                grouped_edges[key] = grouped_edges.get(key, 0) + 1
            elif source_file and edge.resolution.value in {"dynamic", "unknown"}:
                uncertain_sources.add(file_group[source_file])
        elif edge.kind.value == "notifies_handler" and edge.target_id:
            source_file_id = task_to_file.get(edge.source_id)
            if source_file_id in file_by_id:
                notify_sources.add(file_group[file_by_id[source_file_id]])

    for (source, target), count in sorted(grouped_edges.items()):
        if source != target:
            label = "include" if count == 1 else f"{count} includes"
            lines.append(f'    {node_id(source)} -."{label}".-> {node_id(target)}')
    if uncertain_sources:
        lines.append(f'    uncertain["Dynamic or unknown<br/>{len(uncertain_sources)} source groups"]')
        for source in sorted(uncertain_sources):
            lines.append(f'    {node_id(source)} -."dynamic".-> uncertain')
    if notify_sources:
        lines.append('    handlers["Handlers"]')
        for source in sorted(notify_sources):
            lines.append(f'    {node_id(source)} -."notify".-> handlers')
    lines.extend(
        [
            "    classDef groupStyle fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px",
            "    classDef uncertaintyStyle fill:#fff3e0,stroke:#f57c00,stroke-width:2px",
            "    class overview groupStyle",
            "    class uncertain uncertaintyStyle" if uncertain_sources else "",
        ]
    )
    for group in groups:
        lines.append(f"    class {node_id(group)} groupStyle")
    return "\n".join(line for line in lines if line)


def should_generate_architecture_diagram(complexity_report: Any) -> bool:
    """
    Determine if a component architecture diagram should be generated.

    Args:
        complexity_report: ComplexityReport object

    Returns:
        True if role is COMPLEX (25+ tasks) or has high composition score

    Example:
        >>> should_generate_architecture_diagram(complex_report)
        True
        >>> should_generate_architecture_diagram(simple_report)
        False
    """
    if not complexity_report:
        return False

    # Generate for COMPLEX roles
    if complexity_report.category.value in {"complex", "enterprise"}:
        return True

    # Generate for MEDIUM roles with high composition
    if (
        complexity_report.category.value == "medium"
        and complexity_report.metrics.composition_score >= 5
    ):
        return True

    return False
