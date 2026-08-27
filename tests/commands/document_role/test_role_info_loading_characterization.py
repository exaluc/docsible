"""Characterize role-information assembly before consolidating its loaders."""

from pathlib import Path

import pytest

from docsible.commands.document_role.builders.role_info_builder import RoleInfoBuilder
from docsible.commands.document_role.core_orchestrated import build_role_info
from docsible.commands.document_role.models import ProcessingConfig, RepositoryConfig

FIXTURES = Path(__file__).parents[2] / "fixtures"


def _legacy_role_info(
    role_path: Path,
    *,
    playbook_content: str | None = None,
    generate_graph: bool = False,
    comments: bool = False,
    task_line: bool = False,
    belongs_to_collection: dict | None = None,
    repository: RepositoryConfig | None = None,
) -> dict:
    repository = repository or RepositoryConfig()
    return build_role_info(
        role_path=role_path,
        playbook_content=playbook_content,
        generate_graph=generate_graph,
        no_docsible=True,
        comments=comments,
        task_line=task_line,
        belongs_to_collection=belongs_to_collection,
        repository_url=repository.repository_url,
        repo_type=repository.repo_type,
        repo_branch=repository.repo_branch,
    )


def _builder_role_info(
    role_path: Path,
    *,
    playbook_content: str | None = None,
    comments: bool = False,
    task_line: bool = False,
    belongs_to_collection: dict | None = None,
    repository: RepositoryConfig | None = None,
) -> dict:
    return RoleInfoBuilder().build(
        role_path=role_path,
        playbook_content=playbook_content,
        processing=ProcessingConfig(
            no_docsible=True,
            comments=comments,
            task_line=task_line,
        ),
        repository=repository or RepositoryConfig(),
        belongs_to_collection=belongs_to_collection,
    )


@pytest.mark.parametrize(
    ("fixture_name", "task_files", "task_count"),
    [("simple_role", 1, 3), ("complex_role", 4, 13)],
)
def test_read_only_assemblers_match_for_existing_role_fixtures(
    fixture_name: str, task_files: int, task_count: int
) -> None:
    """Simple and complex roles retain the same assembled data during migration."""
    role_path = FIXTURES / fixture_name

    legacy = _legacy_role_info(role_path)
    builder = _builder_role_info(role_path)

    assert builder == legacy
    assert len(builder["tasks"]) == task_files
    assert sum(len(task_file["tasks"]) for task_file in builder["tasks"]) == task_count


def test_read_only_assemblers_match_for_playbook_repository_and_collection_data() -> None:
    """Playbook, repository, and collection fields are part of the loader contract."""
    role_path = FIXTURES / "simple_role"
    playbook_content = """
- hosts: all
  roles:
    - simple_role
    - role: role_from_roles
  pre_tasks:
    - import_role:
        name: role_from_pre_tasks
  tasks:
    - include_role:
        name: role_from_tasks
"""
    repository = RepositoryConfig(
        repository_url="https://example.test/acme/roles",
        repo_type="gitlab",
        repo_branch="release",
    )
    collection = {"namespace": "acme", "name": "platform"}

    legacy = _legacy_role_info(
        role_path,
        playbook_content=playbook_content,
        generate_graph=True,
        belongs_to_collection=collection,
        repository=repository,
    )
    builder = _builder_role_info(
        role_path,
        playbook_content=playbook_content,
        belongs_to_collection=collection,
        repository=repository,
    )

    assert builder == legacy
    assert builder["playbook"]["content"] == playbook_content
    assert builder["playbook"]["dependencies"] == [
        "role_from_pre_tasks",
        "role_from_roles",
        "role_from_tasks",
    ]
    assert builder["playbook"]["graph"] is not None
    assert builder["repository"] == repository.repository_url
    assert builder["repository_type"] == repository.repo_type
    assert builder["repository_branch"] == repository.repo_branch
    assert builder["belongs_to_collection"] == collection


def test_read_only_assemblers_match_comments_and_task_lines() -> None:
    """Task annotations are preserved when their optional extraction is enabled."""
    role_path = FIXTURES / "annotated_role"

    legacy = _legacy_role_info(role_path, comments=True, task_line=True)
    builder = _builder_role_info(role_path, comments=True, task_line=True)

    assert builder == legacy
    task_file = builder["tasks"][0]
    assert len(task_file["comments"]) == 3
    assert task_file["lines"] == {
        "Install service package": 3,
        "Configure service": 9,
        "Start service": 17,
    }
    assert task_file["line_ranges"]


def test_read_only_assemblers_do_not_create_docsible(tmp_path: Path) -> None:
    """Analysis callers can load a role without creating metadata files."""
    role_path = tmp_path / "read_only_role"
    (role_path / "meta").mkdir(parents=True)
    (role_path / "tasks").mkdir()
    (role_path / "meta" / "main.yml").write_text("---\ngalaxy_info: {}\n", encoding="utf-8")
    (role_path / "tasks" / "main.yml").write_text(
        "---\n- name: Read-only task\n  ansible.builtin.debug:\n", encoding="utf-8"
    )

    legacy = _legacy_role_info(role_path)
    builder = _builder_role_info(role_path)

    assert builder == legacy
    assert builder["docsible"] is None
    assert not (role_path / ".docsible").exists()
