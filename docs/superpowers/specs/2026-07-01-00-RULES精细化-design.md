# 00-RULES 精细化 · always-on 瘦身 + 规则 index 按需叠加（spec）

| 项 | 值 |
|----|----|
| 状态 | approved（设计已确认，待实施） |
| 创建 | 2026-07-01 |
| 作者 | dalwin + Claude |
| 性质 | 精细化 ADR-0013 建立的 00-RULES 层：把 always-on 从"读全层"瘦身为"只读身份卡"，操作规则改 index 按需拉、可叠加 |
| 受统领 | `PHILOSOPHY.md` P1–P9 |

## 1 · 背景与问题

ADR-0013 落地的 00-RULES 现有 3 文件（identity 47 行 / tech-stack 24 行 / workflow-style **135 行**），INDEX 指示"常驻：进会话先读 00-RULES" ≈ **206 行/每会话** always-on。审查发现三类问题：
- **always-on 过多**：`workflow-style.md` 一个文件混装 6 类内容（skill 列表 + 决策点 + 术语表 + f1–f9 工作偏好 + 沉淀新规 + docs-readme）。
- **陈旧**：`workflow-style.md:24`「Skills 实体在 `~/Documents/AI/dalwin-workflow/skills/`」等旧路径（SOT 已迁 AiPalace）。
- **重复破单一源**：workflow-style 的「常用术语表」与 `01-PROJECTS/reference/glossary.md` 重复。

## 2 · 目标

- G1：always-on 从 ~206 行降为**一张 ≤25 行精简身份卡**（`identity.md`）。
- G2：操作规则（f1–f9 + 沉淀 + docs）改为 **RULES index 按需拉、且可叠加**（并集加载，交叉生效）。
- G3：术语表**单一源**（只留 `01-PROJECTS/reference/glossary.md`）；清除陈旧路径。
- G4：机制沿用现有 INDEX 决策树（三门并集），不引入新注入机制。

## 3 · 非目标
- N1：不动 tech-stack 的内容实质（仅确认为按需）。
- N2：不做 M4 全局指令整合（仍延后）。
- N3：不改注入器代码（`inject_index` 已注入整份 `INDEX.md`；本次只改 INDEX 内容与 00-RULES 文件）。

## 4 · 目标结构

```
vault/memory/00-RULES/
├── identity.md    ← 唯一常驻 · 精简身份卡（≤25 行）
├── tech-stack.md  ← 按需（技术选型/框架对比）
├── dev.md         ← 按需（Java 修复/改码/commit）
├── flow.md        ← 按需（多步任务/review/执行 plan·spec）
└── ops.md         ← 按需（worktree·git/沉淀 wrap/访问 ~/Documents/AI/docs）
```
`workflow-style.md` **退役删除**（内容按下表重分配）。

## 5 · f1–f9 及其余内容 → 落点映射

| 现有内容（workflow-style.md） | 落点 |
|---|---|
| f3 代码修复手势 / f4 最小改动 / f5 全链路复扫 / f6 test·src 拆 2 commit | `dev.md` |
| f1 主任务链路 / f2 spec 执行边界 / f7 review 口径 / f9 plan 前事实核对 | `flow.md` |
| f8 worktree 语义 / 沉淀新规（vault 路由）/ AI docs 访问前读 README | `ops.md` |
| 决策点①②（方案定调后停 / 提交前停）| 一句话钩子进 `identity.md`；完整版随 biz-workflow 语境进 `flow.md` |
| 最小改动（f4 的原则版）| 一句话钩子进 `identity.md`；完整版在 `dev.md` |
| 常用术语表 | **删除**（唯一源 = `01-PROJECTS/reference/glossary.md`）|
| 采纳 Skill 列表 + "dalwin-workflow/skills" 旧路径 | **删除**（registry 是 SOT；SessionStart pack 已按域推荐）|

> 卡内一句话钩子 + 详情文件 = 薄指针模式，非内容重复（钩子只有名+一句，Why/How 只在详情文件一处）。

## 6 · identity.md 精简后（常驻卡 ≤25 行）
- **Me**：dalwinzzz（jpdalwin@gmail.com），Java 后端，2 个月冲刺转 Go 高级后端/架构；主力 Claude Code + Codex（+ Cowork）。
- **项目代号表**：syzh（智慧托育，主力）/ skc（SunkidCloud 平台）/ Go 转型（Java→Go 8 周）。
- **最高频准则（一句话钩子）**：① 决策点——方案/根因定调后停、落库/提交前停，等拍板（详见 [[flow]]）；② 最小改动——局部兼容修复在现有入口最小改动、不主动抽象（详见 [[dev]]）。
- **指针**：Java 工程配置 → `context/rules/java-spring.md`（path-scoped）。
- 移除：工作分布 table、工具协作段（降为可选/指针 [[skills-root]] [[cross-tool-memory]]）。

## 7 · INDEX 改动

1. 顶部常驻语从「进会话先把 `00-RULES/` 当背景」→ **「进会话只读 `00-RULES/identity.md`（精简卡）；其余按下方决策树命中再拉」**。
2. `[自我画像 · 00-RULES]` 段：`identity.md`（常驻）/ `tech-stack.md`（技术选型时）。移除 `workflow-style.md` 行。
3. 新增 **`[操作规则 · 按需 · 可叠加]`** 段（正交触发域，多组可同时命中、并集加载）：

   | 触发 | 加载 |
   |------|------|
   | Java 修复 / 改代码 / commit | `00-RULES/dev.md` |
   | 多步任务 / review / 执行 plan·spec | `00-RULES/flow.md` |
   | worktree·git 操作 / 沉淀 wrap / 访问 `~/Documents/AI/docs` | `00-RULES/ops.md` |

   > 显式标注：以上可同时命中多组（如"多步 Java 修复"→ dev + flow 都加载）。
4. 更新「当前整树文件索引」块反映新 00-RULES 布局。

## 8 · 治理

改的是 ADR-0013 刚建立的 always-on 模型（结构+行为变更），写一条轻量 **ADR-0014**（精细化 00-RULES：always-on 瘦身 + 规则 index 按需叠加；承继 0013，非推翻）。

## 9 · 验收

- `identity.md` ≤ 25 行；`workflow-style.md` 已删；`dev/flow/ops.md` 各含对应 f 规则、带 frontmatter。
- INDEX 顶部常驻语只提 `identity.md`；含 `[操作规则·按需·可叠加]` 段 + 叠加说明。
- glossary 仅存 `01-PROJECTS/reference/glossary.md`（`grep -rl "常用术语表\|八股" 00-RULES/` 为空）。
- 无 `dalwin-workflow/skills` 等陈旧路径残留于 00-RULES。
- 注入端到端实测：常驻输出含 identity 卡、不含全量 workflow 细则；模拟"Java 修复"任务描述时 INDEX 能路由到 dev（+ 多步则 flow）。
- `doctor` 无新增漂移。
