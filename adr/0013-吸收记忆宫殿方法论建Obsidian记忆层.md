# ADR-0013：吸收「记忆宫殿」方法论，在 AiPalace 内建 Obsidian 记忆层

- 状态：已接受
- 日期：2026-06-30
- 决策人：dalwin
- 关联：承继 [ADR-0007](0007-SessionStart-hook以AiPalace-INDEX注入取代domain-context.md)（SessionStart 注入机制，路径迁移至 `vault/memory/`）；延续 [ADR-0009](0009-指令文件渐进披露与howto子文档.md)（渐进披露原则）；遵循 [PHILOSOPHY.md](../PHILOSOPHY.md) P1–P9
- 参照 spec：[`docs/superpowers/specs/2026-06-27-aipalace-obsidian记忆层-design.md`](../docs/superpowers/specs/2026-06-27-aipalace-obsidian记忆层-design.md)

---

## 背景

同事以「记忆宫殿」方案展示了 Obsidian 外置管理个人 AI-Agent memory 的方法论：五层生命周期分区（RULES / PROJECTS / SOURCES / MAPS / FEEDBACK）、PROTOCOL 跨工具读写契约、统一 frontmatter、捕获→蒸馏→审批→注入飞轮、内核不调 LLM 的确定性晋升。

经分析，**同事方案≈ AiPalace 的 `context/` + `memory/` 这一层**（个人记忆），并非整个 AiPalace。AiPalace 在 skill 管理轴上（registry + skillctl 派生）反而被同事致敬借用。故本次为**方法论吸收**，非整仓搬迁，非替代。

现状痛点：
- 个人画像（`context/self/`）与知识库（`context/memory/`）分散两处，注入路径分别由 `context/INDEX.md` + `context/memory/INDEX.md` 驱动，双源维护。
- 原生 `~/.claude/…/memory/` 的实质记忆事实与仓库 memory 形成双存，无单一 SOT。
- 全局指令文件（`~/.claude/CLAUDE.md`、`~/.codex/AGENTS.md`）存在工具无关的共享规则，但分头平行维护，改一处忘另一处。

---

## 决策（已完成部分）

### M1 · vault 结构（已完成）

在 `AiPalace/vault/memory/` 建立五层目录骨架：

```
vault/
└── memory/
    ├── PROTOCOL.md        ← 唯一读写契约（受 P1–P9 统领）
    ├── INDEX.md           ← always-on 决策树（SessionStart 注入入口）
    ├── 00-RULES/          ← 身份层 + 全局约定（最高法律，只经审批改）
    ├── 01-PROJECTS/       ← 项目/领域层（projects/enterprise/tech/workflow/reference）
    ├── 02-SOURCES/        ← 外部剪藏资料层
    ├── 03-MAPS/           ← 流程图/架构/决策树索引层
    ├── 04-FEEDBACK/       ← 飞轮中枢（journal / candidates / DREAMS）
    └── _template/         ← frontmatter 模板
```

层名用数字 `00–04` 自带优先级排序 + 标明方法论血缘（spec D2）。`vault/` 作为 Obsidian 根，后续其它纳管区可挂于此（spec D1）。

### M2 · PROTOCOL 契约（已完成）

`vault/memory/PROTOCOL.md` 作为**唯一读写契约**：三条最高指令（读 first / 写 back / 不越权改 00-RULES）、去哪找什么入口表、frontmatter 约定、敏感红线。任一 agent 仅读 PROTOCOL 即知如何读写 vault。

### M3 · 内容迁移（已完成）

- `context/self/`（身份/技术栈/工作方式画像）→ `vault/memory/00-RULES/`
- `context/memory/**`（五域知识库）→ `vault/memory/01-PROJECTS/`（按域平移，保留 projects/enterprise/tech/workflow/reference 结构）
- 原生 `~/.claude/…/memory/` 实质记忆事实迁入 vault 对应层，带 frontmatter，建 wikilink

迁移后无内容丢失；原 INDEX 决策树语义在 `vault/memory/INDEX.md` 和 PROTOCOL 中等价保留。

