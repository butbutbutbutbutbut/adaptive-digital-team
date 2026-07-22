# Persistent Holder Control Plane

PROTOCOL_STATUS: `ADOPTED_GOVERNANCE_SPECIFICATION`
PROTOCOL_AUDIT: `ACCEPTED_WITH_RECORDED_LIMITS`
RUNTIME_STATUS: `NOT_IMPLEMENTED`
RUNTIME_ACTIVATION: `NOT_AUTHORIZED`
HERMES_R1: `NOT_AUTHORIZED`

> **Role update**: The Persistent Holder role defined in this document has been
> split into Project Control and Task Holder. See `governance/ROLE_MODEL.md`
> for the complete role model and authority matrix.
>
> **Lifecycle update**: Candidate lifecycle, identity, fingerprint, state
> machine, and CI/audit/merge gates are now defined in
> `protocols/CANDIDATE_LIFECYCLE.md` — the single normative source.
>
> This document is retained as a compatibility entry and for the Dispatch Card /
> Progress Receipt format definitions that remain in active use.

## Purpose and boundary

The Persistent Holder is the resident control-plane interface, Task Router, and
State Registrar for the Adaptive Digital Team. It is not a third Maker, does not
infer missing authority, and does not convert CI success into acceptance.
Temporary Makers create candidates; independent Checkers verify them; Human
retains Ready, Merge, branch deletion, final acceptance, and runtime activation.

This protocol records governance behavior only. It does not implement a service,
scheduler, autonomous agent creator, product change, Persona, Memory, Token,
Profile, Gateway, Feishu integration, memory bridge, or credential operation.

## Holder responsibilities

> **Role update**: These responsibilities are now allocated to Project Control
> and Task Holder per `governance/ROLE_MODEL.md`. The list below is retained as
> a historical reference.

The Holder:

- recovers repository context and live facts;
- resolves one authoritative fact source;
- verifies exact task authority, Base, branch, repository, and scope;
- prepares Dispatch Cards and executable Human authorization packets;
- registers only validated receipts;
- verifies Checker independence;
- derives candidate identity and fingerprint at runtime;
- invalidates stale audit and authorization bindings on drift;
- verifies CI and final realtime gate facts;
- presents concise Human-facing status without black-box claims.

The Holder does not silently Push, widen a lease, retarget a candidate, Ready,
Merge, delete branches, or accept evidence.

## Durable and live state separation

> **Normative source**: `protocols/CANDIDATE_LIFECYCLE.md` § Durable state boundary

`PROJECT_STATE.md` contains only stable task facts:

```text
task_id
repository
branch
starting_base_sha
authorized_write_scope
authority
current_gate
implementation_status
```

The following are live facts and must be resolved at every relevant gate rather
than committed as current values:

- current Head;
- current main;
- current event SHA;
- current remote branch SHA;
- current candidate hash;
- PR state and mergeability;
- checks and protection;
- current user action and blockers.

A historical `resolved_head` may be retained only as an ancestor anchor. It is
never required to equal current Head and must not cause candidate-SHA self-reference.

## Candidate registry topology

> **Normative source**: `protocols/CANDIDATE_LIFECYCLE.md` § Single formal candidate topology

The Holder enforces `ONE_TASK = ONE_BRANCH = ONE_PR = BASE_MAIN`. Before
dispatch and receipt registration, it verifies the candidate PR directly targets
`main`. Any other Base is `STACKED_PR_PROHIBITED`. Pre-audit repair is appended
to the same branch; post-merge defects start a new task from latest main.

## Runtime identity registrar

> **Normative source**: `protocols/CANDIDATE_LIFECYCLE.md` § Runtime-derived identity

Identity is resolved live from `GITHUB_REF` (push), pull-request event (PR),
or local Git facts. No committed-state branch fallback. Full specification in
`protocols/CANDIDATE_LIFECYCLE.md`.

## Candidate fingerprint registrar

> **Normative source**: `protocols/CANDIDATE_LIFECYCLE.md` § Candidate fingerprint

The fingerprint is SHA-256 over canonical JSON of `{repository, base_ref,
base_sha, head_ref, head_sha, sorted(changed_files)}`. It is a live evidence
identifier, not committed into the candidate. Full specification and the
canonical Python implementation are in `protocols/CANDIDATE_LIFECYCLE.md`.

