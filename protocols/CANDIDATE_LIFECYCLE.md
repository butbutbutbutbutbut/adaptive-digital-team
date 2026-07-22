# Candidate Lifecycle

PROTOCOL_STATUS: `ADOPTED_GOVERNANCE_SPECIFICATION`

## Normative source statement

This document is the **single normative source** for ADT candidate lifecycle rules.
All other documents that reference candidate lifecycle, identity, fingerprint,
scope enforcement, state machine, CI gates, or audit receipt rules MUST defer
to this document. Where any other document conflicts with this one, this document
prevails for the concepts it governs.

## This document supersedes

| Replaced Content | Original Location |
|---|---|
| Candidate Lifecycle R1 (full section) | `AGENTS.md` |
| Runtime-derived identity (all modes) | `AGENTS.md`, `protocols/LIGHTWEIGHT_EXECUTION_FLOW.md`, `protocols/PERSISTENT_HOLDER_CONTROL_PLANE.md` |
| Durable state boundary | `AGENTS.md` |
| Candidate fingerprint | `AGENTS.md`, `protocols/LIGHTWEIGHT_EXECUTION_FLOW.md`, `protocols/PERSISTENT_HOLDER_CONTROL_PLANE.md` |
| PR topology rules | `AGENTS.md`, `protocols/LIGHTWEIGHT_EXECUTION_FLOW.md`, `protocols/PERSISTENT_HOLDER_CONTROL_PLANE.md` |
| CI gate | `AGENTS.md`, `protocols/LIGHTWEIGHT_EXECUTION_FLOW.md`, `protocols/PERSISTENT_HOLDER_CONTROL_PLANE.md` |
| Audit receipt validation | `AGENTS.md`, `protocols/LIGHTWEIGHT_EXECUTION_FLOW.md`, `protocols/PERSISTENT_HOLDER_CONTROL_PLANE.md` |
| Final realtime gate (PRE_MERGE_REALTIME_GATE) | `AGENTS.md`, `protocols/LIGHTWEIGHT_EXECUTION_FLOW.md`, `protocols/PERSISTENT_HOLDER_CONTROL_PLANE.md` |
| Lightweight repair and merge safety | `AGENTS.md`, `protocols/LIGHTWEIGHT_EXECUTION_FLOW.md` |
| Candidate state machine | `protocols/LIGHTWEIGHT_EXECUTION_FLOW.md`, `protocols/PERSISTENT_HOLDER_CONTROL_PLANE.md` |
| Pre-write execution gate | `protocols/LIGHTWEIGHT_EXECUTION_FLOW.md`, `protocols/PERSISTENT_HOLDER_CONTROL_PLANE.md` |
| Scope enforcement | `protocols/LIGHTWEIGHT_EXECUTION_FLOW.md`, `protocols/PERSISTENT_HOLDER_CONTROL_PLANE.md` |
| Remote candidate history immutability | `protocols/LIGHTWEIGHT_EXECUTION_FLOW.md`, `protocols/PERSISTENT_HOLDER_CONTROL_PLANE.md` |
| Fingerprint registrar | `protocols/PERSISTENT_HOLDER_CONTROL_PLANE.md` |

Agents and holders SHOULD reference this document directly for all lifecycle rules.
Compatibility entries in other documents remain valid only as summaries with
explicit pointers to this document.

## Single formal candidate topology

The normative equation is:

```text
ONE_TASK = ONE_BRANCH = ONE_PR = BASE_MAIN
```

Rules:

- Every formal candidate PR targets `main` directly.
- A PR whose `base_ref` is not `main` fails as `STACKED_PR_PROHIBITED`.
- CI must trigger for every pull request, including a pull request aimed at another candidate branch; a stacked PR cannot hide by avoiding validation.
- Do not repair an unmerged parent candidate through a child PR.
- Before independent audit, append repair commits directly to the original candidate branch and audit the new Head.
- After a candidate is merged, a newly discovered problem starts from the latest `main` as a new task, new branch, and new PR.
- A former child PR must not be retargeted to `main` after its parent is squash-merged.
- One task may contain multiple append-only commits on its single branch, but it still has exactly one PR and one direct Base: `main`.
- Every formal candidate branch starts from verified `origin/main`.

## Runtime-derived identity

Current identity is resolved live at every relevant gate — never trusted from
committed state. The reference implementation is `scripts/validate_binding.py`.

### Push identity

- `push_branch` is derived only from `GITHUB_REF`.
- Only `refs/heads/<branch>` is accepted.
- Missing, empty, tag, notes, pull-merge, or any other ref format is `HARD_STOP`.
- The identity chain is exact: `git HEAD = GITHUB_SHA = origin/<push_branch>`.
- There is no fallback to a branch cached in `PROJECT_STATE.md`.

### Pull-request identity

