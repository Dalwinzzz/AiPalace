# sql-expert-dba Claude 插件迁移 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 Codex 本地插件 sql-expert-dba（v1.1.0）的核心能力迁移为一个独立的 Claude Code 插件（v1：5 技能 + 4 契约 + 全局 memory），经本地 marketplace 安装。

**Architecture:** 独立 Claude 插件，落点 SOT `~/Library/CodeRepo/AI/claude-plugins/sql-expert-dba/`，自身为 git 仓库便于频繁提交。绝大多数文件从 Codex 版 `cp` 原样移植；实质适配仅两处——记忆触发改技能驱动（脚本路径用 `${CLAUDE_PLUGIN_ROOT}`）、`paths.py` 默认 memory 落点改 `~/.claude/plugins/data/sql-expert-dba/memory/`。Codex 版插件不改动。

**Tech Stack:** Claude Code 插件（`.claude-plugin/plugin.json` + `skills/` + `scripts/`）、本地 `marketplace.json`、Python 3 stdlib、Markdown SKILL.md、Git（全局 commit hook 强制 `<type>(<scope>): <subject>` 中文）。

**Source（只读参考，勿改）:** `/Users/dalwin/.codex/plugins/cache/local-plugins/sql-expert-dba/1.1.0/`
**Target（新建）:** `/Users/dalwin/Library/CodeRepo/AI/claude-plugins/`

---

## Scope Check

单一子系统：一个 Claude 插件的 v1 迁移。项目级 `./sql` 索引、`./sql/biz-rules`、守护式自动沉淀 hook 已在 spec 中划入 v2，不在本计划内。本计划可独立产出可安装、可冒烟验证的插件。

## File Structure

**新建于 Target（`~/Library/CodeRepo/AI/claude-plugins/`）：**

- `.claude-plugin/marketplace.json` — 本地 marketplace 清单，列出 sql-expert-dba。
- `sql-expert-dba/.claude-plugin/plugin.json` — 插件清单。
- `sql-expert-dba/skills/{sql-expert-router,sql-query-optimizer,sql-error-diagnostician,sql-schema-reviewer,sql-report-query-builder}/SKILL.md` — 5 技能（移植 + 适配脚本路径 + v2 段落中性化）。
- `sql-expert-dba/skills/_shared/{output-contract,missing-input-checklists,memory-policy,dialect-guidelines}.md` — 4 契约（移植；memory-policy 适配脚本路径）。
- `sql-expert-dba/scripts/{paths.py,_frontmatter.py,memory_search.py,memory_capture.py,memory_index.py}` — 核心脚本（移植；仅 paths.py 适配）。
- `sql-expert-dba/scripts/{test_paths.py,test_memory.py,test_memory_v2.py}` — 测试（移植；仅 test_paths.py 适配）。
- `sql-expert-dba/memory/{glossary/,rules/,templates/,README.md,index.json}` — 内置 seed（原样移植）。
- `sql-expert-dba/assets/{icon.svg,logo.svg}` — 资产（原样移植）。

**运行时可写数据（由脚本首次运行创建）：** `~/.claude/plugins/data/sql-expert-dba/memory/`

**实施日志（提交到 dalwin-workflow 仓库）：** `docs/superpowers/plans/logs/2026-06-03-sql-expert-dba-claude-plugin.md`

---

## Task 1: 脚手架与 git 仓库

**Files:**
- Create dir: `/Users/dalwin/Library/CodeRepo/AI/claude-plugins/`（及子目录）

- [ ] **Step 1: 创建目录骨架**

Run:

```bash
mkdir -p /Users/dalwin/Library/CodeRepo/AI/claude-plugins/.claude-plugin
mkdir -p /Users/dalwin/Library/CodeRepo/AI/claude-plugins/sql-expert-dba/.claude-plugin
mkdir -p /Users/dalwin/Library/CodeRepo/AI/claude-plugins/sql-expert-dba/skills/_shared
mkdir -p /Users/dalwin/Library/CodeRepo/AI/claude-plugins/sql-expert-dba/scripts
mkdir -p /Users/dalwin/Library/CodeRepo/AI/claude-plugins/sql-expert-dba/memory
mkdir -p /Users/dalwin/Library/CodeRepo/AI/claude-plugins/sql-expert-dba/assets
```

Expected: 命令退出码 0。

- [ ] **Step 2: 初始化 git 仓库**

Run:

