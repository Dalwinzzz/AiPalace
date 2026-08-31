# sql-expert-dba → Claude 插件迁移设计 spec — 2026-06-03

> 范围：把 Codex 本地插件 `sql-expert-dba`（v1.1.0）的核心能力迁移为一个**独立的 Claude Code 插件**（`.claude-plugin`）。v1 覆盖 5 技能 + 4 契约 + 全局 memory；项目级 `./sql` 上下文、`./sql/biz-rules`、守护式自动沉淀 hook 延后 v2。
>
> 决策来源：2026-06-03 brainstorming 七项决策（见 §2）。
>
> 官方规范核对：context7 `/anthropics/claude-code` —— 插件目录结构、`${CLAUDE_PLUGIN_ROOT}`、`marketplace.json` 格式。

---

## 1. 背景与目标

用户已有 Codex 本地插件 `sql-expert-dba`（注册于 `~/.codex/plugins/cache/local-plugins/sql-expert-dba/1.1.0/`，镜像于 `~/.agents/plugins/sql-expert-dba`），希望在 Claude 中获得同等的分析型 SQL DBA 能力。

目标：

1. 以**独立 Claude 插件**形态 1:1 还原 sql-expert-dba 的核心能力。
2. **不改动** Codex 版插件（与「任务1 不碰 plugins 层」取向一致）。
3. 迁移核心分析能力 + 知识沉淀子系统；触发机制适配 Claude 技能模型。
4. 意图与 Codex 版一致，但各自独立维护（SQL 知识两份，后续手动对齐）。

非目标（v1）：项目级 `./sql` 上下文索引、`./sql/biz-rules` 业务规则、Codex 风格守护式自动沉淀 hook。

---

## 2. 决策汇总（brainstorming 2026-06-03）

| # | 决策点 | 选择 |
|---|---|---|
| 1 | 形态 | Claude 插件（`.claude-plugin`），1:1 还原 |
| 2 | 源策略 | 独立 Claude 插件，源放 SOT，不动 Codex 版（知识两份，手动对齐） |
| 3 | 记忆触发 | 技能驱动沉淀（无全局 hook）；memory 子系统与脚本完整平移 |
| 4 | v1 范围 | 核心 5 技能 + 4 契约 + 全局 memory；项目层延后 v2 |
| 5 | router 拓扑 | 保留 router + 4 专家（5 技能） |
| 6 | memory 落点 | `~/.claude/plugins/data/sql-expert-dba/memory/` |
| 7 | 安装方式 | 本地 marketplace + `/plugin install` |

---

## 3. 源插件能力盘点

- **5 技能**：`sql-expert-router`（总入口分诊）、`sql-query-optimizer`、`sql-error-diagnostician`、`sql-schema-reviewer`、`sql-report-query-builder`。
- **4 共享契约**（`skills/_shared/`）：`output-contract.md`（六段式输出）、`missing-input-checklists.md`、`memory-policy.md`、`dialect-guidelines.md`。
- **memory 子系统**：分层（`glossary`/`rules`/`cases`/`templates`/`candidates`），`candidate`↔`approved` 两态，YAML front matter，强制去敏，`index.json` 轻量索引。
- **脚本**（v1 平移）：`memory_search.py`、`memory_capture.py`、`memory_index.py`、`paths.py`、`_frontmatter.py` 及对应 `test_*.py`。
- **脚本**（v2 延后）：`project_context_index.py`、`project_context_search.py`、`biz_rules_capture.py`、`biz_rules_search.py`、`biz_rules_git_guard.py`、`auto_memory_runner.py`。
- **项目层**（v2 延后）：`./sql/.index/`、`./sql/biz-rules/`。

---

## 4. Codex → Claude 构件映射

Claude 插件结构与 Codex 插件几乎同构，平移成本低。

