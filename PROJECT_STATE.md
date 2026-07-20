# Project State

This file stores stable facts for the current ADT governance candidate. Current
Base, Head, event SHA, remote refs, changed files, PR state, CI state, and the
candidate hash are resolved live and are not durable fields in this record.

```yaml
schema_version: "2"
task_id: ADT-ROADMAP-P0-P5-R1
repository: butbutbutbutbutbut/adaptive-digital-team
branch: hermes/adt-roadmap-p0-p5-r1
starting_base_sha: c8a6577bb89073e1ceb0056641ec288c6eb3792d
authorized_write_scope:
  - docs/ADT_ROADMAP_P0_P5.md
  - AGENTS.md
  - PROJECT_STATE.md
  - scripts/validate_binding.py
  - tests/test_binding_validation.py
  - tests/run_tests.py
  - protocols/LIGHTWEIGHT_EXECUTION_FLOW.md
  - protocols/PERSISTENT_HOLDER_CONTROL_PLANE.md
authority:
  authorization_id: ADT-ROADMAP-P0-P5-20260721-002
  holder: HUMAN_HOLDER
  maker: SOLE_MAKER
  checker: EXTERNAL_INDEPENDENT_GOVERNANCE_CHECKER
  pr_creation: AUTHORIZED
  ready: HUMAN_ONLY
  merge: HUMAN_ONLY
current_gate: EXTERNAL_INDEPENDENT_GOVERNANCE_AUDIT
roadmap_status: CANDIDATE
implementation_status: NOT_AUTHORIZED
```
