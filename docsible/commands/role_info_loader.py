"""Read-only assembly of Ansible role information."""

import logging
import os
from pathlib import Path
from typing import Any

import yaml

from docsible.diagrams.mermaid import generate_mermaid_playbook
from docsible.utils.git import get_repo_info
from docsible.utils.project_structure import ProjectStructure
from docsible.utils.special_tasks_keys import process_special_task_keys
from docsible.utils.yaml import (
    get_task_comments,
    get_task_line_numbers,
    get_task_line_ranges,
    load_yaml_files_from_dir_custom,
    load_yaml_generic,
)

logger = logging.getLogger(__name__)


class RoleInfoLoader:
    """Load role information without changing the role directory."""

    def __init__(self, project_structure: ProjectStructure | None = None):
        self.project_structure = project_structure

    def load(
        self,
        role_path: Path,
        *,
        playbook_content: str | None = None,
        generate_graph: bool = False,
        comments: bool = False,
        task_line: bool = False,
        belongs_to_collection: dict | None = None,
        repository_url: str | None = None,
        repo_type: str | None = None,
        repo_branch: str | None = None,
        read_docsible: bool = False,
    ) -> dict:
        """Load all information used to analyze or document a role.

        ``read_docsible`` reads an existing metadata file only. This loader never
        creates or updates ``.docsible``.
        """
        role_path = Path(role_path).resolve()
        project_structure = self.project_structure or ProjectStructure(str(role_path))
        role_name = role_path.name
        meta_path = project_structure.get_meta_file(role_path)
        if meta_path is None:
            logger.warning("No meta file found for role %s", role_name)
            meta_path = role_path / "meta" / "main.yml"

        repository_url, repo_type, repo_branch = self._repository_info(
            role_path, repository_url, repo_type, repo_branch
        )
        argument_specs_path = project_structure.get_argument_specs_file(role_path)
        docsible_path = role_path / ".docsible"

        meta_data: dict[str, Any] = {}
        if meta_path.exists():
            try:
                loaded_meta = load_yaml_generic(meta_path)
                if isinstance(loaded_meta, dict):
                    meta_data = loaded_meta
                elif loaded_meta is None:
                    logger.debug("Meta file %s is empty or invalid", meta_path)
                else:
                    logger.warning("Meta file %s does not contain a dictionary", meta_path)
            except Exception as exc:
                logger.warning("Failed to load meta file %s: %s", meta_path, exc)

        argument_specs_data = None
        if argument_specs_path and argument_specs_path.exists():
            try:
                argument_specs_data = load_yaml_generic(argument_specs_path)
            except Exception as exc:
                logger.warning("Failed to load argument specs file %s: %s", argument_specs_path, exc)

        docsible_data = None
        if read_docsible and docsible_path.exists():
            try:
                docsible_data = load_yaml_generic(docsible_path)
            except Exception as exc:
                logger.warning("Failed to load .docsible file %s: %s", docsible_path, exc)

        return {
            "name": role_name,
            "defaults": load_yaml_files_from_dir_custom(project_structure.get_defaults_dir(role_path))
            or [],
            "vars": load_yaml_files_from_dir_custom(project_structure.get_vars_dir(role_path)) or [],
            "tasks": self._tasks_info(project_structure, role_path, comments, task_line),
            "handlers": self._handlers_info(project_structure, role_path),
            "meta": meta_data,
            "playbook": self._playbook_info(playbook_content, role_name, generate_graph),
            "docsible": docsible_data,
            "belongs_to_collection": belongs_to_collection,
            "repository": repository_url,
            "repository_type": repo_type,
            "repository_branch": repo_branch,
            "argument_specs": argument_specs_data,
        }

    def _tasks_info(
        self, project_structure: ProjectStructure, role_path: Path, comments: bool, task_line: bool
    ) -> list[dict[str, Any]]:
        tasks_dir = project_structure.get_tasks_dir(role_path)
        if not tasks_dir.is_dir():
            return []

        tasks_list: list[dict[str, Any]] = []
        for dirpath, _, filenames in os.walk(str(tasks_dir)):
            for filename in filenames:
                if not any(filename.endswith(ext) for ext in project_structure.get_yaml_extensions()):
                    continue
                file_path = Path(dirpath) / filename
                try:
                    tasks_data = load_yaml_generic(file_path)
                except Exception as exc:
                    logger.warning("Failed to load tasks file %s: %s", file_path, exc)
                    continue
                if not tasks_data:
                    logger.debug("Tasks file %s is empty or invalid", file_path)
                    continue
                task_info: dict[str, Any] = {
                    "file": str(file_path.relative_to(tasks_dir)),
                    "tasks": [],
                    "mermaid": [],
                    "comments": get_task_comments(str(file_path)) if comments else [],
                    "lines": get_task_line_numbers(str(file_path)) if task_line else [],
                    "line_ranges": [],
                }
                try:
                    task_info["line_ranges"] = get_task_line_ranges(str(file_path))
                except Exception as exc:
                    logger.debug("Could not extract line ranges for %s: %s", file_path, exc)
                if isinstance(tasks_data, list):
                    for task in tasks_data:
                        if isinstance(task, dict) and task:
                            task_info["tasks"].extend(process_special_task_keys(task))
                            task_info["mermaid"].append(task)
                    tasks_list.append(task_info)
        return tasks_list

    def _handlers_info(self, project_structure: ProjectStructure, role_path: Path) -> list[dict]:
        handlers_dir = role_path / "handlers"
        if not handlers_dir.is_dir():
            return []

        handlers: list[dict] = []
        for dirpath, _, filenames in os.walk(str(handlers_dir)):
            for filename in filenames:
                if not any(filename.endswith(ext) for ext in project_structure.get_yaml_extensions()):
                    continue
                file_path = Path(dirpath) / filename
                try:
                    handler_data = load_yaml_generic(file_path)
                except Exception as exc:
                    logger.warning("Failed to load handlers file %s: %s", file_path, exc)
                    continue
                if not isinstance(handler_data, list):
                    if handler_data is not None:
                        logger.debug("Handlers file %s does not contain a list", file_path)
                    continue
                for handler in handler_data:
                    if not (isinstance(handler, dict) and "name" in handler):
                        logger.warning("Skipping handler without 'name:' field: %r", handler)
                        continue
                    excluded_keys = ["name", "notify", "when", "tags", "listen"]
                    handlers.append(
                        {
                            "name": handler.get("name", "Unnamed handler"),
                            "module": next(
                                (key for key in handler if key not in excluded_keys), "unknown"
                            ),
                            "listen": handler.get("listen", []),
                            "file": str(file_path.relative_to(handlers_dir)),
                        }
                    )
        return handlers

    def _playbook_info(
        self, playbook_content: str | None, role_name: str, generate_graph: bool
    ) -> dict:
        graph = None
        if playbook_content and generate_graph:
            try:
                graph = generate_mermaid_playbook(yaml.safe_load(playbook_content))
            except Exception as exc:
                logger.warning("Could not generate playbook graph: %s", exc)
        return {
            "content": playbook_content,
            "graph": graph,
            "dependencies": self._playbook_dependencies(playbook_content, role_name),
        }

    def _playbook_dependencies(self, playbook_content: str | None, role_name: str) -> list[str]:
        if not playbook_content:
            return []
        try:
            playbook = yaml.safe_load(playbook_content)
            if not isinstance(playbook, list):
                return []
            dependencies: set[str] = set()
            for play in playbook:
                if not isinstance(play, dict):
                    continue
                for role in play.get("roles", []):
                    self._add_role_dependency(dependencies, role, role_name)
                for section in ["pre_tasks", "tasks", "post_tasks"]:
                    for task in play.get(section, []):
                        if isinstance(task, dict):
                            for action in ["include_role", "import_role"]:
                                if action in task:
                                    self._add_role_dependency(dependencies, task[action], role_name)
            return sorted(dependencies)
        except Exception as exc:
            logger.warning("Could not extract playbook dependencies: %s", exc)
            return []

    @staticmethod
    def _add_role_dependency(dependencies: set[str], role_spec: Any, role_name: str) -> None:
        if isinstance(role_spec, str):
            dependency = role_spec
        elif isinstance(role_spec, dict):
            dependency = str(role_spec.get("role") or role_spec.get("name") or "")
        else:
            return
        if dependency and dependency != role_name:
            dependencies.add(dependency)

    @staticmethod
    def _repository_info(
        role_path: Path, repository_url: str | None, repo_type: str | None, repo_branch: str | None
    ) -> tuple[str | None, str | None, str | None]:
        if repository_url != "detect":
            return repository_url, repo_type, repo_branch
        try:
            git_info = get_repo_info(str(role_path)) or {}
            return (
                git_info.get("repository"),
                repo_type or git_info.get("repository_type"),
                repo_branch or git_info.get("branch", "main"),
            )
        except Exception as exc:
            logger.warning("Could not get Git info: %s", exc)
            return None, repo_type, repo_branch
