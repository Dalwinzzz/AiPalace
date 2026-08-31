# sql-expert-dba 双版本迭代 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 sql-expert-dba 双版本（Codex + Claude）从「各自分化」收敛为「求同存异」——移除 Stop hook 机制、统一记忆读写措辞为「仅产出可见/命中才可见」、新增 sanitize.py 去敏硬化、memory_promote.py 晋升出口、check_dual_sync.py 零差校验脚本。

**Architecture:** 5 个 SKILL.md 主文档两版逐字一致；工具 harness 差异（脚本调用写法、路径解析）隔离到 `_shared/memory-policy.codex.md` / `memory-policy.claude.md` 分片，TOOL-VARIANT 标记替代差异行。sanitize.py 作为独立模块被 memory_capture.py 和 memory_promote.py 复用，不改变 capture 外部接口。

**Tech Stack:** Python 3.11+（标准库）、unittest、正则 re 模块、pathlib、argparse；两版插件均已 Python 3；无第三方依赖。

---

## 文件结构

### 删除

| 路径（Codex 版 `~/.agents/plugins/sql-expert-dba/`） | 操作 |
|------|------|
| `hooks/hooks.json` | 删除 |
| `scripts/auto_memory_runner.py` | 删除 |
| `scripts/test_auto_memory_runner.py` | 删除 |
| `scripts/test_plugin_hooks_manifest.py` | 删除（Codex 独有） |

| 路径（Claude 版 `~/Library/CodeRepo/AI/claude-plugins/sql-expert-dba/`） | 操作 |
|------|------|
| `hooks/hooks.json` | 删除 |
| `scripts/auto_memory_runner.py` | 删除 |
| `scripts/test_auto_memory_runner.py` | 删除 |

### 新建

| 路径（两版对称，仅列 Codex 版） | 职责 |
|------|------|
| `skills/_shared/memory-policy.codex.md` | Codex 差异分片：裸名脚本调用 + `~/.codex/memories` 路径 |
| `skills/_shared/memory-policy.claude.md` | Claude 差异分片：全路径脚本调用 + `~/.claude/plugins/data` 路径 |
| `scripts/sanitize.py` | 默认敏感模式扫描（手机/邮件/身份证/IP）；硬拦截写入 |
| `scripts/memory_promote.py` | candidate→approved 晋升出口；`--list-candidates` / `--id` |
| `scripts/check_dual_sync.py` | 两版 zero-diff 校验 + 分片文件集合校验 |

### 修改

| 路径 | 改动摘要 |
|------|---------|
| `.codex-plugin/plugin.json` | 删除 `"hooks"` 字段；更新 description 删除 hook 增强路径描述 |
| `skills/_shared/memory-policy.md` | 重写「收尾评估流程」段为静默措辞；删除「增强路径落盘指示」段；脚本调用行换为 TOOL-VARIANT 标记 |
| `skills/_shared/output-contract.md` | 第 7 段「记忆判定（必填，三选一）」→「沉淀结果（仅写入时输出）」；删除 last-context.json / Stop hook 说明；硬约束 #6 更新 |
| `skills/sql-expert-router/SKILL.md` | Memory 检索段改为「命中才可见」措辞；脚本调用换 TOOL-VARIANT 标记 |
| `skills/sql-query-optimizer/SKILL.md` | 「后台记忆评估」段改为统一新措辞；脚本调用换 TOOL-VARIANT 标记 |
| `skills/sql-error-diagnostician/SKILL.md` | 同上 |
| `skills/sql-schema-reviewer/SKILL.md` | 同上 |
| `skills/sql-report-query-builder/SKILL.md` | 同上 |
| `scripts/paths.py` | `resolve_user_memory_dir` 上方加注释（真源位置 + 重装不丢 + env 覆盖） |
| `README.md` | 删除「启用增强路径」段；新增「记忆真源位置与重装不丢」和「Skill 执行层为唯一沉淀真源」 |
| `scripts/memory_capture.py` | `contains_forbidden_tokens` → 委托 `sanitize.check()`；新增 `--allow-token` 参数 |
| `scripts/test_skill_docs_v2.py` | 新增 4 个断言：TOOL-VARIANT 标记存在、新记忆措辞存在、旧措辞不存在 |

> **所有修改同时应用到 Claude 版**（`~/Library/CodeRepo/AI/claude-plugins/sql-expert-dba/`），两版 SKILL.md / `_shared` 主文档结果逐字一致。

---

## Task 1: 删除 Stop hook 文件（两版对称）

**Files:**
- Delete: `~/.agents/plugins/sql-expert-dba/hooks/hooks.json`
- Delete: `~/.agents/plugins/sql-expert-dba/scripts/auto_memory_runner.py`
- Delete: `~/.agents/plugins/sql-expert-dba/scripts/test_auto_memory_runner.py`
- Delete: `~/.agents/plugins/sql-expert-dba/scripts/test_plugin_hooks_manifest.py`
- Delete: `~/Library/CodeRepo/AI/claude-plugins/sql-expert-dba/hooks/hooks.json`
- Delete: `~/Library/CodeRepo/AI/claude-plugins/sql-expert-dba/scripts/auto_memory_runner.py`
- Delete: `~/Library/CodeRepo/AI/claude-plugins/sql-expert-dba/scripts/test_auto_memory_runner.py`
- Modify: `~/.agents/plugins/sql-expert-dba/.codex-plugin/plugin.json`

- [ ] **Step 1: 验证待删文件存在**

```bash
ls ~/.agents/plugins/sql-expert-dba/hooks/hooks.json
ls ~/.agents/plugins/sql-expert-dba/scripts/auto_memory_runner.py
ls ~/.agents/plugins/sql-expert-dba/scripts/test_auto_memory_runner.py
ls ~/.agents/plugins/sql-expert-dba/scripts/test_plugin_hooks_manifest.py
ls ~/Library/CodeRepo/AI/claude-plugins/sql-expert-dba/hooks/hooks.json
ls ~/Library/CodeRepo/AI/claude-plugins/sql-expert-dba/scripts/auto_memory_runner.py
ls ~/Library/CodeRepo/AI/claude-plugins/sql-expert-dba/scripts/test_auto_memory_runner.py
```

期望：所有路径均存在，无 No such file 报错。

- [ ] **Step 2: 删除 Codex 版 hook 相关文件**

```bash
rm ~/.agents/plugins/sql-expert-dba/hooks/hooks.json
rm ~/.agents/plugins/sql-expert-dba/scripts/auto_memory_runner.py
rm ~/.agents/plugins/sql-expert-dba/scripts/test_auto_memory_runner.py
rm ~/.agents/plugins/sql-expert-dba/scripts/test_plugin_hooks_manifest.py
rmdir ~/.agents/plugins/sql-expert-dba/hooks 2>/dev/null || true
```

- [ ] **Step 3: 删除 Claude 版 hook 相关文件**

```bash
rm ~/Library/CodeRepo/AI/claude-plugins/sql-expert-dba/hooks/hooks.json
rm ~/Library/CodeRepo/AI/claude-plugins/sql-expert-dba/scripts/auto_memory_runner.py
rm ~/Library/CodeRepo/AI/claude-plugins/sql-expert-dba/scripts/test_auto_memory_runner.py
rmdir ~/Library/CodeRepo/AI/claude-plugins/sql-expert-dba/hooks 2>/dev/null || true
```

- [ ] **Step 4: 从 plugin.json 移除 hooks 字段并更新 description**

编辑 `~/.agents/plugins/sql-expert-dba/.codex-plugin/plugin.json`：

将 `"hooks": "./hooks/hooks.json",` 这一行删除。

将 `"description"` 字段中的增强路径说明删除，改为：

```json
{
  "name": "sql-expert-dba",
  "version": "1.1.0",
  "description": "面向 MySQL/PostgreSQL 与通用 SQL 场景的分析型 DBA 助手，支持查询优化、报错诊断、Schema 评审、业务报表 SQL 生成、便携式全局 SQL memory、显式记忆沉淀（用户说\"记下来\"或 workflow 收尾自评估写入时落库；Skill 执行层为唯一沉淀真源）、项目级 ./sql 上下文索引，以及 ./sql/biz-rules/ 业务规则沉淀。插件会读取当前工作目录 ./sql/ 下的 .sql/.ddl/.explain/.log/.txt/.md 文件，提取 DDL、schema dump、EXPLAIN、慢 SQL 和说明文档信息并生成 ./sql/.index/；不直连数据库、不执行 SQL。",
  "author": {
    "name": "dalwin",
    "url": ""
  },
  "license": "MIT",
  "keywords": [
    "sql",
    "mysql",
    "postgresql",
    "query-optimization",
    "schema-review",
    "reporting-sql",
    "dba"
  ],
  "skills": "./skills/",
  "interface": {
    "displayName": "SQL Expert DBA",
    "shortDescription": "SQL 优化、报错定位、DDL 评审、业务 SQL 生成与 ./sql 项目上下文助手",
    "longDescription": "面向 MySQL/PostgreSQL 与通用 SQL 场景的分析型 DBA 助手。v1.1.0 增加便携式全局 SQL memory、项目级 ./sql 上下文索引，以及 ./sql/biz-rules/ 业务规则沉淀。记忆沉淀以 Skill 执行层为唯一真源：用户说\"记下来/值得沉淀/帮我复盘\"或 workflow 收尾自评估通过时，由 skill 直接调用 memory_capture.py 落库到用户级全局目录。插件会读取当前工作目录 ./sql/ 下的 .sql/.ddl/.explain/.log/.txt/.md 文件，提取 DDL、schema dump、EXPLAIN、慢 SQL 和说明文档信息并生成 ./sql/.index/；业务规则写入 ./sql/biz-rules/ 并维护 table/module 索引；插件不直连数据库、不执行 SQL。",
    "developerName": "dalwin",
    "category": "Programming",
    "capabilities": [
      "Interactive",
      "Read"
    ],
    "defaultPrompt": [
      "优化这条 SQL，并指出性能瓶颈和索引建议",
      "解释这段 SQL 报错，并给出最可能的修复方案",
      "根据业务需求和表结构生成统计 SQL，再帮我检查口径"
    ],
    "brandColor": "#336791",
    "composerIcon": "./assets/icon.svg",
    "logo": "./assets/logo.svg",
    "screenshots": []
  }
}
```