- `head_ref` and `head_sha` come from the pull-request event source Head.
- `base_ref` and `base_sha` come from the pull-request event Base.
- `base_ref` must be `main`.
- `refs/pull/*/merge` and synthetic merge commits are not candidate identity.
- The source Head must equal `origin/<head_ref>` and the checkout used for validation must be that source Head.
- Required equality: `head_sha = origin/<head_ref> = checked-out HEAD`.

### Local and pre-merge identity

- Current Head is `git rev-parse HEAD`.
- Current main is `origin/main`.
- Candidate remote is `origin/<candidate_branch>`.
- Current Base, Head, remote refs, changed files, and fingerprint must not be read from committed cache fields.
- Changed files are derived from `sorted(git diff base...head)`.

## Durable state boundary

`PROJECT_STATE.md` stores stable task facts only:

- `task_id`
- `repository`
- `branch`
- `starting_base_sha`
- `authorized_write_scope`
- `authority`
- `current_gate`
- `implementation_status`

It must not store the current Head, current main, current event SHA, current remote
branch SHA, or current candidate hash. A `resolved_head`, when present in historical
material, is only a historical anchor: it need not equal the current Head, but it must
be a commit reachable from current history. It must never reintroduce SHA self-reference.

The following are live facts and must be resolved at every relevant gate:

- current Head;
- current main;
- current event SHA;
- current remote branch SHA;
- current candidate hash;
- PR state and mergeability;
- checks and protection;
- current user action and blockers.

## Candidate fingerprint

A deterministic SHA-256 fingerprint binds the normalized fields:

```text
repository
base_ref
base_sha
head_ref
head_sha
sorted(changed_files)
```

The canonical algorithm (reference: `scripts/validate_binding.py`, functions `canonical_fields` and `candidate_fingerprint`):

1. Normalize all six fields: stringify, sort changed files, produce canonical JSON with sorted keys and compact separators (`sort_keys=True, separators=(",", ":")`).
2. SHA-256 the UTF-8 encoded JSON.
3. Output the hexadecimal digest.

Validation output must show both the raw normalized fields (`FINGERPRINT_FIELDS`) and
the hash (`CANDIDATE_FINGERPRINT`). The hash is runtime evidence and is not committed
into the candidate it identifies.

The independent audit receipt, Holder Ready authorization, and Holder Merge authorization
must bind the same runtime fingerprint. A change to repository, branch, Base SHA, Head SHA,
or changed files immediately produces:

```text
AUDIT_BINDING: INVALID
READY_AUTHORIZATION: INVALID
MERGE_AUTHORIZATION: INVALID
```

Old audit or authorization cannot be silently rebound to a new candidate identity.

## PR topology rules

All formal candidate PRs must satisfy:

- Target `main` directly. `base_ref != main` is `STACKED_PR_PROHIBITED`.
- Pull-request validation runs regardless of requested Base, so stacked candidates fail visibly.
- A defect discovered before audit is fixed by an append-only commit on the same branch and the new Head is re-audited.
- A defect discovered after merge starts a new task from the latest main.
- A child PR is never the repair mechanism for an unmerged parent and is never retargeted after parent squash merge.

## Candidate state machine

Every formal candidate transitions through this state machine:

```
LOCAL_DRAFT
    → TASK_AUTHORIZED
    → MACHINE_PRECHECK
    → WRITE_AUTHORIZED
    → COMMITTED
    → PUSHED
    → DRAFT_PR
    → CI_PASS
    → FORMAL_CANDIDATE
    → INDEPENDENT_AUDIT
```

### State definitions

| State | Condition |
|-------|-----------|
| `LOCAL_DRAFT` | Local branch; no machine precheck passed or precheck failed. Not a formal candidate. |
| `TASK_AUTHORIZED` | Human has pre-granted conditional write authorization (AUTHORIZATION_ID + scope). |
| `WRITE_AUTHORIZED` | Machine precheck passed; write authorization activated. Local writes permitted within scope. |
| `COMMITTED_CANDIDATE` | At least one commit beyond exact base; pushed to remote. |
| `FORMAL_CANDIDATE` | Formal task branch, non-zero commits, exact base ancestry valid, scope compliant, candidate fingerprint computable. PR event: Head/Base match declaration. |
| `AUDIT_ELIGIBLE` | FORMAL_CANDIDATE + has open PR + CI passed + fingerprint exists. Ready for independent audit. |

### State rules

- Human can pre-grant conditional write permission; only machine precheck activates it.
- Human does not need to re-carry precheck results between windows.
- Agent self-reported PASS cannot substitute for machine facts.
- Local drafts are not formal candidates and cannot be audited.
- `LOCAL_DRAFT` cannot declare `AUDIT_ELIGIBLE`.
- Zero commits cannot declare `FORMAL_CANDIDATE`.
- No fingerprint cannot declare `AUDIT_ELIGIBLE`.
- No PR or CI cannot declare `AUDIT_ELIGIBLE`.

