
from docsible.analyzers.complexity_analyzer.models import (
    ComplexityCategory,
    ComplexityMetrics,
    ComplexityReport,
)
from docsible.formatters.text.positive import PositiveFormatter
from docsible.models.enhancement import Difficulty, Enhancement
from docsible.models.recommendation import Recommendation
from docsible.models.severity import Severity

# ---------------------------------------------------------------------------
# Helpers / shared fixtures
# ---------------------------------------------------------------------------

def make_simple_report() -> ComplexityReport:
    return ComplexityReport(
        metrics=ComplexityMetrics(
            total_tasks=3,
            task_files=1,
            handlers=0,
            conditional_tasks=0,
            max_tasks_per_file=3,
            avg_tasks_per_file=3.0,
        ),
        category=ComplexityCategory.SIMPLE,
    )


def make_medium_report() -> ComplexityReport:
    return ComplexityReport(
        metrics=ComplexityMetrics(
            total_tasks=15,
            task_files=3,
            handlers=2,
            conditional_tasks=4,
            role_dependencies=1,
            max_tasks_per_file=6,
            avg_tasks_per_file=5.0,
        ),
        category=ComplexityCategory.MEDIUM,
    )


def make_complex_report() -> ComplexityReport:
    return ComplexityReport(
        metrics=ComplexityMetrics(
            total_tasks=47,
            task_files=4,
            handlers=3,
            conditional_tasks=16,
            role_dependencies=2,
            task_includes=2,
            max_tasks_per_file=15,
            avg_tasks_per_file=11.75,
        ),
        category=ComplexityCategory.COMPLEX,
    )


def make_rec(
    message: str = "Role has no examples directory",
    severity: Severity = Severity.INFO,
    remediation: str | None = None,
) -> Recommendation:
    return Recommendation(
        category="best_practices",
        message=message,
        rationale="Improves role quality",
        severity=severity,
        remediation=remediation,
        confidence=0.8,
    )


# ---------------------------------------------------------------------------
# TestSuccessHeader
# ---------------------------------------------------------------------------

class TestSuccessHeader:
    def test_contains_success_checkmark(self, tmp_path):
        output_file = tmp_path / "README.md"
        output_file.write_text("# Test\n")
        formatter = PositiveFormatter()
        header = formatter._format_success_header(output_file)
        assert "✅ Documentation Generated Successfully!" in header[0]

    def test_contains_file_path(self, tmp_path):
        output_file = tmp_path / "README.md"
        output_file.write_text("# Test\n")
        formatter = PositiveFormatter()
        header = formatter._format_success_header(output_file)
        combined = "\n".join(header)
        assert str(output_file) in combined

    def test_contains_generated_in_timing(self, tmp_path):
        output_file = tmp_path / "README.md"
        output_file.write_text("# Test\n")
        formatter = PositiveFormatter()
        header = formatter._format_success_header(output_file)
        combined = "\n".join(header)
        assert "Generated in" in combined

    def test_contains_size_label(self, tmp_path):
        output_file = tmp_path / "README.md"
        output_file.write_text("# Test\n")
        formatter = PositiveFormatter()
        header = formatter._format_success_header(output_file)
        combined = "\n".join(header)
        assert "Size:" in combined

    def test_returns_list_of_strings(self, tmp_path):
        output_file = tmp_path / "README.md"
        output_file.write_text("# Test\n")
        formatter = PositiveFormatter()
        header = formatter._format_success_header(output_file)
        assert isinstance(header, list)
        assert all(isinstance(line, str) for line in header)


# ---------------------------------------------------------------------------
# TestDescribeComplexity
# ---------------------------------------------------------------------------

class TestDescribeComplexity:
    def test_simple_description_contains_easy_to_maintain(self):
        formatter = PositiveFormatter()
        desc = formatter._describe_complexity(make_simple_report())
        assert "easy to maintain" in desc.lower()

    def test_simple_description_contains_task_count(self):
        formatter = PositiveFormatter()
        desc = formatter._describe_complexity(make_simple_report())
        assert "3" in desc

    def test_medium_description_contains_task_count(self):
        formatter = PositiveFormatter()
        desc = formatter._describe_complexity(make_medium_report())
        assert "15" in desc

    def test_medium_description_mentions_functionality_balance(self):
        formatter = PositiveFormatter()
        desc = formatter._describe_complexity(make_medium_report())
        assert "balance" in desc.lower() or "well-structured" in desc.lower()

    def test_complex_description_contains_task_count(self):
        formatter = PositiveFormatter()
        desc = formatter._describe_complexity(make_complex_report())
        assert "47" in desc

    def test_complex_description_mentions_comprehensive_or_complex(self):
        formatter = PositiveFormatter()
        desc = formatter._describe_complexity(make_complex_report())
        assert "comprehensive" in desc.lower() or "complex" in desc.lower()

    def test_returns_string(self):
        formatter = PositiveFormatter()
        for report in [make_simple_report(), make_medium_report(), make_complex_report()]:
            assert isinstance(formatter._describe_complexity(report), str)


