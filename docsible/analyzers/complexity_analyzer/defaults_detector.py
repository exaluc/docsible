"""Complexity detection adapter for the SmartDefaultsEngine.

This module provides the SmartDefaultsEngine interface for the complexity analyzer.
It adapts the complexity_analyzer output to the DetectionResult interface used
by the defaults engine.
"""

import logging
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from docsible.constants import (
    MAX_TASK_FILES,
    MAX_TASKS,
    MAX_VARIABLES_USED,
    MINIMUM_TASK_FILES,
    MINIMUM_TASKS_TO_VISUALIZE,
)
from docsible.defaults.detectors.base import DetectionResult, Detector

from .models import ComplexityCategory, ComplexityMetrics

logger = logging.getLogger(__name__)


class ComplexityFindings(BaseModel):
    """Structured complexity findings.

    Why a pydantic class instead of dataclass?
    - Type safety: mypy catches typos like findings['totl_tasks']
    - Auto-completion: IDE knows what fields exist
    - Validation: Can add validators to ensure valid values
    - Documentation: Self-documenting structure
    """

    category: ComplexityCategory
    total_tasks: int = Field(ge=0, description="Total task in file")
    task_files: int = Field(ge=0, description="Task files in role folder")
    total_vars: int = Field(ge=0, description="Total vars in used in this role")
    handlers: int = Field(ge=0, description="Handlers present in this role")
    has_dependencies: bool = Field(description="Boolean has the role dependencies")
    complexity_score: float = Field(
        ge=0.0, description="How complex is this role based on measured criterias"
    )

    @property
    def is_simple(self) -> bool:
        """Convenience method for decision rules."""
        return self.category == ComplexityCategory.SIMPLE

    @property
    def is_complex(self) -> bool:
        """Convenience method for decision rules."""
        return self.category in (ComplexityCategory.COMPLEX, ComplexityCategory.ENTERPRISE)

    @property
    def requires_visualization(self) -> bool:
        """Business logic: when do we need diagrams?"""
        return self.total_tasks > MINIMUM_TASKS_TO_VISUALIZE or self.task_files > MINIMUM_TASK_FILES


class ComplexityDetector(Detector):
    """Detects role complexity using existing analyzers.

    Design Decision: Reuse existing complexity analysis
    - Don't duplicate logic
    - Leverage tested code
    - Adapter pattern: existing analyzer → detector interface
    """

    def detect(self, role_path: Path) -> DetectionResult:
        """Detect complexity characteristics of the role.

        Args:
            role_path: Path to Ansible role

        Returns:
            DetectionResult with ComplexityFindings
        """
        # Validation (inherited from base class)
        self.validate_role_path(role_path)

        try:
            # Leverage existing complexity analyzer
            # This is the Adapter pattern:
            # - ComplexityReport has its own interface
            # - We adapt it to DetectionResult interface
            from docsible.analyzers.complexity_analyzer import analyze_role_complexity_cached

            # Use cached version which accepts Path directly
            # Note: @cache_by_dir_mtime decorator changes first param to 'path'
            report = analyze_role_complexity_cached(
                path=role_path, include_patterns=False, min_confidence=0.7, no_docsible=True
            )

            # Extract metrics and category from report
            metrics = report.metrics
            category = report.category

            # Map ComplexityCategory enum values
            # Note: ComplexityCategory.value is lowercase ("simple"), .name is uppercase ("SIMPLE")
            category_map = {
                "SIMPLE": ComplexityCategory.SIMPLE,
                "MEDIUM": ComplexityCategory.MEDIUM,
                "COMPLEX": ComplexityCategory.COMPLEX,
                "ENTERPRISE": ComplexityCategory.ENTERPRISE,
            }

            # Transform to our detection format
            findings = ComplexityFindings(
                category=category_map.get(category.name, ComplexityCategory.MEDIUM),
                total_tasks=metrics.total_tasks,
                task_files=metrics.task_files,  # Already an int, not a list
                total_vars=0,  # ComplexityMetrics doesn't track variables
                handlers=metrics.handlers,
                has_dependencies=metrics.role_dependencies > 0,
                complexity_score=self._calculate_score(metrics),
            )

            # Return standardized DetectionResult
            # Store the full ComplexityReport in metadata for reuse by orchestrator
            return DetectionResult(
                detector_name="ComplexityDetector",
                findings=findings.model_dump(),
                confidence=self._calculate_confidence(metrics),
                metadata={
                    "analysis_version": "1.0",
                    "task_file_count": metrics.task_files,
                    "complexity_report": report,  # Store full report for reuse
                },
            )

        except Exception as e:
            # Defensive programming: always return valid result
            # Even on error, we can return low-confidence defaults
            logger.error(f"Complexity detection failed for {role_path}: {e}")

            return DetectionResult(
                detector_name="ComplexityDetector",
                findings=self._default_findings(),
                confidence=0.0,  # Zero confidence = error state
                metadata={"error": str(e)},
            )

    def _calculate_score(self, metrics: ComplexityMetrics) -> float:
        """Calculate normalized complexity score (0.0 - 1.0).

        This is a simple heuristic. In production, you might use:
        - Machine learning model
        - More sophisticated weighting
        - Historical data

        Returns:
            Float between 0.0 (trivial) and 1.0 (extremely complex)
        """
        # Simple weighted formula
        # Adjust weights based on what you've learned matters most
        task_score = min(metrics.total_tasks / MAX_TASKS, 1.0)
        file_score = min(metrics.task_files / MAX_TASK_FILES, 1.0)
        # ComplexityMetrics doesn't track variables, so use conditional tasks as proxy
        var_score = min(metrics.conditional_tasks / MAX_VARIABLES_USED, 1.0)

        # Weighted average
        score = (
            task_score * 0.5  # Tasks are 50% of complexity
            + file_score * 0.3  # File organization is 30%
            + var_score * 0.2  # Variables are 20%
        )

        return score

    def _calculate_confidence(self, metrics: ComplexityMetrics) -> float:
        """Calculate confidence in the detection.

        Why confidence levels?
        - Decision rules can weight high-confidence findings more
        - Can warn users when detection is uncertain
        - Enables graceful degradation

        Returns:
            Float between 0.0 (no confidence) and 1.0 (high confidence)
        """
        # High confidence if we found actual content to analyze
        if metrics.total_tasks > 0:
            return 1.0

        # Medium confidence if role structure exists but is empty
        if metrics.task_files:
            return 0.5

        # Low confidence if we found nothing
        return 0.3

    def _default_findings(self) -> dict[str, Any]:
        """Safe defaults when detection fails."""
        return ComplexityFindings(
            category=ComplexityCategory.MEDIUM,  # Conservative default
            total_tasks=0,
            task_files=0,
            total_vars=0,
            handlers=0,
            has_dependencies=False,
            complexity_score=0.5,
        ).model_dump()
