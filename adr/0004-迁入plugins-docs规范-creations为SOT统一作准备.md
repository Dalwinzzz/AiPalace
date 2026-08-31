# ADR-0004：迁入 plugins / docs 规范 / creations，为 SOT 统一管理作准备

- 状态：已接受
- 日期：2026-06-16
- 决策人：dalwin
- 关联：[ADR-0001](0001-AiPalace为个人AI-harness唯一SOT.md)

## 背景

ADR-0001 已确立 AiPalace 为个人本地 AI harness 实践的唯一 SOT，并迁入了 skills 与 dalwin-workflow
的 context/docs。但仍有两处 AI 相关产出散落在外：

1. `~/Documents/AI/`：AwesomeCreator（codex 桌宠 mon3tr 创作）、顶层 `docs/`（文档管理**规范** SOT +
   archive/knowledge/superpowers/problem）、`plugins/`（双版本索引入口空占位）。
2. `~/Library/CodeRepo/AI/claude-plugins/`：Claude 版 sql-expert-dba 插件源（marketplace + 插件）。

此外 Codex 版插件源在 `~/.agents/plugins/`。这些是后续「重构本地 AI 工具配置、把所有 SOT 指向
统一到 AiPalace」的前置物料。

## 决策

本轮**只做 AiPalace 侧的迁移搭建，复制保留源，不动任何现有配置**（hook / 软链 / 插件加载 /
codex 缓存仍指向旧源，照常工作）。

### 1. plugins/ —— 按工具分目录
- `plugins/claude/` ← `~/Library/CodeRepo/AI/claude-plugins/`（marketplace.json + sql-expert-dba，含 .claude-plugin）
- `plugins/codex/`  ← `~/.agents/plugins/`（marketplace.json + sql-expert-dba，含 .codex-plugin）
- `plugins/README.md` 说明双版本「求同存异」布局与 memory 真源落点。
- 原 `~/Documents/AI/plugins/{claude,codex}-sql-expert-dba`（空索引入口占位）角色由此取代。

### 2. docs/ —— 以顶层规范为骨架
- `~/Documents/AI/docs/` 的规范 README + archive/knowledge/superpowers/problem 迁入 `AiPalace/docs/`。
- 规范 README 的「适用范围」路径引用更新为 AiPalace，并加迁移说明。
- 初始化时已迁入的 `docs/dalwin-workflow/`（dalwin-workflow 活跃区）按规范作为来源子路径并存，
  其归档落在 `docs/archive/dalwin-workflow/`——与规范 README「归档统一进顶层 archive、来源路径作子目录」一致。

### 3. creations/ —— 创作产物
- `creations/mon3tr-codex/v1..v4` ← AwesomeCreator 的 codex 桌宠 sprite。
- AwesomeCreator 的「有意思的记录.md」（Palace 知识架构）→ `docs/knowledge/palace-知识架构记录.md`。

### 4. 修正 .gitignore 副作用
`logs/`（无前导 `/`）会匹配任意层级 logs 目录，误伤 `docs/.../plans/logs/` 内 10 个 codex 迁移
历史文档（资产，非垃圾）。精确化为 `/logs/`，仅忽略顶层 skillctl 运行日志，保留用户「忽略垃圾」本意。

## 后果

- 正面：四处 AI 产出（skills/plugins/docs规范/creations）齐聚 AiPalace，为下一步 SOT 指向统一备齐物料。
- 过渡态：源仍在原位、现有工具仍指向旧源。**SOT 正式切换**（改 hook/软链/插件加载指向 AiPalace、
  废弃旧源）留待后续「本地 AI 工具配置重构」专项，本轮不做。
- 待办（见 NEXT-STEPS）：plugins/codex 与 codex 缓存 1.2.0 的版本对账；docs 按规范做一次 archive/knowledge
  归类复检；dalwin-workflow 源目录在 SOT 切换后的废弃。
