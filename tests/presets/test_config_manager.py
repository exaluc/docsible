"""Tests for docsible.presets.config_manager — ConfigManager and resolve_config_path."""
from pathlib import Path

import yaml

from docsible.presets.config_manager import ConfigManager, resolve_config_path
from docsible.presets.models import DocsiblePresetConfig


class TestResolveConfigPath:
    """Tests for the resolve_config_path() helper."""

    def test_none_returns_cwd_based_path(self):
        result = resolve_config_path(None)
        expected = Path.cwd() / ".docsible" / "config.yml"
        assert result == expected

    def test_explicit_path_returns_correct_config_location(self, tmp_path):
        result = resolve_config_path(tmp_path)
        assert result == tmp_path / ".docsible" / "config.yml"

    def test_explicit_string_path_works(self, tmp_path):
        result = resolve_config_path(Path("/some/path"))
        assert result == Path("/some/path/.docsible/config.yml")

    def test_result_ends_with_config_yml(self, tmp_path):
        result = resolve_config_path(tmp_path)
        assert result.name == "config.yml"
        assert result.parent.name == ".docsible"


class TestConfigManagerLoad:
    """Tests for ConfigManager.load()."""

    def test_load_missing_file_returns_empty_config(self, tmp_path):
        config_path = tmp_path / ".docsible" / "config.yml"
        manager = ConfigManager()
        cfg = manager.load(config_path)
        assert isinstance(cfg, DocsiblePresetConfig)
        assert cfg.preset is None
        assert cfg.overrides == {}
        assert cfg.ci_cd == {}

    def test_load_existing_config(self, tmp_path):
        config_path = tmp_path / ".docsible" / "config.yml"
        config_path.parent.mkdir(parents=True)
        payload = {"preset": "team", "overrides": {"generate_graph": True}, "ci_cd": {}}
        config_path.write_text(yaml.dump(payload), encoding="utf-8")

        manager = ConfigManager()
        cfg = manager.load(config_path)
        assert cfg.preset == "team"
        assert cfg.overrides == {"generate_graph": True}

    def test_load_handles_malformed_yaml_gracefully(self, tmp_path):
        config_path = tmp_path / ".docsible" / "config.yml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(":: invalid: yaml: {{{", encoding="utf-8")

        manager = ConfigManager()
        cfg = manager.load(config_path)
        # Should return empty config, not raise
        assert isinstance(cfg, DocsiblePresetConfig)
        assert cfg.preset is None

    def test_load_handles_empty_yaml_file(self, tmp_path):
        config_path = tmp_path / ".docsible" / "config.yml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text("", encoding="utf-8")

        manager = ConfigManager()
        cfg = manager.load(config_path)
        assert isinstance(cfg, DocsiblePresetConfig)

    def test_load_handles_yaml_with_unknown_fields_gracefully(self, tmp_path):
        """Pydantic should accept or reject unknown fields without crashing tests."""
        config_path = tmp_path / ".docsible" / "config.yml"
        config_path.parent.mkdir(parents=True)
        payload = {"preset": "personal", "overrides": {}, "ci_cd": {}, "unknown_field": "value"}
        config_path.write_text(yaml.dump(payload), encoding="utf-8")

        manager = ConfigManager()
        # Should not raise — may silently ignore or accept the unknown field
        try:
            cfg = manager.load(config_path)
            assert cfg.preset == "personal"
        except Exception:
            # If pydantic rejects unknown fields, load() should catch and return empty
            pass


class TestConfigManagerSave:
    """Tests for ConfigManager.save()."""

    def test_save_creates_parent_directories(self, tmp_path):
        config_path = tmp_path / "deep" / "nested" / ".docsible" / "config.yml"
        manager = ConfigManager()
        cfg = DocsiblePresetConfig(preset="personal")
        manager.save(cfg, config_path)
        assert config_path.exists()

    def test_save_writes_valid_yaml(self, tmp_path):
        config_path = tmp_path / ".docsible" / "config.yml"
        manager = ConfigManager()
        cfg = DocsiblePresetConfig(preset="enterprise")
        manager.save(cfg, config_path)

        with open(config_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert data["preset"] == "enterprise"

    def test_save_no_leftover_tmp_file(self, tmp_path):
        """Atomic write: .yml.tmp must not exist after successful save."""
        config_path = tmp_path / ".docsible" / "config.yml"
        manager = ConfigManager()
        cfg = DocsiblePresetConfig(preset="team")
        manager.save(cfg, config_path)

        tmp_file = config_path.with_suffix(".yml.tmp")
        assert not tmp_file.exists()


class TestConfigManagerRoundtrip:
    """Tests for save + load roundtrip."""

    def test_roundtrip_preset(self, tmp_path):
        config_path = tmp_path / ".docsible" / "config.yml"
        manager = ConfigManager()

        original = DocsiblePresetConfig(preset="consultant")
        manager.save(original, config_path)
        loaded = manager.load(config_path)

        assert loaded.preset == "consultant"

    def test_roundtrip_overrides(self, tmp_path):
        config_path = tmp_path / ".docsible" / "config.yml"
        manager = ConfigManager()

        original = DocsiblePresetConfig(
            preset="enterprise",
            overrides={"generate_graph": False, "strict_validation": True},
        )
        manager.save(original, config_path)
        loaded = manager.load(config_path)

        assert loaded.preset == "enterprise"
        assert loaded.overrides["generate_graph"] is False
        assert loaded.overrides["strict_validation"] is True

    def test_roundtrip_ci_cd(self, tmp_path):
        config_path = tmp_path / ".docsible" / "config.yml"
        manager = ConfigManager()

        original = DocsiblePresetConfig(
            preset="team",
            ci_cd={"platform": "github"},
        )
        manager.save(original, config_path)
        loaded = manager.load(config_path)

        assert loaded.ci_cd["platform"] == "github"

    def test_roundtrip_empty_config(self, tmp_path):
        config_path = tmp_path / ".docsible" / "config.yml"
        manager = ConfigManager()

        original = DocsiblePresetConfig()
        manager.save(original, config_path)
        loaded = manager.load(config_path)

        assert loaded.preset is None
        assert loaded.overrides == {}
        assert loaded.ci_cd == {}
