# Final Receipt — ADT Repository-as-Prompt Runtime Binding R1

TASK_ID: ADT-REPOSITORY-AS-PROMPT-RUNTIME-BINDING-R1
AUTHORIZATION_ID: ADT-REPOSITORY-AS-PROMPT-RUNTIME-BINDING-20260720-001
REPOSITORY: butbutbutbutbutbut/adaptive-digital-team
EXECUTOR: Xiaohe (Hermes Agent, single-writer Maker)

## Execution Summary

| Field | Value |
|-------|-------|
| BASE_SHA (origin/main at start) | `8d343f26dfc9f29422b448705bf85e6f0be37362` |
| WORKING_BRANCH | `hermes/adt-repository-as-prompt-runtime-binding-r1` |
| HEAD_SHA | `b5818cdaac37b5bb33e96e0907dbb16ef7b59975` |
| DRAFT_PR | [#21](https://github.com/butbutbutbutbutbut/adaptive-digital-team/pull/21) |
| PRODUCT_REPOSITORY_WRITE | FORBIDDEN — none performed |
| ORIGIN_MAIN_MODIFIED | NO |
| FORCE_PUSH / REBASE / AMEND | NONE |

## Files Changed (9 files, +1706/-1)

| # | File | Change | Lines |
|---|------|--------|-------|
| 1 | `protocols/REPOSITORY_AS_PROMPT_RUNTIME_BINDING.md` | NEW | +427 |
| 2 | `AGENTS.md` | MODIFIED | +98 |
| 3 | `protocols/PERSISTENT_HOLDER_CONTROL_PLANE.md` | MODIFIED | +68 |
| 4 | `protocols/LIGHTWEIGHT_EXECUTION_FLOW.md` | MODIFIED | +36 |
| 5 | `PROJECT_STATE.md` | EXTENDED | +90/-1 |
| 6 | `scripts/validate_binding.py` | NEW | +285 |
| 7 | `tests/test_binding_validation.py` | NEW | +347 |
| 8 | `tests/run_tests.py` | NEW | +304 |
| 9 | `.github/workflows/validate.yml` | NEW | +52 |

## Existing Protocol Reuse

| Requirement | Existing Protocol | Action |
|-------------|------------------|--------|
| Startup sequence | `BOOTSTRAP.md`, `AGENTS.md` | Extended in AGENTS.md § Repository as Prompt; full protocol in new binding doc |
| Routing / dispatch | `PERSISTENT_HOLDER_CONTROL_PLANE.md` | Added fact-source resolution, FACT_SOURCE_REBIND, pre-counter-objective check |
| Efficiency / drift | `LIGHTWEIGHT_EXECUTION_FLOW.md` | Added delta-only prompt, drift trigger rules |
| Counter-objective governance | `ADAPTIVE_COUNTER_OBJECTIVE_GOVERNANCE.md` | Pre-counter-objective check added to Holder; protocol unchanged |
| Human-facing interface | `AGENTS.md` § Human-facing control-plane interface | Added 9-line card format, BLACKBOX_STATUS: PROHIBITED |
| Conceptual principle | `docs/REPOSITORY_AS_PROMPT_PRINCIPLE_R1.md` | Operational implementation created; principle doc unchanged |

No parallel system created. All changes extend existing protocols.

## New Protocol: REPOSITORY_AS_PROMPT_RUNTIME_BINDING.md

Created because existing docs (`docs/REPOSITORY_AS_PROMPT_PRINCIPLE_R1.md`, `docs/ADAPTIVE_DIGITAL_TEAM_REPOSITORY_PROPOSAL_R1.md`) are conceptual proposals (status: `READY_FOR_INDEPENDENT_REVIEW`), not operational protocols. The new protocol is the execution layer.

### Key features:

1. **Single Authoritative Fact Source** (§1) — Binding model with fact-source priority (5=Human explicit, 1=main/governance only)
2. **Mandatory Startup Protocol** (§2) — 8-step sequence; FACT_SOURCE_REBIND on conflict
3. **Delta-Only Prompt** (§3) — Repository carries stable context; chat carries only TASK_ID + user delta
4. **9-Line Progress Card** (§4) — Default format; extended fields only on HARD_STOP; BLACKBOX prohibited
5. **Pre-Counter-Objective Gate** (§5) — 7 questions before any action; REJECT if GOVERNANCE_COST > PRODUCT_OR_SAFETY_VALUE
6. **Candidate Publication Contract** (§6) — candidate_status, visual_status, comparison_group, supersedes
7. **Session Drift Control** (§7) — Full startup only on 6 triggers; delta-only for same-task iteration
8. **Integration** (§8) — Extends Holder, Lightweight Flow, Counter-Objective Governance, Bootstrap
9. **Validation** (§9) — 10 rules enforced by scripts/validate_binding.py
10. **A/B Incident Replay** (§10) — Acceptance test: Version A selected, PR#35/R2/main rejected

## Binding Schema Extension (PROJECT_STATE.md)

Extended from 20 legacy fields to include:

```yaml
schema_version, adt_repository, adt_pin
governance_base: {branch, sha}
authoritative_fact_source: {type, evidence, branch, sha}
product_repository
active_candidate: {branch, resolved_head, status}
comparison_candidates: [{branch, resolved_head, status, comparison_group}]
historical_references: [{branch, sha, role}]
invalidated_candidates: [{branch, sha, invalidation_reason}]
current_gate
visual_status: {active_candidate}
authorized_action, authorized_write_scope
counter_objectives: [...]
progress: {completed, total, display}
user_action_required, system_next_step, last_verified_at
```

## Fact-Source Priority

| Priority | Source | Condition |
|----------|--------|-----------|
| 5 (highest) | Human explicit branch+SHA | Persisted at next authorized write |
| 4 | Active candidate in binding | resolved_head matches live remote |
| 3 | Open PR with Human binding | PR description/commit contains declaration |
| 2 | Branch HEAD with ADT binding | Tip commit contains .adt/project-binding.yaml |
| 1 (lowest) | main | Governance only; NOT product source |

## Drift Triggers (Full Startup Required)

- New window
- New task
- Fact conflict
- Human new candidate receipt
- Binding SHA change
- Current gate change

## Counter-Objective Check (Pre-Action)

1. Does this directly increase product value?
2. Does this increase candidate count?
3. Does this create competing fact source?
4. Does this duplicate existing branch capability?
5. Can this be folded into next product task?
6. Is this formally correct but unnecessary?
7. Does this increase user comprehension burden?

Reject if GOVERNANCE_COST > PRODUCT_OR_SAFETY_VALUE.

## Nine-Line Card and BLACKBOX

Default output:
```text
TASK: / STATUS: / FACT_SOURCE: / ACTIVE_BASELINE: / PROGRESS:
ACTION: / FILES_TOUCHED: / NEXT_GATE: / USER_ACTION_REQUIRED:
```

BLACKBOX_STATUS: PROHIBITED — "处理中", "系统状态延迟", "已完成" without SHA+action+file evidence are forbidden.

## A/B Incident Replay Result

```
GIVEN:  PR #35=historical, Version A=active, Version B=comparison, R2=invalidated
WHEN:   System resolves authoritative fact source
THEN:   System selects Version A ✓
        System does NOT select PR #35 ✓
        System does NOT select main ✓
        System does NOT select R2 ✓
```

Test `test_09a` through `test_09d` all pass.

## Test Results

```
$ python tests/run_tests.py
  PASS  1.1 缺afs.type → FAIL
  PASS  1.2 缺afs.sha → FAIL
  PASS  2   active在invalidated中 → FAIL
  PASS  3.1 main双角色无HUMAN_EXPLICIT → FAIL
  PASS  3.2 main双角色有HUMAN_EXPLICIT → PASS
  PASS  4   comparison当active → FAIL
  PASS  5   CI PASS→HUMAN_ACCEPTED → FAIL
  PASS  6   REBIND+写权限 → FAIL
  PASS  7   进度卡缺next_step → WARN
  PASS  8   非live跳过live检查
  PASS  9.1 A/B回放—Version A选中
  PASS  9.2 拒绝main为产品源
  PASS  9.3 PR#35不影响Version A
  PASS  9.4 R2不污染Version A
  PASS  10.1 完整字段可恢复上下文
  PASS  10.2 缺字段触发警告
  PASS  ALL  完整有效绑定全通过

  17 passed, 0 failed, 17 total
```

## Validator on PROJECT_STATE.md

```
$ python scripts/validate_binding.py --file PROJECT_STATE.md
PASS: All validations passed
```

## CI

`.github/workflows/validate.yml` — runs on push/PR to `hermes/**`, `codex/**`, `agent/**`, `maker/**` branches. Executes: static validator, test suite, live CI-mode check (continue-on-error for fork PRs).

## Product Repository Proof

No write to `butbutbutbutbutbut/he-weizhi-site` or any product repository. Scope limited to `adaptive-digital-team` repository only. No origin/main modification. No Ready, no Merge.

## Independent Audit Required

| Item | Value |
|------|-------|
| Base for audit | `origin/main@8d343f26dfc9f29422b448705bf85e6f0be37362` |
| Head for audit | `hermes/adt-repository-as-prompt-runtime-binding-r1@b5818cdaac37b5bb33e96e0907dbb16ef7b59975` |
| Draft PR | [#21](https://github.com/butbutbutbutbutbut/adaptive-digital-team/pull/21) |
| Next gate | INDEPENDENT_GOVERNANCE_AUDIT |
| Self-acceptance | FORBIDDEN — not performed |

## Authorization Status

CONSUMED — single use per AUTHORIZATION_ID.
