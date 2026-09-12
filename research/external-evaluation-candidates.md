# External Evaluation Candidates

## Overview

This document shortlists a small, diverse corpus of external public Ansible
projects for the docsible external evaluation harness, following the selection
philosophy in `external-evaluation-and-visualization-recommendation.md`. Every
candidate was screened without cloning, using the GitHub REST API (repo
metadata, head commit, recursive git tree) and raw file fetches pinned at an
immutable commit SHA. No repository was cloned and no playbook or repository
script was executed.

The shortlist covers all required behavior-diversity categories:

| Category | Anchor candidate(s) |
|---|---|
| Simple role | geerlingguy/ansible-role-docker, geerlingguy/ansible-role-nginx |
| Modular role (task files split by concern) | nginx/ansible-role-nginx, geerlingguy/ansible-role-mysql |
| Collection-based project (galaxy.yml) | prometheus-community/ansible, dev-sec/ansible-collection-hardening |
| Handler-heavy (many handlers / notify chains) | ansible-lockdown/UBUNTU22-CIS (40 handlers, 139 notify lines) |
| Include-heavy (include/import boundaries) | ansible-lockdown/UBUNTU22-CIS (96 boundaries, 68 task files) |
| Condition-heavy (when, blocks) | ansible-lockdown/UBUNTU22-CIS (826 when lines, 189 blocks), openstack/ansible-hardening |
| Loop-heavy (loop, loop_var, with_*) | geerlingguy/ansible-role-mysql, dev-sec/ansible-collection-hardening |
| Dynamically structured (templated includes, include_role) | nginx/ansible-role-nginx, openstack/ansible-hardening, prometheus-community/ansible |
| Graph too large for a default Mermaid view | ansible-lockdown/UBUNTU22-CIS (~925 tasks) |

Two known gaps remain and are recorded under Limitations: no shortlisted repo
uses `rescue:`/`always:` (0 occurrences across the entire corpus), and the
legacy `collections:` keyword is absent everywhere (0 occurrences).

## Selection method

Stage-one screening without cloning, per the two-stage selection policy:

1. `GET https://api.github.com/repos/OWNER/REPO` for description, stars,
   license, default branch, `pushed_at`, and archived status.
2. `GET https://api.github.com/repos/OWNER/REPO/commits/BRANCH` for the
   immutable head commit SHA to pin.
3. `GET https://api.github.com/repos/OWNER/REPO/git/trees/SHA?recursive=1`
   for full file listings (all trees returned `truncated: false`).
4. Raw fetches (`https://raw.githubusercontent.com/OWNER/REPO/SHA/path`) of
   every `tasks/` and `handlers/` YAML file, plus spot checks of LICENSE and
   defaults files. Raw fetches are not rate limited by the API quota.

Counts in this document are derived as follows and are reproducible at the
pinned SHAs: role/task/handler/template/molecule file counts from git trees;
task counts as `^\s*- name:` grep entries across raw task files (a lower
bound; nameless tasks are not counted); handler counts as `- name:` entries
in handlers files; structural markers (include_tasks, import_tasks, blocks,
loops, when, notify, FQCN) as grep line counts across the same raw files.
Grep line counts are approximate by nature — see Limitations.

Candidate table (screened 2026-09-12):

