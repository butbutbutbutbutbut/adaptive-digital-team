# Dynamic Governance Router

PROTOCOL_STATUS: `ADOPTED_GOVERNANCE_SPECIFICATION`

***
4dc0eb25173e92208b347bbfd23a6b101fa0b571

## 1. Purpose

The Dynamic Governance Router converts natural-language or structured user input
into a constrained, deterministic governance plan. It classifies the task, assesses
safety risk, determines continuity, evaluates material Human premises, binds a
resource tier and Checker timing, decomposes the task into ordered execution units,
and produces a Candidate Control Packet.

The Router generates candidate plans only. It does **not** execute high-risk
operations, auto-Ready, auto-Merge, auto-delete branches, allocate a Checker before
a formal candidate, or expand a read request into repair.

The adaptive counter-objective rationale is defined only in `METHODOLOGY.md`.
This document specifies the existing Router's executable contract; it is not a
second methodology or state system.

## 2. Pipeline

```
USER_INPUT
→ TASK_INTAKE
→ ANTI_REVIEW (silent / zero Point)
→ CLAIM_AND_AUTHORITY_CHECK
→ CONTINUITY_CLASSIFICATION
→ SAFETY_RISK_CLASSIFICATION
→ RESOURCE_AND_CHECKER_BINDING
→ TASK_DECOMPOSITION
→ GOVERNANCE_ROUTE
→ CANDIDATE_CONTROL_PACKET
→ HUMAN_AUTHORIZATION_GATE
```

## 3. Task Intake Classification

### 3.1 TASK_TYPE Enum (FROZEN)

| Value | Trigger |
|-------|---------|
| `PROMPT_LOCAL` | Plain text request, no files, no repository |
| `PROMPT_LOCAL_WITH_FILES` | Request with attachments, no repository |
| `REPOSITORY_READ_ONLY` | Repository reference, read/inspect intent only |
| `REPOSITORY_CANDIDATE` | Repository reference, explicit write/modify intent |
| `CONTROL_PACKET` | Input carries full Dispatch Card or Control Packet header |
| `AMBIGUOUS_REQUEST` | Intent cannot be reliably classified |
| `CONFLICTING_FACTS` | Repository facts (SHA, PR, branch, scope) conflict |

### 3.2 Classification Rules

1. A complete Control Packet with `AUTHORIZATION_ID` routes as `CONTROL_PACKET`.
2. Repository + explicit write action routes as `REPOSITORY_CANDIDATE`.
3. Repository + read/analyze/review/decide action routes as
   `REPOSITORY_READ_ONLY`, even when the material being read describes a bug.
4. Attachments without repository route as `PROMPT_LOCAL_WITH_FILES`.
5. Plain text without repository routes as `PROMPT_LOCAL`.
6. Conflicting facts route as `CONFLICTING_FACTS`.
7. Otherwise route as `AMBIGUOUS_REQUEST`.

`requested_actions` is authoritative when present. A set containing only
`READ`, `ANALYZE`, `DECIDE`, `REVIEW`, `AUDIT`, `VERIFY`, or `SUMMARIZE` cannot
create write intent. Fix language inside a quoted Bug report or evidence body is
not authorization to implement a fix.

## 4. Independent Human-claim judgment

Every material Human premise must produce exactly one `claim_status`:

| Value | Meaning |
|-------|---------|
| `SUPPORTED` | The relevant premise is supported by available facts |
| `PARTIAL` | Supported and rejected parts both exist |
| `REJECTED` | The relevant premise conflicts with available facts |
| `UNVERIFIED` | Available evidence cannot support or reject it |

The Router may consume structured `human_premise` evidence, but it must not turn
polite agreement into `SUPPORTED`. Missing evidence is `UNVERIFIED`.

## 5. Continuity

The Router emits exactly one `continuity_action`:

| Value | Meaning |
|-------|---------|
| `NEW_TASK_START` | No matching active task; normal startup applies |
| `CONTINUE` | Same task; restore current delta only |
| `RESTART` | Restart has a valid reason |
| `RESTART_REJECTED` | Restart requested without a valid reason |

The same `task_id` and `active_task_id` default to `CONTINUE`. Valid restart
reasons are frozen to:

