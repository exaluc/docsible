from pathlib import Path

from docsible.commands.document_role.models import ProcessingConfig, RepositoryConfig
from docsible.commands.role_info_loader import RoleInfoLoader
from docsible.utils.project_structure import ProjectStructure


class RoleInfoBuilder:
    """Compatibility facade for :class:`RoleInfoLoader`."""

    def __init__(self, project_structure: ProjectStructure | None = None):
        """Initialize RoleInfoBuilder.

        Args:
            project_structure: Optional ProjectStructure instance.
                If None, will be created from role_path during build().
        """
        self.project_structure = project_structure
        self.loader = RoleInfoLoader(project_structure)

    def build(
        self,
        role_path: Path,
        playbook_content: str | None,
        processing: ProcessingConfig,
        repository: RepositoryConfig,
        belongs_to_collection: dict | None = None,
        generate_graph: bool = False,
    ) -> dict:
        """Build complete role information dictionary.

        Args:
            role_path: Path to role directory
            playbook_content: Optional playbook YAML content
            processing: Processing configuration (comments, task_line, etc.)
            repository: Repository configuration (url, type, branch)
            belongs_to_collection: Optional collection info if part of collection

        Returns:
            Dictionary with complete role information including:
            - name, defaults, vars, tasks, handlers, meta
            - playbook info (content, graph, dependencies)
            - repository info, argument specs, docsible metadata
        """
        if self.project_structure is None:
            self.project_structure = ProjectStructure(str(role_path))
            self.loader = RoleInfoLoader(self.project_structure)
        return self.loader.load(
            role_path,
            playbook_content=playbook_content,
            generate_graph=generate_graph,
            comments=processing.comments,
            task_line=processing.task_line,
            belongs_to_collection=belongs_to_collection,
            repository_url=repository.repository_url,
            repo_type=repository.repo_type,
            repo_branch=repository.repo_branch,
            read_docsible=not processing.no_docsible,
        )
