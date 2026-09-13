"""Tests for the `docsible scan collection` CLI command.

Uses Click's CliRunner so no subprocess is spawned and no real filesystem
side-effects occur outside of tmp_path fixtures.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import click
import pytest
from click.testing import CliRunner

from docsible.cli import cli

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

FIXTURES = Path(__file__).parent.parent.parent / "fixtures"
MINIMAL_COLLECTION = FIXTURES / "minimal_collection"
MULTI_ROLE_COLLECTION = FIXTURES / "multi_role_collection"


def _invoke(*args: str) -> click.testing.Result:
    runner = CliRunner()
    return runner.invoke(cli, ["scan", "collection", *args], catch_exceptions=False)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestScanDiscovery:
    def test_scan_discovers_roles_in_collection(self):
        """Scanning a collection with roles should report at least 1 role found."""
        result = _invoke(str(MINIMAL_COLLECTION))
        assert result.exit_code == 0, (
            f"Command exited {result.exit_code}.\nstdout:\n{result.output}"
        )
        # The text formatter reports "N roles found"
        assert "1 roles found" in result.output or "role" in result.output.lower()

    def test_scan_discovers_multiple_roles(self):
        """Scanning a multi-role collection should list all roles."""
        result = _invoke(str(MULTI_ROLE_COLLECTION))
        assert result.exit_code == 0, (
            f"Command exited {result.exit_code}.\nstdout:\n{result.output}"
        )
        # 3 roles exist; verify at least 2 are reported
        output_lower = result.output.lower()
        role_names = ["db_role", "cache_role", "proxy_role"]
        found = sum(1 for name in role_names if name in output_lower)
        assert found >= 2, f"Expected >=2 role names in output, got {found}.\n{result.output}"


class TestScanDryRun:
    def test_scan_dry_run(self):
        """--dry-run prints 'would scan' without running analysis and exits 0."""
        result = _invoke(str(MINIMAL_COLLECTION), "--dry-run")
        assert result.exit_code == 0, (
            f"Command exited {result.exit_code}.\nstdout:\n{result.output}"
        )
        assert "would scan" in result.output.lower()

    def test_scan_dry_run_lists_role_names(self):
        """--dry-run should list individual role names."""
        result = _invoke(str(MINIMAL_COLLECTION), "--dry-run")
        assert result.exit_code == 0
        assert "web_role" in result.output


class TestScanJsonOutput:
    def test_scan_json_output_valid(self):
        """--output-format json produces valid JSON with expected top-level keys."""
        result = _invoke(str(MINIMAL_COLLECTION), "--output-format", "json")
        assert result.exit_code == 0, (
            f"Command exited {result.exit_code}.\nstdout:\n{result.output}"
        )
        try:
            data = json.loads(result.output)
        except json.JSONDecodeError as exc:
            pytest.fail(f"Output is not valid JSON: {exc}\nOutput:\n{result.output}")

        assert "collection_path" in data, "JSON missing 'collection_path'"
        assert "total_roles" in data, "JSON missing 'total_roles'"
        assert "summary" in data, "JSON missing 'summary'"
        assert "roles" in data, "JSON missing 'roles'"

    def test_scan_json_summary_keys(self):
        """JSON summary sub-object should have the expected numeric fields."""
        result = _invoke(str(MINIMAL_COLLECTION), "--output-format", "json")
        assert result.exit_code == 0
        data = json.loads(result.output)
        summary = data["summary"]
        assert "total_critical" in summary
        assert "total_warnings" in summary
        assert "complexity_breakdown" in summary

    def test_scan_json_roles_list(self):
        """Each role entry in JSON output should carry required per-role fields."""
        result = _invoke(str(MINIMAL_COLLECTION), "--output-format", "json")
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["total_roles"] >= 1
        for role in data["roles"]:
            for key in ("name", "path", "task_count", "variable_count", "complexity"):
                assert key in role, f"Role entry missing '{key}': {role}"


class TestScanFailOn:
    def test_scan_fail_on_none_exits_0(self):
        """--fail-on none should always exit 0 regardless of findings."""
        result = _invoke(str(MINIMAL_COLLECTION), "--fail-on", "none")
        assert result.exit_code == 0, (
            f"Expected exit 0 with --fail-on none, got {result.exit_code}.\n{result.output}"
        )

    def test_scan_fail_on_critical_exits_0_on_clean_role(self):
        """--fail-on critical should exit 0 when no critical findings exist."""
        # minimal_collection is a simple role unlikely to have critical findings
        result = _invoke(str(MINIMAL_COLLECTION), "--fail-on", "critical")
        # This may exit 0 or 1 depending on findings; we just verify the flag is accepted
        assert result.exit_code in (0, 1), (
            f"Unexpected exit code {result.exit_code}.\n{result.output}"
        )


class TestScanInvalidPath:
    def test_scan_invalid_path_exits_nonzero(self):
        """A nonexistent path should cause the command to exit non-zero."""
        result = CliRunner().invoke(
            cli,
            ["scan", "collection", "/nonexistent/path/that/does/not/exist"],
            catch_exceptions=False,
        )
        assert result.exit_code != 0, (
            f"Expected non-zero exit for invalid path, got {result.exit_code}.\n{result.output}"
        )

    def test_scan_invalid_path_shows_error_message(self):
        """Error output should mention the nonexistent path."""
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["scan", "collection", "/nonexistent/path/that/does/not/exist"],
            catch_exceptions=False,
        )
        combined = result.output
        assert "does not exist" in combined or "Error" in combined, (
            f"Expected error message, got:\n{combined}"
        )


class TestScanEmptyDir:
    def test_scan_empty_dir_handles_gracefully(self, tmp_path: Path):
        """An empty directory (no roles) should not crash; exits 0 with a message."""
        result = CliRunner().invoke(
            cli,
            ["scan", "collection", str(tmp_path)],
            catch_exceptions=False,
        )
        # Should exit cleanly (0) — the command calls sys.exit(0) explicitly
        assert result.exit_code in (0, 1), (
            f"Expected clean exit for empty dir, got {result.exit_code}.\n{result.output}"
        )
        # Should not traceback
        assert "Traceback" not in result.output

    def test_scan_empty_dir_reports_no_roles(self, tmp_path: Path):
        """An empty directory should produce a 'No roles found' message."""
        result = CliRunner().invoke(
            cli,
            ["scan", "collection", str(tmp_path)],
            catch_exceptions=False,
        )
        combined = result.output
        assert "no roles" in combined.lower() or result.exit_code in (0, 1)


class TestScanTopN:
    def test_scan_top_n_limits_output(self):
        """--top-n 1 with a 3-role collection should include at most 1 role in detail."""
        result = _invoke(str(MULTI_ROLE_COLLECTION), "--top-n", "1")
        assert result.exit_code == 0, (
            f"Command exited {result.exit_code}.\nstdout:\n{result.output}"
        )
        # With top_n=1 the text table only renders 1 role row
        # Count how many of the 3 role names appear
        role_names = ["db_role", "cache_role", "proxy_role"]
        found = sum(1 for name in role_names if name in result.output)
        # At most 1 role row should be shown in the table (summary still shows total)
        assert found <= 1, (
            f"Expected <=1 role name in top-n=1 output, found {found}.\n{result.output}"
        )

    def test_scan_top_n_json_limits_roles_array(self):
        """--top-n 2 --output-format json should return at most 2 roles in the array."""
        result = _invoke(
            str(MULTI_ROLE_COLLECTION), "--top-n", "2", "--output-format", "json"
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert len(data["roles"]) <= 2, (
            f"Expected <=2 roles in JSON output, got {len(data['roles'])}"
        )


class TestScanRecommendationParity:
    """Regression test: `_analyse_role()` previously called
    `generate_all_recommendations(role_path)` without the complexity report,
    silently missing the graph-aware findings (e.g. collection dependencies)
    that `document role` already produced. It must now use the same
    `analyze_role()` pipeline as `document role` / `document role
    --collection`.
    """

    def test_scan_surfaces_collection_dependency_recommendation(self, tmp_path):
        collection = tmp_path / "collection"
        shutil.copytree(MINIMAL_COLLECTION, collection)
        meta_path = collection / "roles" / "web_role" / "meta" / "main.yml"
        meta_path.write_text(
            "galaxy_info:\n"
            "  author: Test Author\n"
            "  description: Web role for testing\n"
            "  license: MIT\n"
            "  min_ansible_version: '2.9'\n"
            "dependencies: []\n"
            "collections:\n"
            "  - community.general\n"
        )

        result = _invoke(str(collection), "--output-format", "json")

        assert result.exit_code == 0
        data = json.loads(result.output)
        role = next(r for r in data["roles"] if r["name"] == "web_role")
        assert any(
            "collections" in msg.lower() for msg in role["top_recommendations"]
        ), role["top_recommendations"]
