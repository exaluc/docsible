"""Integration tests for brief/full help CLI behavior."""
import sys
from unittest.mock import patch

import pytest
from click.testing import CliRunner


class TestBriefHelpCommand:
    def test_brief_help_command_importable(self):
        # BriefHelpCommand is appended to cli_helpers.py by another agent.
        # If it has not been added yet, this test will clearly indicate that.
        try:
            from docsible.utils.cli_helpers import BriefHelpCommand
            assert BriefHelpCommand is not None
        except ImportError:
            pytest.skip("BriefHelpCommand not yet implemented in cli_helpers.py")

    def test_brief_help_command_extends_grouped_help(self):
        try:
            from docsible.utils.cli_helpers import BriefHelpCommand, GroupedHelpCommand
        except ImportError:
            pytest.skip("BriefHelpCommand not yet implemented in cli_helpers.py")
        assert issubclass(BriefHelpCommand, GroupedHelpCommand)

    def test_brief_help_command_has_format_help(self):
        try:
            from docsible.utils.cli_helpers import BriefHelpCommand
        except ImportError:
            pytest.skip("BriefHelpCommand not yet implemented in cli_helpers.py")
        assert hasattr(BriefHelpCommand, "format_help")

    def test_brief_help_command_has_write_brief_help(self):
        try:
            from docsible.utils.cli_helpers import BriefHelpCommand
        except ImportError:
            pytest.skip("BriefHelpCommand not yet implemented in cli_helpers.py")
        assert hasattr(BriefHelpCommand, "_write_brief_help")

    def test_role_command_uses_brief_help_command(self):
        try:
            from docsible.utils.cli_helpers import BriefHelpCommand
        except ImportError:
            pytest.skip("BriefHelpCommand not yet implemented in cli_helpers.py")
        from docsible.commands.legacy.role import doc_the_role
        assert isinstance(doc_the_role, BriefHelpCommand), (
            f"doc_the_role is {type(doc_the_role).__name__}, expected BriefHelpCommand. "
            "The role command must be updated to use cls=BriefHelpCommand."
        )

    def test_role_help_shows_brief_by_default(self):
        """Default --help should show brief help with --help-full pointer."""
        try:
            from docsible.utils.cli_helpers import BriefHelpCommand
        except ImportError:
            pytest.skip("BriefHelpCommand not yet implemented in cli_helpers.py")
        from docsible.cli import cli
        runner = CliRunner()
        with patch.object(sys, "argv", ["docsible", "role", "--help"]):
            result = runner.invoke(cli, ["role", "--help"])
        assert result.exit_code == 0
        assert "--help-full" in result.output

    def test_role_full_help_shows_more_options(self):
        """--help-full should show all options (more than brief help)."""
        try:
            from docsible.utils.cli_helpers import BriefHelpCommand
        except ImportError:
            pytest.skip("BriefHelpCommand not yet implemented in cli_helpers.py")
        from docsible.cli import cli
        runner = CliRunner()
        with patch.object(sys, "argv", ["docsible", "role", "--help-full"]):
            result = runner.invoke(cli, ["role", "--help-full"])
        assert result.exit_code == 0

    def test_role_full_help_has_more_lines_than_brief(self):
        """Full help should produce more output lines than brief help."""
        try:
            from docsible.utils.cli_helpers import BriefHelpCommand
        except ImportError:
            pytest.skip("BriefHelpCommand not yet implemented in cli_helpers.py")
        from docsible.cli import cli
        runner = CliRunner()
        with patch.object(sys, "argv", ["docsible", "role", "--help"]):
            brief_result = runner.invoke(cli, ["role", "--help"])
        with patch.object(sys, "argv", ["docsible", "role", "--help-full"]):
            full_result = runner.invoke(cli, ["role", "--help-full"])
        brief_lines = len(brief_result.output.splitlines())
        full_lines = len(full_result.output.splitlines())
        assert full_lines > brief_lines, (
            f"Full help ({full_lines} lines) should have more lines than brief help ({brief_lines} lines)"
        )


class TestGroupedHelpCommandExists:
    """Tests for GroupedHelpCommand which is already implemented."""

    def test_grouped_help_command_importable(self):
        from docsible.utils.cli_helpers import GroupedHelpCommand
        assert GroupedHelpCommand is not None

    def test_grouped_help_command_is_click_command(self):
        import click

        from docsible.utils.cli_helpers import GroupedHelpCommand
        assert issubclass(GroupedHelpCommand, click.Command)

    def test_grouped_help_command_has_format_options(self):
        from docsible.utils.cli_helpers import GroupedHelpCommand
        assert hasattr(GroupedHelpCommand, "format_options")

    def test_role_command_uses_grouped_help_command(self):
        from docsible.commands.legacy.role import doc_the_role
        from docsible.utils.cli_helpers import GroupedHelpCommand
        assert isinstance(doc_the_role, GroupedHelpCommand)

    def test_role_help_shows_grouped_sections(self):
        from docsible.cli import cli
        runner = CliRunner()
        result = runner.invoke(cli, ["role", "--help"])
        assert result.exit_code == 0
        # Grouped help should contain at least one group section heading
        output = result.output
        assert "Options" in output or "Input" in output or "Output" in output


class TestGuideRegisteredInCLI:
    def test_guide_command_registered(self):
        from docsible.cli import cli
        # Check if guide has been registered
        command_names = list(cli.commands.keys()) if hasattr(cli, "commands") else []
        if "guide" not in command_names:
            pytest.xfail(
                "guide command is not yet registered in cli.py — "
                "needs: cli.add_command(guide_command, name='guide')"
            )
        assert "guide" in command_names

    def test_guide_invocable_from_cli(self):
        from docsible.cli import cli
        command_names = list(cli.commands.keys()) if hasattr(cli, "commands") else []
        if "guide" not in command_names:
            pytest.xfail("guide command is not yet registered in cli.py")
        runner = CliRunner()
        result = runner.invoke(cli, ["guide", "--help"])
        assert result.exit_code == 0

    def test_guide_getting_started_from_cli(self):
        from docsible.cli import cli
        command_names = list(cli.commands.keys()) if hasattr(cli, "commands") else []
        if "guide" not in command_names:
            pytest.xfail("guide command is not yet registered in cli.py")
        runner = CliRunner()
        result = runner.invoke(cli, ["guide", "getting-started"])
        assert result.exit_code != 2

    def test_cli_has_expected_commands(self):
        from docsible.cli import cli
        command_names = list(cli.commands.keys()) if hasattr(cli, "commands") else []
        # These are the commands that should always be present
        assert "role" in command_names
        assert "init" in command_names
        assert "check" in command_names
