"""Tests for SuppressionRule and SuppressionStore pydantic models."""

from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from docsible.models.suppression import SuppressionRule, SuppressionStore

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_rule(**kwargs) -> SuppressionRule:
    defaults = {
        "id": "abc12345",
        "pattern": "no examples",
        "reason": "Examples live in separate repo",
    }
    defaults.update(kwargs)
    return SuppressionRule(**defaults)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# SuppressionRule — creation
# ---------------------------------------------------------------------------

class TestSuppressionRuleCreation:
    def test_basic_creation(self):
        rule = make_rule()
        assert rule.id == "abc12345"
        assert rule.pattern == "no examples"
        assert rule.reason == "Examples live in separate repo"
        assert rule.file_pattern is None
        assert rule.expires_at is None
        assert rule.approved_by is None
        assert rule.match_count == 0
        assert rule.last_matched is None
        assert rule.use_regex is False

    def test_all_optional_fields(self):
        now = datetime.now(timezone.utc)
        future = now + timedelta(days=30)
        rule = make_rule(
            file_pattern="roles/webserver",
            expires_at=future,
            approved_by="alice",
            match_count=5,
            last_matched=now,
            use_regex=True,
        )
        assert rule.file_pattern == "roles/webserver"
        assert rule.expires_at == future
        assert rule.approved_by == "alice"
        assert rule.match_count == 5
        assert rule.last_matched == now
        assert rule.use_regex is True


# ---------------------------------------------------------------------------
# SuppressionRule — validators
# ---------------------------------------------------------------------------

class TestSuppressionRuleValidators:
    def test_pattern_not_empty_raises_on_empty_string(self):
        with pytest.raises(ValidationError, match="pattern must not be empty"):
            make_rule(pattern="")

    def test_pattern_not_empty_raises_on_whitespace(self):
        with pytest.raises(ValidationError, match="pattern must not be empty"):
            make_rule(pattern="   ")

    def test_pattern_is_stripped(self):
        rule = make_rule(pattern="  foo  ")
        assert rule.pattern == "foo"

    def test_reason_not_empty_raises_on_empty_string(self):
        with pytest.raises(ValidationError, match="reason must not be empty"):
            make_rule(reason="")

    def test_reason_not_empty_raises_on_whitespace(self):
        with pytest.raises(ValidationError, match="reason must not be empty"):
            make_rule(reason="\t\n")

    def test_reason_is_stripped(self):
        rule = make_rule(reason="  valid reason  ")
        assert rule.reason == "valid reason"


# ---------------------------------------------------------------------------
# SuppressionRule.is_expired()
# ---------------------------------------------------------------------------

class TestIsExpired:
    def test_no_expiry_returns_false(self):
        rule = make_rule(expires_at=None)
        assert rule.is_expired() is False

    def test_future_expiry_returns_false(self):
        future = datetime.now(timezone.utc) + timedelta(days=30)
        rule = make_rule(expires_at=future)
        assert rule.is_expired() is False

    def test_past_expiry_returns_true(self):
        past = datetime.now(timezone.utc) - timedelta(days=1)
        rule = make_rule(expires_at=past)
        assert rule.is_expired() is True


# ---------------------------------------------------------------------------
# SuppressionRule.matches_message()
# ---------------------------------------------------------------------------

class TestMatchesMessage:
    def test_case_insensitive_substring_match(self):
        rule = make_rule(pattern="no examples")
        assert rule.matches_message("Role has no examples section") is True

    def test_case_insensitive_uppercase_message(self):
        rule = make_rule(pattern="no examples")
        assert rule.matches_message("NO EXAMPLES FOUND") is True

    def test_exact_match(self):
        rule = make_rule(pattern="no examples")
        assert rule.matches_message("no examples") is True

    def test_no_match(self):
        rule = make_rule(pattern="no examples")
        assert rule.matches_message("documentation is missing") is False

    def test_regex_mode_match(self):
        rule = make_rule(pattern=r"no\s+example", use_regex=True)
        assert rule.matches_message("Role has no    example section") is True

    def test_regex_mode_no_match(self):
        rule = make_rule(pattern=r"^strict_start", use_regex=True)
        assert rule.matches_message("this does not start strictly") is False

    def test_regex_mode_case_insensitive(self):
        rule = make_rule(pattern=r"NO EXAMPLES", use_regex=True)
        assert rule.matches_message("no examples here") is True


