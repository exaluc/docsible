"""Tests for RoleOrchestrator class."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from docsible.commands.document_role.models import (
    AnalysisConfig,
    ContentFlags,
    DiagramConfig,
    PathConfig,
    ProcessingConfig,
    RepositoryConfig,
    RoleCommandContext,
    TemplateConfig,
    ValidationConfig,
)
from docsible.commands.document_role.orchestrators.role_orchestrator import RoleOrchestrator


class TestRoleOrchestrator:
    """Test RoleOrchestrator class."""

    @pytest.fixture
    def minimal_context(self):
        """Create minimal role command context."""
        return RoleCommandContext(
            paths=PathConfig(role_path=Path("/test/role")),
            template=TemplateConfig(),
            content=ContentFlags(),
            diagrams=DiagramConfig(),
            analysis=AnalysisConfig(),
            processing=ProcessingConfig(),
            validation=ValidationConfig(),
            repository=RepositoryConfig(),
        )

    @pytest.fixture
    def temp_role_dir(self):
        """Create temporary role directory structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            role_path = Path(tmpdir) / "test_role"
            role_path.mkdir()

            # Create minimal role structure
            (role_path / "tasks").mkdir()
            (role_path / "defaults").mkdir()
            (role_path / "meta").mkdir()

            # Create meta/main.yml
            meta_path = role_path / "meta" / "main.yml"
            meta_path.write_text("---\ngalaxy_info:\n  author: Test\n")

            yield role_path

    def test_orchestrator_initialization(self, minimal_context):
        """Test RoleOrchestrator initialization."""
        orchestrator = RoleOrchestrator(minimal_context)
        assert orchestrator.context == minimal_context
        assert orchestrator.role_info_loader is not None
        assert orchestrator.dry_run_formatter is not None

    def test_validate_paths_success(self, temp_role_dir, minimal_context):
        """Test successful path validation."""
        # validate_role_path expects a string, not Path
        minimal_context.paths.role_path = str(temp_role_dir)
        orchestrator = RoleOrchestrator(minimal_context)

        validated_path = orchestrator._validate_paths()
        # Use resolve() to handle symlinks like /var vs /private/var on macOS
        assert validated_path.resolve() == Path(temp_role_dir).resolve()

    def test_validate_paths_none_raises_error(self, minimal_context):
        """Test path validation with None raises error."""
        minimal_context.paths.role_path = None
        orchestrator = RoleOrchestrator(minimal_context)

        with pytest.raises(Exception):  # click.ClickException
            orchestrator._validate_paths()

    def test_load_playbook_none(self, minimal_context):
        """Test loading playbook when none provided."""
        orchestrator = RoleOrchestrator(minimal_context)
        playbook_content = orchestrator._load_playbook()
        assert playbook_content is None

    def test_load_playbook_with_file(self, minimal_context, temp_role_dir):
        """Test loading playbook from file."""
        playbook_path = temp_role_dir / "test.yml"
        playbook_path.write_text("---\n- hosts: all\n")

        minimal_context.paths.playbook = playbook_path
        orchestrator = RoleOrchestrator(minimal_context)

        playbook_content = orchestrator._load_playbook()
        assert playbook_content is not None
        assert "hosts: all" in playbook_content

    def test_build_role_info(self, minimal_context, temp_role_dir):
        """Test building role information."""
        minimal_context.paths.role_path = temp_role_dir
        orchestrator = RoleOrchestrator(minimal_context)

        role_info = orchestrator._build_role_info(temp_role_dir, None)
        assert "name" in role_info
        assert role_info["name"] == "test_role"

    def test_analyze_complexity(self, minimal_context, temp_role_dir):
        """Test complexity analysis."""
        minimal_context.paths.role_path = temp_role_dir
        orchestrator = RoleOrchestrator(minimal_context)

        role_info = orchestrator._build_role_info(temp_role_dir, None)
        analysis_report = orchestrator._analyze_complexity(role_info)

        assert analysis_report is not None
        assert hasattr(analysis_report, "category")
        assert hasattr(analysis_report, "metrics")

    @patch("docsible.commands.document_role.orchestrators.role_orchestrator.click.echo")
    @patch("docsible.utils.console.display_complexity_report")
    @patch("docsible.commands.document_role.helpers.handle_analyze_only_mode")
    def test_display_analysis_and_exit(
        self, mock_handle_analyze, mock_display_complexity, mock_echo, minimal_context
    ):
        """Test analysis display and exit."""
        minimal_context.analysis.complexity_report = True
        orchestrator = RoleOrchestrator(minimal_context)

        mock_report = Mock()
        role_info = {"name": "test_role"}

        orchestrator._display_analysis_and_exit(mock_report, role_info)

        mock_display_complexity.assert_called_once_with(mock_report, role_name="test_role")
        mock_handle_analyze.assert_called_once_with(role_info, "test_role")

    def test_generate_diagrams_disabled(self, minimal_context, temp_role_dir):
        """Test diagram generation when disabled."""
        minimal_context.diagrams.generate_graph = False
        orchestrator = RoleOrchestrator(minimal_context)

        role_info = orchestrator._build_role_info(temp_role_dir, None)
        analysis_report = orchestrator._analyze_complexity(role_info)

        diagrams = orchestrator._generate_diagrams(role_info, analysis_report, None)

        assert "generate_graph" in diagrams
        assert diagrams["generate_graph"] is False

    def test_generate_diagrams_enabled(self, minimal_context, temp_role_dir):
        """Test diagram generation when enabled."""
        minimal_context.diagrams.generate_graph = True
        orchestrator = RoleOrchestrator(minimal_context)

        role_info = orchestrator._build_role_info(temp_role_dir, None)
        analysis_report = orchestrator._analyze_complexity(role_info)

        diagrams = orchestrator._generate_diagrams(role_info, analysis_report, None)

        assert "generate_graph" in diagrams
        assert diagrams["generate_graph"] is True
        assert "mermaid_code_per_file" in diagrams
        assert "integration_boundary_diagram" in diagrams
        assert "architecture_diagram" in diagrams

    def test_generate_dependencies(self, minimal_context, temp_role_dir):
        """Test dependency generation."""
        minimal_context.diagrams.show_dependencies = False
        orchestrator = RoleOrchestrator(minimal_context)

        role_info = orchestrator._build_role_info(temp_role_dir, None)
        analysis_report = orchestrator._analyze_complexity(role_info)

        dependency_data = orchestrator._generate_dependencies(role_info, analysis_report)

        assert "dependency_matrix" in dependency_data
        assert "dependency_summary" in dependency_data
        assert "show_matrix" in dependency_data

    @patch("docsible.commands.document_role.orchestrators.role_orchestrator.click.echo")
    def test_display_dry_run(self, mock_echo, minimal_context, temp_role_dir):
        """Test dry-run display."""
        minimal_context.paths.role_path = temp_role_dir
        orchestrator = RoleOrchestrator(minimal_context)

        role_info = orchestrator._build_role_info(temp_role_dir, None)
        analysis_report = orchestrator._analyze_complexity(role_info)
        diagrams = {"generate_graph": False}
        dependency_data = {
            "dependency_matrix": None,
            "dependency_summary": None,
            "show_matrix": False,
        }

        orchestrator._display_dry_run(
            role_info, temp_role_dir, analysis_report, diagrams, dependency_data
        )

        mock_echo.assert_called_once()
        output = mock_echo.call_args[0][0]
        assert "DRY RUN MODE" in output

    @patch("docsible.commands.document_role.orchestrators.role_orchestrator.click.echo")
    @patch("docsible.renderers.readme_renderer.ReadmeRenderer")
    def test_render_documentation(self, mock_renderer_class, mock_echo, minimal_context, temp_role_dir):
        """Test documentation rendering."""
        minimal_context.paths.role_path = temp_role_dir
        orchestrator = RoleOrchestrator(minimal_context)

        mock_renderer = Mock()
        mock_renderer_class.return_value = mock_renderer

        role_info = orchestrator._build_role_info(temp_role_dir, None)
        analysis_report = orchestrator._analyze_complexity(role_info)
        diagrams = {
            "generate_graph": False,
            "mermaid_code_per_file": {},
            "sequence_diagram_high_level": None,
            "sequence_diagram_detailed": None,
            "state_diagram": None,
            "integration_boundary_diagram": None,
            "architecture_diagram": None,
        }
        dependency_data = {
            "dependency_matrix": None,
            "dependency_summary": None,
            "show_matrix": False,
        }

        orchestrator._render_documentation(
            role_info, temp_role_dir, analysis_report, diagrams, dependency_data
        )

        mock_renderer_class.assert_called_once()
        mock_renderer.render_role.assert_called_once()
        mock_echo.assert_called_once()
        # With positive_framing=True (default), the PositiveFormatter output is shown
        echo_output = mock_echo.call_args[0][0]
        assert "Documentation Generated" in echo_output or "documentation generated" in echo_output

    @patch("docsible.commands.document_role.orchestrators.role_orchestrator.click.echo")
    @patch("docsible.renderers.readme_renderer.ReadmeRenderer")
    def test_render_documentation_hybrid_mode(
        self, mock_renderer_class, mock_echo, minimal_context, temp_role_dir
    ):
        """Test documentation rendering in hybrid mode."""
        minimal_context.paths.role_path = temp_role_dir
        minimal_context.template.hybrid = True
        minimal_context.analysis.include_complexity = False
        orchestrator = RoleOrchestrator(minimal_context)

        mock_renderer = Mock()
        mock_renderer_class.return_value = mock_renderer

        role_info = orchestrator._build_role_info(temp_role_dir, None)
        analysis_report = orchestrator._analyze_complexity(role_info)
        diagrams = {
            "generate_graph": False,
            "mermaid_code_per_file": {},
        }
        dependency_data = {
            "dependency_matrix": None,
            "dependency_summary": None,
            "show_matrix": False,
        }

        orchestrator._render_documentation(
            role_info, temp_role_dir, analysis_report, diagrams, dependency_data
        )

        # Verify hybrid template type was used
        call_kwargs = mock_renderer.render_role.call_args[1]
        assert call_kwargs["template_type"] == "hybrid"
        # Verify complexity was auto-enabled for hybrid mode
        assert call_kwargs["include_complexity"] is True
