"""Tests for docsible.presets.resolver — resolve_settings()."""
import yaml

from docsible.presets.resolver import resolve_settings


class TestResolverNoPreset:
    """Baseline: no preset, no config file."""

    def test_no_preset_no_config_returns_empty(self, tmp_path):
        result = resolve_settings(
            preset_name=None,
            cli_overrides=None,
            base_path=tmp_path,
        )
        assert result == {}

    def test_no_preset_no_config_with_none_overrides_returns_empty(self, tmp_path):
        result = resolve_settings(
            preset_name=None,
            cli_overrides={},
            base_path=tmp_path,
        )
        assert result == {}


class TestResolverWithPreset:
    """Preset applied without any config file or CLI overrides."""

    def test_personal_preset_returns_personal_settings(self, tmp_path):
        result = resolve_settings(preset_name="personal", base_path=tmp_path)
        assert result.get("minimal") is True
        assert result.get("generate_graph") is False

    def test_enterprise_preset_includes_generate_graph_true(self, tmp_path):
        result = resolve_settings(preset_name="enterprise", base_path=tmp_path)
        assert result.get("generate_graph") is True

    def test_enterprise_preset_includes_strict_validation_true(self, tmp_path):
        result = resolve_settings(preset_name="enterprise", base_path=tmp_path)
        assert result.get("strict_validation") is True

    def test_team_preset_returns_team_settings(self, tmp_path):
        result = resolve_settings(preset_name="team", base_path=tmp_path)
        assert result.get("auto_fix") is True
        assert result.get("comments") is True

    def test_consultant_preset_includes_show_dependencies(self, tmp_path):
        result = resolve_settings(preset_name="consultant", base_path=tmp_path)
        assert result.get("show_dependencies") is True
        assert result.get("generate_graph") is True


class TestResolverCliOverrides:
    """CLI flags always win over preset values."""

    def test_cli_overrides_win_over_preset(self, tmp_path):
        """enterprise sets generate_graph=True; CLI sets it to False — CLI wins."""
        result = resolve_settings(
            preset_name="enterprise",
            cli_overrides={"generate_graph": False},
            base_path=tmp_path,
        )
        assert result.get("generate_graph") is False

    def test_cli_override_strict_validation_over_enterprise(self, tmp_path):
        result = resolve_settings(
            preset_name="enterprise",
            cli_overrides={"strict_validation": False},
            base_path=tmp_path,
        )
        assert result.get("strict_validation") is False

    def test_cli_overrides_partial_still_preserves_preset_other_values(self, tmp_path):
        """Only the explicitly overridden key changes; others keep preset values."""
        result = resolve_settings(
            preset_name="enterprise",
            cli_overrides={"generate_graph": False},
            base_path=tmp_path,
        )
        # strict_validation was NOT overridden, should still be True from enterprise
        assert result.get("strict_validation") is True
        assert result.get("generate_graph") is False

    def test_none_cli_override_values_ignored(self, tmp_path):
        """Keys with None values in cli_overrides are filtered out."""
        result = resolve_settings(
            preset_name="enterprise",
            cli_overrides={"generate_graph": None, "strict_validation": False},
            base_path=tmp_path,
        )
        # generate_graph=None should be ignored -> falls through to preset value (True)
        assert result.get("generate_graph") is True
        assert result.get("strict_validation") is False


class TestResolverConfigFile:
    """config.yml overrides applied when no --preset CLI flag."""

    def _write_config(self, tmp_path, data: dict) -> None:
        config_dir = tmp_path / ".docsible"
        config_dir.mkdir(parents=True, exist_ok=True)
        (config_dir / "config.yml").write_text(yaml.dump(data), encoding="utf-8")

    def test_config_preset_field_used_when_no_cli_preset(self, tmp_path):
        self._write_config(tmp_path, {"preset": "personal", "overrides": {}, "ci_cd": {}})
        result = resolve_settings(preset_name=None, base_path=tmp_path)
        assert result.get("minimal") is True
        assert result.get("generate_graph") is False

    def test_config_overrides_applied_on_top_of_config_preset(self, tmp_path):
        self._write_config(
            tmp_path,
            {
                "preset": "personal",
                "overrides": {"generate_graph": True},
                "ci_cd": {},
            },
        )
        result = resolve_settings(preset_name=None, base_path=tmp_path)
        # override in config.yml should win over the personal preset value
        assert result.get("generate_graph") is True

    def test_config_overrides_applied_without_preset(self, tmp_path):
        self._write_config(
            tmp_path,
            {
                "preset": None,
                "overrides": {"generate_graph": True, "minimal": False},
                "ci_cd": {},
            },
        )
        result = resolve_settings(preset_name=None, base_path=tmp_path)
        assert result.get("generate_graph") is True
        assert result.get("minimal") is False

    def test_explicit_cli_preset_ignores_config_file_preset(self, tmp_path):
        """When preset is passed on CLI, config.yml preset field is ignored."""
        self._write_config(tmp_path, {"preset": "personal", "overrides": {}, "ci_cd": {}})
        result = resolve_settings(preset_name="enterprise", base_path=tmp_path)
        # enterprise, not personal
        assert result.get("strict_validation") is True
        assert result.get("generate_graph") is True

    def test_missing_config_file_no_error(self, tmp_path):
        """No config file and no preset should silently return empty dict."""
        result = resolve_settings(preset_name=None, base_path=tmp_path)
        assert result == {}