## Pre-write execution gate

Before any local write, the validator enforces (machine-enforceable):

1. Detached HEAD → `HARD_STOP` (except CI checkout using `GITHUB_REF` / `GITHUB_HEAD_REF` / `GITHUB_BASE_REF`)
2. Current branch must match task-declared branch
3. Exact Base must exist as a commit
4. Exact Base must be an ancestor of current HEAD
5. Candidate must derive from `main` (no non-main parent)
6. Base drift (main advanced beyond declared base) → `HARD_STOP`

## Scope enforcement

The Validator reads `authorized_write_scope` and verifies all actual changed
files are within the authorized set:

- Supports explicit file paths and controlled glob patterns (`fnmatch`)
- Duplicate paths in scope → `SCOPE_VIOLATION`
- Absolute paths in scope → `SCOPE_VIOLATION`
- `..` traversal paths → `SCOPE_VIOLATION`
- Files outside scope → `SCOPE_VIOLATION`
- Missing or empty scope in live candidate mode → fail-closed
- Static text validation does not depend on Git

Coverage modes:

- **Local live**: committed + staged + unstaged + untracked files
- **CI `pull_request`**: candidate Head vs target Base
- **CI push (branch)**: push branch vs `origin/main`
- **CI push (main)**: merge commit vs parent commit

## CI gate

The control plane must verify live that:

- push CI is attached to the current source Head and succeeded;
- pull-request CI is attached to the current source Head and succeeded;
- static validation, complete tests, and live validation all actually ran;
- no required step was skipped or soft-failed;
- `continue-on-error` occurrences are zero.

CI success does not grant Ready or Merge authority. Waiting on CI is not candidate
failure and does not advance progress. CI success is evidence only, not acceptance.

## Audit receipt validation

Before registering a receipt, the Holder verifies task, authorization, repository,
PR, `base_ref`, Base SHA, `head_ref`, Head SHA, sorted changed files, Checker identity,
Checker independence, PR state, and candidate fingerprint.

A transcription or target mismatch is `INVALID_AUDIT_RECEIPT / TARGET_FACT_MISMATCH`;
it is a receipt defect, not automatically a candidate defect, and it consumes no
audit or repair budget.

A valid receipt becomes invalid as soon as any fingerprint field changes. A corrected
receipt for unchanged candidate facts is a retry within the same gate.

Authority conflict, scope violation, candidate drift, Checker conflict, runtime
activation, or history rewrite remains fail-closed.

## Final realtime gate (PRE_MERGE_REALTIME_GATE)

Immediately before Ready or Merge, the control plane executes `PRE_MERGE_REALTIME_GATE`
with the expected audit fingerprint and freshly resolves:

- repository;
- `origin/main`;
- `origin/<candidate_branch>`;
- current Head;
- Base ref and SHA;
- candidate branch and Head SHA;
- sorted changed files;
- workspace cleanliness;
- exact authorized scope coverage.

It must confirm Base is still `main`, Base SHA unchanged, Head unchanged, files unchanged,
runtime fingerprint equals the expected fingerprint, workspace is clean, and actual changed
files equal the authorized path list.

Required result:

```text
base_ref == main
base_sha unchanged
head_sha unchanged
changed_files unchanged
runtime fingerprint == expected fingerprint
workspace clean
sorted(changed_files) == sorted(authorized_write_scope)
```

Any mismatch is `HARD_STOP` / `FINGERPRINT_MISMATCH` and invalidates old audit, Ready
authorization, and Merge authorization. No Ready or Merge decision may continue on old evidence.

## Lightweight repair and merge safety

A non-blocking metadata defect does not justify a new PR. A real pre-audit candidate
defect is repaired on the same branch. Scope expansion requires new Human authorization.

A valid audit finding may be repaired only after authority is verified. The repair remains
on the original branch and PR, inside scope. The new Head invalidates the previous
fingerprint and audit. The Checker reviews the new Head and new fingerprint. A second PR
is prohibited for the same unmerged candidate.

Merge capability must be read live before presenting options. Merge-method capability
mismatch alone may route to precise method reauthorization only when repository, PR, Base,
Head, fingerprint, scope, state, mergeability, checks, and valid audit are unchanged.

## Receipt and authorization binding

The audit receipt and Holder authorizations for Ready and Merge must bind the same
fingerprint as the valid independent audit.

Any repository, Base SHA, Head SHA, branch, or changed-file drift yields:

```text
AUDIT_BINDING: VALID | INVALID
READY_AUTHORIZATION: VALID | INVALID
MERGE_AUTHORIZATION: VALID | INVALID
```

Old evidence cannot cross a Head change, repair commit, Base update, branch change,
file change, or repository change. A new Head requires new runtime fields, new fingerprint,
and new independent audit.

