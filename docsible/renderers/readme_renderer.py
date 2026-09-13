import logging
from pathlib import Path
from typing import Any

from docsible.renderers.models import RenderContext
from docsible.renderers.processors import (
    BackupManager,
    ContentMerger,
    FileWriter,
    MarkdownProcessor,
    MetadataProcessor,
    TagProcessor,
    TemplateProcessor,
)

logger = logging.getLogger(__name__)


class ReadmeRenderer:
    """Renders README files for roles and collections using templates.

    Orchestrates the README generation process using specialized processors
    for each step: template loading, backup, rendering, validation, and writing.

    Attributes:
        backup_enabled: Whether to create backups before overwriting
        backup_manager: Handles file backup operations
        template_processor: Loads and manages templates
        markdown_processor: Validates and fixes markdown
        metadata_processor: Generates and injects metadata
        tag_processor: Manages Docsible tags
        content_merger: Merges new content with existing files
        file_writer: Writes final content to disk
    """

    def __init__(
        self,
        backup: bool = True,
        validate: bool = True,
        auto_fix: bool = False,
        strict_validation: bool = False,
    ):
        """Initialize ReadmeRenderer with specialized processors.

        Args:
            backup: Create backup files before overwriting (default: True)
            validate: Run markdown formatting validation (default: True)
            auto_fix: Automatically fix formatting issues (default: False)
            strict_validation: Fail on validation errors (default: False, warn only)

        Example:
            >>> renderer = ReadmeRenderer(backup=True, validate=True, auto_fix=True)
            >>> renderer.render_role(role_data, output_path)
        """
        # Initialize all processors
        self.backup_enabled = backup
        self.backup_manager = BackupManager()
        self.template_processor = TemplateProcessor()
        self.markdown_processor = MarkdownProcessor(validate, auto_fix, strict_validation)
        self.metadata_processor = MetadataProcessor(include_metadata=True)
        self.tag_processor = TagProcessor()
        self.content_merger = ContentMerger()
        self.file_writer = FileWriter()

    def render_role(
        self,
        role_info: dict[str, Any],
        output_path: Path,
        template_type: str = "standard_modular",
        custom_template_path: str | None = None,
        mermaid_code_per_file: dict[str, str] | None = None,
        sequence_diagram_high_level: str | None = None,
        sequence_diagram_detailed: str | None = None,
        state_diagram: str | None = None,
        integration_boundary_diagram: str | None = None,
        architecture_diagram: str | None = None,
        execution_phases: list[dict[str, Any]] | None = None,
        complexity_report: Any | None = None,
        include_complexity: bool | None = None,
        dependency_matrix: str | None = None,
        dependency_summary: dict[str, Any] | None = None,
        show_dependency_matrix: bool = False,
        no_vars: bool = False,
        no_tasks: bool = False,
        no_diagrams: bool = False,
        simplify_diagrams: bool = False,
        no_examples: bool = False,
        no_metadata: bool = False,
        no_handlers: bool = False,
        append: bool = False,
    ) -> None:
        """Render role README from template.

        Args:
            role_info: Role information dictionary
            output_path: Path where README will be written
            template_type: 'standard_modular' or 'hybrid' (default: 'standard_modular')
            custom_template_path: Optional custom template file path
            mermaid_code_per_file: Task flow graphs per file
            sequence_diagram_high_level: High-level sequence diagram
            sequence_diagram_detailed: Detailed sequence diagram
            no_vars: Skip variable documentation
            append: Append to existing README instead of replacing

        Example:
            >>> renderer = ReadmeRenderer()
            >>> renderer.render_role(
            ...     role_info={'name': 'my_role', ...},
            ...     output_path=Path('README.md')
            ... )
        """
        # Step 1: Backup existing file if requested
        if self.backup_enabled:
            self.backup_manager.create_backup(output_path)

        # Step 2: Load template
        template = self.template_processor.get_role_template(
            template_type=template_type, custom_path=custom_template_path
        )
        
        # Step 3: Render template
        new_content = template.render(
            role=role_info,
            mermaid_code_per_file=mermaid_code_per_file or {},
            sequence_diagram_high_level=sequence_diagram_high_level,
            sequence_diagram_detailed=sequence_diagram_detailed,
            state_diagram=state_diagram,
            integration_boundary_diagram=integration_boundary_diagram,
            architecture_diagram=architecture_diagram,
            execution_phases=execution_phases,
            complexity_report=complexity_report,
            include_complexity=include_complexity,
            dependency_matrix=dependency_matrix,
            dependency_summary=dependency_summary,
            show_dependency_matrix=show_dependency_matrix,
            no_vars=no_vars,
            no_tasks=no_tasks,
            no_diagrams=no_diagrams,
            simplify_diagrams=simplify_diagrams,
            no_examples=no_examples,
            no_metadata=no_metadata,
            no_handlers=no_handlers,
        )

        # Step 4: Add Docsible tags
        new_content = self.tag_processor.add_tags(new_content)

        # Step 5: Validate and fix markdown
        new_content = self.markdown_processor.process(new_content)

        # Step 6: Add metadata
        new_content = self.metadata_processor.add_metadata(new_content, output_path.parent)

        # Step 7: Merge with existing content
        final_content = self.content_merger.merge(output_path, new_content, append)

        # Step 8: Write file
        self.file_writer.write(output_path, final_content)

    def render_role_from_context(self, context: RenderContext, output_path: Path) -> None:
        """Render role README from RenderContext (simplified API).

        This is the preferred method for new code as it reduces the parameter
        count from 25+ to just 2 using a structured RenderContext object.

        Args:
            context: RenderContext containing all rendering configuration
            output_path: Path where README will be written

        Example:
            >>> from docsible.renderers.models import RenderContext
            >>> context = RenderContext(
            ...     role_info={'name': 'my_role'},
            ...     template_type='hybrid',
            ...     no_vars=False,
            ...     no_diagrams=False
            ... )
            >>> renderer = ReadmeRenderer()
            >>> renderer.render_role_from_context(context, Path('README.md'))
        """
        # Delegate to existing render_role with all parameters from context
        self.render_role(
            role_info=context.role_info,
            output_path=output_path,
            template_type=context.template_type,
            custom_template_path=context.custom_template_path,
            mermaid_code_per_file=context.mermaid_code_per_file,
            sequence_diagram_high_level=context.sequence_diagram_high_level,
            sequence_diagram_detailed=context.sequence_diagram_detailed,
            state_diagram=context.state_diagram,
            integration_boundary_diagram=context.integration_boundary_diagram,
            architecture_diagram=context.architecture_diagram,
            complexity_report=context.complexity_report,
            include_complexity=context.include_complexity,
            dependency_matrix=context.dependency_matrix,
            dependency_summary=context.dependency_summary,
            show_dependency_matrix=context.show_dependency_matrix,
            no_vars=context.no_vars,
            no_tasks=context.no_tasks,
            no_diagrams=context.no_diagrams,
            simplify_diagrams=context.simplify_diagrams,
            no_examples=context.no_examples,
            no_metadata=context.no_metadata,
            no_handlers=context.no_handlers,
            append=context.append,
        )

    def render_collection(
        self,
        collection_metadata: dict[str, Any],
        roles_info: list,
        output_path: Path,
        custom_template_path: str | None = None,
        no_vars: bool = False,
        no_tasks: bool = False,
        no_diagrams: bool = False,
        simplify_diagrams: bool = False,
        no_examples: bool = False,
        no_metadata: bool = False,
        no_handlers: bool = False,
        append: bool = False,
    ) -> None:
        """Render collection README from template.

        Args:
            collection_metadata: Collection metadata dictionary
            roles_info: List of role information dictionaries
            output_path: Path where README will be written
            custom_template_path: Optional custom template file path
            no_vars: Hide variable documentation
            no_tasks: Hide task lists and task details
            no_diagrams: Hide all Mermaid diagrams
            simplify_diagrams: Show only high-level diagrams
            no_examples: Hide example playbook sections
            no_metadata: Hide role metadata
            no_handlers: Hide handlers section
            append: Append to existing README instead of replacing

        Example:
            >>> renderer = ReadmeRenderer()
            >>> renderer.render_collection(
            ...     collection_metadata={'namespace': 'my', 'name': 'collection'},
            ...     roles_info=[...],
            ...     output_path=Path('README.md')
            ... )
        """
        # Step 1: Backup existing file if requested
        if self.backup_enabled:
            self.backup_manager.create_backup(output_path)

        # Step 2: Load template
        logger.debug(f"In renderer custom path, {custom_template_path}")
        template = self.template_processor.get_collection_template(custom_template_path)

        # Step 3: Render template
        data = {
            "collection": collection_metadata,
            "roles": roles_info,
            "no_vars": no_vars,
            "no_tasks": no_tasks,
            "no_diagrams": no_diagrams,
            "simplify_diagrams": simplify_diagrams,
            "no_examples": no_examples,
            "no_metadata": no_metadata,
            "no_handlers": no_handlers,
        }
        new_content = template.render(data)

        # Step 4: Add Docsible tags
        new_content = self.tag_processor.add_tags(new_content)

        # Step 5: Normalize excessive blank lines (same as role READMEs)
        new_content = self.markdown_processor.process(new_content)

        # Step 6: Merge with existing content
        final_content = self.content_merger.merge(output_path, new_content, append)

        # Step 7: Write file
        self.file_writer.write(output_path, final_content)
