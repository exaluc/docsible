"""Tests for --fail-on and --strict-validation exit behaviour in RoleOrchestrator."""
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from docsible.commands.document_role.models import (
    AnalysisConfig,
    ContentFlags,
    DiagramConfig,
    PathConfig,
    ProcessingConfig,
    RepositoryConfig,
    RoleCommandContext,
    TemplateConfig,
    ValidationConfig,
)
from docsible.commands.document_role.orchestrators.role_orchestrator import RoleOrchestrator
from docsible.models.recommendation import Recommendation
from docsible.models.severity import Severity

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_rec(severity: Severity) -> Recommendation:
    return Recommendation(
        category="test",
        message=f"Test finding ({severity.value})",
        rationale="For testing",
        severity=severity,
        confidence=1.0,
    )


def _make_context(
    fail_on: str = "none",
    strict_validation: bool = False,
    role_path: Path | None = None,
) -> RoleCommandContext:
    return RoleCommandContext(
        paths=PathConfig(role_path=role_path or Path("/fake/role")),
        template=TemplateConfig(),
        content=ContentFlags(),
        diagrams=DiagramConfig(),
        analysis=AnalysisConfig(fail_on=fail_on, advanced_patterns=True),
        processing=ProcessingConfig(dry_run=True),
        validation=ValidationConfig(strict_validation=strict_validation),
        repository=RepositoryConfig(),
    )


def _make_orchestrator(context: RoleCommandContext) -> RoleOrchestrator:
    return RoleOrchestrator(context)


# Shared patches so every test avoids real filesystem / analysis calls.
_PATCH_VALIDATE = "docsible.commands.document_role.orchestrators.role_orchestrator.RoleOrchestrator._validate_paths"
_PATCH_PLAYBOOK = "docsible.commands.document_role.orchestrators.role_orchestrator.RoleOrchestrator._load_playbook"
_PATCH_BUILD = "docsible.commands.document_role.orchestrators.role_orchestrator.RoleOrchestrator._build_role_info"
_PATCH_ANALYZE = "docsible.commands.document_role.orchestrators.role_orchestrator.RoleOrchestrator._analyze_role"
_PATCH_DIAGRAMS = "docsible.commands.document_role.orchestrators.role_orchestrator.RoleOrchestrator._generate_diagrams"
_PATCH_DEPS = "docsible.commands.document_role.orchestrators.role_orchestrator.RoleOrchestrator._generate_dependencies"
_PATCH_SUPPRESSIONS = "docsible.commands.document_role.orchestrators.role_orchestrator.RoleOrchestrator"


def _run_execute_with_recs(recs: list[Recommendation], context: RoleCommandContext) -> None:
    """Run orchestrator.execute() with mocked internals, injecting given recommendations."""
    orch = _make_orchestrator(context)

    fake_path = Path("/fake/role")
    fake_role_info: dict = {"name": "fake_role"}
    fake_analysis = MagicMock(recommendations=recs)
    fake_diagrams: dict = {
        "generate_graph": False,
        "mermaid_code_per_file": {},
        "sequence_diagram_high_level": None,
        "sequence_diagram_detailed": None,
        "state_diagram": None,
        "integration_boundary_diagram": None,
        "architecture_diagram": None,
    }
    fake_deps: dict = {
        "dependency_matrix": None,
        "dependency_summary": None,
        "show_matrix": False,
    }

    with (
        patch(_PATCH_VALIDATE, return_value=fake_path),
        patch(_PATCH_PLAYBOOK, return_value=None),
        patch(_PATCH_BUILD, return_value=fake_role_info),
        patch(_PATCH_ANALYZE, return_value=fake_analysis),
        patch(_PATCH_DIAGRAMS, return_value=fake_diagrams),
        patch(_PATCH_DEPS, return_value=fake_deps),
        # Skip suppression machinery — just return recs unchanged
        patch(
            "docsible.suppression.engine.apply_suppressions",
            return_value=(recs, []),
        ),
        patch("docsible.commands.document_role.orchestrators.role_orchestrator.click.echo"),
    ):
        orch.execute()


