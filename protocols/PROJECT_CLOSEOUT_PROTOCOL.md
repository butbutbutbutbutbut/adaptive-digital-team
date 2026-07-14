# Project Closeout Protocol

> Status: `PROPOSAL_CANDIDATE`  
> Implementation: `NOT_IMPLEMENTED`  
> Acceptance: `NOT_ACCEPTED`  
> Base: `main@34a66ac2b11c34c31cbb7e1a4732a13238285d4e`

## 1. Gap statement

Creating, repairing, migrating, or validating a repository is project work. A project is not complete merely because its primary deliverable exists. It must also preserve the materials required to reconstruct what happened, verify the result, continue the work, and roll it back safely.

The closeout protocol therefore applies to repository bootstrap work as well as application, design, audit, migration, research, and operational work.

```text
DELIVERABLE_CREATED
!=
PROJECT_CLOSED
```

A project reaches a closed state only after a closeout candidate has been prepared, independently audited, and merged by authorized human or Control Plane approval, or after an explicit incomplete-closeout state has been preserved.

## 2. Authority boundary

```text
AUTO_PREPARE_AND_PUSH: ALLOWED
AUTO_CREATE_CLOSEOUT_PR: ALLOWED
AUTO_MERGE: FORBIDDEN
SELF_ACCEPTANCE: FORBIDDEN
INDEPENDENT_CLOSEOUT_AUDIT: REQUIRED
IRREVERSIBLE_EXTERNAL_ACTION: REQUIRES_EXPLICIT_APPROVAL
```

The Maker may prepare a closeout candidate and open its PR. The Maker may not act as the final Checker, merge the PR, delete external evidence, or silently omit blocked materials.

## 3. Trigger conditions

Closeout preparation is required when any of the following becomes true:

1. the task acceptance criteria have been met;
2. a phase or repository bootstrap has completed;
3. the user explicitly ends or freezes the project;
4. work is abandoned, superseded, or blocked beyond the allowed retry limit;
5. responsibility is transferred to another Agent, team, repository, or storage system;
6. a rollback or revert closes the active work line.

A repository bootstrap such as `ADT-PHASE1-BOOTSTRAP-20260715-001` is therefore a valid closeout subject.

## 4. Canonical state machine

```text
ACTIVE
→ CLOSEOUT_TRIGGERED
→ MATERIAL_INVENTORY_CREATED
→ CLASSIFICATION_COMPLETED
→ SECRET_PRIVACY_LICENSE_SCAN_COMPLETED
→ CLOSEOUT_MANIFEST_CREATED
→ CLOSEOUT_BRANCH_PUSHED
→ CLOSEOUT_PR_OPEN
→ INDEPENDENT_CLOSEOUT_AUDIT
→ CONTROL_PLANE_MERGE_APPROVAL
→ CLOSED
```

Permitted non-success terminal or holding states:

```text
CLOSEOUT_BLOCKED_SECRET
CLOSEOUT_BLOCKED_PRIVACY
CLOSEOUT_BLOCKED_LICENSE
CLOSEOUT_BLOCKED_EXTERNAL_STORAGE
CLOSEOUT_INCOMPLETE_EVIDENCE
CLOSEOUT_STALE_BASE
CLOSEOUT_CHANGES_REQUESTED
CLOSEOUT_SUPERSEDED
CLOSEOUT_REVERTED
INCOMPLETE_CLOSEOUT_RECORDED
```

A blocked or incomplete state must preserve the reason, affected materials, attempted actions, remaining owner, and recovery path. It must never be rewritten as `CLOSED` without a new audited candidate.

## 5. Required closeout materials

The inventory must evaluate, where applicable:

- final source and configuration;
- dependency and lock files;
- project state and phase freezes;
- task freezes, decisions, and accepted scope changes;
- build, test, validation, and audit results;
- changed-file and deletion records;
- startup, deployment, handoff, and recovery instructions;
- rollback or revert instructions;
- evidence manifests and checksums;
- external binary references;
- unresolved findings, limits, and known defects;
- final repository, branch, PR, commit, and tree identifiers.

Absence is valid only when recorded as `NOT_APPLICABLE` with a reason.

## 6. Material classification

Every inventoried item must receive exactly one primary class:

| Class | Meaning | Default action |
|---|---|---|
| `GIT_TEXT` | Source, configuration, Markdown, JSON, YAML, CSV, or other reviewable text | Commit to the closeout branch |
| `GIT_BINARY_APPROVED` | Small binary explicitly allowed by repository policy and task scope | Commit only with approval and checksum |
| `EXTERNAL_BINARY` | Large or unsuitable binary evidence or source asset | Keep in approved external storage; commit metadata and checksum only |
| `EXCLUDED_SECRET` | Credential, token, cookie, password, private key, or equivalent | Do not upload; block closeout until removed or safely replaced |
| `EXCLUDED_PRIVACY` | Private conversation, personal data, or unredacted sensitive material | Do not upload; require redaction or explicit approved handling |
| `EXCLUDED_LICENSE` | Third-party material without verified permission or provenance | Do not upload; require license resolution or metadata-only reference |
| `EPHEMERAL` | Cache, dependency directory, generated temporary file, or replaceable build residue | Exclude and record rule-based omission |
| `MISSING_REQUIRED` | Required material cannot be located or verified | Fail closed as incomplete evidence |

Classification must be deterministic from repository policy, task freeze, file properties, provenance, and scan results. Convenience is not a valid reason to classify an item as excluded.

## 7. Secret, privacy, and license gates

### 7.1 Secret gate

The candidate must fail closed when a probable secret is detected in content, filename, metadata, history introduced by the candidate, or generated archive.

The record must include only safe finding metadata. It must not reproduce the secret value.

