# Instruction Routing and Authority

Status:
CANDIDATE_FOR_INDEPENDENT_REVIEW

Authorization:
ADT-INSTRUCTION-ROUTING-AND-AUTHORITY-R1-20260715-001

Base:
b02d72ecd6597d98b2ccc3f7a8fe2a4410b9151c

## 1. Scope

This protocol applies to:

- cross-Agent instructions;
- cross-window instructions;
- cross-repository instructions;
- repository write authorizations;
- audit requests;
- merge authorizations;
- supersession and rollback instructions.

## 2. Required instruction header

Every governed instruction must contain the following fields before the instruction body:

```text
FROM:
TO:
CC:
EXECUTOR:
CHECKER:
REPOSITORY:
SUBJECT:
AUTHORIZATION_ID:
```

### Field definitions

`FROM:` identifies the instruction issuer and the authority-bearing principal responsible for the authorization.

`TO:` identifies the formal recipient and the recipient of the execution or audit result.

`CC:` identifies parties informed only. CC status does not grant execution, audit, acceptance, or merge authority.

`EXECUTOR:` identifies the actor authorized to perform modifications, commits, pushes, closures, or merges.

`CHECKER:` identifies the independent actor authorized to verify the candidate result. The Checker must not be the Executor for the same candidate.

`REPOSITORY:` identifies the single `owner/repository` to which the authorization applies.

`SUBJECT:` identifies the precise matter authorized. It must not be interpreted as permission for adjacent tasks.

`AUTHORIZATION_ID:` is the unique authorization identifier used for receipt, audit, consumption, and traceability.

## 3. Role rules

1. `TO` does not automatically equal `EXECUTOR`.
2. When `TO` and `EXECUTOR` are the same actor, both fields must still be completed explicitly.
3. `CC` has no execution, acceptance, audit, or merge authority.
4. `EXECUTOR` must not change merely because an instruction was forwarded.
5. `CHECKER` must remain independent from the `EXECUTOR` for the same candidate.
6. A Maker must not accept its own candidate.
7. PR-creation authority, content-acceptance authority, and merge authority must be granted separately.
8. Audit passage does not automatically grant merge authority.
9. Merge authority must not be inferred from `CC`, historical authorization, or adjacent work.
10. Authorization applies only to the named repository, subject, authorization ID, and Executor.

## 4. Fail-closed conditions

```text
MISSING_FROM:
GATE_BLOCKED

MISSING_TO:
GATE_BLOCKED

MISSING_EXECUTOR:
NO_WRITE_ALLOWED

MISSING_CHECKER:
NO_ACCEPTANCE_OR_MERGE_ALLOWED

MISSING_REPOSITORY:
NO_REPOSITORY_ACTION_ALLOWED

MISSING_AUTHORIZATION_ID:
NO_WRITE_ALLOWED

EXECUTOR_CHECKER_CONFLICT:
SELF_ACCEPTANCE_BLOCKED

ROLE_CONFLICT_OR_AMBIGUITY:
GATE_BLOCKED
```

Missing roles must not be inferred from names, windows, context, historical habits, prior assignments, or neighboring tasks.

## 5. Forwarding rules

- A forwarded instruction must preserve the complete original header and `AUTHORIZATION_ID`.
- Forwarding must not convert `CC` into `EXECUTOR`.
- Forwarding must not replace `CHECKER`.
- Forwarding must not expand repository, path, action, scope, acceptance, or merge authority.
- Changing `EXECUTOR`, `CHECKER`, repository, or scope requires a new authorization.
- `FORWARDED_BY:` may be added, but it must not overwrite `FROM:`.

## 6. Standard execution receipt

Every execution receipt must contain at least:

```text
FROM:
TO:
CC:
EXECUTOR:
AUTHORIZATION_ID:
RESULT:
CURRENT_ACTION:
```

A receipt involving repository writes must also contain:

```text
REPOSITORY:
BASE_SHA:
HEAD_SHA:
CHANGED_FILES:
AUTHORITY:
NEXT_GATE:
```

Allowed `RESULT` values are:

```text
CREATED
UPDATED
MERGED
CLOSED
COMPLETED
GATE_BLOCKED
FAILED
```

A vague result must not replace the actual repository or governance state.

## 7. Authority consumption

- A one-time write authorization must be marked `CONSUMED` after the authorized action completes.
- Merge authorization applies only to the specified PR, Base, Head, and merge method.
- A change in Head, Base, file scope, or commit count invalidates the previous merge authorization.
- Unconsumed authority must not be transferred to another Executor.
- Consumed authority must not be reused.

## 8. Candidate gate

```text
SELF_ACCEPTANCE:
FORBIDDEN

AUTO_MERGE:
FORBIDDEN

HISTORY_REWRITE:
FORBIDDEN

PR_CREATION_AUTHORITY:
AUTHORIZED

MERGE_AUTHORITY:
NOT_AUTHORIZED

NEXT_GATE:
INDEPENDENT_INSTRUCTION_ROUTING_PROTOCOL_AUDIT
```
