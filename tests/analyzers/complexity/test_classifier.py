"""Tests for complexity classification."""

from docsible.analyzers.complexity_analyzer import (
    ComplexityCategory,
    ComplexityMetrics,
    classify_complexity,
)

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def make_metrics(
    total_tasks,
    role_dependencies=0,
    role_includes=0,
    task_includes=0,
    conditional_tasks=0,
    external_integrations=0,
    task_files=1,
    handlers=0,
    max_tasks_per_file=None,
    avg_tasks_per_file=None,
):
    """Build a ComplexityMetrics instance with sensible defaults for unit tests."""
    if max_tasks_per_file is None:
        max_tasks_per_file = total_tasks
    if avg_tasks_per_file is None:
        avg_tasks_per_file = float(total_tasks)
    return ComplexityMetrics(
        total_tasks=total_tasks,
        task_files=task_files,
        handlers=handlers,
        conditional_tasks=conditional_tasks,
        max_tasks_per_file=max_tasks_per_file,
        avg_tasks_per_file=avg_tasks_per_file,
        role_dependencies=role_dependencies,
        role_includes=role_includes,
        task_includes=task_includes,
        external_integrations=external_integrations,
    )


def test_classify_simple_role():
    """Test classification of simple role (1-10 tasks)."""
    metrics = ComplexityMetrics(
        total_tasks=8,
        task_files=1,
        handlers=0,
        conditional_tasks=2,
        max_tasks_per_file=8,
        avg_tasks_per_file=8.0,
    )
    assert classify_complexity(metrics) == ComplexityCategory.SIMPLE


def test_classify_medium_role():
    """Test classification of medium role (11-25 tasks)."""
    metrics = ComplexityMetrics(
        total_tasks=18,
        task_files=2,
        handlers=1,
        conditional_tasks=5,
        max_tasks_per_file=12,
        avg_tasks_per_file=9.0,
    )
    assert classify_complexity(metrics) == ComplexityCategory.MEDIUM


def test_classify_complex_role():
    """Test classification of complex role (25+ tasks)."""
    metrics = ComplexityMetrics(
        total_tasks=30,
        task_files=4,
        handlers=3,
        conditional_tasks=15,
        max_tasks_per_file=15,
        avg_tasks_per_file=7.5,
    )
    assert classify_complexity(metrics) == ComplexityCategory.COMPLEX


def test_classify_boundary_conditions():
    """Test boundary conditions for complexity classification."""
    # Exactly 10 tasks = SIMPLE
    metrics_10 = ComplexityMetrics(
        total_tasks=10,
        task_files=1,
        handlers=0,
        conditional_tasks=0,
        max_tasks_per_file=10,
        avg_tasks_per_file=10.0,
    )
    assert classify_complexity(metrics_10) == ComplexityCategory.SIMPLE

    # Exactly 11 tasks = MEDIUM
    metrics_11 = ComplexityMetrics(
        total_tasks=11,
        task_files=1,
        handlers=0,
        conditional_tasks=0,
        max_tasks_per_file=11,
        avg_tasks_per_file=11.0,
    )
    assert classify_complexity(metrics_11) == ComplexityCategory.MEDIUM

    # Exactly 25 tasks = MEDIUM
    metrics_25 = ComplexityMetrics(
        total_tasks=25,
        task_files=2,
        handlers=0,
        conditional_tasks=0,
        max_tasks_per_file=15,
        avg_tasks_per_file=12.5,
    )
    assert classify_complexity(metrics_25) == ComplexityCategory.MEDIUM

    # Exactly 26 tasks = COMPLEX
    metrics_26 = ComplexityMetrics(
        total_tasks=26,
        task_files=2,
        handlers=0,
        conditional_tasks=0,
        max_tasks_per_file=16,
        avg_tasks_per_file=13.0,
    )
    assert classify_complexity(metrics_26) == ComplexityCategory.COMPLEX


def test_classify_enterprise_role():
    """Test classification of enterprise role (50+ tasks with high integrations)."""
    metrics = ComplexityMetrics(
        total_tasks=60,
        task_files=5,
        handlers=5,
        conditional_tasks=20,
        max_tasks_per_file=15,
        avg_tasks_per_file=12.0,
        external_integrations=5,  # > 3
    )
    # total=60 > 50 and integrations=5 > 3 → ENTERPRISE
    assert classify_complexity(metrics) == ComplexityCategory.ENTERPRISE