- `ROLE_ISOLATION`
- `FACT_SOURCE_INVALID`
- `CONTEXT_CONTAMINATION`
- `HUMAN_EXPLICIT_REQUEST`

A restart never creates a second task level, second state system, stacked repair
PR, or independent receipt.

## 6. Safety Risk

### 6.1 RISK Enum (FROZEN)

| Value | Criteria |
|-------|----------|
| `LOW` | Local-only execution, no repository interaction, no external systems |
| `MODERATE` | Repository read, candidate plan generation, no direct writes |
| `HIGH` | Repository writes or file modifications |
| `CRITICAL` | Governance/permission/credential/publishing/history mutation |

Safety risk describes consequence and authorization pressure only. It does not
directly select model tier or Checker timing.

## 7. Adaptive counter-objective outputs

### 7.1 `anti_review_decision`

Frozen values:

- `PROCEED`
- `DOWNSCOPE`
- `BLOCK`

The anti-review runs silently and costs zero Point. It does not emit an
independent receipt. If `estimated_governance_cost > estimated_task_value`, the
Router emits `DOWNSCOPE`, reduces `recommended_points` and
`max_external_messages`, and selects the smallest safe route. A forbidden action
or unsatisfied hard boundary may emit `BLOCK`.

### 7.2 Human friction

When `human_friction_signal=true`, the Router:

- restores `latest_authorized_scope` as the operative write scope;
- discards inferred expansion;
- limits `max_external_messages` to one;
- keeps the current task unless a valid restart reason exists.

## 8. Resource and Checker binding

### 8.1 `resource_tier`

Frozen values: `economy`, `standard`, `strong`.

Default binding:

| Condition | Default tier |
|-----------|--------------|
| LOW local | `economy` |
| MODERATE repository/read | `standard` |
| HIGH bounded candidate | `standard` |
| CRITICAL governance modification | `strong` |

A HIGH bounded write may explicitly use `economy` or `standard`. Risk alone must
not silently upgrade it to `strong`.

### 8.2 `checker_timing`

Frozen values:

- `NONE`
- `AFTER_FORMAL_CANDIDATE`
- `NOW`

Local candidate production emits `AFTER_FORMAL_CANDIDATE` and receives no
Checker allocation. Only a formal candidate or explicit audit stage emits
`NOW`. This timing field, not risk, determines Checker allocation.

The legacy `checker_required` field remains for compatibility and lifecycle
intent. It is not the resource allocator's timing input when `checker_timing` is
present.

## 9. Governance Route

### 9.1 ROUTE Enum (FROZEN)

| Value | When |
|-------|------|
| `DIRECT_LOCAL_EXECUTION` | `PROMPT_LOCAL` with LOW risk |
| `FILE_LOCAL_EXECUTION` | `PROMPT_LOCAL_WITH_FILES` with LOW risk |
| `READ_ONLY_REPOSITORY_ANALYSIS` | `REPOSITORY_READ_ONLY` |
| `CANDIDATE_IMPLEMENTATION` | Authorized bounded repository candidate |
| `INDEPENDENT_AUDIT` | Formal candidate audit |
| `HUMAN_DECISION_REQUIRED` | Ambiguity, critical authorization, or restart rejection |
| `FACT_SOURCE_REBIND` | Conflicting facts; no writes |
| `HARD_STOP` | Forbidden action or hard boundary violation |

## 10. Task Decomposition

Each execution unit retains the adopted structure:

```text
STEP_ID
OBJECTIVE
DEPENDENCIES
REQUIRED_FACTS
AUTHORIZED_WRITE_SCOPE
EXECUTOR_ROLE
CHECKER_REQUIRED
PASS_CONDITIONS
FAIL_CLOSED_ACTION
NEXT_GATE
```

`TASK_HOLDER` is normative; legacy input `HOLDER` is normalized immediately and
never emitted. No generated local-production step assigns `CHECKER`. The Checker
step is generated only when `checker_timing=NOW`.

## 11. Candidate Control Packet

Every `GovernancePlan` includes at least:

