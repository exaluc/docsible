"""Regression coverage for intent command behavior."""

from pathlib import Path
from unittest.mock import patch

import yaml
from click.testing import CliRunner

from docsible.cli import cli
from docsible.models.recommendation import Recommendation
from docsible.models.severity import Severity
from docsible.validation.models import ValidationIssue, ValidationSeverity, ValidationType


def _role(tmp_path: Path) -> Path:
    role = tmp_path / "role"
    (role / "meta").mkdir(parents=True)
    (role / "tasks").mkdir()
    (role / "meta" / "main.yml").write_text("---\ngalaxy_info: {}\n", encoding="utf-8")
    (role / "tasks" / "main.yml").write_text("---\n- name: Do work\n  debug:\n", encoding="utf-8")
    return role


def _recommendation() -> Recommendation:
    return Recommendation(
        category="test",
        message="A finding",
        rationale="Regression coverage",
        severity=Severity.WARNING,
        confidence=1.0,
    )


def test_analyze_outputs_json_and_does_not_write_role_files(tmp_path):
    role = _role(tmp_path)
    runner = CliRunner()

    with patch(
        "docsible.commands.document_role.orchestrators.role_orchestrator.generate_all_recommendations",
        return_value=[_recommendation()],
    ):
        result = runner.invoke(
            cli,
            ["analyze", "role", "--role", str(role), "--output-format", "json", "--fail-on", "warning"],
        )

    assert result.exit_code == 1
    assert '"findings"' in result.output
    assert "A finding" in result.output
    assert not (role / ".docsible").exists()
    assert not (role / "README.md").exists()


def test_validate_is_read_only_and_strict_uses_markdown_issues(tmp_path):
    role = _role(tmp_path)
    readme = role / "README.md"
    readme.write_text("existing documentation\n", encoding="utf-8")
    runner = CliRunner()
    issue = ValidationIssue(
        type=ValidationType.CLARITY,
        severity=ValidationSeverity.ERROR,
        message="Invalid generated markdown",
    )

    with patch("docsible.validation.markdown_validator.MarkdownValidator.validate", return_value=[issue]), patch(
        "docsible.commands.document_role.orchestrators.role_orchestrator.generate_all_recommendations",
        return_value=[_recommendation()],
    ):
        result = runner.invoke(cli, ["validate", "role", "--role", str(role)])

    assert result.exit_code == 1
    assert "Markdown validation failed" in str(result.exception)
    assert readme.read_text(encoding="utf-8") == "existing documentation\n"
    assert not (role / ".docsible").exists()


def test_document_dry_run_does_not_create_docsible(tmp_path):
    role = _role(tmp_path)
    runner = CliRunner()

    result = runner.invoke(cli, ["document", "role", "--role", str(role), "--dry-run"])

    assert result.exit_code == 0, result.output
    assert not (role / ".docsible").exists()
    assert not (role / "README.md").exists()


def test_presets_override_click_defaults_but_explicit_cli_options_win(tmp_path):
    role = _role(tmp_path)
    runner = CliRunner()

    with patch("docsible.commands.document.role.core_doc_the_role") as command:
        result = runner.invoke(cli, ["document", "role", "--role", str(role), "--preset", "personal"])
    assert result.exit_code == 0
    assert command.call_args.kwargs["minimal"] is True
    assert command.call_args.kwargs["validate_markdown"] is True

    with patch("docsible.commands.document.role.core_doc_the_role") as command:
        result = runner.invoke(
            cli,
            ["document", "role", "--role", str(role), "--preset", "personal", "--no-validate"],
        )
    assert result.exit_code == 0
    assert command.call_args.kwargs["validate_markdown"] is False


def test_project_config_is_resolved_from_target_role_not_cwd(tmp_path):
    role = _role(tmp_path / "project")
    config_dir = role / ".docsible"
    config_dir.mkdir()
    (config_dir / "config.yml").write_text(
        yaml.dump({"preset": "personal", "overrides": {}, "ci_cd": {}}), encoding="utf-8"
    )
    runner = CliRunner()

    with runner.isolated_filesystem(), patch("docsible.commands.document.role.core_doc_the_role") as command:
        result = runner.invoke(cli, ["document", "role", "--role", str(role)])

    assert result.exit_code == 0
    assert command.call_args.kwargs["minimal"] is True


def test_implicit_smart_minimal_does_not_change_document_content_flags(tmp_path):
    role = _role(tmp_path)
    runner = CliRunner()

    contexts = []
    with patch(
        "docsible.commands.document_role.smart_defaults_integration.apply_smart_defaults",
        return_value=(False, True, False, None),
    ), patch(
        "docsible.commands.document_role.core_orchestrated.RoleOrchestrator.execute",
        lambda orchestrator: contexts.append(orchestrator.context),
    ):
        result = runner.invoke(cli, ["document", "role", "--role", str(role)])

    assert result.exit_code == 0
    context = contexts[0]
    assert context.content.minimal is False
    assert context.content.no_vars is False
    assert context.content.no_tasks is False
    assert context.content.no_diagrams is False


def test_explicit_minimal_from_cli_preset_or_config_derives_content_flags(tmp_path):
    role = _role(tmp_path)
    runner = CliRunner()
    contexts = []

    with patch(
        "docsible.commands.document_role.core_orchestrated.RoleOrchestrator.execute",
        lambda orchestrator: contexts.append(orchestrator.context),
    ):
        result = runner.invoke(cli, ["document", "role", "--role", str(role), "--minimal"])
        assert result.exit_code == 0

        result = runner.invoke(cli, ["document", "role", "--role", str(role), "--preset", "personal"])
        assert result.exit_code == 0

        config_dir = role / ".docsible"
        config_dir.mkdir()
        (config_dir / "config.yml").write_text(
            yaml.dump({"preset": None, "overrides": {"minimal": True}, "ci_cd": {}}),
            encoding="utf-8",
        )
        result = runner.invoke(cli, ["document", "role", "--role", str(role)])
        assert result.exit_code == 0

    for context in contexts:
        assert context.content.minimal is True
        assert context.content.no_vars is True
        assert context.content.no_tasks is True
        assert context.content.no_diagrams is True


def test_analyze_forces_complexity_report_despite_click_default(tmp_path):
    role = _role(tmp_path)
    runner = CliRunner()

    with patch("docsible.commands.analyze.role.core_doc_the_role") as command:
        result = runner.invoke(cli, ["analyze", "role", "--role", str(role)])

    assert result.exit_code == 0
    assert command.call_args.kwargs["complexity_report"] is True
