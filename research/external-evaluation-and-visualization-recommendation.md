# External Evaluation And Visualization Recommendation

## Product Wording

Docsible helps engineers understand and safely change unfamiliar Ansible roles by producing traceable documentation, quality findings, and navigable execution views.

This positions the project around onboarding, migrations, handovers, and safe change rather than README generation alone.

## External Evaluation Harness

Build the executable external-evaluation harness outside this repository and outside the `docsible/` Python package. A separate repository or sibling workspace keeps third-party cloning, network access, licenses, changing remote branches, and evaluation-specific dependencies out of normal Docsible development and CI.

Docsible should retain only stable machine-readable contracts that the harness consumes, such as JSON analysis output and documented CLI behavior. The harness should clone into temporary directories and never commit third-party source code.

Use a pinned manifest for a small, diverse corpus. Each entry should record:

- Repository URL and immutable commit SHA.
- License and role or collection path.
- Ansible features expected in the project.
- Stable assertions to evaluate after cloning.

Assertions should focus on observable properties instead of full README snapshots:

- Commands complete without crashes.
- Read-only commands do not write role files.
- JSON output is valid.
- Role, task, variable, handler, and include discovery is plausible for known fixtures.
- Generated Markdown validates.

Run this harness manually, nightly, or before a release. Do not make normal pull requests depend on public network availability.

### Location Decision

The executable harness should be a sibling repository, for example
`docsible-evaluation`, rather than a module in this repository. This keeps
network access, third-party licensing, changing remote branches, and
evaluation-only dependencies separate from Docsible's normal development
workflow. This repository should retain the documented machine-readable
contracts that the harness consumes, not the cloned corpus.

## Shortlisting Public Projects

Do not clone every candidate before screening it. Start with repository metadata and a shallow, pinned checkout only after a candidate passes a shortlist review.

Basic complexity signals are useful, but they are not enough on their own:

- Number of roles, task files, tasks, defaults, handlers, and plugins.
- Presence of collections, FQCN modules, nested includes, imports, blocks, rescue/always, loops, conditions, notifications, templates, and argument specs.
- Repository activity, license clarity, testability, and absence of credentials or destructive automation concerns.

Select for behavior diversity, not just high task counts. A useful initial corpus has roles that are simple, modular, collection-based, handler-heavy, include-heavy, condition-heavy, loop-heavy, and dynamically structured. Include at least one role whose graph is intentionally too large for a default Mermaid view.

For every candidate, record a hypothesis before evaluation, for example: "Docsible should identify three task files, two handlers, and an include boundary." This prevents the harness from becoming a generic no-crash test.

### Two-Stage Selection

Use a candidate profile rather than a single complexity score.

1. Discovery without a full clone:
   - Use GitHub or Galaxy metadata for license, activity, repository size, and
     language.
   - Use a Git tree API or sparse shallow checkout to count roles, task files,
     handlers, plugins, defaults, templates, and YAML files.
   - Detect structural markers such as includes/imports, blocks,
     rescue/always, loops, conditions, notifications, collections, FQCNs, and
     argument specifications.
2. Pinned evaluation checkout:
   - Select for feature diversity rather than task count alone.
   - Pin an immutable commit SHA and clone shallowly into a temporary
     directory.
   - Never execute playbooks, repository scripts, or generated code.

High task counts are a useful signal but not a sufficient selection rule. Ten
large roles with the same structure are less valuable than a deliberately
varied corpus that exercises distinct Ansible behaviors.

## Human Value Evaluation

The meaningful question is whether the outputs help engineers answer unfamiliar-role questions faster and more accurately. Compare a repository alone with the repository plus Docsible outputs for tasks such as:

- What does this role install and configure?
- Which variables matter before a migration?
- Which task files and handlers are involved in a change?
- Which execution paths are static, conditional, or dynamic?

Measure completion time, answer accuracy, and confidence with a small group of engineers. This is stronger evidence of value than graph size or README length.

## Visualization Direction

Mermaid remains appropriate for portable, small static summaries. It should not be the only execution view for complex roles.

Build a renderer-independent execution and relationship graph model before integrating interactive visualization. The existing graph-visualization project can become a renderer adapter, not another parser or analyzer:

```text
Ansible role -> role facts -> execution graph -> phase abstraction -> renderer
                                                              -> Mermaid summary
                                                              -> interactive view
```

Phase points are a useful readability abstraction when they group task flow into concepts such as install, configure, validate, migrate, start, and cleanup. The underlying graph must still preserve source links and uncertainty:

- Statically resolvable includes link to their target files.
- Dynamic includes are marked dynamic or unknown.
- Loops remain one task node with loop metadata.
- Conditions annotate branches rather than pretending all paths execute.
- Handler notifications are explicit relationship edges.

This yields an explorable model without claiming that Ansible execution is fully statically knowable.
