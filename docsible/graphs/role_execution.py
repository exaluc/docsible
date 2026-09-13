"""Build a renderer-independent execution graph from loaded Ansible role facts."""

from __future__ import annotations

import re
from collections import deque
from dataclasses import asdict, dataclass, field
from enum import Enum
from fnmatch import fnmatch
from pathlib import PurePosixPath
from typing import Any

from docsible.utils.special_tasks_keys import extract_loop_control


class NodeKind(str, Enum):
    ROLE = "role"
    TASK_FILE = "task_file"
    TASK = "task"
    HANDLER = "handler"
    VARIABLE = "variable"
    EXTERNAL_ROLE = "external_role"


class EdgeKind(str, Enum):
    CONTAINS = "contains"
    INCLUDES_TASK_FILE = "includes_task_file"
    IMPORTS_TASK_FILE = "imports_task_file"
    INCLUDES_ROLE = "includes_role"
    IMPORTS_ROLE = "imports_role"
    NOTIFIES_HANDLER = "notifies_handler"
    USES_VARIABLE = "uses_variable"


class ResolutionStatus(str, Enum):
    STATIC = "static"
    DYNAMIC = "dynamic"
    UNKNOWN = "unknown"
    UNRESOLVED_EXTERNAL = "unresolved_external"


@dataclass(frozen=True)
class SourceLocation:
    file: str
    line: int | None = None


@dataclass(frozen=True)
class GraphNode:
    id: str
    kind: NodeKind
    label: str
    source: SourceLocation | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class GraphEdge:
    kind: EdgeKind
    source_id: str
    target_id: str | None
    resolution: ResolutionStatus
    source: SourceLocation
    condition: str | None = None
    loop: str | None = None
    target_expression: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class RoleExecutionGraph:
    """The small interface shared by phase and renderer projections."""

    role_id: str
    nodes: dict[str, GraphNode] = field(default_factory=dict)
    edges: list[GraphEdge] = field(default_factory=list)

    def add_node(self, node: GraphNode) -> None:
        self.nodes.setdefault(node.id, node)

    def add_edge(self, edge: GraphEdge) -> None:
        if edge not in self.edges:
            self.edges.append(edge)

    def execution_phases(self) -> list[dict[str, Any]]:
        """Return deterministic static traversal phases plus unreachable files."""
        files = [node for node in self.nodes.values() if node.kind is NodeKind.TASK_FILE]
        file_ids = {node.id for node in files}
        roots = sorted(node.id for node in files if node.metadata.get("file") == "main.yml")
        if not roots:
            roots = sorted(file_ids)

        task_files_by_task: dict[str, str] = {
            edge.target_id: edge.source_id
            for edge in self.edges
            if edge.kind is EdgeKind.CONTAINS
            and edge.source_id in file_ids
            and edge.target_id is not None
        }
        outgoing: dict[str, list[GraphEdge]] = {}
        for edge in self.edges:
            if (
                edge.kind in {EdgeKind.INCLUDES_TASK_FILE, EdgeKind.IMPORTS_TASK_FILE}
                and edge.resolution in {ResolutionStatus.STATIC, ResolutionStatus.DYNAMIC}
                and edge.target_id in file_ids
            ):
                source_file_id = task_files_by_task.get(edge.source_id)
                if source_file_id is not None:
                    outgoing.setdefault(source_file_id, []).append(edge)

        phases: list[dict[str, Any]] = []
        seen: set[str] = set()
        queue: deque[tuple[str, str, list[GraphEdge]]] = deque(
            (root, "entrypoint", []) for root in roots
        )
        while queue:
            node_id, phase_kind, incoming = queue.popleft()
            if node_id in seen:
                continue
            seen.add(node_id)
            node = self.nodes[node_id]
            phases.append(
                {
                    "file": node.metadata["file"],
                    "task_count": node.metadata["task_count"],
                    "kind": phase_kind,
                    "conditions": sorted({edge.condition for edge in incoming if edge.condition}),
                    "expressions": sorted(
                        {edge.target_expression for edge in incoming if edge.target_expression}
                    ),
                }
            )
            for edge in outgoing.get(node_id, []):
                if edge.target_id is not None:
                    queue.append(
                        (
                            edge.target_id,
                            "dynamic"
                            if phase_kind == "dynamic" or edge.resolution is ResolutionStatus.DYNAMIC
                            else "conditional"
                            if edge.condition
                            else "static",
                            [edge],
                        )
                    )

        for node in sorted(files, key=lambda item: item.metadata["file"]):
            if node.id not in seen:
                phases.append(
                    {
                        "file": node.metadata["file"],
                        "task_count": node.metadata["task_count"],
                        "kind": "unreachable",
                        "conditions": [],
                        "expressions": [],
                    }
                )
        return phases

    def to_dict(self) -> dict[str, Any]:
        return {
            "role_id": self.role_id,
            "nodes": [asdict(node) for node in self.nodes.values()],
            "edges": [asdict(edge) for edge in self.edges],
        }


