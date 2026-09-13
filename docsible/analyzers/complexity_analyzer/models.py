"""Data models for complexity analysis."""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ComplexityCategory(str, Enum):
    """Role complexity categories based on task count."""

    SIMPLE = "simple"  # 1-10 tasks
    MEDIUM = "medium"  # 11-25 tasks
    COMPLEX = "complex"  # 25+ tasks
    ENTERPRISE = "enterprise"  # Large-scale enterprise roles


class IntegrationType(str, Enum):
    """Types of external system integrations."""

    API = "api"
    DATABASE = "database"
    VAULT = "vault"
    CLOUD = "cloud"
    NETWORK = "network"
    CONTAINER = "container"
    MONITORING = "monitoring"


class IntegrationPoint(BaseModel):
    """Represents a detected external system integration."""

    type: IntegrationType
    system_name: str
    modules_used: list[str]
    task_count: int
    uses_credentials: bool = False
    # Type-specific details
    endpoints: list[str] = Field(default_factory=list, description="API endpoints or URLs")
    ports: list[int] = Field(default_factory=list, description="Network ports used")
    services: list[str] = Field(
        default_factory=list, description="Cloud services or container images"
    )
    details: dict[str, Any] = Field(
        default_factory=dict, description="Additional type-specific details"
    )


class ComplexityMetrics(BaseModel):
    """Detailed metrics for role complexity analysis."""

    # Task metrics
    total_tasks: int = Field(description="Total number of tasks across all files")
    task_files: int = Field(description="Number of task files")
    handlers: int = Field(description="Number of handlers")
    conditional_tasks: int = Field(description="Tasks with 'when' conditions")
    error_handlers: int = Field(
        default=0, description="Tasks with error handling (rescue/always blocks)"
    )

    # Internal composition (role orchestration)
    role_dependencies: int = Field(default=0, description="Role dependencies from meta/main.yml")
    collection_dependencies: int = Field(default=0, description="Collection dependencies from meta/main.yml")
    role_includes: int = Field(default=0, description="include_role/import_role count")
    task_includes: int = Field(default=0, description="include_tasks/import_tasks count")

    # Execution graph metrics (source-backed relationships, not runtime claims)
    static_reachable_task_files: int = Field(
        default=0, description="Files reachable via static/conditional boundaries only"
    )
    dynamically_reachable_task_files: int = Field(
        default=0, description="Files reachable only through an unresolved dynamic boundary"
    )
    dynamic_boundaries: int = Field(default=0)
    unknown_boundaries: int = Field(default=0)
    external_role_references: int = Field(default=0)
    loop_tasks: int = Field(default=0)
    notification_edges: int = Field(default=0)
    unreachable_task_files: int = Field(
        default=0, description="Files with no inbound boundary from any resolved edge"
    )
    conditional_decision_points: int = Field(default=0)

    # External integrations
    external_integrations: int = Field(
        default=0, description="Count of external system connections"
    )

    # Calculated metrics
    max_tasks_per_file: int = Field(description="Maximum tasks in a single file")
    avg_tasks_per_file: float = Field(description="Average tasks per file")

    @property
    def composition_score(self) -> int:
        """Calculate composition complexity score.

        Higher score = more complex orchestration.
        """
        return (
            self.role_dependencies * 2  # Meta deps are important
            + self.role_includes
            + self.task_includes
        )

    @property
    def conditional_percentage(self) -> float:
        """Percentage of tasks that are conditional."""
        if self.total_tasks == 0:
            return 0.0
        return (self.conditional_tasks / self.total_tasks) * 100


class FileComplexityDetail(BaseModel):
    """Detailed complexity metrics for a single task file."""

    file_path: str = Field(description="Relative path to task file")
    task_count: int = Field(description="Number of tasks in this file")
    conditional_count: int = Field(description="Number of conditional tasks")
    conditional_percentage: float = Field(description="Percentage of conditional tasks")
    has_integrations: bool = Field(default=False, description="File uses external integrations")
    integration_types: list[str] = Field(
        default_factory=list, description="Types of integrations used"
    )
    module_diversity: int = Field(description="Number of unique modules used")
    primary_concern: str | None = Field(default=None, description="Detected primary concern")
    phase_detection: dict[str, Any] | None = Field(
        default=None, description="Phase detection results"
    )
    line_ranges: list[tuple] | None = Field(default=None, description="Line ranges for each task")

    @property
    def is_god_file(self) -> bool:
        """Check if this is a 'god file' (too many responsibilities)."""
        return self.task_count > 15 or self.module_diversity > 10

    @property
    def is_conditional_heavy(self) -> bool:
        """Check if this file has high conditional complexity."""
        return self.conditional_percentage > 50.0 and self.conditional_count > 5


class ComplexityReport(BaseModel):
    """Complete complexity analysis report."""

    metrics: ComplexityMetrics
    category: ComplexityCategory
    integration_points: list[IntegrationPoint] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    task_files_detail: list[dict[str, Any]] = Field(default_factory=list)
    execution_graph: dict[str, Any] = Field(default_factory=dict)

    # Pattern analysis (optional)
    pattern_analysis: Any | None = Field(
        default=None,
        description="Detailed pattern analysis report with simplification suggestions",
    )


class ConditionalHotspot(BaseModel):
    """Represents a file with high conditional complexity."""

    file_path: str
    conditional_variable: str = Field(description="Main variable driving conditionals")
    usage_count: int = Field(description="How many times this variable appears in conditions")
    affected_tasks: int = Field(description="Number of tasks using this condition")
    suggestion: str = Field(description="Recommended action")


class InflectionPoint(BaseModel):
    """Represents a major branching point in task execution."""

    file_path: str
    task_name: str = Field(description="Task where branching occurs")
    task_index: int = Field(description="Position in file (0-based)")
    variable: str = Field(description="Variable driving the branch")
    branch_count: int = Field(description="Number of execution paths from this point")
    downstream_tasks: int = Field(description="Tasks affected by this branch")
