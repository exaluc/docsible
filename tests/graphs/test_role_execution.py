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


def test_uses_variable_edge_survives_tokenizer_rewrite():
    """The (a) optimization replaced a per-variable regex with a one-pass
    identifier tokenizer; this guards that a genuinely referenced variable
    still yields a uses_variable edge."""
    graph = build_role_execution_graph(
        {
            "name": "web",
            "defaults": [{"file": "main.yml", "data": {"web_port": {"line": 1}}}],
            "vars": [],
            "handlers": [],
            "tasks": [
                {
                    "file": "main.yml",
                    "tasks": [{}],
                    "line_ranges": [(1, 3)],
                    "mermaid": [
                        {"name": "Bind", "ansible.builtin.template": {"port": "{{ web_port }}"}}
                    ],
                }
            ],
        }
    )
    var_edges = [e for e in graph.edges if e.kind is EdgeKind.USES_VARIABLE]
    assert [e.target_id for e in var_edges] == ["variable:web:defaults:web_port"]


def test_rescue_block_recorded_as_error_handling():
    graph = build_role_execution_graph(
        {
            "name": "r",
            "defaults": [],
            "vars": [],
            "handlers": [],
            "tasks": [
                {
                    "file": "main.yml",
                    "tasks": [{}],
                    "mermaid": [
                        {
                            "name": "Guarded",
                            "block": [{"debug": {}}],
                            "rescue": [{"debug": {}}],
                        }
                    ],
                }
            ],
        }
    )
    nodes = [
        n for n in graph.nodes.values() if n.kind is NodeKind.TASK and "error_handling" in n.metadata
    ]
    assert nodes and nodes[0].metadata["error_handling"] == "rescue"


def test_execution_phases_partition_covers_every_file():
    role_info = {
        "name": "r",
        "defaults": [],
        "vars": [],
        "handlers": [],
        "tasks": [
            {
                "file": "main.yml",
                "tasks": [{}, {}],
                "mermaid": [
                    {"name": "static", "import_tasks": "sub.yml"},
                    {"name": "dyn", "import_tasks": "{{ variant }}stig/main.yml"},
                ],
            },
            {"file": "sub.yml", "tasks": [{}], "mermaid": [{"debug": {}}]},
            {"file": "stig/main.yml", "tasks": [{}], "mermaid": [{"debug": {}}]},
            {"file": "never_referenced.yml", "tasks": [{}], "mermaid": [{"debug": {}}]},
        ],
    }
    phases = build_role_execution_graph(role_info).execution_phases()
    kinds = [p["kind"] for p in phases]
    # every file is classified, and the three tiers partition exactly the files
    assert len(phases) == 4
    assert kinds.count("unreachable") == 1  # never_referenced.yml
    assert kinds.count("dynamic") == 1  # stig/main.yml reached via templated include
    assert "entrypoint" in kinds and "static" in kinds
