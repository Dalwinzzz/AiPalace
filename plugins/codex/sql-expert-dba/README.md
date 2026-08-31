# SQL Expert DBA

面向 MySQL / PostgreSQL 与通用 SQL 场景的分析型 DBA 助手：查询优化、报错诊断、Schema 评审、业务报表 SQL 生成，配套便携式全局 SQL memory、项目级 `./sql` 上下文索引与 `./sql/biz-rules/` 业务规则沉淀。插件只读分析，不直连数据库、不执行 SQL。

## Skill 执行层为唯一沉淀真源

记忆沉淀发生在每个 workflow 收尾的强制自评估中（静默执行）：

- 评估通过 5 硬门槛且有可复用知识时，由 skill 直接调用 `memory_capture.py` 写入用户级全局目录
- 用户说「记下来 / 值得沉淀 / 帮我复盘 / 保存这个经验」时，立即切换显式沉淀模式
- 用户说「复审记忆 / 把这条转正」时，调用 `memory_promote.py` 将 candidate 晋升为 approved

不依赖任何后台 hook 或 Stop 事件——沉淀路径在 skill 内完全自洽。

## 记忆真源位置与重装不丢

| 版本 | 真源落点 | 说明 |
|------|---------|------|
| Codex | `~/.codex/memories/sql-expert-dba/` | 可被 `$CODEX_HOME/memories/sql-expert-dba/` 或 `$SQL_EXPERT_DBA_MEMORY_DIR` 覆盖 |
| Claude | `~/.claude/plugins/data/sql-expert-dba/memory/` | 可被 `$SQL_EXPERT_DBA_MEMORY_DIR` 覆盖 |

两版落点均与插件源码物理分离。插件重装或升级后，历史沉淀记忆保持不变。插件缓存目录中的 `memory/` 仅含 seed memory（`glossary-001` / `rule-001` / `template-001`），随版本分发，升级会被覆盖——详见 [`memory/WHERE-IS-MY-MEMORY.md`](memory/WHERE-IS-MY-MEMORY.md)。