| Repo | License | Pin SHA | Size signals | Category |
|---|---|---|---|---|
| geerlingguy/ansible-role-docker | MIT | 38be616950679548ae0ba8a81ffcceca1b3090bd | 6 task files, ~41 tasks, 2 handlers | simple role |
| geerlingguy/ansible-role-nginx | MIT | 5ff0b235006390a0d5666fd4cce7477410982cdf | 9 task files, ~24 tasks, 3 handlers | simple role, OS-split includes |
| geerlingguy/ansible-role-mysql | MIT | 0a0ea6b728120b3ab3918332d9404bb65836834d | 10 task files, ~52 tasks, 1 handler | modular role, legacy loops |
| geerlingguy/ansible-role-postgresql | MIT | 53abdf144de8231b2f2ce0652523eebc3eda7100 | 10 task files, ~38 tasks, 27 vars files | modular role, include+import mix |
| nginx/ansible-role-nginx | Apache-2.0 | 157e0e97406f798bd6f50db37430a78c4269aa92 | 31 task files (nested), ~244 tasks, 8 handlers | modular, handler-heavy, dynamic include |
| prometheus-community/ansible | Apache-2.0 | e2f46e17d33651c3c09042aaa9c8f29b87a9753f | 25 roles, 65 task files, ~383 tasks, 31 handlers | collection, include_role x100 |
| dev-sec/ansible-collection-hardening | Apache-2.0 | 3102eddbd116c5f8c1581aca543d372dbc326764 | 4 roles, 37 task files, ~217 tasks, 9 handlers | collection, condition/loop-heavy |
| ansible-lockdown/UBUNTU22-CIS | MIT | fad97b54d843eaffc4b7790686cc88bbcbb2330e | 68 task files, ~925 tasks, 40 handlers | too-large graph, include/condition/handler-heavy |
| elastic/ansible-elasticsearch | Apache-2.0 | af05c6470ef63337deba7009eec6af3ea05e2193 | 20 task files, ~182 tasks, 2 handlers | legacy syntax (bare include:, no FQCN) |
| openstack/ansible-hardening | Apache-2.0 | 8c3b5fcf06bf8f93f0f275934af40a27ab44431d | 20 task files, ~193 tasks, 8 handlers | condition-heavy, templated includes |

## Detailed candidate profiles

### geerlingguy/ansible-role-docker (simple role)

- URL: https://github.com/geerlingguy/ansible-role-docker
- Pin: master @ 38be616950679548ae0ba8a81ffcceca1b3090bd
- License: MIT (source: `GET /repos/geerlingguy/ansible-role-docker`, 2026-09-12)
- Stats: 2291 stars, pushed 2026-08-18 (source: same endpoint)
- Structure: root-level standalone role. 6 task files
  (`tasks/main.yml`, `setup-Debian.yml`, `setup-RedHat.yml`, `setup-Suse.yml`,
  `docker-compose.yml`, `docker-users.yml`), 1 handler file (2 handlers),
  1 defaults file (~29 top-level keys), 6 vars files, 4 molecule tree paths
  (source: git tree at pinned SHA).
- Markers (raw fetch of all 6 task files + handlers at pinned SHA):
  5 static `include_tasks` (OS setup, compose, users), 2 blocks, 0
  rescue/always, 33 `when` lines, 2 `with_items` lines, 0 `loop:`,
  11 `ansible.builtin.*` FQCN lines, no `collections:` keyword.
- Hypothesis: docsible discovers 6 task files, ~41 tasks, 2 handlers, 5
  include boundaries, 1 defaults file with ~29 variables; the execution graph
  fits a default Mermaid view and `analyze role --output-format json` parses.
- Risks: none significant; the de facto most-cloned reference role, ideal
  baseline for discovery-count calibration.

### geerlingguy/ansible-role-nginx (simple role, OS-split includes)

- URL: https://github.com/geerlingguy/ansible-role-nginx
- Pin: master @ 5ff0b235006390a0d5666fd4cce7477410982cdf
- License: MIT (source: `GET /repos/geerlingguy/ansible-role-nginx`)
- Stats: 894 stars, pushed 2026-08-10 (same source)
- Structure: 9 task files (`main.yml` + 7 `setup-<OS>.yml` + `vhosts.yml`),
  3 handlers, 3 templates, 8 vars files, 3 molecule tree paths
  (source: git tree at pinned SHA).
- Markers (raw fetch of all task/handler files): 7 `include_tasks` (static,
  OS-guarded) + 1 `import_tasks` (`vhosts.yml`), 18 `when` lines, 2
  `with_items`, 0 blocks, 0 rescue/always, no FQCN (short module names).
- Hypothesis: docsible discovers 9 task files, ~24 tasks, 3 handlers, 8
  include/import boundaries; short module names (no FQCN) must render without
  crashing.
- Risks: none significant. Overlaps the simple-role category with the docker
  role; keep for the import/include mix and the no-FQCN rendering path.

### geerlingguy/ansible-role-mysql (modular role, legacy loops)

- URL: https://github.com/geerlingguy/ansible-role-mysql
- Pin: master @ 0a0ea6b728120b3ab3918332d9404bb65836834d
- License: MIT (source: `GET /repos/geerlingguy/ansible-role-mysql`)
- Stats: 1130 stars, pushed 2026-07-31 (same source)
- Structure: 10 task files split by concern (`configure.yml`,
  `databases.yml`, `replication.yml`, `secure-installation.yml`, `users.yml`,
  `variables.yml`, `setup-<OS>.yml` x3), 1 handler, 3 templates, 12 vars
  files, defaults with ~63 top-level keys, 4 molecule tree paths
  (source: git tree + raw defaults at pinned SHA).
