# Adaptive Digital Team

Organization-level governance repository for project-bound AI teams.

> The repository itself is the prompt.

This repository defines the shared rules used by project repositories:
bootstrap order, authority boundaries, Maker–Checker separation, task
freezing, branch and pull-request policy, audit requirements, rollback,
and project closeout.

It does not contain business application code and is not a standalone
runtime.

## Current verified state

| Area | Status |
|---|---|
| Repository visibility | PRIVATE |
| Default branch | `main` |
| Phase 1 bootstrap baseline | FROZEN |
| Project-first bootstrap order | VERIFIED |
| Agent governance rules | PRESENT |
| Repository design proposal | PRESENT |
| Repository-as-prompt principle | PRESENT |
| Project Closeout Protocol specification | PRESENT_IN_MAIN |
| Closeout Manifest field contract | PRESENT_IN_MAIN |
| Closeout runtime implementation | NOT_IMPLEMENTED |
| Executable manifest validator | NOT_IMPLEMENTED |
| Project bindings | NONE |
| Runtime role assignments | NONE |
| Active Control Lease | NONE |
| Automation | NONE |

## Canonical entry path

This repository is not the first file an Agent should read.

A new Agent must enter through a project repository:

1. Read the user task.
2. Read the project repository root `AGENTS.md`.
3. Read `.adt/project-binding.yaml`.
4. Resolve this repository through the binding's fixed full commit SHA.
5. Read `BOOTSTRAP.md`.
6. Read the project `PROJECT_STATE.md`.
7. Verify default-branch HEAD, branch, diff and pull-request state.
8. Read runtime assignments and Control Lease when present.

A missing, floating, stale or conflicting binding fails closed.

## Repository map

```text
/
├─ README.md
├─ BOOTSTRAP.md
├─ AGENTS.md
├─ PROJECT_STATE.md
├─ docs/
│  ├─ ADAPTIVE_DIGITAL_TEAM_REPOSITORY_PROPOSAL_R1.md
│  └─ REPOSITORY_AS_PROMPT_PRINCIPLE_R1.md
├─ protocols/
│  └─ PROJECT_CLOSEOUT_PROTOCOL.md
└─ schemas/
   └─ CLOSEOUT_MANIFEST_FIELD_CONTRACT.yaml
