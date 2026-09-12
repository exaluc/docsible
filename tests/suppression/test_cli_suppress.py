"""Tests for suppress CLI commands using click.testing.CliRunner."""

from datetime import datetime, timedelta, timezone
from pathlib import Path

import yaml
from click.testing import CliRunner, Result

from docsible.commands.suppress import suppress_group
from docsible.models.suppression import SuppressionRule, SuppressionStore
from docsible.suppression.store import save_store

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_rule(**kwargs) -> SuppressionRule:
    defaults = {
        "id": "abc12345",
        "pattern": "no examples",
        "reason": "Examples in separate repo",
    }
    defaults.update(kwargs)
    return SuppressionRule(**defaults)  # type: ignore[arg-type]


def invoke(args: list[str]) -> Result:
    """Run a suppress_group command with the given args."""
    runner = CliRunner()
    return runner.invoke(suppress_group, args, catch_exceptions=False)


def suppress_path_for(tmp_path: Path) -> Path:
    return tmp_path / ".docsible" / "suppress.yml"


def save_rules_to(tmp_path: Path, rules: list[SuppressionRule]) -> Path:
    path = suppress_path_for(tmp_path)
    store = SuppressionStore(rules=rules)
    save_store(store, path)
    return path


def load_yaml_rules(tmp_path: Path) -> list[dict]:
    path = suppress_path_for(tmp_path)
    if not path.exists():
        return []
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data.get("rules", [])  # type: ignore[no-any-return]


# ---------------------------------------------------------------------------
# suppress add
# ---------------------------------------------------------------------------

class TestSuppressAdd:
    def test_add_creates_rule_in_suppress_yml(self, tmp_path):
        result = invoke(["add", "no examples", "--reason", "Legacy role",
                         "--path", str(tmp_path)])
        assert result.exit_code == 0, result.output
        rules = load_yaml_rules(tmp_path)
        assert len(rules) == 1
        assert rules[0]["pattern"] == "no examples"
        assert rules[0]["reason"] == "Legacy role"

    def test_add_with_expires_sets_expiry(self, tmp_path):
        result = invoke(["add", "no examples", "--reason", "Temp",
                         "--expires", "30", "--path", str(tmp_path)])
        assert result.exit_code == 0, result.output
        rules = load_yaml_rules(tmp_path)
        assert rules[0]["expires_at"] is not None

    def test_add_with_file_sets_file_pattern(self, tmp_path):
        result = invoke(["add", "no examples", "--reason", "Scoped",
                         "--file", "roles/*", "--path", str(tmp_path)])
        assert result.exit_code == 0, result.output
        rules = load_yaml_rules(tmp_path)
        assert rules[0]["file_pattern"] == "roles/*"

    def test_add_with_regex_sets_use_regex(self, tmp_path):
        result = invoke(["add", r"no\s+example", "--reason", "Regex rule",
                         "--regex", "--path", str(tmp_path)])
        assert result.exit_code == 0, result.output
        rules = load_yaml_rules(tmp_path)
        assert rules[0]["use_regex"] is True

    def test_add_with_zero_expires_raises_error(self, tmp_path):
        runner = CliRunner()
        result = runner.invoke(suppress_group,
                               ["add", "no examples", "--reason", "Bad",
                                "--expires", "0", "--path", str(tmp_path)],
                               catch_exceptions=False)
        assert result.exit_code != 0

    def test_add_with_negative_expires_raises_error(self, tmp_path):
        runner = CliRunner()
        result = runner.invoke(suppress_group,
                               ["add", "no examples", "--reason", "Bad",
                                "--expires", "-5", "--path", str(tmp_path)],
                               catch_exceptions=False)
        assert result.exit_code != 0

    def test_add_output_shows_rule_id_and_details(self, tmp_path):
        result = invoke(["add", "no examples", "--reason", "Legacy",
                         "--path", str(tmp_path)])
        assert result.exit_code == 0
        assert "Pattern" in result.output
        assert "no examples" in result.output
        assert "Reason" in result.output
        assert "Legacy" in result.output

    def test_add_appends_to_existing_rules(self, tmp_path):
        existing = make_rule(id="existing1", pattern="old pattern")
        save_rules_to(tmp_path, [existing])
        result = invoke(["add", "new pattern", "--reason", "New reason",
                         "--path", str(tmp_path)])
        assert result.exit_code == 0
        rules = load_yaml_rules(tmp_path)
        assert len(rules) == 2
        patterns = {r["pattern"] for r in rules}
        assert "old pattern" in patterns
        assert "new pattern" in patterns