```bash
cd /Users/dalwin/Library/CodeRepo/AI/claude-plugins && git init && printf '%s\n' '.DS_Store' '__pycache__/' '*.pyc' > .gitignore
```

Expected: `Initialized empty Git repository`，`.gitignore` 创建。

- [ ] **Step 3: 验证目录结构**

Run:

```bash
find /Users/dalwin/Library/CodeRepo/AI/claude-plugins -type d -not -path '*/.git*' | sort
```

Expected: 列出 `claude-plugins`、`.claude-plugin`、`sql-expert-dba` 及其 `.claude-plugin/skills/_shared/scripts/memory/assets` 子目录。

---

## Task 2: 清单文件 plugin.json 与 marketplace.json

**Files:**
- Create: `/Users/dalwin/Library/CodeRepo/AI/claude-plugins/sql-expert-dba/.claude-plugin/plugin.json`
- Create: `/Users/dalwin/Library/CodeRepo/AI/claude-plugins/.claude-plugin/marketplace.json`

- [ ] **Step 1: 写 plugin.json**

写入 `/Users/dalwin/Library/CodeRepo/AI/claude-plugins/sql-expert-dba/.claude-plugin/plugin.json`：

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

- [ ] **Step 2: 写 marketplace.json**

写入 `/Users/dalwin/Library/CodeRepo/AI/claude-plugins/.claude-plugin/marketplace.json`：

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

- [ ] **Step 3: 校验两个 JSON 合法**

Run:

```bash
python3 -m json.tool /Users/dalwin/Library/CodeRepo/AI/claude-plugins/sql-expert-dba/.claude-plugin/plugin.json >/dev/null && echo plugin-ok
python3 -m json.tool /Users/dalwin/Library/CodeRepo/AI/claude-plugins/.claude-plugin/marketplace.json >/dev/null && echo marketplace-ok
```

Expected: 输出 `plugin-ok` 和 `marketplace-ok`。

- [ ] **Step 4: 提交**

```bash
cd /Users/dalwin/Library/CodeRepo/AI/claude-plugins
git add -A
git commit -m "chore(sql-expert-dba): 初始化插件骨架与 marketplace 清单"
```

Expected: commit 成功。

---

## Task 3: 移植核心脚本（原样 cp）

**Files:**
- Create: `sql-expert-dba/scripts/{paths.py,_frontmatter.py,memory_search.py,memory_capture.py,memory_index.py}`

- [ ] **Step 1: 复制 5 个核心脚本**

Run（`SRC`/`DST` 仅本步使用）：

```bash
SRC=/Users/dalwin/.codex/plugins/cache/local-plugins/sql-expert-dba/1.1.0/scripts
DST=/Users/dalwin/Library/CodeRepo/AI/claude-plugins/sql-expert-dba/scripts
for f in paths.py _frontmatter.py memory_search.py memory_capture.py memory_index.py; do cp "$SRC/$f" "$DST/$f"; done
ls -1 "$DST"
```

Expected: 列出 5 个 `.py` 文件。

- [ ] **Step 2: 验证脚本可被 Python 解析**

Run:

```bash
cd /Users/dalwin/Library/CodeRepo/AI/claude-plugins/sql-expert-dba/scripts
python3 -m py_compile paths.py _frontmatter.py memory_search.py memory_capture.py memory_index.py && echo compile-ok
```

Expected: 输出 `compile-ok`。

- [ ] **Step 3: 确认未带入 v2 模块依赖**

Run:

```bash
grep -rn 'project_context\|biz_rules\|auto_memory' /Users/dalwin/Library/CodeRepo/AI/claude-plugins/sql-expert-dba/scripts/*.py | grep -v 'resolve_project_sql_dir\|resolve_biz_rules_dir' || echo "no-v2-dep"
```

Expected: 输出 `no-v2-dep`（仅 paths.py 内的惰性 helper 函数定义，不构成对 v2 脚本的依赖）。

---

## Task 4: 适配 paths.py 与 test_paths.py（测试先行）

**Files:**
- Modify: `sql-expert-dba/scripts/paths.py`
- Create+Modify: `sql-expert-dba/scripts/test_paths.py`

- [ ] **Step 1: 复制 test_paths.py**

Run:

```bash
cp /Users/dalwin/.codex/plugins/cache/local-plugins/sql-expert-dba/1.1.0/scripts/test_paths.py /Users/dalwin/Library/CodeRepo/AI/claude-plugins/sql-expert-dba/scripts/test_paths.py
```

Expected: 文件存在。

