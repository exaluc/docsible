from docsible.analyzers.complexity_analyzer.models import ComplexityCategory as Category
from docsible.defaults.decisions.base import DecisionContext
from docsible.defaults.decisions.dependencies_rule import DependenciesDecisionRule


class TestDependenciesDecisionRule:
    """Test DependenciesDecisionRule in isolation."""

    def test_rule_has_correct_priority(self):
        """Test that priority is 90 (higher than graph/minimal)."""
        rule = DependenciesDecisionRule()
        assert rule.priority == 90

    def test_role_with_dependencies_shows_them(self):
        """Test that roles with dependencies enable show_dependencies."""
        rule = DependenciesDecisionRule()

        context = DecisionContext(
            complexity_category=Category.MEDIUM,
            total_tasks=15,
            complexity_score=0.4,
            has_dependencies=True,  # Role has dependencies!
            has_handlers=True,
            uses_advanced_features=False,
            task_file_count=3,
            user_overrides={}
        )

        decision = rule.decide(context)

        assert decision is not None
        assert decision.option_name == "show_dependencies"
        assert decision.value is True
        assert decision.confidence == 0.9
        assert "dependencies that should be documented" in decision.rationale
        assert decision.rule_name == "DependenciesDecisionRule"

    def test_role_without_dependencies_doesnt_show(self):
        """Test that roles without dependencies disable show_dependencies."""
        rule = DependenciesDecisionRule()

        context = DecisionContext(
            complexity_category=Category.SIMPLE,
            total_tasks=5,
            complexity_score=0.2,
            has_dependencies=False,  # No dependencies
            has_handlers=False,
            uses_advanced_features=False,
            task_file_count=1,
            user_overrides={}
        )

        decision = rule.decide(context)

        assert decision is not None
        assert decision.option_name == "show_dependencies"
        assert decision.value is False
        assert decision.confidence == 0.8
        assert "no dependencies to document" in decision.rationale

    def test_complex_role_without_detected_dependencies(self):
        """Test that complex roles get moderate confidence even without detected deps."""
        rule = DependenciesDecisionRule()

        context = DecisionContext(
            complexity_category=Category.COMPLEX,
            total_tasks=35,
            complexity_score=0.7,
            has_dependencies=False,  # Not detected, but complex role
            has_handlers=True,
            uses_advanced_features=True,
            task_file_count=6,
            user_overrides={}
        )

        decision = rule.decide(context)

        assert decision is not None
        assert decision.option_name == "show_dependencies"
        assert decision.value is True
        assert decision.confidence == 0.5  # Lower confidence - we're guessing
        assert "Complex role" in decision.rationale
        assert "may have dependencies" in decision.rationale

    def test_user_override_respected(self):
        """Test that user explicit setting is respected."""
        rule = DependenciesDecisionRule()

        context = DecisionContext(
            complexity_category=Category.MEDIUM,
            total_tasks=15,
            complexity_score=0.4,
            has_dependencies=True,
            has_handlers=True,
            uses_advanced_features=False,
            task_file_count=3,
            user_overrides={"show_dependencies": False}  # User explicitly disabled
        )

        decision = rule.decide(context)

        # Should return None (abstain) because user explicitly set it
        assert decision is None

    def test_medium_role_without_dependencies(self):
        """Test medium role without dependencies gets False."""
        rule = DependenciesDecisionRule()

        context = DecisionContext(
            complexity_category=Category.MEDIUM,
            total_tasks=15,
            complexity_score=0.4,
            has_dependencies=False,
            has_handlers=True,
            uses_advanced_features=False,
            task_file_count=3,
            user_overrides={}
        )

        decision = rule.decide(context)

        assert decision is not None
        assert decision.value is False
        assert decision.confidence == 0.8

    def test_enterprise_role_triggers_complex_logic(self):
        """Test that ENTERPRISE category triggers complex role logic."""
        rule = DependenciesDecisionRule()

        context = DecisionContext(
            complexity_category=Category.ENTERPRISE,
            total_tasks=100,
            complexity_score=0.9,
            has_dependencies=False,
            has_handlers=True,
            uses_advanced_features=True,
            task_file_count=10,
            user_overrides={}
        )

        decision = rule.decide(context)

        assert decision is not None
        assert decision.value is True
        assert decision.confidence == 0.5  # Moderate confidence
        assert "Complex role" in decision.rationale

    def test_decision_is_overrideable(self):
        """Test that decisions are overrideable by default."""
        rule = DependenciesDecisionRule()

        context = DecisionContext(
            complexity_category=Category.SIMPLE,
            total_tasks=5,
            complexity_score=0.2,
            has_dependencies=False,
            has_handlers=False,
            uses_advanced_features=False,
            task_file_count=1,
            user_overrides={}
        )

        decision = rule.decide(context)

        assert decision is not None
        assert decision.overrideable is True