# ---------------------------------------------------------------------------
# TestDescribeReadiness
# ---------------------------------------------------------------------------

class TestDescribeReadiness:
    def test_simple_readiness_mentions_immediate(self):
        formatter = PositiveFormatter()
        desc = formatter._describe_readiness(make_simple_report())
        assert "immediate" in desc.lower() or "ready" in desc.lower()

    def test_medium_readiness_mentions_production(self):
        formatter = PositiveFormatter()
        desc = formatter._describe_readiness(make_medium_report())
        assert "production" in desc.lower() or "ready" in desc.lower()

    def test_complex_readiness_mentions_complex_deployments(self):
        formatter = PositiveFormatter()
        desc = formatter._describe_readiness(make_complex_report())
        assert "complex" in desc.lower() or "comprehensive" in desc.lower()

    def test_returns_string(self):
        formatter = PositiveFormatter()
        for report in [make_simple_report(), make_medium_report(), make_complex_report()]:
            assert isinstance(formatter._describe_readiness(report), str)


# ---------------------------------------------------------------------------
# TestDescribeStructure
# ---------------------------------------------------------------------------

class TestDescribeStructure:
    def test_no_handlers_no_meta_no_modules_returns_minimal(self):
        formatter = PositiveFormatter()
        desc = formatter._describe_structure(make_simple_report())
        assert "minimal" in desc.lower() or "easy to customize" in desc.lower()

    def test_handlers_only_mentions_handlers(self):
        formatter = PositiveFormatter()
        report = ComplexityReport(
            metrics=ComplexityMetrics(
                total_tasks=10,
                task_files=1,
                handlers=2,
                conditional_tasks=0,
                max_tasks_per_file=10,
                avg_tasks_per_file=10.0,
            ),
            category=ComplexityCategory.SIMPLE,
        )
        desc = formatter._describe_structure(report)
        assert "handler" in desc.lower()

    def test_handlers_and_meta_mentions_both(self):
        formatter = PositiveFormatter()
        report = ComplexityReport(
            metrics=ComplexityMetrics(
                total_tasks=15,
                task_files=2,
                handlers=1,
                conditional_tasks=0,
                role_dependencies=1,
                max_tasks_per_file=8,
                avg_tasks_per_file=7.5,
            ),
            category=ComplexityCategory.MEDIUM,
        )
        desc = formatter._describe_structure(report)
        assert "handler" in desc.lower() or "metadata" in desc.lower()

    def test_full_structure_returns_complete_description(self):
        formatter = PositiveFormatter()
        report = ComplexityReport(
            metrics=ComplexityMetrics(
                total_tasks=20,
                task_files=3,
                handlers=2,
                conditional_tasks=3,
                role_dependencies=1,
                task_includes=1,
                max_tasks_per_file=8,
                avg_tasks_per_file=6.67,
            ),
            category=ComplexityCategory.MEDIUM,
        )
        desc = formatter._describe_structure(report)
        assert "complete" in desc.lower() or "handler" in desc.lower()


# ---------------------------------------------------------------------------
# TestFindHighlights
# ---------------------------------------------------------------------------

