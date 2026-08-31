# ADR-0012：superpowers ask-first 兜底软约束 + 挂入 Codex

- 状态：已接受
- 日期：2026-06-26
- 决策人：dalwin
- 关联：延续 [ADR-0007](0007-SessionStart-hook以AiPalace-INDEX注入取代domain-context.md)（SessionStart 不再强注入 using-superpowers）、[ADR-0009](0009-指令文件渐进披露与howto子文档.md)（全局指令文件为 live、非 SOT 软链）；与 [ADR-0011](0011-SessionStart-pack推荐改registry驱动.md) 的 pack 推荐协同

## 背景

superpowers 是好用的方法论插件。此前演进中：

- **Claude Code**：`superpowers@claude-plugins-official` 插件仍 enabled，其插件级 SessionStart 钩子（`run-hook.cmd session-start`）**仍自动注入** `using-superpowers`——自动加载未受影响。
- **Codex**：`~/.codex/skills` 无任何 superpowers skill，`~/.codex/hooks.json` 的 SessionStart 只有 AiPalace + codeisland 两钩子、无 superpowers 注入，`config.toml` 亦无相关配置——**Codex 侧既不自动加载，skill 也无法直接 invoke**。
- 两个全局指令文件（`~/.claude/CLAUDE.md`、`~/.codex/AGENTS.md`）此前**无** superpowers 相关约束。

用户担心去掉强注入后 superpowers 触发不稳，希望保留为**跨工具兜底**，但用更轻的 **ask-first 前置**形态（而非原 `using-superpowers` 的"必须无条件 invoke"强制语气）。

## 决策

两手并行（用户拍板）：

1. **ask-first 软约束写入双工具全局指令文件**（`~/.claude/CLAUDE.md` + `~/.codex/AGENTS.md`，二者为 live 文件，符合 ADR-0009）：任务命中 superpowers 场景（新功能→brainstorming、bug→systematic-debugging、实现→TDD、多步→writing/executing-plans、完成前→verification）时，**先说明拟用哪个 skill + 理由、征得同意后再 invoke**，不静默自动调用、也不无视。显式优先级：**用户显式指示 > 本软约束 > 默认行为**；用户说"直接做/别走流程"即跳过。
2. **superpowers 挂入 Codex**：把 superpowers 仓库（`~/Library/CodeRepo/AI/superpowers/skills/`）的 14 个 skill 软链进 Codex 原生发现目录 `~/.codex/skills/`，使 Codex 也能 `/skill` 实际 invoke。
   - 复现命令：`for d in ~/Library/CodeRepo/AI/superpowers/skills/*/; do n=$(basename "$d"); [ -e ~/.codex/skills/$n ] || ln -s "$d" ~/.codex/skills/$n; done`
   - **不接 SessionStart 自动注入钩子**：刻意只挂 skill、不复刻 Claude 的强注入，与"ask-first 而非强制"一致。

## 后果

**正面**：superpowers 在两工具均可用——Claude 经插件、Codex 经 skill 软链；触发由"强制无条件"降为"ask-first 前置"，更克制、尊重用户显式指示；Claude 的插件自动注入保留为主路径，软约束为兜底；不依赖脆弱的强注入。

**取舍 / 待观察**：
- **Codex 的 superpowers skill 软链指向 superpowers 仓库（非 AiPalace），是 skillctl 受管域之外的外部挂载**：`is_managed()` 判否 → `sync`/`doctor` 对其 **protect-skip、不 prune、不报漂移**（已验证 doctor 绿、`sync --dry` prune=0）。即它不归 skillctl 治理，由本 ADR 记录其存在与复现方式（P9 显式过渡态，非默默漂移）。superpowers 仓库迁移/删除会使这些软链悬挂，需重跑上方复现命令。
- **全局指令文件仍为 live**（ADR-0009 既有过渡态）：本次软约束直接就地编辑 `~/.claude/CLAUDE.md`、`~/.codex/AGENTS.md`，未纳入 AiPalace 软链派生；"全局指令文件纳入 AiPalace 受管"仍为待议项。
- **两工具触发力度不对称**：Claude 仍有插件级强注入 + 本软约束，Codex 仅本软约束 + skill 可 invoke。可接受（Claude 插件是既有事实，未动）。
