"""Tests for adaptive documentation based on complexity."""

from docsible.analyzers.complexity_analyzer import (
    ComplexityCategory,
    ComplexityMetrics,
    ComplexityReport,
    IntegrationPoint,
    IntegrationType,
)
from docsible.utils.template.loader import TemplateLoader


class TestAdaptiveDocumentation:
    """Test adaptive documentation rendering based on complexity."""

    def test_simple_role_uses_sequence_diagrams(self):
        """Test that SIMPLE roles use sequence diagrams in output."""
        loader = TemplateLoader()
        template = loader.get_template("role/sections/adaptive_diagrams.jinja2")

        complexity_report = ComplexityReport(
            metrics=ComplexityMetrics(
                total_tasks=5,
                task_files=1,
                handlers=0,
                conditional_tasks=1,
                max_tasks_per_file=5,
                avg_tasks_per_file=5.0,
            ),
            category=ComplexityCategory.SIMPLE,
            integration_points=[],
            recommendations=["Role complexity is manageable"],
        )

        result = template.render(
            complexity_report=complexity_report,
            sequence_diagram_detailed="sequenceDiagram\n    A->>B: Test",
            mermaid_code_per_file={"main.yml": "graph TD\n    A-->B"},
            simplify_diagrams=False,
        )

        # SIMPLE roles should show execution flow
        assert "## Execution Flow" in result
        assert "sequence diagram shows the linear task execution flow" in result
        assert "sequenceDiagram" in result

    def test_medium_role_uses_state_diagrams(self):
        """Test that MEDIUM roles use state transition diagrams."""
        loader = TemplateLoader()
        template = loader.get_template("role/sections/adaptive_diagrams.jinja2")

        complexity_report = ComplexityReport(
            metrics=ComplexityMetrics(
                total_tasks=15,
                task_files=2,
                handlers=1,
                conditional_tasks=5,
                max_tasks_per_file=10,
                avg_tasks_per_file=7.5,
            ),
            category=ComplexityCategory.MEDIUM,
            integration_points=[],
            recommendations=[],
        )

        result = template.render(
            complexity_report=complexity_report,
            state_diagram="stateDiagram-v2\n    [*] --> Install",
            sequence_diagram_detailed="sequenceDiagram\n    A->>B: Test",
            mermaid_code_per_file={"main.yml": "graph TD\n    A-->B"},
            simplify_diagrams=False,
        )

        # MEDIUM roles should show workflow phases
        assert "## Workflow Phases" in result
        assert "state diagram shows the role's execution phases" in result
        assert "stateDiagram" in result
        # Should also show detailed execution
        assert "## Detailed Execution Sequence" in result
        # Should show component hierarchy
        assert "## Component Hierarchy" in result

    def test_complex_role_shows_architecture_overview(self):
        """Test that COMPLEX roles show architecture + text documentation."""
        loader = TemplateLoader()
        template = loader.get_template("role/sections/adaptive_diagrams.jinja2")

        complexity_report = ComplexityReport(
            metrics=ComplexityMetrics(
                total_tasks=30,
                task_files=5,
                handlers=3,
                conditional_tasks=15,
                max_tasks_per_file=10,
                avg_tasks_per_file=6.0,
            ),
            category=ComplexityCategory.COMPLEX,
            integration_points=[],
            recommendations=[
                "Role is complex (30 tasks) - consider splitting by concern",
                "Document decision points in README",
            ],
            task_files_detail=[
                {"file": "install.yml", "task_count": 8, "has_integrations": 0},
                {"file": "configure.yml", "task_count": 12, "has_integrations": 0},
            ],
        )

        result = template.render(
            complexity_report=complexity_report,
            sequence_diagram_high_level="sequenceDiagram\n    A->>B: High Level",
            simplify_diagrams=False,
        )

        # COMPLEX roles should show architecture overview
        assert "## Architecture Overview" in result
        assert "### Role Components" in result
        assert "30 tasks" in result
        assert "### Execution Routes" in result
        assert "Entry point: install.yml" in result
        assert "Static continuation: configure.yml" in result
        # Should show recommendations
        assert "### Recommendations" in result
        assert "Role is complex" in result

    def test_complex_role_with_integrations(self):
        """Test COMPLEX role documentation with external integrations."""
        loader = TemplateLoader()
        template = loader.get_template("role/sections/adaptive_diagrams.jinja2")

        integrations = [
            IntegrationPoint(
                type=IntegrationType.API,
                system_name="REST APIs",
                modules_used=["uri", "get_url"],
                task_count=5,
                uses_credentials=True,
            ),
            IntegrationPoint(
                type=IntegrationType.DATABASE,
                system_name="PostgreSQL Database",
                modules_used=["postgresql_db"],
                task_count=3,
                uses_credentials=True,
            ),
        ]

        complexity_report = ComplexityReport(
            metrics=ComplexityMetrics(
                total_tasks=30,
                task_files=3,
                handlers=2,
                conditional_tasks=10,
                external_integrations=2,
                max_tasks_per_file=15,
                avg_tasks_per_file=10.0,
            ),
            category=ComplexityCategory.COMPLEX,
            integration_points=integrations,
            recommendations=[
                "Multiple external integrations (2 systems) - add integration architecture diagram"
            ],
            task_files_detail=[],
        )

        result = template.render(
            complexity_report=complexity_report, simplify_diagrams=False
        )

        # Should show integrations section
        assert "### External Integrations" in result
        assert "2 external system(s)" in result
        assert "REST APIs" in result
        assert "PostgreSQL Database" in result
        assert "⚠️ Requires credentials" in result

    def test_fallback_when_no_complexity_report(self):
        """Test fallback to standard diagrams when no complexity report."""
        loader = TemplateLoader()
        template = loader.get_template("role/sections/adaptive_diagrams.jinja2")

        result = template.render(
            complexity_report=None,
            state_diagram="stateDiagram-v2\n    [*] --> Done",
            mermaid_code_per_file={"main.yml": "graph TD\n    A --> B"},
        )

        # Should include the fallback standard diagrams
        # (The fallback includes sections/diagrams.jinja2)
        assert "stateDiagram" in result

    def test_integration_boundary_section(self):
        """Test integration boundary section rendering."""
        loader = TemplateLoader()
        template = loader.get_template("role/sections/integration_boundary.jinja2")

        integrations = [
            IntegrationPoint(
                type=IntegrationType.API,
                system_name="REST APIs",
                modules_used=["uri"],
                task_count=3,
                uses_credentials=True,
            )
        ]

        complexity_report = ComplexityReport(
            metrics=ComplexityMetrics(
                total_tasks=10,
                task_files=1,
                handlers=0,
                conditional_tasks=0,
                external_integrations=1,
                max_tasks_per_file=10,
                avg_tasks_per_file=10.0,
            ),
            category=ComplexityCategory.SIMPLE,
            integration_points=integrations,
            recommendations=[],
        )

        result = template.render(
            integration_boundary_diagram="graph LR\n    Role-->API",
            complexity_report=complexity_report,
        )

        assert "## Integration Architecture" in result
        assert "graph LR" in result
        assert "### Integration Details" in result
        assert "REST APIs" in result
        assert "### Security Considerations" in result

    def test_no_integration_boundary_when_no_diagram(self):
        """Test that integration section is empty when no diagram."""
        loader = TemplateLoader()
        template = loader.get_template("role/sections/integration_boundary.jinja2")

        result = template.render(
            integration_boundary_diagram=None, complexity_report=None
        )

        # Should be empty/minimal
        assert result.strip() == ""
