"""docsible analyze role — analyze without generating docs."""

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


@click.command(name="role")
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
    help="Apply a built-in preset.",
)
def analyze_role_cmd(preset, **kwargs) -> None:
    """Analyze an Ansible role without generating documentation."""
    kwargs = resolve_role_command_options(preset, kwargs)
    # Analyze runs the recommendation pipeline but never renders documentation.
    kwargs["analyze_only"] = False
    kwargs["recommendations_only"] = True
    kwargs["no_docsible"] = True
    kwargs["complexity_report"] = True
    core_doc_the_role(**kwargs)
