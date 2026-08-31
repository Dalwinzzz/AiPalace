# ADR-0014 · 精细化 00-RULES：always-on 瘦身 + 规则 index 按需叠加

- 状态：Accepted
- 日期：2026-07-01
- 承继：ADR-0013（吸收记忆宫殿方法论建 Obsidian 记忆层）——本 ADR 精细化 0013 建立的 00-RULES 层，**非推翻**。
- 关联 spec：`docs/superpowers/specs/2026-07-01-00-RULES精细化-design.md`

## 背景

ADR-0013 落地的 00-RULES 有 3 文件，INDEX 指示"常驻：进会话先读 `00-RULES/`" ≈ **206 行/每会话** always-on。审查发现：

1. **always-on 过多**：`workflow-style.md`（135 行）一个文件混装 skill 列表 + 决策点 + 术语表 + f1–f9 工作偏好 + 沉淀新规 + docs-readme 六类内容，全被当常驻。
2. **陈旧**：`workflow-style.md` 含「Skills 实体在 `~/Documents/AI/dalwin-workflow/skills/`」等旧路径（SOT 已迁 AiPalace）。
3. **重复破单一源（P1）**：workflow-style 的「常用术语表」与 `01-PROJECTS/reference/glossary.md` 重复。

## 决策

1. **always-on 瘦身为一张精简身份卡**：00-RULES 唯一常驻内容 = `identity.md`（Me + 项目代号表 + 2 条最高频准则一句话钩子 + 指针）。INDEX 顶部常驻语改为「进会话只读 `00-RULES/identity.md`」。
2. **操作规则改 index 按需拉、可叠加**：`workflow-style.md` 退役，f1–f9 及沉淀/docs 规则按触发域正交拆为 3 组——`dev.md`（f3/f4/f5/f6 Java 修复·改码·commit）、`flow.md`（f1/f2/f7/f9 多步·review·plan）、`ops.md`（f8 worktree·沉淀·docs）。INDEX 新增「操作规则 · 按需 · 可叠加」段，**多组可同时命中、并集加载**（如"多步 Java 修复"→ dev + flow 都注入）。机制沿用现有 INDEX 决策树三门并集，不引入新注入机制。
3. **术语表单一源**：删 workflow-style 术语表，唯一源 = `01-PROJECTS/reference/glossary.md`（P1）。
4. **清陈旧**：删「采纳 skill 列表」+ `dalwin-workflow/skills` 旧路径（registry 是 skill SOT；SessionStart pack 已按域推荐）。

## 后果

- 每会话 always-on 从 ~206 行降为 INDEX 决策树 + 一张 ~28 行身份卡；tech-stack、操作规则、术语按任务命中才拉。
- 规则可叠加：交叉任务（多步 Java 修复、fix-then-review 等）自动并集加载相关规则组，无需人工取舍。
- 术语单一源、无陈旧路径。
- `dev/flow/ops.md` 各聚焦一触发域，边界清晰、可独立维护。

## 取舍

- **组粒度 vs 精度**：选"按触发域分 3 组"而非"每规则一文件"——牺牲少量组内精度（命中组时可能带入组内非当前所需的 1–2 条规则），换文件数少、INDEX 路由段紧凑、叠加干净。
- **卡内一句话钩子 ≠ 重复**：决策点/最小改动在身份卡留一句话钩子、完整 Why/How 只在 dev/flow 一处——薄指针模式，不破单一源。

## 验证

- always-on 实测：注入输出常驻只读 identity 卡、含「操作规则·可叠加」路由段、dev/flow/ops 可路由、无 workflow-style 残留。
- `grep 00-RULES/` 术语表 = 0、`dalwin-workflow/skills` = 0。
- `doctor` 无新增漂移。
