"""Tests for complete role analysis."""

from docsible.analyzers.complexity_analyzer import (
    ComplexityCategory,
    analyze_role_complexity,
)


def test_analyze_simple_role(simple_role_info):
    """Test complete analysis of simple role."""
    report = analyze_role_complexity(simple_role_info)

    assert report.category == ComplexityCategory.SIMPLE
    assert report.metrics.total_tasks == 5
    assert report.metrics.task_files == 1
    assert report.metrics.handlers == 0
    assert len(report.integration_points) == 0
    assert len(report.recommendations) > 0


def test_analyze_medium_role(medium_role_info):
    """Test complete analysis of medium role."""
    report = analyze_role_complexity(medium_role_info)

    assert report.category == ComplexityCategory.MEDIUM
    assert report.metrics.total_tasks == 15
    assert report.metrics.task_files == 2
    assert report.metrics.handlers == 2
    assert report.metrics.role_dependencies == 2
    assert report.metrics.composition_score == 4  # 2 dependencies * 2
    assert len(report.task_files_detail) == 2


def test_analyze_complex_role(complex_role_info):
    """Test complete analysis of complex role."""
    report = analyze_role_complexity(complex_role_info)

    assert report.category == ComplexityCategory.COMPLEX
    assert report.metrics.total_tasks == 30
    assert report.metrics.task_files == 5
    assert report.metrics.handlers == 3
    assert report.metrics.role_dependencies == 3
    assert report.metrics.role_includes == 2  # import_role, include_role
    assert report.metrics.task_includes == 2  # include_tasks, import_tasks
    assert report.metrics.composition_score == 10  # (3*2) + 2 + 2
    assert len(report.integration_points) == 3  # API, Database, Vault
    assert report.metrics.external_integrations == 3


def test_analyze_conditional_percentage():
    """Test conditional percentage calculation."""
    role_info = {
        "name": "test_role",
        "tasks": [
            {
                "file": "main.yml",
                "tasks": [
                    {"name": "Task 1", "module": "debug", "when": "condition1"},
                    {"name": "Task 2", "module": "debug", "when": "condition2"},
                    {"name": "Task 3", "module": "debug"},  # No condition
                    {"name": "Task 4", "module": "debug"},  # No condition
                ],
            }
        ],
        "handlers": [],
        "meta": {"dependencies": []},
    }

    report = analyze_role_complexity(role_info)
    assert report.metrics.conditional_tasks == 2
    assert report.metrics.conditional_percentage == 50.0  # 2 out of 4


def test_analyze_max_and_avg_tasks():
    """Test max and average tasks per file calculation."""
    role_info = {
        "name": "test_role",
        "tasks": [
            {
                "file": "file1.yml",
                "tasks": [{"name": f"Task {i}", "module": "debug"} for i in range(10)],
            },
            {
                "file": "file2.yml",
                "tasks": [{"name": f"Task {i}", "module": "debug"} for i in range(5)],
            },
            {
                "file": "file3.yml",
                "tasks": [{"name": f"Task {i}", "module": "debug"} for i in range(15)],
            },
        ],
        "handlers": [],
        "meta": {"dependencies": []},
    }

    report = analyze_role_complexity(role_info)
    assert report.metrics.total_tasks == 30
    assert report.metrics.task_files == 3
    assert report.metrics.max_tasks_per_file == 15
    assert report.metrics.avg_tasks_per_file == 10.0  # (10+5+15)/3


def test_task_includes_is_graph_authoritative_and_counts_legacy_include():
    """Regression: boundary counts come from the RoleExecutionGraph, not a
    separate flattened-task regex that missed the legacy bare `include:`
    keyword (candidate 9 reported 0 despite 20 include boundaries)."""
    role_info = {
        "name": "legacy",
        "defaults": [],
        "vars": [],
        "handlers": [],
        "tasks": [
            {
                "file": "main.yml",
                "tasks": [
                    {"name": "inc", "module": "include", "type": "task", "when": None}
                ],
                "mermaid": [{"name": "inc", "include": "sub.yml"}],
            },
            {
                "file": "sub.yml",
                "tasks": [{"name": "d", "module": "debug", "type": "task", "when": None}],
                "mermaid": [{"name": "d", "debug": {}}],
            },
        ],
    }
    metrics = analyze_role_complexity(role_info).metrics
    assert metrics.task_includes == 1  # bare include: counted via the graph
    assert metrics.role_includes == 0