- Markers (raw fetch of all 10 task files + handlers): 9
  `ansible.builtin.include_tasks` boundaries (static filenames), 1 block,
  38 `when` lines, 11 legacy loop lines (9 `with_items`, 2
  `with_first_found`), 0 modern `loop:`, 49 `ansible.builtin.*` + 2
  `community.mysql.*` FQCN lines.
- Hypothesis: docsible discovers 10 task files, ~52 tasks, 9 include
  boundaries, 1 handler, ~63 defaults variables; `with_items` loop metadata
  renders as loop info on the task nodes.
- Risks: none significant.

### geerlingguy/ansible-role-postgresql (modular role, include+import mix)

- URL: https://github.com/geerlingguy/ansible-role-postgresql
- Pin: master @ 53abdf144de8231b2f2ce0652523eebc3eda7100
- License: MIT (source: `GET /repos/geerlingguy/ansible-role-postgresql`)
- Stats: 655 stars, pushed 2026-09-08 (same source)
- Structure: 10 task files, 1 handler, 2 templates, 27 vars files
  (per-distribution/version), defaults with ~16 top-level keys, 3 molecule
  tree paths (source: git tree at pinned SHA).
- Markers (raw fetch of all 10 task files + handlers): 6 `include_tasks`
  (OS setup) + 3 `import_tasks` (`users.yml`, `databases.yml`,
  `users_props.yml`), 21 `when` lines, 9 `with_items`, 0 blocks.
- Hypothesis: docsible discovers 10 task files, 27 vars files, 6 include + 3
  import boundaries; the variables table handles a 27-file vars directory
  without truncation errors.
- Risks: overlaps mysql (same author, same loop style). Kept because the
  import/include mix and vars-file count differ materially.

### nginx/ansible-role-nginx (modular role, handler-heavy, dynamic include)

- URL: https://github.com/nginx/ansible-role-nginx
  (successor of the moved `nginxinc/ansible-role-nginx`; source:
  `GET /repositories/117019566` returned `nginx/ansible-role-nginx`)
- Pin: main @ 157e0e97406f798bd6f50db37430a78c4269aa92
- License: Apache-2.0 (source: `GET /repositories/117019566` and
  `GET /repos/nginx/ansible-role-nginx`)
- Stats: 704 stars, pushed 2026-09-09, not archived (same source)
- Structure: standalone role with galaxy.yml (published as `nginxinc.nginx`).
  31 task files in nested concern directories (`tasks/agent/`, `config/`,
  `keys/`, `modules/`, `opensource/`, `plus/`, `prerequisites/`, `validate/`),
  1 handler file (8 handlers), 7 defaults files, 6 templates, 66 molecule
  tree paths (source: git tree at pinned SHA).
- Markers (raw fetch of all 31 task files + handlers): 21 `include_tasks`
  including at least one templated filename
  (`include_tasks: "{{ role_path }}/tasks/opensource/install-{{ ansible_facts['os_family'] | lower }}.yml"`)
  that cannot be statically resolved; 38 blocks, 0 rescue/always; 162 `when`
  lines; 8 `loop:` and 0 `with_*`; 28 `notify` lines; 173 `ansible.builtin.*`
  + 51 `community.*` FQCN lines.
- Hypothesis: docsible discovers 31 task files across nested directories,
  ~244 tasks, 8 handlers, 21 include boundaries with at least 1 marked
  dynamic/unresolvable; notify edges connect tasks to 8 handlers.
- Risks: the templated include means the true execution graph is open-ended;
  assertions must accept a dynamic/unknown node rather than a resolved file.

### prometheus-community/ansible (collection, include_role dynamics)

- URL: https://github.com/prometheus-community/ansible
- Pin: main @ e2f46e17d33651c3c09042aaa9c8f29b87a9753f
- License: Apache-2.0 (source: `GET /repos/prometheus-community/ansible`)
- Stats: 577 stars, pushed 2026-09-11, actively maintained (same source)
- Structure: the `prometheus.prometheus` collection. galaxy.yml present;
  25 public roles (`alertmanager`, `node_exporter`, `prometheus`, 22 more)
  plus a hidden `roles/_common` role; 65 role task files, ~383 tasks, 26
  handler files (31 handlers), 25 defaults files, 26 `meta/argument_specs.yml`
  files (one per role plus `_common`), 312 molecule tree paths, 36 templates
  (source: git tree at pinned SHA).
