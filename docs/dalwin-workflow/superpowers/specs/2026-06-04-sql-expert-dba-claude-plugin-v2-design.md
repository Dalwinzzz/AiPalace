# sql-expert-dba Claude 插件 v2 迭代设计 spec — 2026-06-04

> 范围：在已交付的 Claude 插件 v1（`1.0.0`：5 技能 + 4 契约 + 全局 memory）之上，补齐 spec §12 划定的三块 v2 能力——**A 项目级 `./sql` 上下文索引**、**B `./sql/biz-rules` 业务规则沉淀**、**C 守护式自动沉淀 hook**。跨工具知识对账（D）延后 v3。
>
> 决策来源：2026-06-04 brainstorming 四项关键决策（见 §2）。
>
> 官方规范核对：context7 `/anthropics/claude-code` —— 插件 hook 声明（`plugin.json` `hooks` 字段 + `hooks/hooks.json`）、hook 事件与 `type`（`command`/`prompt`）、prompt 型 hook 仅支持 `Stop`/`SubagentStop`/`UserPromptSubmit`/`PreToolUse`、Stop hook `decision:block`+`reason` 驱动模型继续、hook stdin 输入字段（`session_id`/`transcript_path`/`stop_hook_active`）、`${CLAUDE_PLUGIN_ROOT}`。
>
> 前序文档：v1 设计 `docs/superpowers/specs/2026-06-03-sql-expert-dba-claude-plugin-design.md`；v1 实施日志 `docs/superpowers/plans/logs/2026-06-03-sql-expert-dba-claude-plugin.md`。

---

## 1. 背景与目标

v1 已把 Codex 插件 `sql-expert-dba`（`1.1.0`）的**核心分析能力**迁移为独立 Claude 插件（`1.0.0`，已安装，46 tests OK），但将三块能力划入 v2 延后：项目级上下文、业务规则、守护式自动沉淀。本次 v2 迭代补齐这三块，使 Claude 插件能力对齐 Codex `1.1.0` 全集。

目标：

1. 平移 A/B 的 Codex 脚本与项目层结构，让插件在项目工作目录下能**索引 `./sql/` 上下文**、**沉淀 `./sql/biz-rules` 业务规则**。
2. 还原 v1 中性化为「v2 延后」的 5 技能 + `output-contract` 段落，使技能真正消费项目上下文与业务规则。
3. 以**契合 Claude hook 模型**的方式实现 C：守护式自动沉淀。不照搬 Codex 的 command 结构化输入，改为 **command 型 `Stop` hook + `decision:block` 条件化注入**。
4. 不改动 Codex 版插件；Claude 与 Codex 两份知识仍各自独立维护（对账留 v3）。

非目标（v2）：跨工具知识对账与单源化（D）；将工具中性核心提炼为共享单源。

---

## 2. 决策汇总（brainstorming 2026-06-04）

| # | 决策点 | 选择 | 依据 |
|---|---|---|---|
| 1 | v2 范围 | A 项目上下文 + B 业务规则 + **C 守护式自动沉淀 hook**；D 跨工具对账延后 v3 | A/B 平移确定性高；C 在 v1 已被技能驱动覆盖，本次补「守护」增强 |
| 2 | C 触发事件 | **`Stop`**（不用 `SessionEnd`） | 官方明确 prompt 型 hook 不支持 `SessionEnd`；`SessionEnd` 为清理类、不驱动模型 |
| 3 | C 实现机制 | **command 型 Stop hook + `decision:block`+`reason` 条件化注入**（非 prompt 型） | prompt 型 hook 无条件每次注入，无法「先判断是否 SQL 任务再决定注入」；command 型可做门控判断 |
| 4 | C 注入策略 | 仅当**本会话是 SQL 任务/触发过本插件、且未沉淀**时注入一次轻量提醒；否则零注入；幂等防循环 | 用户明确反对复杂任务下 `Stop` 多次触发的重复注入浪费 |

**贯穿原则**：v1 的「技能驱动沉淀」仍是写候选正文的**主路径**（每个 workflow 完成时就地写入）；C 的 hook 是**会话末兜底**，靠 `memory_capture.py` 内置去重避免与主路径重复。

---

## 3. v2 范围

**v2 包含：**