- [ ] **Step 5: 验证 plugin.json 无 hooks 字段**

```bash
grep -c '"hooks"' ~/.agents/plugins/sql-expert-dba/.codex-plugin/plugin.json
```

期望输出：`0`

- [ ] **Step 6: 验证被删文件不存在**

```bash
ls ~/.agents/plugins/sql-expert-dba/hooks/ 2>&1 | grep -q "No such" && echo "OK: hooks/ removed" || echo "FAIL: hooks/ still exists"
ls ~/.agents/plugins/sql-expert-dba/scripts/auto_memory_runner.py 2>&1 | grep -q "No such" && echo "OK" || echo "FAIL"
ls ~/Library/CodeRepo/AI/claude-plugins/sql-expert-dba/hooks/ 2>&1 | grep -q "No such" && echo "OK: claude hooks/ removed" || echo "FAIL"
```

期望：三行均输出 OK。

- [ ] **Step 7: Commit**

```bash
cd ~/.agents/plugins/sql-expert-dba
git add -A
git commit -m "chore: remove stop hook mechanism (hooks/, auto_memory_runner, test files)"
cd ~/Library/CodeRepo/AI/claude-plugins/sql-expert-dba
git add -A
git commit -m "chore: remove stop hook mechanism (hooks/, auto_memory_runner, test files)"
```

---

## Task 2: 新建 _shared/ 分片文件（两版对称）

**Files:**
- Create: `~/.agents/plugins/sql-expert-dba/skills/_shared/memory-policy.codex.md`
- Create: `~/.agents/plugins/sql-expert-dba/skills/_shared/memory-policy.claude.md`
- Create: `~/Library/CodeRepo/AI/claude-plugins/sql-expert-dba/skills/_shared/memory-policy.codex.md`
- Create: `~/Library/CodeRepo/AI/claude-plugins/sql-expert-dba/skills/_shared/memory-policy.claude.md`

- [ ] **Step 1: 写失败测试**

在 `~/.agents/plugins/sql-expert-dba/scripts/test_skill_docs_v2.py` 末尾追加（暂不运行）：

```python
def test_shared_shard_files_exist(self):
    shared = SKILLS_DIR / "_shared"
    self.assertTrue((shared / "memory-policy.codex.md").exists(),
                    "memory-policy.codex.md missing")
    self.assertTrue((shared / "memory-policy.claude.md").exists(),
                    "memory-policy.claude.md missing")
```

- [ ] **Step 2: 运行测试，确认失败**

```bash
cd ~/.agents/plugins/sql-expert-dba
python3 -m pytest scripts/test_skill_docs_v2.py::TestSkillDocsV2::test_shared_shard_files_exist -v
```

期望：FAIL — `memory-policy.codex.md missing`

- [ ] **Step 3: 创建 memory-policy.codex.md（两版内容相同）**

`~/.agents/plugins/sql-expert-dba/skills/_shared/memory-policy.codex.md`：

```markdown
# 记忆策略 — Codex 版工具差异分片

> **依据来源**：Codex 官方文档约定：脚本以裸名调用，路径由 `paths.py` 运行时解析；
> 全局 memory 落点 `CODEX_HOME/memories/sql-expert-dba/` 或 `~/.codex/memories/sql-expert-dba/`。
> 本分片仅记录 Codex harness 相关差异，公共策略规则见 [memory-policy.md](memory-policy.md)。

## Codex 版脚本调用约定

| 时机 | 调用方式 | 目的 |
|------|---------|------|
| workflow 开始前 | `memory_search.py --memory-dir <resolved>` | 查找相关已有记忆 |
| 主任务完成后（有写入时） | `memory_capture.py --memory-dir <resolved> --capture-mode explicit_user_requested ...` | 写入 candidate / approved |
| candidate 复审晋升 | `memory_promote.py --memory-dir <resolved> --id <memory-id>` | 将指定 candidate 晋升为 approved |
| 维护时 | `memory_index.py --memory-dir <resolved>` | 重建或校验索引一致性 |

脚本以裸名调用（由 PATH 或调用方解析），`--memory-dir` 由 `paths.py::resolve_user_memory_dir()` 在运行时决定，优先级：`SQL_EXPERT_DBA_MEMORY_DIR` > `CODEX_HOME/memories/sql-expert-dba` > `~/.codex/memories/sql-expert-dba`。

## Codex 版全局 memory 落点

- 默认：`~/.codex/memories/sql-expert-dba/`
- 覆盖：`$SQL_EXPERT_DBA_MEMORY_DIR`（绝对路径或 `~` 展开路径）
- 备用：`$CODEX_HOME/memories/sql-expert-dba/`（若设置了 CODEX_HOME）

该目录与插件源码物理分离，插件重装/升级不影响已沉淀记忆。
```

- [ ] **Step 4: 创建 memory-policy.claude.md（两版内容相同）**

`~/.agents/plugins/sql-expert-dba/skills/_shared/memory-policy.claude.md`：

```markdown
# 记忆策略 — Claude 版工具差异分片

> **依据来源**：Claude Agent SDK 官方文档约定：脚本以 `${CLAUDE_PLUGIN_ROOT}/scripts/...` 全路径调用；
> 全局 memory 落点 `~/.claude/plugins/data/sql-expert-dba/memory/`（Claude 官方插件 data 区）。
> 本分片仅记录 Claude harness 相关差异，公共策略规则见 [memory-policy.md](memory-policy.md)。

## Claude 版脚本调用约定

| 时机 | 调用方式 | 目的 |
|------|---------|------|
| workflow 开始前 | `${CLAUDE_PLUGIN_ROOT}/scripts/memory_search.py --memory-dir <resolved>` | 查找相关已有记忆 |
| 主任务完成后（有写入时） | `${CLAUDE_PLUGIN_ROOT}/scripts/memory_capture.py --memory-dir <resolved> --capture-mode explicit_user_requested ...` | 写入 candidate / approved |
| candidate 复审晋升 | `${CLAUDE_PLUGIN_ROOT}/scripts/memory_promote.py --memory-dir <resolved> --id <memory-id>` | 将指定 candidate 晋升为 approved |
| 维护时 | `${CLAUDE_PLUGIN_ROOT}/scripts/memory_index.py --memory-dir <resolved>` | 重建或校验索引一致性 |

`--memory-dir` 由 `paths.py::resolve_user_memory_dir()` 在运行时决定，优先级：`SQL_EXPERT_DBA_MEMORY_DIR` > `~/.claude/plugins/data/sql-expert-dba/memory/`。

## Claude 版全局 memory 落点

- 默认：`~/.claude/plugins/data/sql-expert-dba/memory/`（Claude 官方插件 data 区）
- 覆盖：`$SQL_EXPERT_DBA_MEMORY_DIR`（绝对路径或 `~` 展开路径）

该目录与插件源码物理分离，插件重装/升级不影响已沉淀记忆。
```

- [ ] **Step 5: 复制分片到 Claude 版**

```bash
cp ~/.agents/plugins/sql-expert-dba/skills/_shared/memory-policy.codex.md \
   ~/Library/CodeRepo/AI/claude-plugins/sql-expert-dba/skills/_shared/memory-policy.codex.md
cp ~/.agents/plugins/sql-expert-dba/skills/_shared/memory-policy.claude.md \
   ~/Library/CodeRepo/AI/claude-plugins/sql-expert-dba/skills/_shared/memory-policy.claude.md
```

- [ ] **Step 6: 运行测试，确认通过**

```bash
cd ~/.agents/plugins/sql-expert-dba
python3 -m pytest scripts/test_skill_docs_v2.py::TestSkillDocsV2::test_shared_shard_files_exist -v
```

期望：PASSED

- [ ] **Step 7: Commit**

```bash
cd ~/.agents/plugins/sql-expert-dba
git add skills/_shared/memory-policy.codex.md skills/_shared/memory-policy.claude.md scripts/test_skill_docs_v2.py
git commit -m "feat: add _shared/ variant shards for codex/claude tool differences"
cd ~/Library/CodeRepo/AI/claude-plugins/sql-expert-dba
git add skills/_shared/memory-policy.codex.md skills/_shared/memory-policy.claude.md
git commit -m "feat: add _shared/ variant shards for codex/claude tool differences"
```

---

## Task 3: 重写 memory-policy.md 主文档

**Files:**
- Modify: `~/.agents/plugins/sql-expert-dba/skills/_shared/memory-policy.md`
- Modify: `~/Library/CodeRepo/AI/claude-plugins/sql-expert-dba/skills/_shared/memory-policy.md`

目标：删除「增强路径落盘指示」段；「收尾评估流程（强制表态）」→「收尾记忆自评估（强制动作，静默执行）」统一措辞；脚本调用表换为 TOOL-VARIANT 标记。

- [ ] **Step 1: 写失败测试**

在 `test_skill_docs_v2.py` 追加：

