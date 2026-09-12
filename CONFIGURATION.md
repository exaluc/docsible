# Docsible Configuration Reference

Docsible configuration is role-local. For a role passed with `--role`, it reads:

```text
<role>/.docsible/config.yml
```

Initialize it with:

```bash
docsible init --path ./my-role --preset team
```

Install this fork from GitHub:

```bash
pip install "git+https://github.com/jier/docsible.git"
```

For a pinned revision, append `@<tag-or-commit>` to that URL.

## Configuration File

```yaml
# .docsible/config.yml
preset: team

# Settings that override values supplied by the selected preset.
overrides:
  generate_graph: true
  hybrid: true
  max_recommendations: null # No display cap.

# Recommendation settings. See "Precedence" for their interaction with presets.
fail_on: warning
essential_only: false
max_recommendations: 10

# Metadata written by the setup wizard. It does not configure validation behavior.
ci_cd:
  platform: github
```

Supported fields are:

| Field | Type | Meaning |
|---|---|---|
| `preset` | `personal`, `team`, `enterprise`, `consultant`, or null | Preset selected for this role |
| `overrides` | mapping | Option values to apply over the selected preset |
| `fail_on` | `none`, `info`, `warning`, `critical`, or null | Recommendation gate when no preset or `overrides` value supplies it |
| `essential_only` | boolean or null | Accepted and resolved recommendation setting when no preset or `overrides` value supplies it; it is not currently used to filter formatter output |
| `max_recommendations` | integer or null | Recommendation display cap when no preset or `overrides` value supplies it; a top-level null is unset, while `overrides.max_recommendations: null` removes the cap |
| `ci_cd` | mapping | Setup-wizard metadata |

Use Click option names as keys in `overrides`; for example, the graph option is `generate_graph`, not `graph`.

## Precedence

Only options explicitly supplied on the command line override configuration. A Click default is not an explicit CLI option.

For normal options, values are resolved from low to high precedence:

1. Command defaults.
2. The selected preset.
3. `.docsible/config.yml` `overrides`.
4. Explicit CLI options, such as `--graph` or `--no-backup`.

`--preset` selects the preset instead of the role config's `preset`, but role-local `overrides` still apply. The top-level `fail_on`, `essential_only`, and `max_recommendations` fields only fill gaps left by the selected preset and `overrides`; they do not replace those values. Explicit CLI flags always win.

## Presets

| Setting | `personal` | `team` | `enterprise` | `consultant` |
|---|---|---|---|---|
| `generate_graph` | false | smart default | true | true |
| `minimal` | true | smart default | false | false |
| Markdown validation | enabled | enabled | enabled | enabled |
| Markdown strictness | false | false | true | false |
| `auto_fix` | false | true | false | false |
| `fail_on` | none | warning | critical | warning |
| `max_recommendations` | 5 | 10 | unlimited | 15 |

For the `team` preset, graph generation, minimal output, and dependency output are left for runtime smart defaults unless configuration or an explicit CLI option supplies a value.

## Role Commands

The documented role commands are:

```bash
docsible document role --role ./my-role
docsible analyze role --role ./my-role
docsible validate role --role ./my-role
```

`document role` generates documentation. `analyze role` runs recommendation analysis without rendering documentation. `validate role` renders the generated Markdown in memory and validates it without writing a README, backup, or `.docsible` file.

All three commands accept the following role-oriented options.

| Area | Options |
|---|---|
| Paths | `--role/-r`, `--collection/-c`, `--playbook/-p` |
| Output | `--output/-o`, `--append/-a`, `--no-backup/-nob`, `--no-docsible/-nod`, `--dry-run`, `--validate/--no-validate`, `--auto-fix`, `--strict-validation`, `--output-format` (`text` or `json`) |
| Content | `--minimal`, `--no-vars`, `--no-tasks`, `--no-diagrams`, `--simplify-diagrams`, `--no-examples`, `--no-metadata`, `--no-handlers`, `--include-complexity` |
| Generation | `--graph/-g`, `--comments/-com`, `--task-line/-tl`, `--complexity-report`, `--simplification-report`, `--show-dependencies`, `--analyze-only` |
| Recommendations | `--recommendations-only`, `--show-info`, `--advanced-patterns`, `--no-suppress`, `--fail-on` (`none`, `info`, `warning`, or `critical`) |
| Templates | `--md-role-template` (also `--md-template`, `-rtpl`, `-tpl`), `--md-collection-template/-ctpl`, `--hybrid` |
| Repository | `--repository-url/-ru`, `--repo-type/-rt`, `--repo-branch/-rb` |
| Other | `--preset` (`personal`, `team`, `enterprise`, or `consultant`), `--positive/--neutral`, `--help-full` |

`--minimal` hides variables, tasks, diagrams, examples, metadata, and handlers. `--dry-run` does not write files.

## Validation And Recommendation Gates

Markdown validation and recommendation analysis are independent:

- `docsible validate role --role ./my-role` is read-only and validates rendered Markdown in memory. Its command default is strict; use `--no-strict` to disable strict Markdown validation. Preset and config resolution can change that default unless `--strict` or `--no-strict` is explicit.
- `--strict-validation` makes Markdown validation issues fatal when Markdown validation is enabled. With `--no-validate`, it instead gates WARNING and CRITICAL recommendation findings.
- `--fail-on` gates recommendation findings, including findings not displayed because of a display cap. It exits with status 1 for findings at or above its severity: `info`, `warning`, or `critical`. `none` disables this gate.

Examples:

```bash
# Validate generated Markdown without modifying the role.
docsible validate role --role ./my-role

# Generate docs, but fail CI for warning-level recommendations or worse.
docsible document role --role ./my-role --fail-on warning

# Run recommendation analysis and emit JSON for a CI consumer.
docsible analyze role --role ./my-role --output-format json
```

With `--output-format json`, analysis emits JSON even when there are no visible findings. The payload has `role`, `findings`, `summary`, and `truncated` fields; `findings` is an empty array and summary counts are zero when no findings are present.

## CI Example

```yaml
- name: Install Docsible fork
  run: pip install "git+https://github.com/jier/docsible.git"

- name: Validate generated Markdown and gate recommendations
  run: docsible validate role --role . --fail-on warning
```

## Suppressions

Recommendation suppressions are stored at `<role>/.docsible/suppress.yml`. Use the supported command group to manage them:

```bash
docsible suppress add "no example playbook" --reason "Examples are maintained elsewhere"
docsible suppress list
docsible suppress remove <id>
docsible suppress clean --dry-run
```

Pass `--no-suppress` to a role command to include suppressed recommendations.
