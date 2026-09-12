"""Tests for task key extraction: blocks and include/import targets."""

from docsible.utils.special_tasks_keys import process_special_task_keys


def test_regular_task_has_no_include_target():
    result = process_special_task_keys({"name": "Install", "apt": {"name": "nginx"}})
    assert result == [
        {"name": "Install", "module": "apt", "type": "task", "when": None}
    ]
    assert "include_target" not in result[0]


def test_include_tasks_static_target_captured():
    result = process_special_task_keys({"include_tasks": "setup.yml"})
    assert result[0]["module"] == "include_tasks"
    assert result[0]["include_target"] == "setup.yml"


def test_fqcn_include_tasks_target_captured():
    result = process_special_task_keys(
        {"ansible.builtin.include_tasks": "configure.yml"}
    )
    assert result[0]["module"] == "ansible.builtin.include_tasks"
    assert result[0]["include_target"] == "configure.yml"


def test_fqcn_import_tasks_target_captured():
    result = process_special_task_keys({"ansible.builtin.import_tasks": "users.yml"})
    assert result[0]["module"] == "ansible.builtin.import_tasks"
    assert result[0]["include_target"] == "users.yml"


def test_legacy_bare_include_target_captured():
    result = process_special_task_keys({"include": "legacy.yml"})
    assert result[0]["module"] == "include"
    assert result[0]["include_target"] == "legacy.yml"


def test_include_dict_file_form_captured():
    result = process_special_task_keys(
        {"include_tasks": {"file": "nested.yml", "apply": {"tags": ["x"]}}}
    )
    assert result[0]["include_target"] == "nested.yml"


def test_templated_include_target_captured_as_is():
    result = process_special_task_keys(
        {"include_tasks": "{{ ansible_facts['os_family'] }}.yml"}
    )
    assert result[0]["include_target"] == "{{ ansible_facts['os_family'] }}.yml"


def test_include_target_pipes_escaped():
    result = process_special_task_keys({"include_tasks": "{{ item | upper }}.yml"})
    assert "|" not in result[0]["include_target"]
    assert "¦" in result[0]["include_target"]


def test_list_include_target_not_captured():
    result = process_special_task_keys({"include_tasks": ["a.yml", "b.yml"]})
    assert result[0]["module"] == "include_tasks"
    assert "include_target" not in result[0]


def test_include_vars_target_not_captured():
    result = process_special_task_keys({"include_vars": "Debian.yml"})
    assert result[0]["module"] == "include_vars"
    assert "include_target" not in result[0]


def test_include_role_target_captured():
    result = process_special_task_keys({"include_role": "common"})
    assert result[0]["module"] == "include_role"
    assert result[0]["include_target"] == "common"


def test_block_task_shape_unchanged():
    result = process_special_task_keys(
        {"name": "Handle failure", "block": [{"debug": {"msg": "try"}}], "rescue": []}
    )
    assert result[0]["module"] == "block"
    assert result[0]["type"] == "block"
    assert "include_target" not in result[0]
    assert result[1]["module"] == "debug"
    # An empty rescue list contributes no rescue entry
    assert len(result) == 2
