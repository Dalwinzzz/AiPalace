# plugins —— 本地 AI 插件 SOT（双工具版本）

按工具分目录存放插件源码。Claude 版与 Codex 版「核心 SQL 专家能力逐字一致、工具 harness 差异隔离」
（求同存异，详见 `docs/dalwin-workflow/superpowers/specs` 下的 sql-expert-dba 双版本迭代设计）。

```
plugins/                        ← 双工具 plugins 唯一 SOT（ADR-0008）
├─ claude/                      ← Claude marketplace root（known_marketplaces dalwin-local-plugins 指向此处）
│  ├─ .claude-plugin/
│  │  └─ marketplace.json       ← dalwin-local-plugins marketplace（插件源 ./sql-expert-dba）
│  └─ sql-expert-dba/
│     ├─ .claude-plugin/plugin.json
│     ├─ skills/                ← 5 个 sql skill（router/optimizer/diagnostician/schema-reviewer/report-builder）
│     ├─ scripts/               ← memory + biz-rules + project-context 脚本（含测试）
│     ├─ memory/                ← memory 模板/规则/术语（真源运行时落 ~/.claude/plugins/data/）
│     └─ assets/                ← icon / logo
└─ codex/                       ← Codex marketplace root（config.toml marketplaces.dalwin-local-plugins source 指向此处）
   ├─ .agents/plugins/
   │  └─ marketplace.json       ← Codex 约定清单位置（dalwin-local-plugins，插件源 ./sql-expert-dba）
   └─ sql-expert-dba/
      ├─ .codex-plugin/plugin.json
      ├─ skills/                ← 同 claude 版 5 个 sql skill（_shared 主文档逐字一致）
      ├─ scripts/ · memory/ · assets/
```

> Codex 清单置于 `.agents/plugins/marketplace.json` 是 Codex marketplace 约定位置（实测 openai-bundled 印证）；Claude 用 `.claude-plugin/marketplace.json`。两 root 即各自工具 marketplace 注册的 source。

## 版本与真源说明

| 版本 | 源仓 SOT（现行） | memory 运行时真源（与源码分离，重装不丢） |
|------|----------|-------------------------------------------|
| Claude | `AiPalace/plugins/claude` | `~/.claude/plugins/data/sql-expert-dba/memory/` |
| Codex  | `AiPalace/plugins/codex` | `~/.codex/memories/sql-expert-dba/` |

> 两版均可用环境变量 `SQL_EXPERT_DBA_MEMORY_DIR` 覆盖 memory 落点。
> 原 `~/Documents/AI/plugins/{claude,codex}-sql-expert-dba`（空索引入口占位）的角色，
> 由本目录的 claude/ 与 codex/ 取代。

## ✅ SOT 切换完成（2026-06-25，ADR-0008）

双工具 plugins 源已正式切到本目录：
- **Claude**：经 `claude plugin marketplace add <AiPalace>/plugins/claude` 注册（写入 settings.json，durable）+ `claude plugin install sql-expert-dba@dalwin-local-plugins` 重装；装的是 cache 快照。**禁止手编** `known_marketplaces.json`（会被 Claude 回退，详见 ADR-0008 后续修正）。
- **Codex**：`codex plugin marketplace add` 注册 `AiPalace/plugins/codex`，`config.toml [marketplaces.dalwin-local-plugins]` source 指此；`sql-expert-dba@dalwin-local-plugins` installed/enabled。

旧源 `~/Library/CodeRepo/AI/claude-plugins`、`~/.agents/plugins` 退役并已于 2026-06-25 清理（复验逐字一致后删除）。
> 双工具 plugin 状态一律走各自官方 CLI（`claude plugin` / `codex plugin`），禁止手编工具自管状态文件。