```python
def test_memory_policy_unified_wording(self):
    policy = SKILLS_DIR / "_shared" / "memory-policy.md"
    content = policy.read_text(encoding="utf-8")
    # 新措辞必须存在
    self.assertIn("收尾记忆自评估（强制动作，静默执行）", content)
    self.assertIn("📌 已沉淀：", content)
    self.assertIn("TOOL-VARIANT: memory-policy", content)
    # 旧措辞必须不存在
    self.assertNotIn("收尾评估流程（强制表态）", content)
    self.assertNotIn("增强路径落盘指示", content)
    self.assertNotIn("last-context.json", content)
```

- [ ] **Step 2: 运行测试，确认失败**

```bash
cd ~/.agents/plugins/sql-expert-dba
python3 -m pytest scripts/test_skill_docs_v2.py::TestSkillDocsV2::test_memory_policy_unified_wording -v
```

期望：FAIL

- [ ] **Step 3: 重写 memory-policy.md**

将 `~/.agents/plugins/sql-expert-dba/skills/_shared/memory-policy.md` 全文替换为：

```markdown
# 记忆策略

本文件定义 SQL Expert DBA 插件的 memory 系统写入和读取规则。所有 workflow 必须遵守。

## v2 存储分层

- 插件内置 `memory/` 只作为 seed memory，不作为运行时沉淀真源。
- 用户级全局 memory 通过 `SQL_EXPERT_DBA_MEMORY_DIR`、`CODEX_HOME` 或 `~/.codex` 解析，不允许写死用户绝对路径。
- 项目级业务规则写入当前工作目录 `./sql/biz-rules/`。
- 全局 memory 必须去敏和抽象化，不得保留真实表名、字段名、租户标识、私有指标名或原始业务数据。
- 项目级 `./sql/` 与 `./sql/biz-rules/` 可以保留真实表名、字段名和业务口径，以保证项目内上下文保真。
- 自动沉淀只写 candidates；显式沉淀通过校验后可写 approved。

## 硬约束

memory/ 系统 **只允许** 沉淀以下内容：

1. 结构化结论（规则、案例卡片、模板、术语定义）
2. 经过去敏处理的可复用知识

memory/ 系统 **严禁** 沉淀以下内容：

1. 原始长对话
2. 未经验证的猜测
3. 无法去敏的业务细节（真实表名、真实数据、敏感字段值）
4. 纯一次性临时查询上下文
5. 口径不清或有争议的业务定义

## 收尾记忆自评估（强制动作，静默执行）

每个 workflow 完成主任务后，**必须**执行一次记忆自评估（此动作不可省略）。评估过程、以及「判定丢弃 / 不满足门槛」的结果，**一律静默，不输出任何过程性内容**。

**仅当**评估通过 5 硬门槛、实际写入了 candidate 或 approved 时，才在交付末尾输出一行**沉淀结果**：

```
📌 已沉淀：<title>（<type>，<review_status>）→ <相对路径>
```

未写入任何内容时，**不输出**该行，也不解释为何不沉淀。

### 7 步评估流程（静默执行）

1. **确认主输出已交付** — 核心交付物已输出
2. **价值评估** — 判断本次交互是否产生了可复用知识
3. **结构化归一** — 将候选知识转化为标准 YAML front matter 格式
4. **去敏** — 移除真实业务数据、表名（如需）、敏感字段

<!-- TOOL-VARIANT: memory-policy -->
> 工具相关的脚本调用与路径解析见对应分片：
> Codex → memory-policy.codex.md ｜ Claude → memory-policy.claude.md

5. **去重** — 调用 `memory_search.py` 检查是否已有高度相似的记忆
6. **写入** — 自动沉淀只写 `candidate`；显式沉淀通过校验后可写 `approved`
7. **更新索引** — 由 `memory_capture.py` 自动完成

### 评估结果只有三种

| 结果 | 含义 | 可见性 |
|------|------|--------|
| 丢弃 | 不满足沉淀门槛，不写入任何内容 | 静默 |
| 写入 `candidate` | 有价值但需人工复审 | 输出 `📌 已沉淀` 行 |
| 写入 `approved` | 高置信度、高通用性，经校验后直接消费 | 输出 `📌 已沉淀` 行 |

## 沉淀判定标准

### 5 个硬门槛（必须全部满足）

1. **可复用** — 对未来类似问题有参考价值
2. **有证据** — 基于实际分析结论，不是纯推测
3. **有边界** — 明确适用条件和不适用条件
4. **可结构化** — 可转化为标准字段格式
5. **可去敏** — 可移除敏感业务信息而不丧失核心价值

### 5 个优先级信号（提升沉淀优先级）

1. 高频问题 — 多次遇到的相同模式
2. 非直觉陷阱 — 违反直觉的行为差异
3. 跨方言差异 — MySQL vs PostgreSQL 关键差异点
4. 报表统计口径模板 — 可复用的业务 SQL 模式
5. 节省排查时间 — 明显减少未来调试时间的经验

## 正式入库规则

默认只消费 `approved` 状态的记忆。

### 显式校验后可 `approved` 的条目

- 高通用性规则（如"避免 SELECT *"）
- 稳定错误模式（如"ERROR 1062 → 唯一键冲突"）
- 高复用模板（如"日统计报表基础模板"）
- 边界清晰的跨方言规则
- 通用索引/优化规则

### 必须先进 `candidate` 的条目

- 与特定业务场景强相关的案例
- 边界不完全清晰的经验
- 置信度为 medium 或 low 的结论
- 首次出现的新模式

## 显式沉淀模式（硬触发）

当用户明确说出以下关键词时，切换为显式沉淀模式：

- "这个值得沉淀"
- "帮我复盘"
- "记下来"
- "保存这个经验"

**用户说出这些词时，执行显式沉淀流程是强制动作，不是可选项。** 不允许以"本轮无明显新知识"为由静默跳过——如无实质内容，则「判定丢弃」时照常静默，不要额外解释。

显式模式下：
1. 将沉淀过程展示给用户
2. 输出结构化沉淀结果
3. 统一使用 `--capture-mode explicit_user_requested` 调用 `memory_capture.py`：优先尝试 `approved`（经显式校验通过），未完成校验时回退 `candidate`

## 晋升流程（candidate → approved）

candidate 沉淀后，可通过以下方式晋升至 approved：

- 用户说「复审记忆」「把这条转正」「晋升这条记忆」时，router 引导调用晋升流程
- 晋升脚本：`memory_promote.py --id <memory-id>`（字段完整性 + 去敏校验均通过后移动至 approved）
- `memory_promote.py --list-candidates`：列出所有待复审 candidate，供人工挑选

<!-- TOOL-VARIANT: memory-policy -->
> 工具相关的脚本调用与路径解析见对应分片：
> Codex → memory-policy.codex.md ｜ Claude → memory-policy.claude.md
```

- [ ] **Step 4: 复制到 Claude 版（内容完全相同）**

```bash
cp ~/.agents/plugins/sql-expert-dba/skills/_shared/memory-policy.md \
   ~/Library/CodeRepo/AI/claude-plugins/sql-expert-dba/skills/_shared/memory-policy.md
```

- [ ] **Step 5: 运行测试，确认通过**

```bash
cd ~/.agents/plugins/sql-expert-dba
python3 -m pytest scripts/test_skill_docs_v2.py::TestSkillDocsV2::test_memory_policy_unified_wording \
                  scripts/test_skill_docs_v2.py::TestSkillDocsV2::test_shared_memory_policy_mentions_v2_storage_layers -v
```

期望：均 PASSED

- [ ] **Step 6: Commit**

```bash
cd ~/.agents/plugins/sql-expert-dba
git add skills/_shared/memory-policy.md scripts/test_skill_docs_v2.py
git commit -m "docs: rewrite memory-policy.md to silent-eval / output-only-on-write wording"
cd ~/Library/CodeRepo/AI/claude-plugins/sql-expert-dba
git add skills/_shared/memory-policy.md
git commit -m "docs: rewrite memory-policy.md to silent-eval / output-only-on-write wording"
```

---

## Task 4: 重写 output-contract.md 第 7 段

**Files:**
- Modify: `~/.agents/plugins/sql-expert-dba/skills/_shared/output-contract.md`
- Modify: `~/Library/CodeRepo/AI/claude-plugins/sql-expert-dba/skills/_shared/output-contract.md`

- [ ] **Step 1: 写失败测试**

在 `test_skill_docs_v2.py` 追加：

```python
def test_output_contract_no_mandatory_memory_section(self):
    contract = SKILLS_DIR / "_shared" / "output-contract.md"
    content = contract.read_text(encoding="utf-8")
    # 旧措辞必须不存在
    self.assertNotIn("记忆判定（必填，三选一", content)
    self.assertNotIn("缺此段视为任务未完成", content)
    self.assertNotIn("last-context.json", content)
    self.assertNotIn("Stop hook", content)
    # 新措辞必须存在
    self.assertIn("沉淀结果（仅写入时输出）", content)
    self.assertIn("workflow 收尾执行记忆自评估", content)
```

- [ ] **Step 2: 运行测试，确认失败**

```bash
cd ~/.agents/plugins/sql-expert-dba
python3 -m pytest scripts/test_skill_docs_v2.py::TestSkillDocsV2::test_output_contract_no_mandatory_memory_section -v
```

期望：FAIL

- [ ] **Step 3: 重写 output-contract.md**

将 `~/.agents/plugins/sql-expert-dba/skills/_shared/output-contract.md` 全文替换为：

