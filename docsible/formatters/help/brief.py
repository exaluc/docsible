"""Brief help formatter for docsible CLI commands."""

import click


class BriefHelpFormatter:
    """Provides brief help formatting — only essential options."""

    # Options shown in brief help for each command
    ESSENTIAL_OPTION_NAMES = {
        "role": {"role", "output", "graph", "minimal", "help"},
    }

    QUICK_EXAMPLES = {
        "role": [
            "docsible role --role .            # Document current directory",
            "docsible role --role . --graph    # With task flow diagrams",
            "docsible role --role . --minimal  # Minimal documentation",
        ],
    }

    @staticmethod
    def write_brief_help(
        command_name: str, ctx: click.Context, formatter: click.HelpFormatter
    ) -> None:
        """Write brief help to formatter.

        Args:
            command_name: Command name (e.g., "role")
            ctx: Click context
            formatter: Click help formatter to write to
        """
        from docsible.formatters.help.brief import BriefHelpFormatter

        # Usage line
        pieces = ctx.command.collect_usage_pieces(ctx)
        formatter.write_usage(ctx.command_path, " ".join(pieces) if pieces else "")

        # Description — show only the first paragraph (short summary)
        if ctx.command.help:
            first_paragraph = ctx.command.help.split("\n\n")[0].strip()
            formatter.write_paragraph()
            with formatter.indentation():
                formatter.write_text(first_paragraph)

        # Quick start examples
        examples = BriefHelpFormatter.QUICK_EXAMPLES.get(command_name, [])
        if examples:
            formatter.write_paragraph()
            with formatter.section("Quick Start"):
                for example in examples:
                    formatter.write_text(example)

        # Tip for new users
        formatter.write_paragraph()
        formatter.write_text("New to docsible? Run: docsible guide getting-started")

        # Essential options only
        essential = BriefHelpFormatter.ESSENTIAL_OPTION_NAMES.get(command_name, set())
        essential_params = [p for p in ctx.command.get_params(ctx) if p.name in essential]

        if essential_params:
            formatter.write_paragraph()
            with formatter.section("Essential Options"):
                help_records = [
                    rv for p in essential_params if (rv := p.get_help_record(ctx)) is not None
                ]
                if help_records:
                    formatter.write_dl(help_records)

        # Footer
        formatter.write_paragraph()
        formatter.write_text("See all options: docsible role --help-full")
        formatter.write_text("Learn more: https://github.com/jier/docsible")
