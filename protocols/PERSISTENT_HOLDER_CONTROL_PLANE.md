# Persistent Holder Control Plane

PROTOCOL_STATUS: `ADOPTED_GOVERNANCE_SPECIFICATION`
PROTOCOL_AUDIT: `ACCEPTED_WITH_RECORDED_LIMITS`
RUNTIME_STATUS: `NOT_IMPLEMENTED`
RUNTIME_ACTIVATION: `NOT_AUTHORIZED`
HERMES_R1: `NOT_AUTHORIZED`

## Purpose and boundary

The Persistent Holder is the resident control-plane interface, Task Router, and State Registrar for the Adaptive Digital Team. It is not a third Maker, does not infer missing authority, and does not convert CI success into acceptance. Temporary Makers create candidates; independent Checkers verify them; Human retains Ready, Merge, branch deletion, final acceptance, and runtime activation.

This protocol records governance behavior only. It does not implement a service, scheduler, autonomous agent creator, product change, Persona, Memory, Token, Profile, Gateway, Feishu integration, memory bridge, or credential operation.

## Holder responsibilities

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

The Holder does not silently Push, widen a lease, retarget a candidate, Ready, Merge, delete branches, or accept evidence.

## Durable and live state separation

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

The following are live facts and must be resolved at every relevant gate rather than committed as current values:

- current Head;
- current main;
- current event SHA;
- current remote branch SHA;
- current candidate hash;
- PR state and mergeability;
- checks and protection;
- current user action and blockers.

A historical `resolved_head` may be retained only as an ancestor anchor. It is never required to equal current Head and must not cause candidate-SHA self-reference.

## Candidate registry topology

The Holder enforces:

```text
ONE_TASK = ONE_BRANCH = ONE_PR = BASE_MAIN
```

Before dispatch and before receipt registration, it verifies the candidate PR directly targets `main`. Any other Base is `STACKED_PR_PROHIBITED`. The Holder does not route a child PR as repair for an unmerged parent. A pre-audit repair is appended to the same branch and invalidates prior Head-bound evidence. A post-merge defect starts a new task from latest main. Former child PRs are not retargeted after parent squash merge.

## Runtime identity registrar

### Push registration

The Holder accepts branch identity only from `GITHUB_REF=refs/heads/<branch>`. Missing, empty, tag, notes, pull merge, or other formats fail closed. It verifies:

```text
git HEAD = GITHUB_SHA = origin/<push_branch>
```

There is no committed-state branch fallback.

### Pull-request registration

The Holder reads source and Base identities from the pull-request event:

```text
head_ref / head_sha := pull_request.head
base_ref / base_sha := pull_request.base
```

`base_ref` must be main. Source Head must match `origin/<head_ref>` and the checked-out source commit. `refs/pull/*/merge` is not candidate identity.

### Local registration

The Holder derives current Head from `git rev-parse HEAD`, current main from `origin/main`, candidate remote from `origin/<branch>`, and changed files from the runtime diff.

## Candidate fingerprint registrar

The Holder canonicalizes and prints:

```text
FINGERPRINT_FIELDS:
  repository
  base_ref
  base_sha
  head_ref
  head_sha
  changed_files (sorted)
CANDIDATE_FINGERPRINT: SHA-256(canonical fields)
```

The fingerprint is a live evidence identifier. It is not committed into the candidate. Repository, Base, Head, branch, or changed-file drift creates a different fingerprint.

## Audit receipt registration

An audit receipt is registrable only when all target facts match live facts:

- task and authorization;
- repository and PR;
- Base ref and exact Base SHA;
- head ref and exact Head SHA;
- exact sorted changed files;
- candidate fingerprint;
- Checker identity and independence;
- current PR state.

A target transcription error produces `INVALID_AUDIT_RECEIPT / TARGET_FACT_MISMATCH` without changing candidate state or consuming audit/repair budget. A valid receipt is Head- and fingerprint-bound. Once the candidate identity changes, the old receipt is invalid.

## Ready and Merge authorization registry

Ready and Merge authorizations must bind the same fingerprint as the valid independent audit. The Holder reports, separately:

```text
AUDIT_BINDING: VALID | INVALID
READY_AUTHORIZATION: VALID | INVALID
MERGE_AUTHORIZATION: VALID | INVALID
```

Any Base SHA, Head SHA, branch, changed-file set, or repository change invalidates all three old bindings. No old authorization may be silently rebound.

## PRE_MERGE_REALTIME_GATE

Immediately before presenting Ready or Merge, and again immediately before execution, the Holder performs the final realtime gate.

Input:

- expected fingerprint from the valid audit;
- candidate branch;
- exact authorized write scope.

Fresh facts:

- repository identity;
- `origin/main` and Base ref;
- `origin/<candidate_branch>`;
- current Head;
- sorted changed files;
- workspace clean status;
- live PR state, mergeability, checks, permissions, and protections when relevant.

Required checks:

1. Base remains `main`.
2. Base SHA is unchanged.
3. Head SHA is unchanged and equals candidate remote.
4. Changed files are unchanged.
5. Runtime fingerprint equals expected fingerprint.
6. Workspace clean is true.
7. Authorized write scope exactly equals actual changed files.
8. Audit, Ready authorization, and Merge authorization fingerprints are all identical when their gates are invoked.

Any mismatch produces `HARD_STOP`, `STATE_DRIFT`, or `FINGERPRINT_MISMATCH` as applicable. The Holder does not continue to Ready or Merge.

## CI verification

The Holder verifies live that both push and pull-request workflow runs are attached to current source Head and succeeded. Static validation, complete tests, and live validation must all run. Skipped required work, soft failure, missing runs, or any `continue-on-error` occurrence fails closed. CI does not grant Human authority.

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

At every critical node, the Holder distinguishes planned, dispatched, receipt-received, execution-verified, and completed states. It states whether Human action is required and provides an exact executable action when required. Waiting is never presented as a Human action. `BLACKBOX_STATUS: PROHIBITED` remains mandatory.

## Failure routing

- `STACKED_PR_PROHIBITED`: PR Base is not main; no audit or authorization can proceed.
- `INVALID_AUDIT_RECEIPT`: target facts or Checker submission are invalid; candidate is not automatically defective.
- `CANDIDATE_FAILURE`: implementation or evidence itself violates requirements.
- `STATE_DRIFT`: live Base, Head, branch, repository, files, PR, checks, or protection changed.
- `FINGERPRINT_MISMATCH`: runtime identity differs from audited identity.
- `CAPABILITY_UNKNOWN`: required live capability cannot be read; stop without guessing.

## Merge capability and runtime boundaries

Merge methods, mergeability, required checks, protection, and permissions are live facts. The Holder re-reads them before presenting or executing a merge decision. A method mismatch may route only to precise Human method reauthorization when the candidate fingerprint and every other binding remain unchanged. Automatic merge, scheduling, Hermes R1, and persistent runtime remain unauthorized.

## Compatibility preservation matrix

The Candidate Lifecycle R1 registrar operates inside the previously adopted
control plane. It preserves repository-as-prompt recovery, authoritative fact
source rebinding, Dispatch and Progress Receipt packets, target-fact validation,
Checker-independence checks, Human-facing evidence states, progress
anti-inflation, Publish Lease limits, merge-capability preflight, and reviewed
revert rollback. None of those controls is satisfied merely by a matching
fingerprint. Existing regression cases are retained as the compatibility layer;
R1 identity and drift cases are additive.
