# Resource Allocator Integration

PROTOCOL_STATUS: `ADOPTED_GOVERNANCE_SPECIFICATION`

## 1. Purpose

Define the deterministic integration of `scripts/resource_allocator.py` into the
Controller → Holder → Maker dispatch chain. When the Controller classifies a
task's risk level, it invokes the resource allocator to determine the resource
tier, which is then embedded in the Dispatch Card and Authority Card. This
ensures every downstream agent (Holder, Maker, Checker) receives a consistent,
machine-readable resource envelope without re-deriving it from risk.

## 2. Dispatch-time resource allocation flow

```text
Controller classifies risk → runs resource_allocator → embeds tier in Dispatch Card
Holder reads tier → passes to Maker context
Maker reads tier → adjusts behavior (token budget, reasoning depth)
```

The flow is deterministic: risk → tier mapping is the default; a valid Human
`HUMAN_OVERRIDE` takes precedence. Tier is resolved once at dispatch and
carried forward; downstream agents do not re-allocate.

## 3. Dispatch Card extended fields

The existing Dispatch Card (defined in `protocols/PERSISTENT_HOLDER_CONTROL_PLANE.md`)
is extended with the following resource fields:

```text
PACKET: DISPATCH_CARD
TASK_ID:
AUTHORIZATION_ID:
EXECUTOR:
CHECKER:
REPOSITORY:
BASE_REF: main
BASE_SHA:
BRANCH:
PR_BASE: main
ALLOWED_FILES:
FORBIDDEN_ACTIONS:
NEXT_GATE:
RESOURCE_TIER: economy | standard | strong
TOKEN_BUDGET: <approximate token budget, integer>
REASONING_EFFORT: minimal | medium | high
MAX_ITERATIONS: <iteration cap, integer>
HUMAN_OVERRIDE: <true | false>
```

### Field semantics

| Field | Type | Description |
|-------|------|-------------|
| `RESOURCE_TIER` | enum | `economy`, `standard`, or `strong` — the allocated resource tier |
| `TOKEN_BUDGET` | integer | Approximate token budget derived from tier mapping |
| `REASONING_EFFORT` | enum | `minimal`, `medium`, or `high` — reasoning depth |
| `MAX_ITERATIONS` | integer | Maximum iteration count for the Maker |
| `HUMAN_OVERRIDE` | boolean | `true` when the Human explicitly overrode the default tier; `false` when derived from risk |

`HUMAN_OVERRIDE=true` is the only case where `RESOURCE_TIER` may differ from
the risk-to-tier default mapping. A downstream agent must respect the tier as
given; it must not second-guess or re-derive it.

## 4. Authority Card extension

The Authority Card is extended with an equivalent `resource_tier` field:

```text
AUTHORITY_CARD
...
resource_tier: economy | standard | strong
```

This ensures the authorization binding itself carries the resource envelope,
visible to any agent that validates the Authority Card before acting.

## 5. Tier mapping

The default mapping is defined in `scripts/resource_allocator.py` as `TIER_MAP`:

| Risk | Default tier |
|------|-------------|
| `LOW` | `economy` |
| `MODERATE` | `standard` |
| `HIGH` | `strong` |
| `CRITICAL` | `strong` |

A valid Human override via `HUMAN_OVERRIDE=true` replaces the default tier.
Invalid tiers fail validation.

Risk classification follows `protocols/DYNAMIC_GOVERNANCE_ROUTER.md` § 6
(Safety risk classification). The decoupling rule (§ 6.2) remains in effect:
risk, resource tier, and Checker timing are independent controls. HIGH risk
does not automatically select `strong` when an explicit Human tier binding is
supplied.

## 6. Per-tier behavior

### economy

- Token budget: ~8,000 tokens
- Reasoning effort: `minimal`
- Max iterations: 20
- Checker: not allocated (`checker_timing=NONE`)

### standard

- Token budget: ~32,000 tokens
- Reasoning effort: `medium`
- Max iterations: 40
- Checker: conditional (`AFTER_FORMAL_CANDIDATE`)

### strong

- Token budget: ~128,000 tokens
- Reasoning effort: `high`
- Max iterations: 50
- Checker: mandatory (`checker_timing=NOW` when a formal candidate exists)

Token budgets are approximate ceilings, not hard guarantees. The Maker operates
within the budget but is not required to consume it fully.

## 7. Implementation notes

### Non-modification of resource_allocator.py

`scripts/resource_allocator.py` is the executable allocator and is NOT modified
by this protocol. This protocol defines only the integration contract — the
fields that carry the allocator's output into the dispatch chain.

### Delegate-task limitation (current)

`delegate_task` in the current Hermes runtime does not accept caller-side model
selection. This protocol prepares the dispatch chain for tiered delegation: when
Hermes supports tier-differentiated sub-agent spawning, the infrastructure
(dispatch fields, tier mapping, per-tier config) is already in place. Until then:

- `resource_tier` is embedded as metadata in Dispatch Cards and Authority Cards.
- Human and Agent consumers can read and reason about the tier.
- The Maker adjusts its own behavior (token budget, reasoning depth, iteration
  count) based on the tier but cannot enforce model selection on sub-agents.

### Current stage

This protocol is infrastructure preparation. At the current stage, `resource_tier`
serves as readable metadata. Full enforcement (model selection, token budgeting
in sub-agents) activates when the Hermes runtime supports tier-differentiated
delegation.

### References to existing protocols

- Risk classification: `protocols/DYNAMIC_GOVERNANCE_ROUTER.md` § 6
- Resource tier definition: `protocols/DYNAMIC_GOVERNANCE_ROUTER.md` § 7.1
- Checker timing: `protocols/DYNAMIC_GOVERNANCE_ROUTER.md` § 8
- Dispatch Card format: `protocols/PERSISTENT_HOLDER_CONTROL_PLANE.md` § Dispatch Card
- Point and message ceilings: `protocols/DYNAMIC_GOVERNANCE_ROUTER.md` § 7.2

## 8. References

| Reference | Relationship |
|-----------|-------------|
| `scripts/resource_allocator.py` | Executable allocator — not modified by this protocol |
| `protocols/DYNAMIC_GOVERNANCE_ROUTER.md` | Risk classification and resource tier definitions |
| `protocols/PERSISTENT_HOLDER_CONTROL_PLANE.md` | Dispatch Card and Authority Card base format |
| `protocols/CANDIDATE_LIFECYCLE.md` | Candidate lifecycle — gate definitions |
| `governance/ROLE_MODEL.md` | Role topology — Controller, Holder, Maker, Checker |
