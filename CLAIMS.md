# Docsible: Verified Project State

Snapshot: 2026-08-27

## Purpose

Docsible is a Python command-line tool for generating and checking Markdown
documentation for Ansible roles and collections. It analyzes role structure and
metadata, renders documentation, and provides validation, recommendation,
diagram, configuration, and suppression capabilities.

## Attribution and Identity

- This repository is an explicitly attributed fork of
  [docsible/docsible](https://github.com/docsible/docsible).
- The upstream repository is configured as `upstream`; this fork is published
  as [jier/docsible](https://github.com/jier/docsible).
- Distribution package: `docsible-jier`.
- CLI command: `docsible`.
- Current package version: `0.9.0`.
- Supported Python version: 3.10 or newer.
- The project metadata credits Lucian BLETAN as author and Jier Nzuanzu as
  maintainer.

## Current CLI Surface

The CLI registers these top-level commands:

```text
analyze  check  document  guide  init  role  scan  suppress  validate
```

`docsible role` remains registered for compatibility but emits a deprecation
warning. Use `docsible document role` for the current role-documentation
workflow.

## Development Setup

The project uses `uv` dependency groups. Install the development dependencies
with:

```bash
uv sync --group dev
```

The package is built with Hatchling and declares its CLI entry point in
`pyproject.toml`.

## Verification Performed

The following commands were run for this snapshot:

```bash
uv run pytest
uv run ruff check .
uv run python -m build
npx --yes jscpd docsible
```

- `uv run pytest` completed successfully.
- `uv run ruff check .` reported 47 findings, all in the test tree. Most are
  import ordering or unused-import issues; the check is not currently clean.
- `uv run python -m build` successfully produced the source distribution and
  wheel for `docsible-jier` version `0.9.0`.
- `npx --yes jscpd docsible` was run against the source tree only and found
  duplicate code, including overlapping analyzer and command-orchestration
  paths.

## Known Limitations

- There is no GitHub Actions workflow in `.github/workflows`; tests, linting,
  builds, and CLI smoke checks are not yet run by repository CI.
- Ruff currently reports findings in the test tree.
- The analyzer migration is incomplete: role-analysis and role-documentation
  orchestration retain duplicated implementation, including role-information
  assembly in `complexity_analyzer` and `document_role`.
- The deprecated `docsible role` command is still present alongside the newer
  intent-based command groups.

## Remaining Duplication Work

The source-only duplication scan is below the original baseline, but remaining
duplication is prioritized by ownership and behavior rather than percentage.

1. Consolidate role-information assembly into one read-only loader used by
   commands and analyzers. This is the highest priority because duplicate
   loaders previously produced divergent behavior.
2. Consider a private helper for repeated integration-provider task traversal
   after the role-loader migration is complete.
3. Review overlapping renderer model fields only when a concrete rendering
   change requires them to move together.
4. Remove obsolete duplicate tests and generated fixture backups only after
   confirming they are not test contracts.

## Scope of This Document

This file records observable project state and commands verified for this
snapshot. It does not assert historical phase completion, performance results,
future roadmaps, or unverified feature maturity.
