"""Tests for analysis settings wiring in the preset system.

Covers:
- Registry: each preset exposes fail_on / essential_only / max_recommendations
- DocsiblePresetConfig: new fields serialize/deserialize correctly
- resolve_settings(): preset values flow through to resolved dict
- resolve_settings(): config-level top-level fields flow into resolved kwargs
"""
import yaml

from docsible.presets.models import DocsiblePresetConfig
from docsible.presets.registry import PresetRegistry
from docsible.presets.resolver import resolve_settings

# ---------------------------------------------------------------------------
# Registry — per-preset analysis field values
# ---------------------------------------------------------------------------


class TestPersonalPresetAnalysisSettings:
    def setup_method(self):
        self.preset = PresetRegistry.get("personal")

    def test_fail_on_is_none(self):
        assert self.preset.settings["fail_on"] == "none"

    def test_essential_only_is_true(self):
        assert self.preset.settings["essential_only"] is True

    def test_max_recommendations_is_5(self):
        assert self.preset.settings["max_recommendations"] == 5


class TestTeamPresetAnalysisSettings:
    def setup_method(self):
        self.preset = PresetRegistry.get("team")

    def test_fail_on_is_warning(self):
        assert self.preset.settings["fail_on"] == "warning"

    def test_essential_only_is_false(self):
        assert self.preset.settings["essential_only"] is False

    def test_max_recommendations_is_10(self):
        assert self.preset.settings["max_recommendations"] == 10


class TestEnterprisePresetAnalysisSettings:
    def setup_method(self):
        self.preset = PresetRegistry.get("enterprise")

    def test_fail_on_is_critical(self):
        assert self.preset.settings["fail_on"] == "critical"

    def test_essential_only_is_false(self):
        assert self.preset.settings["essential_only"] is False

    def test_max_recommendations_is_none(self):
        assert self.preset.settings["max_recommendations"] is None


class TestConsultantPresetAnalysisSettings:
    def setup_method(self):
        self.preset = PresetRegistry.get("consultant")

    def test_fail_on_is_warning(self):
        assert self.preset.settings["fail_on"] == "warning"

    def test_essential_only_is_false(self):
        assert self.preset.settings["essential_only"] is False

    def test_max_recommendations_is_15(self):
        assert self.preset.settings["max_recommendations"] == 15


# ---------------------------------------------------------------------------
# DocsiblePresetConfig — new fields
# ---------------------------------------------------------------------------


class TestDocsiblePresetConfigAnalysisFields:
    def test_fail_on_defaults_to_none(self):
        cfg = DocsiblePresetConfig()
        assert cfg.fail_on is None

    def test_essential_only_defaults_to_none(self):
        cfg = DocsiblePresetConfig()
        assert cfg.essential_only is None

    def test_max_recommendations_defaults_to_none(self):
        cfg = DocsiblePresetConfig()
        assert cfg.max_recommendations is None

    def test_fail_on_set_to_warning(self):
        cfg = DocsiblePresetConfig(fail_on="warning")
        assert cfg.fail_on == "warning"

    def test_essential_only_set_to_false(self):
        cfg = DocsiblePresetConfig(essential_only=False)
        assert cfg.essential_only is False

    def test_max_recommendations_set_to_10(self):
        cfg = DocsiblePresetConfig(max_recommendations=10)
        assert cfg.max_recommendations == 10

    def test_round_trip_via_model_dump(self):
        """Fields survive a model_dump / model_validate round trip."""
        cfg = DocsiblePresetConfig(
            preset="team",
            fail_on="warning",
            essential_only=False,
            max_recommendations=10,
        )
        data = cfg.model_dump()
        restored = DocsiblePresetConfig(**data)
        assert restored.fail_on == "warning"
        assert restored.essential_only is False
        assert restored.max_recommendations == 10

    def test_round_trip_via_yaml(self):
        """Fields survive a YAML serialisation round trip (as config_manager does)."""
        cfg = DocsiblePresetConfig(fail_on="warning", essential_only=False, max_recommendations=10)
        raw = yaml.dump(cfg.model_dump(exclude_none=False), default_flow_style=False)
        data = yaml.safe_load(raw)
        restored = DocsiblePresetConfig(**data)
        assert restored.fail_on == "warning"
        assert restored.essential_only is False
        assert restored.max_recommendations == 10


# ---------------------------------------------------------------------------
# resolve_settings() — preset values flow through
# ---------------------------------------------------------------------------


