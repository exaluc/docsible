"""Tests for docsible.commands.wizard — wizard_init command."""
import yaml
from click.testing import CliRunner

from docsible.commands.wizard import wizard_init


class TestWizardInitNonInteractive:
    """Tests for non-interactive --preset mode."""

    def test_preset_team_writes_config(self, tmp_path):
        runner = CliRunner()
        result = runner.invoke(wizard_init, ["--preset", "team", "--path", str(tmp_path)])
        assert result.exit_code == 0, result.output
        config_path = tmp_path / ".docsible" / "config.yml"
        assert config_path.exists()
        data = yaml.safe_load(config_path.read_text())
        assert data["preset"] == "team"

    def test_preset_enterprise_writes_config(self, tmp_path):
        runner = CliRunner()
        result = runner.invoke(wizard_init, ["--preset", "enterprise", "--path", str(tmp_path)])
        assert result.exit_code == 0, result.output
        config_path = tmp_path / ".docsible" / "config.yml"
        data = yaml.safe_load(config_path.read_text())
        assert data["preset"] == "enterprise"

    def test_preset_personal_writes_config(self, tmp_path):
        runner = CliRunner()
        result = runner.invoke(wizard_init, ["--preset", "personal", "--path", str(tmp_path)])
        assert result.exit_code == 0, result.output
        config_path = tmp_path / ".docsible" / "config.yml"
        data = yaml.safe_load(config_path.read_text())
        assert data["preset"] == "personal"

    def test_preset_consultant_writes_config(self, tmp_path):
        runner = CliRunner()
        result = runner.invoke(wizard_init, ["--preset", "consultant", "--path", str(tmp_path)])
        assert result.exit_code == 0, result.output
        config_path = tmp_path / ".docsible" / "config.yml"
        data = yaml.safe_load(config_path.read_text())
        assert data["preset"] == "consultant"

    def test_output_contains_initialized_message(self, tmp_path):
        runner = CliRunner()
        result = runner.invoke(wizard_init, ["--preset", "team", "--path", str(tmp_path)])
        assert result.exit_code == 0, result.output
        # The wizard outputs a message confirming initialization
        assert "team" in result.output

    def test_output_contains_initialized_with_preset(self, tmp_path):
        runner = CliRunner()
        result = runner.invoke(wizard_init, ["--preset", "enterprise", "--path", str(tmp_path)])
        assert result.exit_code == 0, result.output
        # Should say something like "Initialized with preset 'enterprise'"
        lower = result.output.lower()
        assert "enterprise" in lower


class TestWizardInitForce:
    """Tests for --force flag behaviour."""

    def test_force_overwrites_existing_config(self, tmp_path):
        runner = CliRunner()
        # First init with personal
        runner.invoke(wizard_init, ["--preset", "personal", "--path", str(tmp_path)])
        # Force overwrite with team
        result = runner.invoke(
            wizard_init, ["--preset", "team", "--path", str(tmp_path), "--force"]
        )
        assert result.exit_code == 0, result.output
        config_path = tmp_path / ".docsible" / "config.yml"
        data = yaml.safe_load(config_path.read_text())
        assert data["preset"] == "team"

    def test_force_does_not_prompt(self, tmp_path):
        runner = CliRunner()
        # Create existing config
        runner.invoke(wizard_init, ["--preset", "personal", "--path", str(tmp_path)])
        # Force overwrite — should not ask for confirmation
        result = runner.invoke(
            wizard_init, ["--preset", "enterprise", "--path", str(tmp_path), "--force"]
        )
        assert result.exit_code == 0, result.output
        assert "Overwrite?" not in result.output

    def test_no_force_existing_config_prompts_overwrite(self, tmp_path):
        runner = CliRunner()
        # Create existing config
        runner.invoke(wizard_init, ["--preset", "personal", "--path", str(tmp_path)])
        # Invoke without --force, but answer "n" to avoid interactive wizard
        result = runner.invoke(
            wizard_init,
            ["--preset", "team", "--path", str(tmp_path)],
            input="n\n",
        )
        assert result.exit_code == 0
        # Should show the prompt or abort message
        assert "Overwrite?" in result.output or "Aborted" in result.output

    def test_no_force_existing_config_aborts_on_no(self, tmp_path):
        runner = CliRunner()
        runner.invoke(wizard_init, ["--preset", "personal", "--path", str(tmp_path)])
        result = runner.invoke(
            wizard_init,
            ["--preset", "team", "--path", str(tmp_path)],
            input="n\n",
        )
        # Config should still contain 'personal', not 'team'
        config_path = tmp_path / ".docsible" / "config.yml"
        data = yaml.safe_load(config_path.read_text())
        assert data["preset"] == "personal"


class TestWizardInitHelp:
    """Tests for --help output."""

    def test_help_exits_zero(self):
        runner = CliRunner()
        result = runner.invoke(wizard_init, ["--help"])
        assert result.exit_code == 0

    def test_help_shows_usage(self):
        runner = CliRunner()
        result = runner.invoke(wizard_init, ["--help"])
        assert "Usage:" in result.output

    def test_help_shows_preset_option(self):
        runner = CliRunner()
        result = runner.invoke(wizard_init, ["--help"])
        assert "--preset" in result.output

    def test_help_shows_force_option(self):
        runner = CliRunner()
        result = runner.invoke(wizard_init, ["--help"])
        assert "--force" in result.output