- Markers (raw fetch of all 91 role task/handler files): 36 `include_tasks`;
  100 `ansible.builtin.include_role` lines, all targeting
  `name: prometheus.prometheus._common` with `tasks_from:`
  (`preflight.yml`, `install.yml`, `selinux.yml`); 23 blocks, 0 rescue/always;
  162 `when` lines; 9 `loop:` + 7 `with_*` lines (5 `with_items`, 1
  `with_fileglob`, 1 `with_dict`); 25 `notify` lines; 419
  `ansible.builtin.*` FQCN lines.
- Hypothesis: `docsible scan collection .` discovers 25 roles (or 26 if
  `_common` is counted — first calibration run must pin which number is
  correct and record it as the assertion); `document role --collection`
  produces per-role output; every role has argument_specs metadata; the 100
  `include_role` boundaries are marked dynamic or resolved to `_common`
  tasks_from targets.
- Risks: `_common` is underscore-prefixed internal content; whether docsible
  counts it is exactly the kind of contract the harness should pin. Very
  active repo — re-pin SHA for each harness run.

### dev-sec/ansible-collection-hardening (collection, condition/loop-heavy)

- URL: https://github.com/dev-sec/ansible-collection-hardening
- Pin: master @ 3102eddbd116c5f8c1581aca543d372dbc326764
- License: Apache-2.0 (source: `GET /repos/dev-sec/ansible-collection-hardening`)
- Stats: 5470 stars, pushed 2026-09-08 (same source)
- Structure: the `devsec.hardening` collection. galaxy.yml present; 4 roles
  (`mysql_hardening`, `nginx_hardening`, `os_hardening`, `ssh_hardening`);
  37 role task files, ~217 tasks, 4 handler files (9 handlers), 24 templates,
  30 role vars files, argument_specs in all 4 roles, 79 molecule tree paths
  (source: git tree at pinned SHA).
- Markers (raw fetch of all 41 role task/handler files): 11 `include_tasks`
  + 22 `import_tasks`; 6 blocks, 0 rescue/always; 143 `when` lines; 29
  modern `loop:` + 14 legacy `with_*` lines including 4
  `with_community.general.flattened` (FQCN lookup loop), 4 `with_dict`, 3
  `with_first_found`, 2 `with_items`, 1 `with_subelements`; 2 `loop_var`
  usages; 20 `notify` lines; 200 `ansible.builtin.*` + 9 `community.*` FQCN
  lines.
- Hypothesis: docsible discovers 4 roles, each with argument_specs; 22
  import + 11 include boundaries; `loop_var` metadata appears on at least 2
  tasks; both modern `loop:` and legacy `with_*` render as loop info.
- Risks: none significant. The only shortlist repo exercising `loop_var`,
  `with_subelements`, and FQCN-prefixed lookup loops.

### ansible-lockdown/UBUNTU22-CIS (too-large graph, include/condition/handler-heavy)

- URL: https://github.com/ansible-lockdown/UBUNTU22-CIS
- Pin: devel @ fad97b54d843eaffc4b7790686cc88bbcbb2330e
  (note: default branch is `devel`, not main/master)
