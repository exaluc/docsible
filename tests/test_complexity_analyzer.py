"""
Unit tests for complexity analyzer.

Tests complexity classification, integration detection, and recommendation generation.
"""

from docsible.analyzers.complexity_analyzer import (
    ComplexityCategory,
    ComplexityMetrics,
    IntegrationPoint,
    IntegrationType,
    analyze_role_complexity,
    classify_complexity,
    detect_integrations,
    generate_recommendations,
)
from docsible.analyzers.patterns.detectors import ComplexityDetector

# Test Fixtures


def create_simple_role_info():
    """Create role info for a simple role (5 tasks)."""
    return {
        "name": "simple_role",
        "tasks": [
            {
                "file": "main.yml",
                "tasks": [
                    {"name": "Install package", "module": "apt", "when": None},
                    {"name": "Start service", "module": "service"},
                    {"name": "Copy config", "module": "copy"},
                    {"name": "Set fact", "module": "set_fact"},
                    {"name": "Debug output", "module": "debug"},
                ],
            }
        ],
        "handlers": [],
        "meta": {"dependencies": []},
    }


def create_medium_role_info():
    """Create role info for a medium role (15 tasks)."""
    return {
        "name": "medium_role",
        "tasks": [
            {
                "file": "main.yml",
                "tasks": [
                    {
                        "name": f"Task {i}",
                        "module": "debug",
                        "when": "i % 3 == 0" if i % 3 == 0 else None,
                    }
                    for i in range(10)
                ],
            },
            {
                "file": "setup.yml",
                "tasks": [
                    {"name": f"Setup task {i}", "module": "command"} for i in range(5)
                ],
            },
        ],
        "handlers": [
            {"name": "restart nginx", "module": "service"},
            {"name": "reload nginx", "module": "service"},
        ],
        "meta": {
            "dependencies": [
                {"role": "common"},
                {"role": "firewall"},
            ]
        },
    }


def create_complex_role_info():
    """Create role info for a complex role (30 tasks)."""
    return {
        "name": "complex_role",
        "tasks": [
            {
                "file": "main.yml",
                "tasks": [
                    {
                        "name": f"Main task {i}",
                        "module": "debug",
                        "when": "i % 2 == 0" if i % 2 == 0 else None,
                    }
                    for i in range(15)
                ],
            },
            {
                "file": "database.yml",
                "tasks": [
                    {
                        "name": "Create database",
                        "module": "postgresql_db",
                        "username": "admin",
                    },
                    {
                        "name": "Create user",
                        "module": "postgresql_user",
                        "password": "secret",
                    },
                    {"name": "Grant privileges", "module": "postgresql_privs"},
                ],
            },
            {
                "file": "api.yml",
                "tasks": [
                    {"name": "Check API", "module": "uri", "url_username": "api_user"},
                    {"name": "Fetch data", "module": "get_url", "token": "abc123"},
                    {"name": "Process response", "module": "debug"},
                ],
            },
            {
                "file": "vault.yml",
                "tasks": [
                    {
                        "name": "Get secret",
                        "module": "hashi_vault",
                        "vault_token": "token123",
                    },
                    {
                        "name": "Set secret",
                        "module": "community.hashi_vault.vault_write",
                    },
                ],
            },
            {
                "file": "orchestration.yml",
                "tasks": [
                    {
                        "name": "Include common tasks",
                        "module": "include_tasks",
                        "file": "common.yml",
                    },
                    {"name": "Import role", "module": "import_role", "role": "base"},
                    {
                        "name": "Include another role",
                        "module": "ansible.builtin.include_role",
                        "role": "utils",
                    },
                    {
                        "name": "Import more tasks",
                        "module": "ansible.builtin.import_tasks",
                        "file": "cleanup.yml",
                    },
                    {"name": "Regular task", "module": "debug"},
                    {"name": "Another task", "module": "copy"},
                    {"name": "Final task", "module": "template"},
                ],
                "mermaid": [
                    {"name": "Include common tasks", "include_tasks": "common.yml"},
                    {"name": "Import role", "import_role": {"name": "base"}},
                    {"name": "Include another role", "ansible.builtin.include_role": {"name": "utils"}},
                    {"name": "Import more tasks", "ansible.builtin.import_tasks": "cleanup.yml"},
                    {"name": "Regular task", "debug": {}},
                    {"name": "Another task", "copy": {}},
                    {"name": "Final task", "template": {}},
                ],
            },
        ],
        "handlers": [
            {"name": "restart app", "module": "systemd"},
            {"name": "reload config", "module": "service"},
            {"name": "clear cache", "module": "command"},
        ],
        "meta": {
            "dependencies": [
                {"role": "base"},
                {"role": "security"},
                {"role": "monitoring"},
            ]
        },
    }