- **A 项目上下文**：平移 `project_context_index.py`、`project_context_search.py`（+ `test_project_context.py`）。
- **B 业务规则**：平移 `biz_rules_capture.py`、`biz_rules_search.py`、`biz_rules_git_guard.py`（+ `test_biz_rules.py`）。
- **C 守护式自动沉淀 hook**：新建 `hooks/hooks.json`（`Stop`/`command`）；`plugin.json` 加 `hooks` 字段；改造 `auto_memory_runner.py`（Codex command 结构化输入 → Claude Stop hook stdin + transcript + `decision` 输出 + 门控 + 幂等）（+ 改造 `test_auto_memory_runner.py`）。
- **技能文档还原**：5 技能 + `output-contract.md` 的 v2 段落还原（+ 平移 `test_skill_docs_v2.py` 作验收）。
- **清单升级**：`plugin.json` `1.0.0 → 1.1.0` + description 还原 v2 表述；`marketplace.json` description 更新。
- **顺手修正**：`memory-policy.md` 第 8 行 v1 残留的 `CODEX_HOME`/`~/.codex` 路径表述。

**v2 延后（v3）：**

- D 跨工具知识对账：Codex 与 Claude 两份 memory 的去重/合并/单源化。
- 工具中性核心的共享单源化。

---

## 4. 现状盘点

### 4.1 v1 已交付（Claude 插件 `1.0.0`）

- 5 技能（router + 4 专家）+ 4 共享契约。
- 全局 memory：`paths.py`、`_frontmatter.py`、`memory_search.py`、`memory_capture.py`、`memory_index.py` + 内置 seed。
- 测试：`test_paths.py`、`test_memory.py`、`test_memory_v2.py`。
- 本地 marketplace `dalwin-local-plugins` + `plugin.json`（`1.0.0`）。

### 4.2 v2 待补（Codex `1.1.0` 有、Claude `1.0.0` 无）

| 构件 | Codex 源 | v2 动作 |
|---|---|---|
| `project_context_index.py` / `project_context_search.py` | `scripts/` | 原样平移（依赖 `paths`，已就绪） |
| `biz_rules_capture.py` / `biz_rules_search.py` / `biz_rules_git_guard.py` | `scripts/` | 原样平移（依赖 `paths`/`_frontmatter`，已就绪） |
| `auto_memory_runner.py` | `scripts/` | **实质改造**为 Claude Stop hook command 脚本 |
| `test_project_context.py` / `test_biz_rules.py` | `scripts/` | 原样平移（tmp `--project-dir`） |
| `test_auto_memory_runner.py` | `scripts/` | 按 command 型 stdin/decision/幂等改造 |
| `test_skill_docs_v2.py` | `scripts/` | 原样平移，作技能文档还原验收 |
| 5 技能 + `output-contract` v2 段落 | `skills/` | 从 v1 中性化还原为 Codex 原版 v2 段落 |

### 4.3 关键省力事实

- **`paths.py` 的 v2 helper 已就绪**：v1 移植时已带入 `resolve_project_sql_dir()`、`resolve_biz_rules_dir()`、`ensure_global_memory_dirs()`（v2 嵌套布局）。A/B **无需再改 `paths.py`**。
- **A/B 脚本用项目级 `./sql` 路径**（不是插件包路径），无需 `${CLAUDE_PLUGIN_ROOT}` 适配，可近乎原样 `cp`。
- **A/B 脚本纯 Python stdlib**（B 另调用 `git` CLI），跨工具无差异。

---

## 5. 文件布局变更（SOT）

新增/改动（`~/Library/CodeRepo/AI/claude-plugins/sql-expert-dba/`）：

