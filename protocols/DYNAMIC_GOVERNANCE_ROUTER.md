> **DEPRECATED — 归档态（2026-08-08）**：本协议已被双层重构取代。
> 完整规范见 `protocols/BINDING.md` / `GATE.md` / `RECEIPT.md` / `PHILOSOPHY.md`；
> 去向登记见 `governance/NORMATIVE_MAP.md`（唯一活入口）。
> 文件保留仅为维持历史引用（84+ PR）不断链，不参与新作业。

# Dynamic Governance Router

PROTOCOL_STATUS: `ADOPTED_GOVERNANCE_SPECIFICATION`

## 1. Purpose and normative boundary

The Dynamic Governance Router converts natural-language or structured Human input
into a constrained, deterministic `GovernancePlan`. It classifies the task,
verifies the fact and authority boundary, judges the adaptive counter-objective,
assesses safety risk, chooses the route, derives continuity and resource controls,
and decomposes the task into ordered execution units.

This document is the **single normative source for dynamic governance routing**.
The adaptive counter-objective principle itself remains normative only in
`METHODOLOGY.md`; this protocol defines how the Router represents and applies that
principle. The JSON Schemas define the serialized contract, while
`scripts/route_task.py` and `scripts/resource_allocator.py` are the executable
implementations.

The Router produces candidate plans only. It does **not** execute unauthorized
writes, auto-Ready, auto-Merge, auto-delete branches, or self-accept a candidate.

## 2. Pipeline

```text
USER_INPUT
→ TASK_INTAKE
→ ADAPTIVE_COUNTER_OBJECTIVE_GATE
→ FACT_AND_AUTHORITY_CHECK
→ TASK_TYPE_CLASSIFICATION
→ READ_ONLY_PRIORITY_GATE
→ CONTROL_PACKET_COMPLETENESS_GATE
→ SAFETY_RISK_CLASSIFICATION
→ CONTINUITY_DECISION
→ RESOURCE_AND_CHECKER_TIMING
→ GOVERNANCE_ROUTE
→ TASK_DECOMPOSITION
→ CANDIDATE_GOVERNANCE_PLAN
→ HUMAN_AUTHORIZATION_GATE
```

The adaptive counter-objective gate runs silently at intake and every material
re-route. It consumes zero Point, creates no standalone receipt, and does not
create a second protocol or state machine.

## 3. Task intake

### 3.1 Preserved task-type enum

| Value | Trigger |
|---|---|
| `PROMPT_LOCAL` | Plain-text request with no repository or attachment |
| `PROMPT_LOCAL_WITH_FILES` | Attachment-backed request with no repository |
| `REPOSITORY_READ_ONLY` | Repository reference with read, analysis, review, audit, verification, or decision intent only |
| `REPOSITORY_CANDIDATE` | Repository reference with explicit write or implementation intent |
| `CONTROL_PACKET` | Input carries a Control Packet object; completeness is validated separately |
| `AMBIGUOUS_REQUEST` | Intent cannot be classified reliably |
| `CONFLICTING_FACTS` | Repository, SHA, branch, PR, scope, or authority facts conflict |

### 3.2 Intake controls

The Router may consume these additive controls:

```text
task_id
active_task_id
requested_actions
audit_request
restart_requested
restart_reason
human_premise
human_friction_signal
latest_authorized_scope
estimated_task_value
estimated_governance_cost
requested_resource_tier
recommended_points
hard_max_points
max_external_messages
candidate_stage
```

These controls extend the existing Task Intake. They do not create S2/S3 task
levels or a parallel lifecycle.

### 3.3 Read-only and Control Packet precedence

Routing priority is deterministic:

1. `audit_request=true` is read-only and takes precedence over write intent.
2. Non-empty `requested_actions` containing only `READ`, `ANALYZE`, `DECIDE`,
   `REVIEW`, `AUDIT`, `VERIFY`, or `SUMMARIZE` is read-only and takes precedence
   over Control Packet write routing.