class TestFindHighlights:
    def test_simple_role_has_no_nested_includes_highlight(self):
        formatter = PositiveFormatter()
        highlights = formatter._find_highlights(make_simple_report())
        assert any(
            "nested" in h.lower() or "straightforward" in h.lower()
            for h in highlights
        )

    def test_role_with_conditionals_gets_conditional_highlight(self):
        formatter = PositiveFormatter()
        highlights = formatter._find_highlights(make_medium_report())
        assert any("conditional" in h.lower() for h in highlights)

    def test_role_with_multiple_task_files_gets_task_file_highlight(self):
        formatter = PositiveFormatter()
        highlights = formatter._find_highlights(make_medium_report())
        assert any("task files" in h.lower() for h in highlights)

    def test_role_with_dependencies_gets_dependency_highlight(self):
        formatter = PositiveFormatter()
        highlights = formatter._find_highlights(make_medium_report())
        assert any("dependenc" in h.lower() for h in highlights)

    def test_role_with_task_includes_does_not_get_no_nested_includes(self):
        formatter = PositiveFormatter()
        highlights = formatter._find_highlights(make_complex_report())
        no_nested = any(
            "no nested" in h.lower() or "straightforward" in h.lower()
            for h in highlights
        )
        assert not no_nested

    def test_role_with_one_task_file_does_not_get_task_file_highlight(self):
        formatter = PositiveFormatter()
        highlights = formatter._find_highlights(make_simple_report())
        task_file_highlight = any("task files" in h.lower() for h in highlights)
        assert not task_file_highlight

    def test_returns_list(self):
        formatter = PositiveFormatter()
        highlights = formatter._find_highlights(make_simple_report())
        assert isinstance(highlights, list)

    def test_conditional_percentage_mentioned_in_highlight(self):
        formatter = PositiveFormatter()
        # medium report: 4/15 = 26%
        highlights = formatter._find_highlights(make_medium_report())
        cond_highlights = [h for h in highlights if "conditional" in h.lower()]
        assert len(cond_highlights) >= 1
        # Should mention a percentage
        assert any("%" in h for h in cond_highlights)

    def test_no_highlights_for_zero_conditional_tasks(self):
        formatter = PositiveFormatter()
        report = make_simple_report()  # conditional_tasks=0
        highlights = formatter._find_highlights(report)
        cond_highlights = [h for h in highlights if "conditional" in h.lower()]
        assert len(cond_highlights) == 0

    def test_dependency_count_mentioned_in_highlight(self):
        formatter = PositiveFormatter()
        highlights = formatter._find_highlights(make_complex_report())
        dep_highlights = [h for h in highlights if "dependenc" in h.lower()]
        assert len(dep_highlights) >= 1
        assert any("2" in h for h in dep_highlights)


# ---------------------------------------------------------------------------
# TestFormatEnhancements
# ---------------------------------------------------------------------------

class TestFormatEnhancements:
    def test_returns_list_of_strings(self):
        formatter = PositiveFormatter()
        enh = Enhancement(
            action="Add examples/",
            value="to help users",
            difficulty=Difficulty.QUICK,
            time_estimate="5 min",
            priority=1,
        )
        lines = formatter._format_enhancements([enh])
        assert isinstance(lines, list)
        assert all(isinstance(l, str) for l in lines)

    def test_header_mentions_enhancement_opportunities(self):
        formatter = PositiveFormatter()
        enh = Enhancement(
            action="Add examples/",
            value="to help users",
            difficulty=Difficulty.QUICK,
            time_estimate="5 min",
            priority=1,
        )
        lines = formatter._format_enhancements([enh])
        assert "Enhancement Opportunities" in lines[0]

    def test_enhancement_action_appears_in_output(self):
        formatter = PositiveFormatter()
        enh = Enhancement(
            action="Add examples/",
            value="to help users",
            difficulty=Difficulty.QUICK,
            time_estimate="5 min",
            priority=1,
        )
        lines = formatter._format_enhancements([enh])
        combined = "\n".join(lines)
        assert "Add examples/" in combined

    def test_enhancements_sorted_by_priority_high_before_low(self):
        formatter = PositiveFormatter()
        high = Enhancement(
            action="High priority action",
            value="",
            difficulty=Difficulty.QUICK,
            time_estimate="5 min",
            priority=1,
        )
        low = Enhancement(
            action="Low priority action",
            value="",
            difficulty=Difficulty.ADVANCED,
            time_estimate="1 hour",
            priority=3,
        )
        lines = formatter._format_enhancements([low, high])
        combined = "\n".join(lines)
        high_idx = combined.index("High priority action")
        low_idx = combined.index("Low priority action")
        assert high_idx < low_idx

    def test_enhancements_sorted_priority_two_between_one_and_three(self):
        formatter = PositiveFormatter()
        high = Enhancement(action="P1", value="", difficulty=Difficulty.QUICK, time_estimate="1 min", priority=1)
        mid = Enhancement(action="P2", value="", difficulty=Difficulty.MEDIUM, time_estimate="10 min", priority=2)
        low = Enhancement(action="P3", value="", difficulty=Difficulty.ADVANCED, time_estimate="1 hour", priority=3)
        lines = formatter._format_enhancements([low, mid, high])
        combined = "\n".join(lines)
        p1_idx = combined.index("P1")
        p2_idx = combined.index("P2")
        p3_idx = combined.index("P3")
        assert p1_idx < p2_idx < p3_idx

    def test_multiple_enhancements_all_appear(self):
        formatter = PositiveFormatter()
        enhancements = [
            Enhancement(action=f"Action {i}", value="val", difficulty=Difficulty.QUICK, time_estimate="5 min", priority=1)
            for i in range(3)
        ]
        lines = formatter._format_enhancements(enhancements)
        combined = "\n".join(lines)
        for i in range(3):
            assert f"Action {i}" in combined


