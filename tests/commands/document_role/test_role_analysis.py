"""Tests for the shared role analysis/render pipeline.

`analyze_role()` and `render_analyzed_role()` are the single implementation
used by single-role `document role`, `document role --collection`, and
`scan collection`. These tests guard the parity property directly: a role
analyzed/rendered through this module must produce the same
complexity/execution-graph/recommendation content regardless of which
command called it.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from docsible.commands.document_role.role_analysis import (
    RoleAnalysis,
    analyze_role,
    render_analyzed_role,
)
from docsible.commands.role_info_loader import RoleInfoLoader


def _write_role(root: Path, *, task_count: int) -> Path:
    """Write a minimal role with `task_count` named, no-op tasks."""
    (root / "tasks").mkdir(parents=True)
    (root / "handlers").mkdir(parents=True)
    (root / "defaults").mkdir(parents=True)

    tasks = "\n".join(
        f"- name: Task {i}\n  debug:\n    msg: 'step {i}'" for i in range(task_count)
    )
    (root / "tasks" / "main.yml").write_text(f"---\n{tasks}\n")
    (root / "handlers" / "main.yml").write_text(
        "---\n- name: restart service\n  debug:\n    msg: restart\n"
    )
    (root / "defaults" / "main.yml").write_text("---\nsome_var: 1\n")
    return root


@pytest.fixture
def small_role(tmp_path) -> Path:
    return _write_role(tmp_path / "small_role", task_count=3)


@pytest.fixture
def large_role(tmp_path) -> Path:
    # 26+ tasks crosses the SIMPLE/MEDIUM -> COMPLEX threshold.
    return _write_role(tmp_path / "large_role", task_count=30)


class TestAnalyzeRole:
    def test_returns_complexity_report_and_recommendations(self, small_role):
        role_info = RoleInfoLoader().load(small_role)

        analysis = analyze_role(role_info, small_role)

        assert isinstance(analysis, RoleAnalysis)
        assert analysis.complexity_report is not None
        assert analysis.complexity_report.metrics.total_tasks == 3
        assert isinstance(analysis.recommendations, list)

    def test_reuses_cached_complexity_report_without_recomputing(self, small_role):
        role_info = RoleInfoLoader().load(small_role)
        cached = analyze_role(role_info, small_role).complexity_report

        analysis = analyze_role(role_info, small_role, cached_complexity_report=cached)

        # Same object identity: the cache path must not run analysis again.
        assert analysis.complexity_report is cached

    def test_large_role_is_classified_complex(self, large_role):
        role_info = RoleInfoLoader().load(large_role)

        analysis = analyze_role(role_info, large_role)

        assert analysis.complexity_report.category.value in ("complex", "enterprise")


class TestRenderAnalyzedRole:
    def test_complex_role_readme_has_architecture_and_execution_routes(self, large_role):
        """Regression test for the collection-parity gap: a role analyzed and
        rendered through this shared pipeline must show the same Architecture
        Overview / Execution Graph Summary / Execution Routes sections that
        standalone `document role` produces for a COMPLEX role.
        """
        role_info = RoleInfoLoader().load(large_role)
        analysis = analyze_role(role_info, large_role)
        output_path = large_role / "README.md"

        render_analyzed_role(
            role_info=role_info,
            role_path=large_role,
            analysis=analysis,
            output_path=output_path,
        )

        readme = output_path.read_text()
        assert "## Architecture Overview" in readme
        assert "### Execution Graph Summary" in readme
        assert "### Execution Routes" in readme
        assert "Statically reachable task files" in readme

    def test_small_role_renders_without_error(self, small_role):
        role_info = RoleInfoLoader().load(small_role)
        analysis = analyze_role(role_info, small_role)
        output_path = small_role / "README.md"

        render_analyzed_role(
            role_info=role_info,
            role_path=small_role,
            analysis=analysis,
            output_path=output_path,
        )

        assert output_path.exists()

    def test_no_excessive_blank_lines(self, large_role):
        role_info = RoleInfoLoader().load(large_role)
        analysis = analyze_role(role_info, large_role)
        output_path = large_role / "README.md"

        render_analyzed_role(
            role_info=role_info,
            role_path=large_role,
            analysis=analysis,
            output_path=output_path,
        )

        blank_run = max_blank_run = 0
        for line in output_path.read_text().splitlines():
            if line.strip() == "":
                blank_run += 1
                max_blank_run = max(max_blank_run, blank_run)
            else:
                blank_run = 0
        assert max_blank_run <= 2
