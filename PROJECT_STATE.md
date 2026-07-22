# Project State

This file stores stable facts for the current ADT governance candidate. Current
Base, Head, event SHA, remote refs, changed files, PR state, CI state, and the
candidate hash are resolved live and are not durable fields in this record.

```yaml
schema_version: "2"
task_id: ADT-BOOTSTRAP-ENTRYPOINT-CONSOLIDATION-R1
repository: butbutbutbutbutbut/adaptive-digital-team
branch: hermes/adt-bootstrap-entrypoint-consolidation-r1
starting_base_sha: 708f14bd1dbdbc374b4061182e4b82a086125c51
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
  checker: HERMES_CHECKER (deleg_887cdce4)
current_gate: CHECKER_PASSED_AWAITING_HUMAN_READY
implementation_status: AUDIT_PASSED
summary: >
  ADT Bootstrap Entrypoint Consolidation R1 — unified Human and Agent
  first-entry paths, deduplicated protocol activation and A/B/C routing
  across five entrypoint files. All 158 tests pass. CI green. Independent
  Checker PASS on all C1-C10.
```

This file does not activate Runtime, Hermes R1, automatic scheduling,
product implementation, Ready, Merge, branch deletion, or final visual or
engineering acceptance.