_TASK_FILE_ACTIONS = {"include", "include_tasks", "import_tasks"}
_ROLE_ACTIONS = {"include_role", "import_role"}
_VARIABLE_PATTERN = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\b")
# One-pass identifier tokenizer for variable-usage edges. Equivalent to the
# previous per-variable `\b<name>\b` search (a variable "matches" iff it
# appears as a whole identifier token in the serialized task), but scans each
# task once instead of once per known variable.
_IDENT_TOKEN_PATTERN = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
_ROLE_PATH_TASK_PREFIX = re.compile(r"^\{\{\s*role_path\s*\}\}/tasks/")


def build_role_execution_graph(role_info: dict[str, Any]) -> RoleExecutionGraph:
    """Build source-backed facts without making renderer-specific guesses."""
    role_name = str(role_info.get("name", "unknown"))
    graph = RoleExecutionGraph(role_id=f"role:{role_name}")
    graph.add_node(GraphNode(graph.role_id, NodeKind.ROLE, role_name))

    task_files = role_info.get("tasks", [])
    file_ids = {
        item.get("file", "unknown"): f"task_file:{role_name}:{item.get('file', 'unknown')}"
        for item in task_files
    }
    for item in task_files:
        file_name = item.get("file", "unknown")
        file_id = file_ids[file_name]
        graph.add_node(
            GraphNode(
                file_id,
                NodeKind.TASK_FILE,
                file_name,
                SourceLocation(file_name),
                {"file": file_name, "task_count": len(item.get("tasks", []))},
            )
        )
        graph.add_edge(
            GraphEdge(EdgeKind.CONTAINS, graph.role_id, file_id, ResolutionStatus.STATIC, SourceLocation(file_name))
        )

    variables = _add_variables(graph, role_name, role_info)
    handlers = _add_handlers(graph, role_name, role_info)
    for item in task_files:
        _add_tasks(graph, role_name, item, file_ids, variables, handlers)
    return graph


def _add_variables(graph: RoleExecutionGraph, role_name: str, role_info: dict[str, Any]) -> dict[str, str]:
    variables: dict[str, str] = {}
    for scope in ("defaults", "vars"):
        for data_file in role_info.get(scope, []):
            for key, details in data_file.get("data", {}).items():
                name = key.split(".", 1)[0]
                node_id = f"variable:{role_name}:{scope}:{name}"
                variables.setdefault(name, node_id)
                graph.add_node(GraphNode(node_id, NodeKind.VARIABLE, name, SourceLocation(data_file["file"], details.get("line")), {"scope": scope}))
    return variables


def _add_handlers(graph: RoleExecutionGraph, role_name: str, role_info: dict[str, Any]) -> dict[str, str]:
    handlers: dict[str, str] = {}
    for handler in role_info.get("handlers", []):
        node_id = f"handler:{role_name}:{handler['name']}"
        graph.add_node(GraphNode(node_id, NodeKind.HANDLER, handler["name"], SourceLocation(f"handlers/{handler.get('file', 'main.yml')}")))
        for name in [handler["name"], *handler.get("listen", [])]:
            handlers[name] = node_id
    return handlers


def _add_tasks(graph: RoleExecutionGraph, role_name: str, task_file: dict[str, Any], file_ids: dict[str, str], variables: dict[str, str], handlers: dict[str, str]) -> None:
    file_name = task_file.get("file", "unknown")
    raw_tasks = task_file.get("mermaid", [])
    line_ranges = task_file.get("line_ranges", [])
    for index, task in _walk_tasks(raw_tasks):
        line = line_ranges[index[0]][0] if index and index[0] < len(line_ranges) else None
        source = SourceLocation(f"tasks/{file_name}", line)
        task_id = f"task:{role_name}:{file_name}:{'.'.join(map(str, index))}"
        metadata = {"file": file_name, "module": _module_name(task)}
        if condition := _condition(task):
            metadata["condition"] = condition
        if loop := _loop(task):
            metadata["loop"] = loop
            if loop_control := extract_loop_control(task):
                metadata["loop_control"] = loop_control
        if error_handling := _error_handling(task):
            metadata["error_handling"] = error_handling
        graph.add_node(GraphNode(task_id, NodeKind.TASK, str(task.get("name", "Unnamed")), source, metadata))
        graph.add_edge(GraphEdge(EdgeKind.CONTAINS, file_ids[file_name], task_id, ResolutionStatus.STATIC, source))
        _add_variable_edges(graph, task_id, task, variables, source)
        _add_notification_edges(graph, task_id, task, handlers, source)
        _add_composition_edge(graph, task_id, task, file_name, file_ids, source)


def _walk_tasks(tasks: list[Any], prefix: tuple[int, ...] = ()):
    for index, task in enumerate(tasks):
        if not isinstance(task, dict):
            continue
        path = (*prefix, index)
        yield path, task
        for section in ("block", "rescue", "always"):
            nested = task.get(section)
            if isinstance(nested, list):
                yield from _walk_tasks(nested, path)


def _module_name(task: dict[str, Any]) -> str:
    for key in task:
        if key.split(".")[-1] in _TASK_FILE_ACTIONS | _ROLE_ACTIONS:
            return key
    excluded = {"name", "when", "notify", "tags", "register", "loop", "loop_control", "block", "rescue", "always", "vars"}
    return next((key for key in task if key not in excluded), "unknown")