### M6 · 注入器改线（已完成，SessionStart 注入路径迁移）

**本次对 ADR-0007 注入机制的承继与路径迁移**：ADR-0007 确立 SessionStart always-on 注入 `context/INDEX.md` + `context/memory/INDEX.md` 两文件。本次将注入路径从两个旧 INDEX 统一迁移至单一 `vault/memory/INDEX.md`（决策树已合并），注入机制本身（`inject_index.py` + `sessionstart.py`）延续 ADR-0007 的双工具同逻辑架构，不重建，仅改参数。

> **不修改 ADR-0007**（append-only）。本 ADR 标注承继关系：继承 ADR-0007 的注入机制，路径由 `context/INDEX.md` + `context/memory/INDEX.md` 迁移至 `vault/memory/INDEX.md`。

注入端到端验证通过：新会话可正确注入 `vault/memory/INDEX.md`，全局约定与决策树完整。

`AiPalace/CLAUDE.md` 同步更新路径引用（self/memory 已迁 vault，详见 vault.md 规范）。

---

## 显式过渡态（未完成部分，P9 诚实标注）

> ⚠️ 以下模块**未在本次计划内完成**，为显式过渡态，列于 `docs/governance/evolution.md` 待决项清单。

### M4 · 全局指令整合（**已推迟，未做**）

**当前状态**：
- `~/.claude/CLAUDE.md` 与 `~/.codex/AGENTS.md` 仍保持现有全量内容，**未执行**"共享规则抽离入 `00-RULES/operating-rules.md` + native 文件瘦身为指针 stub"。
- 原生 memory 事实已迁入 vault，但 native memory 并发机制（`~/.claude/projects/…/memory/`）的实质内容当前在 **native + vault 双存**（显式过渡态，P9）。

**收敛路径**：需先扩 SessionStart hook，令其在注入 `vault/memory/INDEX.md` 之外同时注入 `00-RULES/operating-rules.md`；验证无双注入后，再执行 native 瘦身。此操作风险等级高，排在注入端到端验证之后（已验证）但需单独计划承接。

**当前风险**：全局指令文件仍两处平行维护；改一处规则可能不同步另一处。属 P9 已知不一致，纳管为显式待决项。

### M5 · 飞轮引擎（**独立后续计划，不在本计划**）

`tools/memory/` 确定性打分脚本 + `/ai-palace` 命令为独立后续计划，不在本次 feat 分支内。过渡期 `/wrap` 已重定位指向 vault 路径（未退役）。

---

## 后果

**正面**：
- 个人记忆有单一人类可读 SOT（`vault/memory/`），Obsidian 可直接打开浏览 graph。
- SessionStart 注入路径统一为一个文件（`vault/memory/INDEX.md`），决策树不再分散。
- 五层结构 + PROTOCOL + frontmatter 约定清晰，任何 agent 按契约读写，不猜。
- 内容迁移后，`context/self/` 与 `context/memory/` 旧位置已标注迁移指向，不误导。

**取舍与待观察**：
- always-on 注入 `vault/memory/INDEX.md`（含决策树）每会话 token 成本与原两文件合并注入基本持平；可接受。
- M4 未完成导致 native 与 vault 双存，存在事实漂移风险——由 evolution.md 显式管理，不默默接受。
- M5 飞轮未落地，当前蒸馏依赖 `/wrap`（已重定位），沉淀效率次于飞轮方案，属过渡态。
- `vault/` 目录纳入 AiPalace 仓库，与工程内容同仓——符合 P1（一仓全貌），但 Obsidian 根指向 `vault/` 而非仓库根，保证 graph 干净（spec D1）。

---

## 与既有 ADR 的关系

| ADR | 关系 |
|-----|------|
| ADR-0007 | **承继**：注入机制不变，路径由 `context/INDEX.md` + `context/memory/INDEX.md` 迁移至 `vault/memory/INDEX.md` |
| ADR-0009 | **延续**：渐进披露哲学不变；`context/howto/` 留原处不进 vault，仍由指令文件指针触发 |
| ADR-0012 | **无冲突**：ask-first 软约束与 vault 机制正交，不受本次影响 |
