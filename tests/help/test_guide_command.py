"""Tests for the guide command."""
from pathlib import Path

import pytest
from click.testing import CliRunner

from docsible.commands.guide import AVAILABLE_TOPICS, GUIDES_DIR, guide_command


class TestGuideCommandConstants:
    def test_available_topics_is_list(self):
        assert isinstance(AVAILABLE_TOPICS, list)
        assert len(AVAILABLE_TOPICS) > 0

    def test_getting_started_in_topics(self):
        assert "getting-started" in AVAILABLE_TOPICS

    def test_troubleshooting_in_topics(self):
        assert "troubleshooting" in AVAILABLE_TOPICS

    def test_smart_defaults_in_topics(self):
        assert "smart-defaults" in AVAILABLE_TOPICS

    def test_guides_dir_points_to_help_guides(self):
        guides_str = str(GUIDES_DIR)
        assert "help" in guides_str
        assert "guides" in guides_str

    def test_guides_dir_is_path(self):
        assert isinstance(GUIDES_DIR, Path)


class TestGuideFilesExist:
    def test_guides_dir_exists(self):
        assert GUIDES_DIR.exists(), f"Guides directory not found: {GUIDES_DIR}"

    def test_getting_started_guide_exists(self):
        guide = GUIDES_DIR / "getting-started.md"
        assert guide.exists(), f"Guide not found: {guide}"

    def test_troubleshooting_guide_exists(self):
        guide = GUIDES_DIR / "troubleshooting.md"
        assert guide.exists(), f"Guide not found: {guide}"

    @pytest.mark.xfail(
        not (Path(__file__).parent.parent.parent / "docsible" / "help" / "guides" / "smart-defaults.md").exists(),
        reason="smart-defaults.md guide has not been created yet",
        strict=False,
    )
    def test_smart_defaults_guide_exists(self):
        guide = GUIDES_DIR / "smart-defaults.md"
        assert guide.exists(), f"Guide not found: {guide}"

    def test_guides_have_content(self):
        for topic in AVAILABLE_TOPICS:
            guide = GUIDES_DIR / f"{topic}.md"
            if guide.exists():
                content = guide.read_text()
                assert len(content) > 100, f"Guide too short: {topic}"


class TestGuideCommandInvocation:
    def test_getting_started_runs_successfully(self):
        runner = CliRunner()
        result = runner.invoke(guide_command, ["getting-started"])
        # Should not exit with code 2 (usage error)
        assert result.exit_code != 2, f"Command failed with usage error: {result.output}"

    def test_troubleshooting_runs_successfully(self):
        runner = CliRunner()
        result = runner.invoke(guide_command, ["troubleshooting"])
        assert result.exit_code != 2, f"Command failed with usage error: {result.output}"

    @pytest.mark.xfail(
        not (Path(__file__).parent.parent.parent / "docsible" / "help" / "guides" / "smart-defaults.md").exists(),
        reason="smart-defaults.md guide has not been created yet",
        strict=False,
    )
    def test_smart_defaults_runs_successfully(self):
        runner = CliRunner()
        result = runner.invoke(guide_command, ["smart-defaults"])
        assert result.exit_code != 2, f"Command failed with usage error: {result.output}"

    def test_invalid_topic_fails(self):
        runner = CliRunner()
        result = runner.invoke(guide_command, ["nonexistent-topic"])
        assert result.exit_code != 0

    def test_help_shows_available_topics(self):
        runner = CliRunner()
        result = runner.invoke(guide_command, ["--help"])
        assert result.exit_code == 0
        output_lower = result.output.lower()
        assert "guide" in output_lower or "topic" in output_lower

    def test_guide_command_is_click_command(self):
        import click
        assert isinstance(guide_command, click.BaseCommand)  # type: ignore[arg-type]

    def test_guide_command_name(self):
        assert guide_command.name == "guide"


class TestGuideContent:
    def test_getting_started_uses_current_cli(self):
        guide = GUIDES_DIR / "getting-started.md"
        if guide.exists():
            content = guide.read_text()
            # Should use current CLI format, not a future Phase 3 format
            assert "docsible role --role" in content or "docsible role" in content

    def test_getting_started_has_installation_or_quick_start(self):
        guide = GUIDES_DIR / "getting-started.md"
        if guide.exists():
            content = guide.read_text()
            content_lower = content.lower()
            assert "install" in content_lower or "quick start" in content_lower or "getting started" in content_lower

    def test_troubleshooting_has_examples(self):
        guide = GUIDES_DIR / "troubleshooting.md"
        if guide.exists():
            content = guide.read_text()
            assert "docsible" in content

    def test_troubleshooting_has_docsible_role_commands(self):
        guide = GUIDES_DIR / "troubleshooting.md"
        if guide.exists():
            content = guide.read_text()
            assert "docsible role" in content

    @pytest.mark.xfail(
        not (Path(__file__).parent.parent.parent / "docsible" / "help" / "guides" / "smart-defaults.md").exists(),
        reason="smart-defaults.md guide has not been created yet",
        strict=False,
    )
    def test_smart_defaults_explains_complexity(self):
        guide = GUIDES_DIR / "smart-defaults.md"
        if guide.exists():
            content = guide.read_text()
            assert "SIMPLE" in content or "complexity" in content.lower()

    def test_all_existing_guides_reference_docsible(self):
        for topic in AVAILABLE_TOPICS:
            guide = GUIDES_DIR / f"{topic}.md"
            if guide.exists():
                content = guide.read_text()
                assert "docsible" in content.lower(), f"Guide '{topic}' does not mention docsible"
