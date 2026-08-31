# Claude Code 全局指令(受管 stub)

> **受管派生**:本文件真源在 `AiPalace/context/native/claude-global.md`,`~/.claude/CLAUDE.md` 为其软链(P1/P2,ADR-0016)——改真源即生效,勿手改派生。
> **共享规则**:工具无关全局规则(个人偏好 / Context7 / ConfigFile 审慎 / dbq / ask-first / 跨工具 SOT / AiPalace 治理)单一源在 `vault/memory/00-RULES/operating-rules.md`,经 SessionStart hook 每会话注入。**若本会话开头未见 `[操作规则]` 注入块,先 Read `~/Library/CodeRepo/AI/AiPalace/vault/memory/00-RULES/operating-rules.md`。**

## Claude 专属

- **ConfigFile 第一道防线**:`~/.claude/settings.json` 的 `permissions.deny` 已对 `ConfigFile/**` 读取做工具层拦截;共享规则中的审慎策略为第二道防线。
- **codex plugin(openai-codex)ask-first**:`codex:codex-rescue` 子代理 frontmatter 写的是"Proactively use when...",无官方开关能让它只被动响应。技术侧已用 `~/.claude/hooks/guard-codex-rescue.sh`(PreToolUse,matcher=Agent)拦截该 subagent_type、一律转 `ask` 强制人工确认——本条为第二道防线:除非用户在当前这轮消息里明确要求用 Codex / codex-rescue,或直接敲了 `/codex:*` 命令,否则不得主动派发该子代理;`/codex:review`、`/codex:setup` 等纯 slash command 型能力本身就只能显式触发,不受此条约束。
- **codex plugin 选模型:默认不传 `--model`,要传先查证真名**:
  - **默认省略 `--model`**——Codex 会用 `~/.codex/config.toml` 里 `model = ...` 的默认模型(用户自己维护,通常已是最新),不传即最优解,也免掉写错名字的风险。
  - **仅当用户明确点名某模型时才传 `--model`**,且传之前**必须查证真实模型 id**:优先读 `~/.codex/config.toml` 的 `model=`,或查官方文档/`codex` CLI;**严禁按别名构词法自行推导**。
  - **教训(2026-08-08 实测)**:插件 `MODEL_ALIASES` 只登记了 `spark → gpt-5.3-codex-spark`,我据此套出 `gpt-5.6-codex-terra`,被服务端 400 拒;真名是 **`gpt-5.6-terra`**(无 `-codex-` 段),`codex exec` 与插件 app-server 两条链路实测均正常。
  - **别再怀疑"插件不支持某模型"**:`codex-companion.mjs` 的 `normalizeRequestedModel` 是 `别名表 ?? 原样透传`,**无任何模型白名单**;插件也不持有凭证(直接 `spawn("codex","app-server")` 复用 `~/.codex/auth.json` 的 ChatGPT 登录态)。模型准入完全由账号在服务端判定,**魔改插件解锁不了账号没有的模型**。
- **codex plugin 委派公司项目任务:先判档,决策不外派,过程文件统一落盘**:在公司项目(`~/Library/IdeaProject/ZhiJin/**`)把活派给 `codex:codex-rescue` 前,先按 `ownerpowers` 判线判档。
  - **外派禁区管的是决策内容,不是文档动作**:方案选型·根因定调·提交计划·`grilling` 的每一问,一律回主线由用户本人拍板,不得让 Codex "顺便定了";但**写文档这个动作本身可以外派**——决策已由主线定过之后,Codex 可以产出 spec / 计划 / 调研笔记等过程文件。
  - **转发 prompt 时必须显式附带落盘约束**(不依赖 Codex 自行选中 skill,Codex 侧 AGENTS.md 已有同规则兜底):"走 `ownerpowers` 分档;**本次全部过程文件(spec / 计划 / 任务清单 / 调研笔记,含 `writing-plans` 产物)一律写进 `{work-dir}/docs/spec-architect/{yyyy-mm}/{dd}/` 当次任务目录**,不得另起 `docs/superpowers/` 或散落到仓库其它位置"。
