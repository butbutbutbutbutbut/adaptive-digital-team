# He Weizhi Site Governance Case Study

> Version: R1  
> Transport revision: R2  
> Status: `CANDIDATE_FOR_INDEPENDENT_REVIEW`  
> Evidence class: `PROJECT_LEVEL_GOVERNANCE_CASE`  
> Source repository: `butbutbutbutbutbut/he-weizhi-site`  
> Frozen source HEAD: `ae5b105742da41cd1d8954dc5c6f487a95de7687`  
> Target repository base: `a8661ca6934aa21980d9439dd055bcb239aceb15`

## 1. Purpose

This report records the He Weizhi personal website repository as a project-level case study for the governance ideas later formalized in the Adaptive Digital Team repository.

The case is useful because the governance method did not begin as an abstract organization chart. It emerged from a live project involving application development, design direction, multiple AI execution instances, evidence collection, independent review, failed attempts, migration, recovery, and rollback.

This report does not copy application source or design assets. It references fixed Git commits and pull requests as the evidence ledger.

## 2. Authorization and scope

```text
AUTHORIZATION_ID:
ADT-CASE-STUDY-20260715-001

AUTHORIZATION_SOURCE:
User directive "写报告，送审" in the current project conversation,
sent at 2026-07-15T05:32:23Z.

AUTHORIZED_REPOSITORY:
butbutbutbutbutbut/adaptive-digital-team

AUTHORIZED_BASE:
ae5f0b725374a4cd9108c631cd5e081e0c19c010

AUTHORIZED_BRANCH:
agent/control/20260715-0532-he-weizhi-governance-case-r1

AUTHORIZED_SCOPE:
- add this project-level governance case report;
- cite fixed He Weizhi Site commits and pull requests;
- create a review pull request;
- do not modify application source, runtime, bindings, leases, schemas,
  protocols, automation, or the default branch.
```

```text
MIGRATION_AUTHORIZATION_ID:
ADT-CASE-STUDY-CLEAN-BASE-MIGRATION-20260715-001

MIGRATED_FROM_PR:
3

MIGRATED_FROM_HEAD:
580fd6d75a2dc4f91ac7de5bf5a384ad24696af9

AUTHORIZED_BASE:
a8661ca6934aa21980d9439dd055bcb239aceb15

AUTHORIZED_BRANCH:
agent/control/he-weizhi-governance-case-r2
```

## 3. Case boundary

The source case is the private repository:

```text
butbutbutbutbutbut/he-weizhi-site
```

The frozen evidence boundary for this report is:

```text
SOURCE_HEAD:
ae5b105742da41cd1d8954dc5c6f487a95de7687

SOURCE_HEAD_MESSAGE:
docs: integrate accepted Patagon R1S reference audit
```

All claims in this report are limited to repository facts at or before that commit.

The case covers project governance behavior. It does not claim that the website repository already implements the complete organization-level Adaptive Digital Team runtime.

## 4. Project context

The He Weizhi Site project combines:

- an interactive personal website and portfolio;
- web and desktop workstreams;
- visual direction and engineering boundaries;
- multiple AI execution instances and windows;
- external reference observation and evidence capture;
- repeated protocol, audit, migration, and recovery work;
- explicit human approval gates.

This produced a practical coordination problem:

```text
How can work survive model replacement, context loss, execution failure,
parallel agents, and changing phases without losing authority, evidence,
or rollback safety?
```

The project's answer became a Git-centered governance method in which the human retains final authority, one AI or execution line acts as Maker, another acts as independent Checker, and GitHub preserves the shared facts.

## 5. Evidence timeline

