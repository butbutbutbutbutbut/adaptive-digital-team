# Project State

This file stores durable project state for ADT governance. Per-candidate
transient facts (branch, Base SHA, authorized write scope, authorization ID,
task ID) are now held in `.hermes/CANDIDATE_BINDING.json`. Live facts (Head,
main, CI state, remote refs, changed files, PR state) are resolved at every
gate and are never durable fields in this record.

```yaml
schema_version: "2"
repository: butbutbutbutbutbut/adaptive-digital-team
authority:
  holder: HE-WEIZHI
  maker: HERMES_TEMPORARY_TASK_HOLDER-003
  checker: PENDING_INDEPENDENT_CHECKER
current_gate: MAKER_IMPLEMENTATION
implementation_status: IN_PROGRESS
system_next_step: COMMIT_PUSH_DRAFT_PR
summary: >
  Elevate Runtime Adapter Contract from CANDIDATE to ADOPTED status.
  Protocol implemented, independently audited (12/12 PASS), and merged
  via PR #46. This task changes adoption status only — no semantic,
  implementation, schema, or test changes.
```

This file does not activate Runtime, Hermes R1, automatic scheduling,
product implementation, Ready, Merge, branch deletion, or final visual or
engineering acceptance.
