# Project State

This file stores stable facts for the current ADT governance candidate. Current
Base, Head, event SHA, remote refs, changed files, PR state, CI state, and the
candidate hash are resolved live and are not durable fields in this record.

```yaml
schema_version: "2"
task_id: ADT-PUBLIC-CORE-REMEDIATION-R1
repository: butbutbutbutbutbut/adaptive-digital-team
branch: hermes/adt-public-core-remediation-r1
starting_base_sha: c8a6577bb89073e1ceb0056641ec288c6eb3792d
authorized_write_scope:
  - LICENSE
  - README.md
  - CONTRIBUTING.md
  - SECURITY.md
  - CODE_OF_CONDUCT.md
  - .gitignore
  - config.example.yaml
  - docs/PUBLIC_CORE_OPS_SECRETS_BOUNDARY.md
  - scripts/validate_binding.py
  - tests/test_binding_validation.py
  - .github/workflows/validate.yml
  - PROJECT_STATE.md
authority:
  authorization_id: ADT-PUBLIC-CORE-REMEDIATION-20260721-001
  holder: HUMAN_HOLDER
  maker: SOLE_MAKER
  checker: EXTERNAL_INDEPENDENT_GOVERNANCE_CHECKER
  pr_creation: AUTHORIZED
  ready: HUMAN_ONLY
  merge: HUMAN_ONLY
current_gate: IMPLEMENTATION
implementation_status: NOT_AUTHORIZED
```