# ---------------------------------------------------------------------------
# SuppressionRule.matches_file()
# ---------------------------------------------------------------------------

class TestMatchesFile:
    def test_none_file_pattern_matches_all(self):
        rule = make_rule(file_pattern=None)
        assert rule.matches_file("roles/webserver/tasks/main.yml") is True
        assert rule.matches_file(None) is True
        assert rule.matches_file("any/file.yml") is True

    def test_specific_pattern_matches(self):
        rule = make_rule(file_pattern="roles/webserver")
        assert rule.matches_file("roles/webserver") is True

    def test_glob_wildcard_matches(self):
        rule = make_rule(file_pattern="roles/*")
        assert rule.matches_file("roles/webserver") is True
        assert rule.matches_file("roles/database") is True

    def test_glob_wildcard_no_match(self):
        rule = make_rule(file_pattern="roles/*")
        assert rule.matches_file("collections/myns/myrole") is False

    def test_specific_pattern_no_match(self):
        rule = make_rule(file_pattern="roles/webserver")
        assert rule.matches_file("roles/database") is False

    def test_file_path_none_with_file_pattern_returns_false(self):
        rule = make_rule(file_pattern="roles/*")
        assert rule.matches_file(None) is False


# ---------------------------------------------------------------------------
# SuppressionStore
# ---------------------------------------------------------------------------

class TestSuppressionStore:
    def _make_store(self, *rules: SuppressionRule) -> SuppressionStore:
        return SuppressionStore(rules=list(rules))

    def test_find_by_id_found(self):
        rule = make_rule(id="aabbccdd")
        store = self._make_store(rule)
        found = store.find_by_id("aabbccdd")
        assert found is rule

    def test_find_by_id_not_found(self):
        rule = make_rule(id="aabbccdd")
        store = self._make_store(rule)
        assert store.find_by_id("zzzzzzzz") is None

    def test_remove_by_id_removes_correctly(self):
        rule1 = make_rule(id="id000001")
        rule2 = make_rule(id="id000002")
        store = self._make_store(rule1, rule2)
        result = store.remove_by_id("id000001")
        assert result is True
        assert len(store.rules) == 1
        assert store.rules[0].id == "id000002"

    def test_remove_by_id_returns_false_on_missing(self):
        rule = make_rule(id="id000001")
        store = self._make_store(rule)
        result = store.remove_by_id("doesntexist")
        assert result is False
        assert len(store.rules) == 1

    def test_expired_rules_returns_only_expired(self):
        past = datetime.now(timezone.utc) - timedelta(days=1)
        future = datetime.now(timezone.utc) + timedelta(days=1)
        expired = make_rule(id="exp00001", expires_at=past)
        active = make_rule(id="act00001", expires_at=future)
        no_expiry = make_rule(id="noe00001")
        store = self._make_store(expired, active, no_expiry)
        expired_list = store.expired_rules()
        assert len(expired_list) == 1
        assert expired_list[0].id == "exp00001"

    def test_active_rules_returns_non_expired(self):
        past = datetime.now(timezone.utc) - timedelta(days=1)
        future = datetime.now(timezone.utc) + timedelta(days=1)
        expired = make_rule(id="exp00001", expires_at=past)
        active = make_rule(id="act00001", expires_at=future)
        no_expiry = make_rule(id="noe00001")
        store = self._make_store(expired, active, no_expiry)
        active_list = store.active_rules()
        ids = {r.id for r in active_list}
        assert ids == {"act00001", "noe00001"}
        assert "exp00001" not in ids

    def test_empty_store_has_no_rules(self):
        store = SuppressionStore()
        assert store.rules == []
        assert store.expired_rules() == []
        assert store.active_rules() == []
