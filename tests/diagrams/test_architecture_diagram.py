"""Tests for component architecture diagram generation."""

from docsible.analyzers.complexity_analyzer import (
    ComplexityCategory,
    ComplexityMetrics,
    ComplexityReport,
    IntegrationPoint,
    IntegrationType,
)
from docsible.diagrams.types.architecture import (
    generate_component_architecture,
    should_generate_architecture_diagram,
)


class TestArchitectureDiagram:
    """Test component architecture diagram generation."""

    def test_generate_with_simple_role(self):
        """Test diagram generation for simple role structure."""
        role_info = {
            "name": "test_role",
            "defaults": [
                {"file": "main.yml", "data": {"var1": "value1", "var2": "value2"}}
            ],
            "vars": [],
            "tasks": [
                {"file": "main.yml", "tasks": [{"name": "Task 1"}, {"name": "Task 2"}]}
            ],
            "handlers": [],
        }

        complexity_report = ComplexityReport(
            metrics=ComplexityMetrics(
                total_tasks=2,
                task_files=1,
                handlers=0,
                conditional_tasks=0,
                max_tasks_per_file=2,
                avg_tasks_per_file=2.0,
            ),
            category=ComplexityCategory.SIMPLE,
            integration_points=[],
        )

        diagram = generate_component_architecture(role_info, complexity_report)

        assert diagram is not None
        assert "graph TB" in diagram
        assert "defaults" in diagram
        assert "2 variables" in diagram
        assert "tasks_main_yml" in diagram
        assert "2 tasks" in diagram
        assert "varStyle" in diagram
        assert "taskStyle" in diagram

    def test_generate_with_vars_only(self):
        """Test diagram with vars but no defaults."""
        role_info = {
            "name": "test_role",
            "defaults": [],
            "vars": [
                {
                    "file": "main.yml",
                    "data": {"var1": "val1", "var2": "val2", "var3": "val3"},
                }
            ],
            "tasks": [{"file": "main.yml", "tasks": [{"name": "Task 1"}]}],
            "handlers": [],
        }

        complexity_report = ComplexityReport(
            metrics=ComplexityMetrics(
                total_tasks=1,
                task_files=1,
                handlers=0,
                conditional_tasks=0,
                max_tasks_per_file=1,
                avg_tasks_per_file=1.0,
            ),
            category=ComplexityCategory.SIMPLE,
            integration_points=[],
        )

        diagram = generate_component_architecture(role_info, complexity_report)

        assert diagram is not None
        assert "vars" in diagram
        assert "3 variables" in diagram
        assert "defaults" not in diagram  # No defaults section

    def test_generate_with_multiple_task_files(self):
        """Test diagram with multiple task files."""
        role_info = {
            "name": "test_role",
            "defaults": [{"file": "main.yml", "data": {"var1": "value1"}}],
            "vars": [],
            "tasks": [
                {"file": "install.yml", "tasks": [{"name": "Install package"}] * 5},
                {"file": "configure.yml", "tasks": [{"name": "Configure app"}] * 10},
                {"file": "validate.yml", "tasks": [{"name": "Validate config"}] * 3},
            ],
            "handlers": [],
        }

        complexity_report = ComplexityReport(
            metrics=ComplexityMetrics(
                total_tasks=18,
                task_files=3,
                handlers=0,
                conditional_tasks=5,
                max_tasks_per_file=10,
                avg_tasks_per_file=6.0,
            ),
            category=ComplexityCategory.MEDIUM,
            integration_points=[],
        )

        diagram = generate_component_architecture(role_info, complexity_report)

        assert diagram is not None
        assert "tasks_install_yml" in diagram
        assert "tasks_configure_yml" in diagram
        assert "tasks_validate_yml" in diagram
        assert "5 tasks" in diagram
        assert "10 tasks" in diagram
        assert "3 tasks" in diagram
        # No include data: no inter-file flow edges should be fabricated
        assert "tasks_install_yml --> tasks_validate_yml" not in diagram

    def test_generate_with_handlers(self):
        """Test diagram with handlers."""
        role_info = {
            "name": "test_role",
            "defaults": [],
            "vars": [],
            "tasks": [
                {"file": "main.yml", "tasks": [{"name": "Task 1"}, {"name": "Task 2"}]}
            ],
            "handlers": [
                {"name": "restart service", "module": "service"},
                {"name": "reload config", "module": "command"},
            ],
        }

        complexity_report = ComplexityReport(
            metrics=ComplexityMetrics(
                total_tasks=2,
                task_files=1,
                handlers=2,
                conditional_tasks=0,
                max_tasks_per_file=2,
                avg_tasks_per_file=2.0,
            ),
            category=ComplexityCategory.SIMPLE,
            integration_points=[],
        )

        diagram = generate_component_architecture(role_info, complexity_report)

        assert diagram is not None
        assert "handlers" in diagram
        assert "2 handlers" in diagram
        assert "notify" in diagram
        assert "handlerStyle" in diagram

    def test_generate_with_external_integrations(self):
        """Test diagram with external system integrations."""
        role_info = {
            "name": "test_role",
            "defaults": [],
            "vars": [],
            "tasks": [
                {
                    "file": "api_calls.yml",
                    "tasks": [
                        {"name": "Call API", "module": "uri"},
                        {"name": "Download file", "module": "get_url"},
                    ],
                }
            ],
            "handlers": [],
        }

        integration_points = [
            IntegrationPoint(
                type=IntegrationType.API,
                system_name="REST APIs",
                modules_used=["uri", "get_url"],
                task_count=2,
                uses_credentials=True,
            )
        ]

        complexity_report = ComplexityReport(
            metrics=ComplexityMetrics(
                total_tasks=2,
                task_files=1,
                handlers=0,
                conditional_tasks=0,
                external_integrations=1,
                max_tasks_per_file=2,
                avg_tasks_per_file=2.0,
            ),
            category=ComplexityCategory.SIMPLE,
            integration_points=integration_points,
        )

        diagram = generate_component_architecture(role_info, complexity_report)

        assert diagram is not None
        assert "external" in diagram
        assert "External Systems" in diagram
        assert "REST APIs" in diagram
        assert "externalStyle" in diagram
        # Should show connection from tasks to external
        assert "tasks_api_calls_yml --> external" in diagram

    def test_generate_complex_role_full_diagram(self):
        """Test diagram for complex role with all components."""
        role_info = {
            "name": "complex_role",
            "defaults": [
                {
                    "file": "main.yml",
                    "data": {"var" + str(i): f"val{i}" for i in range(15)},
                }
            ],
            "vars": [
                {
                    "file": "main.yml",
                    "data": {"var" + str(i): f"val{i}" for i in range(8)},
                }
            ],
            "tasks": [
                {
                    "file": "install.yml",
                    "tasks": [
                        {"name": f"Task {i}", "module": "package"} for i in range(11)
                    ]
                    + [
                        {
                            "name": "Include configure",
                            "module": "include_tasks",
                            "include_target": "configure.yml",
                        }
                    ],
                },
                {
                    "file": "configure.yml",
                    "tasks": [
                        {"name": f"Task {i}", "module": "uri"} for i in range(18)
                    ],
                },
            ],
            "handlers": [
                {"name": "restart app", "module": "service"},
                {"name": "reload config", "module": "command"},
                {"name": "notify admin", "module": "mail"},
            ],
        }

        integration_points = [
            IntegrationPoint(
                type=IntegrationType.API,
                system_name="REST APIs",
                modules_used=["uri"],
                task_count=18,
                uses_credentials=False,
            )
        ]

        complexity_report = ComplexityReport(
            metrics=ComplexityMetrics(
                total_tasks=30,
                task_files=2,
                handlers=3,
                conditional_tasks=10,
                external_integrations=1,
                max_tasks_per_file=18,
                avg_tasks_per_file=15.0,
            ),
            category=ComplexityCategory.COMPLEX,
            integration_points=integration_points,
        )

        diagram = generate_component_architecture(role_info, complexity_report)

        assert diagram is not None
        # Check all major sections present
        assert "subgraph Variables" in diagram
        assert "subgraph Tasks" in diagram
        assert "15 variables" in diagram
        assert "8 variables" in diagram
        assert "12 tasks" in diagram
        assert "18 tasks" in diagram
        assert "3 handlers" in diagram
        assert "REST APIs" in diagram
        # Check data flow (variables flow to first task file)
        assert "defaults --> tasks_install_yml" in diagram
        assert "vars --> tasks_install_yml" in diagram
        # Statically resolvable include becomes a labeled edge
        assert 'tasks_install_yml -."includes".-> tasks_configure_yml' in diagram
        assert "notify" in diagram
        assert "tasks_configure_yml --> external" in diagram

    def test_generate_with_include_edges(self):
        """Include/import targets become edges; templated targets are skipped."""
        role_info = {
            "name": "test_role",
            "defaults": [],
            "vars": [],
            "tasks": [
                {
                    "file": "main.yml",
                    "tasks": [
                        {"name": "Load OS vars", "module": "include_vars"},
                        {
                            "name": "Unnamed",
                            "module": "include_tasks",
                            "include_target": "{{ ansible_facts['os_family'] }}.yml",
                        },
                        {
                            "name": "Unnamed",
                            "module": "import_tasks",
                            "include_target": "setup.yml",
                        },
                        {
                            "name": "Unnamed",
                            "module": "include",
                            "include_target": "extra.yml",
                        },
                    ],
                },
                {"file": "setup.yml", "tasks": [{"name": "Setup"}]},
                {"file": "subdir/extra.yml", "tasks": [{"name": "Extra"}]},
                {"file": "orphan.yml", "tasks": [{"name": "Orphan"}]},
            ],
            "handlers": [],
        }

        complexity_report = ComplexityReport(
            metrics=ComplexityMetrics(
                total_tasks=7,
                task_files=4,
                handlers=0,
                conditional_tasks=0,
                max_tasks_per_file=4,
                avg_tasks_per_file=1.75,
            ),
            category=ComplexityCategory.SIMPLE,
            integration_points=[],
        )

        diagram = generate_component_architecture(role_info, complexity_report)

        assert diagram is not None
        # Exact-match target
        assert 'tasks_main_yml -."includes".-> tasks_setup_yml' in diagram
        # Basename match against nested file
        assert 'tasks_main_yml -."includes".-> tasks_subdir_extra_yml' in diagram
        # Templated target must not be drawn as an edge
        assert "os_family" not in diagram
        # No fabricated edges to unrelated files
        assert "--> tasks_orphan_yml" not in diagram

    def test_generate_with_no_role_info(self):
        """Test that None is returned when role_info is None."""
        diagram = generate_component_architecture(None, None)
        assert diagram is None

    def test_should_generate_for_complex_role(self):
        """Test decision logic for COMPLEX role."""
        complexity_report = ComplexityReport(
            metrics=ComplexityMetrics(
                total_tasks=30,
                task_files=5,
                handlers=2,
                conditional_tasks=10,
                max_tasks_per_file=10,
                avg_tasks_per_file=6.0,
            ),
            category=ComplexityCategory.COMPLEX,
            integration_points=[],
        )

        assert should_generate_architecture_diagram(complexity_report) is True

    def test_should_generate_for_medium_with_high_composition(self):
        """Test decision logic for MEDIUM role with high composition score."""
        complexity_report = ComplexityReport(
            metrics=ComplexityMetrics(
                total_tasks=15,
                task_files=3,
                handlers=1,
                conditional_tasks=5,
                role_dependencies=2,  # composition_score = 2*2 = 4
                role_includes=1,  # +1 = 5
                task_includes=0,
                max_tasks_per_file=7,
                avg_tasks_per_file=5.0,
            ),
            category=ComplexityCategory.MEDIUM,
            integration_points=[],
        )

        assert should_generate_architecture_diagram(complexity_report) is True

    def test_should_not_generate_for_simple_role(self):
        """Test decision logic for SIMPLE role."""
        complexity_report = ComplexityReport(
            metrics=ComplexityMetrics(
                total_tasks=5,
                task_files=1,
                handlers=0,
                conditional_tasks=0,
                max_tasks_per_file=5,
                avg_tasks_per_file=5.0,
            ),
            category=ComplexityCategory.SIMPLE,
            integration_points=[],
        )

        assert should_generate_architecture_diagram(complexity_report) is False

    def test_should_not_generate_for_medium_low_composition(self):
        """Test decision logic for MEDIUM role with low composition score."""
        complexity_report = ComplexityReport(
            metrics=ComplexityMetrics(
                total_tasks=12,
                task_files=2,
                handlers=1,
                conditional_tasks=3,
                role_dependencies=0,  # composition_score = 0
                role_includes=0,
                task_includes=0,
                max_tasks_per_file=7,
                avg_tasks_per_file=6.0,
            ),
            category=ComplexityCategory.MEDIUM,
            integration_points=[],
        )

        assert should_generate_architecture_diagram(complexity_report) is False

    def test_should_not_generate_with_no_report(self):
        """Test decision logic with no complexity report."""
        assert should_generate_architecture_diagram(None) is False

    def test_diagram_has_valid_mermaid_syntax(self):
        """Test that generated diagram has valid Mermaid syntax."""
        role_info = {
            "name": "test_role",
            "defaults": [{"file": "main.yml", "data": {"var1": "value1"}}],
            "vars": [],
            "tasks": [{"file": "main.yml", "tasks": [{"name": "Task 1"}]}],
            "handlers": [{"name": "handler1", "module": "service"}],
        }

        complexity_report = ComplexityReport(
            metrics=ComplexityMetrics(
                total_tasks=1,
                task_files=1,
                handlers=1,
                conditional_tasks=0,
                max_tasks_per_file=1,
                avg_tasks_per_file=1.0,
            ),
            category=ComplexityCategory.SIMPLE,
            integration_points=[],
        )

        diagram = generate_component_architecture(role_info, complexity_report)
        assert diagram is not None

        # Check basic Mermaid syntax
        assert diagram.startswith("graph TB")
        assert "subgraph" in diagram
        assert "end" in diagram
        assert "-->" in diagram or "-.notify.->" in diagram
        assert "classDef" in diagram
        assert "class" in diagram