## Audit receipt registration

> **Normative source**: `protocols/CANDIDATE_LIFECYCLE.md` § Audit receipt validation

## Ready and Merge authorization registry

> **Normative source**: `protocols/CANDIDATE_LIFECYCLE.md` § Receipt and authorization binding

## PRE_MERGE_REALTIME_GATE

> **Normative source**: `protocols/CANDIDATE_LIFECYCLE.md` § Final realtime gate (PRE_MERGE_REALTIME_GATE)

## CI verification

> **Normative source**: `protocols/CANDIDATE_LIFECYCLE.md` § CI gate

## Dispatch Card

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
```

## Progress Receipt

```text
PACKET: PROGRESS_RECEIPT
TASK_ID:
AUTHORIZATION_ID:
EXECUTOR:
BASE_SHA:
HEAD_SHA:
CHANGED_FILES:
FINGERPRINT_FIELDS:
CANDIDATE_FINGERPRINT:
VALIDATION:
CI:
UNEXPECTED_CHANGES:
STATUS: CANDIDATE_FOR_INDEPENDENT_REVIEW
NEXT_GATE:
```

A Progress Receipt is Maker evidence only. It is not an audit receipt or acceptance.

## Human-facing control plane

At every critical node, the Holder distinguishes planned, dispatched,
receipt-received, execution-verified, and completed states. It states whether
Human action is required and provides an exact executable action when required.
Waiting is never presented as a Human action. `BLACKBOX_STATUS: PROHIBITED`
remains mandatory.

## Failure routing

- `STACKED_PR_PROHIBITED`: PR Base is not main; no audit or authorization can proceed.
- `INVALID_AUDIT_RECEIPT`: target facts or Checker submission are invalid;
  candidate is not automatically defective.
- `CANDIDATE_FAILURE`: implementation or evidence itself violates requirements.
- `STATE_DRIFT`: live Base, Head, branch, repository, files, PR, checks, or
  protection changed.
- `FINGERPRINT_MISMATCH`: runtime identity differs from audited identity.
- `BLOCKED_BY_HISTORY`: candidate branch or associated PR has been permanently
  disqualified due to prior history rewrite (forced push, deletion, or
  non-fast-forward update). A new branch and new PR are required.
- `CAPABILITY_UNKNOWN`: required live capability cannot be read; stop without
  guessing.

## Remote candidate history immutability

> **Normative source**: `protocols/CANDIDATE_LIFECYCLE.md` § Remote candidate history immutability

Candidate branches are protected by a two-layer defense: (1) the
`candidate-history-protection` ruleset physically blocks force pushes and
deletions; (2) the CI history validator detects violations and persists
permanent disqualification. Full specification in
`protocols/CANDIDATE_LIFECYCLE.md`.

## Merge capability and runtime boundaries

Merge methods, mergeability, required checks, protection, and permissions are
live facts. The Holder re-reads them before presenting or executing a merge
decision. A method mismatch may route only to precise Human method reauthorization
when the candidate fingerprint and every other binding remain unchanged.
Automatic merge, scheduling, Hermes R1, and persistent runtime remain unauthorized.

## Candidate state machine

> **Normative source**: `protocols/CANDIDATE_LIFECYCLE.md` § Candidate state machine

## Pre-write execution gate

> **Normative source**: `protocols/CANDIDATE_LIFECYCLE.md` § Pre-write execution gate

## Scope enforcement

> **Normative source**: `protocols/CANDIDATE_LIFECYCLE.md` § Scope enforcement

## Compatibility preservation matrix

The Candidate Lifecycle R1 registrar operates inside the previously adopted
control plane. It preserves repository-as-prompt recovery, authoritative fact
source rebinding, Dispatch and Progress Receipt packets, target-fact validation,
Checker-independence checks, Human-facing evidence states, progress
anti-inflation, Publish Lease limits, merge-capability preflight, and reviewed
revert rollback. None of those controls is satisfied merely by a matching
fingerprint. Existing regression cases are retained as the compatibility layer;
R1 identity and drift cases are additive.

For the single normative source of lifecycle rules, see `protocols/CANDIDATE_LIFECYCLE.md`.
For the complete role model replacing the Persistent Holder, see `governance/ROLE_MODEL.md`.
For concept-to-source mapping, see `governance/NORMATIVE_MAP.md`.