- [ ] **Step 2: 改写 test_paths.py 的三处路径断言**

在 `sql-expert-dba/scripts/test_paths.py` 中做三处替换。

替换 A —— `test_codex_home_used_when_custom_env_missing` 整个方法（原断言 CODEX_HOME 生效）改为断言 CODEX_HOME 被忽略、回落 Claude 默认：

旧：

```python
    def test_codex_home_used_when_custom_env_missing(self):
        with tempfile.TemporaryDirectory() as td:
            env = {"CODEX_HOME": str(Path(td) / "codex-home")}
            result = resolve_user_memory_dir(env=env, home=Path(td) / "home")
            self.assertEqual(result, Path(td) / "codex-home" / "memories" / "sql-expert-dba")
```

新：

```python
    def test_codex_home_is_ignored(self):
        with tempfile.TemporaryDirectory() as td:
            env = {"CODEX_HOME": str(Path(td) / "codex-home")}
            result = resolve_user_memory_dir(env=env, home=Path(td) / "home")
            self.assertEqual(
                result,
                Path(td) / "home" / ".claude" / "plugins" / "data" / "sql-expert-dba" / "memory",
            )
```

替换 B —— `test_home_fallback_is_portable` 的断言路径改为 Claude 默认：

旧：

```python
            self.assertEqual(result, Path(td) / "home" / ".codex" / "memories" / "sql-expert-dba")
```

新：

```python
            self.assertEqual(
                result,
                Path(td) / "home" / ".claude" / "plugins" / "data" / "sql-expert-dba" / "memory",
            )
```

替换 C —— `test_resolve_plugin_dir_points_to_plugin_root` 的清单路径改为 `.claude-plugin`：

旧：

```python
        manifest_path = plugin_dir / ".codex-plugin" / "plugin.json"
```

新：

```python
        manifest_path = plugin_dir / ".claude-plugin" / "plugin.json"
```

- [ ] **Step 3: 运行测试，确认失败（适配前 paths.py 仍是旧逻辑）**

Run:

```bash
cd /Users/dalwin/Library/CodeRepo/AI/claude-plugins/sql-expert-dba/scripts
python3 -m unittest test_paths -v
```

Expected: FAIL —— `test_codex_home_is_ignored` 与 `test_home_fallback_is_portable` 失败（当前 paths.py 仍返回 `~/.codex/...`）。

- [ ] **Step 4: 适配 paths.py 的 resolve_user_memory_dir**

在 `sql-expert-dba/scripts/paths.py` 中替换整个 `resolve_user_memory_dir` 函数。

旧：

```python
def resolve_user_memory_dir(
    env: Mapping[str, str] | None = None,
    home: Path | None = None,
) -> Path:
    """Resolve the portable user-level SQL Expert DBA memory directory."""
    current_env = os.environ if env is None else env

    custom_memory_dir = current_env.get("SQL_EXPERT_DBA_MEMORY_DIR")
    if custom_memory_dir:
        return Path(custom_memory_dir).expanduser()

    codex_home = current_env.get("CODEX_HOME")
    if codex_home:
        return Path(codex_home).expanduser() / "memories" / "sql-expert-dba"

    user_home = Path.home() if home is None else Path(home).expanduser()
    return user_home / ".codex" / "memories" / "sql-expert-dba"
```

新：

```python
def resolve_user_memory_dir(
    env: Mapping[str, str] | None = None,
    home: Path | None = None,
) -> Path:
    """Resolve the portable user-level SQL Expert DBA memory directory (Claude)."""
    current_env = os.environ if env is None else env

    custom_memory_dir = current_env.get("SQL_EXPERT_DBA_MEMORY_DIR")
    if custom_memory_dir:
        return Path(custom_memory_dir).expanduser()

    user_home = Path.home() if home is None else Path(home).expanduser()
    return user_home / ".claude" / "plugins" / "data" / "sql-expert-dba" / "memory"
```

- [ ] **Step 5: 运行测试，确认通过**

Run:

```bash
cd /Users/dalwin/Library/CodeRepo/AI/claude-plugins/sql-expert-dba/scripts
python3 -m unittest test_paths -v
```

Expected: PASS —— 所有 test_paths 用例通过（含 env-wins、codex-ignored、home-fallback-claude、project-paths、ensure-v2-layout、plugin-dir）。

- [ ] **Step 6: 提交**

```bash
cd /Users/dalwin/Library/CodeRepo/AI/claude-plugins
git add -A
git commit -m "feat(sql-expert-dba): 移植核心脚本并适配 paths 至 Claude memory 路径"
```