# ---------------------------------------------------------------------------
# suppress list
# ---------------------------------------------------------------------------

class TestSuppressList:
    def test_list_no_rules_shows_empty_message(self, tmp_path):
        result = invoke(["list", "--path", str(tmp_path)])
        assert result.exit_code == 0
        assert "No suppression rules found." in result.output

    def test_list_with_rules_shows_table(self, tmp_path):
        rule = make_rule(id="abc12345", pattern="no examples", reason="Legacy")
        save_rules_to(tmp_path, [rule])
        result = invoke(["list", "--path", str(tmp_path)])
        assert result.exit_code == 0
        assert "abc12345" in result.output
        assert "no examples" in result.output

    def test_list_shows_active_count(self, tmp_path):
        rule = make_rule()
        save_rules_to(tmp_path, [rule])
        result = invoke(["list", "--path", str(tmp_path)])
        assert result.exit_code == 0
        assert "1 active" in result.output

    def test_list_hide_expired_by_default(self, tmp_path):
        past = datetime.now(timezone.utc) - timedelta(days=1)
        expired = make_rule(id="expred01", pattern="expired pattern", expires_at=past)
        save_rules_to(tmp_path, [expired])
        result = invoke(["list", "--path", str(tmp_path)])
        assert result.exit_code == 0
        # With no active rules, shows "No suppression rules found."
        assert "No suppression rules found." in result.output

    def test_list_show_expired_includes_expired_rules(self, tmp_path):
        past = datetime.now(timezone.utc) - timedelta(days=1)
        expired = make_rule(id="expred01", pattern="expired pattern", expires_at=past)
        save_rules_to(tmp_path, [expired])
        result = invoke(["list", "--show-expired", "--path", str(tmp_path)])
        assert result.exit_code == 0
        assert "expred01" in result.output
        assert "expired pattern" in result.output

    def test_list_hints_about_expired_when_some_hidden(self, tmp_path):
        past = datetime.now(timezone.utc) - timedelta(days=1)
        expired = make_rule(id="expred01", pattern="expired pattern", expires_at=past)
        save_rules_to(tmp_path, [expired])
        result = invoke(["list", "--path", str(tmp_path)])
        assert result.exit_code == 0
        # Should hint that there are hidden expired rules
        assert "expired" in result.output.lower()


# ---------------------------------------------------------------------------
# suppress remove
# ---------------------------------------------------------------------------

class TestSuppressRemove:
    def test_remove_existing_rule_shows_confirmation(self, tmp_path):
        rule = make_rule(id="abc12345")
        save_rules_to(tmp_path, [rule])
        result = invoke(["remove", "abc12345", "--path", str(tmp_path)])
        assert result.exit_code == 0
        assert "abc12345" in result.output

    def test_remove_existing_rule_actually_removes_it(self, tmp_path):
        rule = make_rule(id="abc12345")
        save_rules_to(tmp_path, [rule])
        invoke(["remove", "abc12345", "--path", str(tmp_path)])
        rules = load_yaml_rules(tmp_path)
        assert all(r["id"] != "abc12345" for r in rules)

    def test_remove_nonexistent_rule_exits_with_error(self, tmp_path):
        save_rules_to(tmp_path, [])
        runner = CliRunner()
        result = runner.invoke(suppress_group,
                               ["remove", "doesntex", "--path", str(tmp_path)],
                               catch_exceptions=False)
        assert result.exit_code != 0

    def test_remove_leaves_other_rules_intact(self, tmp_path):
        rule1 = make_rule(id="rule0001", pattern="pattern one")
        rule2 = make_rule(id="rule0002", pattern="pattern two")
        save_rules_to(tmp_path, [rule1, rule2])
        invoke(["remove", "rule0001", "--path", str(tmp_path)])
        rules = load_yaml_rules(tmp_path)
        assert len(rules) == 1
        assert rules[0]["id"] == "rule0002"


