# Bootstrap Protocol

1. Read the user task.
2. Read this repository's `AGENTS.md`.
3. Read the fixed project binding when one has been approved.
4. Continue only when the organization repository is identified by a fixed full commit SHA.
5. Fail closed when the binding is missing, conflicting, inaccessible, or stale.

Authority boundaries:

- A single Agent cannot grant itself Control Plane authority.
- An Agent cannot accept its own work.
- An Agent cannot merge its own candidate.
- Irreversible actions require explicit human approval.