Expected: commit 成功。

---

## Task 5: 移植内置 seed 与 memory 测试

**Files:**
- Create: `sql-expert-dba/memory/{glossary/,rules/,templates/,README.md,index.json}`
- Create: `sql-expert-dba/scripts/{test_memory.py,test_memory_v2.py}`

- [ ] **Step 1: 复制 seed 与两个 memory 测试**

Run:

```bash
SRC=/Users/dalwin/.codex/plugins/cache/local-plugins/sql-expert-dba/1.1.0
DST=/Users/dalwin/Library/CodeRepo/AI/claude-plugins/sql-expert-dba
cp -R "$SRC/memory/." "$DST/memory/"
cp "$SRC/scripts/test_memory.py" "$DST/scripts/test_memory.py"
cp "$SRC/scripts/test_memory_v2.py" "$DST/scripts/test_memory_v2.py"
find "$DST/memory" -type f | sort
```

Expected: 列出 `glossary/glossary-001-covering-index.md`、`rules/rule-001-implicit-type-conversion.md`、`templates/template-001-daily-statistics.md`、`README.md`、`index.json`。

- [ ] **Step 2: 清理可能带入的 .DS_Store**

Run:

```bash
find /Users/dalwin/Library/CodeRepo/AI/claude-plugins/sql-expert-dba/memory -name '.DS_Store' -delete; echo cleaned
```

Expected: 输出 `cleaned`。

- [ ] **Step 3: 运行 memory 测试套件**

Run:

```bash
cd /Users/dalwin/Library/CodeRepo/AI/claude-plugins/sql-expert-dba/scripts
python3 -m unittest test_memory test_memory_v2 -v
```

Expected: PASS —— 两个套件全部通过（用 tmp `--memory-dir`/`SQL_EXPERT_DBA_MEMORY_DIR`，不依赖用户级路径）。

- [ ] **Step 4: 提交**

```bash
cd /Users/dalwin/Library/CodeRepo/AI/claude-plugins
git add -A
git commit -m "feat(sql-expert-dba): 移植内置 seed memory 与 memory 测试套件"
```

Expected: commit 成功。

---

## Task 6: 移植 4 共享契约并适配 memory-policy 脚本路径

**Files:**
- Create: `sql-expert-dba/skills/_shared/{output-contract,missing-input-checklists,memory-policy,dialect-guidelines}.md`

- [ ] **Step 1: 复制 4 契约**

Run:

```bash
SRC=/Users/dalwin/.codex/plugins/cache/local-plugins/sql-expert-dba/1.1.0/skills/_shared
DST=/Users/dalwin/Library/CodeRepo/AI/claude-plugins/sql-expert-dba/skills/_shared
for f in output-contract.md missing-input-checklists.md memory-policy.md dialect-guidelines.md; do cp "$SRC/$f" "$DST/$f"; done
ls -1 "$DST"
```

Expected: 列出 4 个 `.md`。

- [ ] **Step 2: 适配 memory-policy.md 中的脚本路径**

在 `sql-expert-dba/skills/_shared/memory-policy.md` 中，将三处脚本裸名改为插件根路径（共 5 行：第 39、41、106、107、108 行附近）。Run：

```bash
F=/Users/dalwin/Library/CodeRepo/AI/claude-plugins/sql-expert-dba/skills/_shared/memory-policy.md
python3 - "$F" <<'PY'
import sys, re, pathlib
p = pathlib.Path(sys.argv[1])
s = p.read_text(encoding="utf-8")
for name in ("memory_search.py", "memory_capture.py", "memory_index.py"):
    s = s.replace(f"`{name}`", f"`${{CLAUDE_PLUGIN_ROOT}}/scripts/{name}`")
p.write_text(s, encoding="utf-8")
print("patched")
PY
```

Expected: 输出 `patched`。

- [ ] **Step 3: 验证替换生效、无遗留裸名**

Run:

```bash
F=/Users/dalwin/Library/CodeRepo/AI/claude-plugins/sql-expert-dba/skills/_shared/memory-policy.md
grep -n 'CLAUDE_PLUGIN_ROOT' "$F" | head
grep -nE '`memory_(search|capture|index)\.py`' "$F" && echo "STILL-BARE" || echo "no-bare-refs"
```

Expected: 出现多行含 `CLAUDE_PLUGIN_ROOT`；最后输出 `no-bare-refs`。