```
sql-expert-dba/
├── .claude-plugin/
│   └── plugin.json                       # 改：version 1.1.0 + description + 加 hooks 字段
├── hooks/
│   └── hooks.json                        # 新建：Stop / command / 指向 auto_memory_runner.py
├── skills/
│   ├── sql-expert-router/SKILL.md        # 改：还原 v2 项目上下文段
│   ├── sql-query-optimizer/SKILL.md      # 改：还原 v2 项目上下文段
│   ├── sql-error-diagnostician/SKILL.md  # 改：还原 v2 项目上下文段
│   ├── sql-schema-reviewer/SKILL.md      # 改：还原 v2 schema context + 业务规则沉淀段
│   ├── sql-report-query-builder/SKILL.md # 改：还原 v2 项目索引 + 口径冲突段
│   └── _shared/
│       ├── output-contract.md            # 改：还原 v2 可选子段落
│       └── memory-policy.md              # 改：修正第 8 行 Codex 路径残留
├── scripts/
│   ├── project_context_index.py          # 新建：平移
│   ├── project_context_search.py         # 新建：平移
│   ├── biz_rules_capture.py              # 新建：平移
│   ├── biz_rules_search.py               # 新建：平移
│   ├── biz_rules_git_guard.py            # 新建：平移
│   ├── auto_memory_runner.py             # 新建：改造为 Stop hook command 脚本
│   ├── test_project_context.py           # 新建：平移
│   ├── test_biz_rules.py                 # 新建：平移
│   ├── test_skill_docs_v2.py             # 新建：平移（验收）
│   └── test_auto_memory_runner.py        # 新建：改造
```

**运行时数据（不变）**：全局 memory `~/.claude/plugins/data/sql-expert-dba/memory/`；项目级 `./sql/.index/`、`./sql/biz-rules/`（跟随用户当前工作目录）。

---

## 6. A — 项目上下文索引设计

平移 `project_context_index.py`（核心）+ `project_context_search.py`（查询配套），原样保留逻辑：

- **入口**：`--rebuild`（默认）/ `--validate`，`--project-dir`（默认 `cwd`）。
- **扫描**：`./sql/` 下 `.sql/.ddl/.explain/.log/.txt/.md`；跳过 `biz-rules/`、点目录、symlink、二进制/乱码文件。
- **解析**：正则提取 `CREATE TABLE` 的列/类型/可空/主键/索引/外键（含内联 `REFERENCES`）；推断方言（mysql/postgresql/unknown）；按表名关联 EXPLAIN/慢 SQL 文件与特征（`using_filesort`、`full_table_scan` 等）。
- **产物**：`./sql/.index/{file-digests.json, context-index.json, table-index.json}`（`INDEX_VERSION=1`）。
- **校验**：`--validate` 比对 `file-digests` 与当前文件，报告 `unindexed_file`/`deleted_file`/`changed_file`，输出 `valid`/`stale`。
- **安全**：`.index/` 或索引文件为 symlink 时返回 `disabled`（防逃逸）。

**技能侧消费**：router 在分诊前检查 `./sql/` 是否存在并构建/校验索引；optimizer/diagnostician/schema-reviewer/report-builder 按表名从 `table-index.json` 定位 DDL/索引/EXPLAIN/慢 SQL 上下文（见 §9）。来自项目上下文的事实与用户输入分开标注，**不写入用户级全局 memory**。

---

## 7. B — 业务规则沉淀设计

平移 `biz_rules_capture.py`、`biz_rules_search.py`、`biz_rules_git_guard.py`，原样保留逻辑：

- **`capture.py`**：写 `./sql/biz-rules/{module}/{slug}.md`（YAML frontmatter）+ 重建 `table-index.json`/`module-index.json`。
  - `rule_type` 六类：`metric_definition`/`field_semantics`/`table_relationship`/`report_template`/`exclusion_rule`/`reconciliation_rule`。
  - **冲突检测**：同 `module` 同 `tables` 的 `metric_definition` 若 body 不同 → `conflict`（阻止覆盖，提示用户裁决）。
  - **去重**：相同 `(module, rule_type, tables, title)` 键 → `duplicate`。
  - **自动沉淀门槛**：`capture-mode ∈ {automatic, auto_hook, auto_automation}` 时校验上下文完整性（workspace/module/tables/source_workflow/body），缺失则 `skipped`。
- **`git_guard.py`**：默认把 `/sql/biz-rules/` 写入项目 `.gitignore`（`ensure_ignore`）；`--untrack` 可从 git 索引移除已跟踪文件；symlink 逃逸检测。
- **隐私取向**：业务规则**保留真实表名/字段名**（项目私有事实，保证项目内上下文保真），靠 git guard 默认不进 git 保护；这与「全局 memory 强制去敏」相反——两层隐私边界不同。

**技能侧消费**：report-builder 生成 SQL 前读 `biz-rules/{table,module}-index.json` 复用指标口径，命中口径冲突时停止并请用户裁决；schema-reviewer 评审确认稳定表关系/字段语义时沉淀到 `./sql/biz-rules/`（见 §9）。