### 7.2 Privacy gate

Unredacted personal data, private messages, private account exports, and sensitive identity material are forbidden unless the task freeze and repository policy explicitly authorize their storage.

Redaction must be independently reviewable. A Maker declaration alone is insufficient.

### 7.3 License gate

Third-party material requires provenance and a permitted-use status. Unknown ownership is `BLOCKED`, not implicitly allowed.

For external or excluded third-party assets, Git stores the filename or stable identifier, source, license status, checksum when lawful, and reason for non-inclusion.

## 8. Git and external-binary policy

Git is the authoritative ledger for text, state, decisions, manifests, checksums, and review history. It is not automatically the storage location for every original asset.

An `EXTERNAL_BINARY` record must include:

- stable logical name;
- byte size;
- SHA-256 when available and lawful;
- media type;
- approved storage class and location identifier;
- provenance and license status;
- privacy status;
- availability status;
- responsible owner;
- recovery or replacement instructions.

Raw credentials, private keys, and prohibited personal data must never be stored externally merely to bypass the Git prohibition.

## 9. Closeout branch and PR protocol

The closeout Maker must begin from the verified current default-branch HEAD.

```text
agent/<allowed-maker-role>/<task-id>-closeout-r<revision>
```

`<allowed-maker-role>` must already be valid under the organization branch protocol. This proposal does not create a new permanent role.

The canonical project manifest path is proposed as:

```text
.adt/tasks/<task-id>/CLOSEOUT_MANIFEST.yaml
```

The PR must state:

- task and phase identifiers;
- verified base and candidate HEAD;
- completion type;
- included and excluded material counts;
- scan results;
- external binary count;
- unresolved items;
- rollback plan;
- Maker identity;
- required independent Checker;
- `AUTO_MERGE: FORBIDDEN`;
- `ACCEPTED: NO` until independent audit and Control Plane approval.

The candidate becomes `CLOSEOUT_STALE_BASE` if the default branch changes before merge. Silent rebase, amend, reset, or force-push is forbidden.

## 10. Independent closeout audit

The Checker must be independent of the Maker and verify at least:

1. task and phase identity;
2. base freshness and candidate scope;
3. manifest-schema validity;
4. material inventory completeness;
5. deterministic classification;
6. secret, privacy, and license gates;
7. external binary metadata and checksum coverage;
8. unresolved and incomplete states;
9. rollback instructions;
10. no self-acceptance or automatic merge;
11. no material omitted solely to obtain a passing result;
12. repository facts match the closeout report.

Allowed audit decisions:

```text
CLOSEOUT_ACCEPTED
CLOSEOUT_ACCEPTED_WITH_RECORDED_LIMITS
CHANGES_REQUESTED
BLOCKED
SUPERSEDED
```

Only the first two may proceed to Control Plane merge approval.

## 11. Incomplete closeout

A project that cannot produce a complete closeout must still produce an audited incomplete record when safe to do so.

The record must include:

- last verified repository and commit state;
- work completed;
- work not completed;
- unavailable or blocked materials;
- scan or policy blockers;
- external dependencies;
- branch and PR status;
- recovery owner and next action;
- explicit statement that the project is not `CLOSED`.

Incomplete closeout is evidence preservation, not acceptance.

## 12. Rollback and revert

After a closeout merge, rollback must use a new branch created from the current default branch and a reviewed revert commit.

```text
reset: FORBIDDEN
force-push: FORBIDDEN
history deletion: FORBIDDEN
```

The revert PR must reference the closeout manifest, merged closeout commit, reason for rollback, preserved external evidence, and resulting project status. The previous accepted closeout remains historical evidence and is marked `CLOSEOUT_REVERTED`, not deleted.

## 13. Acceptance matrix

| Test | Fixture | Expected result |
|---|---|---|
| A | A repository-bootstrap project completes with two commits and six governance files | Closeout inventory includes bootstrap freeze, commits, tree/blob identifiers, audit and rollback facts; project creation is treated as project work |
| B | Candidate contains a credential-like value | `CLOSEOUT_BLOCKED_SECRET`; no value reproduced in the manifest |
| C | Candidate includes an unredacted private conversation | `CLOSEOUT_BLOCKED_PRIVACY` |
| D | Candidate includes a third-party asset with unknown rights | `CLOSEOUT_BLOCKED_LICENSE` |
| E | Project has a large approved binary in external storage | Git contains metadata and checksum only; audit verifies location and status |
| F | Required large binary has no approved storage location | `CLOSEOUT_BLOCKED_EXTERNAL_STORAGE` |
| G | Default branch changes after the closeout branch was created | `CLOSEOUT_STALE_BASE`; no silent rebase or merge |
| H | Maker attempts to issue the final audit decision | Audit fails for self-acceptance |
| I | Project is abandoned after partial work | `INCOMPLETE_CLOSEOUT_RECORDED` with recovery owner and remaining work |
| J | Accepted closeout must be rolled back | New revert branch and reviewed revert PR; old closeout preserved as `CLOSEOUT_REVERTED` |

Each implementation test must freeze its fixture commit, input paths, expected manifest path, expected branch and PR state, expected terminal status, and explicit PASS/FAIL rule.

## 14. Proposal boundary

This candidate defines protocol and schema requirements only.

It does not:

- implement automation;
- create project bindings;
- create runtime assignments or Control Leases;
- add GitHub Actions;
- upload project materials;
- close the current Adaptive Digital Team repository project;
- declare this protocol accepted.

```text
IMPLEMENTATION_ALLOWED: NO
MERGE_ALLOWED: NO
NEXT_GATE: INDEPENDENT_PROJECT_CLOSEOUT_PROTOCOL_AUDIT
```
