"""JSON formatter for machine-readable recommendation output."""

import json
from collections import Counter

from docsible.models.recommendation import Recommendation


class JsonRecommendationFormatter:
    """Formats recommendations as JSON for CI tool integration."""

    def format(
        self,
        recommendations: list[Recommendation],
        role_name: str = "",
        truncated: bool = False,
        total_count: int | None = None,
        complexity_report=None,
    ) -> str:
        """Return JSON string of all recommendations."""
        severity_counts: Counter[str] = Counter(r.severity.value.lower() for r in recommendations)
        findings = [
            {
                "severity": r.severity.value.lower(),
                "category": r.category,
                "message": r.message,
                "rationale": r.rationale,
                "file": r.file_path or "",
                "line": r.line_number,
                "remediation": r.remediation or "",
                "confidence": r.confidence,
                "auto_fixable": r.auto_fixable,
            }
            for r in recommendations
        ]
        payload = {
            "role": role_name,
            "findings": findings,
            "summary": {
                "total": total_count if total_count is not None else len(recommendations),
                "shown": len(recommendations),
                "critical": severity_counts.get("critical", 0),
                "warning": severity_counts.get("warning", 0),
                "info": severity_counts.get("info", 0),
            },
            "truncated": truncated,
        }
        if complexity_report is not None:
            payload["complexity"] = complexity_report.metrics.model_dump(mode="json")
            payload["execution_graph"] = complexity_report.execution_graph
        return json.dumps(payload, indent=2)