def _add_variable_edges(graph: RoleExecutionGraph, task_id: str, task: dict[str, Any], variables: dict[str, str], source: SourceLocation) -> None:
    referenced = set(_IDENT_TOKEN_PATTERN.findall(str(task)))
    for name, node_id in variables.items():
        if name in referenced:
            graph.add_edge(GraphEdge(EdgeKind.USES_VARIABLE, task_id, node_id, ResolutionStatus.STATIC, source))


def _add_notification_edges(graph: RoleExecutionGraph, task_id: str, task: dict[str, Any], handlers: dict[str, str], source: SourceLocation) -> None:
    notified = task.get("notify", [])
    for name in [notified] if isinstance(notified, str) else notified if isinstance(notified, list) else []:
        graph.add_edge(GraphEdge(EdgeKind.NOTIFIES_HANDLER, task_id, handlers.get(name), ResolutionStatus.STATIC if name in handlers else ResolutionStatus.UNKNOWN, source, target_expression=name))


def _add_composition_edge(graph: RoleExecutionGraph, task_id: str, task: dict[str, Any], source_file: str, file_ids: dict[str, str], source: SourceLocation) -> None:
    module = _module_name(task)
    short_module = module.split(".")[-1]
    if short_module not in _TASK_FILE_ACTIONS | _ROLE_ACTIONS:
        return
    raw_target = task.get(module)
    if isinstance(raw_target, dict):
        raw_target = raw_target.get("file" if short_module in _TASK_FILE_ACTIONS else "name")
    target = str(raw_target) if raw_target is not None else ""
    resolved_target = _ROLE_PATH_TASK_PREFIX.sub("", target)
    dynamic = "{{" in resolved_target or "{%" in resolved_target
    kind = EdgeKind.IMPORTS_TASK_FILE if short_module == "import_tasks" else EdgeKind.INCLUDES_TASK_FILE
    if short_module in _ROLE_ACTIONS:
        kind = EdgeKind.IMPORTS_ROLE if short_module == "import_role" else EdgeKind.INCLUDES_ROLE
        target_id = f"external_role:{target}" if target and not dynamic else None
        if target_id:
            graph.add_node(GraphNode(target_id, NodeKind.EXTERNAL_ROLE, target, metadata={"role": target}))
        resolution = ResolutionStatus.DYNAMIC if dynamic else ResolutionStatus.UNRESOLVED_EXTERNAL
    else:
        if dynamic:
            candidate_ids = _resolve_dynamic_task_files(resolved_target, source_file, file_ids)
            if candidate_ids:
                for target_id in candidate_ids:
                    graph.add_edge(
                        GraphEdge(
                            kind,
                            task_id,
                            target_id,
                            ResolutionStatus.DYNAMIC,
                            source,
                            condition=_condition(task),
                            loop=_loop(task),
                            target_expression=target,
                        )
                    )
                return
            target_id = None
            resolution = ResolutionStatus.DYNAMIC
        else:
            target_id = _resolve_task_file(resolved_target, source_file, file_ids)
            resolution = ResolutionStatus.STATIC if target_id else ResolutionStatus.UNKNOWN
    graph.add_edge(GraphEdge(kind, task_id, target_id, resolution, source, condition=_condition(task), loop=_loop(task), target_expression=target or None))


def _resolve_task_file(target: str, source_file: str, file_ids: dict[str, str]) -> str | None:
    candidates = [target.removeprefix("tasks/"), str(PurePosixPath(source_file).parent / target)]
    for candidate in candidates:
        if candidate in file_ids:
            return file_ids[candidate]
    matches = [node_id for file_name, node_id in file_ids.items() if PurePosixPath(file_name).name == PurePosixPath(target).name]
    return matches[0] if len(matches) == 1 else None


def _resolve_dynamic_task_files(target: str, source_file: str, file_ids: dict[str, str]) -> list[str]:
    """Find in-repo candidates for a templated include without claiming certainty."""
    pattern = re.sub(r"\{\{.*?\}\}", "*", target)
    if PurePosixPath(pattern).name.startswith("*"):
        return []
    candidates = [pattern.removeprefix("tasks/"), str(PurePosixPath(source_file).parent / pattern)]
    return sorted(
        {
            node_id
            for candidate in candidates
            for file_name, node_id in file_ids.items()
            if fnmatch(file_name, candidate)
        }
    )


def _condition(task: dict[str, Any]) -> str | None:
    value = task.get("when")
    return " and ".join(map(str, value)) if isinstance(value, list) else str(value) if value else None


def _loop(task: dict[str, Any]) -> str | None:
    if "loop" in task:
        return "loop"
    return next((key for key in task if key.startswith("with_")), None)


def _error_handling(task: dict[str, Any]) -> str | None:
    """Return the block error-handling shape ('rescue'/'always'/both) if any."""
    has_rescue = isinstance(task.get("rescue"), list)
    has_always = isinstance(task.get("always"), list)
    if has_rescue and has_always:
        return "rescue + always"
    if has_rescue:
        return "rescue"
    if has_always:
        return "always"
    return None
