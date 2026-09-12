"""Tests for BriefHelpFormatter."""
import click
from click.testing import CliRunner

from docsible.formatters.help.brief import BriefHelpFormatter


class TestBriefHelpFormatterConstants:
    def test_role_essential_options_defined(self):
        essential = BriefHelpFormatter.ESSENTIAL_OPTION_NAMES.get("role", set())
        assert len(essential) > 0
        assert "role" in essential or "help" in essential

    def test_role_quick_examples_defined(self):
        examples = BriefHelpFormatter.QUICK_EXAMPLES.get("role", [])
        assert len(examples) > 0
        assert all("docsible role" in ex for ex in examples)

    def test_quick_examples_show_current_cli_format(self):
        # Should use current CLI format (docsible role --role .) not a future Phase 3 format
        examples = BriefHelpFormatter.QUICK_EXAMPLES.get("role", [])
        assert all("--role" in ex for ex in examples)

    def test_essential_options_is_dict(self):
        assert isinstance(BriefHelpFormatter.ESSENTIAL_OPTION_NAMES, dict)

    def test_quick_examples_is_dict(self):
        assert isinstance(BriefHelpFormatter.QUICK_EXAMPLES, dict)

    def test_essential_role_options_contains_expected_names(self):
        essential = BriefHelpFormatter.ESSENTIAL_OPTION_NAMES.get("role", set())
        # At minimum, the primary option (role) should be present
        assert "role" in essential

    def test_quick_examples_has_multiple_examples(self):
        examples = BriefHelpFormatter.QUICK_EXAMPLES.get("role", [])
        # Should provide more than one example to be useful
        assert len(examples) >= 2


class TestBriefHelpFormatterWriteBriefHelp:
    def _make_simple_command(self, name="role"):
        """Create a simple click command for testing."""
        @click.command(name=name)
        @click.option("--role", help="Role path")
        @click.option("--output", default="README.md", help="Output file")
        @click.option("--graph", is_flag=True, help="Generate graphs")
        @click.option("--minimal", is_flag=True, help="Minimal mode")
        def cmd(role, output, graph, minimal):
            """Generate documentation for an Ansible role."""
            pass
        return cmd

    def test_write_brief_help_writes_something(self):
        cmd = self._make_simple_command()
        runner = CliRunner()
        with runner.isolated_filesystem():
            ctx = click.Context(cmd, info_name="role")
            formatter = ctx.make_formatter()
            BriefHelpFormatter.write_brief_help("role", ctx, formatter)
            output = formatter.getvalue()
            assert len(output) > 0

    def test_brief_help_contains_quick_start(self):
        cmd = self._make_simple_command()
        runner = CliRunner()
        with runner.isolated_filesystem():
            ctx = click.Context(cmd, info_name="role")
            formatter = ctx.make_formatter()
            BriefHelpFormatter.write_brief_help("role", ctx, formatter)
            output = formatter.getvalue()
            assert "Quick Start" in output or "docsible role" in output

    def test_brief_help_contains_help_full_pointer(self):
        cmd = self._make_simple_command()
        runner = CliRunner()
        with runner.isolated_filesystem():
            ctx = click.Context(cmd, info_name="role")
            formatter = ctx.make_formatter()
            BriefHelpFormatter.write_brief_help("role", ctx, formatter)
            output = formatter.getvalue()
            assert "--help-full" in output

    def test_brief_help_contains_guide_tip(self):
        cmd = self._make_simple_command()
        runner = CliRunner()
        with runner.isolated_filesystem():
            ctx = click.Context(cmd, info_name="role")
            formatter = ctx.make_formatter()
            BriefHelpFormatter.write_brief_help("role", ctx, formatter)
            output = formatter.getvalue()
            assert "guide" in output.lower() or "docsible guide" in output

    def test_brief_help_contains_usage(self):
        cmd = self._make_simple_command()
        runner = CliRunner()
        with runner.isolated_filesystem():
            ctx = click.Context(cmd, info_name="role")
            formatter = ctx.make_formatter()
            BriefHelpFormatter.write_brief_help("role", ctx, formatter)
            output = formatter.getvalue()
            # Should include usage line
            assert "Usage" in output or "role" in output

    def test_brief_help_includes_essential_options_section(self):
        cmd = self._make_simple_command()
        runner = CliRunner()
        with runner.isolated_filesystem():
            ctx = click.Context(cmd, info_name="role")
            formatter = ctx.make_formatter()
            BriefHelpFormatter.write_brief_help("role", ctx, formatter)
            output = formatter.getvalue()
            # Should show the essential options section
            assert "Essential Options" in output or "--role" in output

    def test_brief_help_for_unknown_command_does_not_crash(self):
        cmd = self._make_simple_command(name="unknown")
        runner = CliRunner()
        with runner.isolated_filesystem():
            ctx = click.Context(cmd, info_name="unknown")
            formatter = ctx.make_formatter()
            # Should not raise even for an unrecognized command name
            BriefHelpFormatter.write_brief_help("unknown", ctx, formatter)
            output = formatter.getvalue()
            assert len(output) > 0

    def test_brief_help_includes_link_or_see_all_pointer(self):
        cmd = self._make_simple_command()
        runner = CliRunner()
        with runner.isolated_filesystem():
            ctx = click.Context(cmd, info_name="role")
            formatter = ctx.make_formatter()
            BriefHelpFormatter.write_brief_help("role", ctx, formatter)
            output = formatter.getvalue()
            # Should point the user to full help or docs
            assert "--help-full" in output or "http" in output