```markdown
# 统一输出契约

所有 SQL Expert DBA workflow 的输出必须遵循以下六段式结构。该契约确保用户体验一致、事实与推断显式分离。

## 输出骨架

### 1. 任务判断

- 明确当前任务所属 workflow 类型
- 如由 router 分诊，标注 primary_workflow 和 secondary_workflow
- 如需串联下游 workflow，在此声明

**格式**：1-2 句话，简洁明了。

### 2. 已确认

列出用户明确提供的信息，标注 `已确认`：

- SQL 原文
- 方言（MySQL / PostgreSQL / 其他）
- DDL / 表结构
- EXPLAIN / 执行计划
- 报错全文 / 错误码
- 业务需求描述
- 其他用户显式提供的上下文

**格式**：有序列表，每项以 `已确认` 开头。

### 3. 待确认 / 推断

列出基于经验或上下文推断的信息，每项必须标注 `[推断]` 并说明依据：

- `[推断]` 方言为 MySQL（基于语法特征 `LIMIT` + `IFNULL`）
- `[推断]` 数据量级约 100 万行（基于 EXPLAIN rows 估算）

**格式**：有序列表，每项以 `[推断]` 标记开头。

如无推断项，写"无推断项"。

### 4. 主输出

这是 workflow 的核心交付物：

- **sql-query-optimizer**：优化建议 + 改写 SQL + 索引建议
- **sql-error-diagnostician**：根因排序 + 修复路径
- **sql-schema-reviewer**：结构风险 + 索引建议 + 约束建议
- **sql-report-query-builder**：生成的业务 SQL

**格式**：按 workflow 类型的专属格式组织。主输出中的推断内容同样需标注 `[推断]`。

### 5. 验证建议

给出用户可执行的验证步骤：

- 建议运行的 EXPLAIN 命令
- 建议检查的数据样本
- 建议的回归测试场景
- 建议的口径验证方法

**格式**：有序列表，每步可直接执行。

### 6. 可选学习补充

> **默认省略此段。** 仅当用户显式请求时展开：
> - "解释一下"
> - "帮我复盘"
> - "为什么这样做"
> - "我想学习这个知识点"

展开时包含：
- 相关概念解释
- 最佳实践说明
- 跨方言差异说明
- 推荐阅读或参考

## v2 可选段落

以下 v2 可选段落只能嵌入六段式结构中的相关段落内，不得作为第 7 个顶层段落。

### 使用的项目上下文

当回答使用了 `./sql/.index/`、DDL、EXPLAIN、慢 SQL 或项目说明时，简要列出来源文件和已使用事实。

### 命中的业务规则

当回答使用了 `./sql/biz-rules/` 时，列出业务模块、相关表和规则文件。

### 沉淀结果（仅写入时输出）

workflow 收尾执行记忆自评估（强制动作，静默执行）。**仅当**实际写入了 candidate 或 approved 时，才在交付末尾输出一行：

```
📌 已沉淀：<title>（<type>，<review_status>）→ <相对路径>
```

未写入时，此行**不出现**，也不解释原因。

## 硬约束

1. 不允许在 `已确认` 段混入推断内容
2. 不允许在 `主输出` 段省略 `[推断]` 标记
3. `可选学习补充` 在用户未请求时严禁自动展开
4. 所有 SQL 代码块必须标注方言（如 ```sql -- MySQL）
5. 当输入不足以产出可靠的主输出时，必须在 `待确认/推断` 段指出缺口，并在主输出中采用保守策略
6. workflow 收尾**必须执行**记忆自评估（静默动作）；有写入时输出 `📌 已沉淀` 行，无写入时静默——两种情况均视为交付完整
```

- [ ] **Step 4: 复制到 Claude 版**

```bash
cp ~/.agents/plugins/sql-expert-dba/skills/_shared/output-contract.md \
   ~/Library/CodeRepo/AI/claude-plugins/sql-expert-dba/skills/_shared/output-contract.md
```

- [ ] **Step 5: 运行测试，确认通过**

```bash
cd ~/.agents/plugins/sql-expert-dba
python3 -m pytest scripts/test_skill_docs_v2.py::TestSkillDocsV2::test_output_contract_no_mandatory_memory_section \
                  scripts/test_skill_docs_v2.py::TestSkillDocsV2::test_output_contract_mentions_v2_optional_sections -v
```

期望：均 PASSED

- [ ] **Step 6: Commit**

```bash
cd ~/.agents/plugins/sql-expert-dba
git add skills/_shared/output-contract.md scripts/test_skill_docs_v2.py
git commit -m "docs: output-contract section 7 → silent eval / output-only-on-write"
cd ~/Library/CodeRepo/AI/claude-plugins/sql-expert-dba
git add skills/_shared/output-contract.md
git commit -m "docs: output-contract section 7 → silent eval / output-only-on-write"
```

---

## Task 5: 统一 5 个 SKILL.md 记忆措辞（两版对称）

**Files:**
- Modify: `~/.agents/plugins/sql-expert-dba/skills/sql-expert-router/SKILL.md`
- Modify: `~/.agents/plugins/sql-expert-dba/skills/sql-query-optimizer/SKILL.md`
- Modify: `~/.agents/plugins/sql-expert-dba/skills/sql-error-diagnostician/SKILL.md`
- Modify: `~/.agents/plugins/sql-expert-dba/skills/sql-schema-reviewer/SKILL.md`
- Modify: `~/.agents/plugins/sql-expert-dba/skills/sql-report-query-builder/SKILL.md`
- 以上 5 个文件同步到 Claude 版

- [ ] **Step 1: 写失败测试**

在 `test_skill_docs_v2.py` 追加：

```python
def test_skill_unified_memory_wording(self):
    for path in sorted(SKILLS_DIR.glob("sql-*/SKILL.md")):
        content = path.read_text(encoding="utf-8")
        # 旧措辞不应存在
        self.assertNotIn("后台记忆评估", content,
                         f"{path}: old '后台记忆评估' wording found")
        self.assertNotIn("无相关已沉淀记忆", content,
                         f"{path}: old '无相关已沉淀记忆' wording found")
        self.assertNotIn("Memory 检索（读取闭环，强制）", content,
                         f"{path}: old Memory 检索 wording found")

def test_router_skill_hit_only_visible_wording(self):
    router = SKILLS_DIR / "sql-expert-router" / "SKILL.md"
    content = router.read_text(encoding="utf-8")
    self.assertIn("分诊前记忆检索（强制动作，命中才可见）", content)
    self.assertIn("TOOL-VARIANT: memory-policy", content)

def test_workflow_skills_silent_eval_wording(self):
    for skill in ["sql-query-optimizer", "sql-error-diagnostician",
                  "sql-schema-reviewer", "sql-report-query-builder"]:
        path = SKILLS_DIR / skill / "SKILL.md"
        content = path.read_text(encoding="utf-8")
        self.assertIn("收尾记忆自评估（强制动作，静默执行）", content,
                      f"{path}: missing unified memory wording")
        self.assertIn("TOOL-VARIANT: memory-policy", content,
                      f"{path}: missing TOOL-VARIANT marker")
```

- [ ] **Step 2: 运行测试，确认失败**

```bash
cd ~/.agents/plugins/sql-expert-dba
python3 -m pytest scripts/test_skill_docs_v2.py::TestSkillDocsV2::test_skill_unified_memory_wording \
                  scripts/test_skill_docs_v2.py::TestSkillDocsV2::test_router_skill_hit_only_visible_wording \
                  scripts/test_skill_docs_v2.py::TestSkillDocsV2::test_workflow_skills_silent_eval_wording -v
```

期望：三个测试均 FAIL

- [ ] **Step 3: 修改 sql-expert-router/SKILL.md**

将 `## Memory 检索（读取闭环，强制）` 整段替换为：

```markdown
## 分诊前记忆检索（强制动作，命中才可见）

分诊前**必须**调用 `memory_search.py` 检索（此动作不可省略）。

<!-- TOOL-VARIANT: memory-policy -->
> 工具相关的脚本调用与路径解析见对应分片：
> Codex → memory-policy.codex.md ｜ Claude → memory-policy.claude.md

**仅当**命中 approved 记忆**且其实际影响本轮分诊结论**时，才显式引用（注明 memory id / title + 适用要点）。
命中 candidate 仅作内部参考、不作为结论，**不强制输出**。
未命中时**静默**，不输出「无相关记忆」。

当用户说「复审记忆」「把这条转正」「晋升这条记忆」时，引导调用 `memory_promote.py --list-candidates` 列出候选，再由用户指定 `--id` 执行晋升。
```

- [ ] **Step 4: 修改 4 个 workflow SKILL.md 的「后台记忆评估」段**

对 `sql-query-optimizer/SKILL.md`、`sql-error-diagnostician/SKILL.md`、`sql-schema-reviewer/SKILL.md`、`sql-report-query-builder/SKILL.md` 中的 `## 后台记忆评估` 整段，统一替换为：

```markdown
## 收尾记忆自评估（强制动作，静默执行）

主任务完成后，**必须**执行一次记忆自评估（此动作不可省略）。评估过程与「判定丢弃」结果一律静默。
**仅当**实际写入 candidate 或 approved 时，在交付末尾输出：
`📌 已沉淀：<title>（<type>，<review_status>）→ <相对路径>`

<!-- TOOL-VARIANT: memory-policy -->
> 工具相关的脚本调用与路径解析见对应分片：
> Codex → memory-policy.codex.md ｜ Claude → memory-policy.claude.md

以下模式优先考虑沉淀（评估时参考）：
```