class TestResolveSettingsPresetAnalysisFields:
    def test_team_preset_fail_on_warning(self, tmp_path):
        result = resolve_settings(preset_name="team", base_path=tmp_path)
        assert result.get("fail_on") == "warning"

    def test_team_preset_essential_only_false(self, tmp_path):
        result = resolve_settings(preset_name="team", base_path=tmp_path)
        assert result.get("essential_only") is False

    def test_team_preset_max_recommendations_10(self, tmp_path):
        result = resolve_settings(preset_name="team", base_path=tmp_path)
        assert result.get("max_recommendations") == 10

    def test_personal_preset_fail_on_none(self, tmp_path):
        result = resolve_settings(preset_name="personal", base_path=tmp_path)
        assert result.get("fail_on") == "none"

    def test_enterprise_preset_fail_on_critical(self, tmp_path):
        result = resolve_settings(preset_name="enterprise", base_path=tmp_path)
        assert result.get("fail_on") == "critical"

    def test_enterprise_preset_max_recommendations_none(self, tmp_path):
        result = resolve_settings(preset_name="enterprise", base_path=tmp_path)
        assert result.get("max_recommendations") is None

    def test_cli_override_wins_over_preset_fail_on(self, tmp_path):
        result = resolve_settings(
            preset_name="team",
            cli_overrides={"fail_on": "critical"},
            base_path=tmp_path,
        )
        assert result.get("fail_on") == "critical"

    def test_cli_override_wins_over_preset_essential_only(self, tmp_path):
        result = resolve_settings(
            preset_name="team",
            cli_overrides={"essential_only": True},
            base_path=tmp_path,
        )
        assert result.get("essential_only") is True


# ---------------------------------------------------------------------------
# resolve_settings() — config-level top-level fields flow into kwargs
# ---------------------------------------------------------------------------


class TestResolveSettingsConfigLevelAnalysisFields:
    def _write_config(self, tmp_path, data: dict) -> None:
        config_dir = tmp_path / ".docsible"
        config_dir.mkdir(parents=True, exist_ok=True)
        (config_dir / "config.yml").write_text(yaml.dump(data), encoding="utf-8")

    def test_config_fail_on_flows_into_resolved(self, tmp_path):
        self._write_config(tmp_path, {"preset": None, "overrides": {}, "fail_on": "warning"})
        result = resolve_settings(preset_name=None, base_path=tmp_path)
        assert result.get("fail_on") == "warning"

    def test_config_essential_only_flows_into_resolved(self, tmp_path):
        self._write_config(tmp_path, {"preset": None, "overrides": {}, "essential_only": False})
        result = resolve_settings(preset_name=None, base_path=tmp_path)
        assert result.get("essential_only") is False

    def test_config_max_recommendations_flows_into_resolved(self, tmp_path):
        self._write_config(
            tmp_path, {"preset": None, "overrides": {}, "max_recommendations": 7}
        )
        result = resolve_settings(preset_name=None, base_path=tmp_path)
        assert result.get("max_recommendations") == 7

    def test_config_fail_on_does_not_override_preset_value(self, tmp_path):
        """Preset says fail_on='none'; config top-level says 'warning'.
        Preset wins because resolved already has the value before setdefault."""
        self._write_config(
            tmp_path, {"preset": "personal", "overrides": {}, "fail_on": "warning"}
        )
        result = resolve_settings(preset_name=None, base_path=tmp_path)
        # personal preset sets fail_on="none"; config-level should not override it
        assert result.get("fail_on") == "none"

    def test_config_fail_on_not_set_when_cli_preset_given(self, tmp_path):
        """When preset_name is given on CLI, stored_config is never loaded,
        so config-level fail_on has no effect."""
        self._write_config(tmp_path, {"preset": "personal", "overrides": {}, "fail_on": "info"})
        # Explicitly passing preset_name bypasses config loading
        result = resolve_settings(preset_name="team", base_path=tmp_path)
        # team preset provides fail_on="warning"; config-level "info" is ignored
        assert result.get("fail_on") == "warning"

    def test_config_fail_on_with_no_preset_and_no_overrides(self, tmp_path):
        """No preset at all; only config-level field."""
        self._write_config(
            tmp_path, {"preset": None, "overrides": {}, "fail_on": "critical"}
        )
        result = resolve_settings(preset_name=None, base_path=tmp_path)
        assert result.get("fail_on") == "critical"
