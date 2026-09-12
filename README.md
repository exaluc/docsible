# Docsible

## About

Docsible is a command-line interface (CLI) written in Python that automates the documentation of Ansible roles and collections. It generates a Markdown-formatted README file for a role or collection by scanning the Ansible YAML files.

## Fork and Attribution

This is an independently maintained fork of [Docsible](https://github.com/docsible/docsible), maintained by [Jier Nzuanzu](https://github.com/jier). The original project and its authors, including Lucian BLETAN, retain attribution for upstream work.

Fork-specific work focuses on modularization, intent-based CLI commands, presets, suppression rules, caching, analysis, and CI-oriented output. See the [upstream repository](https://github.com/docsible/docsible) for the original project.

Project home: https://github.com/jier/docsible

## Table of Contents

- [Features](#features)
- [Fork and Attribution](#fork-and-attribution)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [CI/CD Integration](#cicd-integration)
- [Command Reference](#command-reference)
  - [docsible init](#docsible-init)
  - [docsible document role](#docsible-document-role)
  - [docsible analyze role](#docsible-analyze-role)
  - [docsible scan collection](#docsible-scan-collection)
  - [docsible validate role](#docsible-validate-role)
  - [docsible suppress](#docsible-suppress)
  - [docsible guide](#docsible-guide)
  - [docsible role (legacy)](#docsible-role-legacy)
- [Presets](#presets)
- [Suppression System](#suppression-system)
- [Hybrid Template](#hybrid-template)
- [Data Sources](#data-sources)
- [Comment Tags](#comment-tags)
- [Prerequisites](#prerequisites)
- [Contributing](#contributing)
- [License](#license)

## Features

- Generates a README in Markdown format
- Scans and includes default variables and role-specific variables
- Parses tasks, including special Ansible task types like `block` and `rescue`
- Optionally includes playbook content in the README
- CLI-based, easy to integrate into a CI/CD pipeline
- Provides a templating feature to customize output
- Supports multiple YAML files within `tasks`, `defaults`, `vars` directories
- Includes metadata like author and license from `meta/main.[yml/yaml]`
- Generates a well-structured table for default and role-specific variables
- Support for encrypted Ansible Vault variables
- Flexible project structure support (AWX, monorepos, custom directories)
- Auto-detection of various Ansible project layouts
- Optional `.docsible/config.yml` configuration for custom structures and presets
- Comment tag flexibility (supports both `-` and `_` separators)
- Intelligent caching system (4-100x faster on repeated runs)
- Modular codebase with improved maintainability
- Smart Defaults Engine — auto-adjusts documentation based on role complexity
- Severity-based output (CRITICAL / WARNING / INFO levels)
- Positive output framing — actionable suggestions instead of bare warnings
- Progressive help — brief `--help` by default, with `--help-full` for all options
- Preset system — four built-in presets covering personal, team, enterprise, and consulting use cases
- Suppression system — silence false-positive recommendations with audit trail and optional expiry
- Interactive setup wizard (`docsible init`) with optional CI/CD workflow generation

## Installation

Create a virtual environment (recommended):

```bash
python3 -m venv docsible-env
source docsible-env/bin/activate
```

Install this fork directly from GitHub:

```bash
pip install git+https://github.com/jier/docsible.git
```

## Quick Start

```bash
# Step 1 — run the interactive wizard (picks a preset, optionally generates CI/CD config)
docsible init

# Step 2 — generate documentation
docsible document role . --preset=team

# Step 3 — just analyze without writing files
docsible analyze role --role /path/to/role

# Step 4 — validate markdown without writing files
docsible validate role --role /path/to/role
```

## CI/CD Integration

Docsible integrates with CI/CD pipelines using the `--fail-on` flag to exit with a non-zero code when documentation findings exceed a threshold.

### Quick Start

```bash
# Fail the pipeline if CRITICAL findings exist (recommended default)
docsible validate role --role . --fail-on critical

# Fail the pipeline if WARNING or CRITICAL findings exist (team standard)
docsible validate role --role . --fail-on warning

# Machine-readable output for downstream tools
docsible analyze role --role . --output-format json

# Gate an entire collection — exit 1 if any role has WARNING or CRITICAL findings
docsible scan collection . --fail-on warning --output-format json
```

### `--fail-on` levels

| Level | Exit 1 when... |
|---|---|
| `none` | Never (default) |
| `info` | Any finding exists |
| `warning` | WARNING or CRITICAL findings exist |
| `critical` | CRITICAL findings exist |

### `--output-format json`

Use `--output-format json` with `docsible analyze role` for machine-readable output:

```bash
docsible analyze role --role . --output-format json
```

Output schema:

```json
{
  "role": "my-role",
  "findings": [
    { "severity": "WARNING", "message": "No example playbook found", "category": "documentation" }
  ],
  "summary": { "total": 3, "critical": 0, "warning": 2, "info": 1 },
  "truncated": false
}
```

### Ready-to-use CI examples

See [`examples/ci_pipeline/`](examples/ci_pipeline/) for complete, ready-to-use configurations:

- **GitHub Actions** — validate on PRs, generate docs on main
- **GitLab CI** — two-stage test/deploy pipeline
- **Azure DevOps** — two-stage pipeline: validate then generate
- **pre-commit** — local hook before every commit

Commit `.docsible/config.yml` to your repository so all team members and CI runners share the same preset and `fail_on` threshold without passing flags every time. See [`examples/team-config/`](examples/team-config/) for a sample team config.

---

## Command Reference

### docsible init

Runs a 3-step interactive wizard to configure Docsible for a project. Creates `.docsible/config.yml` and, optionally, a CI/CD workflow file.

```bash
# Interactive wizard
docsible init

# Non-interactive — apply a preset directly
docsible init --preset=team

# Target a specific directory
docsible init --path /path/to/project

# Overwrite an existing config
docsible init --force
```

Wizard steps:

1. **Use case** — choose personal / team / enterprise / consulting
2. **Smart defaults** — enable auto-adjustment based on role complexity
3. **CI/CD integration** — optionally generate a workflow file for GitHub Actions, GitLab CI, or Azure DevOps

### docsible document role

Generate documentation for an Ansible role. Supports all flags from the legacy `docsible role` command, plus `--preset`.

```bash
# Document the role in the current directory
docsible document role .

# Specify an explicit path
docsible document role --role /path/to/role

# Apply a preset
docsible document role --role /path/to/role --preset=enterprise

# Include Mermaid diagrams and inline task comments
docsible document role --role ./my-role --graph --comments

# Preview without writing any files
docsible document role --role ./my-role --dry-run

# Document a collection
docsible document role --collection ./my-collection --graph

# Include a playbook in the output
docsible document role --role ./my-role --playbook ./site.yml --graph
```

Full flag reference:

```
Input Paths:
  -r, --role TEXT           Path to the Ansible role directory
  -c, --collection TEXT     Path to the Ansible collection directory
  -p, --playbook TEXT       Path to the playbook file

Output Control:
  -o, --output TEXT         Output README file name (default: README.md)
  -nob, --no-backup         Do not create a backup before overwriting
  -a, --append              Append to the existing README instead of replacing
  --dry-run                 Preview output without writing any files
  --validate/--no-validate  Validate markdown formatting before writing (default: on)
  --auto-fix                Automatically fix common markdown formatting issues
  --strict-validation       Fail if markdown validation errors are found

Content Sections:
  --no-vars                 Hide variable documentation
  --no-tasks                Hide task lists and task details
  --no-diagrams             Hide all Mermaid diagrams
  --no-examples             Hide example playbook sections
  --no-metadata             Hide role metadata, author, and license
  --no-handlers             Hide handlers section
  --include-complexity      Include complexity analysis section in README
  --minimal                 Generate minimal documentation (enables all --no-* flags)

Templates:
  --md-role-template        Path to the role markdown template file
  --md-collection-template  Path to the collection markdown template file
  --hybrid                  Use hybrid template (manual + auto-generated sections)

Visualization:
  -g, --graph               Generate Mermaid diagrams for role visualization
  -com, --comments          Extract and include inline task comments
  -tl, --task-line          Include source file line numbers for each task
  --simplify-diagrams       Show only high-level diagrams, hide detailed flowcharts

Analysis & Complexity:
  --complexity-report       Include role complexity analysis in documentation
  --simplification-report   Include detailed pattern analysis with simplification suggestions
  --show-dependencies       Generate task dependency matrix table
  --analyze-only            Analyze role complexity without generating documentation

Repository Integration:
  -ru, --repository-url TEXT  Repository base URL (for standalone roles)
  -rt, --repo-type TEXT       Repository type: github, gitlab, gitea, etc.
  -rb, --repo-branch TEXT     Repository branch name (e.g., main or master)

Preset:
  --preset [personal|team|enterprise|consultant]
                            Apply a built-in preset (see Presets section)

Output Framing:
  --positive / --neutral    Use positive/actionable output framing (default: positive)

Analysis & CI/CD:
  --fail-on [none|info|warning|critical]
                            Exit with code 1 if findings at or above this severity exist (default: none)
  --advanced-patterns       Show all findings including INFO-level; removes the default 5-recommendation cap
  --output-format [text|json]
                            Output format for findings (default: text)
  --recommendations-only    Show recommendations without generating documentation
  --show-info               Show INFO-level recommendations (hidden by default)
```

### docsible analyze role

Analyze a role's complexity and surface recommendations without generating or writing documentation.

```bash
docsible analyze role --role /path/to/role
docsible analyze role --role /path/to/role --preset=enterprise

# Show all findings including INFO-level with no recommendation cap
docsible analyze role --role /path/to/role --advanced-patterns

# Machine-readable JSON output for CI tool integration
docsible analyze role --role /path/to/role --output-format json
```

### docsible scan collection

Scan all roles in a collection directory, run analysis on each, and output a summary table sorted by severity. No files are written — analysis only.

```bash
# Scan all roles in the current collection
docsible scan collection ./my_collection

# CI/CD gating — exit 1 if any role has WARNING or CRITICAL findings
docsible scan collection . --fail-on warning --output-format json

# Show only the 5 worst roles
docsible scan collection ./my_collection --top-n 5

# Preview what would be scanned without running analysis
docsible scan collection ./my_collection --dry-run
```

```
  PATH                        Path to the collection directory
  --output-format [text|json] Output format for findings (default: text)
  --fail-on [none|info|warning|critical]
                              Exit with code 1 if any role has findings at or above this severity (default: none)
  --top-n N                   Show only the N worst roles in the summary
  --preset PRESET             Apply a built-in preset (personal/team/enterprise/consultant)
  --dry-run                   Preview roles that would be scanned without running analysis
```

### docsible validate role

Validate the documentation for a role without writing any files. Runs in dry-run mode with strict markdown validation on by default.

```bash
docsible validate role --role /path/to/role
docsible validate role --role /path/to/role --no-strict

# Exit 1 if CRITICAL findings exist (use in CI pipelines)
docsible validate role --role /path/to/role --fail-on critical

# Exit 1 if WARNING or CRITICAL findings exist
docsible validate role --role /path/to/role --fail-on warning

# Strict markdown validation — now correctly exits 1 on WARNING/CRITICAL (was a no-op previously)
docsible validate role --role /path/to/role --strict-validation
```

### docsible suppress

Manage suppression rules that silence false-positive recommendations. Rules are stored in `.docsible/suppress.yml`.

```bash
# Add a suppression rule
docsible suppress add "no examples" --reason "Examples live in a separate repo"

# Add with an expiry date and file scope
docsible suppress add "no examples" --reason "Legacy role" --expires 90 --file "roles/webserver"

# Add using a regular expression pattern
docsible suppress add "missing (readme|examples)" --reason "Not applicable" --regex

# List all active suppression rules
docsible suppress list

# Remove a rule by its ID
docsible suppress remove <rule-id>

# Remove all expired rules
docsible suppress clean
```

### docsible guide

Display interactive guides and tutorials in the terminal.

```bash
docsible guide getting-started
docsible guide troubleshooting
docsible guide smart-defaults
```

### docsible role (legacy)

The original single-command interface still works and accepts all flags. A deprecation notice is printed to stderr.

```bash
docsible role --role /path/to/ansible/role --playbook /path/to/playbook.yml --graph
docsible role --collection ./my-collection --no-backup --graph
```

Use `docsible document role` for new workflows.

## Presets

Presets bundle a curated set of flags suited to common use cases. Apply any preset with `--preset` on `document`, `analyze`, `validate`, or `init`.

| Preset | Description | `fail_on` | `max_recommendations` |
|---|---|---|---|
| `personal` | Solo developers — fast, minimal output, no diagrams | none | 5 |
| `team` | Team collaboration — comprehensive docs, auto-fix, smart defaults | warning | 10 |
| `enterprise` | Production/compliance — full validation, strict mode, all reports | critical | unlimited |
| `consultant` | Client deliverables — maximum detail, all diagrams and reports | warning | 15 |

```bash
docsible document role . --preset=personal
docsible document role . --preset=team
docsible document role . --preset=enterprise
docsible document role . --preset=consultant
```

Each preset now includes analysis defaults (`fail_on`, `essential_only`, `max_recommendations`) in addition to documentation generation flags. These analysis defaults control CI exit behaviour and how many recommendations are surfaced. See [CONFIGURATION.md](CONFIGURATION.md) for the full preset settings table.

Individual flags passed on the command line override preset defaults.

## Suppression System

When Docsible surfaces recommendations that do not apply to a particular role (false positives), suppressions allow you to silence them persistently.

Suppressions are stored in `.docsible/suppress.yml` relative to the working directory. Each rule records a pattern, a mandatory reason, an optional file scope, an optional expiry date, and an optional approver for audit purposes.

```bash
# Silence a recommendation matching a substring
docsible suppress add "no examples" --reason "Examples live in a separate repo"

# Silence with a 90-day expiry and scope to one role
docsible suppress add "no examples" --reason "Legacy role" --expires 90 --file "roles/webserver"

# View current rules
docsible suppress list

# Clean out expired rules
docsible suppress clean
```

## Hybrid Template

Use the `--hybrid` flag to generate a README with a mix of manual sections (for high-level narrative) and auto-generated sections (for accurate technical details):

```bash
docsible document role --role ./my-role --hybrid --graph --comments
```

The hybrid template includes:

- Manual sections: Quick Start, Architecture Overview, Example Playbooks, Testing, Compatibility
- Auto-generated sections: Task Execution Flow, Role Variables, Task Details, Dependencies, Role Metadata
- HTML comments (`<!-- MANUALLY MAINTAINED -->` / `<!-- DOCSIBLE GENERATED -->`) mark which sections to edit by hand

## Data Sources

Docsible fetches information from the following files within the specified Ansible role:

- `defaults/*.yml/yaml` — default variables
- `vars/*.yml/yaml` — role-specific variables
- `meta/main.yml/yaml` — role metadata
- `tasks/*.yml/yaml` — tasks, including special task types and subfolders

## Example

[Thermo core simulator](https://github.com/docsible/thermo-core)

## Prerequisites

Docsible requires Python 3.x and the following libraries:

- Click
- Jinja2
- PyYAML
- Pydantic

## Comment Tags

### On variables and defaults

Place comment tags immediately before a variable in `defaults/main.yml`. The tool recognises four tags:

| Tag | Column populated | Notes |
|-----|-----------------|-------|
| `# title:` | **Title** | Short label for the variable |
| `# required:` | **Required** | Indicate whether the variable must be set (`true` / `false`) |
| `# choices:` | **Choices** | Comma-separated list of valid values |
| `# description:` | **Description** | Full description; overrides any inline YAML comment on the same line |

**Example `defaults/main.yml`:**

```yaml
# title: Database host
# description: Hostname or IP address of the primary database server
# required: true
db_host: "localhost"

# title: Database port
# required: false
# choices: 3306, 5432, 27017
db_port: 3306

# title: Retry attempts
db_retries: 3  # Number of connection retries before giving up
```

The snippet above produces a variable table like:

| Variable | Value | Type | Required | Choices | Title | Description |
|----------|-------|------|----------|---------|-------|-------------|
| `db_host` | `"localhost"` | str | true | | Database host | Hostname or IP address of the primary database server |
| `db_port` | `3306` | int | false | 3306, 5432, 27017 | Database port | |
| `db_retries` | `3` | int | | | Retry attempts | Number of connection retries before giving up |

Variables with none of the four tags still appear in the table; the columns for those fields are simply left empty.

### On tasks

The tool reads all lines before each `- name:` entry that begin with `#`. Those comments are reported in the **Comments** column of the task tables. For example:

```yaml
# Runs only when the target package is not already installed
- name: Install application package
  ansible.builtin.apt:
    name: myapp
    state: present
```

## Contributing

For details on how to contribute, please read the [Contributing Guidelines](CONTRIBUTING.md).
Pull requests that do not follow the guidelines may be closed or require changes before being accepted.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.