Ready and Merge authorizations must bind the same fingerprint as the valid independent audit.
Any Base SHA, Head SHA, branch, changed-file set, or repository change invalidates all three
old bindings. No old authorization may be silently rebound.

## Remote candidate history immutability

Candidate branches are protected by a two-layer defense:

### Layer 1 — Ruleset (physical block)

The `candidate-history-protection` ruleset blocks `non_fast_forward` pushes and
branch `deletion` on all formal candidate prefixes (`hermes/**`, `codex/**`,
`agent/**`, `maker/**`). This is the primary enforcement layer. CI MUST NOT claim
it prevents force-push — the ruleset does.

### Layer 2 — CI detection and audit

The `validate_candidate_history.py` validator runs on `push`, `delete`, and
`pull_request` events. It detects:

- forced pushes (`event.forced == true`);
- branch deletions;
- non-fast-forward ancestry (before is not ancestor of after);
- missing or unresolvable `before` / `after` fields;
- `before` commit missing (history was demolished);
- illegal branch-creation base (new branch not derived from `main`).

All detection paths fail closed: unresolvable ancestry, missing event fields,
and unresolvable origin/main produce `HARD_STOP`.

### Permanent disqualification

Once a candidate branch is determined to have suffered a history rewrite:

1. The branch is **permanently** disqualified.
2. The associated PR permanently loses Audit, Ready, and Merge eligibility.
3. Subsequent normal commits on the same branch do **not** auto-recover.
4. A new branch and new PR are required.

Disqualification is persisted in a durable evidence layer outside the candidate
branch: `refs/adt/disqualified/<safe-branch-name>`. This ref is a permanent
marker that survives branch deletion and force-push.

### PR eligibility gate

On every `pull_request` event, the PR is checked against the disqualification
registry. A PR whose head branch is disqualified is `BLOCKED_BY_HISTORY` and
cannot proceed to Audit, Ready, or Merge.

### Security

- `pull_request_target` is **not** used to execute untrusted fork code.
- Write permission (`contents: write`) is scoped exclusively to the
  `history-check` job on trusted same-repository `push` / `delete` events.
- Fork PRs receive only `contents: read`.

## Progress accounting

Numeric progress requires a finite pre-bound plan. Only independently verified units
or registered Human decisions count. Planned, dispatched, receipt-received, waiting,
elapsed time, token use, and unverified background claims do not count. Recalculation
must show old percentage, new percentage, and exact reason. Progress never substitutes
for audit, Ready, Merge, or acceptance.

## Failure routing

| Failure | Meaning |
|---|---|
| `STACKED_PR_PROHIBITED` | PR Base is not main; no audit or authorization can proceed. |
| `INVALID_AUDIT_RECEIPT` | Target facts or Checker submission are invalid; candidate is not automatically defective. |
| `CANDIDATE_FAILURE` | Implementation or evidence itself violates requirements. |
| `STATE_DRIFT` | Live Base, Head, branch, repository, files, PR, checks, or protection changed. |
| `FINGERPRINT_MISMATCH` | Runtime identity differs from audited identity. |
| `BLOCKED_BY_HISTORY` | Candidate branch or associated PR has been permanently disqualified due to prior history rewrite. A new branch and new PR are required. |
| `CAPABILITY_UNKNOWN` | Required live capability cannot be read; stop without guessing. |

## Fingerprint registrar appendix

The canonical fingerprint algorithm is implemented in `scripts/validate_binding.py`.
The key functions are:

- `canonical_fields(fields: dict) -> dict`: normalizes the six fingerprint fields
  (stringify all values, sort `changed_files`).
- `candidate_fingerprint(fields: dict) -> str`: produces `SHA-256(canonical_fields)`
  using JSON with `sort_keys=True, separators=(",", ":")`.

The fingerprint is a **live evidence identifier**. It is never committed into the
candidate it identifies. Repository, Base, Head, branch, or changed-file drift creates
a different fingerprint.

Validation output must include both `FINGERPRINT_FIELDS` (the raw normalized fields)
and `CANDIDATE_FINGERPRINT` (the SHA-256 hex digest).

## Compatibility preservation

This document is an additive consolidation of pre-existing lifecycle rules spread across
`AGENTS.md`, `protocols/LIGHTWEIGHT_EXECUTION_FLOW.md`, and `protocols/PERSISTENT_HOLDER_CONTROL_PLANE.md`.
It does not invent new rules. The pre-existing regression set remains a compatibility
baseline; passing new identity tests cannot waive an older safety or authority rule.

Dispatch Cards, Progress Receipts, valid-vs-invalid audit receipt classification,
finite repair handling, Human-action clarity, live merge-capability preflight, reviewed
revert rollback, counter-objective checks, and remote history immutability remain required
wherever their conditions apply.
