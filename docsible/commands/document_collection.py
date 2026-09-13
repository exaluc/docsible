"""Command for documenting Ansible collections."""

import logging
import os
from pathlib import Path

import click
import yaml

from docsible.commands.document_role.role_analysis import analyze_role, render_analyzed_role
from docsible.commands.role_info_loader import RoleInfoLoader
from docsible.exceptions import CollectionNotFoundError
from docsible.renderers.readme_renderer import ReadmeRenderer
from docsible.utils.git import get_repo_info
from docsible.utils.project_structure import ProjectStructure

logger = logging.getLogger(__name__)


def document_collection_roles(
    collection_path: str,
    playbook: str | None,
    graph: bool,
    no_backup: bool,
    no_docsible: bool,
    comments: bool,
    task_line: bool,
    md_collection_template: str | None,
    md_role_template: str | None,
    hybrid: bool,
    no_vars: bool,
    no_tasks: bool,
    no_diagrams: bool,
    simplify_diagrams: bool,
    no_examples: bool,
    no_metadata: bool,
    no_handlers: bool,
    minimal: bool,
    append: bool,
    output: str,
    repository_url: str,
    repo_type: str,
    repo_branch: str,
    dry_run: bool = False,
) -> None:
    """Document all roles in an Ansible collection.

    Extracts metadata from galaxy.yml/yaml and generates documentation
    for the collection and all roles within it.

    Args:
        collection_path: Path to collection directory
        playbook: Path to playbook file (relative to each role), optional
        graph: Generate Mermaid graphs
        no_backup: Skip backup creation
        no_docsible: Skip .docsible file handling
        comments: Extract task comments
        task_line: Extract task line numbers
        md_collection_template: Custom collection template path, optional
        md_role_template: Custom role template path, optional
        hybrid: Use hybrid template for roles
        no_vars: Hide variable documentation
        no_tasks: Hide task lists and task details
        no_diagrams: Hide all Mermaid diagrams
        simplify_diagrams: Show only high-level diagrams
        no_examples: Hide example playbook sections
        no_metadata: Hide role metadata
        no_handlers: Hide handlers section
        minimal: Generate minimal documentation
        append: Append to existing README
        output: Output file name
        repository_url: Repository URL
        repo_type: Repository type (github, gitlab, gitea)
        repo_branch: Repository branch name
        dry_run: Print the collection documentation plan without writing files
    """

    collection_path_obj = Path(collection_path)
    if not collection_path_obj.exists():
        raise CollectionNotFoundError(f"Collection directory does not exist: {collection_path}")

    if not collection_path_obj.is_dir():
        raise CollectionNotFoundError(f"Path is not a directory: {collection_path}")

    # Initialize project structure
    project_structure = ProjectStructure(collection_path)

    # Get repository info
    try:
        git_info = get_repo_info(collection_path) or {}
        repository_url = git_info.get("repository") or repository_url
        repo_branch = repo_branch or git_info.get("branch", "main")
        repo_type = repo_type or str(git_info.get("repository_type") or "github")
    except Exception as e:
        logger.warning(f"Could not get Git info: {e}")
        repository_url = repository_url or ""
        repo_branch = repo_branch or "main"
        repo_type = repo_type or "github"

    # Find all collection markers (galaxy.yml/yaml)
    collection_markers = project_structure.find_collection_markers()

    if not collection_markers:
        logger.warning(f"No collection marker files (galaxy.yml/yaml) found in {collection_path}")
        return

    if dry_run:
        role_count = sum(
            1
            for marker in collection_markers
            for role_path in ProjectStructure(str(marker.parent)).get_roles_dir().iterdir()
            if role_path.is_dir()
        )
        click.echo(f"Dry-run: would document {role_count} role(s) in {collection_path}")
        return

    # Process each collection found
    for galaxy_path in collection_markers:
        collection_root = galaxy_path.parent

        # Load collection metadata
        with open(galaxy_path, encoding="utf-8") as f:
            collection_metadata = yaml.safe_load(f)

        # Determine README path
        if output == "README.md":
            readme_path = collection_root / collection_metadata.get("readme", output)
        else:
            readme_path = collection_root / output

        # Add repository info to metadata
        collection_metadata["repository"] = repository_url
        collection_metadata["repository_type"] = repo_type
        collection_metadata["repository_branch"] = repo_branch

        # Find and document all roles
        collection_structure = ProjectStructure(str(collection_root))
        roles_dir = collection_structure.get_roles_dir()

        roles_info = []
        if roles_dir.exists() and roles_dir.is_dir():
            for role_name in os.listdir(str(roles_dir)):
                role_path = roles_dir / role_name

                if not role_path.is_dir():
                    continue

                # Load playbook content if specified
                playbook_content = None
                if playbook:
                    role_playbook_path = role_path / playbook
                    try:
                        with open(role_playbook_path, encoding="utf-8") as f:
                            playbook_content = f.read()
                    except FileNotFoundError:
                        logger.warning(f"Playbook not found for {role_name}: {role_playbook_path}")
                    except Exception as e:
                        logger.error(f"Error loading playbook for {role_name}: {e}")

                # Build role info
                role_info = RoleInfoLoader().load(
                    role_path,
                    playbook_content=playbook_content,
                    generate_graph=graph,
                    comments=comments,
                    task_line=task_line,
                    belongs_to_collection=collection_metadata,
                    repository_url=repository_url,
                    repo_type=repo_type,
                    repo_branch=repo_branch,
                    read_docsible=not no_docsible,
                )

                # Generate role README
                if not no_docsible:
                    from docsible.renderers.tag_manager import manage_docsible_file_keys

                    role_info["docsible"] = manage_docsible_file_keys(role_path / ".docsible")

                # Analyze complexity, execution graph, and recommendations —
                # identical to standalone `document role` and `scan collection`
                # (previously this was skipped entirely for collection roles).
                analysis = analyze_role(role_info, role_path, min_confidence=0.7)

                role_readme_path = role_path / output
                template_type = "hybrid" if hybrid else "standard_modular"

                render_analyzed_role(
                    role_info=role_info,
                    role_path=role_path,
                    analysis=analysis,
                    output_path=role_readme_path,
                    template_type=template_type,
                    custom_template_path=md_role_template,
                    generate_graph=graph,
                    minimal=minimal,
                    simplify_diagrams=simplify_diagrams,
                    no_vars=no_vars,
                    no_tasks=no_tasks,
                    no_diagrams=no_diagrams,
                    no_examples=no_examples,
                    no_metadata=no_metadata,
                    no_handlers=no_handlers,
                    include_complexity=hybrid,
                    append=append,
                    backup=not no_backup,
                    playbook_content=playbook_content,
                )

                warning_count = sum(
                    1 for r in analysis.recommendations if r.severity.value == "warning"
                )
                critical_count = sum(
                    1 for r in analysis.recommendations if r.severity.value == "critical"
                )
                logger.info(
                    f"✓ Documented role: {role_name} "
                    f"({analysis.complexity_report.category.value}, "
                    f"{critical_count} critical, {warning_count} warning)"
                )

                # Summary fields for the collection-level Role Index (a human
                # scanning the collection README needs to see, at a glance,
                # which roles are complex/risky before opening any of them).
                category = analysis.complexity_report.category.value
                role_info["complexity_category"] = category
                role_info["complexity_rank"] = {
                    "simple": 0,
                    "medium": 1,
                    "complex": 2,
                    "enterprise": 3,
                }.get(category, 0)
                role_info["complexity_badge"] = {
                    "simple": "🟢 SIMPLE",
                    "medium": "🟡 MEDIUM",
                    "complex": "🟠 COMPLEX",
                    "enterprise": "🔴 ENTERPRISE",
                }.get(category, category.upper())
                role_info["complexity_task_count"] = analysis.complexity_report.metrics.total_tasks
                role_info["complexity_critical_count"] = critical_count
                role_info["complexity_warning_count"] = warning_count
                role_info["complexity_top_finding"] = (
                    analysis.recommendations[0].message if analysis.recommendations else None
                )

                roles_info.append(role_info)

        # Generate collection README
        renderer = ReadmeRenderer(backup=not no_backup)
        renderer.render_collection(
            collection_metadata=collection_metadata,
            roles_info=roles_info,
            output_path=readme_path,
            custom_template_path=md_collection_template,
            no_vars=no_vars,
            no_tasks=no_tasks,
            no_diagrams=no_diagrams,
            simplify_diagrams=simplify_diagrams,
            no_examples=no_examples,
            no_metadata=no_metadata,
            no_handlers=no_handlers,
            append=append,
        )

        logger.info(f"✓ Collection documentation generated: {readme_path}")
