# Beginner Bootstrap Router

Status: `FROZEN_DESIGN` / `WAITING_IMPLEMENTATION_AUDIT`

The Beginner Bootstrap Router is the first-contact interaction protocol for
the ADT repository. When a user shares only the ADT repository link without a
clear task, the AI presents exactly three options (A/B/C). When the user's
first message already carries a task, files, a repository, or a control packet,
the menu is skipped and the AI routes directly.

---

## 1. Frozen Menu

### Default Menu (intent unclear, link-only first message)

The AI **must only reply**:

```text
A｜直接开始
B｜我会上传文件
C｜连接我自己拥有或管理的项目仓库
```

No welcome message, project introduction, terminology explanation, or GitHub
tutorial is permitted.

### Option A — Direct Start

```text
你可以直接告诉我想完成什么。

建议包含：
1. 想得到什么结果
2. 已经有哪些信息
3. 希望以什么形式交付

例如：
"帮我整理一份活动方案，最后输出成可复制的正文。"
```

Enters:

```text
MODE: PROMPT_LOCAL
REPOSITORY_ACTION: PROHIBITED
DELIVERY: CHAT_OR_DOWNLOAD
```

### Option B — File Upload

```text
请把文件上传到当前对话，然后告诉我：

1. 需要修改、分析还是整理
2. 最终需要什么格式

可以一次上传多个文件，不需要上传到 GitHub。
```

Enters:

```text
MODE: PROMPT_LOCAL_WITH_FILES
UPLOAD_TARGET: CURRENT_CHAT
REPOSITORY_ACTION: PROHIBITED
```

### Option C — Repository Connection

```text
请提供你自己拥有或管理的项目仓库链接。

然后选择：

1｜只读分析，不修改仓库
2｜允许创建候选变更，但最终提交和合并仍由你确认
```

Enters:

```text
MODE: REPOSITORY_REQUESTED
WRITE_AUTHORITY: NOT_GRANTED
```

After C, the AI must still verify the repository, connection capability,
permission scope, and write authorization before entering `REPOSITORY_ACTIVE`.

If the AI cannot connect to the repository or lacks the necessary tools, it
must offer a fallback to A or B mode rather than pushing complex Git
operations onto the user.

---

## 2. Menu Skip Mechanism

When receiving the first message, the AI must fully parse the message and
attachments before deciding whether to show the menu.

```text
完整治理控制包 (full control packet)
→ CONTROL_PACKET, skip menu

用户自己的仓库 + 明确仓库任务 (user's own repo + clear repo task)
→ REPOSITORY_REQUESTED, skip menu

附件或文件 + 明确处理任务 (attachments/files + clear processing task)
→ PROMPT_LOCAL_WITH_FILES, skip menu

明确的普通任务 (clear plain task)
→ PROMPT_LOCAL, skip menu

只有 ADT 链接或意图不明确 (link-only or unclear intent)
→ Show A / B / C
```

### Explicit Skip Command

```text
跳过引导，直接执行以下任务：
……
```

The skip mechanism only skips the usage guide. It does NOT skip:

- Write authorization
- SHA and target fact verification
- Audit
- Ready
- Merge
- HARD_STOP

A user claiming to be the "owner" does not automatically grant write permission.

---

## 3. Mode Locking

```text
A/B modes:
  Must not auto-upgrade to repository mode.

C mode:
  Must not auto-upgrade to repository write mode.

Mode switching:
  Must be explicitly requested by the user.
```

### Return-to-Menu Command

```text
返回模式选择
```

On receipt, re-display A/B/C.

When an A-mode user later uploads files, the AI may auto-transition to B
without requiring a mode re-selection.

---

## 4. Full State Machine

```
                        FIRST MESSAGE
                             │
              ┌──────────────┼──────────────┐
              │              │              │
         Link-only     Has task/files/repo/ctrl
              │              │
         Show A/B/C    Classify → skip menu
              │              │
    ┌────┬────┴────┬────┐    │
    │    │         │    │    │
    A    B         C  invalid  │
    │    │         │    │    │
    v    v         v    v    v
PROMPT  PROMPT   REPO  re-show  PROMPT_LOCAL
_LOCAL  _LOCAL   _RE-  menu    /PROMPT_LOCAL_WITH_FILES
        _WITH    QUEST-         /REPOSITORY_REQUESTED
        _FILES   ED             /CONTROL_PACKET
```

### Mode Transition Rules

| From | Event | To | Allowed |
|------|-------|----|---------|
| PROMPT_LOCAL | User uploads files | PROMPT_LOCAL_WITH_FILES | YES (auto) |
| PROMPT_LOCAL | User asks for repo | — | BLOCKED |
| PROMPT_LOCAL_WITH_FILES | User asks for repo | — | BLOCKED |
| REPOSITORY_REQUESTED | Write task, no auth | — | BLOCKED |
| Any | "返回模式选择" | Show A/B/C | YES |

---

## 5. Repository Change Scope

When in repository mode, the AI's allowed change scope is determined by the
mode and authorization, not by the user's identity claim.

### Write Authorization Gate

Before any write action in repository mode:

1. Verify the repository is accessible
2. Verify the user has ownership or collaborator access
3. Confirm the write scope (read-only vs. candidate changes)
4. Create branch per `ONE_TASK = ONE_BRANCH = ONE_PR = BASE_MAIN`
5. Never push, Ready, or Merge without explicit per-action authorization

---

## 6. Invalid Input Handling

| Input | Response |
|-------|----------|
| Invalid option (not A/B/C) | Repeat A/B/C only |
| Empty message after link | Show A/B/C |
| "owner" claim without verification | May skip menu; does NOT grant write |
| Write request in A/B mode | Explain mode lock; suggest "返回模式选择" |

---

## 7. Design Freeze

This protocol is `READY_FOR_FREEZE` / `FROZEN_DESIGN`. The menu text, option
labels, mode names, transition rules, and skip conditions in this document
are the authoritative reference. Implementation changes require a new
Dispatch Card with explicit scope.

### Frozen Elements

- A/B/C menu text (exact)
- A guide text (exact)
- B guide text (exact)
- C guide text (exact)
- Mode lock rules
- Skip conditions
- "返回模式选择" command
- "跳过引导" command semantics
- Write authorization gate semantics

---

## 8. Compliance: Existing Governance

This protocol is additive. It does not modify:

- Ruleset
- History immutability
- Permission model
- Audit protocol core semantics
- P1–P5 roadmap
- Product repositories

Existing governance (AGENTS.md, Candidate Lifecycle R1, scope enforcement,
fingerprint binding, audit receipt validation) remains normative and takes
precedence in any conflict.