```json
{
  "route": "<ROUTE>",
  "risk": "<RISK>",
  "task_type": "<TASK_TYPE>",
  "facts_status": "VERIFIED | REQUIRES_VERIFICATION | CONFLICTING | INCOMPLETE",
  "control_packet_status": "CANDIDATE",
  "anti_review_decision": "PROCEED | DOWNSCOPE | BLOCK",
  "claim_status": "SUPPORTED | PARTIAL | REJECTED | UNVERIFIED",
  "continuity_action": "NEW_TASK_START | CONTINUE | RESTART | RESTART_REJECTED",
  "recommended_points": 1,
  "hard_max_points": 2,
  "resource_tier": "economy | standard | strong",
  "checker_timing": "NONE | AFTER_FORMAL_CANDIDATE | NOW",
  "max_external_messages": 1,
  "stop_condition": "<STOP_CONDITION>",
  "write_scope": [],
  "steps": [],
  "checker_required": false,
  "human_authorization_required": false,
  "write_actions_permitted": false,
  "limitations": []
}
```

The Router may only generate `CANDIDATE`, never `AUTHORIZED`. Human Holder
approval remains a separate gate.

## 12. Resource Allocator contract

The Resource Allocator consumes `GovernancePlan.resource_tier` and
`GovernancePlan.checker_timing`.

It returns `BLOCKED` when any of the following exceeds the Human boundary:

- `recommended_points`
- `hard_max_points`
- approximate token budget
- Checker permission when `checker_timing=NOW`

No silent tier upgrade, Checker removal, Checker early start, token overspend, or
Point overspend is permitted. For compatibility only, legacy plans that omit new
fields may use the old risk/checker fallback; all new Router output includes the
new fields.

## 13. Fact Conflict Isolation

When repository, PR, branch, SHA, permissions, or scope facts conflict:

```text
FACT_RECEIPT_INVALID
READ_ONLY_RECHECK_REQUIRED
WRITE_ACTIONS: PROHIBITED
```

The Router must not auto-create a fix branch, close a PR, expand scope, infer
missing facts, or assume write permission.

## 14. Fail-Closed Rules

| Condition | Action |
|-----------|--------|
| Missing critical authority | HARD_STOP or HUMAN_DECISION_REQUIRED |
| Auto-Ready / Auto-Merge / auto-delete | HARD_STOP |
| Scope expansion | HARD_STOP: SCOPE_EXPANSION_REQUIRED |
| P0 A/B/C contract modification | HARD_STOP |
| Capability-based authority inference | HARD_STOP |
| Invalid enum | HARD_STOP |
| Same-task restart without valid reason | `RESTART_REJECTED` |
| Human point/token/Checker boundary exceeded | ResourcePlan `BLOCKED` |
| Governance cost exceeds task value | `DOWNSCOPE` |
| User cancellation | zero writes |
| Public ADT upstream without explicit authorization | READ_ONLY |

## 15. Preservation boundaries

This change does not:

- add S2/S3 task levels;
- modify Candidate Lifecycle;
- modify the A/B/C first-contact protocol;
- create a second anti-objective protocol or state system;
- auto-spawn sub-agents;
- authorize Ready, Merge, branch deletion, or product acceptance;
- change product repositories or CI.

## 16. Adoption Record

```text
IMPLEMENTATION_STATUS: ACTIVE_CANDIDATE
PHASE: S2 / DOWNSCOPED_IMPLEMENTATION
TASK_ID: ADT-ADAPTIVE-COUNTER-OBJECTIVE-GATE-R1
AUTHORIZATION: ADT-ADAPTIVE-COUNTER-OBJECTIVE-GATE-20260726-001
ROLE_NORMALIZATION: TASK_HOLDER (normative), HOLDER (legacy input alias only)
ANTI_REVIEW_RECEIPT: NONE
ANTI_REVIEW_POINT_COST: 0
INDEPENDENT_AUDIT: PENDING_AFTER_FORMAL_CANDIDATE
SELF_ACCEPTANCE: FORBIDDEN
AUTO_READY: FORBIDDEN
AUTO_MERGE: FORBIDDEN
HISTORY_REWRITE: FORBIDDEN
NEXT_GATE: IMPLEMENTATION_COMPLETE → LOCAL_VALIDATION → FORMAL_CANDIDATE → INDEPENDENT_AUDIT
```
