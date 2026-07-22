# ADT Runtime Adapter Contract

PROTOCOL_STATUS: `ADOPTED_GOVERNANCE_SPECIFICATION`

## 1. Purpose

The Runtime Adapter Contract defines the interface between an AI coding tool's
native runtime (Hermes, Codex, Cursor, etc.) and the ADT Governance Core. It
establishes a three-layer model that isolates tool-native state from ADT
governance decisions, ensuring that tool identity, session metadata, and
credential tags never leak into or contaminate governance routing.

The adapter is **not** an authorization source. Authorization always comes from
an external `ExecutionAuthorizationBinding`, never from the adapter or the tool
runtime.

## 2. Three-Layer Model

```
┌─────────────────────────────────────────────────────────┐
│ Layer 1: Tool-Native Context                            │
│ (Runtime-internal: process state, API keys,             │
│  tool session state, user prefs, file handles)          │
│ NEVER enters ADT Core — local to the adapter only       │
├─────────────────────────────────────────────────────────┤
│ Layer 2: Adapter Envelope                               │
│ (Structured metadata carried alongside the task:        │
│  tool_identity, tool_session_id, tool_capability_tags,  │
│  session_principal, claimed_actor, credential_tags,     │
│  independence_evidence)                                 │
│ Stripped before reaching Layer 3                        │
├─────────────────────────────────────────────────────────┤
│ Layer 3: TaskIntake (ADT Core Input)                    │
│ (Existing schema: request, repository, base_sha,        │
│  branch, attachments, claimed_authority, etc.)          │
│ The ONLY input the Governance Router sees               │
└─────────────────────────────────────────────────────────┘
```

### 2.1 Layer 1: Tool-Native Context

Tool-runtime state that the adapter holds but never forwards to ADT Core:
- Process environment variables
- Tool authentication credentials
- Session-local file handles
- Tool-specific user preferences
- Raw API response data

**Rule**: Layer 1 data MUST NEVER reach the Governance Router or any ADT Core
component. The adapter is the sole boundary.

### 2.2 Layer 2: Adapter Envelope

Structured metadata about the tool session, carried alongside but separate from
the task intake. Schema: `schemas/adapter-envelope.schema.json`.

Fields:
- `tool_identity` — the tool name and version (e.g., "hermes/4.2.1")
- `tool_session_id` — opaque, tool-specific session identifier
- `tool_capability_tags` — descriptive tags only (e.g., "git", "file_write",
  "browser"); NOT authority grants
- `session_principal` — the identity under which the tool session is running
  (tags only: e.g., "xiaohe", "alice@example.com")
- `claimed_actor` — the actor the session claims to represent (tags only)
- `credential_tags` — tag descriptions of available credentials (e.g.,
  "github_pat", "openai_api_key"); NEVER contain actual credential values
- `independence_evidence` — two-phase evidence object for Checker independence
  (see §7)

### 2.3 Layer 3: TaskIntake

The existing ADT Core input contract. Schema: `schemas/task-intake.schema.json`.
**UNCHANGED** by this protocol. The adapter normalizes tool-native input into a
standard TaskIntake and discards all Layer 2 metadata before forwarding.

## 3. Interface Boundaries

### 3.1 TaskIntake (Unchanged)

The TaskIntake schema (`schemas/task-intake.schema.json`) is the single
normative input to the Governance Router. The adapter produces TaskIntake
objects from tool-native input. No additional fields are added.

### 3.2 GovernancePlan (Unchanged)

The GovernancePlan schema (`schemas/governance-plan.schema.json`) is the
single normative output of the Governance Router. The adapter receives
GovernancePlan objects and gates execution through the Authorization Binding.

### 3.3 Adapter Standard Input

The adapter receives from the tool runtime:

