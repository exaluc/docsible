"""End-to-end tests for machine-readable JSON output cleanliness.

When ``--output-format json`` is used, stdout must carry only valid JSON.
Logging is routed to stderr so the output can be piped or parsed directly.
"""

import json

from click.testing import CliRunner

from docsible.cli import cli


def _make_role(tmp_path):
    role = tmp_path / "test_role"
    (role / "tasks").mkdir(parents=True)
    (role / "tasks" / "main.yml").write_text(
        "---\n- name: Say hello\n  debug:\n    msg: hello\n"
    )
    return role


def test_analyze_role_json_stdout_is_pure_json(tmp_path):
    role = _make_role(tmp_path)
    runner = CliRunner()
    result = runner.invoke(
        cli, ["analyze", "role", "--role", str(role), "--output-format", "json"]
    )
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["role"] == "test_role"
    assert "findings" in payload
    assert "summary" in payload
    assert "truncated" in payload


def test_analyze_role_json_stdout_clean_even_with_verbose(tmp_path):
    """Verbose forces DEBUG logging; stdout must still parse as pure JSON."""
    role = _make_role(tmp_path)
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "--verbose",
            "analyze",
            "role",
            "--role",
            str(role),
            "--output-format",
            "json",
        ],
    )
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["role"] == "test_role"


def test_validate_role_json_stdout_is_pure_json(tmp_path):
    role = _make_role(tmp_path)
    runner = CliRunner()
    result = runner.invoke(
        cli, ["validate", "role", "--role", str(role), "--output-format", "json"]
    )
    assert result.exit_code == 0
    json.loads(result.stdout)
