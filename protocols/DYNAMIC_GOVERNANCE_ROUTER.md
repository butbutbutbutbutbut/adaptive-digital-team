# Dynamic Governance Router

PROTOCOL_STATUS: `ADOPTED_GOVERNANCE_SPECIFICATION`

***
4dc0eb25173e92208b347bbfd23a6b101fa0b571

## 1. Purpose

The Dynamic Governance Router converts natural-language or structured user input
into a constrained, deterministic governance plan. It classifies the task, assesses
risk, determines the execution route, decomposes the task into ordered execution
units, and produces a Candidate Control Packet.

P1 generates candidate plans only. It does **not** execute high-risk operations,
auto-Ready, auto-Merge, or auto-delete branches.

## 2. Pipeline

```
USER_INPUT
→ TASK_INTAKE
→ FACT_AND_AUTHORITY_CHECK
→ RISK_CLASSIFICATION
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
| `REPOSITORY_CANDIDATE` | Repository reference, write/modify intent |
| `CONTROL_PACKET` | Input carries full Dispatch Card or Control Packet header |
| `AMBIGUOUS_REQUEST` | Intent cannot be reliably classified |
| `CONFLICTING_FACTS` | Repository facts (SHA, PR, branch, scope) conflict |

### 3.2 Classification Rules

1. If the input carries a complete Control Packet with `AUTHORIZATION_ID`,
   `FROM`, `TO`, `EXECUTOR`, `REPOSITORY`, `BASE_SHA` → `CONTROL_PACKET`.

2. If the input references a repository AND explicitly requests writes (modify,
   create, fix, add, delete files or branches, push, create PR) →
   `REPOSITORY_CANDIDATE`.

3. If the input references a repository AND does NOT request writes (read,
   inspect, check, audit, list, verify) → `REPOSITORY_READ_ONLY`.

4. If the input has file attachments AND no repository reference →
   `PROMPT_LOCAL_WITH_FILES`.

5. If the input is plain text with no attachments and no repository reference →
   `PROMPT_LOCAL`.

6. If repository facts (branch, SHA, PR, scope) conflict with each other or
   with the declared intent → `CONFLICTING_FACTS`.

7. If none of the above can be determined with confidence →
   `AMBIGUOUS_REQUEST`.

## 4. Risk Classification

### 4.1 RISK Enum (FROZEN)

| Value | Criteria |
|-------|----------|
| `LOW` | Local-only execution, no repository interaction, no external systems |
| `MODERATE` | Repository read, candidate plan generation, no direct writes |
| `HIGH` | Repository writes, file modifications, PR creation, execution unit generation |
| `CRITICAL` | Governance file modification, permission changes, credential handling, publishing, branch deletion, Ready/Merge, candidate history mutation, external system interaction |

### 4.2 Risk Assessment Factors

Risk is the **maximum** of all applicable factors:

1. **Write**: any repository write → at least `HIGH`
2. **Governance files**: modifying AGENTS.md, protocols/, .github/workflows/,
   or any governance file → `CRITICAL`
3. **Permissions**: modifying authority, scope, roles, access controls → `CRITICAL`
4. **Credentials**: touching secrets, tokens, keys, or credential files → `CRITICAL`
5. **Publishing**: Ready, Merge, push, deploy, release → `CRITICAL`
6. **History mutation**: deleting branches, force-push, rebase, amend → `CRITICAL`
7. **External systems**: APIs, webhooks, services outside the repo → `CRITICAL`
8. **Ambiguity**: incomplete or inconsistent facts → at least `MODERATE`
9. **Local only**: no repository at all → `LOW`

## 5. Governance Route

### 5.1 ROUTE Enum (FROZEN)

| Value | When |
|-------|------|
| `DIRECT_LOCAL_EXECUTION` | `PROMPT_LOCAL` with LOW risk |
| `FILE_LOCAL_EXECUTION` | `PROMPT_LOCAL_WITH_FILES` with LOW risk |
| `READ_ONLY_REPOSITORY_ANALYSIS` | `REPOSITORY_READ_ONLY` |
| `CANDIDATE_IMPLEMENTATION` | `REPOSITORY_CANDIDATE` with MODERATE or HIGH risk |
| `INDEPENDENT_AUDIT` | `CONTROL_PACKET` requesting audit |
| `HUMAN_DECISION_REQUIRED` | `AMBIGUOUS_REQUEST`, or CRITICAL risk without explicit authorization, or missing write scope |
| `FACT_SOURCE_REBIND` | `CONFLICTING_FACTS` — facts conflict, no writes permitted |
| `HARD_STOP` | CRITICAL risk on governance/permissions, auto-Ready/Merge attempt, scope expansion, P0 violation |

### 5.2 Route Determination Logic

```
Input → TASK_TYPE + RISK → ROUTE