- [ ] **Step 4: 提交**

```bash
cd /Users/dalwin/Library/CodeRepo/AI/claude-plugins
git add -A
git commit -m "feat(sql-expert-dba): 移植共享契约并将 memory 脚本路径改为 CLAUDE_PLUGIN_ROOT"
```

Expected: commit 成功。

---

## Task 7: 移植 5 技能并适配（脚本路径 + v2 段落中性化）

**Files:**
- Create: `sql-expert-dba/skills/{sql-expert-router,sql-query-optimizer,sql-error-diagnostician,sql-schema-reviewer,sql-report-query-builder}/SKILL.md`

- [ ] **Step 1: 复制 5 技能目录**

Run:

```bash
SRC=/Users/dalwin/.codex/plugins/cache/local-plugins/sql-expert-dba/1.1.0/skills
DST=/Users/dalwin/Library/CodeRepo/AI/claude-plugins/sql-expert-dba/skills
for s in sql-expert-router sql-query-optimizer sql-error-diagnostician sql-schema-reviewer sql-report-query-builder; do
  mkdir -p "$DST/$s"; cp "$SRC/$s/SKILL.md" "$DST/$s/SKILL.md"
done
find "$DST" -name SKILL.md | sort
```

Expected: 列出 5 个 SKILL.md。

- [ ] **Step 2: 机械替换全部技能内的 memory 脚本裸名**

Run（一次覆盖 router/optimizer/schema-reviewer/report-query-builder 内所有 memory 脚本引用）：

```bash
DST=/Users/dalwin/Library/CodeRepo/AI/claude-plugins/sql-expert-dba/skills
python3 - "$DST" <<'PY'
import sys, pathlib
root = pathlib.Path(sys.argv[1])
names = ("memory_search.py", "memory_capture.py", "memory_index.py")
for f in root.rglob("SKILL.md"):
    s = f.read_text(encoding="utf-8")
    for n in names:
        s = s.replace(f"`{n}`", f"`${{CLAUDE_PLUGIN_ROOT}}/scripts/{n}`")
    f.write_text(s, encoding="utf-8")
print("patched")
PY
```

Expected: 输出 `patched`。

- [ ] **Step 3: 中性化 sql-expert-router 的 v2 项目上下文段**

在 `sql-expert-router/SKILL.md` 中，将以下整段（`## v2 项目上下文发现` 起，至下一个标题 `## 输出格式` 之前）

旧：

```text
## v2 项目上下文发现

分诊前检查当前工作目录是否存在 `./sql/`。当存在项目 SQL 上下文，或用户问题提到表、字段、模块时：

1. 构建或校验 `./sql/.index/`，用于定位相关 DDL、EXPLAIN、慢 SQL、表字段和模块索引。
2. 根据 primary_workflow 判断是否加载 `./sql/biz-rules/` 中的 `biz-rules`。
3. 将命中的项目上下文只作为当前项目事实使用，不写入用户级全局 memory。
```

替换为：

```text
## 项目上下文（v2 延后）

项目级 `./sql` 上下文索引与 `./sql/biz-rules` 业务规则属 v2 能力，未随本版（v1）发布。本版分诊仅基于用户显式提供的输入，不读取或构建项目 `./sql/` 目录。
```

- [ ] **Step 4: 中性化 sql-query-optimizer 的项目上下文段**

在 `sql-query-optimizer/SKILL.md` 中，将该段

旧：

```text
如当前项目存在 `./sql/.index/table-index.json`，优先用项目 `table-index.json` 定位相关 DDL、索引定义、慢 SQL 和 EXPLAIN 文件。来自项目上下文的 DDL/index/EXPLAIN 事实必须与用户输入分开标注，避免把项目事实伪装成用户已确认输入。
```

替换为：

```text
> **v1 说明**：项目级 `./sql` 上下文索引为 v2 能力，未随本版发布；本版仅基于用户显式提供的 SQL/DDL/EXPLAIN 分析，不读取项目 `./sql/` 目录。
```

- [ ] **Step 5: 中性化 sql-error-diagnostician 的项目上下文段**

在 `sql-error-diagnostician/SKILL.md` 中，将该段

旧：

```text
当报错信息、SQL 或栈信息中出现表名、字段名、约束名、索引名、SQLSTATE 或错误码时，先在项目上下文中查找相关表、字段、constraints、SQLSTATE/error codes 映射：

- 使用 `./sql/.index/` 定位 DDL、约束、索引和错误相关说明。
- 使用 `./sql/biz-rules/` 查找项目内约束含义、字段语义和业务规则。
- 项目上下文命中项必须标注来源，不得写入用户级全局 memory。
```

