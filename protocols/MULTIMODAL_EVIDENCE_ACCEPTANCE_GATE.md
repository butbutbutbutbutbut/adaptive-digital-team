# Multimodal Evidence Acceptance Gate

> Status: `ACTIVE`  
> Adopted by PR: `6`  
> Adoption main SHA: `c911df097632f4ba9496601fa618d267cf562182`  
> Authorization: `ADT-MULTIMODAL-EVIDENCE-GATE-R1-20260715-001`  
> Base: `79da69258056e059a07f35a9d1d32f2c698b473e`

## 1. Purpose

This protocol separates metadata integrity, binary availability, actual modality review, manifest mapping, semantic support, and final acceptance. A passing repository or metadata audit does not establish that evidence content was reviewed or that it supports the claimed conclusion.

It applies whenever a claim depends on images, audio, video, traces, screen recordings, externally retained binary batches, or another non-text modality.

## 2. Required state record

Every governed evidence decision must record:

```text
EVIDENCE_METADATA_AUDIT:
PASS / FAIL / NOT_PERFORMED

EVIDENCE_BINARY_AVAILABILITY:
PASS / FAIL / NOT_APPLICABLE

ACTUAL_MODAL_REVIEW_PERFORMED:
YES / NO

REVIEWED_MODALITIES:
TEXT / IMAGE / AUDIO / VIDEO / TRACE / OTHER

REVIEW_SCOPE:
FULL / SAMPLED / NONE

MANIFEST_TO_BINARY_MAPPING:
PASS / FAIL / NOT_APPLICABLE

SEMANTIC_SUPPORT_AUDIT:
PASS / FAIL / NOT_PERFORMED

EVIDENCE_ACCEPTANCE:
FINAL / PROVISIONAL / BLOCKED
```

Multiple reviewed modalities must be listed explicitly. `TEXT` alone is insufficient when the claim depends on a non-text modality.

## 3. Gate meanings

### 3.1 Metadata audit

`EVIDENCE_METADATA_AUDIT: PASS` means declared filenames, counts, hashes, manifests, ledgers, references, and repository records are internally consistent within the audited scope.

It does not mean the referenced binaries were accessible, opened, viewed, heard, played, interpreted, or semantically accepted.

### 3.2 Binary availability

`EVIDENCE_BINARY_AVAILABILITY: PASS` means the independent Checker obtained usable access to the original governed binaries in the authorized form.

`NOT_APPLICABLE` is valid only when the claim does not depend on external or non-text binary evidence. The reason must be recorded.

Missing, inaccessible, corrupted, substituted, renamed, transcoded, regenerated, or unverifiable required binaries produce `FAIL`.

### 3.3 Actual modal review

`ACTUAL_MODAL_REVIEW_PERFORMED: YES` means the independent Checker actually inspected the evidence using the modality required to evaluate the claim.

Examples include:

- viewing governed images at usable resolution;
- listening to required audio;
- playing required video or reviewing the full necessary sequence;
- opening and interpreting traces with an appropriate viewer or parser;
- inspecting another modality through an authorized method that preserves evidence meaning.

Reading a manifest, filename, hash list, summary, or prior actor's description is not actual modal review.

### 3.4 Manifest-to-binary mapping

`MANIFEST_TO_BINARY_MAPPING: PASS` means each reviewed binary is matched to its intended manifest or ledger record through authorized filenames, counts, digests, identifiers, sequence positions, or another frozen mapping rule.

Hash verification without content review is metadata evidence only. Content review without mapping does not establish which governed record was reviewed.

### 3.5 Semantic support audit

`SEMANTIC_SUPPORT_AUDIT: PASS` means the actually reviewed evidence supports the stated conclusion within the declared review scope and recorded limits.

The Checker must distinguish:

- what the evidence directly shows;
- what is inferred;
- what remains unresolved;
- what lies outside the reviewed scope;
- what is contradicted.

## 4. Final evidence acceptance gate

`EVIDENCE_ACCEPTANCE: FINAL` requires:

```text
EVIDENCE_METADATA_AUDIT:
PASS

EVIDENCE_BINARY_AVAILABILITY:
PASS or a justified NOT_APPLICABLE

ACTUAL_MODAL_REVIEW_PERFORMED:
YES

MANIFEST_TO_BINARY_MAPPING:
PASS or a justified NOT_APPLICABLE

SEMANTIC_SUPPORT_AUDIT:
PASS
```

When a claim depends on external binaries, `NOT_APPLICABLE` is not permitted for binary availability or manifest-to-binary mapping.

Missing any required core step produces:

```text
EVIDENCE_ACCEPTANCE:
BLOCKED
```

