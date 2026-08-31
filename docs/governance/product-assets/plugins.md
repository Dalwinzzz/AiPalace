# plugins.md — 插件机制规范

> 关联哲学：[PHILOSOPHY P7](../../../PHILOSOPHY.md#p7--内容统一源机制分治)
>
> 本规范定义 AiPalace 插件体系的版本布局、边界划分与 memory 真源落点。现状索引见 [`plugins/README.md`](../../../plugins/README.md)。

---

## 原则

插件（plugin）是**与特定工具 harness 深度耦合的可发布单元**，包含工具专属配置、技能声明、脚本、图标等完整部署包。插件机制属于产品形态，遵循 **P7 机制分治**：双工具各自维护自己的插件目录，内容能力（SQL 知识、业务规则等）以工具无关形式在插件内对齐，harness 差异隔离于各自版本。

---

## 双工具版本布局

```
plugins/
├─ claude/                          ← Claude Code 版插件
│  ├─ .claude-plugin/
│  │  └─ marketplace.json           ← dalwin-local-plugins marketplace 索引
│  └─ sql-expert-dba/               ← SQL 专家 DBA 插件（Claude 版）
│     ├─ .claude-plugin/plugin.json ← 插件元信息（Claude harness）
│     ├─ skills/                    ← 5 个 SQL skill（router/optimizer/diagnostician/schema-reviewer/report-builder）
│     ├─ scripts/                   ← memory + biz-rules + project-context 辅助脚本（含测试）
│     ├─ memory/                    ← memory 模板/规则/术语（见 memory 真源落点）
│     └─ assets/                    ← icon / logo
└─ codex/                           ← Codex 版插件（marketplace root；ADR-0008）
   ├─ .agents/plugins/marketplace.json  ← Codex 约定清单位置（dalwin-local-plugins，源 ./sql-expert-dba）
   └─ sql-expert-dba/               ← SQL 专家 DBA 插件（Codex 版）
      ├─ .codex-plugin/plugin.json  ← 插件元信息（Codex harness）
      ├─ skills/                    ← 同 claude 版 5 个 SQL skill（_shared 主文档逐字一致）
      ├─ scripts/ · memory/ · assets/
```

### 版本对齐原则

- **核心能力逐字一致**：SQL 专家的诊断逻辑、优化建议、查询构建等 skill 主文档（`_shared`）在两版本中保持一致。
- **harness 差异隔离**：`plugin.json` 格式、钩子注册方式、工具调用语法等与工具形态相关的部分，各版本独立维护，不强行统一。
- **求同存异**：内容求同（避免知识分叉），形式存异（避免 harness 污染）。

---

## 插件 ↔ Skill 边界

### 何时做插件（plugin）

满足以下任一条件时，应作为插件：

| 条件 | 说明 |
|------|------|
| **需要工具特定部署配置** | `plugin.json`、marketplace 注册、图标、assets 等工具专属元信息不可缺 |
| **包含辅助脚本/数据** | 有 `scripts/`（获取 biz-rules、project-context）或外部数据依赖，作为 skill 单文件无法容纳 |
| **需要独立 memory 存储** | 有跨会话持久化的领域 memory，且需要与工具 native memory 分离管理（见 memory 真源落点） |
| **多 skill 成体系** | 一组 skill 共享同一领域知识库（如 SQL 专家的 5 个 skill），整体部署比散装更合理 |
| **需要 marketplace 发布** | 计划在本地或团队 marketplace 注册分发 |

### 何时做 Skill（skill）

满足以下条件时，应直接作为 skill（`skills/` 下的 `.md` 文件）而非插件：

| 条件 | 说明 |
|------|------|
| **单文件可容纳** | skill 逻辑自足，无需脚本或外部数据 |
| **工具无关** | 核心逻辑对 Claude / Codex 都适用，无 harness 专属部分 |
| **无独立 memory 需求** | 不需要跨会话持久化自己专属的领域 memory |
| **轻量场景** | 快速落地的辅助能力，不值得为其创建完整插件目录结构 |

### 判断树

```
需要 plugin.json / marketplace 注册？
    ├─ 是 → 做插件
    └─ 否 → 有辅助脚本或独立 memory？
                ├─ 是 → 考虑插件（若规模值得）
                └─ 否 → 直接做 skill（skills/ 下 .md）
```

> 边界模糊时优先做 skill，保持轻量；待 memory/脚本/部署需求出现后再升级为插件。

---

## memory 真源落点

插件 memory 的真源分**仓库层（源码）**与**运行时层（数据）**两层，严格分离：

| 层 | Claude 版 | Codex 版 | 说明 |
|----|-----------|----------|------|
| **仓库源码层**（SOT） | `plugins/claude/sql-expert-dba/memory/` | `plugins/codex/sql-expert-dba/memory/` | 模板、规则、术语定义；随仓库版控 |
| **运行时数据层**（持久化，重装不丢） | `~/.claude/plugins/data/sql-expert-dba/memory/` | `~/.codex/memories/sql-expert-dba/` | 实际运行积累的 memory 条目；不进仓库 |

- 环境变量 `SQL_EXPERT_DBA_MEMORY_DIR` 可覆盖运行时 memory 落点（两版均支持）。
- 运行时 memory 是工具 native memory 的专属域，不与 AiPalace `memory/` 主线混用。
- 可从运行时 memory 周期凝练提取高价值条目写回仓库 memory 模板层（与 injection.md 机制 C 对齐）。

---

## SOT 说明

`plugins/` 目录已为双工具 plugins 唯一 SOT（2026-06-25 切换完成，[ADR-0008](../../../adr/0008-双工具plugins切到AiPalace并改Codex约定布局.md)）：

| 版本 | 现行 SOT | 工具注册指向 | 旧源（已退役） |
|------|----------|--------------|----------------|
| Claude | `plugins/claude/` | `claude plugin marketplace add` → `dalwin-local-plugins`（落 settings.json） | `~/Library/CodeRepo/AI/claude-plugins` |
| Codex | `plugins/codex/` | `config.toml [marketplaces.dalwin-local-plugins]` | `~/.agents/plugins`（`marketplace.json` 已改名中和） |

> 切换机制与取舍见 ADR-0008（含 2026-06-26 后续修正）；旧源目录 `~/Library/CodeRepo/AI/claude-plugins`、`~/.agents/plugins` 已于 2026-06-25 清理（复验逐字一致后删除）。
> Codex marketplace 清单须置于 root 内 `.agents/plugins/marketplace.json`（约定位置），`source.path` 相对 root 且不得越界。
> **plugin 状态一律走官方 CLI**（`claude plugin marketplace add/install`、`codex plugin marketplace add` / `plugin add`）；**禁止手编** `known_marketplaces.json` / `installed_plugins.json` 等工具自管状态文件（Claude 会自动回退手编结果）。

---

## 参考

- [plugins/README.md](../../../plugins/README.md) — 现状索引（双版本目录结构与迁移状态）
- [PHILOSOPHY.md P7](../../../PHILOSOPHY.md) — 内容统一源、机制分治原则
- [injection.md](./injection.md) — 注入机制规范（含 native memory 协同）
- 设计 spec §7.2：`docs/superpowers/specs/2026-06-18-aipalace治理与设计哲学-design.md`
