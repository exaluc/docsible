"""
YAML file loading functions with metadata extraction.

This module has been refactored from a single 280-line function into focused
helper functions for better maintainability and testability.
"""

import logging
import os
from pathlib import Path
from typing import Any, cast

import yaml

from docsible.utils.cache import cache_by_file_mtime

from .parser import get_multiline_indicator

logger = logging.getLogger(__name__)


@cache_by_file_mtime
def load_yaml_generic(filepath: str | Path) -> dict[str, Any] | None:
    """Load YAML file and return parsed data.

    Args:
        filepath: Path to YAML file

    Returns:
        Parsed YAML data as dictionary, or None if error occurs

    Example:
        >>> data = load_yaml_generic('defaults/main.yml')
        >>> if data:
        ...     print(data.get('my_var'))
    """
    try:
        with open(filepath, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return cast(dict[str, Any] | None, data)
    except (FileNotFoundError, yaml.YAMLError, OSError) as e:
        logger.error(f"Error loading {filepath}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error loading {filepath}: {e}")
        return None


@cache_by_file_mtime
def load_yaml_file_custom(file_path):
    """Load a YAML file and extract both its data and associated metadata from comments.

    This is now a clean coordinator that delegates to focused helper functions.

    Args:
        file_path (str): Path to the YAML file.

    Returns:
        dict or None: A dictionary mapping each key path to its value, metadata, and line number,
        or None if the file is empty or an error occurs.
    """
    try:
        # Read file lines and parse YAML
        lines, data = _read_and_parse_yaml(file_path)

        if not data:
            return None

        # Process YAML data with metadata extraction
        result: dict[str, dict[str, Any]] = {}
        parent_line_tracker = {"line": 0}

        for key, value in data.items():
            _process_yaml_value(key, value, lines, result, parent_line_tracker)

        return result

    except (FileNotFoundError, yaml.constructor.ConstructorError, yaml.YAMLError) as e:
        logger.error(f"Error loading {file_path}: {e}")
        return None


@cache_by_file_mtime
def load_yaml_files_from_dir_custom(dir_path):
    """Function to load all YAML files from a given directory and include file names"""
    collected_data = []

    def process_yaml_file(full_path, dir_path):
        if full_path.endswith((".yml", ".yaml")):
            file_data = load_yaml_file_custom(full_path)
            if file_data:
                relative_path = os.path.relpath(full_path, dir_path)
                return {"file": relative_path, "data": file_data}
        return None

    if os.path.exists(dir_path) and os.path.isdir(dir_path):
        # dir-path
        for file in os.listdir(dir_path):
            full_path = os.path.join(dir_path, file)
            if os.path.isfile(full_path):
                item = process_yaml_file(full_path, dir_path)
                if item:
                    collected_data.append(item)
        # main-dir
        main_dir = os.path.join(dir_path, "main")
        if os.path.exists(main_dir) and os.path.isdir(main_dir):
            for root, _, files in os.walk(main_dir):
                for yaml_file in files:
                    full_path = os.path.join(root, yaml_file)
                    item = process_yaml_file(full_path, dir_path)
                    if item:
                        collected_data.append(item)

    return collected_data


# ============================================================================
# Helper Functions - Each focused on one aspect of YAML processing
# ============================================================================


def _read_and_parse_yaml(file_path: str) -> tuple[list[str], dict[str, Any] | None]:
    """Read file lines and parse YAML content.

    Args:
        file_path: Path to YAML file

    Returns:
        Tuple of (file lines, parsed YAML data)
    """
    with open(file_path, encoding="utf-8") as file:
        lines = file.readlines()

    with open(file_path, encoding="utf-8") as file:
        data = yaml.safe_load(file)

    return lines, data


def _extract_metadata_from_comments(
    lines: list[str], line_idx: int | None
) -> dict[str, str | None]:
    """Extract metadata from comments preceding a given line.

    Supports: title, required, choices, description, type, description-lines

    Args:
        lines: File lines
        line_idx: Line index to extract metadata for

    Returns:
        Metadata dictionary
    """
    if line_idx is None:
        return {
            "title": None,
            "required": None,
            "choices": None,
            "description": None,
            "type": None,
        }

    # Collect preceding comment lines
    comments = []
    for comment_index in range(line_idx - 1, -1, -1):
        line = lines[comment_index].strip()
        if line.startswith("#"):
            comments.append(line[1:].strip())
        else:
            break
    comments.reverse()

    # Parse metadata from comments
    meta: dict[str, str | None] = {
        "title": None,
        "required": None,
        "choices": None,
        "description": None,
        "type": None,
    }

    for comment_idx, comment in enumerate(comments):
        lc = comment.lower()
        normalized_lc = lc.replace("_", "-")

        if normalized_lc.startswith("title:"):
            meta["title"] = comment.split(":", 1)[1].strip()
        elif normalized_lc.startswith("required:"):
            meta["required"] = comment.split(":", 1)[1].strip()
        elif normalized_lc.startswith("choices:"):
            meta["choices"] = comment.split(":", 1)[1].strip()
        elif normalized_lc.startswith("description:"):
            meta["description"] = comment.split(":", 1)[1].strip()
        elif normalized_lc.startswith("type:"):
            meta["type"] = comment.split(":", 1)[1].strip()
        elif (
            normalized_lc.startswith("description-lines:")
            or "description-lines:" in normalized_lc
            or "description_lines:" in lc
        ):
            # Extract multi-line description
            meta["description"] = _extract_multiline_description(
                lines, line_idx - len(comments) + comment_idx
            )

    return meta


def _extract_multiline_description(lines: list[str], start_idx: int) -> str:
    """Extract multi-line description from comment block.

    Args:
        lines: File lines
        start_idx: Index where description-lines tag appears

    Returns:
        Combined description string
    """
    description_lines = []
    start_collecting = False

    for subsequent_line in lines[start_idx:]:
        line_content = subsequent_line.strip()
        normalized_line = line_content.lower().replace("_", "-")

        # Start collecting after description-lines tag
        if line_content.startswith("#") and (
            "description-lines:" in normalized_line or "description_lines:" in line_content.lower()
        ):
            start_collecting = True
            continue

        # Stop at end marker
        if line_content.startswith("# end"):
            break

        if start_collecting:
            if line_content.startswith("#"):
                description_lines.append(f"{line_content[1:].strip()}<br>")
            else:
                break

    return "\n".join(description_lines) if description_lines else ""


def _find_key_line_number(
    key: str,
    value: Any,
    lines: list[str],
    parent_line: int,
    result: dict[str, dict[str, Any]],
) -> int | None:
    """Find the line number where a key appears in the YAML file.

    Handles dicts, lists, and scalar values.

    Args:
        key: Full key path (dot-separated)
        value: Value associated with the key
        lines: File lines
        parent_line: Starting line for search
        result: Accumulated result dict (for context)

    Returns:
        Line index or None
    """
    dictkey = key.split(".")[-1]
    vtype = type(value)

    for idx in range(parent_line, len(lines)):
        line_stripped = lines[idx].strip()

        # Skip comments
        if line_stripped.startswith("#"):
            continue

        # Handle dict values
        if isinstance(value, dict):
            dictvalue = None
            if dictkey.isnumeric():
                prev_path = ".".join(key.split(".")[:-1])
                if result.get(prev_path, {}).get("type") == "list":
                    dictkey = list(value.keys())[0]
                    dictvalue = str(list(value.values())[0])

            if dictvalue is None:
                # Regular dict
                if line_stripped.startswith(f"{dictkey}:") or line_stripped.startswith(
                    f"- {dictkey}:"
                ):
                    return idx
            else:
                # Inline dict
                if f"{dictkey}:" in line_stripped and dictvalue in line_stripped:
                    return idx

        # Handle list values
        elif isinstance(value, list):
            if line_stripped.startswith(f"{dictkey}:") or line_stripped.startswith(f"- {value}"):
                return idx

        # Handle scalar values
        else:
            # Key match
            if line_stripped.startswith(f"{dictkey}:") or f"{dictkey}:" in line_stripped:
                return idx
            # Bool in list
            if vtype is bool and f"- {str(value).lower()}" in line_stripped.lower():
                return idx
            # None/null in list
            if value is None and any(
                null_str in line_stripped.lower() for null_str in ["- none", "- null"]
            ):
                return idx
            # List item
            if f"- {str(value).lower()}" in line_stripped.lower():
                return idx
            # List item (numeric key)
            if dictkey.isnumeric():
                prev_path = ".".join(key.split(".")[:-1])
                if result.get(prev_path, {}).get("type") == "list":
                    if str(value).lower() in line_stripped.lower():
                        return idx

    return None


def _infer_value_type(value: Any, meta_type: str | None) -> str:
    """Infer the type of a YAML value.

    Args:
        value: The value to inspect
        meta_type: Type from metadata comment (if any)

    Returns:
        Type string
    """
    if meta_type:
        return meta_type
    elif isinstance(value, dict):
        return "dict"
    elif isinstance(value, list):
        return "list"
    else:
        return type(value).__name__


def _format_value_for_display(value: Any, multiline_indicator: str | None) -> Any:
    """Format a value for display in the result dict.

    Args:
        value: The raw value
        multiline_indicator: Multiline indicator if any

    Returns:
        Formatted value
    """
    if multiline_indicator:
        return f"<multiline value: {multiline_indicator}>"
    elif isinstance(value, list):
        return []
    elif isinstance(value, dict):
        return {}
    elif isinstance(value, str):
        return value.strip()
    else:
        return value


def _process_yaml_value(
    key: str,
    value: Any,
    lines: list[str],
    result: dict[str, dict[str, Any]],
    parent_line_tracker: dict[str, int],
) -> None:
    """Process a single YAML key-value pair and its children.

    Recursively processes nested dicts and lists.

    Args:
        key: Full key path
        value: Value associated with key
        lines: File lines
        result: Result dict to populate
        parent_line_tracker: Mutable dict tracking current line
    """
    # Find line number
    line_idx = _find_key_line_number(key, value, lines, parent_line_tracker["line"], result)

    current_line = line_idx if line_idx is not None else parent_line_tracker["line"]
    parent_line_tracker["line"] = current_line

    # Extract metadata
    meta = _extract_metadata_from_comments(lines, current_line)

    # Get multiline indicator
    indicator_name = get_multiline_indicator(lines[current_line])

    # Store result
    result[key] = {
        "value": _format_value_for_display(value, indicator_name),
        "multiline_indicator": indicator_name,
        "title": meta["title"],
        "required": meta["required"],
        "choices": meta["choices"],
        "description": meta["description"],
        "line": current_line + 1,
        "type": _infer_value_type(value, meta["type"]),
    }

    # Recursively process nested structures
    if isinstance(value, dict):
        for k, v in value.items():
            full_key = f"{key}.{k}"
            _process_yaml_value(full_key, v, lines, result, parent_line_tracker)
    elif isinstance(value, list):
        for idx, item in enumerate(value):
            full_key = f"{key}.{idx}"
            _process_yaml_value(full_key, item, lines, result, parent_line_tracker)