# ---------------------------------------------------------------------------
# fail_on tests
# ---------------------------------------------------------------------------


class TestFailOn:
    def test_fail_on_none_with_critical_no_exit(self):
        """fail_on='none' never raises SystemExit regardless of severity."""
        recs = [_make_rec(Severity.CRITICAL)]
        context = _make_context(fail_on="none")
        # Should not raise
        _run_execute_with_recs(recs, context)

    def test_fail_on_critical_with_critical_raises(self):
        """fail_on='critical' exits 1 when CRITICAL findings are present."""
        recs = [_make_rec(Severity.CRITICAL)]
        context = _make_context(fail_on="critical")
        with pytest.raises(SystemExit) as exc_info:
            _run_execute_with_recs(recs, context)
        assert exc_info.value.code == 1

    def test_fail_on_critical_with_warning_only_no_exit(self):
        """fail_on='critical' does NOT exit when only WARNING findings exist."""
        recs = [_make_rec(Severity.WARNING)]
        context = _make_context(fail_on="critical")
        # Should not raise
        _run_execute_with_recs(recs, context)

    def test_fail_on_warning_with_warning_raises(self):
        """fail_on='warning' exits 1 when WARNING findings are present."""
        recs = [_make_rec(Severity.WARNING)]
        context = _make_context(fail_on="warning")
        with pytest.raises(SystemExit) as exc_info:
            _run_execute_with_recs(recs, context)
        assert exc_info.value.code == 1

    def test_fail_on_warning_with_critical_raises(self):
        """fail_on='warning' also exits 1 when CRITICAL findings exist (threshold met)."""
        recs = [_make_rec(Severity.CRITICAL)]
        context = _make_context(fail_on="warning")
        with pytest.raises(SystemExit) as exc_info:
            _run_execute_with_recs(recs, context)
        assert exc_info.value.code == 1

    def test_fail_on_warning_with_empty_recs_no_exit(self):
        """fail_on='warning' does NOT exit when there are no recommendations."""
        recs: list[Recommendation] = []
        context = _make_context(fail_on="warning")
        # Should not raise
        _run_execute_with_recs(recs, context)

    def test_fail_on_info_with_info_raises(self):
        """fail_on='info' exits 1 when INFO findings are present."""
        recs = [_make_rec(Severity.INFO)]
        context = _make_context(fail_on="info")
        with pytest.raises(SystemExit) as exc_info:
            _run_execute_with_recs(recs, context)
        assert exc_info.value.code == 1


# ---------------------------------------------------------------------------
# strict_validation tests
# ---------------------------------------------------------------------------


class TestStrictValidation:
    def test_strict_validation_with_warning_raises(self):
        """strict_validation=True exits 1 when WARNING findings are present."""
        recs = [_make_rec(Severity.WARNING)]
        context = _make_context(strict_validation=True)
        with pytest.raises(SystemExit) as exc_info:
            _run_execute_with_recs(recs, context)
        assert exc_info.value.code == 1

    def test_strict_validation_with_critical_raises(self):
        """strict_validation=True exits 1 when CRITICAL findings are present."""
        recs = [_make_rec(Severity.CRITICAL)]
        context = _make_context(strict_validation=True)
        with pytest.raises(SystemExit) as exc_info:
            _run_execute_with_recs(recs, context)
        assert exc_info.value.code == 1

    def test_strict_validation_with_no_findings_no_exit(self):
        """strict_validation=True does NOT exit when there are no findings."""
        recs: list[Recommendation] = []
        context = _make_context(strict_validation=True)
        # Should not raise
        _run_execute_with_recs(recs, context)

    def test_strict_validation_with_info_only_no_exit(self):
        """strict_validation=True does NOT exit for INFO-only findings."""
        recs = [_make_rec(Severity.INFO)]
        context = _make_context(strict_validation=True)
        # Should not raise — strict_validation only blocks WARNING/CRITICAL
        _run_execute_with_recs(recs, context)