# ---------------------------------------------------------------------------
# TestFormatNextSteps
# ---------------------------------------------------------------------------

class TestFormatNextSteps:
    def test_header_contains_next_steps(self, tmp_path):
        output_file = tmp_path / "README.md"
        formatter = PositiveFormatter()
        lines = formatter._format_next_steps(output_file, make_simple_report())
        assert "Next Steps" in lines[0]

    def test_simple_role_mentions_file_name(self, tmp_path):
        output_file = tmp_path / "README.md"
        formatter = PositiveFormatter()
        lines = formatter._format_next_steps(output_file, make_simple_report())
        combined = "\n".join(lines)
        assert "README.md" in combined

    def test_simple_role_next_steps_include_playbook(self, tmp_path):
        output_file = tmp_path / "README.md"
        formatter = PositiveFormatter()
        lines = formatter._format_next_steps(output_file, make_simple_report())
        combined = "\n".join(lines)
        assert "ansible-playbook" in combined.lower() or "share" in combined.lower()

    def test_complex_role_next_steps_include_docsible_or_check(self, tmp_path):
        output_file = tmp_path / "README.md"
        formatter = PositiveFormatter()
        lines = formatter._format_next_steps(output_file, make_complex_report())
        combined = "\n".join(lines)
        assert "docsible" in combined.lower() or "ansible-playbook" in combined.lower()

    def test_returns_list_of_strings(self, tmp_path):
        output_file = tmp_path / "README.md"
        formatter = PositiveFormatter()
        lines = formatter._format_next_steps(output_file, make_simple_report())
        assert isinstance(lines, list)
        assert all(isinstance(l, str) for l in lines)

    def test_next_steps_returns_list_of_strings(self, tmp_path):
        output_file = tmp_path / "README.md"
        formatter = PositiveFormatter()
        lines = formatter._format_next_steps(output_file, make_medium_report())
        assert isinstance(lines, list)
        assert all(isinstance(line, str) for line in lines)


# ---------------------------------------------------------------------------
# TestFileSizeFormatting
# ---------------------------------------------------------------------------

class TestFileSizeFormatting:
    def test_missing_file_returns_unknown(self, tmp_path):
        f = tmp_path / "nonexistent.md"
        formatter = PositiveFormatter()
        assert formatter._format_file_size(f) == "unknown"

    def test_small_file_returns_bytes_or_kb(self, tmp_path):
        f = tmp_path / "small.md"
        f.write_bytes(b"x" * 512)
        formatter = PositiveFormatter()
        result = formatter._format_file_size(f)
        assert "B" in result or "KB" in result

    def test_file_over_1kb_returns_kb(self, tmp_path):
        f = tmp_path / "medium.md"
        f.write_bytes(b"x" * 2048)
        formatter = PositiveFormatter()
        result = formatter._format_file_size(f)
        assert "KB" in result

    def test_empty_file_returns_zero_bytes(self, tmp_path):
        f = tmp_path / "empty.md"
        f.write_bytes(b"")
        formatter = PositiveFormatter()
        result = formatter._format_file_size(f)
        assert "0.0 B" in result

    def test_result_is_string(self, tmp_path):
        f = tmp_path / "test.md"
        f.write_bytes(b"hello")
        formatter = PositiveFormatter()
        assert isinstance(formatter._format_file_size(f), str)


# ---------------------------------------------------------------------------
# TestFormatSuccess (integration-level)
# ---------------------------------------------------------------------------