3. A Control Packet is complete only when all of these non-empty fields exist:

   ```text
   authorization_id
   from
   to
   executor
   repository
   base_sha
   ```

4. An incomplete Control Packet routes to `HUMAN_DECISION_REQUIRED` with
   `facts_status=INCOMPLETE`, zero write scope, and no write permission.
5. A complete Control Packet with `audit_request=true` routes to
   `INDEPENDENT_AUDIT`.
6. A complete Control Packet with a pure read-only request routes to
   `READ_ONLY_REPOSITORY_ANALYSIS`.
7. A Control Packet may route to `CANDIDATE_IMPLEMENTATION` only when it is
   complete, carries explicit write or implementation action, is authorization
   bearing, is not an audit, and is not pure read-only.
8. A repository request is `REPOSITORY_CANDIDATE` only when write intent is
   explicit. A bug, defect, diagnosis, review, or decision does not imply repair.
9. Attachments without a repository route as `PROMPT_LOCAL_WITH_FILES`; plain
   text without attachments or repository routes as `PROMPT_LOCAL`.

A read-only task must not expand into repair, implementation, branch creation,
commit, push, PR creation, or any repository write.

## 4. Adaptive counter-objective controls

### 4.1 Anti-review decision

`anti_review_decision` is one of:

| Value | Meaning |
|---|---|
| `PROCEED` | Governance cost is proportionate and no hard stop applies |
| `DOWNSCOPE` | Estimated governance cost exceeds estimated task value; use the smallest safe path |
| `BLOCK` | A hard-stop condition prevents execution |

Rules:

- A hard-stop condition produces `BLOCK`.
- `estimated_governance_cost > estimated_task_value` produces `DOWNSCOPE`.
- `DOWNSCOPE` caps the recommended Point at 1, caps external messages at 1, and
  records the governance-cost limitation.
- The gate never silently increases scope, Point, Checker capacity, token budget,
  or message count.

### 4.2 Human premise classification

Every material Human premise is classified as:

| Value | Meaning |
|---|---|
| `SUPPORTED` | Material parts are supported and none are rejected or unverifiable |
| `PARTIAL` | Some material parts are supported and others are rejected or unverifiable |
| `REJECTED` | Material parts are rejected and none are supported |
| `UNVERIFIED` | The premise lacks sufficient verified support |

Agreement language is not evidence. Classification affects the plan but does not
alter machine facts.

### 4.3 Human friction signal

When the Human restates, narrows, corrects, or expresses friction with the task:

- discard inferred scope;
- restore `latest_authorized_scope` when present;
- cap `max_external_messages` at 1;
- continue the same task unless a valid restart condition exists.

## 5. Continuity

`continuity_action` is one of:

| Value | Rule |
|---|---|
| `NEW_TASK_START` | No active task matches the requested task |
| `CONTINUE` | `task_id` equals `active_task_id`; restore only the current delta |
| `RESTART` | Restart is requested with a valid reason |
| `RESTART_REJECTED` | Restart is requested without a valid reason |

Valid restart reasons are exactly:

```text
ROLE_ISOLATION
FACT_SOURCE_INVALID
CONTEXT_CONTAMINATION
HUMAN_EXPLICIT_REQUEST
```

Same-task work defaults to `CONTINUE`. A rejected restart does not create a new
task, branch, PR, Point, or authorization. It records
`JUSTIFIED_RESTART_REQUIRED` as the stop condition.

## 6. Safety risk classification

### 6.1 Risk enum

| Value | Criteria |
|---|---|
| `LOW` | Local-only work with no repository or external system |
| `MODERATE` | Repository read, audit, incomplete Control Packet, ambiguous facts, or decision-only routing |
| `HIGH` | Authorized repository writes or candidate implementation without a critical factor |
| `CRITICAL` | Governance files, permissions, credentials, publishing, history mutation, destructive branch operations, or equivalent authority-sensitive work |

Risk is the maximum applicable safety factor.

### 6.2 Decoupling rule