| 构件 | Codex 落点 | Claude 落点 | 适配动作 |
|---|---|---|---|
| 清单 | `.codex-plugin/plugin.json` | `.claude-plugin/plugin.json` | 转换字段；去掉 Codex 专有 `interface`/`composerIcon`/`defaultPrompt` 块 |
| 技能 | `skills/{name}/SKILL.md` | `skills/{name}/SKILL.md` | frontmatter 同为 `name`+`description`，直接平移；自动发现，无需清单登记 |
| 共享契约 | `skills/_shared/*.md` | `skills/_shared/*.md` | 直接平移；`_shared` 无 SKILL.md 不会被当作技能 |
| 脚本 | `scripts/*.py` | `scripts/*.py` | v1 子集平移；脚本调用路径改 `${CLAUDE_PLUGIN_ROOT}/scripts/` |
| 内置 seed | `memory/` | `memory/` | 直接平移（插件内置 seed，两边都非工具原生能力） |
| 资产 | `assets/icon.svg`/`logo.svg` | `assets/` | 可选保留 |
| 运行时 memory | `~/.codex/memories/sql-expert-dba/` | `~/.claude/plugins/data/sql-expert-dba/memory/` | 改 `paths.py` 默认落点，保留 env 覆盖 |
| 自动沉淀触发 | Codex Hook → `auto_memory_runner.py` | 技能内步骤 → `memory_capture.py` | 不移植 hook 接线；改技能驱动 |

---

## 5. 文件布局（SOT）

marketplace 根与插件分离（`marketplace.json` 在 marketplace 根，不在插件自身 `.claude-plugin/`）：

```
~/Library/CodeRepo/AI/claude-plugins/            # 本地 marketplace 根
├── .claude-plugin/
│   └── marketplace.json                          # 列出 sql-expert-dba，source "./sql-expert-dba"
└── sql-expert-dba/                               # 插件本体
    ├── .claude-plugin/
    │   └── plugin.json
    ├── skills/
    │   ├── sql-expert-router/SKILL.md
    │   ├── sql-query-optimizer/SKILL.md
    │   ├── sql-error-diagnostician/SKILL.md
    │   ├── sql-schema-reviewer/SKILL.md
    │   ├── sql-report-query-builder/SKILL.md
    │   └── _shared/
    │       ├── output-contract.md
    │       ├── missing-input-checklists.md
    │       ├── memory-policy.md
    │       └── dialect-guidelines.md
    ├── scripts/
    │   ├── paths.py
    │   ├── _frontmatter.py
    │   ├── memory_search.py
    │   ├── memory_capture.py
    │   ├── memory_index.py
    │   └── test_*.py
    ├── memory/                                    # 内置 seed
    │   ├── glossary/glossary-001-covering-index.md
    │   ├── rules/rule-001-implicit-type-conversion.md
    │   ├── templates/template-001-daily-statistics.md
    │   ├── README.md
    │   └── index.json
    └── assets/
        ├── icon.svg
        └── logo.svg
```

运行时可写数据（与只读插件包分离）：`~/.claude/plugins/data/sql-expert-dba/memory/`。

---

## 6. 清单文件设计

### 6.1 `sql-expert-dba/.claude-plugin/plugin.json`

保留 `name`/`version`/`description`/`author`/`license`/`keywords`；去掉 Codex 的 `interface` 块。skills 由 `skills/` 自动发现，无需在清单登记。

```json
{
  "name": "sql-expert-dba",
  "version": "1.0.0",
  "description": "面向 MySQL/PostgreSQL 与通用 SQL 的分析型 DBA 助手：查询优化、报错诊断、Schema 评审、业务报表 SQL 生成，配套去敏的便携式全局 SQL memory。不直连数据库、不执行 SQL。",
  "author": { "name": "dalwin" },
  "license": "MIT",
  "keywords": ["sql", "mysql", "postgresql", "query-optimization", "schema-review", "reporting-sql", "dba"]
}
```

> 版本号从 `1.0.0` 起（Claude 插件 v1），与 Codex 的 `1.1.0` 解耦。

### 6.2 `claude-plugins/.claude-plugin/marketplace.json`