```json
{
  "adapter_envelope": {
    "tool_identity": "hermes/4.2.1",
    "tool_session_id": "sess_abc123",
    "tool_capability_tags": ["git", "file_write", "browser"],
    "session_principal": "xiaohe",
    "claimed_actor": "xiaohe",
    "credential_tags": ["github_pat"],
    "independence_evidence": { ... }
  },
  "task_intake": {
    "request": "Implement feature X",
    "repository": "owner/repo",
    ...
  },
  "authorization_binding": {
    "authorization_id": "AUTH-001",
    ...
  }
}
```

### 3.4 Adapter Standard Output

The adapter produces for the tool runtime:

```json
{
  "governance_plan": { ... },
  "adapter_error": null,
  "route": "CANDIDATE_IMPLEMENTATION"
}
```

Schema: `schemas/adapter-output.schema.json`. The `governance_plan` field
`$ref`s the existing GovernancePlan schema — no duplicate definition.

### 3.5 Error States

The adapter MUST produce an `adapter_error` field, distinct from
`governance_plan.route`. Errors:

| Error | Cause |
|-------|-------|
| `SCOPE_VIOLATION` | Action outside authorized write scope |
| `UNAUTHORIZED_ACTION` | Action type not in authorized_actions |
| `BINDING_MISSING` | No AuthorizationBinding present for gated action |
| `BINDING_INVALID` | AuthorizationBinding fails validation |
| `CREDENTIAL_LEAK` | Credential values detected attempting to cross Layer 2→3 |
| `INDEPENDENCE_FAILED` | Checker independence evidence invalid |
| `ATTEMPTED_SCOPE_VIOLATION` | Out-of-scope write attempt blocked |

**Critical rule**: `plan.route` is NEVER overwritten by an adapter error.
The adapter error is a separate field. The router's route determination is
preserved for audit.

## 4. Tool Capability Mapping (Descriptive Only)

Tool capabilities are described by tags in the Adapter Envelope. They are
**descriptive metadata only** — never authority grants.

| Capability Tag | Description |
|----------------|-------------|
| `git` | Tool can perform git operations |
| `file_write` | Tool can write to filesystem |
| `file_read` | Tool can read from filesystem |
| `browser` | Tool can access web content |
| `terminal` | Tool can execute shell commands |
| `github_api` | Tool can interact with GitHub API |
| `network` | Tool has network access |

**Rule**: Capability presence does NOT imply authority. A tool with `git` tag
is not authorized to commit or push without explicit AuthorizationBinding.

## 5. Identity Passthrough

### 5.1 SESSION_PRINCIPAL ≠ Human Holder

- **SESSION_PRINCIPAL**: The identity the tool session is running under (e.g.,
  a tool login, a service account). Stored in the Adapter Envelope as a tag.
- **CLAIMED_ACTOR**: The human or system the session claims to represent.
  Stored as a tag only.
- **Human Holder**: The governance authority recognized by ADT. Authority must
  come from an external `ExecutionAuthorizationBinding`, never from
  SESSION_PRINCIPAL or CLAIMED_ACTOR.

**ZERO mappings**: There is NO mapping from "tool login → Human Holder".
A tool login is an operational identity; Human Holder is a governance identity.
They are separate domains.

### 5.2 Credential Boundary

Credentials (API keys, tokens, passwords) exist ONLY in Layer 1 (Tool-Native
Context). The Adapter Envelope carries `credential_tags` — descriptive string
tags that indicate what credentials are available (e.g., `["github_pat",
"openai_api_key"]`). Actual credential values are NEVER included.

The adapter MUST strip credential values before constructing the Adapter
Envelope. Any attempt to pass credential values across the Layer 2→3 boundary
MUST result in `CREDENTIAL_LEAK` error.

## 6. Authorization Binding Gate

### 6.1 Position in Pipeline

```
USER_INPUT → TASK_INTAKE → GOVERNANCE_ROUTER → GOVERNANCE_PLAN (CANDIDATE)
                                                    ↓
                                     AUTHORIZATION_BINDING (external)
                                                    ↓
                                     PER-ACTION SCOPE GATE (adapter)
                                                    ↓
                                     TOOL EXECUTION (gated)
```

