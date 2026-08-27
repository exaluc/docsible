"""Pydantic models for role command context.

Reduces 30+ parameters to structured configuration objects.
"""

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class PathConfig(BaseModel):
    """File and directory paths configuration.

    Attributes:
        role_path: Path to role directory
        collection_path: Optional path to collection directory
        playbook: Optional playbook file path
        output: Output filename for generated documentation
    """

    role_path: Path | None = Field(None, description="Path to role directory")
    collection_path: Path | None = Field(None, description="Path to collection")
    playbook: Path | None = Field(None, description="Playbook file path")
    output: str = Field("README.md", description="Output filename")

    class ConfigDict:
        """Pydantic configuration."""

        frozen = False
        validate_assignment = True


class TemplateConfig(BaseModel):
    """Template configuration.

    Attributes:
        hybrid: Use hybrid template (manual + auto-generated)
        md_role_template: Custom role template path
        md_collection_template: Custom collection template path
    """

    hybrid: bool = Field(False, description="Use hybrid template")
    md_role_template: Path | None = Field(None, description="Custom role template")
    md_collection_template: Path | None = Field(None, description="Custom collection template")

    class ConfigDict:
        """Pydantic configuration."""

        frozen = False
        validate_assignment = True


class ContentFlags(BaseModel):
    """Content inclusion/exclusion flags.

    Controls which sections to include in generated documentation.

    Attributes:
        no_vars: Skip variable documentation
        no_tasks: Skip task documentation
        no_diagrams: Skip all diagrams
        simplify_diagrams: Show only simplified diagrams
        no_examples: Skip example playbooks
        no_metadata: Skip metadata section
        no_handlers: Skip handlers documentation
        minimal: Enable minimal mode (sets multiple flags)
    """

    no_vars: bool = Field(False, description="Skip variables")
    no_tasks: bool = Field(False, description="Skip tasks")
    no_diagrams: bool = Field(False, description="Skip diagrams")
    simplify_diagrams: bool = Field(False, description="Simplify diagrams")
    no_examples: bool = Field(False, description="Skip examples")
    no_metadata: bool = Field(False, description="Skip metadata")
    no_handlers: bool = Field(False, description="Skip handlers")
    minimal: bool = Field(False, description="Minimal mode")

    class ConfigDict:
        """Pydantic configuration."""

        frozen = False
        validate_assignment = True


class DiagramConfig(BaseModel):
    """Diagram generation configuration.

    Attributes:
        generate_graph: Generate Mermaid diagrams
        show_dependencies: Show dependency matrix
    """

    generate_graph: bool = Field(False, description="Generate Mermaid diagrams")
    show_dependencies: bool = Field(False, description="Show dependency matrix")

    class ConfigDict:
        """Pydantic configuration."""

        frozen = False
        validate_assignment = True


class AnalysisConfig(BaseModel):
    """Analysis and reporting configuration.

    Attributes:
        complexity_report: Display complexity report
        include_complexity: Include complexity in README
        simplification_report: Show simplification suggestions
        analyze_only: Analyze without generating documentation
        cached_complexity_report: Cached ComplexityReport from smart defaults (internal)
        show_info: Show INFO-level recommendations
        recommendations_only: Show only recommendations without generating documentation
    """

    complexity_report: bool = Field(False, description="Show complexity report")
    include_complexity: bool = Field(False, description="Include in README")
    simplification_report: bool = Field(False, description="Show simplification suggestions")
    analyze_only: bool = Field(False, description="Analyze without generating docs")
    show_info: bool = Field(False, description="Show INFO-level recommendations")
    recommendations_only: bool = Field(
        False, description="Show only recommendations without generating docs"
    )
    positive_framing: bool = Field(True, description="Use positive output framing")
    fail_on: str = Field(
        "none",
        description="Exit 1 if findings at this severity or above (none/info/warning/critical)",
    )
    essential_only: bool = Field(
        True, description="Show only WARNING/CRITICAL findings by default (hide INFO)"
    )
    max_recommendations: int | None = Field(
        5, description="Cap recommendations shown in default mode (None=unlimited)"
    )
    advanced_patterns: bool = Field(False, description="Show all findings including INFO, no cap")
    output_format: str = Field("text", description="Output format: text or json")
    apply_suppressions: bool = Field(
        default=True,
        description="Apply .docsible/suppress.yml rules before displaying recommendations",
    )
    cached_complexity_report: Any | None = Field(
        None,
        description="Cached ComplexityReport from smart defaults (avoid duplicate analysis)",
        exclude=True,  # Don't include in model serialization
    )

    class ConfigDict:
        """Pydantic configuration."""

        frozen = False
        validate_assignment = True


class ProcessingConfig(BaseModel):
    """Processing options.

    Attributes:
        comments: Extract task comments
        task_line: Extract line numbers
        no_backup: Skip backup creation
        no_docsible: Skip .docsible file handling
        dry_run: Preview without writing files
        append: Append to existing README
    """

    comments: bool = Field(False, description="Extract task comments")
    task_line: bool = Field(False, description="Extract line numbers")
    no_backup: bool = Field(False, description="Skip backup creation")
    no_docsible: bool = Field(False, description="Skip .docsible file")
    dry_run: bool = Field(False, description="Preview without writing")
    append: bool = Field(False, description="Append to existing README")

    class ConfigDict:
        """Pydantic configuration."""

        frozen = False
        validate_assignment = True


class ValidationConfig(BaseModel):
    """Markdown validation configuration.

    Attributes:
        validate_markdown: Enable markdown validation
        auto_fix: Automatically fix validation issues
        strict_validation: Fail on validation errors
    """

    validate_markdown: bool = Field(False, description="Validate markdown")
    auto_fix: bool = Field(False, description="Auto-fix issues")
    strict_validation: bool = Field(False, description="Fail on validation errors")
    validate_only: bool = Field(False, description="Validate rendered markdown without writing files")

    class ConfigDict:
        """Pydantic configuration."""

        frozen = False
        validate_assignment = True


class RepositoryConfig(BaseModel):
    """Repository information.

    Attributes:
        repository_url: Repository URL or 'detect' for auto-detection
        repo_type: Repository type (github, gitlab, gitea)
        repo_branch: Repository branch name
    """

    repository_url: str | None = Field(None, description="Repository URL or 'detect'")
    repo_type: str | None = Field(None, description="Repository type")
    repo_branch: str | None = Field(None, description="Repository branch")

    class ConfigDict:
        """Pydantic configuration."""

        frozen = False
        validate_assignment = True


class RoleCommandContext(BaseModel):
    """Complete context for role documentation command.

    Reduces 30 parameters to 1 structured object following the pattern
    established by RenderContext in the renderers module.

    Example:
        >>> from pathlib import Path
        >>> context = RoleCommandContext(
        ...     paths=PathConfig(role_path=Path("./my-role")),
        ...     template=TemplateConfig(hybrid=True),
        ...     content=ContentFlags(no_vars=False),
        ...     diagrams=DiagramConfig(generate_graph=True),
        ...     analysis=AnalysisConfig(),
        ...     processing=ProcessingConfig(),
        ...     validation=ValidationConfig(),
        ...     repository=RepositoryConfig(),
        ... )
    """

    paths: PathConfig
    template: TemplateConfig
    content: ContentFlags
    diagrams: DiagramConfig
    analysis: AnalysisConfig
    processing: ProcessingConfig
    validation: ValidationConfig
    repository: RepositoryConfig

    class ConfigDict:
        """Pydantic configuration."""

        frozen = False
        validate_assignment = True