`SAFETY_RISK`, `RESOURCE_TIER`, and `CHECKER_TIMING` are independent controls.

- HIGH risk does not automatically select `strong`.
- HIGH risk does not automatically start a Checker.
- CRITICAL governance modification defaults to `strong` only when no valid Human
  resource-tier binding is supplied.
- Risk remains descriptive and controls routing and authorization; it is not the
  primary allocator key when `resource_tier` exists.

## 7. Resource and Point controls

### 7.1 Resource tier

`resource_tier` is one of:

```text
economy
standard
strong
```

Default derivation:

| Risk | Default tier |
|---|---|
| `LOW` | `economy` |
| `MODERATE` | `standard` |
| `HIGH` | `standard` |
| `CRITICAL` | `strong` |

A valid explicit Human tier overrides the default. Invalid tiers fail validation.

### 7.2 Point and message ceilings

- `recommended_points` and `hard_max_points` are integers from 0 through 2.
- `recommended_points` must not exceed `hard_max_points`.
- Allocation must also remain within the Human-provided Point boundary.
- `max_external_messages` is an integer from 0 through 10.
- Human Point, token, Checker, message, and scope ceilings fail closed.
- No allocator may silently overspend or infer a larger boundary.

## 8. Checker timing

`checker_timing` is one of:

| Value | Meaning |
|---|---|
| `NONE` | No Checker is allocated |
| `AFTER_FORMAL_CANDIDATE` | Reserve the later audit gate; allocate no Checker during local production |
| `NOW` | Allocate an independent Checker now because a formal candidate or explicit audit route exists |

Rules:

1. Local candidate production uses `AFTER_FORMAL_CANDIDATE`.
2. `candidate_stage=FORMAL_CANDIDATE` may produce `NOW`.
3. `INDEPENDENT_AUDIT` uses `NOW` and produces one read-only Checker step.
4. A Checker agent is configured only when `checker_timing=NOW`.
5. `checker_required` is a compatibility and audit-requirement field; it does not
   itself authorize immediate Checker allocation when `checker_timing` is present.
6. Maker and Checker remain independent contexts.
7. Checker allocation must remain within the Human Checker boundary.

The former rule “HIGH/CRITICAL risk without an already allocated Checker is a
HARD_STOP” is superseded. The normative requirement is correct timing and
independence, not premature allocation.

## 9. Governance route

### 9.1 Route enum

| Value | When |
|---|---|
| `DIRECT_LOCAL_EXECUTION` | `PROMPT_LOCAL` with LOW risk |
| `FILE_LOCAL_EXECUTION` | `PROMPT_LOCAL_WITH_FILES` with LOW risk |
| `READ_ONLY_REPOSITORY_ANALYSIS` | Repository or Control Packet read-only work |
| `CANDIDATE_IMPLEMENTATION` | Complete, explicitly authorized, non-critical write Control Packet or repository candidate |
| `INDEPENDENT_AUDIT` | Complete Control Packet with `audit_request=true` |
| `HUMAN_DECISION_REQUIRED` | Ambiguity, incomplete Control Packet, missing authority, no explicit action, or critical work requiring Human decision |
| `FACT_SOURCE_REBIND` | Conflicting or invalidated fact source |
| `HARD_STOP` | Forbidden or unauthorized action |

### 9.2 Route determination

```text
PROMPT_LOCAL + LOW                         → DIRECT_LOCAL_EXECUTION
PROMPT_LOCAL_WITH_FILES + LOW              → FILE_LOCAL_EXECUTION
REPOSITORY_READ_ONLY + any                 → READ_ONLY_REPOSITORY_ANALYSIS
REPOSITORY_CANDIDATE + HIGH                → CANDIDATE_IMPLEMENTATION
REPOSITORY_CANDIDATE + CRITICAL            → HUMAN_DECISION_REQUIRED
CONTROL_PACKET + incomplete                → HUMAN_DECISION_REQUIRED
CONTROL_PACKET + audit_request=true        → INDEPENDENT_AUDIT
CONTROL_PACKET + pure read-only actions     → READ_ONLY_REPOSITORY_ANALYSIS
CONTROL_PACKET + explicit write + HIGH      → CANDIDATE_IMPLEMENTATION
CONTROL_PACKET + no explicit action         → HUMAN_DECISION_REQUIRED
CONTROL_PACKET + CRITICAL                   → HUMAN_DECISION_REQUIRED
AMBIGUOUS_REQUEST + any                    → HUMAN_DECISION_REQUIRED
CONFLICTING_FACTS + any                    → FACT_SOURCE_REBIND
Forbidden automation or authority inference → HARD_STOP
```

