# AI Docs — 文档管理规范

> 本文件是 `docs/` 目录的唯一管理规范，AI 工具执行整理任务时以此为准，查阅任何子目录文档前也应先读本文件。

---

## 目录结构总览

```
docs/
├── README.md               ← 本文件（管理规范）
├── archive/                ← 历史归档区
├── knowledge/              ← 知识性文档区
└── <skill-folder>/         ← 各 skill 活跃工作区（如 superpowers/, problem/）
    ├── specs/
    ├── plans/
    ├── reviews/
    └── verification/
```

---

## 各区职责

### `archive/` — 历史归档区

- **含义**：已完成任务的所有相关文档。
- **归档对象**：除每个 skill 文件夹下**最近一次任务**之外，所有旧版本的 spec / plan / review / log 均应移入此处。
- **目录结构**：按来源路径平铺保留，即 `archive/superpowers/specs/xxx.md`、`archive/spec-best-practices/xxx.md`，不做二次折叠。
- **只读原则**：归档后的文档仅供历史迭代演进参考，**新任务迭代中不需要、也不应该同步更新**归档文档中的内容。
- **AI 行为**：执行新任务时无需读取 archive 下的文档，除非用户明确要求追溯历史版本。

---

### `knowledge/` — 知识性文档区

- **含义**：无时效性的纯知识点文档，不绑定任何具体任务。
- **典型内容**：原理解析、harness 学习笔记、架构对比、最佳实践摘要。
- **不应放入**：任何带日期、带版本号、与某次具体任务挂钩的 spec / plan / log。
- **AI 行为**：需要背景知识时可直接读取；内容不会因任务推进而过期，无需定期归档。

---

### `<skill-folder>/` — 各 skill 活跃工作区

- **含义**：每个 skill（如 `superpowers/`、`problem/`、`spec-best-practices/`）各自维护的工作文档区。
- **子目录约定**（各 skill 按自身规范生成，常见子目录如下）：

  | 子目录 | 内容 |
  |--------|------|
  | `specs/` | 设计稿 / 需求规格 |
  | `plans/` | 实施计划 |
  | `reviews/` | 代码 / 方案评审结果 |
  | `verification/` | 验证脚本与场景 |
  | `logs/` | 执行过程记录（如排查日志） |

- **"最近一次任务"留存原则**：每个子目录下**只保留最新一次任务**对应的文档；其余旧版本一律移入 `archive/`。如何判定"最近一次任务"：以文件名日期最大值为准，同一 feature 系列（如 `git-merge-conductor-v1` 与 `v2`）视为同一任务的迭代，仅留最新迭代。
- **verification/ 例外**：`verification/<feature>/` 目录（测试夹具、场景脚本等）整体作为一个单元看待，不按文件粒度拆分归档，随最新版 plan/spec 一并保留或整体归档。

---

## 整理操作规范（AI 执行指引）

执行"整理 docs 目录"类任务时，按以下步骤进行：

1. **识别 knowledge 候选**：无日期、无版本号、内容为纯知识点的文档 → 移入 `knowledge/`（保留来源子路径，如原在 `harness-learning/` 则移至 `knowledge/harness-learning/`）。
2. **识别最新任务文档**：对每个 skill 文件夹下的每个子目录，找出日期最新的文档（同一 feature 系列取最新迭代），标记为"保留"。
3. **归档旧版本**：非最新的文档移入 `archive/`，保留完整相对路径（如 `archive/superpowers/specs/2026-04-09-xxx.md`）。
4. **不修改内容**：整理只做移动操作，不修改任何文档的内容。
5. **不删除文档**：任何文档只移动到 `archive/` 或 `knowledge/`，不做删除。
6. **更新本 README**：如有新增 skill 文件夹，在"目录结构总览"和"各 skill 活跃工作区"的表格中补充说明。

---

## 新文档命名约定

| 类型 | 命名格式 |
|------|----------|
| spec / plan / review | `YYYY-MM-DD-<feature-slug>[-v<N>][-design\|-plan\|-review].md` |
| log / 排查记录 | `YYYY-MM-DD-<topic>-排查.md` 或 `YYYY-MM-DD-<topic>-log.md` |
| knowledge 文档 | 无日期，语义化文件名，如 `00-what-is-a-harness.md` |

---

## 适用范围

本规范适用于 AiPalace 内所有 `docs/` 层级，约束完全一致：

- `~/Library/CodeRepo/AI/AiPalace/docs/`（顶层，本文件所在 · 新 SOT）
- `~/Library/CodeRepo/AI/AiPalace/docs/dalwin-workflow/`（dalwin-workflow 活跃区子来源）

各子层级的 `docs/` 无需维护各自的 README，统一以本文件为准。归档文档统一移入**顶层** `docs/archive/`，来源路径作为子目录区分（如 `archive/dalwin-workflow/superpowers/specs/`）。

> **迁移说明（2026-06-16）**：本 docs 已从 `~/Documents/AI/docs/` 迁入 AiPalace 作为新 SOT（复制快照，源仍保留）。
> 原 `~/Documents/AI/dalwin-workflow/docs/` 的活跃区内容现位于本仓 `docs/dalwin-workflow/`。

---

## 当前目录对照（截至 2026-06-05）

### 顶层 `docs/`

| 路径 | 区域 | 说明 |
|------|------|------|
| `knowledge/harness-learning/` | knowledge | harness 原理学习笔记 |
| `superpowers/` | skill 活跃区 | superpowers skill 开发文档（当前活跃：git-merge-conductor-v2、sql-expert-dba 能力对比） |
| `problem/` | skill 活跃区 | 排查记录与问题复盘 |
| `archive/` | 归档区 | 所有已完成任务的历史文档 |
| `archive/dalwin-workflow/` | 归档区 | dalwin-workflow/docs 中归档的历史文档 |

### `dalwin-workflow/docs/`

| 路径 | 区域 | 说明 |
|------|------|------|
| `superpowers/specs/` | skill 活跃区 | 当前保留：codex-personal-workflow-design、personal-context-layer-design、sql-expert-dba v2 相关 |
| `superpowers/plans/` | skill 活跃区 | 当前保留：codex-personal-workflow、sql-expert-dba-claude-plugin-v2 及对应 logs |
| `problem/` | skill 活跃区 | memory 问题排查截图与 README |
