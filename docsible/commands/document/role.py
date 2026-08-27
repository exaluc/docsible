"""docsible document role — new intent-based command."""

import click

from docsible.commands.document_role.core_orchestrated import doc_the_role as core_doc_the_role
from docsible.commands.document_role.options import (
    add_content_options,
    add_framing_options,
    add_generation_options,
    add_output_options,
    add_path_options,
    add_recommendation_options,
    add_repository_options,
    add_template_options,
    resolve_role_command_options,
)
from docsible.presets.registry import PresetRegistry
from docsible.utils.cli_helpers import BriefHelpCommand


@click.command(name="role", cls=BriefHelpCommand)
@add_path_options
@add_output_options
@add_content_options
@add_template_options
@add_generation_options
@add_repository_options
@add_recommendation_options
@add_framing_options
@click.option(
    "--preset",
    type=click.Choice(PresetRegistry.names()),
    default=None,
    help="Apply a built-in preset (personal/team/enterprise/consultant).",
)
def document_role_cmd(preset, **kwargs) -> None:
    """Generate documentation for an Ansible role."""
    core_doc_the_role(**resolve_role_command_options(preset, kwargs))
