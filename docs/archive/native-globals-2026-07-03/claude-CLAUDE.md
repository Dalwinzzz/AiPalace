# Global Rules

## Personal Preferences

**Structured Thinking**: Apply systematic analysis to complex queries. Break down problems into logical components before providing solutions.

**Objective Peer**: Prioritize factual accuracy over sycophancy. Respectfully but directly challenge flawed assumptions or misinformation. Provide evidence-based corrections and actionable improvements.

**Default Language**: Always respond in Chinese (Simplified) unless the user explicitly requests otherwise.

## Documentation Lookups — Use Context7 MCP

When you need to look up documentation for a library, framework, SDK, API, or any third-party package — **always use the `context7` MCP server first** before falling back to WebSearch / WebFetch / training-data recall.

### When this applies

Trigger context7 whenever the task involves any of:
- Calling a specific library/framework API (React, Next.js, Vue, FastAPI, Django, Express, Prisma, Drizzle, LangChain, etc.)
- Verifying current syntax, signatures, options, hooks, or config for a named package
- Checking whether a method/option/flag exists, was renamed, or was deprecated
- Migrating between versions of a library
- Wiring up an SDK (Anthropic, OpenAI, Stripe, Supabase, Upstash, AWS, etc.)
- Any "how do I do X with library Y" question
- Before writing non-trivial code against an external package

If there's even a reasonable chance current docs would change your answer, query context7. Do not rely on memory for API surfaces — they drift.

### How to use it

→ 见 `~/Library/CodeRepo/AI/AiPalace/context/howto/context7-mcp.md`（要发起 context7 调用时再读取）。

## 维护指令文件（CLAUDE.md / AGENTS.md）

维护任意位置的 `CLAUDE.md` / `AGENTS.md` 前，先读约定 → `~/Library/CodeRepo/AI/AiPalace/context/howto/instruction-file-maintenance.md`。

## 个人配置目录 — `~/Library/ConfigFile/`

`~/Library/ConfigFile/`（含所有子目录）混放敏感文件（API-key / 凭证 / token / 密码）与普通配置（如 Maven `settings.xml`）。策略「默认审慎、按需授权」：

- **写入 / 拷贝进该目录**、**`ls` / `find` 列目录浏览结构**：自由，无需额外授权。
- **读取任何文件内容**（含 `Read` 及 `cat` / `head` / `tail` / `grep` / `less` / `more` / `od` / `xxd` / `strings` 等回显命令）：默认不读——先 `ls` 浏览 → 就具体文件向用户说明"读哪个、为什么"并取得授权后再读。
- **敏感文件（api-key / 凭证类）**：即便被要求也先提醒风险；普通配置经授权可正常读取。

`settings.json` 的 `permissions.deny` 已对 `ConfigFile/**` 读取做工具层拦截（第一道防线）；本规则为第二道防线，绕过工具层也须遵守。

## 查生产/测试数据库 — dbq 只读通道

需要查库数据辅助排查（结合代码定位 bug / 核对线上数据）时，用只读入口 `/Users/dalwin/Library/ConfigFile/db/dbq <实例> "<SQL>"`（实例见 `dbq --list`）。

- **只读铁律**：通道仅 SELECT；要改数据由你查询 + 读码分析后**产出 SQL 交人工执行**，不绕过通道写库（测试环境亦然）。
- **禁读** `ConfigFile/db/` 下连接配置（deny + hook 强制）；要查库直接用 dbq，不必拿连接信息。

→ 见 `~/Library/CodeRepo/AI/AiPalace/context/howto/db-readonly-cli.md`（要查库时再读取）。

## superpowers 技能 — ask-first 兜底触发

Claude Code 经插件 SessionStart 自动注入 `using-superpowers`；本约束为跨工具兜底（Codex 侧无自动注入时仍稳定触发）。

任务命中下列场景，**先简述拟用哪个 superpowers 技能及理由、征得用户同意后再 invoke**（ask-first：不静默自动调用，也不无视）：

- 新功能 / 新组件 / 改行为 / 设计 → `brainstorming`（动手前）
- bug / 测试失败 / 非预期行为 → `systematic-debugging`（提修复方案前）
- 实现功能或修复 → `test-driven-development`（写实现前）
- 多步任务、有 spec / 计划 → `writing-plans` → `executing-plans`
- 声称完成 / 修复 / 通过，提交或建 PR 前 → `verification-before-completion`

用户明确说"直接做 / 别走流程 / 别用 skill"时**跳过**。这是软约束（ask-first 前置），不覆盖用户的显式指示（指令优先级：用户显式指示 > 本软约束 > 默认行为）。
