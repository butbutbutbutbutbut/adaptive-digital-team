# Project State

This file stores stable facts for the current ADT governance candidate. Current
Base, Head, event SHA, remote refs, changed files, PR state, CI state, and the
candidate hash are resolved live and are not durable fields in this record.

```yaml
schema_version: "2"
task_id: ADT-BOOTSTRAP-ENTRYPOINT-CONSOLIDATION-R1
repository: butbutbutbutbutbut/adaptive-digital-team
branch: hermes/adt-bootstrap-entrypoint-consolidation-r1
starting_base_sha: 708f14b9bc7bcd33037c6ac61c5af75d256c1e71
authorized_write_scope:
  - README.md
  - BOOTSTRAP.md
  - AGENTS.md
  - protocols/BEGINNER_BOOTSTRAP_ROUTER.md
  - 中文内容/README.md
  - PROJECT_STATE.md
authority:
  holder: HE-WEIZHI
  task_holder: CURRENT_WINDOW
  maker: CURRENT_WINDOW
  checker: INDEPENDENT_CHECKER
current_gate: MAKER_EXECUTING
implementation_status: IN_PROGRESS
summary: >
  ADT Bootstrap Entrypoint Consolidation R1 — unifies Human and Agent
  first-entry paths, deduplicates protocol activation and A/B/C routing
  across five entrypoint files, establishes single-path routing without
  modifying core methodology, role model, or candidate lifecycle.
```

This file does not activate Runtime, Hermes R1, automatic scheduling,
product implementation, Ready, Merge, branch deletion, or final visual or
engineering acceptance.
