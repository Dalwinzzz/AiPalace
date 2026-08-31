# ADR-0009：指令文件（CLAUDE.md/AGENTS.md）渐进披露 + `context/howto/` 子文档

- 状态：已接受
- 日期：2026-06-25
- 决策人：dalwin
- 关联：落实用户「固化 CLAUDE.md/AGENTS.md 维护理念」需求；延续 [P4 控预算](../PHILOSOPHY.md#p4--分级控预算tier)、[P7 内容统一源](../PHILOSOPHY.md#p7--内容统一源机制分治)

## 背景

全局 `~/.claude/CLAUDE.md` 的「Documentation Lookups — Use Context7 MCP」段含完整 how-to（`resolve-library-id`→`get-library-docs`→`topic` 流程 + Do-not 清单）。指令文件（CLAUDE.md / AGENTS.md）是 **always-on 注入层**——每会话 / 每路径匹配都进上下文；其中的 how-to 细节实际**只在真要发起 context7 调用时**才需要，却每会话常驻，徒增 token。

用户要求：把 how-to 迁成子 md 按需动态加载、主文件只留索引指针；并把这套理念**固化为通用规则**，适用于日后维护任意位置的 CLAUDE.md / AGENTS.md。

## 决策

1. **确立「指令文件渐进披露」约定**（[`context/howto/instruction-file-maintenance.md`](../context/howto/instruction-file-maintenance.md)）：
   - 主文件**只留**全局规则约束 / when-to-use 触发 / 系统级注入；
   - **how-to 等操作细节移入子文档**，主文件只留一行索引指针，按需 `Read`、不常驻上下文。
2. **子文档落 `AiPalace/context/howto/`**（SOT），与 `self/`（关于我）、`memory/`（关于事）并列，同属 context 层渐进披露内容；**触发入口 = 指令文件中的指针**（区别于 `context/INDEX` 决策树）。
3. **首例**：`~/.claude/CLAUDE.md` 的 context7 段 —— 保留 headline + 「When this applies」+ 指针；how-to / Do-not → [`context/howto/context7-mcp.md`](../context/howto/context7-mcp.md)。约定本身 → `instruction-file-maintenance.md`。
4. **全局 `~/.claude/CLAUDE.md` / `~/.codex/AGENTS.md` 保持 live**（就地瘦身 + 指针），**不**纳入 AiPalace 软链派生（用户选「薄壳 + AiPalace 子文档」方案，与现有 rules/hooks「`~/.claude` 薄壳 + AiPalace 内容」一致，风险低）。

## 后果

**正面**：指令文件瘦身、每会话 token 省；维护约定可复用（任意 CLAUDE.md/AGENTS.md 适用）；how-to 子文档版控于 SOT（AiPalace）；"何时用"常驻、"怎么用"按需，命中渐进披露设计。

**取舍 / 待观察**：
- 主文件指针指向 AiPalace 绝对路径 —— 耦合该路径（机器固定，可接受）；how-to 内容此后在 AiPalace 维护，主文件不再随之改动。
- 同类可瘦身段（如全局 CLAUDE.md「个人配置目录 ConfigFile」细则、`~/.codex/AGENTS.md` 各段）**本轮（写本 ADR 时）未动**，可后续按本约定逐步瘦身。（后于 2026-06-26 完成：ConfigFile / superpowers 段已按本约定就地精简，索引指针只留纯指向 + 加载时机。）
- 全局指令文件仍为 live（非 SOT 软链）—— "全局 CLAUDE.md/AGENTS.md 纳入 AiPalace 受管" 作为可选演进留待后议。
