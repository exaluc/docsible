"""Tests for generate_rule_id in docsible.suppression.id_gen."""

import re

from docsible.suppression.id_gen import generate_rule_id


class TestGenerateRuleId:
    def test_returns_8_character_string(self):
        result = generate_rule_id("some pattern")
        assert isinstance(result, str)
        assert len(result) == 8

    def test_returns_lowercase_hex_string(self):
        result = generate_rule_id("some pattern")
        assert re.fullmatch(r"[0-9a-f]{8}", result), f"Not a lowercase hex string: {result!r}"

    def test_two_calls_same_pattern_produce_different_ids(self):
        id1 = generate_rule_id("no examples")
        id2 = generate_rule_id("no examples")
        assert id1 != id2, "IDs should be unique across calls even for the same pattern"

    def test_works_with_empty_string(self):
        result = generate_rule_id("")
        assert isinstance(result, str)
        assert len(result) == 8
        assert re.fullmatch(r"[0-9a-f]{8}", result)

    def test_works_with_unicode_pattern(self):
        result = generate_rule_id("パターン unicode pattern")
        assert isinstance(result, str)
        assert len(result) == 8
        assert re.fullmatch(r"[0-9a-f]{8}", result)

    def test_works_with_long_pattern(self):
        long_pattern = "x" * 10000
        result = generate_rule_id(long_pattern)
        assert isinstance(result, str)
        assert len(result) == 8
        assert re.fullmatch(r"[0-9a-f]{8}", result)

    def test_multiple_calls_produce_all_different_ids(self):
        ids = [generate_rule_id("test") for _ in range(10)]
        # With UUID+time entropy all 10 should be unique
        assert len(set(ids)) == 10
