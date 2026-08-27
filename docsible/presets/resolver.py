"""Resolve final settings from preset + config overrides + CLI flags."""

from pathlib import Path
from typing import Any

from .config_manager import ConfigManager, resolve_config_path
from .registry import PresetRegistry


def resolve_settings(
    preset_name: str | None,
    cli_overrides: dict[str, Any] | None = None,
    base_path: Path | None = None,
) -> dict[str, Any]:
    """Merge preset defaults, config.yml overrides, and explicit CLI flags.

    Priority (low -> high):
      1. Built-in preset defaults (from PresetRegistry)
      2. .docsible/config.yml `overrides` block
      3. Explicit CLI flags (cli_overrides)

    Args:
        preset_name: Name of the preset to apply, or None for no preset
        cli_overrides: Dict of CLI flags the user explicitly set (non-default values)
        base_path: Base path for locating .docsible/config.yml

    Returns:
        Flat dict of resolved settings ready to be passed to core_doc_the_role()
    """
    resolved: dict[str, Any] = {}

    # 1. Apply preset defaults
    effective_preset = preset_name
    config_path = resolve_config_path(base_path)
    manager = ConfigManager()
    stored_config = manager.load(config_path)
    if effective_preset is None:
        # A command-line preset takes precedence over the project's preset.
        effective_preset = stored_config.preset

    # Project overrides apply whether the preset came from the project or CLI.
    resolved.update(stored_config.overrides)

    if effective_preset:
        preset = PresetRegistry.get(effective_preset)
        base = dict(preset.settings)
        base.update(resolved)  # config overrides win over preset
        resolved = base

    # Apply config-level analysis settings (from .docsible/config.yml top-level fields)
    # Use setdefault so preset settings don't override explicit CLI flags, and so that
    # these only fill in gaps not already covered by the preset or config overrides.
    if stored_config.fail_on is not None:
        resolved.setdefault("fail_on", stored_config.fail_on)
    if stored_config.essential_only is not None:
        resolved.setdefault("essential_only", stored_config.essential_only)
    if stored_config.max_recommendations is not None:
        resolved.setdefault("max_recommendations", stored_config.max_recommendations)

    # 3. CLI overrides always win
    if cli_overrides:
        resolved.update({k: v for k, v in cli_overrides.items() if v is not None})

    return resolved
