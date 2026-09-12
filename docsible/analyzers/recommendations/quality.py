from pathlib import Path

from docsible.analyzers.complexity_analyzer import analyze_role_complexity_cached
from docsible.analyzers.complexity_analyzer.models import ComplexityCategory
from docsible.models.recommendation import Recommendation
from docsible.models.severity import Severity


class QualityRecommendationGenerator:
    """Generate quality/maintainability recommendations."""

    def analyze_role(self, role_path: Path) -> list[Recommendation]:
        """Analyze role for quality issues."""
        recommendations = []

        # Get complexity analysis
        complexity = analyze_role_complexity_cached(role_path, no_docsible=True)

        # Check documentation vs complexity
        # Only recommend task descriptions for complex roles
        if complexity.category == ComplexityCategory.COMPLEX:
            if complexity.metrics.total_tasks > 20:
                # Point to the main task file if it exists
                main_tasks = role_path / "tasks" / "main.yml"
                task_file = "tasks/main.yml" if main_tasks.exists() else None

                recommendations.append(
                    Recommendation(
                        category="documentation",
                        message=f"Complex role ({complexity.metrics.total_tasks} tasks) lacks task descriptions",
                        rationale="Large roles need documentation for maintainability",
                        severity=Severity.WARNING,
                        file_path=task_file,  # Point to actual task file
                        line_number=None,  # No specific line - applies to all tasks
                        remediation="Add # comments above tasks explaining their purpose",
                        confidence=0.9,
                        auto_fixable=False,
                    )
                )

        # Check for undocumented variables
        vars_without_docs = self._find_undocumented_vars(role_path)
        if vars_without_docs:
            recommendations.append(
                Recommendation(
                    category="documentation",
                    message=f"{len(vars_without_docs)} variables used but not documented",
                    rationale="Undocumented variables make roles hard to use",
                    severity=Severity.WARNING,
                    file_path="defaults/main.yml",  # Specific file
                    line_number=None,  # Multiple variables, no single line
                    remediation="Add comments describing each variable's purpose",
                    confidence=0.85,
                    auto_fixable=False,
                )
            )

        return recommendations

    def _find_undocumented_vars(self, role_path: Path) -> list[str]:
        """Find variables that are defined but not documented.

        Returns:
            List of variable names without documentation comments
        """
        undocumented: list[str] = []

        # Check defaults/main.yml
        defaults_file = role_path / "defaults" / "main.yml"
        if not defaults_file.exists():
            return undocumented

        try:
            import yaml

            content = defaults_file.read_text()
            lines = content.splitlines()

            # Parse YAML to get variable names
            with open(defaults_file) as f:
                data = yaml.safe_load(f) or {}

            if not isinstance(data, dict):
                return undocumented

            # For each variable, check if it has a documentation comment
            for var_name in data.keys():
                # Find the line where this variable is defined
                var_line_idx = None
                for idx, line in enumerate(lines):
                    # Match "var_name:" at start of line
                    if line.strip().startswith(f"{var_name}:"):
                        var_line_idx = idx
                        break

                if var_line_idx is not None:
                    # Check if there's a comment on the same line or line before
                    has_comment = False

                    # Check same line
                    if "#" in lines[var_line_idx]:
                        has_comment = True

                    # Check line before
                    if var_line_idx > 0:
                        prev_line = lines[var_line_idx - 1].strip()
                        if prev_line.startswith("#"):
                            has_comment = True

                    if not has_comment:
                        undocumented.append(var_name)

        except Exception:
            # If we can't parse, return empty list
            pass

        return undocumented
