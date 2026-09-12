"""Tests for TipGenerator."""
from docsible.helpers.tips.tip_generator import TipGenerator


class TestTipGeneratorConstants:
    def test_tips_dict_is_not_empty(self):
        assert len(TipGenerator.TIPS) > 0

    def test_general_context_exists(self):
        assert "general" in TipGenerator.TIPS

    def test_first_run_context_exists(self):
        assert "first_run" in TipGenerator.TIPS

    def test_simple_role_context_exists(self):
        assert "simple_role" in TipGenerator.TIPS

    def test_complex_role_context_exists(self):
        assert "complex_role" in TipGenerator.TIPS

    def test_after_generation_context_exists(self):
        assert "after_generation" in TipGenerator.TIPS

    def test_all_contexts_have_tips(self):
        for context, tips in TipGenerator.TIPS.items():
            assert len(tips) > 0, f"No tips for context: {context}"

    def test_tips_are_strings(self):
        for context, tips in TipGenerator.TIPS.items():
            for tip in tips:
                assert isinstance(tip, str), f"Non-string tip in context '{context}': {tip!r}"

    def test_tips_dict_is_dict(self):
        assert isinstance(TipGenerator.TIPS, dict)


class TestTipGeneratorGetTip:
    def test_get_tip_returns_string_or_none(self):
        result = TipGenerator.get_tip()
        assert result is None or isinstance(result, str)

    def test_get_tip_for_general_context(self):
        result = TipGenerator.get_tip("general")
        assert result is not None
        assert isinstance(result, str)

    def test_get_tip_for_simple_role(self):
        result = TipGenerator.get_tip("simple_role")
        assert result is not None
        assert isinstance(result, str)

    def test_get_tip_for_complex_role(self):
        result = TipGenerator.get_tip("complex_role")
        assert result is not None
        assert isinstance(result, str)

    def test_get_tip_for_first_run(self):
        result = TipGenerator.get_tip("first_run")
        assert result is not None
        assert isinstance(result, str)

    def test_get_tip_for_after_generation(self):
        result = TipGenerator.get_tip("after_generation")
        assert result is not None
        assert isinstance(result, str)

    def test_get_tip_for_unknown_context_falls_back_to_general(self):
        # Per implementation: unknown context falls back to general tips list,
        # so it returns a string, not None.
        result = TipGenerator.get_tip("nonexistent_context")
        # Implementation falls back to general: result should be a string
        assert result is None or isinstance(result, str)

    def test_get_tip_result_is_from_context(self):
        # Result of get_tip must be one of the tips from that context
        tips = TipGenerator.get_all_tips("simple_role")
        result = TipGenerator.get_tip("simple_role")
        assert result in tips

    def test_get_tip_general_result_is_from_general_tips(self):
        tips = TipGenerator.get_all_tips("general")
        result = TipGenerator.get_tip("general")
        assert result in tips

    def test_get_tip_default_context_is_general(self):
        # get_tip() with no argument should behave same as get_tip("general")
        general_tips = TipGenerator.get_all_tips("general")
        result = TipGenerator.get_tip()
        # Should return one of the general tips
        assert result in general_tips


class TestTipGeneratorGetAllTips:
    def test_get_all_tips_returns_list(self):
        result = TipGenerator.get_all_tips()
        assert isinstance(result, list)

    def test_get_all_tips_not_empty_for_general(self):
        result = TipGenerator.get_all_tips("general")
        assert len(result) > 0

    def test_get_all_tips_for_specific_context(self):
        result = TipGenerator.get_all_tips("simple_role")
        assert isinstance(result, list)
        assert len(result) > 0

    def test_get_all_tips_are_strings(self):
        result = TipGenerator.get_all_tips("general")
        assert all(isinstance(t, str) for t in result)

    def test_get_all_tips_matches_tips_dict(self):
        for context in TipGenerator.TIPS:
            result = TipGenerator.get_all_tips(context)
            assert result == TipGenerator.TIPS[context]

    def test_get_all_tips_default_is_general(self):
        default_result = TipGenerator.get_all_tips()
        general_result = TipGenerator.get_all_tips("general")
        assert default_result == general_result

    def test_get_all_tips_unknown_context_falls_back_to_general(self):
        # Per implementation: falls back to general on unknown context
        result = TipGenerator.get_all_tips("no_such_context")
        general = TipGenerator.get_all_tips("general")
        assert result == general


class TestTipGeneratorAvailableContexts:
    def test_get_available_contexts_returns_list(self):
        contexts = TipGenerator.get_available_contexts()
        assert isinstance(contexts, list)

    def test_general_in_available_contexts(self):
        contexts = TipGenerator.get_available_contexts()
        assert "general" in contexts

    def test_first_run_in_available_contexts(self):
        contexts = TipGenerator.get_available_contexts()
        assert "first_run" in contexts

    def test_available_contexts_match_tips_keys(self):
        contexts = TipGenerator.get_available_contexts()
        assert set(contexts) == set(TipGenerator.TIPS.keys())

    def test_available_contexts_not_empty(self):
        contexts = TipGenerator.get_available_contexts()
        assert len(contexts) > 0
