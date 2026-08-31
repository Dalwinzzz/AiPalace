# Codex 全局指令(受管 stub)

> **受管派生**:本文件真源在 `AiPalace/context/native/codex-global.md`,`~/.codex/AGENTS.md` 为其软链(P1/P2,ADR-0016)——改真源即生效,勿手改派生。
> **共享规则**:工具无关全局规则(个人偏好 / Context7 / ConfigFile 审慎 / dbq / ask-first / 跨工具 SOT / AiPalace 治理)单一源在 `vault/memory/00-RULES/operating-rules.md`,经 SessionStart hook 每会话注入。**若本会话开头未见 `[操作规则]` 注入块,先 Read `~/Library/CodeRepo/AI/AiPalace/vault/memory/00-RULES/operating-rules.md`。**

## Codex 专属

- **Workflow Memory Boundary**: AGENTS.md 与 SessionStart 注入的 `[操作规则]` 块共同构成 always-on 硬约束;memories 仅作辅助回忆或上下文提示,不承载必须始终生效的硬要求。
- **ConfigFile 第一道防线**:`~/.codex/hooks/pretooluse-configfile-guard.py` 对该目录读取返回 permissionDecision="ask";共享规则中的审慎策略为第二道防线。
- **公司项目(ZhiJin)必走 ownerpowers**:cwd 落在 `~/Library/IdeaProject/ZhiJin/**` 即公司项目——做开发需求 / 排查问题**一律先用 `ownerpowers` 判线判档**再动手,不得绕过它自行规划。
  - **spec 由 `spec-architect` 规范产出**,落盘 `{work-dir}/docs/spec-architect/{yyyy-mm}/{dd}/`(complex 为该日期下的当次任务目录)。
  - **过程文档可以产出**——计划 / 任务清单 / 调研笔记等都允许,`writing-plans` 也可用(它本就是 spec-architect complex 分支的正规衔接手段)。约束不在"能不能写",而在**写到哪**:**本次任务的全部过程文件一律收敛到上述 spec-architect 当次任务目录下**,不得另起 `docs/superpowers/` 或散落到仓库其它位置。
  - 本条对**直接使用 Codex** 与**被 Claude 的 codex plugin 委派**两种入口同等生效;后者即便转发来的 prompt 没提 ownerpowers,也按本条执行。