其中 `sql-query-optimizer` 在列表保留：
```
- 非直觉的反模式案例（如隐式类型转换）
- 跨方言的索引行为差异
- 高复用的 EXPLAIN 解读经验
- 通用优化规则
```

`sql-error-diagnostician` 保留（从原段落的「沉淀优先级判断」表格，精简为）：
```
- 稳定错误模式（错误码到根因的确定映射）
- 跨方言行为差异导致的报错
- 首次出现的新错误模式（先进 candidate）
- 一次性拼写错误或配置问题 → 不沉淀，丢弃
```

`sql-schema-reviewer` 保留：
```
- 发现的通用命名反模式（如"使用 `data` 作为字段名"）
- 跨方言的类型选择规则（如"金额字段使用 DECIMAL"）
- 特定场景的索引策略（经去敏后）
- 高频出现的约束缺失模式
```

`sql-report-query-builder` 保留：
```
- 可复用的报表 SQL 模板（去敏后）
- 高频口径定义模式
- 跨业务通用的统计 SQL 结构
```

同时将 `sql-query-optimizer/SKILL.md` 的行内 `memory_search.py` 裸名调用（Step 1 引用部分）改为 TOOL-VARIANT 标记（如果有）。

注意：`sql-schema-reviewer` 的「全局 memory 沉淀流程」列表中的 `memory_search.py` / `memory_capture.py` 裸调用行，替换为：

```markdown
<!-- TOOL-VARIANT: memory-policy -->
> 工具相关的脚本调用与路径解析见对应分片：
> Codex → memory-policy.codex.md ｜ Claude → memory-policy.claude.md
```

- [ ] **Step 5: 复制 5 个 SKILL.md 到 Claude 版**

```bash
for skill in sql-expert-router sql-query-optimizer sql-error-diagnostician sql-schema-reviewer sql-report-query-builder; do
  cp ~/.agents/plugins/sql-expert-dba/skills/$skill/SKILL.md \
     ~/Library/CodeRepo/AI/claude-plugins/sql-expert-dba/skills/$skill/SKILL.md
done
```

- [ ] **Step 6: 运行测试，确认通过**

```bash
cd ~/.agents/plugins/sql-expert-dba
python3 -m pytest scripts/test_skill_docs_v2.py -v
```

期望：所有测试 PASSED（包括已有 6 个 + 新增 5 个）

- [ ] **Step 7: Commit**

```bash
cd ~/.agents/plugins/sql-expert-dba
git add skills/
git commit -m "docs: unify 5 SKILL.md memory wording (silent eval + hit-only-visible + TOOL-VARIANT)"
cd ~/Library/CodeRepo/AI/claude-plugins/sql-expert-dba
git add skills/
git commit -m "docs: unify 5 SKILL.md memory wording (silent eval + hit-only-visible + TOOL-VARIANT)"
```

---

## Task 6: paths.py 注释 + README 更新（两版对称）

**Files:**
- Modify: `~/.agents/plugins/sql-expert-dba/scripts/paths.py`
- Modify: `~/.agents/plugins/sql-expert-dba/README.md`
- Modify: `~/Library/CodeRepo/AI/claude-plugins/sql-expert-dba/scripts/paths.py`
- Modify: `~/Library/CodeRepo/AI/claude-plugins/sql-expert-dba/README.md`

- [ ] **Step 1: 在 paths.py 的 resolve_user_memory_dir 上方添加注释**

在 `~/.agents/plugins/sql-expert-dba/scripts/paths.py` 第 19 行（`def resolve_user_memory_dir(` 前）插入：

```python
# 真源位置与重装不丢说明：
#   Codex 版落点：~/.codex/memories/sql-expert-dba/（或 CODEX_HOME/memories/sql-expert-dba/）
#   Claude 版落点：~/.claude/plugins/data/sql-expert-dba/memory/
#   两版落点均与插件源码物理分离——插件重装/升级不影响已沉淀记忆。
#   可用 SQL_EXPERT_DBA_MEMORY_DIR 环境变量覆盖（优先级最高）。
```

- [ ] **Step 2: 重写 README.md**

将 `~/.agents/plugins/sql-expert-dba/README.md` 全文替换为：

```markdown
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
```

- [ ] **Step 3: 同步到 Claude 版**

```bash
cp ~/.agents/plugins/sql-expert-dba/scripts/paths.py \
   ~/Library/CodeRepo/AI/claude-plugins/sql-expert-dba/scripts/paths.py
cp ~/.agents/plugins/sql-expert-dba/README.md \
   ~/Library/CodeRepo/AI/claude-plugins/sql-expert-dba/README.md
```

- [ ] **Step 4: 验证 README 无 hook 启用指南**

```bash
grep -c "启用增强路径" ~/.agents/plugins/sql-expert-dba/README.md
grep -c "plugin_hooks" ~/.agents/plugins/sql-expert-dba/README.md
```

期望：两行均输出 `0`

- [ ] **Step 5: Commit**

```bash
cd ~/.agents/plugins/sql-expert-dba
git add scripts/paths.py README.md
git commit -m "docs: document memory true source location and reinstall safety in paths.py + README"
cd ~/Library/CodeRepo/AI/claude-plugins/sql-expert-dba
git add scripts/paths.py README.md
git commit -m "docs: document memory true source location and reinstall safety in paths.py + README"
```

---

## Task 7: 新建 sanitize.py

**Files:**
- Create: `~/.agents/plugins/sql-expert-dba/scripts/sanitize.py`
- Create: `~/.agents/plugins/sql-expert-dba/scripts/test_sanitize.py`
- 两文件同步到 Claude 版

- [ ] **Step 1: 写失败测试**

创建 `~/.agents/plugins/sql-expert-dba/scripts/test_sanitize.py`：

```python
#!/usr/bin/env python3
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


class TestSanitize(unittest.TestCase):

    def setUp(self):
        import sanitize
        self.sanitize = sanitize

    def test_phone_blocked(self):
        result = self.sanitize.check("联系方式 13812345678 请查收")
        self.assertFalse(result.ok)
        self.assertIn("phone", result.pattern)

    def test_email_blocked(self):
        result = self.sanitize.check("发邮件到 user@example.com 确认")
        self.assertFalse(result.ok)
        self.assertIn("email", result.pattern)

    def test_id_card_blocked(self):
        result = self.sanitize.check("身份证 110101199003074512 核验")
        self.assertFalse(result.ok)
        self.assertIn("id_card", result.pattern)

    def test_ip_blocked(self):
        result = self.sanitize.check("服务器 192.168.1.100 上的 MySQL")
        self.assertFalse(result.ok)
        self.assertIn("ip", result.pattern)

    def test_clean_text_passes(self):
        result = self.sanitize.check("VARCHAR字段与数字比较导致索引失效")
        self.assertTrue(result.ok)

    def test_allow_token_bypasses_block(self):
        result = self.sanitize.check("13812345678", allow_tokens=["13812345678"])
        self.assertTrue(result.ok)

    def test_forbidden_token_blocks(self):
        result = self.sanitize.check("orders表的amount字段", forbidden_tokens=["orders"])
        self.assertFalse(result.ok)
        self.assertIn("forbidden_token", result.pattern)

    def test_biz_rules_scope_not_scanned(self):
        # biz_rules=True → 内置模式不扫描，但 forbidden_token 仍生效
        result = self.sanitize.check("13812345678", biz_rules=True)
        self.assertTrue(result.ok)

    def test_biz_rules_forbidden_token_still_blocks(self):
        result = self.sanitize.check("orders表", forbidden_tokens=["orders"], biz_rules=True)
        self.assertFalse(result.ok)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 运行测试，确认失败**

```bash
cd ~/.agents/plugins/sql-expert-dba
python3 -m pytest scripts/test_sanitize.py -v
```

期望：ImportError — `No module named 'sanitize'`

- [ ] **Step 3: 创建 sanitize.py**

```python
#!/usr/bin/env python3
"""
Sensitive-pattern scanner for SQL Expert DBA global memory entries.

Scope:
  - Applied to global memory (candidates + approved).
  - NOT applied to biz-rules/ (real table names are allowed there).

Usage (programmatic):
    from sanitize import check, CheckResult
    result = check(text, forbidden_tokens=["real_table"], allow_tokens=["13800000000"])
    if not result.ok:
        raise ValueError(result.message)

CLI usage (for manual testing):
    python3 sanitize.py --text "some text" [--forbidden-token tok] [--allow-token tok]
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field


# Built-in sensitive patterns (global memory only)
_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("phone", re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)")),
    ("email", re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")),
    ("id_card", re.compile(r"(?<!\d)\d{17}[\dXx](?!\d)")),
    ("ip", re.compile(r"(?<!\d)(?:\d{1,3}\.){3}\d{1,3}(?!\d)")),
]


@dataclass
class CheckResult:
    ok: bool
    pattern: str = ""
    matched: str = ""
    message: str = ""


def check(
    text: str,
    *,
    forbidden_tokens: list[str] | None = None,
    allow_tokens: list[str] | None = None,
    biz_rules: bool = False,
) -> CheckResult:
    """Scan text for sensitive patterns.

    Args:
        text: Content to scan.
        forbidden_tokens: Additional tokens that must not appear.
        allow_tokens: Tokens to explicitly allow (false-positive bypass).
        biz_rules: If True, skip built-in pattern scan (biz-rules scope).

    Returns:
        CheckResult with ok=True if text is clean.
    """
    allow_set = {t.lower() for t in (allow_tokens or [])}

    if not biz_rules:
        for pattern_name, regex in _PATTERNS:
            match = regex.search(text)
            if match:
                matched = match.group(0)
                if matched.lower() in allow_set:
                    continue
                return CheckResult(
                    ok=False,
                    pattern=pattern_name,
                    matched=matched,
                    message=(
                        f"Sensitive pattern '{pattern_name}' detected: {matched!r}. "
                        f"Remove the sensitive content or use --allow-token to bypass."
                    ),
                )

    for token in (forbidden_tokens or []):
        if not token:
            continue
        if token.lower() in allow_set:
            continue
        if token.lower() in text.lower():
            return CheckResult(
                ok=False,
                pattern="forbidden_token",
                matched=token,
                message=(
                    f"Forbidden token {token!r} found in text. "
                    f"Remove or use --allow-token to bypass."
                ),
            )

    return CheckResult(ok=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Sanitize check for memory entry text")
    parser.add_argument("--text", required=True, help="Text to scan")
    parser.add_argument("--forbidden-token", action="append", dest="forbidden_tokens",
                        help="Additional forbidden token (repeatable)")
    parser.add_argument("--allow-token", action="append", dest="allow_tokens",
                        help="Token to allow despite matching a pattern (repeatable)")
    parser.add_argument("--biz-rules", action="store_true",
                        help="Skip built-in pattern scan (biz-rules scope)")
    args = parser.parse_args()

    result = check(
        args.text,
        forbidden_tokens=args.forbidden_tokens,
        allow_tokens=args.allow_tokens,
        biz_rules=args.biz_rules,
    )
    if result.ok:
        print("OK: text is clean")
    else:
        print(f"BLOCKED: {result.message}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: 运行测试，确认通过**

```bash
cd ~/.agents/plugins/sql-expert-dba
python3 -m pytest scripts/test_sanitize.py -v
```

期望：所有 9 个测试 PASSED

- [ ] **Step 5: 复制到 Claude 版**

```bash
cp ~/.agents/plugins/sql-expert-dba/scripts/sanitize.py \
   ~/Library/CodeRepo/AI/claude-plugins/sql-expert-dba/scripts/sanitize.py
cp ~/.agents/plugins/sql-expert-dba/scripts/test_sanitize.py \
   ~/Library/CodeRepo/AI/claude-plugins/sql-expert-dba/scripts/test_sanitize.py
```

- [ ] **Step 6: Commit**

```bash
cd ~/.agents/plugins/sql-expert-dba
git add scripts/sanitize.py scripts/test_sanitize.py
git commit -m "feat: add sanitize.py with built-in sensitive pattern scanning"
cd ~/Library/CodeRepo/AI/claude-plugins/sql-expert-dba
git add scripts/sanitize.py scripts/test_sanitize.py
git commit -m "feat: add sanitize.py with built-in sensitive pattern scanning"
```

---

## Task 8: 将 sanitize.py 接入 memory_capture.py

**Files:**
- Modify: `~/.agents/plugins/sql-expert-dba/scripts/memory_capture.py`
- Modify: `~/.agents/plugins/sql-expert-dba/scripts/test_memory_capture_sanitize.py`（新建测试）
- 两文件同步到 Claude 版

- [ ] **Step 1: 写失败测试**

创建 `~/.agents/plugins/sql-expert-dba/scripts/test_memory_capture_sanitize.py`：

```python
#!/usr/bin/env python3
"""Tests that memory_capture.py blocks sensitive content via sanitize.py."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
CAPTURE_SCRIPT = SCRIPTS_DIR / "memory_capture.py"