替换为：

```text
> **v1 说明**：项目级 `./sql` 上下文与 `./sql/biz-rules` 为 v2 能力，未随本版发布；本版仅基于用户显式提供的报错全文、SQL 和 DDL 诊断，不读取项目 `./sql/` 目录。
```

- [ ] **Step 6: 中性化 sql-schema-reviewer 的两处 v2 引用**

在 `sql-schema-reviewer/SKILL.md` 中做两处替换。

替换 A —— Step 1 内的项目 schema context 段：

旧：

```text
如当前项目存在 `./sql/.index/table-index.json`、DDL 文件或其他现有 `./sql/` schema context，评审提交的 DDL 前必须先对照现有 `./sql/` schema context，检查表名、字段、索引、约束和表关系是否与项目现状冲突。来自项目上下文的事实必须与用户输入分开标注。
```

新：

```text
> **v1 说明**：项目级 `./sql` schema context 为 v2 能力，未随本版发布；本版仅评审用户显式提交的 DDL，不读取项目 `./sql/` 目录。
```

替换 B —— `### v2 项目业务规则沉淀` 小节（该小节标题行及其下一段正文）：

旧：

```text
### v2 项目业务规则沉淀

当评审确认了项目内稳定的表关系、字段语义、主外键含义或模块归属时，将这些项目事实写入 `./sql/biz-rules/` 的 `biz-rules`。项目业务规则沉淀保持真实表名和字段名；不要把这些项目表关系和字段语义写入用户级全局 memory。
```

新：

```text
### 项目业务规则沉淀（v2 延后）

`./sql/biz-rules/` 项目业务规则沉淀为 v2 能力，未随本版发布。本版仅做全局 memory 沉淀（见下）。
```

- [ ] **Step 7: 中性化 sql-report-query-builder 的项目上下文段**

在 `sql-report-query-builder/SKILL.md` 中，将该段（含其后三条 `./sql/...` 列表项与口径冲突说明）

旧：

```text
如当前项目存在 `./sql/` 或相关索引，生成 SQL 前必须读取项目 SQL 索引和业务规则索引；如果 `./sql/` 或相关索引不存在，则基于用户已提供的业务需求、DDL 和表关系降级生成，并在 `待确认/推断` 中说明缺口：

- `./sql/.index/table-index.json`：按表查找 DDL、字段、索引、表关系、EXPLAIN 和慢 SQL 上下文。
- `./sql/biz-rules/table-index.json`：按表查找指标、字段语义、过滤规则和关联关系。
- `./sql/biz-rules/module-index.json`：按业务模块查找指标口径、维度定义和报表模板。
- 如命中规则之间存在 `口径冲突`，必须停止生成最终 SQL，列出冲突规则并请用户确认采用哪一个口径。
```

替换为：

```text
> **v1 说明**：项目级 `./sql` 索引与 `./sql/biz-rules` 业务规则为 v2 能力，未随本版发布；本版基于用户显式提供的业务需求、DDL 和表关系生成 SQL，口径不明确时按下方「口径澄清」反问用户。
```

- [ ] **Step 8: 验证全部技能无遗留裸脚本名、无残留 v2 硬调用**

Run:

```bash
DST=/Users/dalwin/Library/CodeRepo/AI/claude-plugins/sql-expert-dba/skills
echo "--- 残留裸脚本名（应无）---"; grep -rnE '`memory_(search|capture|index)\.py`' "$DST" && echo "STILL-BARE" || echo "no-bare-refs"
echo "--- 残留 v2 硬调用（应无 .index/ 或 biz-rules 索引文件构建指令）---"; grep -rnE '\./sql/\.index/|biz-rules/table-index|biz-rules/module-index' "$DST" && echo "STILL-V2" || echo "no-v2-hardcalls"
echo "--- CLAUDE_PLUGIN_ROOT 已注入文件数 ---"; grep -rl 'CLAUDE_PLUGIN_ROOT' "$DST" | wc -l
```

Expected: `no-bare-refs`；`no-v2-hardcalls`；最后一行计数 ≥ 4（router/optimizer/schema-reviewer/report-query-builder 至少各一处）。

- [ ] **Step 9: 校验 5 个 SKILL.md frontmatter 完整**

Run:

