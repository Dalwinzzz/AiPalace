---
name: spec-architect
description: >
  Generates executable specs for AI coding tools (Codex / Claude Code). Use when
  planning new features, complex bug fixes, refactoring, migration, or cross-module
  coordination. Triggers on: "write spec", "plan task", "task breakdown",
  "technical design", "development plan", "PRD", "specification", "plan",
  or when the user wants to plan before coding. Also use when the user describes
  a non-trivial change involving multiple files, tables, or call chains — even if
  they don't explicitly say "spec". Do not use for trivial one-step operations
  or pure code implementation requests.
---

# Spec Architect

先把"地图"画清楚再写代码：**勘察真实代码**，产出能直接驱动编码的 spec。
不是写 PRD，是写执行计划。

## 流程

| Step | 动作 |
|------|------|
| 1. 判复杂度 | small / medium / complex（见下表），并宣告一句 |
| 2. 定目标工具 | Codex 还是 Claude Code（见「目标工具」） |
| 3. 勘察 | 扫真实代码、入口、链路——**遇歧义当场问，不要写成 `[待确认]` 交付** |
| 4. Confirm | small 一次；medium 两次（勘察前业务确认 + 勘察后实施确认）；complex 首次确认须含 2-3 个候选方案对比 + 推荐结论 |
| 5. 生成 | 按 [templates/spec.md](templates/spec.md) 的"部分清单"裁剪成稿 |
| 6. 落盘 + commit | `{work-dir}/docs/spec-architect/{yyyy-mm}/{dd}/`，单次原子 commit |
| 7. 衔接编码 | 见「衔接编码」，**不停在 commit 后等指令** |

### 复杂度

| 级别 | 信号 | 产物 |
|------|------|------|
| Small | 1-3 任务、单模块、边界清晰（加字段、修校验、调查询条件） | 单文件 spec |
| Medium | 3-8 任务、跨模块、共享表/接口（CRUD + 详情 + 统计 + 导出） | 单文件 spec |
| Complex | 8+ 任务、多阶段、跨域（架构重构、多模块迁移） | 目录：README + overview + 逐阶段 spec |

勘察后若复杂度变了，**显式宣告升降级**，不静默切换。

### 目标工具

优先级：用户本轮明说 > 运行时自身识别 > 用户记忆里的偏好 > 仓库文件信号。

**`AGENTS.md` / `CLAUDE.md` 不能单独作为判定证据**——很多团队两个工具都支持、两个文件并存。只有这个弱信号时，按当前运行时走并顺带告知用户，别静默切到另一套。

两工具的 spec 侧重差异见 [templates/spec.md](templates/spec.md#目标工具差异)。

## 提问规则

犀利但精简，不跑固定问卷：**一次一问**、每问附推荐答案或候选让用户点选、只问阻塞当前阶段的、**能查代码就先查**（代码库里查得到的不问）。用户已给够信息就总结推进。

用户答完立即写进 spec 的"已锁定决策"；只有用户说"你看着办 / 推迟"才进"待确认项"。

## 衔接编码

commit spec 后必须走到三个终点之一，**不允许停下来等用户说"继续"**：

- **A · 直接编码**（默认）：small，或 medium 且用户未拒绝。宣告一句"spec 已落档并提交，直接开始 Step 1"，然后真的动手改代码。编码中发现与 spec 冲突 → 先更新 spec 并 commit，再继续。
- **B · 显式停止**：用户在 Confirm 时说过"只要 spec / 我自己来"。回一句"本次只交付 spec，需要继续编码时再唤醒我"。
- **C · 先出计划**：complex 任务。建议先用 `writing-plans` 拆成可执行任务清单，或由用户按阶段手工分配，再进编码。

## 硬约束

1. **勘察实证**：spec 里的路径、表名、入口名必须是扫过的；未验证的标 `[推断]`，不写 `已确认`。
2. **歧义当场问**：业务语义、范围归属、决策依赖、兼容策略（保留/灰度/下线）四类歧义必须当场问清，不得留成 `[待确认]` 把成本转给用户。
3. **工具判定**：不得仅凭 `AGENTS.md` / `CLAUDE.md` 判定工具。
4. **复杂度切换显式宣告**。
5. **complex 不单文件交付**：必须 README + 阶段拆分。
6. **auto-commit 规矩**：spec 落盘后单次原子 commit（`docs(spec): {主题}`）；禁止 `--no-verify`，禁止 amend；pre-commit 报错就停下报给用户。不在 git 仓 / 文件全被 ignore / 仓库处于 rebase-merge 中间态 → 打印一行说明后跳过。
7. **架构级任务**：含 Mermaid 目标架构图 + 覆盖矩阵，图遵守 [references/mermaid-style-guide.md](references/mermaid-style-guide.md)。

## 反模式

- ❌ 为只改一行的修改生成 spec —— 直接动手
- ❌ 跳过勘察、只凭口述生成 spec —— 代码库才是真相
- ❌ 让用户确认代码库里查得到的事
- ❌ 把能当场问的歧义写成 `[待确认]` 交付
- ❌ commit spec 后停在原地等"继续"
- ❌ 强行把所有章节塞进每个 spec —— 按实际形态裁剪
- ❌ 在 spec 里写实现代码 —— 只写接口/结构示例
