# ADR-0008：双工具 plugins SOT 切到 AiPalace + Codex marketplace 改 `.agents/plugins` 约定布局

- 状态：已接受
- 日期：2026-06-25
- 决策人：dalwin
- 关联：落实 final-spec 阶段 4 降级的 plugins 待决项；延续 [ADR-0001](0001-AiPalace为个人AI-harness唯一SOT.md)（唯一 SOT）、[ADR-0004](0004-迁入plugins-docs规范-creations为SOT统一作准备.md)（plugins 迁入）

## 背景

SOT 切换 final-spec 阶段 4 把 plugins 降级为待决项，因实测发现**三处来源**：

- Claude：marketplace `dalwin-local-plugins`（`~/.claude/plugins/known_marketplaces.json`，`directory` 源）→ `~/Library/CodeRepo/AI/claude-plugins`（独立 git 仓）。
- Codex：`local-plugins` marketplace 由 `~/.agents/plugins/marketplace.json`（personal，root=home）**自动发现**，`config.toml` 仅存其插件 enabled 态。
- AiPalace：`plugins/{claude,codex}` 镜像。

**内容比对结论**（排除 `__pycache__`/`WHERE-IS-MY-MEMORY` 等缓存垃圾）：双工具 `sql-expert-dba` 在 live 源与 AiPalace 间**逐字一致**（均 1.2.0）——所谓"分叉"是假警报，**切换无需内容调和，纯粹重指 marketplace 源**。

**官方文档要点**（code.claude.com plugin-marketplaces；developers.openai.com codex/plugins,build）：

- Claude 本地 marketplace = `<root>/.claude-plugin/marketplace.json`，插件源 `./<name>` 相对 root；`/plugin marketplace add/update`（TUI）；安装时 directory 源就地从 `installLocation` 读。
- Codex marketplace 约定（实测 openai-bundled 印证）= `<root>/.agents/plugins/marketplace.json` + 插件在 root 内、`source.path` 相对 root 且**不得越出 root、不得绝对**；CLI `codex plugin marketplace add/remove`、`codex plugin add/remove`；`config.toml` 记 `[marketplaces.<name>]`（支持绝对 source）+ `[plugins."<p>@<m>"] enabled`。
- AiPalace `plugins/codex` 旧布局（根 `marketplace.json` + `source.path` bug `./.agents/plugins/sql-expert-dba`）**不符 Codex 约定**。

## 决策

1. **AiPalace/plugins 为双工具 plugins 唯一 SOT。**
2. **Codex**：`plugins/codex` 重构为约定布局——清单移至 `plugins/codex/.agents/plugins/marketplace.json`（命名统一 `dalwin-local-plugins`、`source.path` 修为 `./sql-expert-dba`），插件真身保持 `plugins/codex/sql-expert-dba/`。经 `codex plugin marketplace add <AiPalace/plugins/codex>` 注册（落 `config.toml [marketplaces.dalwin-local-plugins] source=AiPalace/plugins/codex`）+ `codex plugin add sql-expert-dba@dalwin-local-plugins` 安装；移除旧（卸 `sql-expert-dba@local-plugins` + 把 `~/.agents/plugins/marketplace.json` 改名中和其自动发现）。
3. **Claude**：`known_marketplaces.json` 把 `dalwin-local-plugins` 的 `source.path` + `installLocation` 重指 `~/Library/CodeRepo/AI/claude-plugins` → `AiPalace/plugins/claude`（directory 源就地读、内容一致，无缝）。TUI `/plugin marketplace remove+add` 为受支持等价路径；因本会话不能跑 TUI 斜杠命令，改为直编该 state 文件（JSON-safe）并留新 session 验证 + TUI 回退。
4. **旧源退役**：`~/Library/CodeRepo/AI/claude-plugins`、`~/.agents/plugins` 不再为现役引用（后者 `marketplace.json` 已改名 `.retired-*` 中和），列入清理待决。

## 后果

**正面**：双工具 plugins 单源 AiPalace（达成"harness 配置全走 AiPalace"目标）；Codex 走官方 CLI、状态落 `config.toml`；内容逐字一致 → 切换零内容风险；全程有备份（`ConfigFile/claude/sot-switch-backup-*/plugins-config/`）。

**取舍 / 待观察**：
- Claude 直编 `known_marketplaces.json` 非 TUI 受支持路径——**需新 Claude session 验证** sql-expert-dba 仍可用；异常则 TUI `/plugin marketplace update dalwin-local-plugins` 或 remove+add 回退。
- Codex `codex plugin add` 装的是 **cache 快照**（`~/.codex/plugins/cache/dalwin-local-plugins/sql-expert-dba/1.2.0`）；AiPalace 源日后更新需 `codex plugin marketplace upgrade` / 重装刷新（与 Claude directory 源就地读不同，属双工具机制差异，P7 可接受）。
- 旧源目录 `~/Library/CodeRepo/AI/claude-plugins`、`~/.agents/plugins` 留待清理（见 NEXT-STEPS）。

> 实证：官方文档 + `codex plugin` CLI 实跑（P5）。备份与回滚见 SOT 切换执行 ledger。

---

## 后续修正（2026-06-26，P5/P8 诚实标注）

上方决策 #3 的 **Claude 侧手编 `known_marketplaces.json`** 方案**被实证推翻**：

- **失败现象**：新 Claude session 验证发现 `sql-expert-dba` 不可用，`claude plugin list` 报 `Marketplace dalwin-local-plugins failed to load: cache-miss`。
- **根因（两错叠加）**：① Claude 会**自动重写** `known_marketplaces.json`，把手编的 AiPalace 指向**回退**回 `~/Library/CodeRepo/AI/claude-plugins`；② 随后旧源清理把 `~/Library/CodeRepo/AI/claude-plugins` 删除 → marketplace 指向已删目录、cache 缺失，插件加载不了。
- **另一处认知错误**：原文称 Claude directory 源「就地读」——错。`claude plugin install` 会**拷贝一份 cache 快照**（`~/.claude/plugins/cache/<mkt>/<plugin>/<ver>/`），与 Codex 同属 cache 快照机制（源更新需 `update`/重装刷新）。

**修正方案（改用官方 CLI，durable）**：

```
claude plugin marketplace remove dalwin-local-plugins      # 移除指向已删目录的坏 marketplace
claude plugin marketplace add  <AiPalace>/plugins/claude    # 重指 AiPalace（写入 settings.json，不被回退）
claude plugin install sql-expert-dba@dalwin-local-plugins   # 重装，生成 cache 快照
claude plugin list                                          # 验证：无 cache-miss、installed/enabled
```

**教训**：双工具 plugin 状态一律走各自官方 CLI（`claude plugin` / `codex plugin`），**禁止手编** `known_marketplaces.json` / `installed_plugins.json` 等工具自管状态文件（会被回退）。