---

## 8. C — 守护式自动沉淀 hook 设计（重点）

### 8.1 技术约束（context7 核实）

1. **prompt 型 hook 仅支持 `Stop`/`SubagentStop`/`UserPromptSubmit`/`PreToolUse`**，**不支持 `SessionEnd`**。故「`SessionEnd` 一次 + prompt 自动写」不可行。
2. prompt 型 hook 一旦挂 `Stop` 即**无条件每次注入**，无「先判断是否 SQL 任务再决定注入」的能力。
3. **command 型 Stop hook** 输出 `{"decision":"block","reason":"..."}` 会**阻止停止并把 `reason` 作为指令驱动模型继续**——可由脚本逻辑决定**是否**注入、注入**什么**，实现条件化。
4. hook stdin 通用输入：`session_id`、`transcript_path`、`cwd`、`permission_mode`、`hook_event_name`；Stop hook 触发的「继续」循环中 `stop_hook_active=true`（官方防循环字段）。

### 8.2 方案：command 型 Stop hook + `decision:block` 条件化注入

`hooks/hooks.json`：

```json
{
  "Stop": [
    {
      "matcher": ".*",
      "hooks": [
        {
          "type": "command",
          "command": "python3 ${CLAUDE_PLUGIN_ROOT}/scripts/auto_memory_runner.py",
          "timeout": 30
        }
      ]
    }
  ]
}
```

`plugin.json` 增加 `"hooks": "./hooks/hooks.json"`。

### 8.3 改造版 `auto_memory_runner.py` 流程

输入从 Codex 的 `--input <结构化 JSON file>` 改为 **读 stdin 的 Claude hook 输入**；输出从「capture 结果 JSON」改为 **Stop hook `decision` JSON**：

1. 从 stdin 读 hook 输入，解析 `session_id`、`transcript_path`、`stop_hook_active`。
2. **幂等短路**：若 `stop_hook_active` 为真，或 `capture-log.jsonl` 已有本 `session_id` 的 `stop-guard` 标记 → `exit 0` 静默（防重复注入与死循环）。
3. **门控判断**：读 `transcript_path`，判定本会话是否 SQL 任务——复用 `SQL_TASK_SIGNAL_RE`（SQL 关键字/错误码/中文 DBA 术语正则）命中，**或** transcript 中检测到本插件技能触发痕迹（`sql-expert-router`/`sql-query-optimizer` 等）。
4. **非 SQL 任务** → `exit 0` 静默，**零注入**。
5. **是 SQL 任务且未沉淀** → 向 `capture-log.jsonl` 追加 `{session_id, event:"stop-guard-prompted", ts}` 幂等标记，然后输出 `{"decision":"block","reason":"<轻量沉淀提醒>"}` 到 stdout，**仅一次**。

`<轻量沉淀提醒>` 草案：

> 本轮疑似 SQL Expert DBA 任务。若产生了**稳定、可复用**的经验/结论，且本轮尚未沉淀：请按 memory-policy 的 5 硬门槛（可复用/有证据/有边界/可结构化/可去敏）评估，全满足时先调 `${CLAUDE_PLUGIN_ROOT}/scripts/memory_search.py` 去重，再调 `${CLAUDE_PLUGIN_ROOT}/scripts/memory_capture.py --capture-mode auto_hook`（仅写 candidate）并**强制去敏**（不得含真实表名/字段，必要时 `--forbidden-token`）。若不值得沉淀或已沉淀，直接结束、不必额外输出。

### 8.4 关键性质

- **条件化**：门控由 command 脚本承担——非 SQL 会话**零 prompt 注入**，满足用户对重复注入浪费的反对。
- **保留自动写正文**：`reason` 驱动模型用完整上下文评估并自动写 candidate，质量高于 transcript 反解。
- **`auto_hook` 只落 candidate**：`memory_capture.py` 对 `capture-mode=auto_hook` 硬返回 `candidate`，绝不污染 `approved` 真源。
- **幂等防循环**：`stop_hook_active` + `capture-log` 本 session 标记，确保整会话最多注入一次。
- **主/兜底分工**：技能驱动沉淀仍为主路径；hook 仅在「是 SQL 任务但漏沉淀」时补一次提醒。