```json
{
  "$schema": "https://json.schemastore.org/claude-code-marketplace.json",
  "name": "dalwin-local-plugins",
  "version": "1.0.0",
  "description": "dalwin 本地 Claude 插件 marketplace",
  "plugins": [
    {
      "name": "sql-expert-dba",
      "description": "分析型 SQL DBA 助手：优化/诊断/评审/报表 + 全局 SQL memory",
      "source": "./sql-expert-dba",
      "category": "development"
    }
  ]
}
```

---

## 7. 5 技能与契约

### 7.1 内容平移

六段式输出契约、缺失输入分级检查表、记忆策略、方言指南、MySQL/PG 错误码速查、反模式分级表、Schema 评审 P0–P3 分级、报表口径澄清等**原文平移**。全局原则（区分 `已确认`/`[推断]`、输入不足先指缺口、默认只读 SQL、默认不展开教学）保留。

### 7.2 router 触发模型

`sql-expert-router` 保留为总入口：分诊决策树 + 4 条固定串联链路 + 前置 `memory_search` 检索。

Claude 按 description 自动触发，因此实际行为：

- **清晰单意图**（如「优化这条 SQL」）可能直达对应专家技能。
- **歧义 / 多 workflow 串联**由 router 兜底分诊与编排。
- 各专家技能 description 保持精确，确保单意图直达不被 router 抢占；router description 强调「分诊/串联/入口」语义。

### 7.3 脚本路径适配

各 SKILL 中调用脚本统一改为：

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/memory_search.py" ...
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/memory_capture.py" ...
```

### 7.4 v2 段落处理

各专家技能内的「v2 项目上下文发现 / 使用的项目上下文 / 命中的业务规则」段落，在 v1 标注 **「v2 延后，未随本版发布」**，并移除对 `./sql/.index/`、`./sql/biz-rules/`、`project_context_*`、`biz_rules_*` 的硬调用，避免引用未打包脚本导致运行错误。

---

## 8. Memory 子系统与技能驱动沉淀

### 8.1 子系统平移

分层目录、`candidate`↔`approved`、YAML front matter 字段（`id/title/type/workflow/dialect/tags/problem_pattern/preconditions/conclusion/boundaries/example/anti_example/confidence/review_status/...`）、强制去敏、`index.json` 全部平移。

两类目录需区分（与 Codex 版一致）：

- **内置 seed**（`${CLAUDE_PLUGIN_ROOT}/memory/`）：只读参考，扁平布局（`glossary/`、`rules/`、`templates/` + `index.json`），随包发布，**不作为运行时沉淀真源**。
- **运行时数据目录**（`~/.claude/plugins/data/sql-expert-dba/memory/`）：可写真源，由 `ensure_global_memory_dirs()` 构建为按状态嵌套布局（`approved/{glossary,rules,cases,templates}` + `candidates/{...}` + `index.json` + `capture-log.jsonl`）。

「seed 是否在首次运行时被检索/合并入运行时索引」属实现细节，由实施计划阶段决定。

### 8.2 `paths.py` 适配

`resolve_user_memory_dir()` 解析顺序改为：

1. `SQL_EXPERT_DBA_MEMORY_DIR`（保留，最高优先）
2. 默认落点：`~/.claude/plugins/data/sql-expert-dba/memory/`

移除对 `CODEX_HOME`/`~/.codex` 的默认回退（Claude 版独立）。`ensure_global_memory_dirs()` 等其余逻辑不变。

### 8.3 技能驱动沉淀流程（无全局 hook）

| 时机 | 动作 |
|---|---|
| workflow 开始 | 技能调 `memory_search.py` 检索相关 `approved` 记忆，命中则在分诊/分析中附提示 |
| 主任务完成 | 技能在六段式「沉淀结果」段执行后台评估：满足 5 硬门槛→调 `memory_capture.py` 写 `candidate` |
| 用户显式「记下来/复盘/保存这个经验」 | 展示沉淀过程，校验+去敏+去重通过后写 `approved` |

读写分离：插件包（脚本/seed）经 `${CLAUDE_PLUGIN_ROOT}` 只读引用；运行时 memory 写入可写的 `~/.claude/plugins/data/sql-expert-dba/memory/`。

### 8.4 不移植项

`auto_memory_runner.py`（为 Codex hook `--input` JSON 设计）及其 hook 接线在 v1 不移植——技能驱动已覆盖其职责。

---

## 9. v1 边界与延后

**v1 包含**：

- 5 技能（router + 4 专家）+ 4 共享契约
- 全局 memory 子系统：`memory_search.py` / `memory_capture.py` / `memory_index.py` / `paths.py` / `_frontmatter.py` + 内置 seed
- 本地 marketplace + plugin.json
- 单元测试：平移 `test_memory*.py`、`test_paths.py`（按 Claude 路径调整断言）

**v2 延后**：

- 项目级 `./sql` 上下文索引（`project_context_*`）
- `./sql/biz-rules` 业务规则（`biz_rules_*`）
- 守护式自动沉淀 hook（`auto_memory_runner` + Claude hook 接线）
- 与 Codex 版的知识对账机制

---

## 10. 安装与验证

### 10.1 安装

```bash
claude plugin marketplace add /Users/dalwin/Library/CodeRepo/AI/claude-plugins
claude plugin install sql-expert-dba@dalwin-local-plugins
```

（或会话内 `/plugin marketplace add <path>` + `/plugin install`。）

### 10.2 验证清单

- `plugin.json` / `marketplace.json` JSON 合法。
- 5 技能在 Claude 中可被发现（`/help` 或技能列表含 5 个 SQL 技能）。
- 给出「优化这条 SQL …」→ 触发 `sql-query-optimizer`，输出符合六段式契约。
- 给出报错全文 → 触发 `sql-error-diagnostician`，根因排序 + 修复路径。
- `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/memory_search.py"` 在插件环境可执行；seed 记忆可被检索。
- 显式「记下来」→ `memory_capture.py` 写入 `~/.claude/plugins/data/sql-expert-dba/memory/` 下 `approved`，`index.json` 更新。
- `python3 -m pytest`（或脚本自带 test runner）通过平移后的测试。
- 全局 memory 写入经去敏，不含真实表名/敏感字段。

