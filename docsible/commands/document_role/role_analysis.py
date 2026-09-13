"""Shared role analysis and rendering, reused across entry points.

Three call sites need "what does this role's complexity/execution graph/
recommendations look like": single-role `document role`, `document role
--collection`, and `scan collection`. Before this module they each computed
it independently and had drifted (e.g. `scan collection` did not pass the
complexity report into recommendation generation, so it missed the
graph-aware findings the single-role path already had).

This module splits the work into two layers:

- `analyze_role()` — pure computation, no file I/O. Used by all three
  callers, including `scan collection` which never renders a README.
- `render_analyzed_role()` — diagram generation, dependency matrix, and the
  actual `ReadmeRenderer.render_role()` call. Used by callers that write a
  role README (single-role `document role`, and `document role
  --collection`, which previously skipped this entirely).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from docsible.analyzers import analyze_role_complexity
from docsible.analyzers.complexity_analyzer.models import ComplexityReport
from docsible.analyzers.recommendations import generate_all_recommendations
from docsible.graphs import build_role_execution_graph
from docsible.models.recommendation import Recommendation


@dataclass
class RoleAnalysis:
    """Pure analysis result for one role: no file I/O, no rendering."""

    complexity_report: ComplexityReport
    recommendations: list[Recommendation]
    execution_graph: Any = None


def analyze_role(
    role_info: dict[str, Any],
    role_path: Path,
    *,
    include_patterns: bool = False,
    min_confidence: float = 0.7,
    cached_complexity_report: ComplexityReport | None = None,
) -> RoleAnalysis:
    """Compute complexity (incl. execution graph) and recommendations.

    Args:
        role_info: Role information dictionary from RoleInfoLoader
        role_path: Path to the role directory (recommendations scan the
            filesystem directly for some checks, e.g. vault encryption)
        include_patterns: Whether to run the (expensive) pattern analyzer
        min_confidence: Minimum confidence for pattern detection
        cached_complexity_report: Reuse an already-computed report (e.g. from
            smart defaults) instead of analyzing again

    Returns:
        RoleAnalysis with the complexity report, recommendations, and the
        one shared execution graph (reused by the complexity metrics and by
        any downstream render, so it is never rebuilt per command).
    """
    execution_graph = build_role_execution_graph(role_info)
    complexity_report = cached_complexity_report or analyze_role_complexity(
        role_info,
        include_patterns=include_patterns,
        min_confidence=min_confidence,
        execution_graph=execution_graph,
    )
    recommendations = generate_all_recommendations(role_path, complexity_report)
    return RoleAnalysis(
        complexity_report=complexity_report,
        recommendations=recommendations,
        execution_graph=execution_graph,
    )


def render_analyzed_role(
    *,
    role_info: dict[str, Any],
    role_path: Path,
    analysis: RoleAnalysis,
    output_path: Path,
    template_type: str = "standard_modular",
    custom_template_path: str | None = None,
    generate_graph: bool = False,
    minimal: bool = False,
    simplify_diagrams: bool = False,
    show_dependencies: bool = False,
    no_vars: bool = False,
    no_tasks: bool = False,
    no_diagrams: bool = False,
    no_examples: bool = False,
    no_metadata: bool = False,
    no_handlers: bool = False,
    include_complexity: bool = False,
    append: bool = False,
    backup: bool = True,
    validate: bool = True,
    auto_fix: bool = False,
    strict_validation: bool = False,
    playbook_content: str | None = None,
    execution_graph: Any | None = None,
) -> Path:
    """Generate diagrams/dependency matrix and render a role README.

    Reuses the same diagram-generation helpers as single-role `document
    role`, so a role documented as part of a collection gets an identical
    Architecture Overview / Execution Graph Summary / Execution Routes /
    Complexity Analysis to a standalone role.

    Returns:
        The path written.
    """
    from docsible.commands.document_role.helpers import (
        generate_dependency_matrix,
        generate_integration_and_architecture_diagrams,
        generate_mermaid_diagrams,
    )
    from docsible.graphs import build_role_execution_graph
    from docsible.renderers.readme_renderer import ReadmeRenderer

    analysis_report = analysis.complexity_report
    if execution_graph is None:
        execution_graph = build_role_execution_graph(role_info)

    diagrams = generate_mermaid_diagrams(
        generate_graph=generate_graph,
        role_info=role_info,
        playbook_content=playbook_content,
        analysis_report=analysis_report,
        minimal=minimal,
        simplify_diagrams=simplify_diagrams,
    )
    diagrams["generate_graph"] = generate_graph
    diagrams["execution_graph"] = execution_graph
    diagrams["execution_phases"] = execution_graph.execution_phases()

    integration_boundary, architecture = generate_integration_and_architecture_diagrams(
        generate_graph=generate_graph,
        role_info=role_info,
        analysis_report=analysis_report,
        execution_graph=execution_graph,
    )
    diagrams["integration_boundary_diagram"] = integration_boundary
    diagrams["architecture_diagram"] = architecture

    dependency_matrix, dependency_summary, show_dependency_matrix = generate_dependency_matrix(
        show_dependencies=show_dependencies,
        role_info=role_info,
        analysis_report=analysis_report,
    )

    render_options: dict[str, Any] = {
        "mermaid_code_per_file": diagrams.get("mermaid_code_per_file", {}),
        "sequence_diagram_high_level": diagrams.get("sequence_diagram_high_level"),
        "sequence_diagram_detailed": diagrams.get("sequence_diagram_detailed"),
        "state_diagram": diagrams.get("state_diagram"),
        "integration_boundary_diagram": diagrams.get("integration_boundary_diagram"),
        "architecture_diagram": diagrams.get("architecture_diagram"),
        "execution_phases": diagrams.get("execution_phases"),
        "complexity_report": analysis_report,
        "include_complexity": include_complexity,
        "dependency_matrix": dependency_matrix,
        "dependency_summary": dependency_summary,
        "show_dependency_matrix": show_dependency_matrix,
        "no_vars": no_vars,
        "no_tasks": no_tasks,
        "no_diagrams": no_diagrams,
        "simplify_diagrams": simplify_diagrams,
        "no_examples": no_examples,
        "no_metadata": no_metadata,
        "no_handlers": no_handlers,
    }

    renderer = ReadmeRenderer(
        backup=backup,
        validate=validate,
        auto_fix=auto_fix,
        strict_validation=strict_validation,
    )
    renderer.render_role(
        role_info=role_info,
        output_path=output_path,
        template_type=template_type,
        custom_template_path=custom_template_path,
        append=append,
        **render_options,
    )
    return output_path