The Router always receives Intake and always produces a GovernancePlan with
`control_packet_status: CANDIDATE`. The AuthorizationBinding is a separate,
external document that gates execution AFTER the Router.

### 6.2 Binding Validation

The adapter validates the AuthorizationBinding against three sources:
1. TaskIntake fields (repository, base_sha, branch)
2. AuthorizationBinding fields (repository, base_sha, branch)
3. Live git origin (fetched at gate time)

All three MUST agree. Mismatch → `BINDING_INVALID`.

### 6.3 Write Scope: Subset, Not Equality

```
plan.write_scope ⊆ auth.authorized_write_scope
```

The plan's write scope MUST be a **subset** of the authorization's write scope.
Equality is NOT required — the authorization may grant broader scope than the
plan uses. But the plan can NEVER exceed what the authorization permits.

### 6.4 Per-Action Gate

Before EVERY tool action execution:

1. `action.type ∈ authorized_actions` — the action type must be permitted
2. If the action targets a file: `action.path ∈ plan.write_scope` AND
   `action.path ∈ authorized_write_scope`
3. Pathless actions (commit, push, create_draft_pr) are constrained by
   `authorized_actions` only

**ALL out-of-scope attempts → BLOCKED as `ATTEMPTED_SCOPE_VIOLATION`**.
Credential capability is IRRELEVANT to the scope gate — having a credential
does not expand scope.

### 6.5 Default Forbidden Actions

The following actions are DEFAULT FORBIDDEN and MUST NOT appear in
`authorized_actions`:
- `ready` (mark PR as ready for review)
- `merge` (merge PR)
- `close_pr` (close PR without merging)
- `delete_branch` (delete remote branch)

These require explicit, separate Human Holder authorization outside the
normal Maker workflow.

## 7. Checker Independence — Two-Phase Evidence

### 7.1 Evidence Object (5 Fields)

```json
{
  "separate_execution_context": true,
  "maker_context_inherited": false,
  "participated_in_implementation": false,
  "independent_fact_read": true,
  "independent_conclusion": true
}
```

This is NOT a single boolean. All five fields MUST be present.

### 7.2 Phase 1: Pre-Execution

Satisfied before the Checker begins work:
- `separate_execution_context`: The Checker runs in a separate execution
  context (separate process, agent window, or container).
- `maker_context_inherited`: MUST be `false`. The Checker does NOT inherit
  the Maker's session state, memory, or conversation context.

### 7.3 Phase 2: Post-Execution

Satisfied after the Checker completes its audit:
- `participated_in_implementation`: MUST be `false`. The Checker did not
  design, write, or contribute to the implementation.
- `independent_fact_read`: MUST be `true`. The Checker read facts from
  independent sources (repository, git log, file contents, test output),
  not from the Maker's claims.
- `independent_conclusion`: MUST be `true`. The Checker reached its own
  conclusion, not the Maker's.

### 7.4 Timing Constraint

The adapter MUST NOT require `independent_conclusion: true` before the
Checker has executed. Pre-execution validation checks only Phase 1 fields.
Post-execution validation checks all five.

### 7.5 Independence Boundary

"Same API key" does NOT break independence. Two agent windows using the
same API provider are independent if they do not share session state,
conversation context, or implementation participation.

## 8. Adapter Examples

### 8.1 Hermes (Pseudocode)