# Tests for classify_complexity()


def test_classify_simple_role():
    """Test classification of simple role (1-10 tasks)."""
    metrics = ComplexityMetrics(
        total_tasks=8,
        task_files=1,
        handlers=0,
        conditional_tasks=2,
        max_tasks_per_file=8,
        avg_tasks_per_file=8.0,
    )
    assert classify_complexity(metrics) == ComplexityCategory.SIMPLE


def test_classify_medium_role():
    """Test classification of medium role (11-25 tasks)."""
    metrics = ComplexityMetrics(
        total_tasks=18,
        task_files=2,
        handlers=1,
        conditional_tasks=5,
        max_tasks_per_file=12,
        avg_tasks_per_file=9.0,
    )
    assert classify_complexity(metrics) == ComplexityCategory.MEDIUM


def test_classify_complex_role():
    """Test classification of complex role (25+ tasks)."""
    metrics = ComplexityMetrics(
        total_tasks=30,
        task_files=4,
        handlers=3,
        conditional_tasks=15,
        max_tasks_per_file=15,
        avg_tasks_per_file=7.5,
    )
    assert classify_complexity(metrics) == ComplexityCategory.COMPLEX


def test_classify_boundary_conditions():
    """Test boundary conditions for complexity classification."""
    # Exactly 10 tasks = SIMPLE
    metrics_10 = ComplexityMetrics(
        total_tasks=10,
        task_files=1,
        handlers=0,
        conditional_tasks=0,
        max_tasks_per_file=10,
        avg_tasks_per_file=10.0,
    )
    assert classify_complexity(metrics_10) == ComplexityCategory.SIMPLE

    # Exactly 11 tasks = MEDIUM
    metrics_11 = ComplexityMetrics(
        total_tasks=11,
        task_files=1,
        handlers=0,
        conditional_tasks=0,
        max_tasks_per_file=11,
        avg_tasks_per_file=11.0,
    )
    assert classify_complexity(metrics_11) == ComplexityCategory.MEDIUM

    # Exactly 25 tasks = MEDIUM
    metrics_25 = ComplexityMetrics(
        total_tasks=25,
        task_files=2,
        handlers=0,
        conditional_tasks=0,
        max_tasks_per_file=15,
        avg_tasks_per_file=12.5,
    )
    assert classify_complexity(metrics_25) == ComplexityCategory.MEDIUM

    # Exactly 26 tasks = COMPLEX
    metrics_26 = ComplexityMetrics(
        total_tasks=26,
        task_files=2,
        handlers=0,
        conditional_tasks=0,
        max_tasks_per_file=16,
        avg_tasks_per_file=13.0,
    )
    assert classify_complexity(metrics_26) == ComplexityCategory.COMPLEX


# Tests for detect_integrations()


def test_detect_api_integration():
    """Test detection of API integrations."""
    role_info = {
        "tasks": [
            {
                "file": "api.yml",
                "tasks": [
                    {"name": "Call API", "module": "uri", "url_username": "user"},
                    {"name": "Download file", "module": "get_url", "token": "abc"},
                    {"name": "Process", "module": "debug"},
                ],
            }
        ],
    }

    integrations = detect_integrations(role_info)
    assert len(integrations) == 1
    assert integrations[0].type == IntegrationType.API
    assert integrations[0].system_name == "REST APIs"
    assert integrations[0].task_count == 2
    assert integrations[0].uses_credentials is True
    assert "uri" in integrations[0].modules_used
    assert "get_url" in integrations[0].modules_used


