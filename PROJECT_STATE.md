# Project State

This file stores stable facts for the current ADT governance candidate. Current
Base, Head, event SHA, remote refs, changed files, PR state, CI state, and the
candidate hash are resolved live and are not durable fields in this record.

```yaml
schema_version: "2"
task_id: ADT-BEGINNER-BOOTSTRAP-R1
repository: butbutbutbutbutbut/adaptive-digital-team
branch: hermes/adt-beginner-bootstrap-clean-r1
starting_base_sha: daddf4a7ad073d80474d8e99038cf1d8e6b6475c
authorized_write_scope:
  - AGENTS.md
  - PROJECT_STATE.md
  - README.md
  - protocols/BEGINNER_BOOTSTRAP_ROUTER.md
  - tests/test_beginner_bootstrap.py
  - tests/test_binding_validation.py
  - 中文内容/README.md
authority:
  holder: HE-WEIZHI
  maker: HERMES_TEMPORARY_GOVERNANCE_MAKER
  checker: EXTERNAL_INDEPENDENT_GOVERNANCE_CHECKER-024
current_gate: FINAL_CANDIDATE_FREEZE
implementation_status: NOT_AUTHORIZED
```

This file does not activate Runtime, Hermes R1, automatic scheduling,
product implementation, Ready, Merge, branch deletion, or final visual or
engineering acceptance.