# ---------------------------------------------------------------------------
# suppress clean
# ---------------------------------------------------------------------------

class TestSuppressClean:
    def test_clean_no_expired_shows_no_rules_message(self, tmp_path):
        future = datetime.now(timezone.utc) + timedelta(days=30)
        rule = make_rule(expires_at=future)
        save_rules_to(tmp_path, [rule])
        result = invoke(["clean", "--path", str(tmp_path)])
        assert result.exit_code == 0
        assert "No expired rules to clean." in result.output

    def test_clean_no_rules_at_all_shows_no_rules_message(self, tmp_path):
        result = invoke(["clean", "--path", str(tmp_path)])
        assert result.exit_code == 0
        assert "No expired rules to clean." in result.output

    def test_clean_removes_expired_rules(self, tmp_path):
        past = datetime.now(timezone.utc) - timedelta(days=1)
        future = datetime.now(timezone.utc) + timedelta(days=30)
        expired = make_rule(id="expred01", expires_at=past)
        active = make_rule(id="active01", expires_at=future)
        save_rules_to(tmp_path, [expired, active])

        result = invoke(["clean", "--path", str(tmp_path)])
        assert result.exit_code == 0
        assert "1" in result.output

        rules = load_yaml_rules(tmp_path)
        ids = {r["id"] for r in rules}
        assert "expred01" not in ids
        assert "active01" in ids

    def test_clean_shows_removed_count(self, tmp_path):
        past = datetime.now(timezone.utc) - timedelta(days=1)
        expired1 = make_rule(id="expred01", pattern="pattern one", expires_at=past)
        expired2 = make_rule(id="expred02", pattern="pattern two", expires_at=past)
        save_rules_to(tmp_path, [expired1, expired2])
        result = invoke(["clean", "--path", str(tmp_path)])
        assert result.exit_code == 0
        assert "2" in result.output

    def test_clean_dry_run_shows_what_would_be_removed(self, tmp_path):
        past = datetime.now(timezone.utc) - timedelta(days=1)
        expired = make_rule(id="expred01", pattern="my pattern", expires_at=past)
        save_rules_to(tmp_path, [expired])

        result = invoke(["clean", "--dry-run", "--path", str(tmp_path)])
        assert result.exit_code == 0
        assert "expred01" in result.output
        assert "my pattern" in result.output

    def test_clean_dry_run_does_not_remove_rules(self, tmp_path):
        past = datetime.now(timezone.utc) - timedelta(days=1)
        expired = make_rule(id="expred01", expires_at=past)
        save_rules_to(tmp_path, [expired])

        invoke(["clean", "--dry-run", "--path", str(tmp_path)])

        rules = load_yaml_rules(tmp_path)
        ids = {r["id"] for r in rules}
        assert "expred01" in ids


# ---------------------------------------------------------------------------
# suppress group help
# ---------------------------------------------------------------------------

class TestSuppressGroupHelp:
    def test_help_shows_all_subcommands(self):
        runner = CliRunner()
        result = runner.invoke(suppress_group, ["--help"])
        assert result.exit_code == 0
        for cmd in ("add", "list", "remove", "clean"):
            assert cmd in result.output

    def test_add_help(self):
        runner = CliRunner()
        result = runner.invoke(suppress_group, ["add", "--help"])
        assert result.exit_code == 0
        assert "PATTERN" in result.output

    def test_list_help(self):
        runner = CliRunner()
        result = runner.invoke(suppress_group, ["list", "--help"])
        assert result.exit_code == 0

    def test_remove_help(self):
        runner = CliRunner()
        result = runner.invoke(suppress_group, ["remove", "--help"])
        assert result.exit_code == 0

    def test_clean_help(self):
        runner = CliRunner()
        result = runner.invoke(suppress_group, ["clean", "--help"])
        assert result.exit_code == 0