PROMPT_LOCAL + LOW                  → DIRECT_LOCAL_EXECUTION
PROMPT_LOCAL_WITH_FILES + LOW       → FILE_LOCAL_EXECUTION
REPOSITORY_READ_ONLY + any          → READ_ONLY_REPOSITORY_ANALYSIS
REPOSITORY_CANDIDATE + MODERATE     → CANDIDATE_IMPLEMENTATION
REPOSITORY_CANDIDATE + HIGH         → CANDIDATE_IMPLEMENTATION
REPOSITORY_CANDIDATE + CRITICAL     → HUMAN_DECISION_REQUIRED
CONTROL_PACKET + audit request      → INDEPENDENT_AUDIT
CONTROL_PACKET + non-audit          → CANDIDATE_IMPLEMENTATION
AMBIGUOUS_REQUEST + any             → HUMAN_DECISION_REQUIRED
CONFLICTING_FACTS + any             → FACT_SOURCE_REBIND
Any + auto-Ready/Merge detected     → HARD_STOP
Any + scope expansion detected      → HARD_STOP
Any + P0 violation detected         → HARD_STOP
Any + missing critical authority    → HARD_STOP
```

## 6. Task Decomposition

### 6.1 Step Structure

Each execution unit must contain:

```text
STEP_ID           — unique step identifier
OBJECTIVE         — what this step accomplishes
DEPENDENCIES      — list of STEP_IDs that must complete first
REQUIRED_FACTS    — facts that must be verified before execution
AUTHORIZED_WRITE_SCOPE — files this step may modify
EXECUTOR_ROLE      — TASK_HOLDER / MAKER / CHECKER / HUMAN
CHECKER_REQUIRED   — true / false
PASS_CONDITIONS    — criteria for step success
FAIL_CLOSED_ACTION — action on failure (RETRY / ESCALATE / HARD_STOP / HUMAN)
NEXT_GATE          — next decision point after completion
```

> **Role normalization**: `TASK_HOLDER` is the normative executor role.
> The legacy value `HOLDER` is accepted as a backward-compatible input alias
> and normalized to `TASK_HOLDER` immediately on intake. Output must never
> emit `HOLDER`.

### 6.2 Step Generation

Steps are generated deterministically from the route, risk, and task type.
The decomposition must be pure (no randomness, no model-specific variation).

## 7. Candidate Control Packet

### 7.1 CONTROL_PACKET_STATUS Enum (FROZEN)

| Value | Meaning |
|-------|---------|
| `CANDIDATE` | Plan generated, NOT yet authorized |
| `NOT_AUTHORIZED` | Plan was reviewed and explicitly denied |
| `AUTHORIZED` | Human Holder explicitly authorized execution |

### 7.2 Packet Structure

```json
{
  "route": "<ROUTE>",
  "risk": "<RISK>",
  "task_type": "<TASK_TYPE>",
  "facts_status": "VERIFIED | REQUIRES_VERIFICATION | CONFLICTING | INCOMPLETE",
  "control_packet_status": "CANDIDATE",
  "write_scope": [],
  "steps": [],
  "checker_required": true,
  "human_authorization_required": true,
  "write_actions_permitted": false,
  "limitations": []
}
```

### 7.3 Authorization Boundary

- The router may ONLY generate packets with `control_packet_status: CANDIDATE`.
- `AUTHORIZED` status requires explicit Human Holder approval through a
  separate gate.
- The router must never auto-approve, auto-Ready, auto-Merge, or auto-delete.

## 8. Fact Conflict Isolation

When repository, PR, branch, SHA, permissions, or scope facts conflict:

```text
FACT_RECEIPT_INVALID
READ_ONLY_RECHECK_REQUIRED
WRITE_ACTIONS: PROHIBITED
```

The router must NOT:
- Auto-create a fix branch
- Auto-close a PR
- Auto-expand the task scope
- Infer missing facts from chat context
- Assume write permission exists

## 9. Fail-Closed Rules (FROZEN)

| Condition | Action |
|-----------|--------|
| Missing AUTHORIZATION_ID in Control Packet | HARD_STOP |
| Missing REPOSITORY in repo task | FACT_SOURCE_REBIND |
| Missing BASE_SHA in repo task | FACT_SOURCE_REBIND |
| Missing write scope in CANDIDATE task | HUMAN_DECISION_REQUIRED |
| Auto-Ready request detected | HARD_STOP |
| Auto-Merge request detected | HARD_STOP |
| Auto-delete branch detected | HARD_STOP |
| Scope expansion beyond authorization | HARD_STOP: SCOPE_EXPANSION_REQUIRED |
| P0 A/B/C contract modification attempted | HARD_STOP |
| Maker == Checker for same task | HARD_STOP |
| HIGH/CRITICAL risk without Checker | HARD_STOP |
| Capability-based authority inference | HARD_STOP |
| Illegal enum values in output | HARD_STOP |
| User cancellation | STOPPED, zero writes |
| Public ADT upstream write attempt | READ_ONLY |

## 10. P1 Boundaries

### 10.1 P1 DOES

- Classify task type from user input
- Assess risk level
- Generate a deterministic route
- Decompose tasks into ordered steps
- Produce Candidate Control Packets (CANDIDATE status only)
- Validate input and output against frozen schemas
- Fail closed on all error conditions

### 10.2 P1 DOES NOT

- Auto-Ready, auto-Merge, or auto-delete
- Auto-allocate model tiers or costs (P2)
- Auto-spawn sub-agents or parallel workers (P3)
- Execute generated control packets directly
- Modify P0 A/B/C first-contact contracts
- Infer authority from model capabilities
- Expand write scope beyond authorization
- Create fix branches for conflicting facts

## 11. Adoption Record

```text
IMPLEMENTATION_STATUS: ACTIVE
PHASE: P1
AUTHORIZATION: ADT-P1-DYNAMIC-GOVERNANCE-ROUTER-20260721-001
***
4dc0eb25173e92208b347bbfd23a6b101fa0b571
ROLE_NORMALIZATION: TASK_HOLDER (normative), HOLDER (legacy input alias only)
INDEPENDENT_AUDIT: PENDING
SELF_ACCEPTANCE: FORBIDDEN
AUTO_READY: FORBIDDEN
AUTO_MERGE: FORBIDDEN
HISTORY_REWRITE: FORBIDDEN
NEXT_GATE: IMPLEMENTATION_COMPLETE → LOCAL_VALIDATION → INDEPENDENT_AUDIT
```
