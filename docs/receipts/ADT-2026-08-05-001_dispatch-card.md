# Dispatch Card

```
TASK_ID:       ADT-2026-08-05-001
TASK_TYPE:     CODE_CHANGE
REPOSITORY:    butbutbutbutbutbut/adaptive-digital-team
BASE_SHA:      0b6b1a4
AUTHORIZATION_ID: AUTH-2026-08-05-001
EXECUTOR:      MAKER (小禾)
CHECKER:       CHECKER (小禾，独立审计)
FILES_IN_SCOPE:
  - GitHub PR state (via `gh pr close`)
  - Local git branches (via `git branch -D`)
ACTIONS_IN_SCOPE:
  - Close identified low-quality OPEN PRs
  - Delete corresponding local branches
  - Delete local branches for already-CLOSED PRs
PURPOSE:       Clean up low-quality/duplicate PRs and stale branches from S2 sprint
HUMAN_AUTH:    之 directed cleanup of "刚才提交的那些" (extended to "已closed的也干掉")
```

## Target PRs

| PR | State Before | Reason |
|----|-------------|--------|
| #75 | OPEN | Duplicate of #76 |
| #70 | OPEN | Duplicate of #71 |
| #68 | OPEN | Duplicate of #71 |
| #64 | OPEN | Duplicate of #69 |
| #62 | OPEN | Auto-generated patch PR |
| #56 | OPEN | Chain integrity test PR |
| #66 | CLOSED | Duplicate of #67 |
| #39 | CLOSED | Stale, superseded by #44 |
| #36 | CLOSED | Stale, superseded by #37 |
| #32/#31 | CLOSED | Stale, superseded by #33 |
| #29/#27 | CLOSED | Stale, superseded by #58 |
| #35/#34 | CLOSED | Stale patch PRs (branch already gone) |

## Governance Note

此 Dispatch Card 为**事后补发**。Controller（小禾）在执行时未先经 Holder（安鼎）分类派发，违反了 ADT 治理链的 Holder→Maker→Checker 分离原则。缺陷已记录在 Progress Receipt 的 KNOWN_LIMITS 中。