| Event | Pull request | Merged main commit | Governance evidence |
|---|---:|---|---|
| Accidental direct-main change corrected through forward history | [#4](https://github.com/butbutbutbutbutbut/he-weizhi-site/pull/4) | `24d091b76e98ce0e224153a1b9b1e8b96e7475da` | The accidental commit `a063405e7ccfe7865fad3a331061cdfad7ccbd82` was not erased. A separate revert branch and reviewed revert commit restored `main`; reset and force-push were explicitly excluded. |
| R0 evidence boundary frozen | [#6](https://github.com/butbutbutbutbutbut/he-weizhi-site/pull/6) | `db388741182080613003e12864ae431bfabbf189` | A fixed evidence boundary was established before later observation and tooling work. |
| R1 observation protocol defined | [#7](https://github.com/butbutbutbutbutbut/he-weizhi-site/pull/7) | `ae43dcfe6e51525531d8c15952615dd42e906981` | Execution was separated from protocol approval; reference access remained blocked until the preceding gate passed. |
| R1S sandbox interaction protocol defined | [#8](https://github.com/butbutbutbutbutbut/he-weizhi-site/pull/8) | `b30e5e48d015ca27dd994ac6b1bbafe21da67459` | A constrained sandbox protocol was reviewed before pilot execution. |
| Stale protocol status corrected | [#9](https://github.com/butbutbutbutbutbut/he-weizhi-site/pull/9) | `2d8eb8654b91b4617a33afb2896f07944482e1db` | Post-merge state drift was repaired as a new visible commit rather than silently rewriting prior history. |
| Tooling safety and evidence gates accepted | [#10](https://github.com/butbutbutbutbutbut/he-weizhi-site/pull/10) | `42c1cee0d893bad267a35c25683bd1b67bc9e788` | Action budgets, screenshot budgets, domain gates, control isolation, and frozen runner hashes were treated as auditable prerequisites. |
| Sui sandbox pilot recorded | [#11](https://github.com/butbutbutbutbutbut/he-weizhi-site/pull/11) | `a3e2db05714bdbfe7885e36fd922f9410c4a062a` | Passing, blocked, diagnostic, and unresolved outcomes were preserved separately; CT06 remained an explicit limit rather than being rewritten as success. |
| Agent GitOps continuity method added | [#12](https://github.com/butbutbutbutbutbut/he-weizhi-site/pull/12) | `e1e0c48c99a0c950514b8e46397516d81f03f860` | The project experience was formalized into Maker–Checker, three-layer facts, `HANDOFF_READY`, Evidence Ledger, gates, recovery, and rollback. |
| Method marked validated in project | [#13](https://github.com/butbutbutbutbutbut/he-weizhi-site/pull/13) | `bff061181faff8e44c977e88339693e8248bbde1` | The method status changed from `READY_FOR_REVIEW` to `VALIDATED_IN_PROJECT` without claiming organization-level validation. |
| Adaptive Digital Team proposal accepted in source project | [#14](https://github.com/butbutbutbutbutbut/he-weizhi-site/pull/14) | `334ee56c1c08164c6548f6825ff5c63aa6ba13de` | The repository-as-prompt principle, project-first cold start, Task Freeze, single active Control Lease, and falsifiable tests were derived from the project method. |
| Accepted Patagon history integrated through migration-integrity review | [#15](https://github.com/butbutbutbutbutbut/he-weizhi-site/pull/15) | `ae5b105742da41cd1d8954dc5c6f487a95de7687` | Migration preserved a frozen base, exact commit count and order, independent integrity review, and prohibitions on rebase, amend, reset, and force-push. |

## 6. Governance pattern mapping

### 6.1 Human + AI Maker + AI Checker

The project evolved toward a three-party control structure:

```text
Human / Design Director
→ defines intent, scope, risk tolerance, and final decision

AI Maker / Execution Plane
→ performs authorized work on an isolated branch and produces evidence

Independent AI Checker / Control or Audit Plane
→ verifies repository facts, scope, evidence, and gate conditions
```

The important distinction is functional independence, not model branding. Changing a model name, window, or alias does not create Checker independence when the same actor made the candidate diff.

### 6.2 GitHub as the fact plane

GitHub served four functions in the project:

1. engineering state source through commits, trees, branches, diffs, and PRs;
2. asynchronous handoff channel between execution and audit instances;
3. evidence ledger for manifests, records, checksums, status, and limits;
4. transaction and rollback system through reviewed merge and revert history.

Chat summaries supported coordination but did not replace repository facts.

### 6.3 Frozen scope before execution

The project repeatedly fixed:

- complete base commit SHA;
- branch and owner;
- allowed and forbidden paths;
- permitted references or external domains;
- expected records and checks;
- merge and rollback constraints;
- the next valid gate.

This reduced the ability of an execution instance to reinterpret its own task after work had started.

### 6.4 Maker–Checker separation

The source history distinguishes between:

```text
candidate creation
independent audit
human or Control Plane approval
merge
```

A completed candidate did not automatically become accepted. PRs explicitly preserved `MERGE_ALLOWED: NO` until the required audit or approval gate was satisfied.

### 6.5 Evidence classes and fail-closed behavior

The Sui pilot separated simulated output, diagnostics, run records, manifests, screenshots, and final project conclusions. It also preserved non-success outcomes:

- external-domain-gated cases were stopped;
- CT06 remained `UNRESOLVED_AFTER_MAX_ATTEMPTS`;
- a protocol-deviating attempt was retained as evidence;
- local evidence existence was not treated as equivalent to accepted delivery;
- no formal R1 observation was claimed from sandbox-only evidence.

This is a practical example of fail-closed governance: uncertainty and incomplete evidence reduce authority rather than being rounded up to success.

### 6.6 Failure and recovery as permanent evidence

The repository contains several negative or corrective records:

- an accidental direct-main commit followed by a reviewed forward revert;
- a stale status correction after merge;
- invalidated or limited pilot records;
- a migration whose integrity had to be verified separately from its inherited semantic review.

These records were not deleted to make the history appear clean. They became inputs to later gates and organization-level rules.

### 6.7 Model replaceability

The continuity method treats Codex, Hermes, Sol, and other models or windows as replaceable instances. Durable authority and project state are not attached to an instance name. Continuity comes from frozen repository facts, handoff records, and explicit ownership.

### 6.8 Repository as prompt

The organization-level principle emerged from this project-level observation:

```text
A new instance should not need the full old conversation.
It should reconstruct the task from repository structure, fixed state,
authority records, branch history, evidence, and the active gate.
```

The He Weizhi Site repository therefore serves as provenance for the later proposal that a project repository should encode enough state and protocol to restart work deterministically.

## 7. What the case demonstrates

At project level, the evidence supports the following claims:

- multiple AI execution instances can coordinate through versioned repository facts;
- human authority can remain distinct from AI execution and AI audit;
- branch ownership and fixed bases can constrain scope;
- evidence manifests and status records can preserve incomplete or adverse results;
- a project can repair mistakes through forward history without reset or force-push;
- practical project incidents can be converted into reusable governance rules;
- the resulting Agent GitOps continuity method reached `VALIDATED_IN_PROJECT`.

## 8. What the case does not demonstrate

This report must not be used to claim any of the following:

- organization-level validation of the full Adaptive Digital Team design;
- successful `.adt/project-binding.yaml` integration;
- a working runtime role-assignment system;
- an active or tested Control Lease implementation;
- a complete single-link cold-start pilot;
- executable closeout schema validation;
- automatic orchestration, scheduling, or merge;
- general performance superiority over other collaboration methods;
- that every source PR was semantically successful;
- that project-level validation automatically transfers to other repositories.

## 9. Case status

```text
CASE_STATUS:
CANDIDATE_FOR_INDEPENDENT_REVIEW

SOURCE_METHOD_STATUS:
VALIDATED_IN_PROJECT

SOURCE_METHOD_COMMIT:
bff061181faff8e44c977e88339693e8248bbde1

SOURCE_CASE_HEAD:
ae5b105742da41cd1d8954dc5c6f487a95de7687

ORGANIZATION_LEVEL_VALIDATION:
NOT_ESTABLISHED

PROJECT_BINDING:
NOT_CREATED

RUNTIME_IMPLEMENTATION:
NOT_PRESENT

GENERALIZATION_CLAIM:
FORBIDDEN

APPLICATION_SOURCE_COPIED:
NO

BINARY_EVIDENCE_COPIED:
NO
```

## 10. Independent audit request

The independent Checker should verify:

1. the target branch begins from `a8661ca6934aa21980d9439dd055bcb239aceb15`;
2. this report is the only changed file;
3. the source repository is fixed at `ae5b105742da41cd1d8954dc5c6f487a95de7687`;
4. every referenced PR and merged commit pair is accurate;
5. the accidental-main incident and forward revert are represented accurately;
6. the Sui CT06 limitation and external-domain stops are preserved;
7. `VALIDATED_IN_PROJECT` is not upgraded to organization-level acceptance;
8. no application source, binary evidence, runtime, binding, lease, protocol, schema, or automation is introduced;
9. the report distinguishes governance evidence from promotional claims;
10. the candidate remains unmerged until independent review and explicit Control Plane approval.

Allowed audit decisions:

```text
CASE_STUDY_ACCEPTED
CASE_STUDY_ACCEPTED_WITH_RECORDED_LIMITS
CHANGES_REQUESTED
BLOCKED
SUPERSEDED
```

## 11. Gate

```text
IMPLEMENTATION:
NONE

MAIN_MODIFICATION:
NONE

SELF_ACCEPTANCE:
FORBIDDEN

AUTO_MERGE:
FORBIDDEN

MERGE_ALLOWED:
NO

NEXT_GATE:
INDEPENDENT_HE_WEIZHI_GOVERNANCE_CASE_AUDIT
```
