import pytest

from docsible.formatters.text.message import MessageTransformer
from docsible.models.enhancement import Difficulty, Enhancement
from docsible.models.recommendation import Recommendation
from docsible.models.severity import Severity

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def make_rec(
    message: str,
    severity: Severity = Severity.INFO,
    remediation: str | None = None,
    category: str = "documentation",
    rationale: str = "Improves role quality",
    confidence: float = 0.8,
) -> Recommendation:
    """Factory for Recommendation instances with sensible defaults."""
    return Recommendation(
        category=category,
        message=message,
        rationale=rationale,
        severity=severity,
        remediation=remediation,
        confidence=confidence,
    )


@pytest.fixture
def transformer() -> MessageTransformer:
    return MessageTransformer()


@pytest.fixture
def examples_rec() -> Recommendation:
    return make_rec("Role has no examples directory")


@pytest.fixture
def meta_missing_rec() -> Recommendation:
    return make_rec("Missing meta/main.yml")


@pytest.fixture
def no_meta_rec() -> Recommendation:
    return make_rec("No meta/main.yml")


@pytest.fixture
def task_desc_rec() -> Recommendation:
    return make_rec("No task descriptions")


@pytest.fixture
def vars_undocumented_rec() -> Recommendation:
    return make_rec("Variables not documented")


@pytest.fixture
def readme_rec() -> Recommendation:
    return make_rec("Consider adding a README")


@pytest.fixture
def unknown_rec() -> Recommendation:
    return make_rec("Something completely unknown and unmatched")


# ---------------------------------------------------------------------------
# TestMessageTransformerPatterns
# ---------------------------------------------------------------------------

class TestMessageTransformerPatterns:
    """Test that known patterns are transformed to the correct Enhancement."""

    def test_no_examples_directory_pattern(self, transformer, examples_rec):
        enh = transformer.transform(examples_rec)
        assert isinstance(enh, Enhancement)
        full_text = enh.action + " " + enh.value
        assert "examples" in full_text.lower()

    def test_no_examples_difficulty_is_quick(self, transformer, examples_rec):
        enh = transformer.transform(examples_rec)
        assert enh.difficulty == Difficulty.QUICK

    def test_no_examples_time_estimate(self, transformer, examples_rec):
        enh = transformer.transform(examples_rec)
        assert enh.time_estimate == "5 min"

    def test_missing_meta_pattern(self, transformer, meta_missing_rec):
        enh = transformer.transform(meta_missing_rec)
        full_text = enh.action + " " + enh.value
        assert "meta" in full_text.lower() or "galaxy" in full_text.lower()

    def test_no_meta_pattern_also_matches(self, transformer, no_meta_rec):
        enh = transformer.transform(no_meta_rec)
        full_text = enh.action + " " + enh.value
        assert "meta" in full_text.lower() or "galaxy" in full_text.lower()

    def test_missing_meta_difficulty_is_quick(self, transformer, meta_missing_rec):
        enh = transformer.transform(meta_missing_rec)
        assert enh.difficulty == Difficulty.QUICK

    def test_missing_meta_time_estimate(self, transformer, meta_missing_rec):
        enh = transformer.transform(meta_missing_rec)
        assert enh.time_estimate == "10 min"

    def test_task_descriptions_pattern(self, transformer, task_desc_rec):
        enh = transformer.transform(task_desc_rec)
        full_text = enh.action + " " + enh.value
        assert "task" in full_text.lower() or "comment" in full_text.lower()

    def test_task_descriptions_difficulty_is_medium(self, transformer, task_desc_rec):
        enh = transformer.transform(task_desc_rec)
        assert enh.difficulty == Difficulty.MEDIUM

    def test_task_descriptions_time_estimate(self, transformer, task_desc_rec):
        enh = transformer.transform(task_desc_rec)
        assert enh.time_estimate == "15 min"

    def test_variables_undocumented_pattern(self, transformer, vars_undocumented_rec):
        enh = transformer.transform(vars_undocumented_rec)
        full_text = enh.action + " " + enh.value
        assert "variable" in full_text.lower() or "document" in full_text.lower()

    def test_variables_undocumented_difficulty_is_medium(self, transformer, vars_undocumented_rec):
        enh = transformer.transform(vars_undocumented_rec)
        assert enh.difficulty == Difficulty.MEDIUM

    def test_variables_undocumented_time_estimate(self, transformer, vars_undocumented_rec):
        enh = transformer.transform(vars_undocumented_rec)
        assert enh.time_estimate == "20 min"

    def test_consider_adding_readme_pattern(self, transformer, readme_rec):
        enh = transformer.transform(readme_rec)
        full_text = enh.action + " " + enh.value
        assert "readme" in full_text.lower() or "documentation" in full_text.lower()

    def test_consider_adding_readme_difficulty_is_quick(self, transformer, readme_rec):
        enh = transformer.transform(readme_rec)
        assert enh.difficulty == Difficulty.QUICK

    def test_consider_adding_readme_time_estimate(self, transformer, readme_rec):
        enh = transformer.transform(readme_rec)
        assert enh.time_estimate == "Generated automatically!"

    def test_fallback_transformation_returns_enhancement(self, transformer, unknown_rec):
        enh = transformer.transform(unknown_rec)
        assert isinstance(enh, Enhancement)

    def test_fallback_transformation_value_mentions_quality(self, transformer, unknown_rec):
        enh = transformer.transform(unknown_rec)
        assert "quality" in enh.value.lower()

    def test_fallback_transformation_difficulty_is_medium(self, transformer, unknown_rec):
        enh = transformer.transform(unknown_rec)
        assert enh.difficulty == Difficulty.MEDIUM

    def test_fallback_transformation_time_estimate_is_varies(self, transformer, unknown_rec):
        enh = transformer.transform(unknown_rec)
        assert enh.time_estimate == "varies"

    def test_pattern_matching_case_insensitive_lower(self, transformer):
        rec = make_rec("role has no examples directory")
        enh = transformer.transform(rec)
        assert enh.difficulty == Difficulty.QUICK

    def test_pattern_matching_case_insensitive_upper(self, transformer):
        rec = make_rec("MISSING META/MAIN.YML")
        enh = transformer.transform(rec)
        assert enh.difficulty == Difficulty.QUICK