def test_classify_enterprise_via_high_composition():
    """Test enterprise via high composition score with large task count."""
    metrics = ComplexityMetrics(
        total_tasks=55,
        task_files=4,
        handlers=3,
        conditional_tasks=10,
        max_tasks_per_file=20,
        avg_tasks_per_file=13.75,
        role_dependencies=3,
        role_includes=2,
        task_includes=0,
        external_integrations=1,  # only 1, not > 3
    )
    # composition_score = 3*2 + 2 + 0 = 8 (not > 10), integrations=1 (not > 3) → COMPLEX not ENTERPRISE
    assert classify_complexity(metrics) == ComplexityCategory.COMPLEX


def test_classify_large_role_without_secondary_complexity():
    """Test that large role without secondary factors is COMPLEX, not ENTERPRISE."""
    metrics = ComplexityMetrics(
        total_tasks=60,
        task_files=3,
        handlers=0,
        conditional_tasks=10,
        max_tasks_per_file=20,
        avg_tasks_per_file=20.0,
        role_dependencies=0,
        role_includes=0,
        task_includes=0,
        external_integrations=2,  # only 2, not > 3
    )
    # total=60 > 50 but integrations=2 ≤ 3 and composition=0 ≤ 10 → COMPLEX
    assert classify_complexity(metrics) == ComplexityCategory.COMPLEX


def test_classify_small_role_promoted_to_medium_by_composition():
    """Test that small role with high composition is promoted to MEDIUM."""
    metrics = ComplexityMetrics(
        total_tasks=5,
        task_files=1,
        handlers=0,
        conditional_tasks=2,
        max_tasks_per_file=5,
        avg_tasks_per_file=5.0,
        role_dependencies=3,  # composition_score = 3*2 + 0 + 0 = 6 > 4
        role_includes=0,
        task_includes=0,
        external_integrations=0,
    )
    # conditional_pct = 40%, composition = 6 > 4 → MEDIUM
    assert classify_complexity(metrics) == ComplexityCategory.MEDIUM


def test_classify_medium_role_promoted_to_complex_by_conditionals():
    """Test that medium task count with heavy conditionals is promoted to COMPLEX."""
    metrics = ComplexityMetrics(
        total_tasks=15,
        task_files=2,
        handlers=0,
        conditional_tasks=12,
        max_tasks_per_file=10,
        avg_tasks_per_file=7.5,
        role_dependencies=0,
        role_includes=0,
        task_includes=0,
        external_integrations=0,
    )
    # conditional_pct = 80% > 60, total=15 > 10 → COMPLEX
    assert classify_complexity(metrics) == ComplexityCategory.COMPLEX


def test_classify_simple_no_promotion():
    """Test that a small role with no secondary factors stays SIMPLE."""
    metrics = ComplexityMetrics(
        total_tasks=8,
        task_files=1,
        handlers=0,
        conditional_tasks=0,
        max_tasks_per_file=8,
        avg_tasks_per_file=8.0,
        role_dependencies=0,
        role_includes=0,
        task_includes=0,
        external_integrations=0,
    )
    # total=8 ≤ 10, no secondary factors → SIMPLE
    assert classify_complexity(metrics) == ComplexityCategory.SIMPLE


def test_classify_medium_baseline():
    """Test medium classification with moderate task count and no secondary factors."""
    metrics = ComplexityMetrics(
        total_tasks=15,
        task_files=2,
        handlers=1,
        conditional_tasks=3,
        max_tasks_per_file=10,
        avg_tasks_per_file=7.5,
        role_dependencies=0,
        role_includes=0,
        task_includes=0,
        external_integrations=0,
    )
    # total=15 > 10, no secondary boost → MEDIUM
    assert classify_complexity(metrics) == ComplexityCategory.MEDIUM


def test_classify_complex_baseline():
    """Test complex baseline with 30 tasks and no extreme secondary factors."""
    metrics = ComplexityMetrics(
        total_tasks=30,
        task_files=4,
        handlers=2,
        conditional_tasks=8,
        max_tasks_per_file=10,
        avg_tasks_per_file=7.5,
        role_dependencies=0,
        role_includes=0,
        task_includes=0,
        external_integrations=0,
    )
    # total=30 > 25 → COMPLEX
    assert classify_complexity(metrics) == ComplexityCategory.COMPLEX


