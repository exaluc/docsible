"""Shared resolution of role-command options, presets, and role config."""

from pathlib import Path
from typing import Any

import click

from docsible.presets.resolver import resolve_settings


def resolve_role_command_options(
    preset: str | None,
    kwargs: dict[str, Any],
) -> dict[str, Any]:
    """Apply role-local configuration and explicit CLI options to command values."""
    ctx = click.get_current_context()
    explicit_options = {
        name: value
        for name, value in kwargs.items()
        if ctx.get_parameter_source(name) is click.core.ParameterSource.COMMANDLINE
    }
    role_path = kwargs.get("role_path")
    resolved = resolve_settings(
        preset_name=preset,
        cli_overrides=explicit_options,
        base_path=Path(role_path) if role_path else None,
    )
    kwargs["_minimal_explicit"] = "minimal" in resolved
    kwargs.update(resolved)
    kwargs["_explicit_options"] = explicit_options
    return kwargs
