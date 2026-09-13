"""Regression tests for `docsible.commands.document_collection`.

These cover three defects found during the first full evaluation against a
real Ansible collection (prometheus-community/ansible):

1. `document role --collection ... --dry-run` was not read-only: it created
   backup files and could still crash before the actual dry-run short-circuit
   existed.
2. `meta/argument_specs.yml` files using Ansible's `!unsafe` YAML tag failed
   to load (`could not determine a constructor for the tag '!unsafe'`).
3. The collection-level README template referenced `role.belongs_to_collection`
   in a macro where `role` was never in scope, raising
   `jinja2.exceptions.UndefinedError: 'role' is undefined` for any collection
   with a detectable repository URL. This also produced malformed
   argument-spec tables (blank lines between rows) once the template gained
   an argument-specs section.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from docsible.commands.document_collection import document_collection_roles
from docsible.utils.yaml.loader import load_yaml_generic

FIXTURES = Path(__file__).parent.parent / "fixtures"
MINIMAL_COLLECTION = FIXTURES / "minimal_collection"
MULTI_ROLE_COLLECTION = FIXTURES / "multi_role_collection"


def _copy_collection(src: Path, dest: Path) -> Path:
    shutil.copytree(src, dest)
    return dest


def _document(
    collection_path: Path,
    *,
    dry_run: bool = False,
    repository_url: str = "",
    repo_type: str = "",
    repo_branch: str = "",
) -> None:
    document_collection_roles(
        collection_path=str(collection_path),
        playbook=None,
        graph=False,
        no_backup=True,
        no_docsible=True,
        comments=False,
        task_line=False,
        md_collection_template=None,
        md_role_template=None,
        hybrid=False,
        no_vars=False,
        no_tasks=False,
        no_diagrams=True,
        simplify_diagrams=False,
        no_examples=False,
        no_metadata=False,
        no_handlers=False,
        minimal=False,
        append=False,
        output="README.md",
        repository_url=repository_url,
        repo_type=repo_type,
        repo_branch=repo_branch,
        dry_run=dry_run,
    )


class TestCollectionDryRun:
    def test_dry_run_does_not_write_any_files(self, tmp_path, capsys):
        collection = _copy_collection(MULTI_ROLE_COLLECTION, tmp_path / "collection")
        before = sorted(p.relative_to(collection) for p in collection.rglob("*") if p.is_file())

        _document(collection, dry_run=True)

        after = sorted(p.relative_to(collection) for p in collection.rglob("*") if p.is_file())
        assert before == after, "dry-run must not create, modify, or remove any files"

        captured = capsys.readouterr()
        assert "Dry-run" in captured.out
        assert "3 role(s)" in captured.out  # cache_role, db_role, proxy_role

    def test_dry_run_reports_role_count_for_single_role_collection(self, tmp_path, capsys):
        collection = _copy_collection(MINIMAL_COLLECTION, tmp_path / "collection")

        _document(collection, dry_run=True)

        captured = capsys.readouterr()
        assert "1 role(s)" in captured.out


class TestUnsafeYamlTag:
    def test_load_yaml_generic_handles_unsafe_scalar(self, tmp_path):
        yaml_file = tmp_path / "argument_specs.yml"
        yaml_file.write_text(
            "argument_specs:\n"
            "  main:\n"
            "    options:\n"
            "      my_var:\n"
            "        type: str\n"
            "        default: !unsafe 'plain value with {{ jinja }}'\n"
        )

        data = load_yaml_generic(yaml_file)

        assert data is not None
        default = data["argument_specs"]["main"]["options"]["my_var"]["default"]
        assert default == "plain value with {{ jinja }}"

    def test_collection_document_survives_unsafe_tagged_argument_specs(self, tmp_path):
        collection = _copy_collection(MINIMAL_COLLECTION, tmp_path / "collection")
        meta_dir = collection / "roles" / "web_role" / "meta"
        meta_dir.mkdir(parents=True, exist_ok=True)
        (meta_dir / "argument_specs.yml").write_text(
            "argument_specs:\n"
            "  main:\n"
            "    short_description: Web role\n"
            "    options:\n"
            "      web_port:\n"
            "        type: int\n"
            "        default: !unsafe 80\n"
        )

        # Must not raise.
        _document(collection, dry_run=False)

        readme = (collection / "roles" / "web_role" / "README.md").read_text()
        assert "web_port" in readme


class TestArgumentSpecTableRendering:
    def test_argument_spec_table_has_no_blank_lines_between_rows(self, tmp_path):
        collection = _copy_collection(MINIMAL_COLLECTION, tmp_path / "collection")
        meta_dir = collection / "roles" / "web_role" / "meta"
        meta_dir.mkdir(parents=True, exist_ok=True)
        (meta_dir / "argument_specs.yml").write_text(
            "argument_specs:\n"
            "  main:\n"
            "    short_description: Web role\n"
            "    options:\n"
            "      web_port:\n"
            "        type: int\n"
            "        default: 80\n"
            "        description: Port to listen on\n"
            "      web_user:\n"
            "        type: str\n"
            "        default: www-data\n"
            "        description: User to run as\n"
        )

        _document(collection, dry_run=False)

        readme = (collection / "roles" / "web_role" / "README.md").read_text()
        lines = readme.splitlines()
        header_idx = next(i for i, line in enumerate(lines) if line.startswith("| Parameter"))
        separator_idx = header_idx + 1
        assert lines[separator_idx].startswith("|-")

        first_row = lines[separator_idx + 1]
        second_row = lines[separator_idx + 2]
        # No blank line was inserted between the separator and the first row,
        # or between consecutive rows.
        assert first_row.strip() != ""
        assert first_row.startswith("| `web_")
        assert second_row.startswith("| `web_")


class TestCollectionReadmeGeneration:
    def test_collection_readme_does_not_raise_undefined_error(self, tmp_path):
        collection = _copy_collection(MULTI_ROLE_COLLECTION, tmp_path / "collection")

        # A truthy repository_url is required to exercise the buggy
        # render_repo_link() path (it short-circuits to a relative link
        # when no repository is known).
        _document(
            collection,
            dry_run=False,
            repository_url="https://github.com/example/repo",
            repo_type="github",
            repo_branch="main",
        )

        collection_readme = (collection / "README.md").read_text()
        assert "roles/cache_role" in collection_readme
        assert "roles/db_role" in collection_readme
        assert "roles/proxy_role" in collection_readme

    def test_collection_readme_has_no_excessive_blank_lines(self, tmp_path):
        """Regression test: collection templates previously left runs of many
        blank lines between roles, list items, and argument-spec entries,
        making generated collection READMEs unreadable. render_collection
        must apply the same blank-line normalization as render_role.
        """
        collection = _copy_collection(MULTI_ROLE_COLLECTION, tmp_path / "collection")

        _document(collection, dry_run=False)

        readme = (collection / "README.md").read_text()
        blank_run = 0
        max_blank_run = 0
        for line in readme.splitlines():
            if line.strip() == "":
                blank_run += 1
                max_blank_run = max(max_blank_run, blank_run)
            else:
                blank_run = 0

        assert max_blank_run <= 2, (
            f"found a run of {max_blank_run} consecutive blank lines in the "
            "generated collection README"
        )