def test_detect_database_integration():
    """Test detection of database integrations."""
    role_info = {
        "tasks": [
            {
                "file": "database.yml",
                "tasks": [
                    {"name": "Create DB", "module": "postgresql_db"},
                    {
                        "name": "Create user",
                        "module": "postgresql_user",
                        "password": "secret",
                    },
                    {
                        "name": "Grant access",
                        "module": "community.postgresql.postgresql_privs",
                    },
                ],
            }
        ],
    }

    integrations = detect_integrations(role_info)
    assert len(integrations) == 1
    assert integrations[0].type == IntegrationType.DATABASE
    assert "PostgreSQL" in integrations[0].system_name
    assert integrations[0].task_count == 3
    assert integrations[0].uses_credentials is True


def test_detect_vault_integration():
    """Test detection of HashiCorp Vault integrations."""
    role_info = {
        "tasks": [
            {
                "file": "secrets.yml",
                "tasks": [
                    {
                        "name": "Read secret",
                        "module": "hashi_vault",
                        "vault_token": "token",
                    },
                    {
                        "name": "Write secret",
                        "module": "community.hashi_vault.vault_write",
                    },
                ],
            }
        ],
    }

    integrations = detect_integrations(role_info)
    assert len(integrations) == 1
    assert integrations[0].type == IntegrationType.VAULT
    assert integrations[0].system_name == "HashiCorp Vault"
    assert integrations[0].task_count == 2
    assert integrations[0].uses_credentials is True


def test_detect_multiple_integrations():
    """Test detection of multiple integration types."""
    role_info = {
        "tasks": [
            {
                "file": "main.yml",
                "tasks": [
                    {"name": "API call", "module": "uri"},
                    {
                        "name": "DB query",
                        "module": "mysql_db",
                        "login_password": "pass",
                    },
                    {"name": "Vault read", "module": "hashi_vault"},
                    {"name": "Regular task", "module": "debug"},
                ],
            }
        ],
    }

    integrations = detect_integrations(role_info)
    assert len(integrations) == 3

    types = {i.type for i in integrations}
    assert IntegrationType.API in types
    assert IntegrationType.DATABASE in types
    assert IntegrationType.VAULT in types


def test_exclude_composition_modules():
    """Test that role/task composition modules are excluded from integrations."""
    role_info = {
        "tasks": [
            {
                "file": "main.yml",
                "tasks": [
                    {
                        "name": "Include role",
                        "module": "include_role",
                        "role": "common",
                    },
                    {"name": "Import role", "module": "import_role", "role": "base"},
                    {
                        "name": "Include tasks",
                        "module": "include_tasks",
                        "file": "setup.yml",
                    },
                    {
                        "name": "Import tasks",
                        "module": "ansible.builtin.import_tasks",
                        "file": "cleanup.yml",
                    },
                    {"name": "API call", "module": "uri"},  # This should be detected
                ],
            }
        ],
    }

    integrations = detect_integrations(role_info)
    # Only the API call should be detected, not the composition modules
    assert len(integrations) == 1
    assert integrations[0].type == IntegrationType.API


def test_detect_no_integrations():
    """Test role with no external integrations."""
    role_info = {
        "tasks": [
            {
                "file": "main.yml",
                "tasks": [
                    {"name": "Install package", "module": "apt"},
                    {"name": "Copy file", "module": "copy"},
                    {"name": "Template config", "module": "template"},
                ],
            }
        ],
    }

    integrations = detect_integrations(role_info)
    assert len(integrations) == 0


# Tests for analyze_role_complexity()


