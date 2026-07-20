# Project State

This file stores stable facts for the current ADT governance candidate. Current
Base, Head, event SHA, remote refs, changed files, PR state, CI state, and the
candidate hash are resolved live and are not durable fields in this record.

```yaml
schema_version: "2"
task_id: ADT-BEGINNER-BOOTSTRAP-R1
repository: butbutbutbutbutbut/adaptive-digital-team
branch: hermes/adt-beginner-bootstrap-r1
starting_base_sha: daddf4a7ad073d80474d8e99038cf1d8e6b6475c
authorized_write_scope:
  - README.md
  - AGENTS.md
  - protocols/BEGINNER_BOOTSTRAP_ROUTER.md
  - tests/test_beginner_bootstrap.py
  - PROJECT_STATE.md
authority:
  authorization_id: ADT-BEGINNER-BOOTSTRAP-R1
  holder: HUMAN_HOLDER
  maker: SOLE_MAKER
  checker: EXTERNAL_INDEPENDENT_GOVERNANCE_CHECKER
  pr_creation: AUTHORIZED
  ready: HUMAN_ONLY
  merge: HUMAN_ONLY
current_gate: IMPLEMENTATION
implementation_status: NOT_AUTHORIZED
```
