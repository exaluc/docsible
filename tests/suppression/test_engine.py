"""Tests for apply_suppressions and _find_matching_rule in docsible.suppression.engine."""

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import yaml

from docsible.models.suppression import SuppressionRule, SuppressionStore
from docsible.suppression.engine import apply_suppressions
from docsible.suppression.store import save_store

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


def make_recommendation(message: str, file_path: str | None = None) -> Any:
    """Create a MagicMock that mimics a Recommendation with .message and .file_path."""
    rec = MagicMock()
    rec.message = message
    rec.file_path = file_path
    return rec


def save_rules(tmp_path: Path, rules: list[SuppressionRule]) -> Path:
    """Write rules to the default suppress.yml location under tmp_path."""
    suppress_path = tmp_path / ".docsible" / "suppress.yml"
    store = SuppressionStore(rules=rules)
    save_store(store, suppress_path)
    return suppress_path


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestApplySuppressions:
    def test_no_suppress_yml_returns_all_visible(self, tmp_path):
        recs = [make_recommendation("no examples")]
        visible, suppressed = apply_suppressions(recs, base_path=tmp_path)
        assert visible == recs
        assert suppressed == []

    def test_empty_store_returns_all_visible(self, tmp_path):
        save_rules(tmp_path, [])
        recs = [make_recommendation("no examples")]
        visible, suppressed = apply_suppressions(recs, base_path=tmp_path)
        assert visible == recs
        assert suppressed == []

    def test_matching_recommendation_is_suppressed(self, tmp_path):
        rule = make_rule(pattern="no examples")
        save_rules(tmp_path, [rule])
        rec = make_recommendation("Role has no examples section")
        visible, suppressed = apply_suppressions([rec], base_path=tmp_path)
        assert suppressed == [rec]
        assert visible == []

    def test_non_matching_recommendation_stays_visible(self, tmp_path):
        rule = make_rule(pattern="no examples")
        save_rules(tmp_path, [rule])
        rec = make_recommendation("documentation is missing")
        visible, suppressed = apply_suppressions([rec], base_path=tmp_path)
        assert visible == [rec]
        assert suppressed == []

    def test_mixed_some_suppressed_some_visible(self, tmp_path):
        rule = make_rule(pattern="no examples")
        save_rules(tmp_path, [rule])
        rec_match = make_recommendation("no examples found")
        rec_no_match = make_recommendation("readme is empty")
        visible, suppressed = apply_suppressions([rec_match, rec_no_match], base_path=tmp_path)
        assert rec_match in suppressed
        assert rec_no_match in visible
        assert len(visible) == 1
        assert len(suppressed) == 1

    def test_expired_rule_does_not_suppress(self, tmp_path):
        past = datetime.now(timezone.utc) - timedelta(days=1)
        rule = make_rule(pattern="no examples", expires_at=past)
        save_rules(tmp_path, [rule])
        rec = make_recommendation("no examples found")
        visible, suppressed = apply_suppressions([rec], base_path=tmp_path)
        assert visible == [rec]
        assert suppressed == []

    def test_match_count_and_last_matched_updated_in_yaml(self, tmp_path):
        rule = make_rule(id="testid01", pattern="no examples", match_count=0)
        suppress_path = save_rules(tmp_path, [rule])
        rec = make_recommendation("no examples here")

        apply_suppressions([rec], base_path=tmp_path)

        # Re-read the YAML to verify persistence
        raw = suppress_path.read_text(encoding="utf-8")
        data = yaml.safe_load(raw)
        saved_rule = data["rules"][0]
        assert saved_rule["match_count"] == 1
        assert saved_rule["last_matched"] is not None

    def test_file_pattern_scoping_suppresses_matching_file(self, tmp_path):
        rule = make_rule(pattern="no examples", file_pattern="roles/*")
        save_rules(tmp_path, [rule])
        rec = make_recommendation("no examples found", file_path="roles/webserver")
        visible, suppressed = apply_suppressions([rec], base_path=tmp_path)
        assert rec in suppressed
        assert visible == []

    def test_file_pattern_scoping_does_not_suppress_non_matching_file(self, tmp_path):
        rule = make_rule(pattern="no examples", file_pattern="roles/*")
        save_rules(tmp_path, [rule])
        rec = make_recommendation("no examples found", file_path="collections/myns/role")
        visible, suppressed = apply_suppressions([rec], base_path=tmp_path)
        assert rec in visible
        assert suppressed == []

    def test_regex_mode_matching(self, tmp_path):
        rule = make_rule(pattern=r"no\s+example", use_regex=True)
        save_rules(tmp_path, [rule])
        rec = make_recommendation("Role has no   example blocks")
        visible, suppressed = apply_suppressions([rec], base_path=tmp_path)
        assert rec in suppressed
        assert visible == []

    def test_regex_mode_no_match(self, tmp_path):
        rule = make_rule(pattern=r"^strict_start", use_regex=True)
        save_rules(tmp_path, [rule])
        rec = make_recommendation("this does not match the strict start pattern")
        visible, suppressed = apply_suppressions([rec], base_path=tmp_path)
        assert rec in visible
        assert suppressed == []

    def test_multiple_rules_first_match_wins(self, tmp_path):
        rule1 = make_rule(id="rule0001", pattern="no examples")
        rule2 = make_rule(id="rule0002", pattern="no examples")
        save_rules(tmp_path, [rule1, rule2])
        rec = make_recommendation("no examples here")
        visible, suppressed = apply_suppressions([rec], base_path=tmp_path)
        assert rec in suppressed
        # Verify only first rule's match_count incremented
        suppress_path = tmp_path / ".docsible" / "suppress.yml"
        data = yaml.safe_load(suppress_path.read_text())
        assert data["rules"][0]["match_count"] == 1
        assert data["rules"][1]["match_count"] == 0

    def test_empty_recommendations_list(self, tmp_path):
        rule = make_rule(pattern="no examples")
        save_rules(tmp_path, [rule])
        visible, suppressed = apply_suppressions([], base_path=tmp_path)
        assert visible == []
        assert suppressed == []
