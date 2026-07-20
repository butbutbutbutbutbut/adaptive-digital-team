# Contributing to Adaptive Digital Team

Thank you for your interest. ADT uses a structured governance workflow — this is not a
typical open-source repo. Please read this before opening a pull request.

## Workflow

1. **Fork** the repository.
2. **Create a branch** from `main`. Use a descriptive prefix: `hermes/`, `codex/`, `agent/`, `maker/`.
3. **Write your change** — keep it to exactly one task. One task = one branch = one PR.
4. **Run the tests and validator locally:**
   ```bash
   pip install pytest pyyaml
   python scripts/validate_binding.py
   python tests/run_tests.py
   ```
5. **Open a Draft PR** targeting `main`.

## Rules

- **Do not** force-push, rebase, amend, or reset your candidate branch after pushing.
- **Do not** stack PRs — every formal candidate targets `main` directly.
- **Do not** self-accept — the Maker who wrote the change cannot be its Checker.
- **Do not** commit secrets, private material, unapproved binaries, or product-repo changes.
- **Do** keep scope tight — every task has an exact `authorized_write_scope` file list.
- **Do** accept that the Human Holder retains Ready, Merge, and final acceptance.

## Roles during contribution

| Role | Who | What |
|------|-----|------|
| **Maker** | You (the contributor) | Implement within authorized scope |
| **Independent Checker** | Someone who did not write the candidate | Read-only audit |
| **Human Holder** | Repository owner | Ready, Merge, final acceptance |

If you're contributing and no independent Checker is available, the Human Holder will
appoint one. A candidate without independent audit cannot be merged.

## PR lifecycle

```
LOCAL_DRAFT → WRITE_AUTHORIZED → COMMITTED_CANDIDATE → FORMAL_CANDIDATE → AUDIT_ELIGIBLE
```

Each state transition requires validation to pass. The Validator, test suite, and CI
must all pass before a candidate reaches AUDIT_ELIGIBLE.

## Scope enforcement

Every authorized task declares an exact list of files it may touch. The validator
checks this list at commit time, push time, and CI time. Files outside scope cause a
`SCOPE_VIOLATION` and block progress. This is intentional — scope creep is a governance
failure, not a feature request.

## Questions

If you're unsure whether something belongs in a PR, open a Draft PR early and ask.
The Holder will route your question or request a scope amendment if needed.
