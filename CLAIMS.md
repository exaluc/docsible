# Docsible: Verified Project State

Snapshot: 2026-09-13 (updated: Role Execution Graph completion, collection
support fixes, and role-analysis consolidation)

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
uv run mypy docsible
```

- `uv run pytest`: **1200 passed, 3 xpassed** (was 1156 passed at the
  2026-08-27 baseline; growth is new regression tests for the Role Execution
  Graph, collection-support fixes, and the role-analysis consolidation below).
- `uv run ruff check .`: **all checks passed** (was 47 findings, all in the
  test tree). The 5 findings remaining after the graph work (an undefined
  `click` reference, unused defensive imports, an unused loop variable) have
  since been fixed; the check is now clean.
- `uv run mypy docsible`: **no issues found in 236 source files**.
- `uv run python -m build` and `npx --yes jscpd docsible` were run for the
  2026-08-27 baseline only and have not been re-verified in this snapshot.

## Known Limitations

- There is no GitHub Actions workflow in `.github/workflows`; tests, linting,
  builds, and CLI smoke checks are not yet run by repository CI.
- `RoleInfoBuilder` (`docsible/commands/document_role/builders/role_info_builder.py`)
  is still present as a deprecated, unused-in-production duplicate of
  `RoleInfoLoader`. The role-analysis pipeline (complexity, execution graph,
  recommendations) is now consolidated (see below); role-information
  *loading* still has this one remaining duplicate implementation.
- The deprecated `docsible role` command is still present alongside the newer
  intent-based command groups.
- Collections do not yet resolve cross-role boundaries: `include_role`/
  `import_role` targets pointing at a sibling role in the same collection are
  recorded as `unresolved_external` rather than a real internal graph edge.
  See Next Graph Milestones.

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
  than being presented as filesystem-order phases. The README presents these
  as Execution Routes rather than placeholder phases.
- Component architecture diagrams derive variable and handler edges from graph
  facts, replacing the old first-file and last-file proxy edges.
- Task nodes preserve modern and legacy loop syntax (`loop`, `with_items`,
  `with_first_found`, and other `with_*` forms), and structured
  `loop_control` — `loop_var`, `index_var`, `label` — is captured into the
  task-node metadata and the serialized graph, and surfaced in the README
  Loop column as `loop (as: <var>)`. This makes custom loop variables visible
  (they are loop-local, not role variables) for both humans and external
  renderers.
- Complexity reports retain their structural metrics and add graph metrics:
  statically reachable task files, dynamic and unknown boundaries, external
  role references, loop tasks, notification edges, orphan task files,
  collection dependencies, and conditional decision points. The full
  serialized graph (`nodes`, `edges`) is attached to the complexity report and
  exposed via `analyze role --output-format json`.
- The graph uses standard-library dataclasses for a small serializable core.
  NetworkX is not a Docsible dependency; a future visualization adapter may
  convert the graph for layout algorithms.
- Templated include/import targets are classified, not just marked unknown:
  a target matching `{{ role_path }}/tasks/<literal>` resolves statically; a
  templated target with a literal filename prefix (e.g.
  `install-{{ os_family }}.yml`) resolves to one or more `dynamic` candidate
  edges against in-repo files with that prefix; fully unconstrained
  expressions remain dynamic with no fabricated candidates.
- For roles classified `ENTERPRISE`, the README uses a bounded **grouped
  execution overview** (directory-level groups, dynamic/unknown boundaries
  summarized as counts, orphan files collapsed to one line) instead of a
  detailed per-task-file diagram that would be unreadable at that size. The
  detailed projection is used below a fixed budget (20 task files, 35
  relationship edges, fan-out 8); any signal exceeded switches projection.
- The rendered README leads with product value before task-file reference
  material: Overview → Architecture Overview → Execution Graph Summary →
  Execution Routes → Recommendations → Variable Reference → Task File
  Reference → Handlers.

### Verified External Cases

- `geerlingguy/ansible-role-docker` @ `38be616950679548ae0ba8a81ffcceca1b3090bd`:
  JSON parses, documentation generation succeeds, `main.yml` is Phase 1, and
  the five conditional include boundaries plus actual handler notifications
  render as source-backed relationships.
- `geerlingguy/ansible-role-nginx` @ `5ff0b235006390a0d5666fd4cce7477410982cdf`:
  JSON parses, documentation generation succeeds, `main.yml` is Phase 1, the
  seven OS-specific branches retain their `when` conditions, and `vhosts.yml`
  is reached through its static import.
- `geerlingguy/ansible-role-mysql` @ `0a0ea6b728120b3ab3918332d9404bb65836834d`:
  legacy `with_items`/`with_first_found` loops render in task tables; 9 static
  include boundaries resolve; no false orphans.
- `geerlingguy/ansible-role-postgresql` @ `53abdf144de8231b2f2ce0652523eebc3eda7100`:
  mixed `include_tasks`/`import_tasks` boundaries resolve; a 27-file `vars/`
  directory renders without truncation.
- `nginx/ansible-role-nginx` (official) @ `157e0e97406f798bd6f50db37430a78c4269aa92`:
  244 tasks, 31 nested task files, classified `ENTERPRISE`. Verifies the
  grouped execution overview and templated-target classification: 22 dynamic
  candidate edges resolve against in-repo files, 0 unknown boundaries, 0 false
  orphans (was 13 before dynamic-candidate resolution).
- `prometheus-community/ansible` @ `e2f46e17d33651c3c09042aaa9c8f29b87a9753f`
  (the `prometheus.prometheus` collection, 26 roles): first real collection
  exercised end-to-end; verifies collection support fixes and role-analysis
  parity below.
- `dev-sec/ansible-collection-hardening` @ `3102eddbd116c5f8c1581aca543d372dbc326764`
  (the `devsec.hardening` collection; loop/condition-heavy; 4 real roles +
  2 uninitialized submodule dirs under `roles/`): verifies the loop_control
  capture (2 `loop_var` usages now render as `loop (as: …)`), the collection
  discovery parity (scan and `--collection` both report 4; the 2 empty
  submodule dirs are skipped/warned and excluded from the index), and the
  ENTERPRISE grouped diagram still reachable via explicit `--graph`
  (`os_hardening`, 125 tasks / 23 files).

### Completed Graph Milestones

1. Preserve loop metadata on ordinary tasks and render it in documentation.
2. Add graph-derived execution metrics alongside structural complexity counts.
3. Replace placeholder phases with source-backed Execution Routes.
4. Preserve static and dynamic cross-role boundaries in a JSON-serializable
   renderer contract.
5. Classify templated include/import targets as static, dynamic-candidate, or
   genuinely unresolved, instead of leaving every templated target as an
   orphan.
6. Add a bounded grouped-execution-overview projection for `ENTERPRISE` roles
   so large role graphs stay readable instead of being suppressed entirely or
   rendered as an unreadable wall of nodes.
7. Consolidate role complexity/execution-graph/recommendation analysis into
   one shared implementation (`docsible/commands/document_role/role_analysis.py`:
   `analyze_role()` + `render_analyzed_role()`), used identically by
   `RoleOrchestrator` (standalone `document role`), `document_collection_roles()`
   (`document role --collection`), and `scan/collection.py::_analyse_role()`
   (`scan collection`). This fixed a real divergence: `scan collection`
   previously computed recommendations without the complexity report and
   silently missed the graph-aware findings the other two paths already had.
8. Give collection roles full parity with standalone roles: every role
   documented via `document role --collection` now gets an identical
   Architecture Overview, Execution Graph Summary, Execution Routes, and
   Recommendations section (previously skipped entirely for collection
   roles).
9. Add a collection-level **Complexity Overview** and **Role Index** to the
   collection README: aggregate role counts by complexity category and total
   task count, plus a per-role table (complexity badge, task count,
   critical/warning counts, top finding) sorted by complexity descending, so
   a reader sees which roles need attention before opening any of them. This
   is deliberately an index of independent per-role facts, not a synthesized
   single "collection complexity" score — a collection has no single
   execution graph the way one role does.
10. Capture `loop_control` (`loop_var`/`index_var`/`label`) into task-node
    metadata and the serialized graph, and surface it in the README Loop
    column as `loop (as: <var>)`. (Candidate 7 finding: source `loop_var`
    appeared in 0 of 2 generated READMEs; now 2 of 2 render, with the graph
    carrying the metadata.)
11. Make collection role discovery consistent: `document role --collection`
    now iterates `ProjectStructure.find_roles()` (the same filter `scan
    collection` uses), so the two can no longer disagree on what is a role.
    Role-less `roles/*` directories (e.g. uninitialized git submodules with
    no `tasks`/`defaults`/`vars`/`meta`) are skipped, warned about, excluded
    from the dry-run count and the collection Role Index, and never written
    into. (Candidate 7 finding: `scan` found 4, `--collection` documented 6,
    and 2 stub READMEs were silently written into empty submodule dirs
    invisible to the parent `git status`; now 4 everywhere with warnings.)
12. Bound the grouped-execution overview for flat task directories. Grouping
    keyed on the first path segment, so a nested layout already compresses
    (official nginx: 31 files → 9 directory nodes, 50 mermaid lines) but a
    flat layout degenerated to one node per file (os_hardening: 23 files → 23
    nodes, 100 lines — the densest diagram in the corpus). Added a hard node
    cap (`_MAX_GROUP_NODES = 10`): when grouping yields more groups than the
    cap, keep the entry point and the largest groups by task count and fold
    the remainder into one `other (N task files)` node; hub fan-out into the
    bucket collapses via the existing edge dedup. Verified: os_hardening
    23 → 11 nodes (100 → 52 lines) with an `other (13 task files)` bucket;
    nested layouts at or under the cap render unchanged (official nginx stays
    at 9 directory nodes, no bucket). Also fixed label pluralization (`1 task
    file` vs `N task files`). This subsumes finding B (nested roles already
    give the bounded multi-level view); finding D stays deferred (see Next
    Graph Milestones).

### Next Graph Milestones

1. Publish a documented JSON graph contract after its node and edge fields are
   exercised by more external candidates.
2. Resolve `include_role`/`import_role` targets that point at a sibling role
   in the same collection into real internal graph edges, instead of
   `unresolved_external`. Scoped narrowly to this one relationship (not a
   full collection-wide dependency graph, which was assessed as low value:
   readers almost always want one role's own dependencies, not a map of all
   roles' relationships).
3. Add graph projections for blocks, rescue/always, and source-linked
   variable scopes without claiming static certainty where Ansible defers
   resolution.
4. Make `graph_visualisation` a renderer adapter over this contract, using
   NetworkX only for renderer-specific layout work.
5. Extend the pinned external corpus before treating the graph contract as
   release-stable.
6. (Finding D, deferred) Surface diagram tiering for `--graph`: COMPLEX and
   ENTERPRISE roles currently render only the file-level architecture
   diagram; per-task-file flow diagrams are shown only for SIMPLE/MEDIUM.
   This is by design (a task-level graph is unreadable at that size), not a
   defect, so no inline disclaimer is added yet. The genuine remedy is to
   expose task-level flow through the interactive `graph_visualisation`
   adapter (item 4), where the "too large for Mermaid" content belongs; the
   README note, if ever needed, should be written once that adapter exists so
   it does not churn.

## Collection Support

`document role --collection` and `scan collection` were exercised end-to-end
for the first time against a real, non-trivial collection
(`prometheus-community/ansible`, 26 roles) and had several defects that a
smaller/synthetic test collection did not surface:

- `document role --collection ... --dry-run` was not read-only: it wrote a
  README backup before any short-circuit existed. Fixed with an explicit
  dry-run check before any file is touched.
- `meta/argument_specs.yml` files using Ansible's `!unsafe` YAML tag failed to
  load (`could not determine a constructor for the tag '!unsafe'`). Fixed
  with a `DocsibleSafeLoader` that preserves the scalar value.
- The role README template referenced `sections/argument_specs.jinja2`,
  which did not exist, crashing collection documentation for any role with
  argument specs. The template was added.
- The collection-level README template referenced `role.belongs_to_collection`
  in a macro where `role` was never in scope, raising
  `jinja2.exceptions.UndefinedError` for any collection with a detectable
  repository URL. Fixed: collection-level links always build the `roles/`
  prefix, since collection templates are always in a collection context.
- Nearly every collection template (`overview.jinja2`, `roles_list.jinja2`,
  `galaxy_info.jinja2`, `dependencies.jinja2`, `plugin_list.jinja2`, and the
  `render_arguments_list` macro) was missing Jinja whitespace control,
  producing a blank line after almost every list item, table row, and
  argument-spec field — a generated collection README for a 26-role
  collection was ~8000 lines, mostly blank. Fixed at the template level, and
  `render_collection()` now applies the same blank-line normalization
  (`MarkdownProcessor`) that `render_role()` already applied, capping any
  residual run at 2 consecutive blank lines.
- `sections/overview.jinja2` printed a literal `\n` after every collection
  author name (a template typo, not an escape sequence). Fixed.
- The per-role loop used a raw `os.listdir` of `roles/`, so it disagreed with
  `scan`'s `find_roles` filter and treated uninitialized git submodules
  (empty `roles/*` dirs) as zero-content roles: it miscounted in `--dry-run`,
  wrote stub `README.md`/`.docsible` into submodule paths invisible to the
  parent `git status`, and inflated the collection Role Index. Fixed: the
  collection path now iterates `ProjectStructure.find_roles()` and skips +
  warns on role-less dirs. (Found via
  `dev-sec/ansible-collection-hardening`, which has 4 real roles + 2 empty
  submodule dirs under `roles/`.)

## Remaining Duplication Work

The source-only duplication scan is below the original baseline, but remaining
duplication is prioritized by ownership and behavior rather than percentage.

1. **Partially resolved.** Role complexity/execution-graph/recommendation
   *analysis* is now consolidated in `role_analysis.py` (see Role Execution
   Graph, milestone 7) and used identically by `document role`,
   `document role --collection`, and `scan collection`. Role-information
   *loading* still has one remaining duplicate: `RoleInfoBuilder` alongside
   `RoleInfoLoader` (see Known Limitations).
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
