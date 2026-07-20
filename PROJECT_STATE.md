# Project State

This file stores stable facts for the current ADT governance candidate. Current
Base, Head, event SHA, remote refs, changed files, PR state, CI state, and the
candidate hash are resolved live and are not durable fields in this record.

```yaml
schema_version: "2"
task_id: ADT-REMOTE-CANDIDATE-HISTORY-IMMUTABILITY-R1
repository: butbutbutbutbutbut/adaptive-digital-team
branch: hermes/adt-remote-history-immutability-r1
starting_base_sha: 74c596bbc97288f3b84f1d57cf4bed035250cbc7
authorized_write_scope:
  - .github/workflows/validate.yml
  - scripts/validate_binding.py
  - scripts/validate_candidate_history.py
  - tests/test_binding_validation.py
  - tests/test_candidate_history.py
  - tests/run_tests.py
  - protocols/LIGHTWEIGHT_EXECUTION_FLOW.md
  - protocols/PERSISTENT_HOLDER_CONTROL_PLANE.md
  - PROJECT_STATE.md
authority:
  authorization_id: ADT-REMOTE-CANDIDATE-HISTORY-IMMUTABILITY-20260721-001
  stage_2_authorization_id: ADT-REMOTE-CANDIDATE-HISTORY-IMMUTABILITY-STAGE2-20260721-001
  holder: HUMAN_HOLDER
  maker: SOLE_MAKER
  checker: EXTERNAL_INDEPENDENT_GOVERNANCE_CHECKER
  pr_creation: AUTHORIZED
  ready: HUMAN_ONLY
  merge: HUMAN_ONLY
current_gate: IMPLEMENTATION
implementation_status: NOT_AUTHORIZED
```
