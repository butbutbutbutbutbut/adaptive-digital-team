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
