"""
Custom Jinja2 filters for Docsible templates.

Provides filters for safely rendering content in markdown tables and other contexts.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


def normalize_license(value: Any) -> str:
    """Remove redundant ``license (...)`` wrapping from Galaxy metadata."""
    text = str(value or "").strip()
    if text.lower().startswith("license (") and text.endswith(")"):
        return text[9:-1].strip()
    return text


def escape_table_cell(
    value: Any, max_length: int | None = None, truncate_indicator: str = "..."
) -> str:
    """
    Escape a value for safe rendering in a markdown table cell.

    Handles the following special characters and cases:
    - Pipe characters (|) - breaks table columns
    - Newlines (\n, \r\n) - breaks table rows
    - Backticks (`) - breaks inline code blocks
    - Backslashes (\\) - escape sequences
    - Very long values - makes tables unreadable

    Args:
        value: The value to escape (can be any type)
        max_length: Optional maximum length for truncation (default: no truncation)
        truncate_indicator: String to append when truncating (default: "...")

    Returns:
        Escaped string safe for markdown table cells

    Example:
        >>> escape_table_cell("Install | Configure | Monitor")
        'Install ¦ Configure ¦ Monitor'
        >>> escape_table_cell("Multi\nline\ntext")
        'Multi<br>line<br>text'
        >>> escape_table_cell("Code with `backtick`")
        'Code with \\`backtick\\`'
        >>> escape_table_cell("Very long text" * 20, max_length=50)
        'Very long textVery long textVery long textVery ...'
    """
    if value is None:
        return ""

    # Convert to string
    s = str(value)

    # If empty, return early
    if not s:
        return ""

    # Replace pipe with similar unicode character (broken bar)
    # This preserves readability while preventing column breaks
    s = s.replace("|", "¦")

    # Replace newlines with HTML line breaks
    # This keeps multi-line content in a single table cell
    s = s.replace("\r\n", "<br>")
    s = s.replace("\n", "<br>")
    s = s.replace("\r", "<br>")

    # Escape backticks to prevent code block issues
    # Must be done carefully to avoid double-escaping
    s = s.replace("`", "\\`")

    # Note: We intentionally don't escape backslashes themselves
    # because that would break intentional escape sequences in the content
    # If this causes issues, we can add: s = s.replace('\\', '\\\\')

    # Truncate if max_length is specified
    if max_length and len(s) > max_length:
        s = s[:max_length] + truncate_indicator

    return s.strip()


def escape_table_value(value: Any, as_code: bool = True, max_length: int | None = None) -> str:
    """
    Escape a value for safe rendering in a markdown table cell, optionally with code formatting.

    This is a specialized version of escape_table_cell that handles code-formatted values
    (wrapped in backticks) more carefully.

    Args:
        value: The value to escape
        as_code: If True, wrap in backticks for inline code (default: True)
        max_length: Optional maximum length for truncation

    Returns:
        Escaped and optionally code-formatted string

    Example:
        >>> escape_table_value("my_variable")
        '`my_variable`'
        >>> escape_table_value("Multi\nline", as_code=False)
        'Multi<br>line'
        >>> escape_table_value("Very | long | value", max_length=15)
        '`Very ¦ long ¦ ...`'
    """
    if value is None:
        return ""

    # First escape the cell content
    escaped = escape_table_cell(value, max_length=max_length)

    # If empty after escaping, return early
    if not escaped:
        return ""

    # Wrap in backticks if requested (for code formatting)
    if as_code and escaped:
        # For code blocks, we need to be extra careful with backticks
        # We already escaped them above, so we're safe to wrap
        return f"`{escaped}`"

    return escaped


def safe_join(items: Any, separator: str = ", ", max_items: int | None = None) -> str:
    """
    Safely join items into a string, escaping each item for table cells.

    Args:
        items: Iterable of items to join (or single item)
        separator: Separator string (default: ", ")
        max_items: Optional limit on number of items to show

    Returns:
        Escaped and joined string

    Example:
        >>> safe_join(["tag1|special", "tag2\nline", "tag3"])
        'tag1¦special, tag2<br>line, tag3'
        >>> safe_join(["a", "b", "c", "d", "e"], max_items=3)
        'a, b, c (+2 more)'
    """
    if items is None:
        return ""

    # Handle non-iterable items
    if isinstance(items, str):
        return escape_table_cell(items)

    # Convert to list
    try:
        items_list = list(items)
    except TypeError:
        return escape_table_cell(str(items))

    # If empty, return early
    if not items_list:
        return ""

    # Limit items if max_items is specified
    if max_items and len(items_list) > max_items:
        shown_items = items_list[:max_items]
        remaining = len(items_list) - max_items
        escaped_items = [escape_table_cell(item) for item in shown_items]
        return separator.join(escaped_items) + f" (+{remaining} more)"

    # Escape and join all items
    escaped_items = [escape_table_cell(item) for item in items_list]
    return separator.join(escaped_items)


# Export all filters for easy registration
TEMPLATE_FILTERS = {
    "escape_table_cell": escape_table_cell,
    "escape_table_value": escape_table_value,
    "safe_join": safe_join,
    "normalize_license": normalize_license,
}