### 8.5 不采用方案与理由

| 方案 | 否决理由 |
|---|---|
| prompt 型 Stop hook | 无条件每次注入，复杂任务多次触发浪费，无法条件化 |
| `SessionEnd` + prompt | 官方不支持 prompt 型 `SessionEnd` |
| `SessionEnd` + command 启发式写正文 | 会话已终止不驱动模型；从 transcript 反解结构化候选脏数据风险高 |
| `UserPromptSubmit` + prompt | 每次用户输入都注入，更频繁；沉淀延迟到下一轮 |

### 8.6 风险与降级

- `decision:block`+`reason` 驱动模型执行沉淀（含调工具）的确切行为、`stop_hook_active`/`capture-log` 幂等的可靠性，**实施时实测验证**。
- 若 `block` 多触发一轮的开销不可接受 → 降级为 `reason` 仅提示、不强制（模型可忽略）。
- 若门控误判（非 SQL 会话被注入）→ 收紧 `SQL_TASK_SIGNAL_RE` 或要求「同时命中技能触发痕迹」。

---

## 9. 技能文档还原与验收

### 9.1 还原内容

将 v1 中性化为「v2 延后」的段落**还原为 Codex 原版 v2 段落**（脚本路径用 `${CLAUDE_PLUGIN_ROOT}/scripts/`）：

- **`sql-expert-router`**：还原「v2 项目上下文发现」——分诊前检查 `./sql/`、构建/校验 `./sql/.index/`、按 primary_workflow 决定是否加载 `./sql/biz-rules/`。
- **`sql-query-optimizer`**：还原「优先用项目 `table-index.json` 定位 DDL/索引/慢 SQL/EXPLAIN」，项目事实与用户输入分开标注。
- **`sql-error-diagnostician`**：还原「用 `./sql/.index/` 与 `./sql/biz-rules/` 定位表/字段/约束/错误码映射」，项目命中项标注来源、不写全局 memory。
- **`sql-schema-reviewer`**：还原「对照现有 `./sql/` schema context 检查冲突」+「v2 项目业务规则沉淀到 `./sql/biz-rules/`（保留真实表名字段）」。
- **`sql-report-query-builder`**：还原「读 `./sql/.index/table-index.json` 与 `biz-rules/{table,module}-index.json` 复用口径，口径冲突时停止并请用户裁决」。
- **`output-contract.md`**：还原可选子段落「使用的项目上下文」「命中的业务规则」「沉淀结果」，且明确**不得作为第 7 个顶层段落**（不破坏六段式）。

### 9.2 验收红线 = `test_skill_docs_v2.py`

平移该测试，断言（节选）：

- router 含 `./sql/.index/`、`biz-rules`。
- report-builder 含 `如当前项目存在`、`./sql/.index/table-index.json`、`biz-rules/table-index.json`、`口径冲突`。
- schema-reviewer 含 `现有 ./sql/ schema context`、`全局 memory 沉淀必须去敏`、`项目业务规则沉淀保持真实表名和字段名`。
- `memory-policy.md` 含 `用户级全局 memory`、`./sql/biz-rules/`、`自动沉淀只写 candidates`。
- `output-contract.md` 含 `使用的项目上下文`、`命中的业务规则`、`沉淀结果`、`不得作为第 7 个顶层段落`。
- 所有 `sql-*/SKILL.md` **不含** `可直接 approved`、`candidate 或 approved`。

还原以该测试 RED→GREEN 驱动。

---

## 10. paths.py 现状与 memory-policy 残留修正

- **`paths.py`**：v2 helper 已就绪（§4.3），**本次不改**。
- **`memory-policy.md` 第 8 行修正**：当前残留「全局 memory 通过 `SQL_EXPERT_DBA_MEMORY_DIR`、`CODEX_HOME` 或 `~/.codex` 解析」——与 v1 已改的 `paths.py`（删除 `CODEX_HOME`/`~/.codex`、默认 `~/.claude/plugins/data/sql-expert-dba/memory/`）不一致。改为：「全局 memory 通过 `SQL_EXPERT_DBA_MEMORY_DIR` 覆盖，默认 `~/.claude/plugins/data/sql-expert-dba/memory/`，不允许写死用户绝对路径。」该句不在 `test_skill_docs_v2` 断言内，修正不破坏测试。

---

