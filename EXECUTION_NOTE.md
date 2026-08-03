# ADT S2-002-A Execution Note

## Executor

Hermes

---

## Objective

将 Artifact Package 落入真实仓库。

---

## Execution Rules

### 1. 不改变 ADT 核心定义

保持：

ADT =
Governance Control Plane
+
Adaptive Team Mechanism

---

### 2. 增量修改

禁止：

- 重构无关目录
- 删除旧文档
- 新增无必要机制

---

### 3. 必须验证 Artifact

完成条件：

```

File Changed
+
Git Diff Exists
+
Commit Exists
+
Location Returned

```

---

### 4. 输出格式

返回：

```

Changed Files:

Commit:

PR:

Checker Result:

Human Review Required:

```

---

## Anti-goal

不要：

- 用文档堆复杂度
- 增加人工审批
- 将 README 写成论文
