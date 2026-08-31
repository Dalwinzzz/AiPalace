# sql-expert-dba 双版本能力对比

> 日期：2026-06-05
> 范围：Codex 版（`~/.agents/plugins/sql-expert-dba`，v1.1.0）vs Claude 版（`~/Library/CodeRepo/AI/claude-plugins/sql-expert-dba`，v1.1.0）
> 索引入口：`~/Documents/AI/plugins/codex-sql-expert-dba`、`~/Documents/AI/plugins/claude-sql-expert-dba`

---

## 相同能力（完全一致）

| 能力 | 说明 |
|------|------|
| **5 个专家 Skill** | `sql-expert-router`（分诊）、`sql-query-optimizer`（优化）、`sql-error-diagnostician`（报错诊断）、`sql-schema-reviewer`（DDL 评审）、`sql-report-query-builder`（业务 SQL 生成） |
| **_shared 四份契约**（dialect/missing-input 完全一致） | 方言指南（MySQL/PG/通用）、缺失输入检查表 |
| **全局 Memory 结构** | `glossary/`、`rules/`、`templates/`、`candidates/`、`cases/`，同 3 条 seed（glossary-001/rule-001/template-001） |
| **Memory 脚本全集** | `memory_capture.py`、`memory_index.py`、`memory_search.py`、`paths.py`、`_frontmatter.py` |
| **项目上下文（A）** | `project_context_index.py`、`project_context_search.py`——读 `./sql/` 生成 `.index/` |
| **业务规则沉淀（B）** | `biz_rules_capture.py`、`biz_rules_search.py`、`biz_rules_git_guard.py`——`./sql/biz-rules/` |
| **Assets** | `icon.svg`、`logo.svg` 完全相同 |
| **测试集（大部分）** | `test_memory.py`、`test_memory_v2.py`、`test_paths.py`、`test_project_context.py`、`test_biz_rules.py`、`test_skill_docs_v2.py` |

---

## 差异对比

### 1. Hook 机制（最核心差异）

| | Codex 版 | Claude 版 |
|--|----------|-----------|
| **Hook 触发方式** | Stop 事件，`--input ${PLUGIN_DATA}/last-context.json`（读结构化 JSON 文件） | Stop 事件，读 stdin（`session_id`/`transcript_path`/`stop_hook_active`）+ 读 transcript |
| **Hook 入口变量** | `${PLUGIN_ROOT}` | `${CLAUDE_PLUGIN_ROOT}` |
| **守护逻辑** | 依赖 Skill 写 `last-context.json` → Stop hook 消费 | Stop hook 主动读 transcript，通过正则门控判断是否为 SQL 任务 |
| **防循环** | 无（依赖上层能否正确写 JSON） | `stop_hook_active` 检测 + `capture-log.jsonl` session 幂等标记，整会话最多注入一次 |
| **Hook 配置位置** | `hooks/hooks.json`（`PLUGIN_ROOT` 变量）+ `plugin.json` 里 `"hooks"` 字段引用 | `hooks/hooks.json`（`CLAUDE_PLUGIN_ROOT` 变量）+ `plugin.json` **不**声明 hooks 字段（自动加载） |
| **守护效果** | 因 codex plugin_hooks 实验特性约束，实际可能不生效（README 有启用指南） | 经 `claude plugin validate` 验证通过，`claude plugin details` 确认 Stop hook 已挂载 |

### 2. 记忆沉淀策略（Skill 层行为差异）

| | Codex 版 | Claude 版 |
|--|----------|-----------|
| **收尾评估** | **强制表态**——每次 workflow 收尾必须在"记忆判定"段显式输出三选一（丢弃/candidate/approved），省略等于交付不完整 | **后台评估**——默认后台执行，不强制显式确认，可静默 |
| **Memory 检索** | **强制读取闭环**——分诊前必须先检索，命中 `approved` 必须在分诊结果中显式引用，命中 `candidate` 需标注待复审状态，未命中需说明 | 分诊前调用检索，有相关记忆则附带提示（弱约束） |
| **显式触发** | 硬触发——用户说"记下来"等词时不允许静默跳过，必须在"记忆判定"段说明结果 | 同样支持显式触发，但没有强制不可跳过的约束 |
| **增强路径冗余** | Skill 收尾时额外写 `${PLUGIN_DATA}/last-context.json` 供 Stop hook 消费（双路径兜底） | Stop hook 自己读 transcript，Skill 无需额外落盘 |
| **脚本调用写法** | 直接写脚本名（`memory_search.py`），路径由 `paths.py` 运行时解析 | 写 `${CLAUDE_PLUGIN_ROOT}/scripts/memory_search.py`（完整环境变量路径） |

### 3. 测试集差异

| | Codex 版 | Claude 版 |
|--|----------|-----------|
| `test_auto_memory_runner.py` | 测试"读 `last-context.json`"模式（结构化输入） | 测试 Stop hook 模式（stdin 读取、transcript 门控、幂等防循环，7 个 case） |
| `test_plugin_hooks_manifest.py` | 有（验证 `hooks/hooks.json` + `plugin.json` 的 hooks 字段结构） | 无 |

### 4. Memory 路径解析

| | Codex 版 | Claude 版 |
|--|----------|-----------|
| **全局 Memory 路径** | 通过 `SQL_EXPERT_DBA_MEMORY_DIR` 覆盖，或回退 `CODEX_HOME`/`~/.codex` | 通过 `SQL_EXPERT_DBA_MEMORY_DIR` 覆盖，默认 `~/.claude/plugins/data/sql-expert-dba/memory/` |

---

## 一句话总结

两个版本的**分析型 SQL 能力完全对称**（5 skill + 项目上下文 + 业务规则 + Memory 全套脚本），差异集中在**记忆自动沉淀的实现路径**上：Codex 版依赖 Skill 主动落盘 `last-context.json` + Stop hook 消费，Skill 层强制显式记忆判定输出；Claude 版 Stop hook 自主读 transcript 做门控，防循环更严格，但 Skill 层记忆评估为后台静默模式。两者各自适配了工具的 harness 设计哲学。
