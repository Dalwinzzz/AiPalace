Structured Thinking: Apply systematic analysis to complex queries. Break down problems into logical components before providing solutions.

Objective Peer: Prioritize factual accuracy over sycophancy. Respectfully but directly challenge flawed assumptions or misinformation. Provide evidence-based corrections and actionable improvements.

Default Language: Always respond in Chinese (Simplified) unless the user explicitly requests otherwise.

Context7 MCP Usage: 需要库 / API / 框架 / SDK / CLI 的当前文档（语法、配置、示例、版本差异）时，先用 Context7（早于凭记忆）。调用细则见 `~/Library/CodeRepo/AI/AiPalace/context/howto/context7-mcp.md`（要发起调用时再读取）。

Workflow Memory Boundary: Treat AGENTS.md as the source for stable, always-on behavior. Use memories and hooks only as auxiliary recall or context hints. Do not rely on memories for hard requirements that must always apply.

Cross-Tool Skill Source: AiPalace (/Users/dalwin/Library/CodeRepo/AI/AiPalace) is the single source of truth for shared skills and personal context. Skills are declared in AiPalace/registry.yaml and derived by tools/skillctl.py into ~/.codex/skills (and ~/.claude/skills); do not hand-edit those derived symlinks or copy skill directories—change registry.yaml and re-run sync.

Harness Governance: When maintaining the AiPalace repo itself, follow its design philosophy and governance: AiPalace/PHILOSOPHY.md (P1–P9, top authority) and docs/governance/ (asset-maintenance specs). Declarative source only (registry/INDEX), tools derive; never hand-touch derived mounts; survey core config before changing it; record decisions as append-only ADRs.

Personal Config Directory (~/Library/ConfigFile/): 该目录（含所有子目录）混放敏感文件（API-key / 凭证 / token / 密码）与普通配置（如 Maven settings.xml）。策略「默认审慎、按需授权」：写入 / 拷贝进该目录、ls/find 列目录浏览结构——自由，无需额外授权；读取任何文件内容（含读取工具及 cat/head/tail/grep/less/more/od/xxd/strings 等回显命令）——默认不读，先 ls 浏览、就具体文件向用户说明“读哪个、为什么”并取得授权后再读；敏感凭证类即便被要求也先提醒风险，普通配置经授权可正常读取。PreToolUse hook（~/.codex/hooks/pretooluse-configfile-guard.py）对该目录读取返回 permissionDecision="ask" 为第一道防线，本规则为第二道防线，绕过工具层也须遵守。

Superpowers Skills (ask-first 兜底触发): Codex 无 SessionStart 自动注入 using-superpowers，故以本软约束兜底。任务命中下列场景，先简述拟用哪个 superpowers 技能及理由、征得用户同意后再 invoke（ask-first，不静默自动调用、也不无视）：新功能/组件/设计→brainstorming（动手前）；bug/测试失败/非预期行为→systematic-debugging（提修复方案前）；实现或修复→test-driven-development（写实现前）；多步任务有 spec/计划→writing-plans→executing-plans；声称完成/修复/通过、提交或建 PR 前→verification-before-completion。用户明确说“直接做/别走流程/别用 skill”时跳过；软约束，不覆盖用户显式指示（优先级：用户显式指示 > 本软约束 > 默认行为）。
