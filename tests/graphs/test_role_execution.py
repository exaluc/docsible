"""Tests for the source-backed role execution graph."""

from docsible.graphs import EdgeKind, ResolutionStatus, build_role_execution_graph


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
