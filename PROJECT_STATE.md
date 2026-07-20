# Project State

This file stores stable facts for the current ADT governance candidate. Current
Base, Head, event SHA, remote refs, changed files, PR state, CI state, and the
candidate hash are resolved live and are not durable fields in this record.

```yaml
schema_version: "2"
task_id: ADT-PREWRITE-EXECUTION-AND-SCOPE-GATE-HARDENING-R1
repository: butbutbutbutbutbut/adaptive-digital-team
branch: hermes/adt-prewrite-scope-gate-r1
starting_base_sha: 3272a565576ec41db99d427efb9ed687b765ac06
authorized_write_scope:
  - scripts/validate_binding.py
  - tests/test_binding_validation.py
  - tests/run_tests.py
  - protocols/LIGHTWEIGHT_EXECUTION_FLOW.md
  - protocols/PERSISTENT_HOLDER_CONTROL_PLANE.md
  - PROJECT_STATE.md
authority:
  authorization_id: ADT-PREWRITE-SCOPE-GATE-20260721-001
  holder: HUMAN_HOLDER
  maker: SOLE_MAKER
  checker: EXTERNAL_INDEPENDENT_GOVERNANCE_CHECKER
  pr_creation: AUTHORIZED
  ready: HUMAN_ONLY
  merge: HUMAN_ONLY
current_gate: IMPLEMENTATION
implementation_status: NOT_AUTHORIZED
```
