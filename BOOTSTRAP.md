# Bootstrap Protocol

This file is not a standalone entry point.

It may be read only after the following project-first sequence has completed:

1. Read the user task.
2. Read the project repository root `AGENTS.md`.
3. Read the project repository `.adt/project-binding.yaml`.
4. Resolve this organization repository and this `BOOTSTRAP.md` through the binding's fixed full commit SHA.

After entering through that fixed binding:

5. Read the project repository `PROJECT_STATE.md`.
6. Verify the project Git default-branch HEAD, diff, branch and pull-request state.
7. Read approved runtime assignments and Control Lease only when those files exist in the project repository.
8. Fail closed when the binding is missing, conflicting, inaccessible, stale, or does not reference a fixed full commit SHA.

Authority boundaries:

- A single Agent cannot grant itself Control Plane authority.
- An Agent cannot accept its own work.
- An Agent cannot merge its own candidate.
- Irreversible actions require explicit human approval.
