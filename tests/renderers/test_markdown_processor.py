"""Tests for MarkdownProcessor blank-line normalization behavior.

Excessive consecutive blank lines are always collapsed to the validator's
maximum, even without --auto-fix, so generated output complies with
docsible's own markdown validation by default.
"""

from docsible.renderers.processors.markdown_processor import MarkdownProcessor


def test_collapses_excessive_blank_lines_without_auto_fix():
    processor = MarkdownProcessor(validate=False, auto_fix=False)
    markdown = "# Title\n\n\n\n\nBody\n"
    assert processor.process(markdown) == "# Title\n\n\nBody\n"


def test_keeps_allowed_blank_lines():
    processor = MarkdownProcessor(validate=False, auto_fix=False)
    markdown = "# Title\n\n\nBody\n"
    assert processor.process(markdown) == markdown


def test_auto_fix_still_applies_other_fixes():
    processor = MarkdownProcessor(validate=False, auto_fix=True)
    markdown = "Line with trailing   \n\tTabbed line\n\n\n\n\nEnd\n"
    result = processor.process(markdown)
    assert "Line with trailing\n" in result
    assert "\t" not in result
    assert "\n\n\n\n" not in result


def test_strict_validation_raises_on_errors():
    processor = MarkdownProcessor(
        validate=True, auto_fix=False, strict_validation=True
    )
    markdown = "# Title\n\n```yaml\nunclosed\n"
    try:
        processor.process(markdown)
    except ValueError as exc:
        assert "Markdown validation failed" in str(exc)
    else:
        raise AssertionError("expected ValueError from strict validation")
