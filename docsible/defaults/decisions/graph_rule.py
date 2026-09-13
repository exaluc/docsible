"""Decision rule for graph generation."""

import logging

from docsible.constants import MAX_TASK_FILES_LOWER_BOUND, MAX_TASKS_IN_FILES
from docsible.defaults.decisions.base import Decision, DecisionContext, DecisionRule

logger = logging.getLogger(__name__)


class GraphDecisionRule(DecisionRule):
    """Decides whether to generate Mermaid diagrams.

    Business Logic:
    - Simple roles (< 10 tasks): No diagrams needed
    - Medium roles (10-50 tasks): Optional, user preference
    - Complex roles (50+ tasks): Diagrams highly recommended

    This encapsulates domain knowledge about when diagrams add value.
    """

    @property
    def priority(self) -> int:
        """Priority 100 = normal business logic (not override, not fallback)."""
        return 100

    def decide(self, context: DecisionContext) -> Decision | None:
        """Decide on graph generation.

        Decision tree:
        1. If user explicitly set --graph or --no-diagrams → respect it
        2. If simple role (< 10 tasks, 1 file) → no graphs needed
        3. If complex role (COMPLEX category OR > 5 files) → graphs highly recommended
        4. If medium role (11-25 tasks OR 2-5 files) → graphs recommended with moderate confidence
        5. Otherwise → default to graphs for visibility
        """
        # 1. Check for user override
        if context.user_specified("generate_graph"):
            # User explicitly set this, don't override
            return None

        if context.user_specified("no_diagrams"):
            # User explicitly disabled diagrams
            return Decision(
                option_name="generate_graph",
                value=False,
                rationale="User explicitly disabled diagrams via --no-diagrams",
                confidence=1.0,
                rule_name="GraphDecisionRule",
                overrideable=False,  # Respect user intent
            )

        # 2. Simple role → skip graphs
        if context.total_tasks < MAX_TASKS_IN_FILES and context.task_file_count == 1:
            return Decision(
                option_name="generate_graph",
                value=False,
                rationale=(
                    f"Simple role ({context.total_tasks} tasks in single file) "
                    "doesn't benefit from diagrams"
                ),
                confidence=0.9,
                rule_name="GraphDecisionRule",
            )

        # 3. Complex role → highly recommend graphs
        if (
            context.complexity_category in {"complex", "enterprise"}
            or context.task_file_count > MAX_TASK_FILES_LOWER_BOUND
        ):
            return Decision(
                option_name="generate_graph",
                value=True,
                rationale=(
                    f"Complex role ({context.complexity_category}, "
                    f"{context.task_file_count} task files) benefits from visualization"
                ),
                confidence=0.8,
                rule_name="GraphDecisionRule",
            )

        # 4. Medium role → recommend graphs with moderate confidence
        # Medium roles have multiple task files or moderate task count
        if context.task_file_count >= 2 or context.total_tasks >= MAX_TASKS_IN_FILES:
            return Decision(
                option_name="generate_graph",
                value=True,
                rationale=(
                    f"Medium role ({context.total_tasks} tasks, "
                    f"{context.task_file_count} files) benefits from visualization"
                ),
                confidence=0.6,  # Lower confidence than complex roles
                rule_name="GraphDecisionRule",
            )

        # 5. Default: very simple role, no graphs
        return Decision(
            option_name="generate_graph",
            value=False,
            rationale=(f"Very simple role ({context.total_tasks} tasks) doesn't require diagrams"),
            confidence=0.7,
            rule_name="GraphDecisionRule",
        )