# ---------------------------------------------------------------------------
# TestMakePositive
# ---------------------------------------------------------------------------

class TestMakePositive:
    """Test the _make_positive helper."""

    def test_removes_leading_no(self):
        transformer = MessageTransformer()
        result = transformer._make_positive("No examples directory")
        assert not result.startswith("No ")

    def test_removes_leading_missing(self):
        transformer = MessageTransformer()
        result = transformer._make_positive("Missing examples directory")
        assert not result.startswith("Missing ")

    def test_removes_leading_lacks(self):
        transformer = MessageTransformer()
        result = transformer._make_positive("Lacks examples directory")
        assert not result.startswith("Lacks ")

    def test_prepends_add_when_no_action_prefix(self):
        transformer = MessageTransformer()
        result = transformer._make_positive("examples directory")
        assert result.startswith("Add ")

    def test_does_not_double_add_when_already_starts_with_add(self):
        transformer = MessageTransformer()
        result = transformer._make_positive("Add something important")
        assert result.count("Add") == 1
        assert result.startswith("Add")

    def test_does_not_prepend_add_when_starts_with_create(self):
        transformer = MessageTransformer()
        result = transformer._make_positive("Create a file")
        assert result.startswith("Create")
        assert not result.startswith("Add Create")

    def test_does_not_prepend_add_when_starts_with_include(self):
        transformer = MessageTransformer()
        result = transformer._make_positive("Include something")
        assert result.startswith("Include")

    def test_does_not_prepend_add_when_starts_with_consider(self):
        transformer = MessageTransformer()
        result = transformer._make_positive("Consider something")
        assert result.startswith("Consider")

    def test_removes_has_no_phrase(self):
        transformer = MessageTransformer()
        result = transformer._make_positive("role has no examples directory")
        assert "has no" not in result


# ---------------------------------------------------------------------------
# TestExtractCommand
# ---------------------------------------------------------------------------

