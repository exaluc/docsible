from docsible.analyzers.complexity_analyzer.models import ComplexityCategory as Category
from docsible.defaults.decisions.base import DecisionContext
from docsible.defaults.decisions.graph_rule import GraphDecisionRule


class TestGraphDecisionRule:
    """Test GraphDecisionRule decision logic."""

    def test_simple_role_no_graph(self):
        """Simple roles should not generate graphs."""
        context = DecisionContext(
            complexity_category=Category.SIMPLE,
            total_tasks=5,
            complexity_score=0.2,
            has_handlers=False,
            uses_advanced_features=False,
            task_file_count=1,
            user_overrides={}
        )

        rule = GraphDecisionRule()
        decision = rule.decide(context)

        assert decision is not None
        assert decision.value is False
        assert "Simple role" in decision.rationale

    def test_complex_role_needs_graph(self):
        """Complex roles should generate graphs."""
        context = DecisionContext(
            complexity_category=Category.COMPLEX,
            total_tasks=75,
            complexity_score=0.9,
            has_handlers=True,
            uses_advanced_features=True,
            task_file_count=8,
            user_overrides={}
        )

        rule = GraphDecisionRule()
        decision = rule.decide(context)

        assert decision is not None
        assert decision.value is True
        assert "Complex role" in decision.rationale

    def test_user_override_respected(self):
        """User overrides should be respected."""
        context = DecisionContext(
            complexity_category=Category.SIMPLE,
            total_tasks=5,
            complexity_score=0.2,
            has_handlers=False,
            uses_advanced_features=False,
            task_file_count=1,
            user_overrides={"generate_graph": True}  # User wants graphs
        )

        rule = GraphDecisionRule()
        decision = rule.decide(context)

        # Rule should abstain (return None) when user specified
        assert decision is None