def test_analyze_simple_role():
    """Test complete analysis of simple role."""
    role_info = create_simple_role_info()
    report = analyze_role_complexity(role_info)

    assert report.category == ComplexityCategory.SIMPLE
    assert report.metrics.total_tasks == 5
    assert report.metrics.task_files == 1
    assert report.metrics.handlers == 0
    assert len(report.integration_points) == 0
    assert len(report.recommendations) > 0


def test_analyze_medium_role():
    """Test complete analysis of medium role."""
    role_info = create_medium_role_info()
    report = analyze_role_complexity(role_info)

    assert report.category == ComplexityCategory.MEDIUM
    assert report.metrics.total_tasks == 15
    assert report.metrics.task_files == 2
    assert report.metrics.handlers == 2
    assert report.metrics.role_dependencies == 2
    assert report.metrics.composition_score == 4  # 2 dependencies * 2
    assert len(report.task_files_detail) == 2


def test_analyze_complex_role():
    """Test complete analysis of complex role."""
    role_info = create_complex_role_info()
    report = analyze_role_complexity(role_info)

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
                "mermaid": [
                    {"name": "Task 1", "debug": {}, "when": "condition1"},
                    {"name": "Task 2", "debug": {}, "when": "condition2"},
                    {"name": "Task 3", "debug": {}},
                    {"name": "Task 4", "debug": {}},
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


# Tests for generate_recommendations()


def test_recommendations_for_complex_role():
    """Test recommendations for complex role."""
    metrics = ComplexityMetrics(
        total_tasks=35,
        task_files=3,
        handlers=2,
        conditional_tasks=15,
        max_tasks_per_file=20,
        avg_tasks_per_file=11.7,
    )

    recommendations = generate_recommendations(
        metrics, ComplexityCategory.COMPLEX, [],
        file_details=[], hotspots=[], inflection_points=[], role_info={"tasks": []}
    )

    assert len(recommendations) >= 2
    assert any("complex" in rec.lower() for rec in recommendations)
    assert any("20 tasks" in rec for rec in recommendations)


def test_recommendations_for_high_composition():
    """Test recommendations for high composition complexity."""
    metrics = ComplexityMetrics(
        total_tasks=15,
        task_files=2,
        handlers=1,
        conditional_tasks=3,
        role_dependencies=5,
        role_includes=2,
        task_includes=1,
        max_tasks_per_file=8,
        avg_tasks_per_file=7.5,
    )

    recommendations = generate_recommendations(
        metrics, ComplexityCategory.MEDIUM, [],
        file_details=[], hotspots=[], inflection_points=[], role_info={"tasks": []}
    )

    # Composition score = (5*2) + 2 + 1 = 13 (>= 8, so should recommend documenting dependencies)
    assert any("composition" in rec.lower() for rec in recommendations)
    assert any("dependencies" in rec.lower() for rec in recommendations)


def test_recommendations_for_multiple_integrations():
    """Test recommendations for multiple external integrations."""
    metrics = ComplexityMetrics(
        total_tasks=20,
        task_files=2,
        handlers=1,
        conditional_tasks=5,
        external_integrations=4,
        max_tasks_per_file=12,
        avg_tasks_per_file=10.0,
    )

    integration_points = [
        IntegrationPoint(
            type=IntegrationType.API,
            system_name="REST API",
            modules_used=["uri"],
            task_count=2,
            uses_credentials=True,
        ),
        IntegrationPoint(
            type=IntegrationType.DATABASE,
            system_name="PostgreSQL",
            modules_used=["postgresql_db"],
            task_count=3,
            uses_credentials=True,
        ),
        IntegrationPoint(
            type=IntegrationType.VAULT,
            system_name="Vault",
            modules_used=["hashi_vault"],
            task_count=1,
            uses_credentials=True,
        ),
        IntegrationPoint(
            type=IntegrationType.API,
            system_name="GraphQL API",
            modules_used=["uri"],
            task_count=1,
            uses_credentials=False,
        ),
    ]

    recommendations = generate_recommendations(
        metrics, ComplexityCategory.MEDIUM, integration_points,
        file_details=[], hotspots=[], inflection_points=[], role_info={"tasks": []}
    )

    # Should recommend architecture diagram for multiple integrations
    assert any("integration" in rec.lower() for rec in recommendations)
    assert any("architecture diagram" in rec.lower() for rec in recommendations)


def test_recommendations_for_credentials():
    """Test recommendations when external systems require credentials."""
    metrics = ComplexityMetrics(
        total_tasks=12,
        task_files=2,
        handlers=0,
        conditional_tasks=2,
        external_integrations=1,
        max_tasks_per_file=6,
        avg_tasks_per_file=6.0,
    )

    from docsible.analyzers.complexity_analyzer import IntegrationPoint

    integration_points = [
        IntegrationPoint(
            type=IntegrationType.DATABASE,
            system_name="PostgreSQL",
            modules_used=["postgresql_db"],
            task_count=3,
            uses_credentials=True,
        )
    ]

    recommendations = generate_recommendations(
        metrics, ComplexityCategory.MEDIUM, integration_points,
        file_details=[], hotspots=[], inflection_points=[], role_info={"tasks": []}
    )

    assert any(
        "credentials" in rec.lower() or "authentication" in rec.lower()
        for rec in recommendations
    )


def test_recommendations_for_simple_role():
    """Test recommendations for manageable simple role."""
    metrics = ComplexityMetrics(
        total_tasks=8,
        task_files=1,
        handlers=1,
        conditional_tasks=2,
        max_tasks_per_file=8,
        avg_tasks_per_file=8.0,
    )

    recommendations = generate_recommendations(
        metrics, ComplexityCategory.SIMPLE, [],
        file_details=[], hotspots=[], inflection_points=[], role_info={"tasks": []}
    )

    # Should indicate role is manageable
    assert any(
        "manageable" in rec.lower() or "standard" in rec.lower()
        for rec in recommendations
    )


# Edge Cases


def test_empty_role():
    """Test analysis of role with no tasks."""
    role_info = {
        "name": "empty_role",
        "tasks": [],
        "handlers": [],
        "meta": {"dependencies": []},
    }

    report = analyze_role_complexity(role_info)
    assert report.category == ComplexityCategory.SIMPLE  # 0 tasks <= 10
    assert report.metrics.total_tasks == 0
    assert report.metrics.conditional_percentage == 0.0


def test_role_with_empty_task_files():
    """Test role with task files that have no tasks."""
    role_info = {
        "name": "test_role",
        "tasks": [
            {"file": "empty.yml", "tasks": []},
            {"file": "main.yml", "tasks": [{"name": "Task 1", "module": "debug"}]},
        ],
        "handlers": [],
        "meta": {"dependencies": []},
    }

    report = analyze_role_complexity(role_info)
    assert report.metrics.total_tasks == 1
    assert report.metrics.task_files == 2
    assert report.metrics.max_tasks_per_file == 1

def test_calculate_include_depth_simple():
    """Test depth calculation for simple linear chain."""
    detector = ComplexityDetector()
    
    include_graph = {
        "main.yml": ["setup.yml"],
        "setup.yml": ["install.yml"],
        "install.yml": []
    }
    
    depth = detector._calculate_max_include_depth(include_graph, "main.yml", set())
    assert depth == 3

#FIXME Either change implementation and have depth == 1
# Assumption test Depth = 1, number of include layers before recursion becomes unsafe
# Assumption function Depth = 2, number of unique files reachable before hitting a cycle
def test_calculate_include_depth_with_cycle():
    """Test cycle detection."""
    detector = ComplexityDetector()
    
    include_graph = {
        "main.yml": ["setup.yml"],
        "setup.yml": ["main.yml"]  # Cycle!
    }
    
    depth = detector._calculate_max_include_depth(include_graph, "main.yml", set())
    assert depth == 2  # Should detect cycle and stop
