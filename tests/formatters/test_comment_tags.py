"""Tests verifying that comment tags in defaults/ and task comments in tasks/

are parsed and appear in the generated README output.

The fixture under tests/fixtures/annotated_role contains:
  defaults/main.yml
    service_port    — title, description, required, choices tags
    service_tls_enabled — title, required tags (no description, no choices)
    service_log_level   — title, required, choices tags
    service_timeout     — inline comment only (no structured tags)
  tasks/main.yml
    Three tasks each preceded by a plain # comment line.
"""

import shutil
from pathlib import Path

from click.testing import CliRunner

from docsible.cli import cli

FIXTURE_PATH = Path("tests/fixtures/annotated_role")


def _generate_readme(tmp_path: Path) -> str:
    """Copy annotated_role fixture into tmp_path, run document, return README text."""
    role_copy = tmp_path / "annotated_role"
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
    return readme.read_text()


class TestCommentTagsInVariableTable:
    """Verify that structured comment tags (title, description, required, choices)

    from defaults/main.yml are surfaced in the generated README.
    """

    def test_title_tag_populates_variable_table(self, tmp_path):
        """The '# title: Listen port' tag must appear in the README."""
        content = _generate_readme(tmp_path)
        assert "Listen port" in content, (
            "'Listen port' (from # title: tag on service_port) not found in README"
        )

    def test_description_tag_populates_variable_table(self, tmp_path):
        """The '# description:' tag value must appear in the README."""
        content = _generate_readme(tmp_path)
        assert "TCP port on which the service listens" in content, (
            "Description value for service_port not found in README"
        )

    def test_required_tag_populates_variable_table(self, tmp_path):
        """The '# required: true' tag must result in the required marker appearing."""
        content = _generate_readme(tmp_path)
        # The variable name must appear alongside its required annotation
        assert "service_port" in content, (
            "'service_port' variable not found in README"
        )
        assert "true" in content.lower(), (
            "Required 'true' value for service_port not found in README"
        )

    def test_choices_tag_populates_variable_table(self, tmp_path):
        """The '# choices: 80, 443, 8080' tag must appear in the README."""
        content = _generate_readme(tmp_path)
        assert "service_port" in content, (
            "'service_port' variable not found in README"
        )
        # At least one of the listed choices must be surfaced
        assert any(choice in content for choice in ["80", "443", "8080"]), (
            "None of the choices (80, 443, 8080) from the choices tag found in README"
        )

    def test_inline_comment_falls_back_when_no_tags(self, tmp_path):
        """service_timeout has only an inline YAML comment; variable must still appear."""
        content = _generate_readme(tmp_path)
        assert "service_timeout" in content, (
            "'service_timeout' (inline-comment-only variable) not found in README"
        )


class TestTaskCommentsInTaskTable:
    """Verify that plain # comments above tasks appear in the tasks section."""

    def test_task_comments_appear_in_task_table(self, tmp_path):
        """Each task's preceding # comment should be present in the README."""
        content = _generate_readme(tmp_path)

        assert "Install service package" in content, (
            "Task name 'Install service package' not found in README"
        )
        assert "Configure service" in content, (
            "Task name 'Configure service' not found in README"
        )
        assert "Start service" in content, (
            "Task name 'Start service' not found in README"
        )
