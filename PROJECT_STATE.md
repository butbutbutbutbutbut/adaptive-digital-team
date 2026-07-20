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
roadmap:
  task_id: ADT-ROADMAP-P0-P5-R1
  authorization_id: ADT-ROADMAP-P0-P5-20260721-001
  document: docs/ADT_ROADMAP_P0_P5.md
  version: R1
  status: CANDIDATE_FOR_INDEPENDENT_REVIEW
  phases:
    P0: OPERATIONAL_BASELINE / CONTINUING_MAINTENANCE
    P1: PLANNED / NOT_AUTHORIZED
    P2: PLANNED / NOT_AUTHORIZED
    P3: PLANNED / NOT_AUTHORIZED
    P4: DESIGN_BASELINE_PARTIAL / IMPLEMENTATION_NOT_AUTHORIZED
    P5: PLANNED / NOT_AUTHORIZED
  model_tier:
    control: DeepSeek V4 Pro Max
    primary_maker: DeepSeek V4 Pro
    independent_checker: DeepSeek V4 Pro Max
    subagents: 0
    max_active_agents: 1
```