```python
def adapt_hermes_to_adt(
    hermes_context: dict,
    authorization_binding: dict,
) -> AdapterOutput:
    # 1. Build Layer 2 Envelope (strip credentials)
    envelope = AdapterEnvelope(
        tool_identity=f"hermes/{hermes_context['version']}",
        tool_session_id=hermes_context['session_id'],
        tool_capability_tags=["git", "file_write", "terminal", "browser"],
        session_principal=hermes_context['active_profile'],
        claimed_actor=hermes_context.get('claimed_actor', ''),
        credential_tags=["github_pat"],  # tags only, no values
        independence_evidence=None,      # set per-role
    )

    # 2. Build Layer 3 TaskIntake (existing schema)
    intake = TaskIntake(
        request=hermes_context['user_request'],
        repository=hermes_context.get('repository', ''),
        base_sha=hermes_context.get('base_sha', ''),
        branch=hermes_context.get('branch', ''),
    )

    # 3. Route through Governance Router
    plan = route_task(intake.to_dict())

    # 4. Gate with AuthorizationBinding
    if not _validate_binding(authorization_binding, intake):
        return AdapterOutput(
            governance_plan=plan,
            adapter_error="BINDING_INVALID",
            route=plan['route'],  # preserved
        )

    # 5. Scope check
    if not _scope_subset(plan['write_scope'],
                         authorization_binding['authorized_write_scope']):
        return AdapterOutput(
            governance_plan=plan,
            adapter_error="SCOPE_VIOLATION",
            route=plan['route'],  # preserved
        )

    return AdapterOutput(
        governance_plan=plan,
        adapter_error=None,
        route=plan['route'],
    )
```

### 8.2 Codex (Pseudocode)

```python
def adapt_codex_to_adt(
    codex_session: dict,
    auth_binding: dict,
) -> dict:
    envelope = {
        "tool_identity": "codex/stable",
        "tool_session_id": codex_session['id'],
        "tool_capability_tags": ["git", "file_write", "terminal"],
        "session_principal": codex_session.get('user', ''),
        "claimed_actor": codex_session.get('user', ''),
        "credential_tags": ["github_token"],
        "independence_evidence": None,
    }
    intake = {
        "request": codex_session['prompt'],
        "repository": codex_session.get('repo', ''),
    }
    plan = route_task(intake)
    # ... same gating as Hermes
    return {
        "governance_plan": plan,
        "adapter_error": None,
        "route": plan['route'],
    }
```

## 9. Error Separation

### 9.1 plan.route ≠ adapter_error

The `route` field in the GovernancePlan is the Router's determination. It is
NEVER overwritten by adapter errors. The adapter maintains a separate
`adapter_error` field.

This preserves audit integrity: an auditor can see what the Router decided
AND separately what the adapter encountered.

### 9.2 Error Preservation

When an adapter error occurs:
- `governance_plan` is still returned (Router's output, unmodified)
- `adapter_error` describes the adapter-level failure
- `route` mirrors `governance_plan.route` for convenience, but is NOT the
  authoritative source

## 10. Normative Schemas

| Schema | Layer | Status |
|--------|-------|--------|
| `schemas/adapter-envelope.schema.json` | Layer 2 | CANDIDATE |
| `schemas/adapter-output.schema.json` | Adapter Output | CANDIDATE |
| `schemas/execution-authorization-binding.schema.json` | Authorization | CANDIDATE |
| `schemas/task-intake.schema.json` | Layer 3 (existing) | ADOPTED |
| `schemas/governance-plan.schema.json` | Router Output (existing) | ADOPTED |

## 11. Validation

The `scripts/validate_adapter.py` script validates all three new schemas
against JSON Schema draft 2020-12. It performs validation ONLY — no
authorization generation, no action execution.

Usage:
```bash
python scripts/validate_adapter.py
```

## 12. Compliance Checklist

- [ ] Layer 2 Envelope never contains credential values
- [ ] Layer 1 data never reaches Governance Router
- [ ] SESSION_PRINCIPAL never maps to Human Holder
- [ ] AuthorizationBinding is external, not self-set
- [ ] `human_holder_approved` is never set by adapter
- [ ] `plan.write_scope ⊆ auth.authorized_write_scope` (subset, not equality)
- [ ] Every file-targeting action gated by scope
- [ ] `ATTEMPTED_SCOPE_VIOLATION` for all out-of-scope attempts
- [ ] Independence evidence has 5 fields, not single boolean
- [ ] `independent_conclusion` not required before Checker execution
- [ ] `adapter-output.schema.json` uses `$ref`, no duplicate GovernancePlan
- [ ] `plan.route` never overwritten by `adapter_error`
