# Project State

This file stores stable facts for the current ADT governance candidate. Current
Base, Head, event SHA, remote refs, changed files, PR state, CI state, and the
candidate hash are resolved live and are not durable fields in this record.

```yaml
schema_version: "2"
task_id: ADT-EXTERNAL-BOOTSTRAP-ACTIVATION-R1
repository: butbutbutbutbutbut/adaptive-digital-team
branch: hermes/adt-external-bootstrap-activation-r1
starting_base_sha: c4b7dcc079a764a1e76012428536ac3c37549be5
authorized_write_scope:
  - AGENTS.md
  - BOOTSTRAP.md
  - PROJECT_STATE.md
  - README.md
  - protocols/BEGINNER_BOOTSTRAP_ROUTER.md
  - tests/test_beginner_bootstrap.py
  - tests/test_binding_validation.py
  - 中文内容/README.md
authority:
  holder: HE-WEIZHI
  maker: HERMES_TEMPORARY_MAKER
  checker: PENDING_INDEPENDENT_CHECKER
current_gate: DRAFT_PR
implementation_status: IN_PROGRESS
phase: P0_CONTINUING_MAINTENANCE
summary: >
  External bootstrap activation semantic repair — corrected approach.
  Product goal: READ_ACTIVATES_PROTOCOL. Any interactive AI reading the
  repository enters ADT_PROTOCOL_ACTIVE with ANDING_INTERFACE assigned.
  Authority (write/Ready/Merge/Control) remains UNGRANTED.
  ANDING_INTERFACE ≠ ANDING_CONTROL.
  P1–P5 remain NOT_AUTHORIZED.
```

This file does not activate Runtime, Hermes R1, automatic scheduling,
product implementation, Ready, Merge, branch deletion, or final visual or
engineering acceptance.
