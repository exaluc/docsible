"""End-to-end integration tests for the edge_case_role fixture.

These tests exercise the code paths introduced by the fixture at
tests/fixtures/edge_case_role/:
  - block/rescue/always task grouping
  - include_role / import_role
  - register, retries/until, notify
  - 20+ default variables
  - runtime vars with list and nested-dict values
  - 3 handlers, two with listen aliases
  - .docsible metadata file
  - no meta/ or files/ directories
"""

import shutil
from pathlib import Path

from click.testing import CliRunner

from docsible.cli import cli

FIXTURE_PATH = Path("tests/fixtures/edge_case_role")


class TestEdgeCaseRole:
    """End-to-end tests for the edge_case_role fixture."""

    def test_edge_case_role_dry_run(self):
        """dry-run mode must exit 0 without writing any files."""
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["role", "--role", str(FIXTURE_PATH), "--dry-run"],
        )
        assert result.exit_code == 0, (
            f"dry-run exited non-zero.\nOutput:\n{result.output}"
        )

    def test_edge_case_role_with_graph(self):
        """--graph --dry-run must exit 0 (exercises Mermaid diagram code path)."""
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["role", "--role", str(FIXTURE_PATH), "--graph", "--dry-run"],
        )
        assert result.exit_code == 0, (
            f"--graph --dry-run exited non-zero.\nOutput:\n{result.output}"
        )

    def test_edge_case_role_no_handlers(self):
        """--no-handlers --dry-run must exit 0 (exercises handler-exclusion path)."""
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["role", "--role", str(FIXTURE_PATH), "--no-handlers", "--dry-run"],
        )
        assert result.exit_code == 0, (
            f"--no-handlers --dry-run exited non-zero.\nOutput:\n{result.output}"
        )

    def test_edge_case_role_no_vars(self):
        """--no-vars --dry-run must exit 0 (exercises variable-exclusion path)."""
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["role", "--role", str(FIXTURE_PATH), "--no-vars", "--dry-run"],
        )
        assert result.exit_code == 0, (
            f"--no-vars --dry-run exited non-zero.\nOutput:\n{result.output}"
        )

    def test_edge_case_role_generates_readme(self, tmp_path):
        """Full README generation from edge_case_role produces expected content.

        The fixture is copied into tmp_path so the source tree is not modified.
        Assertions cover:
          - handlers section with "Restart application service"
          - block task name appearing in the task list
          - at least one default variable name
        """
        role_copy = tmp_path / "edge_case_role"
        shutil.copytree(str(FIXTURE_PATH), str(role_copy))

        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["role", "--role", str(role_copy), "--no-backup"],
        )
        assert result.exit_code == 0, (
            f"README generation exited non-zero.\nOutput:\n{result.output}"
        )

        readme = role_copy / "README.md"
        assert readme.exists(), "README.md was not created"

        content = readme.read_text()

        # Handlers section — "Restart application service" is the first handler
        assert "Restart application service" in content, (
            "Handler 'Restart application service' not found in README"
        )

        # Block task name from tasks/main.yml
        assert "Deploy application with error handling" in content, (
            "Block task name not found in README"
        )

        # At least one default variable from defaults/main.yml
        assert "app_name" in content, (
            "Default variable 'app_name' not found in README"
        )