Read-only priority is evaluated before Control Packet write routing. Every route
other than `CANDIDATE_IMPLEMENTATION` emits `write_scope=[]` and
`write_actions_permitted=false`.

An upstream ADT repository remains read-only unless a separate, verified write
authorization is present.

## 10. Fact and scope isolation

When repository, PR, branch, SHA, permission, or scope facts conflict:

```text
FACT_RECEIPT_INVALID
FACT_SOURCE_REBIND_REQUIRED
WRITE_ACTIONS: PROHIBITED
```

The Router must not:

- infer missing facts from conversational confidence;
- create a repair branch for an invalid fact source;
- expand the authorized write scope;
- treat capability as authority;
- convert read authority into write authority.

When a Human explicitly expands scope, the binding must be updated to record the
new exact path before Live Binding validation can pass.

## 11. Task decomposition

Each execution unit contains:

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

`TASK_HOLDER` is the normative Holder executor value. `HOLDER` is accepted only
as a legacy input alias and is normalized immediately; output must not emit it.

Candidate implementation steps follow this order:

1. verify repository facts;
2. continue or create the authorized candidate branch;
3. implement only the authorized scope;
4. run local validation and produce a formal candidate;
5. run independent Checker audit only when `checker_timing=NOW`.

`INDEPENDENT_AUDIT` generates exactly a read-only Checker audit step with
`authorized_write_scope=[]` and `checker_required=true`. It generates no Maker,
branch creation, implementation, or write step.

`READ_ONLY_REPOSITORY_ANALYSIS` generates no write scope and no Maker
implementation step.

## 12. Candidate GovernancePlan

The Router emits one existing `GovernancePlan`, not a second receipt or state
object.

```json
{
  "route": "<ROUTE>",
  "risk": "<LOW|MODERATE|HIGH|CRITICAL>",
  "task_type": "<TASK_TYPE>",
  "facts_status": "<FACTS_STATUS>",
  "control_packet_status": "CANDIDATE",
  "write_scope": [],
  "steps": [],
  "checker_required": false,
  "human_authorization_required": true,
  "write_actions_permitted": false,
  "anti_review_decision": "<PROCEED|DOWNSCOPE|BLOCK>",
  "claim_status": "<SUPPORTED|PARTIAL|REJECTED|UNVERIFIED>",
  "continuity_action": "<NEW_TASK_START|CONTINUE|RESTART|RESTART_REJECTED>",
  "recommended_points": 0,
  "hard_max_points": 2,
  "resource_tier": "<economy|standard|strong>",
  "checker_timing": "<NONE|AFTER_FORMAL_CANDIDATE|NOW>",
  "max_external_messages": 3,
  "stop_condition": "<STOP_CONDITION>",
  "limitations": []
}
```

The Router may emit only candidate or denied planning state. Human Holder
authorization is a separate gate and cannot be inferred from the plan.

## 13. Stop conditions

| Value | Meaning |
|---|---|
| `TASK_COMPLETE` | The bounded non-authorized planning step is complete |
| `HUMAN_BOUNDARY_REACHED` | A Human ceiling prevents further work |
| `AUTHORIZATION_REQUIRED` | Explicit Human authority is required |
| `FACT_SOURCE_REBIND_REQUIRED` | Facts must be rebound to one authoritative source |
| `JUSTIFIED_RESTART_REQUIRED` | Requested restart lacks a valid reason |
| `GOVERNANCE_COST_EXCEEDS_VALUE` | Plan was downscoped to the smallest safe path |
| `HARD_STOP` | A forbidden condition blocks the route |

