# Role Model

## Topology

```
Human Holder
    │
    └── Project Control ──────────────────────────┐
            │                                      │
            └── Task Holder ──────────────────────┐│
                    │                             ││
                    ├── Maker (sub-agent)          ││
                    │                              ││
                    └── Independent Checker        ││
                        (sub-agent)                ││
                                                   ││
            (receipts, conclusions, facts) ◄───────┘│
    ◄───────────────────────────────────────────────┘
    │
    └── Human final authorization (Ready, Merge, Accept)
```

The topology is a tree, not a pipeline. Authority flows down; evidence and
receipts flow up. No role has authority over a role above it.

## Authority matrix

| Action | Human Holder | Project Control | Task Holder | Maker | Independent Checker |
|--------|:---:|:---:|:---:|:---:|:---:|
| Set project direction | **Yes** | No | No | No | No |
| Authorize task scope | **Yes** | No | No | No | No |
| Expand scope | **Yes** | No | No | No | No |
| Verify repository facts | Read | **Yes** | **Yes** | Read | Read |
| Classify and route tasks | No | **Yes** | No | No | No |
| Orchestrate multiple Task Holders | No | **Yes** | No | No | No |
| Spawn Task Holders | No | **Yes** | No | No | No |
| Freeze Checker Target Packet | No | No | **Yes** | No | No |
| Dispatch Maker | No | No | **Yes** | No | No |
| Dispatch Checker | No | No | **Yes** | No | No |
| Write within authorized scope | No | No* | No | **Yes** | No |
| Create Draft PR | No | No* | No | **Yes** | No |
| Push to candidate branch | No | No* | No | **Yes** | No |
| Self-audit own work | — | — | — | **Forbidden** | — |
| Audit any candidate (read-only) | Read | Read | Read | Read | **Yes** |
| Veto a candidate | No | No | No | No | **Yes** |
| Recommend Ready | No | No | No | No | **Yes** |
| Execute Ready | **Yes** | No | No | No | No |
| Execute Merge | **Yes** | No | No | No | No |
| Delete branch | **Yes** | No | No | No | No |
| Final acceptance | **Yes** | No | No | No | No |
| Activate runtime | **Yes** | No | No | No | No |
| Change authorization scope | **Yes** | No | No | No | No |
| Present executable Human actions | No | **Yes** | No | No | No |

\* Project Control defaults to **no repository write access**. Write access
requires separate explicit Human authorization per task.

## Role definitions

### Human Holder

The Human Holder is the only source of direction, authorization, and final
acceptance. The Holder:

- Sets project direction and priorities
- Authorizes task scope, repository, branch, Base, and permitted paths
- Executes Ready, Merge, branch deletion, and final acceptance
- Activates runtime and destructive external actions
- Can change goals and authorizations at any time
- Cannot change machine facts through language alone

### Project Control

The Project Control is the **single Human-facing entry window**. It is not a
Maker, not a Checker, and not a replacement for Human judgment. Project Control:

- Receives Human intent and verifies repository facts
- Classifies tasks by type and risk
- Routes tasks to appropriate Task Holders
- Orchestrates multiple concurrent Task Holders when needed
- Validates receipts from Task Holders
- Presents executable Human actions (Ready, Merge, etc.)
- Registers state transitions

**Default: no repository write access.** Project Control only writes when
explicitly authorized for a specific task with exact scope. This separation
prevents the entry window from silently becoming an implementation agent.

### Task Holder

A Task Holder is a **bounded sub-window** spawned by Project Control for a
single task. A Task Holder:

- Receives an exact task packet from Project Control
- Freezes the Checker Target Packet before Maker execution begins
- Creates Maker and Independent Checker sub-agents with independent contexts
- Validates Maker and Checker receipts
- Returns only conclusions and exact facts to Project Control

A Task Holder **does not directly implement candidates**. It coordinates; it
does not produce. One Task Holder handles exactly one task. Multiple Task
Holders may run concurrently under one Project Control.

### Maker

A Maker implements exactly the authorized task on the authorized branch, within
the authorized file scope. A Maker:

- Writes within the exact authorized scope only
- Pushes to the candidate branch
- Creates a Draft PR
- Does not self-audit
- Does not Ready, Merge, or accept
- Fixes pre-audit defects on the same candidate branch

A Maker is temporary and task-scoped. Its authority ends when it pushes.

### Independent Checker

An Independent Checker performs **read-only independent audit**. A Checker:

- Did not design or implement the candidate
- Did not produce the candidate's evidence
- Operates from an independent context and evidence path
- Can veto (reject) any candidate
- Can recommend Ready

A Checker **cannot modify the candidate**, cannot Ready, cannot Merge, and
cannot provide final acceptance. Veto power is a safety gate, not governance
authority. Any independence ambiguity fails closed.

## Separation rules

1. **Project Control ≠ Task Holder.** The entry window and the task coordinator
   are distinct roles. Project Control routes; Task Holder executes
   coordination.
2. **Task Holder ≠ Maker.** The coordinator does not implement. This prevents
   the dispatcher from also being the producer.
3. **Maker ≠ Checker.** No role audits its own work. Maker and Checker use
   independent contexts and evidence paths.
4. **Checker ≠ Human Holder.** The Checker can veto but cannot accept. Final
   authority stays with the Human.
5. **Project Control defaults to no write.** Writing is a separately authorized
   capability, not a property of the role.
