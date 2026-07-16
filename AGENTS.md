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

`BRANCH_SYNC_METHOD` and `PR_FINAL_MERGE_METHOD` are distinct.

`allow_merge_commit`, `allow_squash_merge`, and `allow_rebase_merge` are
GitHub Pull Request final merge method settings. They control how GitHub
merges a PR into the target branch via the PR Merge API. They do not control
ordinary git operations on the feature branch.

`allow_merge_commit=false` means GitHub will not offer or execute a merge
commit when merging the PR. It does not forbid a developer from running
`git merge <target>` on the feature branch to produce an ordinary merge
commit for branch synchronization.

`BRANCH_SYNC_METHOD` must not be treated as `PR_FINAL_MERGE_METHOD`, and
vice versa. Branch sync operations (bringing target changes into the feature
branch during development) and PR final merge (closing the PR into the
target branch) are separate action classes. They must be separately
authorized and separately verified.

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

Immediately before calling the PR Merge API, re-verify live facts:

- repository identity
- PR identity
- exact Base SHA
- exact Head SHA
- PR state
- mergeability
- the authorized merge method is still enabled in repository settings
- applicable required checks
- applicable branch-protection and permission facts (when accessible)

If any authorized binding fact has changed since authorization, stop and
fail closed. Do not proceed to merge.

### Merge method capability mismatch

`MERGE_METHOD_CAPABILITY_MISMATCH` applies only when ALL of the following
facts remain unchanged since authorization:

- repository identity
- PR identity
- Base SHA
- Head SHA
- scope (files and actions in authorization)
- candidate files and their content
- PR state
- mergeability
- a valid independent audit conclusion bound to the exact Head SHA

When repository policy rejects the authorized merge method but all the
above facts are unchanged:

- candidate state is unchanged
- valid independent audit conclusion remains valid
- audit budget is not consumed
- repair budget is not consumed
- repository repair is not triggered
- a full audit rerun is not triggered
- the candidate does not enter a failure gate

The situation routes to `HUMAN_MERGE_METHOD_REAUTHORIZATION` only. The
new authorization may only replace the exact merge method with a different
enabled method. It must not expand any other permission, scope, or gate.

### Drift (not eligible for lightweight re-authorization)

The following changes are genuine drift. None of them may use
`HUMAN_MERGE_METHOD_REAUTHORIZATION` or any lightweight path:

- repository change
- PR identity change
- Base drift (Base SHA differs from authorization)
- Head drift (Head SHA differs from authorization)
- scope change (files or actions outside authorization)
- candidate file change or candidate content change
- PR state change (e.g. CLOSED, MERGED, converted from Draft)
- mergeability change
- permission change
- required-check change
- branch-protection change

When any of the above occurs, stop. Do not silently rebind the old
authorization. Return to the appropriate fact-verification, audit, or
Human gate for the changed fact.

### Merge settings as live facts

The following are live control-plane facts, read from the repository at
execution time. They are not durable repository state and must never be
written to committed files, the PR body, or any durable record as
authoritative bindings:

- enabled PR merge methods (`allow_merge_commit`, `allow_squash_merge`,
  `allow_rebase_merge`)
- PR mergeability
- required status checks
- branch-protection rules
- applicable merge permissions

Each merge-capability gate must re-read these facts live. Stale cached
values are not authoritative.

### Runtime and automation boundaries

Automatic merge, Hermes R1, and automatic scheduling remain unauthorized.
Merge capability preflight is a pre-authorization verification step, not a
Runtime activation.
