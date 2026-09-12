"""Tests for the storage layer: resolve_suppress_path, load_store, save_store."""

from datetime import datetime, timedelta, timezone
from pathlib import Path

import yaml

from docsible.models.suppression import SuppressionRule, SuppressionStore
from docsible.suppression.store import load_store, resolve_suppress_path, save_store

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_rule(**kwargs) -> SuppressionRule:
    defaults = {
        "id": "abc12345",
        "pattern": "no examples",
        "reason": "Examples in separate repo",
    }
    defaults.update(kwargs)
    return SuppressionRule(**defaults)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# resolve_suppress_path
# ---------------------------------------------------------------------------

class TestResolvesuppresspath:
    def test_none_returns_cwd_based_path(self, monkeypatch, tmp_path):
        monkeypatch.chdir(tmp_path)
        result = resolve_suppress_path(None)
        assert result == tmp_path / ".docsible" / "suppress.yml"

    def test_explicit_base_path(self, tmp_path):
        result = resolve_suppress_path(tmp_path)
        assert result == tmp_path / ".docsible" / "suppress.yml"

    def test_explicit_absolute_path(self):
        base = Path("/some/path")
        result = resolve_suppress_path(base)
        assert result == Path("/some/path/.docsible/suppress.yml")


# ---------------------------------------------------------------------------
# load_store
# ---------------------------------------------------------------------------

class TestLoadStore:
    def test_returns_empty_store_when_file_missing(self, tmp_path):
        suppress_path = tmp_path / ".docsible" / "suppress.yml"
        store = load_store(suppress_path)
        assert isinstance(store, SuppressionStore)
        assert store.rules == []

    def test_handles_malformed_yaml_gracefully(self, tmp_path, caplog):
        suppress_path = tmp_path / ".docsible" / "suppress.yml"
        suppress_path.parent.mkdir(parents=True)
        suppress_path.write_text("rules: [{{{{bad yaml: [", encoding="utf-8")
        import logging
        with caplog.at_level(logging.WARNING):
            store = load_store(suppress_path)
        assert isinstance(store, SuppressionStore)
        assert store.rules == []
        # Should have logged a warning
        assert any("Failed to load" in r.message or "suppress" in r.message.lower()
                   for r in caplog.records)


# ---------------------------------------------------------------------------
# save_store + load_store roundtrip
# ---------------------------------------------------------------------------

class TestSaveLoadRoundtrip:
    def test_empty_store_roundtrip(self, tmp_path):
        suppress_path = tmp_path / ".docsible" / "suppress.yml"
        store = SuppressionStore()
        save_store(store, suppress_path)
        loaded = load_store(suppress_path)
        assert loaded.rules == []

    def test_roundtrip_preserves_all_fields(self, tmp_path):
        suppress_path = tmp_path / ".docsible" / "suppress.yml"
        now = datetime.now(timezone.utc).replace(microsecond=0)
        future = now + timedelta(days=30)

        rule = make_rule(
            id="deadbeef",
            pattern="missing readme",
            reason="Legacy role",
            file_pattern="roles/*",
            expires_at=future,
            approved_by="bob",
            match_count=3,
            last_matched=now,
            use_regex=True,
        )
        store = SuppressionStore(rules=[rule])
        save_store(store, suppress_path)
        loaded = load_store(suppress_path)

        assert len(loaded.rules) == 1
        r = loaded.rules[0]
        assert r.id == "deadbeef"
        assert r.pattern == "missing readme"
        assert r.reason == "Legacy role"
        assert r.file_pattern == "roles/*"
        assert r.approved_by == "bob"
        assert r.match_count == 3
        assert r.use_regex is True
        # Datetimes should survive roundtrip (compare to second precision)
        assert r.expires_at is not None
        assert abs((r.expires_at - future).total_seconds()) < 2
        assert r.last_matched is not None
        assert abs((r.last_matched - now).total_seconds()) < 2

    def test_roundtrip_preserves_multiple_rules(self, tmp_path):
        suppress_path = tmp_path / ".docsible" / "suppress.yml"
        rules = [
            make_rule(id=f"rule{i:04d}", pattern=f"pattern {i}", reason=f"reason {i}")
            for i in range(5)
        ]
        store = SuppressionStore(rules=rules)
        save_store(store, suppress_path)
        loaded = load_store(suppress_path)
        assert len(loaded.rules) == 5
        for i, r in enumerate(loaded.rules):
            assert r.id == f"rule{i:04d}"
            assert r.pattern == f"pattern {i}"

    def test_save_creates_parent_directories(self, tmp_path):
        deep_path = tmp_path / "a" / "b" / "c" / ".docsible" / "suppress.yml"
        assert not deep_path.parent.exists()
        store = SuppressionStore()
        save_store(store, deep_path)
        assert deep_path.exists()

    def test_save_produces_valid_yaml_with_rules_key(self, tmp_path):
        suppress_path = tmp_path / ".docsible" / "suppress.yml"
        rule = make_rule()
        store = SuppressionStore(rules=[rule])
        save_store(store, suppress_path)

        raw = suppress_path.read_text(encoding="utf-8")
        parsed = yaml.safe_load(raw)
        assert "rules" in parsed
        assert isinstance(parsed["rules"], list)
        assert len(parsed["rules"]) == 1

    def test_empty_store_writes_rules_empty_list(self, tmp_path):
        suppress_path = tmp_path / ".docsible" / "suppress.yml"
        save_store(SuppressionStore(), suppress_path)
        raw = suppress_path.read_text(encoding="utf-8")
        parsed = yaml.safe_load(raw)
        assert "rules" in parsed
        assert parsed["rules"] == []