---

## 11. 风险与降级

| 风险 | 缓解 |
|---|---|
| router 与专家技能在 Claude 下双触发/抢占 | 精修各 description 语义边界；router 强调「分诊/串联」，专家强调具体场景 |
| `${CLAUDE_PLUGIN_ROOT}` 在某些调用上下文未注入 | 脚本内 `paths.py` 做兜底（基于 `__file__` 解析插件根） |
| 运行时 memory 目录不可写 | `ensure_global_memory_dirs()` 先建目录；失败则降级为只读检索 + 提示 |
| v2 段落残留硬调用导致报错 | v1 明确移除 `./sql`/`biz_rules` 硬调用，仅留「延后」说明 |
| 平移测试断言仍指向 `~/.codex` 路径 | 测试改用 `SQL_EXPERT_DBA_MEMORY_DIR` 或 tmp 目录，不写死用户路径 |
| 知识双份漂移 | v2 引入与 Codex 版对账机制；v1 文档标注两份独立 |

---

## 12. 后续 v2

- 项目级 `./sql` 上下文索引与 `./sql/biz-rules` 移植（含 `project_context_*` / `biz_rules_*`）。
- 守护式自动沉淀：评估 Claude 插件级 hook（`Stop`/`PostToolUse`）复刻可行性与「本轮是否 SQL 任务」判定。
- 跨工具知识对账：Codex 与 Claude 两份 memory 的去重/合并/单源化策略。
- 视需要将工具中性核心提炼为共享单源（brainstorming 时的「共享单源核心」备选）。

---

## 13. 结论

Codex 与 Claude 插件结构同构，sql-expert-dba 的核心分析能力（5 技能 + 契约 + 全局 memory）可低成本 1:1 平移；唯一实质适配是**记忆触发改技能驱动**与**memory 路径改 Claude 侧**。v1 先交付核心 DBA 能力 + 知识沉淀，项目层与自动化留待 v2。
