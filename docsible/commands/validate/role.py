"""docsible validate role — validate without writing files."""

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
@click.option(
    "--strict/--no-strict",
    "strict_validation",
    default=True,
    help="Fail on validation warnings (default: on for validate intent).",
)
def validate_role_cmd(preset, strict_validation, **kwargs) -> None:
    """Validate documentation for an Ansible role (no files written)."""
    ctx = click.get_current_context()
    strict_source = ctx.get_parameter_source("strict_validation")
    # add_output_options supplies the shared false default; validate's default is strict.
    kwargs["strict_validation"] = (
        True if strict_source is click.core.ParameterSource.DEFAULT else strict_validation
    )
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
    # Validate renders and checks markdown in memory only.
    kwargs["validate_markdown"] = True
    kwargs["validate_only"] = True
    kwargs["dry_run"] = True
    kwargs["no_docsible"] = True
    kwargs["analyze_only"] = False
    core_doc_the_role(**kwargs)
