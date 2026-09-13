"""docsible scan collection — batch-scan all roles in a collection directory."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import click

from docsible.commands.scan.formatters.json import format_scan_json
from docsible.commands.scan.formatters.text import format_scan_text
from docsible.commands.scan.models.scan_result import RoleResult, ScanCollectionResult
from docsible.presets.registry import PresetRegistry
from docsible.presets.resolver import resolve_settings
from docsible.utils.cli_helpers import BriefHelpCommand

logger = logging.getLogger(__name__)

# Map ComplexityCategory enum values to human-friendly labels
_COMPLEXITY_MAP: dict[str, str] = {
    "simple": "low",
    "medium": "medium",
    "complex": "high",
    "enterprise": "high",
}

_SEVERITY_RANK: dict[str, int] = {
    "none": 0,
    "info": 1,
    "warning": 2,
    "critical": 3,
}


def _complexity_label(category_value: str) -> str:
    """Convert ComplexityCategory value to display label."""
    return _COMPLEXITY_MAP.get(category_value.lower(), "unknown")


def _analyse_role(role_path: Path, git_info: dict) -> RoleResult:
    """Run analysis on a single role and return a RoleResult.

    Args:
        role_path: Absolute path to the role directory.
        git_info: Pre-fetched git repository info (cached at collection level).

    Returns:
        RoleResult with metrics and findings.
    """
    from docsible.commands.document_role.role_analysis import analyze_role
    from docsible.commands.role_info_loader import RoleInfoLoader
    from docsible.models.severity import Severity

    role_name = role_path.name

    # Build role info (no README writes — analysis only)
    role_info = RoleInfoLoader().load(
        role_path,
        playbook_content=None,
        generate_graph=False,
        comments=False,
        task_line=False,
        belongs_to_collection=None,
        repository_url=git_info.get("repository"),
        repo_type=git_info.get("repository_type"),
        repo_branch=git_info.get("branch", "main"),
    )

    # Count tasks and variables
    task_count = sum(
        len(tf.get("tasks", [])) for tf in role_info.get("tasks", [])
    )
    defaults_count = sum(
        len(df.get("data", {})) for df in role_info.get("defaults", [])
    )
    vars_count = sum(
        len(vf.get("data", {})) for vf in role_info.get("vars", [])
    )
    variable_count = defaults_count + vars_count

    # Complexity + recommendations — shared with `document role` and
    # `document role --collection` so all three agree (this previously called
    # generate_all_recommendations() without the complexity report, missing
    # the graph-aware findings the other two paths already had).
    analysis = analyze_role(role_info, role_path, min_confidence=0.7)
    complexity_report = analysis.complexity_report
    complexity = _complexity_label(complexity_report.category.value)
    recommendations = analysis.recommendations

    critical_count = sum(1 for r in recommendations if r.severity == Severity.CRITICAL)
    warning_count = sum(1 for r in recommendations if r.severity == Severity.WARNING)
    info_count = sum(1 for r in recommendations if r.severity == Severity.INFO)

    top_recommendations = [r.message for r in recommendations[:5]]

    return RoleResult(
        name=role_name,
        path=role_path,
        task_count=task_count,
        variable_count=variable_count,
        complexity=complexity,
        critical_count=critical_count,
        warning_count=warning_count,
        info_count=info_count,
        top_recommendations=top_recommendations,
    )


@click.command(name="collection", cls=BriefHelpCommand)
@click.argument("path", default=".", required=False)
@click.option(
    "--path",
    "path_opt",
    default=None,
    help="Path to the collection directory (alternative to positional argument).",
    metavar="PATH",
)
@click.option(
    "--output-format",
    "output_format",
    type=click.Choice(["text", "json"]),
    default="text",
    show_default=True,
    help="Output format for the scan results.",
)
@click.option(
    "--fail-on",
    "fail_on",
    type=click.Choice(["none", "info", "warning", "critical"]),
    default="none",
    show_default=True,
    help="Exit with code 1 if any role has findings at or above this severity.",
)
@click.option(
    "--top-n",
    "top_n",
    type=int,
    default=0,
    show_default=True,
    help="Show only the N worst roles (0 = all roles).",
)
@click.option(
    "--preset",
    type=click.Choice(PresetRegistry.names()),
    default=None,
    help="Apply a built-in preset (personal/team/enterprise/consultant).",
)
@click.option(
    "--dry-run",
    "dry_run",
    is_flag=True,
    default=False,
    help="Print what would be scanned without running analysis.",
)
def scan_collection_cmd(
    path: str,
    path_opt: str | None,
    output_format: str,
    fail_on: str,
    top_n: int,
    preset: str | None,
    dry_run: bool,
) -> None:
    """Scan all roles in an Ansible collection directory.

    Discovers every role under PATH, runs analysis on each (no README writes),
    and outputs an aggregated cross-role summary.

    \b
    Examples:
      docsible scan collection ./my_collection
      docsible scan collection --path ./my_collection --output-format json
      docsible scan collection . --fail-on warning
    """
    # Resolve preset settings (they don't override explicit CLI flags here,
    # but we honour fail_on from preset if not explicitly set by user)
    resolved = resolve_settings(preset_name=preset, cli_overrides={"fail_on": fail_on})
    effective_fail_on: str = resolved.get("fail_on", fail_on)

    # Determine effective path: --path option wins over positional arg
    effective_path = path_opt if path_opt is not None else path

    collection_path = Path(effective_path).resolve()

    if not collection_path.exists():
        raise click.ClickException(f"Path does not exist: {collection_path}")

    if not collection_path.is_dir():
        raise click.ClickException(f"Path is not a directory: {collection_path}")

    # Discover roles
    from docsible.utils.project_structure import ProjectStructure

    ps = ProjectStructure(root_path=str(collection_path))
    role_paths = ps.find_roles()

    if not role_paths:
        click.echo(f"No roles found in {collection_path}", err=True)
        sys.exit(0)

    if dry_run:
        click.echo(f"\nDry-run: would scan {len(role_paths)} role(s) in {collection_path}")
        for rp in sorted(role_paths):
            click.echo(f"  - {rp.name}")
        click.echo("")
        return

    # In JSON mode, redirect logging to stderr so stdout carries only valid JSON
    if output_format == "json":
        for handler in logging.root.handlers:
            if isinstance(handler, logging.StreamHandler) and handler.stream is sys.stdout:
                handler.stream = sys.stderr

    # Cache git info at collection level to avoid per-role subprocess calls
    from docsible.utils.git import get_repo_info

    try:
        git_info: dict = get_repo_info(str(collection_path)) or {}
    except Exception as exc:
        logger.warning(f"Could not get Git info for collection: {exc}")
        git_info = {}

    # Analyse each role with per-role error isolation
    role_results: list[RoleResult] = []
    for role_path in sorted(role_paths):
        try:
            result = _analyse_role(role_path, git_info)
            role_results.append(result)
            logger.debug(f"Scanned role: {role_path.name}")
        except Exception as exc:
            logger.warning(f"Failed to analyse role '{role_path.name}': {exc}")
            role_results.append(
                RoleResult(
                    name=role_path.name,
                    path=role_path,
                    task_count=0,
                    variable_count=0,
                    complexity="unknown",
                    critical_count=0,
                    warning_count=0,
                    info_count=0,
                    top_recommendations=[],
                    error=str(exc),
                )
            )

    scan_result = ScanCollectionResult(
        collection_path=collection_path,
        total_roles=len(role_results),
        roles=role_results,
    )

    # Format and output
    if output_format == "json":
        click.echo(format_scan_json(scan_result, top_n=top_n))
    else:
        click.echo(format_scan_text(scan_result, top_n=top_n))

    # Exit code gate based on --fail-on threshold
    if effective_fail_on != "none":
        threshold = _SEVERITY_RANK[effective_fail_on]

        def _role_breaches_threshold(r: RoleResult) -> bool:
            # A role breaches if it has any findings at or above the threshold level.
            # threshold=1 (info)    → any of info/warning/critical
            # threshold=2 (warning) → warning or critical
            # threshold=3 (critical)→ critical only
            if threshold <= _SEVERITY_RANK["info"] and r.info_count > 0:
                return True
            if threshold <= _SEVERITY_RANK["warning"] and r.warning_count > 0:
                return True
            if threshold <= _SEVERITY_RANK["critical"] and r.critical_count > 0:
                return True
            return False

        failed_roles = [r for r in role_results if _role_breaches_threshold(r)]
        if failed_roles:
            click.echo(
                f"\nExiting with code 1: {len(failed_roles)} role(s) have findings"
                f" at '{effective_fail_on}' level or above.",
                err=True,
            )
            sys.exit(1)
