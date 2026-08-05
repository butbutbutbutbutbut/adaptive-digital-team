# Worktree 使用说明（快速上手）

> 规范定义见 `protocols/WORKSPACE_ISOLATION.md`。本文档只讲怎么操作。
> 适用环境：Windows 10 + git-bash（本仓库的标准 shell）。

## 1. 一句话总结

**每个 agent 一个独立工作目录（worktree），一个 worktree 只对应一个分支。
主工作区永远停在 main。** Git 本身禁止两个 worktree 检出同一个分支，
所以并行 agent 不可能互相覆盖。

## 2. 目录约定

```text
<repo-parent>\.adt-worktrees\<repository-name>\<agent-name>\
```

本仓库实际路径：

```text
C:\Users\x2270\.adt-worktrees\adaptive-digital-team\maker-adt-2026-08-06-001\
```

agent 名 = `<role>-<task-id>`，小写，字符集 `[a-z0-9-]`。

## 3. 创建（Maker：从 Base 拉新分支）

在主工作区执行：

```bash
cd /c/Users/x2270/adaptive-digital-team
git worktree add -b hermes/adt-workspace-isolation-r1 \
  "C:/Users/x2270/.adt-worktrees/adaptive-digital-team/maker-adt-2026-08-06-001" \
  0b6b1a4
```

- `-b <branch>`：新建并检出该分支；
- 最后一个参数是 `base_sha`（Dispatch Card 的 BASE_SHA）；
- 路径用引号包裹，斜杠用正斜杠（git-bash 兼容）。

## 4. 创建（Checker：只读检出候选分支）

```bash
git worktree add --detach \
  "C:/Users/x2270/.adt-worktrees/adaptive-digital-team/checker-adt-2026-08-06-001" \
  <candidate_head_sha>
```

- `--detach`：不切换分支，只读审查；
- 候选 SHA 以 Candidate Lifecycle 的 live facts 为准。

## 5. 进入 worktree 工作

```bash
cd "C:/Users/x2270/.adt-worktrees/adaptive-digital-team/maker-adt-2026-08-06-001"
```

进去之后就是普通 git 仓库操作（edit / add / commit / push），
**只是不要执行 `git checkout` 切分支**。

## 6. 开工前验证（必做）

```bash
git rev-parse HEAD            # 必须 == Dispatch Card BASE_SHA
git branch --show-current     # 必须 == Dispatch Card BRANCH
git status                    # 必须干净
git worktree list             # 确认绑定：本路径 -> 本分支
cat .hermes/CANDIDATE_BINDING.json   # 必须与 Dispatch Card 一致
```

任何一项不符：**停止**，不要开工，回 Holder 重新绑定。

## 7. 查看当前所有 worktree

```bash
git worktree list
```

输出示例：

```text
C:/Users/x2270/adaptive-digital-team                0b6b1a4 [main]
C:/Users/x2270/.adt-worktrees/adaptive-digital-team/maker-adt-2026-08-06-001  0b6b1a4 [hermes/adt-workspace-isolation-r1]
```

## 8. 关闭与清理

候选合并完成后（或任务取消并获授权后）：

```bash
git worktree remove "C:/Users/x2270/.adt-worktrees/adaptive-digital-team/maker-adt-2026-08-06-001"
git worktree prune
```

- 工作区不干净时 `remove` 会失败：先把变更 commit 到绑定分支；
- 分支删除仍需 Publish Lease，与既有规则一致；
- 清理后 `git worktree list` 应只剩主工作区。

## 9. 常见问题（FAQ）

### 9.1 报错 `fatal: '<branch>' is already checked out at '<path>'`

说明该分支已被另一个 worktree 占用 —— 这是**正常的隔离保护**。
不要加 `--force`。执行 `git worktree list` 找到占用者，确认后回 Holder。

### 9.2 worktree 里改了文件，但主工作区看不到？

正常。worktree 是独立目录，文件各自落盘；只有 commit 之后
变更才通过 git 对象库共享。

### 9.3 worktree 的 `.hermes/CANDIDATE_BINDING.json` 和主工作区不一样？

正常。它是跟踪文件，每个分支（每个 worktree）有自己的版本。
校验时以**本 worktree 内**的文件为准（`scripts/validate_binding.py` 读取语义不变）。

### 9.4 崩溃后遗留的 worktree 怎么清理？

```bash
git worktree list          # 找到遗留路径
git worktree remove "<path>"   # 确认无活动任务后
git worktree prune
```

### 9.5 Windows 路径报错？

- 路径含空格时用引号包裹；
- 统一用正斜杠 `/`；
- agent 名只含 `[a-z0-9-]`，不要用中文或空格；
- 超长路径报错时，缩短 agent 名或启用 Windows 长路径支持。

### 9.6 单人单任务也要用 worktree 吗？

写任务一律建议用 worktree（成本一次命令，收益是习惯一致）；
主工作区只保留 main 与治理读操作。
