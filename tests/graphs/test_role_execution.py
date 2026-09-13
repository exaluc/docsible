"""Tests for the source-backed role execution graph."""

import json

from docsible.graphs import (
    EdgeKind,
    NodeKind,
    ResolutionStatus,
    build_role_execution_graph,
)


def test_builds_static_dynamic_and_notify_relationships():
    role_info = {
        "name": "web",
        "defaults": [{"file": "main.yml", "data": {"web_port": {"line": 1}}}],
        "vars": [],
        "handlers": [{"name": "restart web", "listen": ["restart"], "file": "main.yml"}],
        "tasks": [
            {
                "file": "main.yml",
                "tasks": [{}, {}],
                "line_ranges": [(1, 5), (6, 10)],
                "mermaid": [
                    {
                        "name": "Configure",
                        "template": {"src": "web.j2"},
                        "notify": "restart",
                        "when": "web_port > 0",
                    },
                    {"include_tasks": "setup.yml"},
                ],
            },
            {
                "file": "setup.yml",
                "tasks": [{}],
                "line_ranges": [(1, 3)],
                "mermaid": [{"include_tasks": "{{ ansible_facts.os_family }}.yml"}],
            },
        ],
    }

    graph = build_role_execution_graph(role_info)

    assert any(edge.kind is EdgeKind.NOTIFIES_HANDLER and edge.target_id for edge in graph.edges)
    static_include = next(edge for edge in graph.edges if edge.target_expression == "setup.yml")
    assert static_include.kind is EdgeKind.INCLUDES_TASK_FILE
    assert static_include.resolution is ResolutionStatus.STATIC
    assert static_include.target_id == "task_file:web:setup.yml"
    dynamic_include = next(edge for edge in graph.edges if edge.target_expression and "{{" in edge.target_expression)
    assert dynamic_include.resolution is ResolutionStatus.DYNAMIC
    assert dynamic_include.target_id is None
    phases = graph.execution_phases()
    assert [phase["file"] for phase in phases] == ["main.yml", "setup.yml"]
    assert phases[1]["kind"] == "static"


def test_preserves_external_role_boundaries_in_renderer_contract():
    graph = build_role_execution_graph(
        {
            "name": "web",
            "defaults": [],
            "vars": [],
            "handlers": [],
            "tasks": [
                {
                    "file": "main.yml",
                    "tasks": [{}, {}],
                    "line_ranges": [(1, 2), (3, 4)],
                    "mermaid": [
                        {"import_role": {"name": "vendor.common", "tasks_from": "setup"}},
                        {"include_role": "{{ selected_role }}"},
                    ],
                }
            ],
        }
    )

    role_edges = [
        edge for edge in graph.edges if edge.kind in {EdgeKind.IMPORTS_ROLE, EdgeKind.INCLUDES_ROLE}
    ]
    assert role_edges[0].resolution is ResolutionStatus.UNRESOLVED_EXTERNAL
    assert role_edges[0].target_id == "external_role:vendor.common"
    assert role_edges[1].resolution is ResolutionStatus.DYNAMIC
    assert role_edges[1].target_id is None
    json.dumps(graph.to_dict())


def test_loop_control_recorded_in_task_metadata():
    graph = build_role_execution_graph(
        {
            "name": "web",
            "defaults": [],
            "vars": [],
            "handlers": [],
            "tasks": [
                {
                    "file": "main.yml",
                    "tasks": [{}],
                    "line_ranges": [(1, 3)],
                    "mermaid": [
                        {
                            "name": "Loop custom var",
                            "ansible.builtin.debug": {},
                            "loop": ["a", "b"],
                            "loop_control": {"loop_var": "entry", "index_var": "i"},
                        }
                    ],
                }
            ],
        }
    )

    loop_nodes = [
        node
        for node in graph.nodes.values()
        if node.kind is NodeKind.TASK and "loop_control" in node.metadata
    ]
    assert loop_nodes, "loop_control must be recorded on the task node"
    assert loop_nodes[0].metadata["loop"] == "loop"
    assert loop_nodes[0].metadata["loop_control"] == {"loop_var": "entry", "index_var": "i"}
