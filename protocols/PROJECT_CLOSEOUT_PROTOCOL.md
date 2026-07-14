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

A project reaches `CLOSED` only after a closeout candidate has been prepared, independently audited, approved for merge, merged, and followed by a post-merge attestation that records the actual resulting repository state. An explicit audited incomplete-closeout state may be preserved when completion is impossible.

## 2. Authority boundary

```text
AUTO_PREPARE_AND_PUSH: ALLOWED_ONLY_WITH_VALID_AUTHORIZATION
AUTO_CREATE_CLOSEOUT_PR: ALLOWED_ONLY_WITH_VALID_AUTHORIZATION
AUTO_MERGE: FORBIDDEN
SELF_ACCEPTANCE: FORBIDDEN
INDEPENDENT_CLOSEOUT_AUDIT: REQUIRED
IRREVERSIBLE_EXTERNAL_ACTION: REQUIRES_EXPLICIT_APPROVAL
```

`AUTO_PREPARE_AND_PUSH` and `AUTO_CREATE_CLOSEOUT_PR` are not ambient repository permissions. They are allowed only when at least one currently valid authority record explicitly covers the closeout action:

- a Task Freeze;
- a role assignment;
- a Control Lease; or
- explicit Control Plane authorization.

The authority record must identify its source, scope, repository, branch or task, and relevant base or expected head. Missing, stale, conflicting, or out-of-scope authority fails closed.