def test_classify_medium_promoted_by_integrations():
    """Test that medium task count with many integrations is promoted to COMPLEX."""
    metrics = ComplexityMetrics(
        total_tasks=12,
        task_files=2,
        handlers=0,
        conditional_tasks=3,
        max_tasks_per_file=8,
        avg_tasks_per_file=6.0,
        role_dependencies=0,
        role_includes=0,
        task_includes=0,
        external_integrations=4,  # > 3
    )
    # total=12 > 10, integrations=4 > 3 → COMPLEX
    assert classify_complexity(metrics) == ComplexityCategory.COMPLEX


def test_classify_small_role_promoted_to_medium_by_conditionals():
    """Test that small role with many conditionals is promoted to MEDIUM."""
    metrics = ComplexityMetrics(
        total_tasks=5,
        task_files=1,
        handlers=0,
        conditional_tasks=3,  # conditional_pct = 60%, not > 40%? Wait 3/5=60% > 40% → MEDIUM
        max_tasks_per_file=5,
        avg_tasks_per_file=5.0,
        role_dependencies=0,
        role_includes=0,
        task_includes=0,
        external_integrations=0,
    )
    # conditional_pct = 60% > 40 → MEDIUM
    assert classify_complexity(metrics) == ComplexityCategory.MEDIUM


# ---------------------------------------------------------------------------
# New multi-factor classifier tests (using make_metrics helper)
# ---------------------------------------------------------------------------

def test_simple_baseline():
    """8 tasks with no secondary factors should be SIMPLE."""
    metrics = make_metrics(total_tasks=8)
    assert classify_complexity(metrics) == ComplexityCategory.SIMPLE


def test_medium_baseline():
    """15 tasks with no secondary factors should be MEDIUM."""
    metrics = make_metrics(total_tasks=15)
    assert classify_complexity(metrics) == ComplexityCategory.MEDIUM


def test_complex_baseline():
    """30 tasks (> 25) should be COMPLEX regardless of secondary factors."""
    metrics = make_metrics(total_tasks=30)
    assert classify_complexity(metrics) == ComplexityCategory.COMPLEX


def test_enterprise_requires_both_size_and_complexity():
    """60 tasks with integrations=5 satisfies ENTERPRISE criteria."""
    metrics = make_metrics(total_tasks=60, external_integrations=5)
    assert classify_complexity(metrics) == ComplexityCategory.ENTERPRISE


def test_large_simple_role_stays_complex_not_enterprise():
    """60 tasks but integrations=2 and composition=0 should be COMPLEX, not ENTERPRISE."""
    metrics = make_metrics(total_tasks=60, external_integrations=2)
    # integrations=2 ≤ 3 and composition=0 ≤ 10 → does not qualify for ENTERPRISE
    assert classify_complexity(metrics) == ComplexityCategory.COMPLEX


def test_small_role_promoted_to_medium_by_composition():
    """5 tasks with role_dependencies=3 (composition=6 > 4) should be MEDIUM."""
    metrics = make_metrics(total_tasks=5, role_dependencies=3)
    # composition_score = 3*2 = 6 > 4 → MEDIUM
    assert classify_complexity(metrics) == ComplexityCategory.MEDIUM


def test_small_role_promoted_to_medium_by_conditionals():
    """5 tasks with 3 conditional (60% > 40%) should be MEDIUM."""
    metrics = make_metrics(total_tasks=5, conditional_tasks=3)
    # conditional_pct = 60% > 40 → MEDIUM
    assert classify_complexity(metrics) == ComplexityCategory.MEDIUM


def test_medium_role_promoted_to_complex_by_conditionals():
    """15 tasks with 10 conditional (66% > 60%) should be COMPLEX."""
    metrics = make_metrics(total_tasks=15, conditional_tasks=10)
    # conditional_pct ≈ 66.7% > 60 and total=15 > 10 → COMPLEX
    assert classify_complexity(metrics) == ComplexityCategory.COMPLEX


def test_medium_role_promoted_to_complex_by_composition():
    """15 tasks with role_includes=5, task_includes=4 (composition=9 > 8) should be COMPLEX."""
    metrics = make_metrics(total_tasks=15, role_includes=5, task_includes=4)
    # composition_score = 0 + 5 + 4 = 9 > 8 and total=15 > 10 → COMPLEX
    assert classify_complexity(metrics) == ComplexityCategory.COMPLEX


def test_zero_tasks_is_simple():
    """A role with 0 tasks should be SIMPLE (fallback)."""
    metrics = make_metrics(total_tasks=0)
    assert classify_complexity(metrics) == ComplexityCategory.SIMPLE
