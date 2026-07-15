# Monad Visual Audit Gap — 2026-07-15

```text
INCIDENT_ID:
ADT-INCIDENT-MONAD-VISUAL-AUDIT-GAP-20260715-001

INCIDENT_TYPE:
GOVERNANCE_WORKFLOW_GAP

TRIGGER:
CHECKER_OVER-INFERENCE

ROOT_CAUSE:
METADATA_AUDIT, BINARY_AVAILABILITY, ACTUAL_MODAL_REVIEW,
AND SEMANTIC_ACCEPTANCE WERE NOT SEPARATED AS MANDATORY GATES

REPOSITORY_INTEGRITY:
PASS

METADATA_INTEGRITY:
PASS

HISTORY_REWRITE:
FORBIDDEN
```

## 1. Preserved history

He Weizhi Site PR #16 was legally merged as commit `b0bf4f9cac4b9d40211b689998b961789df2c407`. Adaptive Digital Team PR #5 was also legally merged as commit `79da69258056e059a07f35a9d1d32f2c698b473e`.

Neither merge damaged repository integrity or metadata integrity. Their history must remain visible. This incident is corrected through new forward commits and reviewed pull requests, not through deletion, reset, amend, rebase, force-push, or replacement of prior records.

## 2. Audit gap

The PR #16 repository records identified 53 active PNG evidence records and stated that the PNG binaries were retained externally. The Control Plane verified repository state, manifests, ledgers, filenames, counts, SHA references, and recorded limits, but did not obtain and inspect the 53 actual PNG files before semantic acceptance was stated.

Metadata verification was therefore upgraded prematurely into semantic evidence acceptance.

The user identified the missing modality review. Monad was immediately downgraded to:

```text
MONAD_REPOSITORY_DELIVERY:
MERGED

MONAD_METADATA_AUDIT:
PASS

MONAD_BINARY_AVAILABILITY:
PENDING_HANDOFF

MONAD_VISUAL_EVIDENCE_AUDIT:
NOT_PERFORMED

MONAD_SEMANTIC_ACCEPTANCE:
NOT_YET_FINAL

MONAD_USAGE_AS_ACCEPTED_VISUAL_REFERENCE:
BLOCKED
```

Hermes was instructed to hand off the original evidence package without rescreenshotting, transcoding, compressing, renaming, replacing, or modifying PR #16.

## 3. Actual full visual review

The original evidence package was subsequently obtained and reviewed across all 53 stills.

```text
PACKAGE_INTEGRITY:
PASS

ACTUAL_MODAL_REVIEW_PERFORMED:
YES

REVIEW_SCOPE:
FULL_53_STILLS

SEMANTIC_SUPPORT_AUDIT:
FAIL

EVIDENCE_ACCEPTANCE:
BLOCKED
```

The review produced:

```text
MON-FULL-FORWARD:
PARTIAL_SUPPORT

MON-FULL-REVERSE:
PARTIAL_SUPPORT

MON-SECTION-BOUNDARY:
PARTIAL_SUPPORT

MON-TITLE-NAV-SYNC:
NOT_SUPPORTED

MON-STRONG-TO-READING:
PARTIAL_SUPPORT

MON-BURST-ORDER:
PARTIAL_SUPPORT

MON-STATIC-READING:
NOT_SUPPORTED

MON-REFRESH-RECOVERY:
CONTRADICTED

MON-REDUCE:
PARTIAL_SUPPORT
```

## 4. Confirmed contradiction

The previous refresh claim stated:

```text
All four refresh points recovered to initial hero state.
```

The actual evidence showed:

```text
Hero refresh remained at hero.
Section refresh remained at section.
Body refresh remained at body.
End refresh remained at end.
```

The supported interpretation is:

```text
Refresh preserved or restored the current scroll position.
```

The old hero-recovery conclusion is contradicted.

## 5. Unsupported temporal and state claims

The reviewed stills did not visibly establish navigation highlighting synchronized with title and body state. `MON-TITLE-NAV-SYNC` is therefore not supported.

A single screenshot captured after 12 seconds cannot demonstrate that the page remained static throughout the interval. `MON-STATIC-READING` is therefore not supported.

Static screenshots cannot establish motion smoothness, the magnitude of Reduced Motion changes, or complete transition behavior. Those conclusions remain partial or unsupported until continuous frames or video are reviewed.

A persistent Cookie dialog also obstructed page content and reduced the evidentiary value of affected frames.

## 6. Current Monad status

```text
REPOSITORY_INTEGRITY:
PASS

METADATA_INTEGRITY:
PASS

VISUAL_EVIDENCE_AUDIT:
COMPLETED

SEMANTIC_SUPPORT_AUDIT:
FAIL

EVIDENCE_ACCEPTANCE:
BLOCKED_PENDING_REMEDIATION

MONAD_USAGE_AS_ACCEPTED_VISUAL_REFERENCE:
BLOCKED
```

Manifest, ledger, filenames, and SHA records remain valid as metadata facts. They do not establish the failed semantic conclusions.

## 7. Forward correction and remediation

Hermes is authorized under:

```text
HE-WEIZHI-MONAD-VISUAL-AUDIT-CORRECTION-20260715-001
```

to correct only the authorized semantic observation and submission records and to add a visual-audit correction record. Original evidence, manifests, ledgers, filenames, and hashes must remain unchanged.

Remediation evidence must:

- handle the Cookie dialog first;
- use video or continuous same-position frames for temporal claims;
- record STATIC at `t0 / t4 / t8 / t12`;
- capture title, navigation state, and body state together for TITLE-NAV-SYNC;
- provide paired normal/reduce sequences at the same position;
- provide continuous boundary frames or short video for section smoothness;
- avoid re-running the already supported refresh scroll-restoration conclusion.

## 8. Workflow correction

This repository adds `protocols/MULTIMODAL_EVIDENCE_ACCEPTANCE_GATE.md` and an AGENTS rule separating:

- metadata audit;
- binary availability;
- actual modal review;
- manifest-to-binary mapping;
- semantic support audit;
- final evidence acceptance.

The correction is not evidence that the governance system had already succeeded. The system preserved facts and history, but it omitted a mandatory modal-review gate. Human supervision detected the omission, and the repair proceeds forward-only.

## 9. Remaining gates

Two independent tracks remain:

```text
1. Monad remediation evidence and independent visual re-audit
2. Independent audit of the ADT multimodal evidence acceptance gate
```

The evidence package handoff does not equal workflow repair. Workflow repair does not equal Monad visual evidence acceptance.

```text
SELF_ACCEPTANCE:
FORBIDDEN

MERGE_ALLOWED:
NO

NEXT_GATE:
INDEPENDENT_MULTIMODAL_EVIDENCE_GATE_AUDIT
```
