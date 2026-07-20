# Project State

This file stores stable facts for the current ADT governance candidate. Current
Base, Head, event SHA, remote refs, changed files, PR state, CI state, and the
candidate hash are resolved live and are not durable fields in this record.

```yaml
schema_version: "2"
task_id: ADT-CANDIDATE-IDENTITY-AND-SINGLE-PR-GATE-R1
repository: butbutbutbutbutbut/adaptive-digital-team
branch: hermes/adt-candidate-identity-single-pr-gate-r1
starting_base_sha: a3d6a7cd15ba057e7d66d30c0f972562e961005c
authorized_write_scope:
  - AGENTS.md
  - protocols/LIGHTWEIGHT_EXECUTION_FLOW.md
  - protocols/PERSISTENT_HOLDER_CONTROL_PLANE.md
  - .github/workflows/validate.yml
  - scripts/validate_binding.py
  - tests/test_binding_validation.py
  - tests/run_tests.py
  - PROJECT_STATE.md
authority:
  authorization_id: ADT-CANDIDATE-IDENTITY-AND-SINGLE-PR-GATE-20260720-001
  holder: HUMAN_HOLDER
  maker: SOLE_MAKER
  checker: EXTERNAL_INDEPENDENT_GOVERNANCE_CHECKER
  pr_creation: AUTHORIZED
  ready: HUMAN_ONLY
  merge: HUMAN_ONLY
current_gate: EXTERNAL_INDEPENDENT_GOVERNANCE_AUDIT
implementation_status: NOT_AUTHORIZED
```