class TestFormatSuccess:
    def test_result_is_string(self, tmp_path):
        output_file = tmp_path / "README.md"
        output_file.write_text("# Test\n")
        formatter = PositiveFormatter()
        result = formatter.format_success(
            output_file=output_file,
            complexity=make_simple_report(),
            recommendations=[],
        )
        assert isinstance(result, str)

    def test_contains_success_checkmark(self, tmp_path):
        output_file = tmp_path / "README.md"
        output_file.write_text("# Test\n")
        formatter = PositiveFormatter()
        result = formatter.format_success(
            output_file=output_file,
            complexity=make_simple_report(),
            recommendations=[],
        )
        assert "✅ Documentation Generated Successfully!" in result

    def test_contains_role_analysis_section(self, tmp_path):
        output_file = tmp_path / "README.md"
        output_file.write_text("# Test\n")
        formatter = PositiveFormatter()
        result = formatter.format_success(
            output_file=output_file,
            complexity=make_simple_report(),
            recommendations=[],
        )
        assert "📊 Role Analysis:" in result

    def test_contains_next_steps_section(self, tmp_path):
        output_file = tmp_path / "README.md"
        output_file.write_text("# Test\n")
        formatter = PositiveFormatter()
        result = formatter.format_success(
            output_file=output_file,
            complexity=make_simple_report(),
            recommendations=[],
        )
        assert "🎯 Next Steps:" in result

    def test_no_recommendations_shows_praise(self, tmp_path):
        output_file = tmp_path / "README.md"
        output_file.write_text("# Test\n")
        formatter = PositiveFormatter()
        result = formatter.format_success(
            output_file=output_file,
            complexity=make_simple_report(),
            recommendations=[],
        )
        assert "Excellent" in result or "best practices" in result

    def test_with_recommendations_shows_enhancement_opportunities(self, tmp_path):
        output_file = tmp_path / "README.md"
        output_file.write_text("# Test\n")
        formatter = PositiveFormatter()
        result = formatter.format_success(
            output_file=output_file,
            complexity=make_simple_report(),
            recommendations=[make_rec("Role has no examples directory")],
        )
        assert "Enhancement Opportunities" in result

    def test_no_recommendations_does_not_show_enhancement_section(self, tmp_path):
        output_file = tmp_path / "README.md"
        output_file.write_text("# Test\n")
        formatter = PositiveFormatter()
        result = formatter.format_success(
            output_file=output_file,
            complexity=make_simple_report(),
            recommendations=[],
        )
        assert "Enhancement Opportunities" not in result

    def test_multiple_recommendations_all_appear(self, tmp_path):
        output_file = tmp_path / "README.md"
        output_file.write_text("# Test\n")
        formatter = PositiveFormatter()
        recs = [
            make_rec("Role has no examples directory"),
            make_rec("Missing meta/main.yml"),
        ]
        result = formatter.format_success(
            output_file=output_file,
            complexity=make_simple_report(),
            recommendations=recs,
        )
        assert "Enhancement Opportunities" in result
        # Both transformations should produce some output in the enhancement section
        assert result.count("•") >= 2

    def test_format_success_with_medium_complexity(self, tmp_path):
        output_file = tmp_path / "README.md"
        output_file.write_text("# Test\n" * 50)
        formatter = PositiveFormatter()
        result = formatter.format_success(
            output_file=output_file,
            complexity=make_medium_report(),
            recommendations=[],
        )
        assert "15" in result  # task count
        assert "✅ Documentation Generated Successfully!" in result

    def test_format_success_with_complex_role(self, tmp_path):
        output_file = tmp_path / "README.md"
        output_file.write_text("# Test\n" * 200)
        formatter = PositiveFormatter()
        result = formatter.format_success(
            output_file=output_file,
            complexity=make_complex_report(),
            recommendations=[],
        )
        assert "47" in result

    def test_format_success_contains_file_output_path(self, tmp_path):
        output_file = tmp_path / "ROLE_README.md"
        output_file.write_text("# Test\n")
        formatter = PositiveFormatter()
        result = formatter.format_success(
            output_file=output_file,
            complexity=make_simple_report(),
            recommendations=[],
        )
        assert "ROLE_README.md" in result

    def test_format_success_with_critical_recommendation(self, tmp_path):
        output_file = tmp_path / "README.md"
        output_file.write_text("# Test\n")
        formatter = PositiveFormatter()
        rec = make_rec("Role has no examples directory", severity=Severity.CRITICAL)
        result = formatter.format_success(
            output_file=output_file,
            complexity=make_simple_report(),
            recommendations=[rec],
        )
        assert "Enhancement Opportunities" in result

    def test_format_success_section_ordering(self, tmp_path):
        """Header must come before analysis, which must come before next steps."""
        output_file = tmp_path / "README.md"
        output_file.write_text("# Test\n")
        formatter = PositiveFormatter()
        result = formatter.format_success(
            output_file=output_file,
            complexity=make_medium_report(),
            recommendations=[],
        )
        header_pos = result.index("✅ Documentation Generated Successfully!")
        analysis_pos = result.index("📊 Role Analysis:")
        next_steps_pos = result.index("🎯 Next Steps:")
        assert header_pos < analysis_pos < next_steps_pos