```bash
DST=/Users/dalwin/Library/CodeRepo/AI/claude-plugins/sql-expert-dba/skills
for s in sql-expert-router sql-query-optimizer sql-error-diagnostician sql-schema-reviewer sql-report-query-builder; do
  head -3 "$DST/$s/SKILL.md" | grep -q "name: $s" && echo "$s frontmatter-ok" || echo "$s FRONTMATTER-BAD"
done
```

Expected: 5 行均为 `<name> frontmatter-ok`。

- [ ] **Step 10: 提交**

```bash
cd /Users/dalwin/Library/CodeRepo/AI/claude-plugins
git add -A
git commit -m "feat(sql-expert-dba): 移植 5 技能并适配脚本路径与 v2 段落"
```

Expected: commit 成功。

---

## Task 8: 移植资产

**Files:**
- Create: `sql-expert-dba/assets/{icon.svg,logo.svg}`

- [ ] **Step 1: 复制资产**

Run:

```bash
SRC=/Users/dalwin/.codex/plugins/cache/local-plugins/sql-expert-dba/1.1.0/assets
DST=/Users/dalwin/Library/CodeRepo/AI/claude-plugins/sql-expert-dba/assets
cp "$SRC/icon.svg" "$DST/icon.svg"; cp "$SRC/logo.svg" "$DST/logo.svg"
ls -1 "$DST"
```

Expected: 列出 `icon.svg`、`logo.svg`。

- [ ] **Step 2: 提交**

```bash
cd /Users/dalwin/Library/CodeRepo/AI/claude-plugins
git add -A
git commit -m "chore(sql-expert-dba): 移植插件图标资产"
```

Expected: commit 成功。

---

## Task 9: 本地 marketplace 安装与冒烟验证

**Files:**
- 只读验证：整个 `sql-expert-dba/` 插件

- [ ] **Step 1: 全量脚本测试再跑一遍（回归）**

Run:

```bash
cd /Users/dalwin/Library/CodeRepo/AI/claude-plugins/sql-expert-dba/scripts
python3 -m unittest test_paths test_memory test_memory_v2 -v 2>&1 | tail -5
```

Expected: 末尾出现 `OK`，无 FAIL/ERROR。

- [ ] **Step 2: 添加本地 marketplace**

Run:

```bash
claude plugin marketplace add /Users/dalwin/Library/CodeRepo/AI/claude-plugins
```

Expected: 成功注册 marketplace `dalwin-local-plugins`（命令退出码 0）。若提示已存在，运行 `claude plugin marketplace update dalwin-local-plugins`。

- [ ] **Step 3: 安装插件**

Run:

```bash
claude plugin install sql-expert-dba@dalwin-local-plugins
```

Expected: 安装成功，退出码 0。

- [ ] **Step 4: 确认插件与 5 技能被发现**

Run:

```bash
claude plugin list 2>&1 | grep -i sql-expert-dba
```

Expected: 输出包含 `sql-expert-dba`（已安装/启用）。

> 交互冒烟（人工，在 Claude 会话内执行，非脚本）：
> - 输入「优化这条 SQL：`SELECT * FROM orders WHERE DATE(created_at)='2024-01-01'`」→ 应触发 `sql-query-optimizer`，输出符合六段式契约（任务判断/已确认/待确认推断/主输出含反模式+索引建议+改写/验证建议/默认省略学习段）。
> - 输入「这段报错什么原因：ERROR 1062 (23000): Duplicate entry」→ 应触发 `sql-error-diagnostician`，给出根因排序（指向唯一键冲突）+ 修复路径。
> - 输入「记下来这个经验」→ 技能调 `${CLAUDE_PLUGIN_ROOT}/scripts/memory_capture.py`，在 `~/.claude/plugins/data/sql-expert-dba/memory/` 写入 approved 条目并更新 index.json。

- [ ] **Step 5: 验证运行时 memory 目录可被创建并写入（脚本级，不依赖交互）**

Run:

```bash
TMPM=$(mktemp -d)
SQL_EXPERT_DBA_MEMORY_DIR="$TMPM/mem" python3 /Users/dalwin/Library/CodeRepo/AI/claude-plugins/sql-expert-dba/scripts/memory_index.py --memory-dir "$TMPM/mem" --rebuild >/dev/null 2>&1
find "$TMPM/mem" -maxdepth 2 -type d | sort
rm -rf "$TMPM"
```

