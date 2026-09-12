# Docsible: Verified Project State

Snapshot: 2026-09-13

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

## Role Execution Graph

Docsible now has an internal, renderer-independent `RoleExecutionGraph` built
from the raw Ansible task facts already retained by `RoleInfoLoader`. Its small
interface is `build_role_execution_graph(role_info)`.

- Nodes represent roles, task files, tasks, handlers, variables, and external
  role references.
- Typed edges represent containment, task-file include/import, role
  include/import, task-to-handler notification, and known-variable use.
- Every relationship carries its source location and preserves the resolution
  state: `static`, `dynamic`, `unknown`, or `unresolved_external`. Dynamic
  Ansible expressions are recorded without inventing a target.
- README execution phases are now a static traversal from `tasks/main.yml`;
  conditional paths are annotated and unreachable files are identified rather
  than being presented as filesystem-order phases.
- Component architecture diagrams derive variable and handler edges from graph
  facts, replacing the old first-file and last-file proxy edges.
- The graph uses standard-library dataclasses for a small serializable core.
  NetworkX is not a Docsible dependency; a future visualization adapter may
  convert the graph for layout algorithms.

### Verified External Cases

- `geerlingguy/ansible-role-docker` @ `38be616950679548ae0ba8a81ffcceca1b3090bd`:
  JSON parses, documentation generation succeeds, `main.yml` is Phase 1, and
  the five conditional include boundaries plus actual handler notifications
  render as source-backed relationships.
- `geerlingguy/ansible-role-nginx` @ `5ff0b235006390a0d5666fd4cce7477410982cdf`:
  JSON parses, documentation generation succeeds, `main.yml` is Phase 1, the
  seven OS-specific branches retain their `when` conditions, and `vhosts.yml`
  is reached through its static import.

### Next Graph Milestones

1. Publish a documented JSON graph contract after its node and edge fields are
   exercised by more external candidates.
2. Resolve locally available roles in sibling role directories and collections;
   retain absent Galaxy/FQCN roles as explicit external-reference nodes.
3. Add graph projections for dynamic task/role includes, loops, blocks,
   rescue/always, and source-linked variable scopes without claiming static
   certainty where Ansible defers resolution.
4. Make `graph_visualisation` a renderer adapter over this contract, using
   NetworkX only for renderer-specific layout work.
5. Extend the pinned external corpus before treating the graph contract as
   release-stable.

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

This file records observable project state, commands verified for this
snapshot, and explicitly approved next milestones for the Role Execution Graph.
It does not assert historical phase completion, performance results, or
unverified feature maturity.
