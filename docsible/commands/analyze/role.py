"""docsible analyze role — analyze without generating docs."""

from pathlib import Path

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
)
from docsible.presets.registry import PresetRegistry
from docsible.presets.resolver import resolve_settings


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
    ctx = click.get_current_context()
    explicit = {
        name: value
        for name, value in kwargs.items()
        if ctx.get_parameter_source(name) is click.core.ParameterSource.COMMANDLINE
    }
    role_path = kwargs.get("role_path")
    resolved = resolve_settings(
        preset_name=preset,
        cli_overrides=explicit,
        base_path=Path(role_path) if role_path else None,
    )
    kwargs["_minimal_explicit"] = "minimal" in resolved
    kwargs.update(resolved)
    kwargs["_explicit_options"] = explicit
    # Analyze runs the recommendation pipeline but never renders documentation.
    kwargs["analyze_only"] = False
    kwargs["recommendations_only"] = True
    kwargs["no_docsible"] = True
    kwargs["complexity_report"] = True
    core_doc_the_role(**kwargs)
