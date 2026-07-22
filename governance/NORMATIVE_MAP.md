# Normative Map

This document establishes the single normative source for every ADT governance
concept. No concept may have two authoritative definitions. All other documents
that reference a concept are secondary, compatibility, or executable detail.

## Normative sources

| Concept | Normative Source | Status | Compatibility Entries |
|---|---|---|---|
| ADT definition | `METHODOLOGY.md` | ADOPTED | `README.md` § What ADT provides |
| Role model | `governance/ROLE_MODEL.md` | ADOPTED | `AGENTS.md` § Roles, `README.md` § Roles |
| Fact/action separation | `governance/AUTHORITY_AND_FACTS.md` | ADOPTED | `AGENTS.md` § FACT_SOURCE_REBIND |
| Candidate lifecycle | `protocols/CANDIDATE_LIFECYCLE.md` | ADOPTED | `AGENTS.md`, `protocols/LIGHTWEIGHT_EXECUTION_FLOW.md`, `protocols/PERSISTENT_HOLDER_CONTROL_PLANE.md` |
| Agent-facing rules | `AGENTS.md` | ADOPTED | — |
| Protocol activation | `BOOTSTRAP.md` | ADOPTED | `AGENTS.md` § Protocol activation, `README.md` § AI ACTIVATION DIRECTIVE |
| First-contact routing | `README.md` | ADOPTED | `BOOTSTRAP.md`, `AGENTS.md` § First-contact routing |
| Human-facing evidence | `AGENTS.md` § Human-facing evidence discipline | ADOPTED | — |
| Lightweight execution flow | `protocols/LIGHTWEIGHT_EXECUTION_FLOW.md` | ADOPTED | — |
| Beginner bootstrap | `protocols/BEGINNER_BOOTSTRAP_ROUTER.md` | ADOPTED | — |
| Multimodal evidence | `protocols/MULTIMODAL_EVIDENCE_ACCEPTANCE_GATE.md` | ADOPTED | — |
| Instruction routing | `protocols/INSTRUCTION_ROUTING_AND_AUTHORITY.md` | ADOPTED | — |
| Project closeout | `protocols/PROJECT_CLOSEOUT_PROTOCOL.md` | ADOPTED | — |

## Status definitions

| Status | Meaning |
|---|---|
| `ADOPTED` | Normative; all other references must defer. |
| `CANDIDATE` | Proposed normative, under independent review. |
| `EXPERIMENTAL` | Not yet normative; subject to change without preserving compatibility. |

## Deprecated / replaced concepts

| Old Concept | Old Location | Replaced By | New Location |
|---|---|---|---|
| Persistent Holder (role) | `protocols/PERSISTENT_HOLDER_CONTROL_PLANE.md` | Project Control + Task Holder | `governance/ROLE_MODEL.md` |
| Holder responsibilities | `protocols/PERSISTENT_HOLDER_CONTROL_PLANE.md` | Role definitions | `governance/ROLE_MODEL.md` |
| Candidate lifecycle (duplicate) | `protocols/LIGHTWEIGHT_EXECUTION_FLOW.md` | Candidate Lifecycle | `protocols/CANDIDATE_LIFECYCLE.md` |
| Candidate lifecycle (duplicate) | `AGENTS.md` § Candidate Lifecycle R1 | Candidate Lifecycle | `protocols/CANDIDATE_LIFECYCLE.md` |
| Runtime identity registrar | `protocols/PERSISTENT_HOLDER_CONTROL_PLANE.md` | Runtime-derived identity | `protocols/CANDIDATE_LIFECYCLE.md` |
| Candidate fingerprint registrar | `protocols/PERSISTENT_HOLDER_CONTROL_PLANE.md` | Candidate fingerprint | `protocols/CANDIDATE_LIFECYCLE.md` |
| Audit receipt registration | `protocols/PERSISTENT_HOLDER_CONTROL_PLANE.md` | Audit receipt validation | `protocols/CANDIDATE_LIFECYCLE.md` |
| Ready/Merge authorization registry | `protocols/PERSISTENT_HOLDER_CONTROL_PLANE.md` | Receipt and authorization binding | `protocols/CANDIDATE_LIFECYCLE.md` |
| PRE_MERGE_REALTIME_GATE (duplicate) | `protocols/PERSISTENT_HOLDER_CONTROL_PLANE.md` | Final realtime gate | `protocols/CANDIDATE_LIFECYCLE.md` |
| CI verification (duplicate) | `protocols/PERSISTENT_HOLDER_CONTROL_PLANE.md` | CI gate | `protocols/CANDIDATE_LIFECYCLE.md` |
| Candidate state machine (duplicate) | `protocols/PERSISTENT_HOLDER_CONTROL_PLANE.md` | Candidate state machine | `protocols/CANDIDATE_LIFECYCLE.md` |
| Pre-write execution gate (duplicate) | `protocols/PERSISTENT_HOLDER_CONTROL_PLANE.md` | Pre-write execution gate | `protocols/CANDIDATE_LIFECYCLE.md` |
| Scope enforcement (duplicate) | `protocols/PERSISTENT_HOLDER_CONTROL_PLANE.md` | Scope enforcement | `protocols/CANDIDATE_LIFECYCLE.md` |
| Remote candidate history immutability (duplicate) | `protocols/PERSISTENT_HOLDER_CONTROL_PLANE.md` | Remote candidate history immutability | `protocols/CANDIDATE_LIFECYCLE.md` |
| Runtime candidate identity (duplicate) | `protocols/LIGHTWEIGHT_EXECUTION_FLOW.md` | Runtime-derived identity | `protocols/CANDIDATE_LIFECYCLE.md` |
| Candidate fingerprint (duplicate) | `protocols/LIGHTWEIGHT_EXECUTION_FLOW.md` | Candidate fingerprint | `protocols/CANDIDATE_LIFECYCLE.md` |

## Rules

1. **One concept = one normative source.** No exceptions. Every ADT concept has exactly one document that defines it authoritatively.
2. **Compatibility entries may exist** but MUST point to the normative source. They are summaries, not alternatives.
3. **This map itself is normative** — disputes about "which document is authoritative" resolve here.
4. **New concepts** that are introduced in a compatibility document and not yet mapped to a normative source are EXPERIMENTAL until mapped.
5. **Deprecation** must be recorded in this map before a compatibility entry is removed.
