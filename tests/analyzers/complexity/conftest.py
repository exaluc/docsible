"""Shared fixtures for complexity analyzer tests."""

import pytest


@pytest.fixture
def simple_role_info():
    """Create role info for a simple role (5 tasks)."""
    return {
        "name": "simple_role",
        "tasks": [
            {
                "file": "main.yml",
                "tasks": [
                    {"name": "Install package", "module": "apt", "when": None},
                    {"name": "Start service", "module": "service"},
                    {"name": "Copy config", "module": "copy"},
                    {"name": "Set fact", "module": "set_fact"},
                    {"name": "Debug output", "module": "debug"},
                ],
            }
        ],
        "handlers": [],
        "meta": {"dependencies": []},
    }


@pytest.fixture
def medium_role_info():
    """Create role info for a medium role (15 tasks)."""
    return {
        "name": "medium_role",
        "tasks": [
            {
                "file": "main.yml",
                "tasks": [
                    {
                        "name": f"Task {i}",
                        "module": "debug",
                        "when": "i % 3 == 0" if i % 3 == 0 else None,
                    }
                    for i in range(10)
                ],
            },
            {
                "file": "setup.yml",
                "tasks": [
                    {"name": f"Setup task {i}", "module": "command"} for i in range(5)
                ],
            },
        ],
        "handlers": [
            {"name": "restart nginx", "module": "service"},
            {"name": "reload nginx", "module": "service"},
        ],
        "meta": {
            "dependencies": [
                {"role": "common"},
                {"role": "firewall"},
            ]
        },
    }


@pytest.fixture
def complex_role_info():
    """Create role info for a complex role (30 tasks)."""
    return {
        "name": "complex_role",
        "tasks": [
            {
                "file": "main.yml",
                "tasks": [
                    {
                        "name": f"Main task {i}",
                        "module": "debug",
                        "when": "i % 2 == 0" if i % 2 == 0 else None,
                    }
                    for i in range(15)
                ],
            },
            {
                "file": "database.yml",
                "tasks": [
                    {
                        "name": "Create database",
                        "module": "postgresql_db",
                        "username": "admin",
                    },
                    {
                        "name": "Create user",
                        "module": "postgresql_user",
                        "password": "secret",
                    },
                    {"name": "Grant privileges", "module": "postgresql_privs"},
                ],
            },
            {
                "file": "api.yml",
                "tasks": [
                    {"name": "Check API", "module": "uri", "url_username": "api_user"},
                    {"name": "Fetch data", "module": "get_url", "token": "abc123"},
                    {"name": "Process response", "module": "debug"},
                ],
            },
            {
                "file": "vault.yml",
                "tasks": [
                    {
                        "name": "Get secret",
                        "module": "hashi_vault",
                        "vault_token": "token123",
                    },
                    {
                        "name": "Set secret",
                        "module": "community.hashi_vault.vault_write",
                    },
                ],
            },
            {
                "file": "orchestration.yml",
                "tasks": [
                    {
                        "name": "Include common tasks",
                        "module": "include_tasks",
                        "file": "common.yml",
                    },
                    {"name": "Import role", "module": "import_role", "role": "base"},
                    {
                        "name": "Include another role",
                        "module": "ansible.builtin.include_role",
                        "role": "utils",
                    },
                    {
                        "name": "Import more tasks",
                        "module": "ansible.builtin.import_tasks",
                        "file": "cleanup.yml",
                    },
                    {"name": "Regular task", "module": "debug"},
                    {"name": "Another task", "module": "copy"},
                    {"name": "Final task", "module": "template"},
                ],
                "mermaid": [
                    {"name": "Include common tasks", "include_tasks": "common.yml"},
                    {"name": "Import role", "import_role": {"name": "base"}},
                    {"name": "Include another role", "ansible.builtin.include_role": {"name": "utils"}},
                    {"name": "Import more tasks", "ansible.builtin.import_tasks": "cleanup.yml"},
                    {"name": "Regular task", "debug": {}},
                    {"name": "Another task", "copy": {}},
                    {"name": "Final task", "template": {}},
                ],
            },
        ],
        "handlers": [
            {"name": "restart app", "module": "systemd"},
            {"name": "reload config", "module": "service"},
            {"name": "clear cache", "module": "command"},
        ],
        "meta": {
            "dependencies": [
                {"role": "base"},
                {"role": "security"},
                {"role": "monitoring"},
            ]
        },
    }