`PROVISIONAL` may record an explicitly incomplete intermediate state. It grants no final semantic acceptance and no merge authority for claims that depend on the missing review.

## 5. Recorded limits cannot replace missing review

`ACCEPTED_WITH_RECORDED_LIMITS`, equivalent wording, or a recorded-limits section must not cover any of the following:

- original binaries are inaccessible;
- the Checker did not actually open or inspect the evidence;
- image, audio, video, trace, or other modality content was not checked;
- manifest records were not mapped to actual files;
- semantic support for the conclusion was not evaluated.

Recorded limits may constrain a completed review. They cannot convert an unperformed review into an accepted review.

## 6. Full and sampled review boundaries

### 6.1 Full-batch claims

A claim that a complete batch passes requires review of the complete batch and:

```text
REVIEW_SCOPE:
FULL
```

The audit record must include the governed batch size and the number actually reviewed.

### 6.2 Sampled review

Sampling is allowed only when the Task Freeze explicitly authorizes it before execution. The authorization must define:

- purpose;
- population;
- sample size or selection rule;
- selection method;
- conclusions the sample may support;
- conclusions the sample may not support.

An unauthorized sample fails closed.

A sampled review supports conclusions only within the authorized sample scope and must record:

```text
REVIEW_SCOPE:
SAMPLED
```

It must not be represented as full-batch acceptance.

### 6.3 Sequence-dependent claims

Claims about sequence, transition, state change, before-and-after relationships, continuity, timing, smoothness, recovery, or temporal causality require review of the complete necessary sequence.

Isolated stills cannot establish motion smoothness, timing, animation reduction, or intermediate transition behavior unless the Task Freeze defines a sufficient ordered-frame method.

A single delayed still cannot establish static behavior over the preceding interval.

## 7. Modality-specific minimums

### Images

The Checker must open the actual governed images at a resolution sufficient for the claim and verify their mapping to the manifest.

### Audio

The Checker must listen to the required duration and channels needed for the claim.

### Video

The Checker must play or inspect the complete necessary segment, preserving sequence and timing.

### Traces

The Checker must open and interpret the trace with the required viewer or parser and record the reviewed range.

### Other

The Task Freeze must define the method required to perceive and interpret the modality without substituting metadata for content.

## 8. Merge authorization gate

A pull request whose acceptance depends on external multimodal evidence may receive merge authorization only when the authorization text explicitly includes:

```text
ACTUAL_MODAL_REVIEW_PERFORMED:
YES

REVIEW_SCOPE:
FULL / AUTHORIZED_SAMPLED

SEMANTIC_SUPPORT_AUDIT:
PASS
```

For `AUTHORIZED_SAMPLED`, the Task Freeze authorization and the allowed conclusion boundary must be referenced.

When any required field is absent, or when the values are `NO`, `NONE`, or `NOT_PERFORMED`:

```text
MERGE_ALLOWED:
NO
```

Technical mergeability, repository integrity, metadata integrity, binary existence, hash matching, or prior recorded limits do not override this gate.

## 9. Contradiction and correction

When actual modal review contradicts an earlier accepted or provisional claim:

- preserve the original repository and review history;
- record the contradiction explicitly;
- downgrade unsupported conclusions;
- use a new branch, forward commit, and independently reviewed pull request;
- do not reset, amend, rebase, force-push, or erase the earlier record;
- block downstream use of the contradicted conclusion until remediation and re-audit.

## 10. Monad incident application

For `ADT-INCIDENT-MONAD-VISUAL-AUDIT-GAP-20260715-001`, the actual review record is:

```text
PACKAGE_INTEGRITY:
PASS

ACTUAL_MODAL_REVIEW_PERFORMED:
YES

REVIEW_SCOPE:
FULL_53_STILLS

SEMANTIC_SUPPORT_AUDIT:
FAIL

SEMANTIC_CONTRADICTION_FOUND:
YES

UNSUPPORTED_TEMPORAL_CLAIMS_FOUND:
YES

PREVIOUS_ACCEPTANCE:
PREMATURE

CORRECTION_METHOD:
FORWARD_ONLY

EVIDENCE_ACCEPTANCE:
BLOCKED
```

The package handoff and workflow correction are independent gates. Neither establishes that the Monad visual evidence passed.

## 11. Governance

```text
PROTOCOL_STATUS:
ACTIVE

ADOPTED_BY_PR:
6

ADOPTION_MAIN_SHA:
c911df097632f4ba9496601fa618d267cf562182

SELF_ACCEPTANCE:
FORBIDDEN

AUTO_MERGE:
FORBIDDEN

HISTORY_REWRITE:
FORBIDDEN

PR_6_MERGE_AUTHORITY:
CONSUMED

DOCUMENT_GATE:
CLOSED
```
