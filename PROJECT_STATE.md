# Project State

This file stores stable facts for the current ADT governance candidate. Current
Base, Head, event SHA, remote refs, changed files, PR state, CI state, and the
candidate hash are resolved live and are not durable fields in this record.

```yaml
schema_version: "2"
task_id: ADT-MODEL-CATALOG-FIXTURE-INTEGRITY-R1
repository: butbutbutbutbutbut/adaptive-digital-team
branch: hermes/adt-model-catalog-fixture-integrity-r1
starting_base_sha: b94c41e8882205592e129d21b826153042b05c0f
authorized_write_scope:
  - scripts/resource_allocator.py
  - schemas/resource-plan.schema.json
  - tests/test_resource_allocator.py
  - tests/fixtures/model-catalog.sample.json
  - PROJECT_STATE.md
authority:
  authorization_id: ADT-MODEL-CATALOG-FIXTURE-INTEGRITY-20260723-001
  holder: HUMAN_HOLDER
  maker: XIAOHE_DEPUTY
  checker: EXTERNAL_INDEPENDENT_GOVERNANCE_CHECKER
  pr_creation: DRAFT_ONLY
  ready: HUMAN_ONLY
  merge: HUMAN_ONLY
current_gate: IMPLEMENTATION
implementation_status: IN_PROGRESS
```
