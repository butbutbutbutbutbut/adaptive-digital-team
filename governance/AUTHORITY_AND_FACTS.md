# Authority and Facts

ADT separates **fact authority** (what *is*) from **action authority** (who
*may do what*). Facts are resolved from durable sources. Actions require Human
authorization.

## Fact authority

Facts are claims about reality that cannot be changed through language. ADT
recognizes these fact classes:

### Human intent, preference, and acceptance facts

The Human Holder's stated goals, authorizations, preferences, and acceptance
decisions are facts. They are recorded in authorization cards, Dispatch Cards,
and acceptance records. Only the Human Holder can create or change these facts.
No agent can infer, reinterpret, or override Human intent.

### Repository, SHA, PR, CI, and file machine facts

Machine facts come from Git, GitHub, CI systems, and the filesystem. These
include: branch names, commit SHAs, PR numbers and states, CI run results, file
contents, and workspace state. Machine facts are resolved live at every gate —
they are never trusted from cached or committed state.

### Fixed-version specification facts

Protocol documents (`AGENTS.md`, `METHODOLOGY.md`, `protocols/*.md`,
`governance/*.md`) at a given commit are fixed-version facts. A spec at SHA `X`
is the spec for that candidate. Spec changes require a separate authorized task
and a new candidate.

### Project history facts

Past commits, merged PRs, audit records, and acceptance records are immutable
history facts. They cannot be rewritten, amended, or rebased. Rollback uses a
new revert branch and reviewed revert commit.

### Personal memory facts

Individual Human and agent memories, conversation logs, and private notes are
personal facts. They are not shared governance facts unless explicitly recorded
in the repository. Memory is never a substitute for live machine facts.

## Action authority

Action authority defines who may perform which actions. All action authority
flows from the Human Holder.

### Write authority

Who may write to which repository, branch, and files. Write authority:

- Is granted per task, per branch, per exact file list
- Must be explicitly stated in an authorization card
- Is not inherited from role identity alone
- Expires when the task gate advances past implementation

Project Control and Task Holder default to **no write access**. Only a
designated Maker receives write authority, and only within its authorized scope.

### Ready, Merge, and deletion authority

Only the Human Holder may execute Ready, Merge, or branch deletion. These are
governance actions, not implementation actions. No agent may Ready or Merge its
own work. No agent may delete branches.

### Runtime activation authority

Only the Human Holder may activate runtime systems, deploy candidates, or
trigger external effects. Governance documents describe activation rules; they
do not self-activate.

### Scope change authority

Only the Human Holder may expand or change the authorized scope of a task.
Scope drift without reauthorization fails closed.

## FACT_SOURCE_REBIND

When two fact sources conflict (e.g., `PROJECT_STATE.md` says branch `X` but
`git branch` shows branch `Y`), the system enters `FACT_SOURCE_REBIND`:

1. **Stop.** Do not write, do not push, do not proceed.
2. **Report** both fact sources and the conflict to the Human Holder.
3. **Wait** for Human resolution before continuing.

The repository is the durable prompt. Machine facts resolved live from Git and
GitHub take priority over committed cache fields. When live resolution is
impossible, the system fails closed.

## Key principles

1. **Humans can change goals and authorizations, but cannot change machine facts
   through language.** Saying "the branch is clean" does not make it clean. Only
   live resolution determines machine facts.

2. **Fact authority and action authority are separate.** Knowing a fact (e.g.,
   the current HEAD SHA) does not grant permission to act on it (e.g., push to
   that branch). Action authority must be separately and explicitly granted.

3. **Authority is per-task, not per-role.** A role identity (Maker, Checker,
   etc.) is a capability template. Actual authority to exercise that capability
   requires a task-specific authorization card with exact repository, branch,
   Base, and scope.

4. **Default deny.** Without explicit authorization, all actions are forbidden.
   Ambiguous authority fails closed. Missing authorization fails closed.
