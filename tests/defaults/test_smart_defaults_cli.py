from click.testing import CliRunner

from docsible.cli import cli


class TestSmartDefaultsCLI:
    """Test smart defaults integration in CLI."""

    def test_simple_role_no_graphs_by_default(self, simple_role, tmp_path):
        """Simple role should not get graphs by default."""
        runner = CliRunner()

        # Use absolute path for output
        output_file = tmp_path / "README.md"

        result = runner.invoke(
            cli,
            ["role", "--role", str(simple_role), "--output", str(output_file)],
            catch_exceptions=False,
        )

        assert result.exit_code == 0, f"CLI failed: {result.output}"

        # Check that README was created
        assert output_file.exists(), f"README not found at {output_file}"

        # Simple role should not have graphs (smart default)
        content = output_file.read_text()
        assert "```mermaid" not in content  # No graphs

    def test_complex_role_gets_graphs_by_default(self, complex_role_fixture, tmp_path):
        """Complex role should get graphs by default."""
        runner = CliRunner()

        # Use absolute path for output
        output_file = tmp_path / "README.md"

        result = runner.invoke(
            cli,
            ["role", "--role", str(complex_role_fixture), "--output", str(output_file)],
            catch_exceptions=False,
        )

        assert result.exit_code == 0, f"CLI failed: {result.output}"

        # Check that README was created
        assert output_file.exists(), f"README not found at {output_file}"

        # Complex role should have visualization enabled (smart default)
        content = output_file.read_text()

        # Complex roles may use either Mermaid diagrams OR execution routes
        has_mermaid = "```mermaid" in content
        has_execution_routes = "Execution Routes" in content
        has_architecture = "Architecture Overview" in content

        assert has_mermaid or (has_execution_routes and has_architecture), \
            f"Complex role should have visualization (mermaid: {has_mermaid}, routes: {has_execution_routes}, arch: {has_architecture})"

    def test_user_override_respected(self, simple_role, tmp_path):
        """User --graph flag should override smart default."""
        runner = CliRunner()

        # Use absolute path for output
        output_file = tmp_path / "README.md"

        result = runner.invoke(
            cli,
            [
                "role",
                "--role",
                str(simple_role),
                "--graph",  # Force graphs
                "--output",
                str(output_file),
            ],
            catch_exceptions=False,
        )

        assert result.exit_code == 0, f"CLI failed: {result.output}"

        # User explicitly requested --graph, should be in output (even for simple role)
        assert output_file.exists(), f"README not found at {output_file}"
        content = output_file.read_text()
        assert "```mermaid" in content, "User override --graph should force graphs"

    def test_smart_defaults_can_be_disabled(self, complex_role_fixture, tmp_path, monkeypatch):
        """Smart defaults can be disabled via env var."""
        runner = CliRunner()

        # Disable smart defaults
        monkeypatch.setenv("DOCSIBLE_ENABLE_SMART_DEFAULTS", "false")

        # Use absolute path for output
        output_file = tmp_path / "README.md"

        result = runner.invoke(
            cli,
            ["role", "--role", str(complex_role_fixture), "--output", str(output_file)],
            catch_exceptions=False,
        )

        assert result.exit_code == 0, f"CLI failed: {result.output}"

        # With smart defaults disabled, complex role shouldn't auto-get graphs
        assert output_file.exists(), f"README not found at {output_file}"
        content = output_file.read_text()
        assert "```mermaid" not in content, "Graphs should NOT be auto-enabled when smart defaults disabled"

    def test_minimal_role_gets_minimal_mode(self, minimal_role, tmp_path):
        """Minimal role should get minimal mode by default."""
        runner = CliRunner()

        # Use absolute path for output
        output_file = tmp_path / "README.md"

        result = runner.invoke(
            cli,
            ["role", "--role", str(minimal_role), "--output", str(output_file)],
            catch_exceptions=False,
        )

        assert result.exit_code == 0, f"CLI failed: {result.output}"

        # Minimal role should use minimal mode (fewer sections)
        assert output_file.exists(), f"README not found at {output_file}"
        content = output_file.read_text()

        # Minimal mode should hide variables and examples sections
        # Check for absence of these sections
        assert "## Role Variables" not in content or "No variables" in content, "Minimal mode should hide/minimize variables"