def run_capture(args: list[str], memory_dir: Path) -> dict:
    env = {**os.environ, "SQL_EXPERT_DBA_MEMORY_DIR": str(memory_dir)}
    result = subprocess.run(
        [sys.executable, str(CAPTURE_SCRIPT)] + args,
        capture_output=True, text=True, env=env,
    )
    if result.stdout.strip():
        return json.loads(result.stdout)
    return {"status": "error", "stderr": result.stderr, "returncode": result.returncode}


class TestMemoryCaptureSanitize(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.mkdtemp()
        self.memory_dir = Path(self._tmp)

    def _base_args(self, **overrides) -> list[str]:
        base = {
            "--title": "测试规则",
            "--type": "rule",
            "--problem-pattern": "测试模式",
            "--conclusion": "测试结论",
            "--boundaries": "测试边界",
            "--capture-mode": "explicit_user_requested",
        }
        base.update(overrides)
        args = []
        for k, v in base.items():
            args.extend([k, v])
        return args

    def test_phone_in_conclusion_is_blocked(self):
        args = self._base_args(**{"--conclusion": "联系 13812345678 确认"})
        result = run_capture(args, self.memory_dir)
        self.assertEqual(result["status"], "skipped")
        self.assertEqual(result["reason"], "unsanitized_global_memory")

    def test_clean_content_is_captured(self):
        args = self._base_args()
        result = run_capture(args, self.memory_dir)
        self.assertEqual(result["status"], "captured")

    def test_allow_token_bypasses_phone_block(self):
        args = self._base_args(**{"--conclusion": "联系 13812345678 确认"})
        args.extend(["--allow-token", "13812345678"])
        result = run_capture(args, self.memory_dir)
        self.assertEqual(result["status"], "captured")

    def test_forbidden_token_still_blocks(self):
        args = self._base_args(**{"--conclusion": "orders表统计"})
        args.extend(["--forbidden-token", "orders"])
        result = run_capture(args, self.memory_dir)
        self.assertEqual(result["status"], "skipped")
        self.assertEqual(result["reason"], "unsanitized_global_memory")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 运行测试，确认失败**

```bash
cd ~/.agents/plugins/sql-expert-dba
python3 -m pytest scripts/test_memory_capture_sanitize.py::TestMemoryCaptureSanitize::test_phone_in_conclusion_is_blocked -v
```

期望：FAIL — phone 号未被拦截（旧代码只检查 forbidden_token）

- [ ] **Step 3: 修改 memory_capture.py**

1. 在 `from paths import ...` 行后加导入：
```python
from sanitize import check as sanitize_check
```

2. 在 `parser` 中新增 `--allow-token` 参数（紧接现有 `--forbidden-token` 后）：
```python
parser.add_argument(
    "--allow-token", action="append",
    help="Token to allow despite matching a sensitive pattern (false-positive bypass)"
)
```

3. 将 `contains_forbidden_tokens` 函数调用替换为 `sanitize_check`。在 `main()` 内的 `if contains_forbidden_tokens(args):` 块替换为：

```python
    # 合并所有需扫描的字段文本
    _scan_text = " ".join(
        str(value or "")
        for value in (
            args.title,
            args.type,
            args.workflow,
            args.dialect,
            args.tags,
            args.problem_pattern,
            args.preconditions,
            args.conclusion,
            args.boundaries,
            args.example,
            args.anti_example,
            args.confidence,
            args.origin_skill,
            args.capture_mode,
        )
    )
    _sanitize_result = sanitize_check(
        _scan_text,
        forbidden_tokens=args.forbidden_token or [],
        allow_tokens=args.allow_token or [],
        biz_rules=False,
    )
    if not _sanitize_result.ok:
        print(json.dumps({
            "status": "skipped",
            "reason": "unsanitized_global_memory",
            "title": args.title,
            "detail": _sanitize_result.message,
        }, ensure_ascii=False, indent=2))
        return
```

- [ ] **Step 4: 运行所有 sanitize + capture 测试**

```bash
cd ~/.agents/plugins/sql-expert-dba
python3 -m pytest scripts/test_sanitize.py scripts/test_memory_capture_sanitize.py -v
```

期望：所有测试 PASSED

- [ ] **Step 5: 复制到 Claude 版**

```bash
cp ~/.agents/plugins/sql-expert-dba/scripts/memory_capture.py \
   ~/Library/CodeRepo/AI/claude-plugins/sql-expert-dba/scripts/memory_capture.py
cp ~/.agents/plugins/sql-expert-dba/scripts/test_memory_capture_sanitize.py \
   ~/Library/CodeRepo/AI/claude-plugins/sql-expert-dba/scripts/test_memory_capture_sanitize.py
```

- [ ] **Step 6: Commit**

```bash
cd ~/.agents/plugins/sql-expert-dba
git add scripts/memory_capture.py scripts/test_memory_capture_sanitize.py
git commit -m "feat: wire sanitize.py into memory_capture.py; add --allow-token"
cd ~/Library/CodeRepo/AI/claude-plugins/sql-expert-dba
git add scripts/memory_capture.py scripts/test_memory_capture_sanitize.py
git commit -m "feat: wire sanitize.py into memory_capture.py; add --allow-token"
```

---

## Task 9: 新建 memory_promote.py

**Files:**
- Create: `~/.agents/plugins/sql-expert-dba/scripts/memory_promote.py`
- Create: `~/.agents/plugins/sql-expert-dba/scripts/test_memory_promote.py`
- 两文件同步到 Claude 版

- [ ] **Step 1: 写失败测试**

创建 `~/.agents/plugins/sql-expert-dba/scripts/test_memory_promote.py`：

```python
#!/usr/bin/env python3
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
PROMOTE_SCRIPT = SCRIPTS_DIR / "memory_promote.py"
CAPTURE_SCRIPT = SCRIPTS_DIR / "memory_capture.py"

REQUIRED_FIELDS = ("id", "title", "type", "problem_pattern", "conclusion", "boundaries")


def run_script(script: Path, args: list[str], memory_dir: Path) -> tuple[int, str, str]:
    env = {**os.environ, "SQL_EXPERT_DBA_MEMORY_DIR": str(memory_dir)}
    r = subprocess.run(
        [sys.executable, str(script)] + args,
        capture_output=True, text=True, env=env,
    )
    return r.returncode, r.stdout, r.stderr


def capture_candidate(memory_dir: Path, title: str = "测试规则") -> str:
    """Capture a candidate entry and return its memory ID."""
    args = [
        "--title", title,
        "--type", "rule",
        "--problem-pattern", "测试模式",
        "--conclusion", "测试结论",
        "--boundaries", "测试边界",
        "--capture-mode", "auto_background",
    ]
    _, stdout, _ = run_script(CAPTURE_SCRIPT, args, memory_dir)
    data = json.loads(stdout)
    assert data["status"] == "captured", f"Capture failed: {data}"
    return data["id"]


class TestMemoryPromote(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.mkdtemp()
        self.memory_dir = Path(self._tmp)

    def test_list_candidates_shows_captured_entry(self):
        capture_candidate(self.memory_dir, "列表测试规则")
        rc, stdout, _ = run_script(
            PROMOTE_SCRIPT, ["--list-candidates"], self.memory_dir
        )
        self.assertEqual(rc, 0)
        self.assertIn("列表测试规则", stdout)

    def test_promote_moves_to_approved(self):
        memory_id = capture_candidate(self.memory_dir, "晋升测试规则")
        rc, stdout, stderr = run_script(
            PROMOTE_SCRIPT, ["--id", memory_id], self.memory_dir
        )
        self.assertEqual(rc, 0, f"promote failed: {stderr}")
        data = json.loads(stdout)
        self.assertEqual(data["status"], "promoted")
        self.assertEqual(data["review_status"], "approved")
        # 验证文件已移动到 approved/
        approved_path = self.memory_dir / data["file"]
        self.assertTrue(approved_path.exists())
        self.assertIn("approved", str(approved_path))

    def test_promote_updates_index(self):
        memory_id = capture_candidate(self.memory_dir, "索引更新测试")
        run_script(PROMOTE_SCRIPT, ["--id", memory_id], self.memory_dir)
        index = json.loads((self.memory_dir / "index.json").read_text())
        approved = [e for e in index["entries"] if e["id"] == memory_id]
        self.assertEqual(len(approved), 1)
        self.assertEqual(approved[0]["review_status"], "approved")

    def test_promote_nonexistent_id_fails(self):
        rc, _, stderr = run_script(
            PROMOTE_SCRIPT, ["--id", "rule-nonexist"], self.memory_dir
        )
        self.assertNotEqual(rc, 0)
        self.assertIn("not found", stderr.lower())

    def test_promote_blocked_by_sanitize(self):
        # 手动构造一个含敏感内容的 candidate 文件（绕过 capture 的正常拦截）
        from pathlib import Path
        import time
        candidate_dir = self.memory_dir / "candidates" / "rules"
        candidate_dir.mkdir(parents=True, exist_ok=True)
        bad_file = candidate_dir / "rule-badc0d-test.md"
        bad_file.write_text(
            '---\nid: "rule-badc0d"\ntitle: "电话规则"\ntype: "rule"\n'
            'problem_pattern: "联系 13812345678 查询"\nconclusion: "测试"\n'
            'boundaries: "test"\nreview_status: "candidate"\n---\n\n# 电话规则\n',
            encoding="utf-8",
        )
        rc, _, stderr = run_script(
            PROMOTE_SCRIPT, ["--id", "rule-badc0d"], self.memory_dir
        )
        self.assertNotEqual(rc, 0)
        self.assertIn("sensitiv", stderr.lower())


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 运行测试，确认失败**

```bash
cd ~/.agents/plugins/sql-expert-dba
python3 -m pytest scripts/test_memory_promote.py -v
```

期望：ImportError 或 FileNotFoundError — `memory_promote.py` 不存在

- [ ] **Step 3: 创建 memory_promote.py**

```python
#!/usr/bin/env python3
"""
Promote a candidate memory entry to approved after field validation and sanitize check.

Usage:
    python3 memory_promote.py --list-candidates
    python3 memory_promote.py --id <memory-id> [--allow-token <tok>]
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _frontmatter import parse_frontmatter
from paths import ensure_global_memory_dirs, resolve_user_memory_dir
from sanitize import check as sanitize_check

REQUIRED_FIELDS = ("id", "title", "type", "problem_pattern", "conclusion", "boundaries")


def _candidate_files(memory_dir: Path) -> list[Path]:
    candidates_root = memory_dir / "candidates"
    if not candidates_root.is_dir():
        return []
    return sorted(candidates_root.rglob("*.md"))


def find_candidate(memory_dir: Path, memory_id: str) -> Path | None:
    for f in _candidate_files(memory_dir):
        fm = parse_frontmatter(f)
        if fm and fm.get("id") == memory_id:
            return f
    return None


def list_candidates(memory_dir: Path) -> None:
    files = _candidate_files(memory_dir)
    if not files:
        print("No candidates found.")
        return
    print(f"{'ID':<20} {'Type':<12} {'Title'}")
    print("-" * 70)
    for f in files:
        fm = parse_frontmatter(f)
        if fm:
            print(f"{fm.get('id',''):<20} {fm.get('type',''):<12} {fm.get('title','')}")


def promote(memory_dir: Path, memory_id: str, allow_tokens: list[str]) -> None:
    candidate_path = find_candidate(memory_dir, memory_id)
    if candidate_path is None:
        print(f"Error: candidate with id '{memory_id}' not found in {memory_dir}/candidates/",
              file=sys.stderr)
        sys.exit(1)

    fm = parse_frontmatter(candidate_path)
    if fm is None:
        print(f"Error: could not parse frontmatter from {candidate_path}", file=sys.stderr)
        sys.exit(1)

    # Field validation
    missing = [f for f in REQUIRED_FIELDS if not str(fm.get(f, "") or "").strip()]
    if missing:
        print(f"Error: missing required fields for promotion: {missing}", file=sys.stderr)
        sys.exit(1)

    # Sanitize check — re-scan all persisted fields
    scan_text = " ".join(str(fm.get(f, "") or "") for f in (
        "title", "type", "workflow", "dialect", "tags",
        "problem_pattern", "preconditions", "conclusion",
        "boundaries", "example", "anti_example",
    ))
    result = sanitize_check(scan_text, allow_tokens=allow_tokens, biz_rules=False)
    if not result.ok:
        print(f"Error: sanitize check failed — {result.message}", file=sys.stderr)
        sys.exit(1)

    # Determine target approved path (mirror structure under approved/)
    rel = candidate_path.relative_to(memory_dir / "candidates")
    approved_path = memory_dir / "approved" / rel
    approved_path.parent.mkdir(parents=True, exist_ok=True)

    # Read, update review_status, write to approved
    text = candidate_path.read_text(encoding="utf-8")
    text = text.replace('review_status: "candidate"', 'review_status: "approved"', 1)
    approved_path.write_text(text, encoding="utf-8")
    candidate_path.unlink()

    # Update index
    _update_index(memory_dir, memory_id, approved_path)

    result_data = {
        "status": "promoted",
        "id": memory_id,
        "review_status": "approved",
        "file": str(approved_path.relative_to(memory_dir)),
    }
    print(json.dumps(result_data, ensure_ascii=False, indent=2))


def _update_index(memory_dir: Path, memory_id: str, approved_path: Path) -> None:
    index_path = memory_dir / "index.json"
    if not index_path.exists():
        return
    data = json.loads(index_path.read_text(encoding="utf-8"))
    entries = data.get("entries", [])
    for entry in entries:
        if entry.get("id") == memory_id:
            entry["review_status"] = "approved"
            entry["file"] = str(approved_path.relative_to(memory_dir))
            break
    index_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                          encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Promote candidate memory entry to approved")
    parser.add_argument("--memory-dir", type=Path, help="User-level global memory directory")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--list-candidates", action="store_true",
                       help="List all candidate entries")
    group.add_argument("--id", help="Memory ID to promote")
    parser.add_argument("--allow-token", action="append", dest="allow_tokens",
                        help="Token to allow despite matching a sensitive pattern")
    args = parser.parse_args()

    if args.memory_dir is None:
        args.memory_dir = resolve_user_memory_dir()
    args.memory_dir = args.memory_dir.expanduser()
    ensure_global_memory_dirs(args.memory_dir)

    if args.list_candidates:
        list_candidates(args.memory_dir)
    else:
        promote(args.memory_dir, args.id, args.allow_tokens or [])


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: 运行所有 promote 测试**

```bash
cd ~/.agents/plugins/sql-expert-dba
python3 -m pytest scripts/test_memory_promote.py -v
```

期望：所有 5 个测试 PASSED

- [ ] **Step 5: 复制到 Claude 版**

```bash
cp ~/.agents/plugins/sql-expert-dba/scripts/memory_promote.py \
   ~/Library/CodeRepo/AI/claude-plugins/sql-expert-dba/scripts/memory_promote.py
cp ~/.agents/plugins/sql-expert-dba/scripts/test_memory_promote.py \
   ~/Library/CodeRepo/AI/claude-plugins/sql-expert-dba/scripts/test_memory_promote.py
```

- [ ] **Step 6: Commit**

```bash
cd ~/.agents/plugins/sql-expert-dba
git add scripts/memory_promote.py scripts/test_memory_promote.py
git commit -m "feat: add memory_promote.py for candidate→approved promotion with sanitize check"
cd ~/Library/CodeRepo/AI/claude-plugins/sql-expert-dba
git add scripts/memory_promote.py scripts/test_memory_promote.py
git commit -m "feat: add memory_promote.py for candidate→approved promotion with sanitize check"
```

---

## Task 10: check_dual_sync.py

**Files:**
- Create: `~/.agents/plugins/sql-expert-dba/scripts/check_dual_sync.py`

注意：此脚本仅在 Codex 版创建（它是跨版本 diff 工具，天然只需一份）。

- [ ] **Step 1: 写失败测试**

在 `test_skill_docs_v2.py` 追加：

```python
def test_check_dual_sync_script_exists(self):
    sync_script = PLUGIN_DIR / "scripts" / "check_dual_sync.py"
    self.assertTrue(sync_script.exists(), "check_dual_sync.py missing")
```

- [ ] **Step 2: 运行测试，确认失败**

```bash
cd ~/.agents/plugins/sql-expert-dba
python3 -m pytest scripts/test_skill_docs_v2.py::TestSkillDocsV2::test_check_dual_sync_script_exists -v
```

期望：FAIL

- [ ] **Step 3: 创建 check_dual_sync.py**

```python
#!/usr/bin/env python3
"""
Cross-version zero-diff validator for sql-expert-dba shared layer.

Validates:
1. Fully-shared files are byte-identical between Codex and Claude versions.
2. Both versions' _shared/ directories have the same file name set.
3. No unsharded tool-variant patterns remain in shared-layer files.

Usage:
    python3 check_dual_sync.py [--codex-root PATH] [--claude-root PATH]

Defaults:
    Codex root:  ~/.agents/plugins/sql-expert-dba
    Claude root: ~/Library/CodeRepo/AI/claude-plugins/sql-expert-dba
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

CODEX_DEFAULT = Path("~/.agents/plugins/sql-expert-dba").expanduser()
CLAUDE_DEFAULT = Path("~/Library/CodeRepo/AI/claude-plugins/sql-expert-dba").expanduser()

# Files that must be byte-identical between both versions
SHARED_LAYER_FILES: list[str] = [
    "skills/_shared/memory-policy.md",
    "skills/_shared/output-contract.md",
    "skills/_shared/dialect-guidelines.md",
    "skills/_shared/missing-input-checklists.md",
    "skills/sql-expert-router/SKILL.md",
    "skills/sql-query-optimizer/SKILL.md",
    "skills/sql-error-diagnostician/SKILL.md",
    "skills/sql-schema-reviewer/SKILL.md",
    "skills/sql-report-query-builder/SKILL.md",
    "scripts/memory_capture.py",
    "scripts/memory_search.py",
    "scripts/memory_promote.py",
    "scripts/sanitize.py",
    "scripts/paths.py",
    "scripts/_frontmatter.py",
]

# Patterns that must NOT appear in shared-layer files (indicate unsharded differences)
FORBIDDEN_PATTERNS: list[str] = [
    "${CLAUDE_PLUGIN_ROOT}",
    "~/.codex/memories",
    "CODEX_HOME",
    "~/.claude/plugins/data",
]


def check_zero_diff(codex_root: Path, claude_root: Path) -> list[str]:
    errors: list[str] = []
    for rel_path in SHARED_LAYER_FILES:
        codex_file = codex_root / rel_path
        claude_file = claude_root / rel_path
        if not codex_file.exists():
            errors.append(f"MISSING in Codex: {rel_path}")
            continue
        if not claude_file.exists():
            errors.append(f"MISSING in Claude: {rel_path}")
            continue
        codex_text = codex_file.read_text(encoding="utf-8")
        claude_text = claude_file.read_text(encoding="utf-8")
        if codex_text != claude_text:
            errors.append(f"DIFF: {rel_path} — not byte-identical between versions")
    return errors


def check_shared_dir_parity(codex_root: Path, claude_root: Path) -> list[str]:
    errors: list[str] = []
    codex_shared = codex_root / "skills" / "_shared"
    claude_shared = claude_root / "skills" / "_shared"
    codex_files = {f.name for f in codex_shared.glob("*.md")} if codex_shared.is_dir() else set()
    claude_files = {f.name for f in claude_shared.glob("*.md")} if claude_shared.is_dir() else set()
    only_codex = codex_files - claude_files
    only_claude = claude_files - codex_files
    if only_codex:
        errors.append(f"_shared/ files only in Codex: {sorted(only_codex)}")
    if only_claude:
        errors.append(f"_shared/ files only in Claude: {sorted(only_claude)}")
    return errors


def check_no_unsharded_patterns(codex_root: Path) -> list[str]:
    errors: list[str] = []
    for rel_path in SHARED_LAYER_FILES:
        f = codex_root / rel_path
        if not f.exists():
            continue
        text = f.read_text(encoding="utf-8")
        for pattern in FORBIDDEN_PATTERNS:
            if pattern in text:
                errors.append(f"UNSHARDED PATTERN '{pattern}' in {rel_path}")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate dual-version zero-diff for sql-expert-dba")
    parser.add_argument("--codex-root", type=Path, default=CODEX_DEFAULT)
    parser.add_argument("--claude-root", type=Path, default=CLAUDE_DEFAULT)
    args = parser.parse_args()

    all_errors: list[str] = []
    all_errors += check_zero_diff(args.codex_root, args.claude_root)
    all_errors += check_shared_dir_parity(args.codex_root, args.claude_root)
    all_errors += check_no_unsharded_patterns(args.codex_root)

    if all_errors:
        print("SYNC CHECK FAILED:")
        for err in all_errors:
            print(f"  ✗ {err}")
        sys.exit(1)
    else:
        print(f"SYNC CHECK PASSED — {len(SHARED_LAYER_FILES)} shared files verified.")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: 运行测试**

```bash
cd ~/.agents/plugins/sql-expert-dba
python3 -m pytest scripts/test_skill_docs_v2.py::TestSkillDocsV2::test_check_dual_sync_script_exists -v
```

期望：PASSED

- [ ] **Step 5: 试运行 check_dual_sync.py（预期此时可能有 DIFF）**

```bash
cd ~/.agents/plugins/sql-expert-dba
python3 scripts/check_dual_sync.py
```

期望：若前序 Task 已全部完成，输出 `SYNC CHECK PASSED`。若有残余 diff，根据输出定位并补同步。

- [ ] **Step 6: Commit**

```bash
cd ~/.agents/plugins/sql-expert-dba
git add scripts/check_dual_sync.py scripts/test_skill_docs_v2.py
git commit -m "feat: add check_dual_sync.py for cross-version zero-diff validation"
```

---

## Task 11: 运行全量测试套件，验收

**Files:** 无新增，仅运行测试

- [ ] **Step 1: 在 Codex 版运行全量测试**

```bash
cd ~/.agents/plugins/sql-expert-dba
python3 -m pytest scripts/ -v --tb=short
```

期望：所有测试 PASSED（包含 test_skill_docs_v2.py、test_sanitize.py、test_memory_capture_sanitize.py、test_memory_promote.py；已删除的 test_auto_memory_runner.py / test_plugin_hooks_manifest.py 不再存在）

- [ ] **Step 2: 在 Claude 版运行全量测试**

```bash
cd ~/Library/CodeRepo/AI/claude-plugins/sql-expert-dba
python3 -m pytest scripts/ -v --tb=short
```

期望：同上，全绿

- [ ] **Step 3: 运行 check_dual_sync.py**

```bash
python3 ~/.agents/plugins/sql-expert-dba/scripts/check_dual_sync.py
```

期望：`SYNC CHECK PASSED — 15 shared files verified.`

- [ ] **Step 4: 手动验收 spec §5 验收标准**

```
1. ✓ hooks/ 目录、auto_memory_runner.py 及相关测试全部移除（Task 1）
2. ✓ _shared/ 含全部分片；主文档两版 zero-diff（Task 2、3；check_dual_sync.py 校验）
3. ✓ 5 个 SKILL.md 两版 zero-diff；记忆读写措辞统一（Task 5；check_dual_sync.py 校验）
4. ✓ memory_promote.py 可列出 candidate 并晋升；含测试（Task 9）
5. ✓ 去敏硬化：命中默认敏感模式时硬拦截；biz-rules 不扫描；含测试（Task 7、8）
6. ✓ paths.py 注释 + README 说明真源位置与重装不丢（Task 6）
7. ✓ check_dual_sync.py 通过；原有测试集全绿（Task 10、11）
```

- [ ] **Step 5: 最终 Commit（如有未提交改动）**

```bash
cd ~/.agents/plugins/sql-expert-dba
git status
# 如有，git add + git commit
cd ~/Library/CodeRepo/AI/claude-plugins/sql-expert-dba
git status
```

---

## 自检：Spec 覆盖验证

| Spec 章节 | 覆盖任务 |
|-----------|---------|
| §2A 删除 Stop hook 文件 | Task 1 |
| §2B _shared/ 分片化 | Task 2、3 |
| §2C 5 个 SKILL.md 统一措辞 | Task 5 |
| §2D paths.py + README 文档化 | Task 6 |
| §2E 测试集对齐（删 + 改 + 新增） | Task 1（删）、Task 5（test_skill_docs_v2.py 新断言）、Task 7-9（新测试） |
| §2F 共有短板修复 | Task 7（sanitize）、Task 8（接入 capture）、Task 9（promote）|
| §3.1 仅产出可见措辞 | Task 3、4、5 |
| §3.2 命中才可见措辞 | Task 5（router SKILL.md） |
| §3.3 晋升出口 | Task 9（memory_promote.py）、Task 5（router 晋升引导） |
| §3.4 去敏硬化 | Task 7（sanitize.py）、Task 8（接入 capture）|
| §4 双版源码同步机制 | Task 10（check_dual_sync.py） |
| §5 验收标准 7 条 | Task 11 |