class TestExtractCommand:
    """Test command extraction from remediation text."""

    def test_extracts_command_with_run_prefix(self):
        transformer = MessageTransformer()
        rec = make_rec(
            "Missing meta/main.yml",
            remediation="Run: mkdir -p meta && touch meta/main.yml",
        )
        command = transformer._extract_command(rec)
        assert command == "mkdir -p meta && touch meta/main.yml"

    def test_extracts_command_with_execute_prefix(self):
        transformer = MessageTransformer()
        rec = make_rec(
            "Some issue",
            remediation="Execute: ansible-lint .",
        )
        command = transformer._extract_command(rec)
        assert command == "ansible-lint ."

    def test_extracts_command_with_try_prefix(self):
        transformer = MessageTransformer()
        rec = make_rec(
            "Some issue",
            remediation="Try: molecule test",
        )
        command = transformer._extract_command(rec)
        assert command == "molecule test"

    def test_returns_none_when_no_remediation(self):
        transformer = MessageTransformer()
        rec = make_rec("Some issue", remediation=None)
        command = transformer._extract_command(rec)
        assert command is None

    def test_returns_none_when_remediation_has_no_run_pattern(self):
        transformer = MessageTransformer()
        rec = make_rec(
            "Some issue",
            remediation="Add comments above tasks explaining their purpose",
        )
        command = transformer._extract_command(rec)
        assert command is None

    def test_command_is_embedded_in_enhancement_when_remediation_has_run(self):
        transformer = MessageTransformer()
        rec = make_rec(
            "Role has no examples directory",
            remediation="Run: mkdir -p examples",
        )
        enh = transformer.transform(rec)
        assert enh.command == "mkdir -p examples"

    def test_command_is_none_in_enhancement_when_no_run_pattern(self):
        transformer = MessageTransformer()
        rec = make_rec(
            "Role has no examples directory",
            remediation="Create the examples directory manually",
        )
        enh = transformer.transform(rec)
        assert enh.command is None


# ---------------------------------------------------------------------------
# TestCalculatePriority
# ---------------------------------------------------------------------------

class TestCalculatePriority:
    """Test priority calculation based on severity."""

    def test_critical_severity_gives_priority_one(self):
        transformer = MessageTransformer()
        rec = make_rec("Some critical issue", severity=Severity.CRITICAL)
        assert transformer._calculate_priority(rec) == 1

    def test_warning_severity_gives_priority_two(self):
        transformer = MessageTransformer()
        rec = make_rec("Some warning", severity=Severity.WARNING)
        assert transformer._calculate_priority(rec) == 2

    def test_info_severity_gives_priority_three(self):
        transformer = MessageTransformer()
        rec = make_rec("Some info", severity=Severity.INFO)
        assert transformer._calculate_priority(rec) == 3

    def test_priority_embedded_in_enhancement_critical(self):
        transformer = MessageTransformer()
        rec = make_rec("Role has no examples directory", severity=Severity.CRITICAL)
        enh = transformer.transform(rec)
        assert enh.priority == 1

    def test_priority_embedded_in_enhancement_warning(self):
        transformer = MessageTransformer()
        rec = make_rec("Role has no examples directory", severity=Severity.WARNING)
        enh = transformer.transform(rec)
        assert enh.priority == 2

    def test_priority_embedded_in_enhancement_info(self):
        transformer = MessageTransformer()
        rec = make_rec("Role has no examples directory", severity=Severity.INFO)
        enh = transformer.transform(rec)
        assert enh.priority == 3

    def test_fallback_priority_is_two(self):
        transformer = MessageTransformer()
        # Fallback path always returns priority=2 regardless of severity
        rec = make_rec("Something completely unknown and unmatched", severity=Severity.INFO)
        enh = transformer.transform(rec)
        assert enh.priority == 2


# ---------------------------------------------------------------------------
# TestTransformReturnType
# ---------------------------------------------------------------------------

class TestTransformReturnType:
    """Ensure transform() always returns a valid Enhancement."""

    def test_returns_enhancement_for_all_known_patterns(self):
        transformer = MessageTransformer()
        messages = [
            "Role has no examples directory",
            "Missing meta/main.yml",
            "No meta/main.yml",
            "No task descriptions",
            "task description",
            "Variables not documented",
            "Variable documented",
            "Consider adding a README",
            "Consider adding README",
        ]
        for msg in messages:
            rec = make_rec(msg)
            enh = transformer.transform(rec)
            assert isinstance(enh, Enhancement), f"Expected Enhancement for message: {msg!r}"

    def test_transform_always_produces_non_empty_action(self):
        transformer = MessageTransformer()
        for msg in ["Role has no examples directory", "totally unknown message xyz"]:
            rec = make_rec(msg)
            enh = transformer.transform(rec)
            assert enh.action.strip() != ""