Expected: 出现 `approved/{glossary,rules,templates,cases}` 与 `candidates/...` 的 v2 目录结构（证明 `ensure_global_memory_dirs` 在 Claude 路径逻辑下正常）。

---

## Task 10: 实施日志（提交到 dalwin-workflow）

**Files:**
- Create: `/Users/dalwin/Documents/AI/dalwin-workflow/docs/superpowers/plans/logs/2026-06-03-sql-expert-dba-claude-plugin.md`

- [ ] **Step 1: 写实施日志**

写入该文件，按以下模板，将「实测」占位处替换为本次执行验证到的真实结果：

```markdown
# sql-expert-dba Claude 插件迁移实施日志 — 2026-06-03

> 依据：`docs/superpowers/specs/2026-06-03-sql-expert-dba-claude-plugin-design.md`
> 计划：`docs/superpowers/plans/2026-06-03-sql-expert-dba-claude-plugin.md`

## 成果

- 独立 Claude 插件：`/Users/dalwin/Library/CodeRepo/AI/claude-plugins/sql-expert-dba/`（自身 git 仓库）。
- 本地 marketplace：`dalwin-local-plugins`。
- 安装命令：
  - `claude plugin marketplace add /Users/dalwin/Library/CodeRepo/AI/claude-plugins`
  - `claude plugin install sql-expert-dba@dalwin-local-plugins`

## 范围

- v1 含：5 技能（router + 4 专家）+ 4 契约 + 全局 memory（search/capture/index + seed）。
- v2 延后：项目 `./sql` 索引、`./sql/biz-rules`、守护式自动沉淀 hook。

## 适配

- 记忆触发改技能驱动：技能内调 `${CLAUDE_PLUGIN_ROOT}/scripts/memory_*.py`，无全局 hook。
- `paths.py` 默认 memory 落点：`~/.claude/plugins/data/sql-expert-dba/memory/`，去掉 CODEX_HOME 分支，保留 `SQL_EXPERT_DBA_MEMORY_DIR` 覆盖。
- 5 技能 v2 项目上下文段已中性化为「v2 延后」说明。

## 验证结果（实测）

- `python3 -m unittest test_paths test_memory test_memory_v2`：实测（应为 OK，0 fail）。
- `claude plugin list` 含 sql-expert-dba：实测。
- 冒烟「优化 SQL」→ 触发 sql-query-optimizer，六段式输出：实测。
- 冒烟「ERROR 1062」→ 触发 sql-error-diagnostician，根因排序：实测。
- 运行时 memory v2 目录创建：实测。

## 对账提醒

- 与 Codex 版 sql-expert-dba 为两份独立知识源；后续若需单源化或对账，见 spec §12 v2 计划。
- 插件配置变更后需重启 Claude 会话加载。
```

- [ ] **Step 2: 提交日志到 dalwin-workflow**

```bash
cd /Users/dalwin/Documents/AI/dalwin-workflow
git add docs/superpowers/plans/logs/2026-06-03-sql-expert-dba-claude-plugin.md
git commit -m "docs(dalwin-workflow): 记录 sql-expert-dba Claude 插件迁移实施"
```

Expected: commit 成功。

---

## Plan Completion Verification

- [ ] **Step 1: 插件仓库提交历史完整**

Run:

```bash
git -C /Users/dalwin/Library/CodeRepo/AI/claude-plugins log --oneline
```

Expected: 含骨架、脚本+paths、seed、契约、5 技能、资产等若干 feat/chore 提交。

- [ ] **Step 2: 最终结构核对**

Run:

```bash
find /Users/dalwin/Library/CodeRepo/AI/claude-plugins -type f -not -path '*/.git/*' -name '*.md' -o -type f -not -path '*/.git/*' -name '*.json' -o -type f -not -path '*/.git/*' -name '*.py' | sort
```

Expected: 含 `marketplace.json`、`plugin.json`、5 个 `SKILL.md`、4 个 `_shared/*.md`、5 个核心 `.py` + 3 个 `test_*.py`、`memory/index.json` + seed `.md`。

## Rollback Summary

- 卸载插件：`claude plugin uninstall sql-expert-dba@dalwin-local-plugins`；移除 marketplace：`claude plugin marketplace remove dalwin-local-plugins`。
- 删除插件源：`rm -rf /Users/dalwin/Library/CodeRepo/AI/claude-plugins`（独立仓库，不影响其它 SOT）。
- 运行时数据：`rm -rf ~/.claude/plugins/data/sql-expert-dba`。
- Codex 版插件全程未改动，无需回滚。
```
