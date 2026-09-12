"""Tests for intent-based CLI commands: document, analyze, validate."""
from click.testing import CliRunner

from docsible.cli import cli
from docsible.commands.analyze import analyze_group
from docsible.commands.analyze.role import analyze_role_cmd
from docsible.commands.document import document_group
from docsible.commands.document.role import document_role_cmd
from docsible.commands.validate import validate_group
from docsible.commands.validate.role import validate_role_cmd

# ---------------------------------------------------------------------------
# document role --help
# ---------------------------------------------------------------------------

class TestDocumentRoleHelp:
    def test_document_role_help_exits_zero(self):
        runner = CliRunner()
        result = runner.invoke(document_role_cmd, ["--help"])
        assert result.exit_code == 0

    def test_document_role_help_shows_usage(self):
        runner = CliRunner()
        result = runner.invoke(document_role_cmd, ["--help"])
        assert "Usage:" in result.output

    def test_document_role_has_preset_option(self):
        """--preset is registered on document_role_cmd (may be hidden in brief help)."""
        option_names = [
            name
            for param in document_role_cmd.params
            for name in param.opts
        ]
        assert "--preset" in option_names


# ---------------------------------------------------------------------------
# analyze role --help
# ---------------------------------------------------------------------------

class TestAnalyzeRoleHelp:
    def test_analyze_role_help_exits_zero(self):
        runner = CliRunner()
        result = runner.invoke(analyze_role_cmd, ["--help"])
        assert result.exit_code == 0

    def test_analyze_role_help_shows_usage(self):
        runner = CliRunner()
        result = runner.invoke(analyze_role_cmd, ["--help"])
        assert "Usage:" in result.output


# ---------------------------------------------------------------------------
# validate role --help
# ---------------------------------------------------------------------------

class TestValidateRoleHelp:
    def test_validate_role_help_exits_zero(self):
        runner = CliRunner()
        result = runner.invoke(validate_role_cmd, ["--help"])
        assert result.exit_code == 0

    def test_validate_role_help_shows_usage(self):
        runner = CliRunner()
        result = runner.invoke(validate_role_cmd, ["--help"])
        assert "Usage:" in result.output


# ---------------------------------------------------------------------------
# document --help (group)
# ---------------------------------------------------------------------------

class TestDocumentGroupHelp:
    def test_document_help_exits_zero(self):
        runner = CliRunner()
        result = runner.invoke(document_group, ["--help"])
        assert result.exit_code == 0

    def test_document_help_lists_role_subcommand(self):
        runner = CliRunner()
        result = runner.invoke(document_group, ["--help"])
        assert "role" in result.output


# ---------------------------------------------------------------------------
# analyze --help (group)
# ---------------------------------------------------------------------------

class TestAnalyzeGroupHelp:
    def test_analyze_help_exits_zero(self):
        runner = CliRunner()
        result = runner.invoke(analyze_group, ["--help"])
        assert result.exit_code == 0

    def test_analyze_help_lists_role_subcommand(self):
        runner = CliRunner()
        result = runner.invoke(analyze_group, ["--help"])
        assert "role" in result.output


# ---------------------------------------------------------------------------
# validate --help (group)
# ---------------------------------------------------------------------------

class TestValidateGroupHelp:
    def test_validate_help_exits_zero(self):
        runner = CliRunner()
        result = runner.invoke(validate_group, ["--help"])
        assert result.exit_code == 0

    def test_validate_help_lists_role_subcommand(self):
        runner = CliRunner()
        result = runner.invoke(validate_group, ["--help"])
        assert "role" in result.output


# ---------------------------------------------------------------------------
# docsible --help (top-level CLI)
# ---------------------------------------------------------------------------

class TestTopLevelCliHelp:
    def test_cli_help_exits_zero(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0

    def test_cli_help_shows_document_command(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        assert "document" in result.output

    def test_cli_help_shows_analyze_command(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        assert "analyze" in result.output

    def test_cli_help_shows_validate_command(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        assert "validate" in result.output

    def test_cli_help_shows_init_command(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        assert "init" in result.output


# ---------------------------------------------------------------------------
# Subcommand routing via top-level CLI
# ---------------------------------------------------------------------------

class TestSubcommandRouting:
    def test_cli_document_help_exits_zero(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["document", "--help"])
        assert result.exit_code == 0

    def test_cli_document_role_help_exits_zero(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["document", "role", "--help"])
        assert result.exit_code == 0

    def test_cli_analyze_help_exits_zero(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["analyze", "--help"])
        assert result.exit_code == 0

    def test_cli_analyze_role_help_exits_zero(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["analyze", "role", "--help"])
        assert result.exit_code == 0

    def test_cli_validate_help_exits_zero(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["validate", "--help"])
        assert result.exit_code == 0

    def test_cli_validate_role_help_exits_zero(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["validate", "role", "--help"])
        assert result.exit_code == 0
