# Contributor Guide

## Scope

- Keep each change focused on the requested behavior; do not refactor unrelated code.
- Preserve upstream attribution in package metadata, documentation, and notices.
- Do not edit `role_test/` unless a test explicitly requires a fixture change.
- Do not modify `CLAIMS.md` unless the task explicitly requests it.
- Follow existing patterns and reuse existing utilities before adding abstractions.

## Working Practices

- Read the affected code and nearby tests before editing.
- Add or update tests when behavior changes; keep fixtures minimal.
- Use the real CLI and its documented options when validating behavior. Do not invent shell tests or claim checks pass without running them.
- Do not hide lint, type-check, or test failures. Report failures with their command output and distinguish pre-existing failures from new ones when verified.

## Verification

Set up the development environment, then run the applicable checks from the repository root:

```bash
uv sync --group dev
uv run pytest
uv run ruff check .
uv run mypy docsible
```

Run the source-only duplication scan when it is useful:

```bash
npx --yes jscpd docsible --pattern "**/*.py"
```

`jscpd` is informational: its current baseline is 21 clones and 1.30% duplicated lines, not a zero-threshold gate. Update the baseline only after reviewing intentional duplication.

## Verified Baseline (2026-08-27)

- `uv run pytest`: 1156 passed, 10 warnings.
- `uv run ruff check .`: 47 findings.
- `uv run mypy docsible`: 3 errors in 2 files.

Treat these results as a starting point, not permission to introduce additional failures.
