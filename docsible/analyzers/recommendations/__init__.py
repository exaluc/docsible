from pathlib import Path

from docsible.models.recommendation import Recommendation
from docsible.models.severity import Severity

from .enhancement import EnhancementRecommendationGenerator
from .quality import QualityRecommendationGenerator
from .security import SecurityRecommendationGenerator


def generate_all_recommendations(role_path: Path, analysis_report=None) -> list[Recommendation]:
    """Generate all recommendations for a role.

    Args:
        role_path: Path to Ansible role

    Returns:
        List of recommendations sorted by severity (critical first)
    """
    all_recommendations = []

    # Security (CRITICAL)
    security_gen = SecurityRecommendationGenerator()
    all_recommendations.extend(security_gen.analyze_role(role_path))

    # Quality (WARNING)
    quality_gen = QualityRecommendationGenerator()
    all_recommendations.extend(quality_gen.analyze_role(role_path))

    # Enhancements (INFO)
    enhancement_gen = EnhancementRecommendationGenerator()
    all_recommendations.extend(enhancement_gen.analyze_role(role_path))

    if analysis_report is not None:
        metrics = analysis_report.metrics
        if metrics.dynamic_boundaries:
            all_recommendations.append(
                Recommendation(
                    severity=Severity.INFO,
                    category="execution_graph",
                    message=f"{metrics.dynamic_boundaries} dynamic execution boundaries need runtime review",
                    rationale="Templated includes cannot be resolved to one static execution path.",
                    remediation="Review the Execution Graph Summary and validate each dynamic path.",
                    confidence=1.0,
                )
            )
        if metrics.collection_dependencies:
            all_recommendations.append(
                Recommendation(
                    severity=Severity.INFO,
                    category="execution_graph",
                    message=f"Role depends on {metrics.collection_dependencies} Ansible collections",
                    rationale="Collection availability affects portability and runtime module resolution.",
                    remediation="Pin and document collection requirements.",
                    confidence=1.0,
                )
            )

    # Sort by severity (critical first)
    all_recommendations.sort(key=lambda r: r.severity.priority, reverse=True)

    return all_recommendations