def _role_info_with_files(files):
    return {
        "name": "r",
        "defaults": [],
        "vars": [],
        "handlers": [],
        "tasks": [{"file": name, "tasks": [{}] * n} for name, n in files],
    }


def _group_node_count(mermaid):
    return sum(
        1
        for line in mermaid.splitlines()
        if line.lstrip().startswith("group_") and "[" in line
    )


class TestGroupedOverviewBounding:
    """Regression tests for the flat-layout grouping failure found while
    re-running candidate 7 (os_hardening: 23 flat task files became 23
    'groups' -> an unreadable 100-line diagram). Nested layouts (candidate 5,
    9 directory groups) must stay untouched.
    """

    def test_flat_layout_is_bounded_with_other_bucket(self):
        from docsible.diagrams.types.architecture import _MAX_GROUP_NODES
        from docsible.graphs import build_role_execution_graph

        files = [("main.yml", 2)] + [(f"sec_{i}.yml", 1) for i in range(22)]
        role_info = _role_info_with_files(files)
        graph = build_role_execution_graph(role_info)

        mermaid = generate_component_architecture(
            role_info, None, execution_graph=graph
        )

        assert "Grouped execution overview" in mermaid
        assert "group_other[" in mermaid
        assert "13 task files" in mermaid  # 23 - entry - 9 largest folded into other
        assert _group_node_count(mermaid) <= _MAX_GROUP_NODES + 1
        assert '1 task file"' in mermaid  # singular for one-file groups
        assert "1 task files" not in mermaid  # no plural on a single file

    def test_nested_layout_within_cap_is_not_folded(self):
        from docsible.graphs import build_role_execution_graph

        files = [("main.yml", 1)] + [
            (f"dir_{d}/x{i}.yml", 1) for d in range(8) for i in range(3)
        ]  # 25 files (>20 -> grouped) but 8 directories + entry = 9 groups
        role_info = _role_info_with_files(files)
        graph = build_role_execution_graph(role_info)

        mermaid = generate_component_architecture(
            role_info, None, execution_graph=graph
        )

        assert "Grouped execution overview" in mermaid
        assert "group_other[" not in mermaid  # 9 groups <= cap -> no folding
        assert _group_node_count(mermaid) == 9  # entry + 8 directories
        assert "3 task files" in mermaid  # each directory keeps 3 files