- License: MIT (source: `GET /repos/ansible-lockdown/UBUNTU22-CIS` says MIT;
  verified against raw
  `https://raw.githubusercontent.com/ansible-lockdown/UBUNTU22-CIS/fad97b54d843eaffc4b7790686cc88bbcbb2330e/LICENSE`,
  "MIT License, Copyright (c) 2026 MindPoint Group - A Tyto Athene Company /
  Ansible Lockdown")
- Stats: 257 stars, pushed 2026-08-25 (same API source)
- Structure: root-level standalone role. 68 task files: 11 directly under
  `tasks/` (`main.yml`, `prelim.yml`, `post.yml`, audit plumbing) plus 57
  nested under `tasks/section_1/` .. `tasks/section_7/`; 1 handler file with
  40 handlers; `defaults/main/` is a directory (`main.yml` ~532 top-level
  keys plus `audit.yml`); 42 templates; 13 molecule tree paths (source: git
  tree at pinned SHA; defaults keys counted from raw fetch).
- Markers (raw fetch of all 68 task files + handlers): 95 `import_tasks` + 1
  `include_tasks` boundaries; 189 blocks, 0 rescue/always; 826 `when` lines;
  76 `loop:` + ~20 `with_*` lines (17 `with_items`; 3 other matches were
  false positives — see Limitations); 139 `notify` lines (handler chains);
  83 `loop_control: label:` usages; 739 `ansible.builtin.*` + 20
  `community.*` FQCN lines.
- Hypothesis: docsible discovers 68 task files, ~925 tasks, 40 handlers, 96
  import/include boundaries; `document role --graph` and `analyze role`
  must complete without crashing and the JSON `truncated` field or diagram
  simplification must engage for a graph of this size; a default Mermaid
  view of ~925 nodes is intentionally too large and is the stress case for
  the "too large for default Mermaid" requirement.
- Risks: benchmark roles are restructured frequently between benchmark
  releases — pin strictly by SHA. Destructive remediation content
  (auditd, PAM, SSH changes) is irrelevant to static analysis but the
  harness must never execute it.

### elastic/ansible-elasticsearch (legacy syntax: bare include:, no FQCN)

- URL: https://github.com/elastic/ansible-elasticsearch
- Pin: main @ af05c6470ef63337deba7009eec6af3ea05e2193
- License: Apache-2.0 (source: raw
  `https://raw.githubusercontent.com/elastic/ansible-elasticsearch/main/LICENSE`;
  the API license field reports NOASSERTION/"Other" — see Limitations)
- Stats: 1588 stars, archived, last push 2022-06-24 (source:
  `GET /repos/elastic/ansible-elasticsearch`)
- Structure: root-level standalone role. 20 task files: 14 directly under
  `tasks/` plus 6 nested under `tasks/xpack/` and `tasks/xpack/security/`;
  1 handler file (2 handlers); 7 templates; defaults with ~62 top-level
  keys; 3 vars files; no molecule (source: git tree + raw fetch at pinned
  SHA).
- Markers (raw fetch of all 20 task files + handlers): 19 legacy bare
  `include:` statements (static filenames, no `include_tasks`/
  `import_tasks`); 0 FQCN anywhere (pre-2.10 short module names); 24 legacy
  loop lines (22 `with_items`, 2 `with_fileglob`); 6 blocks; 142 `when`
  lines; 17 `notify` lines.
- Hypothesis: docsible parses the legacy `include:` keyword as an include
  boundary (19 boundaries), renders short module names without crashing,
  and discovers 20 task files including the nested `xpack/security/`
  subtree.
- Risks: archived since 2022 — acceptable because the pinned SHA is
  immutable and the corpus value is the legacy syntax coverage, but it will
  never receive fixes; if the harness needs a maintained legacy-style role,
  none was found during screening (see Limitations).

### openstack/ansible-hardening (condition-heavy, templated includes)

- URL: https://github.com/openstack/ansible-hardening
- Pin: master @ 8c3b5fcf06bf8f93f0f275934af40a27ab44431d
- License: Apache-2.0 (source: `GET /repos/openstack/ansible-hardening`;
  repo is a mirror of opendev.org)
- Stats: 688 stars, pushed 2026-08-27 (same source)
- Structure: root-level standalone role. 20 task files: `tasks/main.yml`,
  `tasks/contrib/main.yml`, and 18 files under `tasks/rhel7stig/`; 1 handler
  file (8 handlers); 13 templates; 5 vars files (`main`, `debian`,
  `redhat-8/9/10`) (source: git tree at pinned SHA).
- Markers (raw fetch of all 20 task files + handlers): 13 `import_tasks` +
  4 `include_tasks`, of which two have templated, statically unresolvable
  filenames: `ansible.builtin.import_tasks: "{{ stig_version }}stig/main.yml"`
  and `ansible.builtin.include_tasks: "{{ ansible_facts['pkg_mgr'] }}.yml"`;
  8 blocks; 201 `when` lines; 20 legacy loop lines (19 `with_items`, 1
  `with_nested`); 1 modern `loop:`; 20 `notify` lines; 187
  `ansible.builtin.*` FQCN lines.
- Hypothesis: docsible discovers 20 task files, ~193 tasks, 8 handlers, 17
  include/import boundaries of which exactly 2 are marked dynamic/
  unresolvable; the graph renders conditional branches rather than
  pretending all paths execute.
- Risks: `{{ stig_version }}` resolves to `rhel7stig` in practice via
  vars/defaults, so a smarter future analyzer could resolve it; the
  assertion should be "completes and marks it dynamic or resolves it via
  defaults", not a hard failure either way.

## Rejected candidates and why

- ansible-collections/community.general (GPL-3.0-or-later, 1068 stars).
  No `roles/` directory — top-level content is plugins, tests, docs, meta,
  changelogs (source: repository file listing fetched from
  https://github.com/ansible-collections/community.general on 2026-09-12;
  API license field GPL-3.0). Docsible needs roles; a module-only collection
  exercises no role-documentation behavior.
- ansible-collections/kubernetes.core (GPL-3.0, 261 stars). Same reason,
  verified harder: full git tree at head
  a7922e498ca8fa62aef89b47174868f0d8d0ae7d (810 entries) contains 22
  `plugins/modules/*.py` and zero `roles/` paths (source:
  `GET /git/trees/...?recursive=1`). License verified from raw `LICENSE`
  (GPL-3.0 text; API field said NOASSERTION).
- ansible-collections/community.docker, ansible-collections/ansible.posix,
  ansible-collections/community.postgresql. No `roles/` paths found in the
  repository file listings (HTML payload grep of each repo page,
  2026-09-12). ansible.posix and community.postgresql licenses verified
  from raw `COPYING` files as GPL-3.0 (API fields said NOASSERTION).
- nginxinc/ansible-role-nginx. HTTP 301 "Moved Permanently" (source:
  `GET /repos/nginxinc/ansible-role-nginx` returned a redirect to
  `/repositories/117019566`, which resolves to `nginx/ansible-role-nginx`).
  The successor repo is shortlisted.
- cloudalchemy/ansible-prometheus (MIT, 1114 stars). Archived 2023-03-06
  (source: `GET /repos/cloudalchemy/ansible-prometheus`). Its exporter roles
  were migrated into prometheus-community/ansible, which is shortlisted;
  keeping both would duplicate the same role families.
- atosatto/ansible-role-elasticsearch. 404 Not Found (source:
  `GET /repos/atosatto/ansible-role-elasticsearch`). Renamed or removed.
- mongo_single. Could not be identified as a well-known public Ansible role.
  GitHub search `q=mongo_single in:name` returned only unrelated JavaScript
  coursework repositories and unlicensed personal projects (source:
  `GET /search/repositories?q=mongo_single+in:name`, 2026-09-12). Rejected
  as unverifiable rather than risk an unmaintained, unlicensed corpus entry.
- geerlingguy docker_ce collection. Does not exist under that name. Search
  `q=docker_ce user:geerlingguy` returns only `docker-centos6/7/8-ansible`
  playbook repos (source: `GET /search/repositories?q=docker_ce+user:geerlingguy`).
- geerlingguy/ansible-role-jenkins (MIT, 851 stars, active; source:
  `GET /repos/geerlingguy/ansible-role-jenkins`). Screened but not
  shortlisted: the handler-heavy and modular categories are already covered
  by stronger anchors, and the corpus budget is 10.
- elastic/ansible-elasticsearch was nearly rejected for archival but kept
  deliberately: it is the only screened repo still using the legacy bare
  `include:` keyword, zero FQCN, and `with_items` loops throughout. Pinned
  SHAs are immutable, so archival is acceptable for a static-analysis corpus.

## Evaluation harness proposal

Sibling repository `docsible-evaluation` (outside this repo and the
`docsible/` package), per the location decision in the recommendation doc.
It contains only: a pinned corpus manifest, a runner script, and recorded
results. No third-party source is committed.

Pinned manifest (YAML, one file per candidate or a single corpus file):

```yaml
- id: ubuntu22-cis
  url: https://github.com/ansible-lockdown/UBUNTU22-CIS
  sha: fad97b54d843eaffc4b7790686cc88bbcbb2330e
  license: MIT
  kind: role
  path: .
  categories: [too-large-graph, include-heavy, condition-heavy, handler-heavy]
  features: [import_tasks, include_tasks, blocks, when, loop, with_items, notify, loop_control]
  hypotheses:
    - command: docsible analyze role --role . --output-format json
      asserts:
        - exit_code: 0
        - json_parses: true
        - json_schema: [role, findings, summary, truncated]
        - task_files_discovered: 68
        - handlers_discovered: 40
        - include_boundaries: 96
        - tasks_discovered: {min: 850, max: 1000}
        - no_mutation: git-status-empty
  notes: default branch is devel; pin by SHA only
```

Two-stage selection (as proven during this research):

1. Screening without cloning: `GET /repos/OWNER/REPO`,
   `GET /repos/OWNER/REPO/git/trees/HEAD?recursive=1`, plus raw fetches of
   representative task files to confirm structural markers. Unauthenticated
   API allows ~20 screened repos per hour per IP (60 requests); a CI token
   raises this to 5000/h but manual local runs should work unauthenticated
   with cached metadata.
2. Pinned evaluation checkout: `git fetch --depth 1 origin <sha>` into a
   `mktemp` directory, checkout `FETCH_HEAD`, run docsible commands, assert,
   delete. Never execute playbooks, repo scripts, or CI configs from the
   corpus. Never commit corpus code.

Assertion types:

- Command completes: exit code 0, no traceback, for `analyze role`,
  `validate role`, `scan collection`, and `document role --dry-run`.
- No mutation: after every read-only command, `git status --porcelain` in
  the cloned tree must be empty. For `document role` (writes README), assert
  only expected output files change and that `--no-backup` / backup behavior
  matches documented flags.
- JSON validity: `--output-format json` parses and conforms to the
  documented schema (`role`, `findings[]`, `summary{total, critical,
  warning, info}`, `truncated`).
- Discovery counts match hypotheses: exact counts where the parser contract
  is unambiguous (files, handlers), tolerant ranges where grep-vs-parser
  semantics differ (task counts; see Limitations). First run against each
  candidate is a calibration run: record actuals, then freeze them as
  assertions so the harness is not a generic no-crash test.
- Markdown exists and validates: `document role` produces a README that
  passes `validate role --strict-validation`.
- Graph behavior: for UBUNTU22-CIS, the graph path must complete and engage
  truncation/simplification for ~925 tasks; assert completion and valid
  JSON, not an exact node count.

Cadence: run manually, nightly, and before releases in the sibling repo.
Never on normal docsible PRs; never as a gate that depends on public network
availability.

Human value evaluation sketch: 4-6 engineers, two corpus roles (one simple,
e.g. docker; one unfamiliar and complex, e.g. a UBUNTU22-CIS section or
devsec os_hardening). Each answers the philosophy-doc questions (what does
this role install/configure; which variables matter; which files and
handlers are involved; which paths are static, conditional, dynamic) under
two conditions: repository only, then repository plus docsible outputs.
Measure completion time, answer accuracy (scored against the pinned SHA's
actual structure), and self-reported confidence. A compact scorecard per
participant per role is enough; no tooling required beyond a timer.

## Limitations encountered during research

- GitHub API rate limit: never hit the wall, but the budget shaped the
  method. Final state per response header `x-ratelimit-remaining`: 18 of 60
  unauthenticated core requests left (42 used) at the end of research on
  2026-09-12. Screening was therefore capped at ~18 metadata fetches plus
  11 commit/tree pairs; every response was cached to disk so no call was
  repeated. The harness should assume the same 60/h constraint for manual
  runs.
- API license field is unreliable and must be verified against raw LICENSE
  files: community.postgresql, ansible.posix, and kubernetes.core report
  NOASSERTION but ship GPL-3.0 `COPYING`/`LICENSE` text; elastic/ansible-
  elasticsearch reports NOASSERTION/"Other" but its LICENSE is Apache-2.0.
  All license claims in this file state their source for this reason.
- Moved and dead repositories: nginxinc/ansible-role-nginx returns 301
  (moved to nginx/ansible-role-nginx); atosatto/ansible-role-elasticsearch
  returns 404. Repos can move between screening and harness execution — the
  manifest should store the resolved owner/name plus SHA, and the runner
  should fail loudly on redirects rather than follow them silently.
- Unverifiable candidate names from the original request: mongo_single could
  not be matched to any well-known, licensed Ansible role (GitHub name
  search returns unrelated JavaScript coursework); the geerlingguy
  "docker_ce" collection does not exist under that name (only stale
  docker-centos6/7/8-ansible playbook repos). Both were rejected rather
  than guessed at.
- Grep-based marker counts have known error modes observed in this corpus:
  `with_cves` matched a filename (`fs_with_cves.sh`) and `with_efi` matched
  a variable (`booted_with_efi`) in UBUNTU22-CIS / openstack/ansible-
  hardening, inflating naive `with_` counts by 5 lines total. Counts are
  line counts, not occurrence counts: multiline `when` conditions and
  folded tasks are counted once per line, and nameless tasks (common in
  legacy-style roles) are excluded from `- name:` task counts, so task
  totals are lower bounds. The harness must parse YAML rather than grep;
  grep numbers in this file are screening estimates, good enough for
  hypotheses but not for exact assertions.
- Category gap: no shortlisted repo uses `rescue:` or `always:` (0
  occurrences across all 296 fetched task files), despite block/rescue/
  always being a target marker. The shortlist exercises plain blocks (189
  in CIS, 38 in the nginx role) but not error-handling flows. A future
  corpus revision should add a block/rescue/always-heavy role; none was
  found among the recommended families during this screening round.
- The legacy `collections:` keyword is absent from all shortlisted repos
  (0 occurrences), so the corpus cannot assert anything about it.
- elastic/ansible-elasticsearch is archived (last push 2022-06-24). Kept
  deliberately for its unique legacy syntax (bare `include:`, zero FQCN),
  accepting that it will never be updated; no maintained replacement with
  the same syntax profile was identified during screening.
- ansible-lockdown/UBUNTU22-CIS defaults to branch `devel`, not main/
  master. Screening tooling that assumes main/master would misresolve it;
  pin by SHA everywhere. Lockdown licenses also vary per benchmark repo
  over time (UBUNTU22-CIS is MIT today; other lockdown repos historically
  GPL-3.0) — verify per repo when extending the corpus.
- Destructive automation concern: hardening roles (CIS, devsec, openstack)
  contain destructive remediation tasks (auditd, PAM, SSH). The harness is
  static-analysis-only and must never execute corpus playbooks, which
  contains this risk; no embedded credentials were observed in the fetched
  task files, but no dedicated secret scan was performed and the harness
  should not assume it.
- All 11 git trees returned `truncated: false` (largest: 984 entries for
  prometheus-community/ansible), so tree-derived file counts are complete.
  Repos exceeding the tree API size/entry limits would truncate; not hit
  during this research, but the harness should assert on the `truncated`
  field rather than assume completeness.

## Research log

Date: 2026-09-12. All calls made unauthenticated from this workstation;
responses cached under the session temp directory during research.

GitHub REST API (core quota, limit 60/h):

- `GET /rate_limit` x5 (free; does not consume quota) — final reading
  `used=42 remaining=18`.
- `GET /repos/{owner}/{repo}` x19: geerlingguy/ansible-role-{docker,nginx,
  mysql,postgresql,jenkins}, ansible-collections/{community.general,
  community.docker, community.postgresql, ansible.posix, kubernetes.core},
  prometheus-community/ansible, dev-sec/ansible-collection-hardening,
  elastic/ansible-elasticsearch, ansible-lockdown/UBUNTU22-CIS,
  openstack/ansible-hardening, nginxinc/ansible-role-nginx (301),
  atosatto/ansible-role-elasticsearch (404), nginx/ansible-role-nginx.
- `GET /repos/{owner}/{repo}/commits/{branch}` x11 (head SHAs for the ten
  shortlist repos plus the nginx role).
- `GET /repos/{owner}/{repo}/git/trees/{sha}?recursive=1` x11 (all
  `truncated: false`).
- `GET /repositories/117019566` x1 (resolved the nginxinc 301 redirect to
  nginx/ansible-role-nginx).

GitHub search API (separate quota): `GET /search/repositories` x2
(`mongo_single in:name`; `docker_ce user:geerlingguy`).

Raw fetches (raw.githubusercontent.com, not rate limited): 296 task/handler
YAML files pinned at the SHAs in the candidate table (docker 7, geerlingguy
nginx 10, mysql 11, postgresql 11, nginx role 32, prometheus 91, devsec 41,
UBUNTU22-CIS 69, elastic 21, openstack 21), plus 5 LICENSE/COPYING
verifications and 5 defaults-file fetches. Zero raw fetch failures.

Failures and interventions: two dead/moved repos (301 nginxinc, 404
atosatto) handled by redirect resolution and rejection; one local tooling
error (xargs invocation too long during the raw-fetch loop, fixed by
switching to a two-column URL/destination pairs file); no HTTP 403/429 and
no tree truncation at any point.
