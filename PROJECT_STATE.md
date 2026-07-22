# Project State

This file stores stable facts for the current ADT governance candidate. Current
Base, Head, event SHA, remote refs, changed files, PR state, CI state, and the
candidate hash are resolved live and are not durable fields in this record.

```yaml
schema_version: "2"
task_id: ADT-HERMES-RUNTIME-ADAPTER-R1
repository: butbutbutbutbutbut/adaptive-digital-team
branch: hermes/adt-hermes-runtime-adapter-r1
starting_base_sha: 9ec8cc80d6b2b4120100e4751263f833bd12229c
authorized_write_scope:
  - .hermes/plugins/guarded_adapter/__init__.py
  - .hermes/plugins/guarded_adapter/plugin.yaml
  - .hermes/plugins/guarded_adapter/tools/guarded_write.py
  - .hermes/plugins/guarded_adapter/tools/guarded_repo_actions.py
  - .hermes/plugins/guarded_adapter/gate.py
  - .hermes/plugins/guarded_adapter/runtime_models.py
  - tests/test_guarded_adapter_enforcement.py
  - tests/fixtures/adapter_e2e_allowed.txt
  - PROJECT_STATE.md
authority:
  authorization_id: ADT-HERMES-RUNTIME-ADAPTER-20260723-001
  holder: HUMAN_HOLDER
  maker: SOLE_MAKER
  checker: EXTERNAL_INDEPENDENT_GOVERNANCE_CHECKER
  pr_creation: AUTHORIZED
  ready: HUMAN_ONLY
  merge: HUMAN_ONLY
current_gate: IMPLEMENTATION
implementation_status: IN_PROGRESS
---
task_id: ADT-DYNAMIC-MODEL-RESOURCE-ALLOCATION-MVP-R1
repository: butbutbutbutbutbut/adaptive-digital-team
branch: hermes/adt-dynamic-model-resource-allocation-mvp-r1
starting_base_sha: ed648d90bbb230d76b969d28a153ac4a2ce5af5b
authorized_write_scope:
  - scripts/resource_allocator.py
  - schemas/resource-plan.schema.json
  - tests/test_resource_allocator.py
  - tests/fixtures/model-catalog.sample.json
  - PROJECT_STATE.md
authority:
  authorization_id: ADT-DYNAMIC-MODEL-RESOURCE-ALLOCATION-20260723-001
  holder: HUMAN_HOLDER
  maker: XIAOHE_DEPUTY
  checker: EXTERNAL_INDEPENDENT_GOVERNANCE_CHECKER
  pr_creation: DRAFT_ONLY
  ready: HUMAN_ONLY
  merge: HUMAN_ONLY
current_gate: IMPLEMENTATION
implementation_status: IN_PROGRESS
```
