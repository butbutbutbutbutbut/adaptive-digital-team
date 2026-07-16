# Agent Governance

- Maker and Checker responsibilities must remain separate.
- Self-acceptance is forbidden.
- Automatic merge is forbidden.
- Do not reset, force-push, or amend a submitted candidate.
- Do not commit secrets, private material, or unapproved binary assets.
- After the initial bootstrap commit, every change must use a separate branch and pull request.
- Rollback must use a new revert branch and a reviewed revert commit.
- Missing authority, state conflicts, or incomplete evidence must fail closed.

## Multimodal evidence

Metadata integrity does not establish semantic evidence acceptance.

When a claim depends on images, audio, video, traces, or other external
binaries, the independent Checker must obtain and review the actual
evidence modality before acceptance or merge authorization.

Missing binary access or unperformed modal review fails closed and
cannot be downgraded to a recorded limitation.

## Instruction routing and authority

All cross-Agent, cross-window, cross-repository, repository-write,
audit, and merge instructions must follow
`protocols/INSTRUCTION_ROUTING_AND_AUTHORITY.md`.

Missing or conflicting FROM, TO, EXECUTOR, CHECKER, REPOSITORY, or
AUTHORIZATION_ID fields fail closed.

CC status grants no execution, acceptance, audit, or merge authority.

Maker, Checker, PR-creation authority, evidence acceptance, and merge
authority must remain distinct.

## Persistent Holder adopted governance specification

`protocols/PERSISTENT_HOLDER_CONTROL_PLANE.md` is a
`ADOPTED_GOVERNANCE_SPECIFICATION`. The Persistent Holder is the resident
control-plane interface and Task Router, not a third Maker. Makers and
Checkers are temporary task roles; the Holder may be Checker only when the
independence test in that protocol passes.

The Holder routes publication but does not Push directly. A task-scoped
Publish Lease cannot expand its parent authorization. Ready, Merge, branch
deletion, final acceptance, and final visual or engineering acceptance are
Human-only. PR10 is a read-only source candidate and must not be merged,
cherry-picked, updated, closed, or deleted.

Persistent Holder runtime, Hermes R1, and automatic scheduling remain
unimplemented and unauthorized.

## Human-facing governance communication

- Key fields use `English field（中文解释）` when addressing Human.
- Preserve the original machine values for Authorization ID, Lease ID, SHA,
  branch, repository, file path, and fixed state values.
- Chinese explanations may clarify but must not change authority, scope,
  state, gate, or restriction. Mark only key fields and high-risk actions.
- If a Chinese explanation conflicts with a machine value, fail closed.

## Lightweight execution routing

Use `protocols/LIGHTWEIGHT_EXECUTION_FLOW.md` for L0/L1/L2 routing. L0
defaults to one Maker, one independent Checker, and one final Human decision.
Non-blocking metadata must be recorded as a limit and must not create a new
commit loop. Human-only Ready, Merge, branch deletion, final acceptance, and
runtime activation remain unchanged.

## Audit receipt validation

Audit receipts must be validated against the exact target facts (`TASK_ID`,
`AUTHORIZATION_ID`, repository, PR, exact Base, exact Head, Checker
identity, current PR state) before any state registration, per
`protocols/PERSISTENT_HOLDER_CONTROL_PLANE.md` and
`protocols/LIGHTWEIGHT_EXECUTION_FLOW.md`.

A target-fact mismatch is `INVALID_AUDIT_RECEIPT / TARGET_FACT_MISMATCH`:
the receipt is rejected without changing candidate state, consuming audit or
repair budget, triggering repository repair or a full audit rerun, or moving
any gate. Checker input errors are receipt defects, not candidate defects.
A corrected receipt is a receipt retry within the same gate, not a new full
audit, and non-permission receipt errors do not require new Human
authorization. Authority, scope, Base/Head drift, Checker conflict, Runtime,
and history-rewrite violations remain fail-closed.

## Merge method capability preflight

### Branch sync vs. final merge

`BRANCH_SYNC_METHOD` and `PR_FINAL_MERGE_METHOD` are distinct. The branch
sync method (rebase, merge, squash used during development and branch
updates) has narrower authority than the final PR merge method, which is a
Human-only gate. Do not conflate them.

### Pre-authorization verification

Before requesting Human authorization for `PR_FINAL_MERGE_METHOD`, the
Holder or its delegate must verify live repository facts:

- repository identity
- PR number and state (must be OPEN)
- exact Base SHA
- exact Head SHA
- mergeability (`MERGEABLE`, `UNKNOWN`, or `CONFLICTING`)
- enabled PR merge methods (from repository settings)
- required checks and protection rules (when accessible)

Only the target repository's currently enabled PR merge methods may be
presented to Human. Disabled or unavailable methods must not appear as
options.

### Merge capability unknown

When merge capability cannot be read from the repository (API failure,
insufficient permissions, ambiguous response) or when enabled methods
conflict with each other:

`MERGE_CAPABILITY_UNKNOWN / FAIL_CLOSED`

Do not proceed to Human authorization. Do not default to any merge method.
Do not guess.

### Merge authorization binding

A PR final merge authorization must precisely bind:

- repository
- PR number
- exact Head SHA at time of authorization
- exact PR merge method (one of the currently enabled methods)
- branch deletion decision (delete / retain after merge)

Any drift in these bindings between authorization and execution fails closed.

### Pre-execution re-verification

Immediately before merge execution, re-verify:

- exact Head SHA matches the authorization
- merge capability (enabled methods) has not changed

If Head or merge capability has changed since authorization, stop and fail
closed.

### Merge method capability mismatch

If an authorized merge method is rejected by repository policy but the
candidate has not drifted (same Head, same Base, same scope, same PR state,
same mergeability):

`MERGE_METHOD_CAPABILITY_MISMATCH`

This does not:
- invalidate the audit
- consume audit or repair budget
- trigger code repair or a full re-audit

It enters `HUMAN_MERGE_METHOD_REAUTHORIZATION` only. The Human selects a
different enabled method; no other gate is reopened.

### Scope or state drift

If Base, Head, scope, PR state, or mergeability has changed since
authorization, fail closed. Return to the appropriate Human gate; do not
silently rebind or widen scope.

### Merge settings as live facts

Repository merge settings (enabled methods, protection rules, required
checks) are live control-plane facts. They are not written to durable
repository state, committed files, or the PR body as authoritative bindings.
They must be re-read at each merge-capability gate.

### Runtime and automation boundaries

Automatic merge, Hermes R1, and automatic scheduling remain unauthorized.
Merge capability preflight is a pre-authorization verification step, not a
Runtime activation.