## 14. Fail-closed rules

| Condition | Action |
|---|---|
| Incomplete Control Packet | `HUMAN_DECISION_REQUIRED`, `facts_status=INCOMPLETE`, zero writes |
| `audit_request=true` without complete Control Packet | `HUMAN_DECISION_REQUIRED`, zero writes |
| Complete audit Control Packet | `INDEPENDENT_AUDIT`, Checker-only read step |
| Pure read-only Control Packet | `READ_ONLY_REPOSITORY_ANALYSIS`, zero writes |
| Control Packet lacks explicit write action | `HUMAN_DECISION_REQUIRED`, zero writes |
| Conflicting repository facts | `FACT_SOURCE_REBIND` |
| Missing verified Base before repository write | block write until verified |
| Missing exact write scope for candidate implementation | `HUMAN_DECISION_REQUIRED` |
| Read-only request expands into repair or write | reject expansion |
| Unsupported restart | `RESTART_REJECTED` |
| Governance cost exceeds task value | `DOWNSCOPE` |
| Recommended Point exceeds Human hard max | allocation blocked |
| Token, Point, Checker, message, or scope boundary exceeded | allocation blocked |
| Auto-Ready, auto-Merge, or auto-delete branch | `HARD_STOP` |
| Force-push, rebase, amend, or unauthorized history mutation | `HARD_STOP` |
| Capability-based authority inference | `HARD_STOP` |
| Maker and Checker identity collapse | `HARD_STOP` |
| Illegal enum or malformed plan | validation failure |
| User cancellation | stop with zero new writes |

## 15. Boundaries

The Router does:

- classify task type and safety risk;
- apply the silent adaptive counter-objective;
- classify Human premises;
- enforce Control Packet completeness and read-only priority;
- determine continuity, resource tier, Checker timing, Point and message controls;
- generate deterministic routes and steps;
- emit a candidate GovernancePlan;
- fail closed on authority, fact, scope, and budget violations.

The Router does not:

- create S2/S3 task levels;
- create a second anti-objective or audit protocol;
- execute the generated candidate plan;
- infer write authority;
- expand scope without Human authorization;
- auto-allocate an early Checker solely because risk is HIGH;
- auto-Ready, auto-Merge, auto-delete, or self-accept;
- modify the Candidate Lifecycle or A/B/C first-contact protocol.

## 16. Adoption record

```text
IMPLEMENTATION_STATUS: ACTIVE
PHASE: DYNAMIC_ROUTING_WITH_ADAPTIVE_CONTROLS
BASE_AUTHORIZATION: ADT-P1-DYNAMIC-GOVERNANCE-ROUTER-20260721-001
ADAPTIVE_AUTHORIZATION: ADT-ADAPTIVE-COUNTER-OBJECTIVE-GATE-20260726-001
AUDIT_FIX: ADT-ADAPTIVE-COUNTER-OBJECTIVE-GATE-AUDIT-FIX-R1
ROLE_NORMALIZATION: TASK_HOLDER (normative), HOLDER (legacy input alias only)
COUNTER_OBJECTIVE_SOURCE: METHODOLOGY.md
ROUTER_NORMATIVE_SOURCE: protocols/DYNAMIC_GOVERNANCE_ROUTER.md
SCHEMA_CONTRACT: schemas/governance-plan.schema.json
EXECUTABLE_ROUTER: scripts/route_task.py
EXECUTABLE_ALLOCATOR: scripts/resource_allocator.py
SELF_ACCEPTANCE: FORBIDDEN
AUTO_READY: FORBIDDEN
AUTO_MERGE: FORBIDDEN
HISTORY_REWRITE: FORBIDDEN
NEXT_GATE: FULL_REGRESSION_AND_LIVE_BINDING_PASS → SAME_CHECKER_INCREMENTAL_DELTA_REAUDIT
```