The Maker may prepare a closeout candidate and open its PR only within that authorization. The Maker may not act as the final Checker, merge the PR, delete external evidence, or silently omit blocked materials.

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
→ CLOSEOUT_CANDIDATE_CREATED
→ INDEPENDENT_CLOSEOUT_AUDIT
→ CONTROL_PLANE_MERGE_APPROVAL
→ CANDIDATE_MERGED
→ POST_MERGE_ATTESTATION_RECORDED
→ CLOSED
```

The canonical state names above must be identical in the protocol and the manifest field contract.

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

A blocked or incomplete state must preserve the reason, affected materials, attempted actions, remaining owner, and recovery path. It must never be rewritten as `CLOSED` without a new audited candidate and the required post-merge attestation.

## 5. Candidate Manifest semantics

The Candidate Manifest is created before merge at the proposed canonical path:

```text
.adt/tasks/<task-id>/CLOSEOUT_MANIFEST.yaml
```

It belongs to one immutable closeout transaction identified by `closeout_id` and `task_id`.

Before merge it must:

- record the verified base commit;
- record the candidate branch, candidate head, and candidate tree;
- record the closeout PR number or URL;
- record the expected merge method;
- record the Candidate Manifest Blob SHA when available;
- record material inventory, classifications, scans, checks, unresolved items, rollback, authority, and audit state;
- set `merged_commit` to `null`;
- set `resulting_tree` to `null`;
- avoid claiming the final repository state;
- avoid claiming `CANDIDATE_MERGED`, `POST_MERGE_ATTESTATION_RECORDED`, or `CLOSED`.

The Candidate Manifest is the auditable pre-merge claim. It cannot know or predict the actual squash or merge commit SHA.

## 6. Post-Merge Attestation semantics

After the authorized closeout PR is merged, a Post-Merge Attestation must record:

- the unchanged `closeout_id` and `task_id`;
- the original closeout PR;
- the Candidate Manifest Blob SHA;
- the candidate head and candidate tree;
- the actual merged commit;
- the resulting repository tree;
- the actual merge method;
- the independent audit decision and audit record;
- the Control Plane merge authorization evidence;
- the attestation recorder and timestamp.

The canonical default location is a top-level comment on the original merged closeout PR with the heading:

```text
POST_MERGE_CLOSEOUT_ATTESTATION
```

This record belongs to the original closeout transaction. It does not recursively trigger another closeout when all of the following are true:

1. `task_id` is unchanged;
2. `closeout_id` is unchanged;
3. no deliverable, source, governance, or external operational change is introduced;
4. the record only attests facts created by the original closeout merge.

This exemption is narrow. Any wider change, including a source edit, deliverable edit, governance edit, external operational action, changed task identity, or changed closeout identity, starts a new normal work line and follows ordinary authorization and closeout rules.

A repository policy may require a separate attestation-only PR, but that path requires explicit authorization and must use the same narrow exemption. The attestation records the original closeout merge, not its own transport commit.

## 7. Required closeout materials

The inventory must evaluate, where applicable:

- final source and configuration;
- dependency and lock files;
- project state and phase freezes;
- task freezes, decisions, authorization evidence, and accepted scope changes;
- build, test, validation, and audit results;
- changed-file and deletion records;
- startup, deployment, handoff, and recovery instructions;
- rollback or revert instructions;
- evidence manifests and checksums;
- external binary references;
- unresolved findings, limits, and known defects;
- candidate repository, branch, PR, commit, tree, and manifest Blob identifiers.

Final merged commit and resulting tree are recorded by the Post-Merge Attestation, not guessed by the Candidate Manifest.

Absence is valid only when recorded as `NOT_APPLICABLE` with a reason.

## 8. Material classification

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

## 9. Secret, privacy, and license gates

### 9.1 Secret gate

The candidate must fail closed when a probable secret is detected in content, filename, metadata, history introduced by the candidate, or generated archive.

The record must include only safe finding metadata. It must not reproduce the secret value.

### 9.2 Privacy gate

Unredacted personal data, private messages, private account exports, and sensitive identity material are forbidden unless the Task Freeze and repository policy explicitly authorize their storage.

Redaction must be independently reviewable. A Maker declaration alone is insufficient.

### 9.3 License gate

Third-party material requires provenance and a permitted-use status. Unknown ownership is `BLOCKED`, not implicitly allowed.

For external or excluded third-party assets, Git stores the filename or stable identifier, source, license status, checksum when lawful, and reason for non-inclusion.

Completion of these three gates is represented only by the canonical state:

```text
SECRET_PRIVACY_LICENSE_SCAN_COMPLETED
```

## 10. Git and external-binary policy

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

## 11. Closeout branch and PR protocol

The closeout Maker must begin from the verified current default-branch HEAD and must possess valid authority under Section 2.

```text
agent/<allowed-maker-role>/<task-id>-closeout-r<revision>
```

`<allowed-maker-role>` must already be valid under the organization branch protocol. This proposal does not create a new permanent role.

The PR must state:

- task, closeout, and phase identifiers;
- authorization ID, source, scope, branch, base, and authorized current head;
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

## 12. Independent closeout audit

The Checker must be independent of the Maker and verify at least:

1. task, closeout, and phase identity;
2. authorization evidence and scope;
3. base freshness and candidate scope;
4. manifest field-contract conformance;
5. material inventory completeness;
6. deterministic classification;
7. secret, privacy, and license gates;
8. external binary metadata and checksum coverage;
9. unresolved and incomplete states;
10. rollback instructions;
11. no self-acceptance or automatic merge;
12. no material omitted solely to obtain a passing result;
13. repository facts match the Candidate Manifest;
14. final repository facts are deferred to the Post-Merge Attestation.

Allowed audit decisions:

```text
CLOSEOUT_ACCEPTED
CLOSEOUT_ACCEPTED_WITH_RECORDED_LIMITS
CHANGES_REQUESTED
BLOCKED
SUPERSEDED
```

Only the first two may proceed to Control Plane merge approval.

## 13. Incomplete closeout

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

## 14. Rollback and revert

After a closeout merge, rollback must use a new branch created from the current default branch and a reviewed revert commit.

```text
reset: FORBIDDEN
force-push: FORBIDDEN
history deletion: FORBIDDEN
```

The revert PR must reference the Candidate Manifest, Post-Merge Attestation, merged closeout commit, reason for rollback, preserved external evidence, and resulting project status. The previous accepted closeout remains historical evidence and is marked `CLOSEOUT_REVERTED`, not deleted.

## 15. Acceptance matrix

| Test | Fixture | Expected result |
|---|---|---|
| A | A repository-bootstrap project completes with two commits and six governance files | Candidate inventory includes bootstrap freeze, candidate commits, tree/blob identifiers, audit and rollback facts; Post-Merge Attestation records the actual merge; project creation is treated as project work |
| B | Candidate contains a credential-like value | `CLOSEOUT_BLOCKED_SECRET`; no value reproduced in the manifest |
| C | Candidate includes an unredacted private conversation | `CLOSEOUT_BLOCKED_PRIVACY` |
| D | Candidate includes a third-party asset with unknown rights | `CLOSEOUT_BLOCKED_LICENSE` |
| E | Project has a large approved binary in external storage | Git contains metadata and checksum only; audit verifies location and status |
| F | Required large binary has no approved storage location | `CLOSEOUT_BLOCKED_EXTERNAL_STORAGE` |
| G | Default branch changes after the closeout branch was created | `CLOSEOUT_STALE_BASE`; no silent rebase or merge |
| H | Maker attempts to issue the final audit decision | Audit fails for self-acceptance |
| I | Project is abandoned after partial work | `INCOMPLETE_CLOSEOUT_RECORDED` with recovery owner and remaining work |
| J | Accepted closeout must be rolled back | New revert branch and reviewed revert PR; old closeout preserved as `CLOSEOUT_REVERTED` |
| K | Candidate Manifest attempts to include a predicted merged commit | Field-contract conformance fails; `merged_commit` must be `null` before merge |
| L | Post-Merge Attestation uses unchanged task and closeout IDs and introduces no wider change | Attestation is recorded in the original transaction and does not trigger recursive closeout |
| M | Post-Merge record changes source, governance, deliverable, operation, task ID, or closeout ID | A new normal authorized work line is required |
| N | Maker has no valid Task Freeze, assignment, Lease, or explicit Control Plane authorization | Preparation and PR creation fail closed |

Each implementation test must freeze its fixture commit, input paths, expected manifest path, expected branch and PR state, expected terminal status, and explicit PASS/FAIL rule.

## 16. Field contract and implementation boundary

The candidate field contract is:

```text
schemas/CLOSEOUT_MANIFEST_FIELD_CONTRACT.yaml
```

It is a non-executable field contract, not a standard JSON Schema. Conformance is an independent review obligation until a separate implementation workstream supplies an accepted executable schema or deterministic validator.

This candidate defines protocol and field-contract requirements only. It does not:

- implement a validator or executable JSON Schema;
- implement automation;
- create project bindings;
- create runtime assignments or Control Leases;
- add GitHub Actions;
- upload project materials;
- execute closeout for the current Adaptive Digital Team repository;
- declare this protocol accepted.

```text
IMPLEMENTATION_ALLOWED: NO
MERGE_ALLOWED: NO
NEXT_GATE: INDEPENDENT_PROJECT_CLOSEOUT_PROTOCOL_REAUDIT
```
