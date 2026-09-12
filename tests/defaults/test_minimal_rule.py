from docsible.analyzers.complexity_analyzer.models import ComplexityCategory as Category
from docsible.defaults.decisions.base import DecisionContext
from docsible.defaults.decisions.minimal_rule import MinimalModeRule


class TestMinimalModeRule:
    """Test minimal mode decision logic."""

    def test_rule_has_correct_priority(self):
        """Test that minimal rule has priority 80."""
        rule = MinimalModeRule()
        assert rule.priority == 80

    def test_simple_role_gets_minimal_mode(self):
        """Test that simple role with 1 file gets minimal mode."""
        context = DecisionContext(
            complexity_category=Category.SIMPLE,
            total_tasks=3,  # <= 5 threshold
            complexity_score=0.2,
            has_dependencies=False,
            has_handlers=False,  # No handlers
            uses_advanced_features=False,  # No includes/imports/roles
            task_file_count=1,  # Single file
            user_overrides={},
        )

        rule = MinimalModeRule()
        decision = rule.decide(context)

        assert decision is not None
        assert decision.option_name == "minimal"
        assert decision.value is True
        assert decision.confidence >= 0.6
        assert decision.rule_name == "MinimalModeRule"
        assert "Simple role" in decision.rationale

    def test_role_with_handlers_not_minimal(self):
        """Test that role with handlers doesn't get minimal mode."""
        context = DecisionContext(
            complexity_category=Category.SIMPLE,
            total_tasks=3,
            complexity_score=0.2,
            has_dependencies=False,
            has_handlers=True,  # Has handlers
            uses_advanced_features=False,
            task_file_count=1,
            user_overrides={},
        )

        rule = MinimalModeRule()
        decision = rule.decide(context)

        assert decision is not None
        assert decision.option_name == "minimal"
        assert decision.value is False
        assert "complexity justifies" in decision.rationale

    def test_role_with_multiple_files_not_minimal(self):
        """Test that role with multiple task files doesn't get minimal mode."""
        context = DecisionContext(
            complexity_category=Category.SIMPLE,
            total_tasks=4,
            complexity_score=0.3,
            has_dependencies=False,
            has_handlers=False,
            uses_advanced_features=False,
            task_file_count=3,  # Multiple files
            user_overrides={},
        )

        rule = MinimalModeRule()
        decision = rule.decide(context)

        assert decision is not None
        assert decision.value is False

    def test_role_with_advanced_features_not_minimal(self):
        """Test that role using includes/imports doesn't get minimal mode."""
        context = DecisionContext(
            complexity_category=Category.SIMPLE,
            total_tasks=4,
            complexity_score=0.3,
            has_dependencies=False,
            has_handlers=False,
            uses_advanced_features=True,  # Uses advanced features
            task_file_count=1,
            user_overrides={},
        )

        rule = MinimalModeRule()
        decision = rule.decide(context)

        assert decision is not None
        assert decision.value is False

    def test_too_many_tasks_not_minimal(self):
        """Test that role with >5 tasks doesn't get minimal mode."""
        context = DecisionContext(
            complexity_category=Category.MEDIUM,
            total_tasks=10,  # > 5 threshold
            complexity_score=0.4,
            has_dependencies=False,
            has_handlers=False,
            uses_advanced_features=False,
            task_file_count=1,
            user_overrides={},
        )

        rule = MinimalModeRule()
        decision = rule.decide(context)

        assert decision is not None
        assert decision.value is False

    def test_user_override_respected(self):
        """Test that user-specified minimal mode is not overridden."""
        context = DecisionContext(
            complexity_category=Category.SIMPLE,
            total_tasks=3,
            complexity_score=0.2,
            has_dependencies=False,
            has_handlers=False,
            uses_advanced_features=False,
            task_file_count=1,
            user_overrides={"minimal": True},  # User explicitly set
        )

        rule = MinimalModeRule()
        decision = rule.decide(context)

        # Rule should abstain when user specified
        assert decision is None

    def test_minimal_criteria_threshold(self):
        """Test exact threshold at 5 tasks."""
        # Exactly 5 tasks should still get minimal (<=5)
        context_at_threshold = DecisionContext(
            complexity_category=Category.SIMPLE,
            total_tasks=5,  # At threshold
            complexity_score=0.3,
            has_dependencies=False,
            has_handlers=False,
            uses_advanced_features=False,
            task_file_count=1,
            user_overrides={},
        )

        rule = MinimalModeRule()
        decision = rule.decide(context_at_threshold)

        assert decision is not None
        assert decision.value is True

        # 6 tasks should not get minimal (>5)
        context_over_threshold = DecisionContext(
            complexity_category=Category.SIMPLE,
            total_tasks=6,  # Over threshold
            complexity_score=0.3,
            has_dependencies=False,
            has_handlers=False,
            uses_advanced_features=False,
            task_file_count=1,
            user_overrides={},
        )

        decision_over = rule.decide(context_over_threshold)

        assert decision_over is not None
        assert decision_over.value is False

    def test_medium_complexity_not_minimal(self):
        """Test that medium complexity roles don't get minimal mode."""
        context = DecisionContext(
            complexity_category=Category.MEDIUM,
            total_tasks=15,
            complexity_score=0.5,
            has_dependencies=False,
            has_handlers=False,
            uses_advanced_features=False,
            task_file_count=3,
            user_overrides={},
        )

        rule = MinimalModeRule()
        decision = rule.decide(context)

        assert decision is not None
        assert decision.value is False

    def test_complex_role_not_minimal(self):
        """Test that complex roles never get minimal mode."""
        context = DecisionContext(
            complexity_category=Category.COMPLEX,
            total_tasks=30,
            complexity_score=0.8,
            has_dependencies=True,
            has_handlers=True,
            uses_advanced_features=True,
            task_file_count=5,
            user_overrides={},
        )

        rule = MinimalModeRule()
        decision = rule.decide(context)

        assert decision is not None
        assert decision.value is False
        assert decision.confidence >= 0.5