## 11. 清单文件变更

### 11.1 `plugin.json`

- `version`：`1.0.0 → 1.1.0`。
- `description`：还原 v2 能力表述（项目级 `./sql` 上下文索引、`./sql/biz-rules` 业务规则、守护式自动沉淀；仍声明不直连数据库、不执行 SQL）。
- 新增 `"hooks": "./hooks/hooks.json"`。
- skills 仍由 `skills/` 自动发现，无需登记。

### 11.2 `marketplace.json`

- `plugins[0].description` 更新，提示 v2 增项目上下文/业务规则/守护式沉淀。
- 既有 `owner` 字段（v1 修正所加）保留。

---

## 12. 测试与验收清单

### 12.1 单元测试

- **平移**：`test_project_context.py`、`test_biz_rules.py`、`test_skill_docs_v2.py`（tmp `--project-dir` / `SKILLS_DIR` 相对路径，不依赖用户级路径）。
- **改造**：`test_auto_memory_runner.py`——覆盖 stdin hook 输入解析、非 SQL 静默（零注入）、SQL 任务未沉淀→`decision:block`、`stop_hook_active`/已沉淀→静默（幂等）。
- **全量回归**：`python3 -m unittest test_paths test_memory test_memory_v2 test_project_context test_biz_rules test_skill_docs_v2 test_auto_memory_runner`，期望 `OK`。

### 12.2 冒烟（人工/脚本）

- `project_context_index.py --rebuild` 在含 `./sql/*.sql` 的临时项目生成 `.index/` 三文件；`--validate` 报告一致。
- `biz_rules_capture.py` 写入 `./sql/biz-rules/{module}/*.md` 且 `/sql/biz-rules/` 自动进 `.gitignore`。
- `plugin.json`/`marketplace.json`/`hooks.json` JSON 合法。
- 插件重装后 `claude plugin details` 显示 5 技能 + Hooks 1（Stop）。
- SQL 会话末触发 hook → 条件注入沉淀提醒；非 SQL 会话 → 零注入（实测 §8.6）。

### 12.3 实施日志

`docs/superpowers/plans/logs/2026-06-04-sql-expert-dba-claude-plugin-v2.md`，记录成果、范围、适配点、实测验证结果与对账提醒。

---

## 13. 风险与降级

| 风险 | 缓解 |
|---|---|
| `decision:block` 驱动模型沉淀的行为与 v1 假设不符 | 实施时按官方 hook 文档 + 实测验证；不符则降级为 reason 仅提示 |
| hook 幂等失效导致重复注入/死循环 | `stop_hook_active` + `capture-log` 本 session 标记双保险；测试覆盖幂等分支 |
| 门控误判（非 SQL 会话被注入） | 收紧 `SQL_TASK_SIGNAL_RE`，必要时要求同时命中技能触发痕迹 |
| 还原段落引用脚本裸名导致运行错误 | 统一改 `${CLAUDE_PLUGIN_ROOT}/scripts/`；`test_skill_docs_v2` + grep 校验 |
| `search` 脚本依赖未带入 | 实施 Task 内先核对 `project_context_search.py`/`biz_rules_search.py` 的 import，仅依赖 `paths`/`_frontmatter`（已就绪） |
| 业务规则误入 git | `git_guard.ensure_ignore` 默认写 `.gitignore`；`capture` 落盘后即调用 |
| 知识双份漂移 | v2 文档标注两份独立；对账机制留 v3 |

---

## 14. v3 延后（D 跨工具对账）

- Codex 与 Claude 两份 memory 的去重/合并/单源化策略。
- 工具中性核心提炼为共享单源的可行性。
- 触发条件：两份知识量增长到手动对齐成本不可接受时启动。

---

## 15. 结论

v2 三块能力中，A/B 是低风险平移（脚本纯 stdlib、`paths.py` 已就绪、用项目级路径），技能文档还原有 `test_skill_docs_v2` 明确红线；唯一实质设计是 C——受「prompt 型 hook 不支持 `SessionEnd`」与「prompt 型无法条件化」两条硬约束，最终落到 **command 型 `Stop` hook + `decision:block` 条件化注入 + 幂等**：非 SQL 会话零注入、SQL 会话末补一次轻量沉淀提醒，技能驱动沉淀仍为主路径。跨工具对账留 v3。
