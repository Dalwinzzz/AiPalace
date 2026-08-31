# sql-expert-dba Claude 插件 v2 迭代 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在已交付的 Claude 插件 v1（`1.0.0`）之上补齐 v2 三块能力——A 项目 `./sql` 上下文索引、B `./sql/biz-rules` 业务规则、C 守护式自动沉淀 hook（command 型 `Stop` + `decision:block` 条件化注入），并还原 5 技能的 v2 段落，升版 `1.1.0`。

**Architecture:** A/B 脚本从 Codex 版原样 `cp` 平移（纯 stdlib，依赖 `paths`/`_frontmatter` 均已就绪，用项目级 `./sql` 路径，无需 `${CLAUDE_PLUGIN_ROOT}` 适配）。C 把 Codex 的 `auto_memory_runner.py`（`--input` 结构化文件）**重写**为 Claude Stop hook 脚本（读 stdin、读 transcript 门控、输出 `decision` JSON、capture-log 幂等），并新建 `hooks/hooks.json`。技能文档还原 = 把 v1 中性化段落改回 Codex 原版 v2 段落，以 `test_skill_docs_v2.py` 为红线。

**Tech Stack:** Python 3 stdlib、Claude Code 插件（`.claude-plugin/plugin.json` + `hooks/hooks.json` + `skills/` + `scripts/`）、unittest、Git（中文 commit `<type>(<scope>): <subject>`）。

**Source（只读参考）:** `/Users/dalwin/.codex/plugins/cache/local-plugins/sql-expert-dba/1.1.0/`
**Target（修改）:** `/Users/dalwin/Library/CodeRepo/AI/claude-plugins/sql-expert-dba/`
**Spec:** `docs/superpowers/specs/2026-06-04-sql-expert-dba-claude-plugin-v2-design.md`

---

## Scope Check

单一子系统：一个 Claude 插件的 v2 增量。三块能力 A/B/C 同属该插件、共享 `paths.py`/memory 子系统，耦合紧密，应在同一计划内交付。D 跨工具对账已在 spec 划入 v3，不在本计划。本计划可独立产出可安装、可回归验证的 `1.1.0`。

## File Structure

**Target 内新建：**
- `scripts/project_context_index.py` / `project_context_search.py` — 项目 `./sql` 索引构建与查询（cp）。
- `scripts/biz_rules_capture.py` / `biz_rules_search.py` / `biz_rules_git_guard.py` — 业务规则沉淀/查询/git 保护（cp）。
- `scripts/auto_memory_runner.py` — **重写**为 Claude Stop hook 守护脚本。
- `scripts/test_project_context.py` / `test_biz_rules.py` — A/B 测试（cp）。
- `scripts/test_skill_docs_v2.py` — 技能文档 v2 验收（cp）。
- `scripts/test_auto_memory_runner.py` — **重写**为 Stop hook 测试。
- `hooks/hooks.json` — Stop / command hook 声明。

**Target 内修改：**
- `.claude-plugin/plugin.json` — version `1.1.0` + description + `hooks` 字段。
- `skills/sql-expert-router|sql-query-optimizer|sql-error-diagnostician|sql-schema-reviewer|sql-report-query-builder/SKILL.md` — 还原 v2 段落。
- `skills/_shared/output-contract.md` — 还原 v2 可选子段落。
- `skills/_shared/memory-policy.md` — 修正第 8 行 Codex 路径残留。

**dalwin-workflow 内新建：**
- `docs/superpowers/plans/logs/2026-06-04-sql-expert-dba-claude-plugin-v2.md` — 实施日志。

---

## Task 1: 平移 A 项目上下文脚本与测试

**Files:**
- Create: `scripts/{project_context_index.py, project_context_search.py, test_project_context.py}`

- [ ] **Step 1: 复制 A 的 2 脚本 + 1 测试**

Run:

```bash
SRC=/Users/dalwin/.codex/plugins/cache/local-plugins/sql-expert-dba/1.1.0/scripts
DST=/Users/dalwin/Library/CodeRepo/AI/claude-plugins/sql-expert-dba/scripts
for f in project_context_index.py project_context_search.py test_project_context.py; do cp "$SRC/$f" "$DST/$f"; done
ls -1 "$DST" | grep project_context
```

Expected: 列出 `project_context_index.py`、`project_context_search.py`、`test_project_context.py`。

- [ ] **Step 2: 编译校验 + 确认依赖均已就绪**

Run:

```bash
cd /Users/dalwin/Library/CodeRepo/AI/claude-plugins/sql-expert-dba/scripts
python3 -m py_compile project_context_index.py project_context_search.py && echo compile-ok
grep -nE '^from |^import ' project_context_index.py project_context_search.py | grep -vE 'argparse|hashlib|json|^.*:import re|sys|datetime|pathlib|typing|from __future__'
```

Expected: `compile-ok`；第二条仅显示对 `paths`（`resolve_project_sql_dir`）和 `project_context_index`（同包）的 import，无缺失依赖。

- [ ] **Step 3: 运行 A 测试**

Run:

```bash
cd /Users/dalwin/Library/CodeRepo/AI/claude-plugins/sql-expert-dba/scripts
python3 -m unittest test_project_context -v 2>&1 | tail -5
```

Expected: 末尾 `OK`，无 FAIL/ERROR（测试用 tmp `--project-dir`，不依赖用户路径）。

- [ ] **Step 4: 提交**

```bash
cd /Users/dalwin/Library/CodeRepo/AI/claude-plugins
git add -A && git commit -m "feat(sql-expert-dba): 移植项目 ./sql 上下文索引脚本与测试"
```

Expected: commit 成功。

---

## Task 2: 平移 B 业务规则脚本与测试

**Files:**
- Create: `scripts/{biz_rules_capture.py, biz_rules_search.py, biz_rules_git_guard.py, test_biz_rules.py}`

- [ ] **Step 1: 复制 B 的 3 脚本 + 1 测试**

Run:

```bash
SRC=/Users/dalwin/.codex/plugins/cache/local-plugins/sql-expert-dba/1.1.0/scripts
DST=/Users/dalwin/Library/CodeRepo/AI/claude-plugins/sql-expert-dba/scripts
for f in biz_rules_capture.py biz_rules_search.py biz_rules_git_guard.py test_biz_rules.py; do cp "$SRC/$f" "$DST/$f"; done
ls -1 "$DST" | grep biz_rules
```

Expected: 列出 4 个 `biz_rules*` 文件。

- [ ] **Step 2: 编译校验 + 确认依赖**

Run:

```bash
cd /Users/dalwin/Library/CodeRepo/AI/claude-plugins/sql-expert-dba/scripts
python3 -m py_compile biz_rules_capture.py biz_rules_search.py biz_rules_git_guard.py && echo compile-ok
```

Expected: `compile-ok`（依赖 `_frontmatter`、`paths`、`biz_rules_git_guard` 同包均已就绪）。

- [ ] **Step 3: 运行 B 测试**

Run:

```bash
cd /Users/dalwin/Library/CodeRepo/AI/claude-plugins/sql-expert-dba/scripts
python3 -m unittest test_biz_rules -v 2>&1 | tail -5
```

Expected: 末尾 `OK`。若个别用例依赖 `git` 用户配置，确认 `git config user.email/user.name` 已设置（本机已设 czw）。

- [ ] **Step 4: 提交**

```bash
cd /Users/dalwin/Library/CodeRepo/AI/claude-plugins
git add -A && git commit -m "feat(sql-expert-dba): 移植 ./sql/biz-rules 业务规则脚本与测试"
```

Expected: commit 成功。

---

## Task 3: 重写 C 守护脚本 auto_memory_runner.py（TDD）

**Files:**
- Create: `scripts/auto_memory_runner.py`（全新）
- Create: `scripts/test_auto_memory_runner.py`（全新，覆盖旧文件）

- [ ] **Step 1: 写失败测试 `test_auto_memory_runner.py`**

写入下列完整内容（测 Claude Stop hook 接口：stdin 输入 + decision 输出 + 门控 + 幂等）：

```python
#!/usr/bin/env python3
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent
RUNNER = SCRIPTS_DIR / "auto_memory_runner.py"


def run_hook(hook_input: dict, memory_dir: Path) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["SQL_EXPERT_DBA_MEMORY_DIR"] = str(memory_dir)
    return subprocess.run(
        [sys.executable, str(RUNNER)],
        input=json.dumps(hook_input),
        capture_output=True,
        text=True,
        env=env,
    )


def write_transcript(td: Path, text: str) -> Path:
    path = td / "transcript.jsonl"
    path.write_text(text, encoding="utf-8")
    return path


class TestAutoMemoryRunnerHook(unittest.TestCase):
    def test_silent_when_not_sql_task(self):
        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td)
            transcript = write_transcript(tdp, "user: how is the weather today\nassistant: sunny")
            result = run_hook(
                {"session_id": "s1", "transcript_path": str(transcript), "stop_hook_active": False},
                tdp / "memory",
            )
            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stdout.strip(), "")

    def test_block_when_sql_task_and_not_prompted(self):
        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td)
            transcript = write_transcript(
                tdp, "user: 帮我优化这条慢 SQL，EXPLAIN 显示 using filesort\nassistant: ..."
            )
            result = run_hook(
                {"session_id": "s2", "transcript_path": str(transcript), "stop_hook_active": False},
                tdp / "memory",
            )
            self.assertEqual(result.returncode, 0)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["decision"], "block")
            self.assertIn("memory_capture.py", payload["reason"])

    def test_skill_name_in_transcript_counts_as_sql(self):
        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td)
            transcript = write_transcript(tdp, "assistant invoked skill sql-query-optimizer for the user")
            result = run_hook(
                {"session_id": "s3", "transcript_path": str(transcript), "stop_hook_active": False},
                tdp / "memory",
            )
            payload = json.loads(result.stdout)
            self.assertEqual(payload["decision"], "block")

    def test_silent_when_stop_hook_active(self):
        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td)
            transcript = write_transcript(tdp, "user: 优化 SQL 索引\nassistant: ...")
            result = run_hook(
                {"session_id": "s4", "transcript_path": str(transcript), "stop_hook_active": True},
                tdp / "memory",
            )
            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stdout.strip(), "")

    def test_idempotent_second_call_is_silent(self):
        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td)
            transcript = write_transcript(tdp, "user: SQL 死锁 deadlock 诊断\nassistant: ...")
            hook = {"session_id": "s5", "transcript_path": str(transcript), "stop_hook_active": False}
            first = run_hook(hook, tdp / "memory")
            self.assertEqual(json.loads(first.stdout)["decision"], "block")
            second = run_hook(hook, tdp / "memory")
            self.assertEqual(second.returncode, 0)
            self.assertEqual(second.stdout.strip(), "")

    def test_silent_when_transcript_missing(self):
        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td)
            result = run_hook(
                {"session_id": "s6", "transcript_path": str(tdp / "nope.jsonl"), "stop_hook_active": False},
                tdp / "memory",
            )
            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stdout.strip(), "")

    def test_silent_when_empty_stdin(self):
        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td)
            env = os.environ.copy()
            env["SQL_EXPERT_DBA_MEMORY_DIR"] = str(tdp / "memory")
            result = subprocess.run(
                [sys.executable, str(RUNNER)], input="", capture_output=True, text=True, env=env
            )
            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stdout.strip(), "")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 运行测试，确认失败**

Run:

```bash
cd /Users/dalwin/Library/CodeRepo/AI/claude-plugins/sql-expert-dba/scripts
python3 -m unittest test_auto_memory_runner -v 2>&1 | tail -8
```

Expected: FAIL/ERROR（当前 `auto_memory_runner.py` 仍是 Codex `--input` 版，读 stdin 接口不存在）。

- [ ] **Step 3: 重写 `auto_memory_runner.py`**

写入下列完整内容（覆盖旧文件）：

```python
#!/usr/bin/env python3
"""Claude Stop hook: guarded SQL Expert DBA memory-capture reminder.

Reads the Stop hook JSON from stdin, inspects the transcript to decide whether
this session was a SQL Expert DBA task, and—only when it was and no reminder has
fired yet this session—emits a Stop ``decision: block`` reminder nudging the
model to run memory_capture.py. Otherwise it stays silent (exit 0, no output),
so non-SQL sessions get zero prompt injection.
"""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from paths import ensure_global_memory_dirs, resolve_user_memory_dir


SQL_TASK_SIGNAL_RE = re.compile(
    r"("
    r"\bselect\b|\bwith\b|\binsert\b|\bupdate\b|\bdelete\b|\bcreate\s+table\b|"
    r"\balter\s+table\b|\bdrop\s+table\b|\bexplain\b|\bsqlstate\b|"
    r"\berror\b|\bsyntax\b|\bdeadlock\b|\btimeout\b|\bduplicate\b|"
    r"\bforeign\s+key\b|\bunique\b|"
    r"SQL|DDL|执行计划|慢\s*SQL|慢查询|报错|错误码|死锁|锁等待|"
    r"索引|表结构|建表|查询优化|报表|统计|对账|汇总|业务\s*SQL"
    r")",
    re.IGNORECASE,
)

SKILL_SIGNAL_RE = re.compile(
    r"sql-(expert-router|query-optimizer|error-diagnostician|schema-reviewer|report-query-builder)",
    re.IGNORECASE,
)

GUARD_EVENT = "stop-guard-prompted"

REMINDER = (
    "本轮疑似 SQL Expert DBA 任务。若产生了稳定、可复用的经验或结论，且本轮尚未沉淀："
    "请按 memory-policy 的 5 硬门槛（可复用 / 有证据 / 有边界 / 可结构化 / 可去敏）评估；"
    "全部满足时，先调用 ${CLAUDE_PLUGIN_ROOT}/scripts/memory_search.py 去重，"
    "再调用 ${CLAUDE_PLUGIN_ROOT}/scripts/memory_capture.py --capture-mode auto_hook（仅写 candidate），"
    "并强制去敏（不得含真实表名、字段名或敏感数据，必要时用 --forbidden-token）。"
    "若不值得沉淀，或本轮已沉淀，请直接结束、无需额外输出。"
)


def read_hook_input() -> dict:
    try:
        raw = sys.stdin.read()
    except Exception:
        return {}
    raw = raw.strip()
    if not raw:
        return {}
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def read_transcript(transcript_path: object) -> str:
    if not transcript_path:
        return ""
    try:
        return Path(str(transcript_path)).expanduser().read_text(
            encoding="utf-8", errors="replace"
        )
    except OSError:
        return ""


def is_sql_task(transcript: str) -> bool:
    return bool(SQL_TASK_SIGNAL_RE.search(transcript) or SKILL_SIGNAL_RE.search(transcript))


def already_prompted(memory_dir: Path, session_id: str) -> bool:
    if not session_id:
        return False
    log_path = memory_dir / "capture-log.jsonl"
    if not log_path.exists():
        return False
    try:
        lines = log_path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return False
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if record.get("event") == GUARD_EVENT and record.get("session_id") == session_id:
            return True
    return False


def mark_prompted(memory_dir: Path, session_id: str) -> None:
    record = {
        "event": GUARD_EVENT,
        "session_id": session_id,
        "ts": datetime.now(timezone.utc).isoformat(),
    }
    with (memory_dir / "capture-log.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def main() -> None:
    hook_input = read_hook_input()

    # Never re-enter our own Stop-continuation loop.
    if hook_input.get("stop_hook_active"):
        return

    transcript = read_transcript(hook_input.get("transcript_path"))

    # Gate: only SQL Expert DBA sessions are eligible for the reminder.
    if not is_sql_task(transcript):
        return

    session_id = str(hook_input.get("session_id", ""))
    memory_dir = resolve_user_memory_dir()
    ensure_global_memory_dirs(memory_dir)

    # At most one reminder per session.
    if already_prompted(memory_dir, session_id):
        return

    mark_prompted(memory_dir, session_id)
    print(json.dumps({"decision": "block", "reason": REMINDER}, ensure_ascii=False))


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: 运行测试，确认通过**

Run:

```bash
cd /Users/dalwin/Library/CodeRepo/AI/claude-plugins/sql-expert-dba/scripts
python3 -m unittest test_auto_memory_runner -v 2>&1 | tail -10
```

Expected: `OK`，7 个用例全过。

- [ ] **Step 5: 提交**

```bash
cd /Users/dalwin/Library/CodeRepo/AI/claude-plugins
git add -A && git commit -m "feat(sql-expert-dba): 重写 auto_memory_runner 为 Claude Stop hook 守护脚本"
```

Expected: commit 成功。

---

## Task 4: hooks.json 与 plugin.json 升级

**Files:**
- Create: `hooks/hooks.json`
- Modify: `.claude-plugin/plugin.json`

- [ ] **Step 1: 创建 `hooks/hooks.json`**

Run:

```bash
mkdir -p /Users/dalwin/Library/CodeRepo/AI/claude-plugins/sql-expert-dba/hooks
```

写入 `/Users/dalwin/Library/CodeRepo/AI/claude-plugins/sql-expert-dba/hooks/hooks.json`：

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

- [ ] **Step 2: 修改 `plugin.json`**（version 1.1.0 + description + hooks 字段）

将 `version` 改为 `1.1.0`；`description` 改为含 v2 能力表述；在 `keywords` 后增加 `"hooks": "./hooks/hooks.json"`。最终内容：

```json
{
  "name": "sql-expert-dba",
  "version": "1.1.0",
  "description": "面向 MySQL/PostgreSQL 与通用 SQL 的分析型 DBA 助手：查询优化、报错诊断、Schema 评审、业务报表 SQL 生成，配套去敏的便携式全局 SQL memory、项目级 ./sql 上下文索引、./sql/biz-rules 业务规则沉淀，以及守护式自动沉淀（Stop hook）。不直连数据库、不执行 SQL。",
  "author": { "name": "dalwin" },
  "license": "MIT",
  "keywords": ["sql", "mysql", "postgresql", "query-optimization", "schema-review", "reporting-sql", "dba"],
  "hooks": "./hooks/hooks.json"
}
```

- [ ] **Step 3: 校验 JSON 合法**

Run:

```bash
python3 -m json.tool /Users/dalwin/Library/CodeRepo/AI/claude-plugins/sql-expert-dba/hooks/hooks.json >/dev/null && echo hooks-ok
python3 -m json.tool /Users/dalwin/Library/CodeRepo/AI/claude-plugins/sql-expert-dba/.claude-plugin/plugin.json >/dev/null && echo plugin-ok
```

Expected: `hooks-ok` 与 `plugin-ok`。

- [ ] **Step 4: 提交**

```bash
cd /Users/dalwin/Library/CodeRepo/AI/claude-plugins
git add -A && git commit -m "feat(sql-expert-dba): 接线 Stop hook 并升版 1.1.0"
```

Expected: commit 成功。

---

## Task 5: 还原 5 技能 + output-contract 的 v2 段落，修正 memory-policy 残留

**Files:**
- Create: `scripts/test_skill_docs_v2.py`（cp，作验收红线）
- Modify: 5 个 `skills/sql-*/SKILL.md`、`skills/_shared/output-contract.md`、`skills/_shared/memory-policy.md`

**还原原则**：对每个文件，将 v1 中性化的「v2 延后」段落，改回 Codex 源对应文件（`$SRC/skills/...`）的 v2 段落原文；其中 memory 脚本引用保持 `${CLAUDE_PLUGIN_ROOT}/scripts/`（与 v1 既有约定一致），新引入的 `project_context_*`/`biz_rules_*` 脚本引用也写 `${CLAUDE_PLUGIN_ROOT}/scripts/`。验收以 `test_skill_docs_v2.py` 为准。

- [ ] **Step 1: 复制验收测试**

Run:

```bash
cp /Users/dalwin/.codex/plugins/cache/local-plugins/sql-expert-dba/1.1.0/scripts/test_skill_docs_v2.py /Users/dalwin/Library/CodeRepo/AI/claude-plugins/sql-expert-dba/scripts/test_skill_docs_v2.py
```

- [ ] **Step 2: 运行验收测试，确认失败（还原前）**

Run:

```bash
cd /Users/dalwin/Library/CodeRepo/AI/claude-plugins/sql-expert-dba/scripts
python3 -m unittest test_skill_docs_v2 -v 2>&1 | tail -15
```

Expected: 多个 FAIL（router/report-builder/schema-reviewer/output-contract 的 v2 文本因 v1 中性化而缺失）。记下失败的具体断言作为还原清单。

- [ ] **Step 3: 逐文件还原 v2 段落（对照 Codex 源 Edit）**

对下列每个文件，读 Codex 源原文与当前 Claude 文件，将中性化段落 Edit 还原（脚本路径用 `${CLAUDE_PLUGIN_ROOT}/scripts/`）：

| Claude 文件 | Codex 源（还原内容来源） | 还原段落 |
|---|---|---|
| `skills/sql-expert-router/SKILL.md` | `$SRC/skills/sql-expert-router/SKILL.md` | 「## v2 项目上下文发现」：检查 `./sql/`、构建/校验 `./sql/.index/`、按 workflow 加载 `./sql/biz-rules/` |
| `skills/sql-query-optimizer/SKILL.md` | `$SRC/skills/sql-query-optimizer/SKILL.md` | 优先用 `./sql/.index/table-index.json` 定位 DDL/索引/慢 SQL/EXPLAIN，项目事实与用户输入分开标注 |
| `skills/sql-error-diagnostician/SKILL.md` | `$SRC/skills/sql-error-diagnostician/SKILL.md` | 用 `./sql/.index/`、`./sql/biz-rules/` 定位表/字段/约束/错误码映射，命中项标来源不写全局 memory |
| `skills/sql-schema-reviewer/SKILL.md` | `$SRC/skills/sql-schema-reviewer/SKILL.md` | A：对照现有 `./sql/` schema context 检查冲突；B：`### v2 项目业务规则沉淀` 写 `./sql/biz-rules/`（保留真实表名字段） |
| `skills/sql-report-query-builder/SKILL.md` | `$SRC/skills/sql-report-query-builder/SKILL.md` | 读 `./sql/.index/table-index.json`、`biz-rules/{table,module}-index.json` 复用口径，`口径冲突` 时停止请用户裁决 |
| `skills/_shared/output-contract.md` | `$SRC/skills/_shared/output-contract.md` | 可选子段落「使用的项目上下文」「命中的业务规则」「沉淀结果」，且「不得作为第 7 个顶层段落」 |

其中 `$SRC=/Users/dalwin/.codex/plugins/cache/local-plugins/sql-expert-dba/1.1.0`。还原时若 Codex 原文用 memory 脚本裸名（`memory_search.py` 等），改为 `${CLAUDE_PLUGIN_ROOT}/scripts/<name>`。

- [ ] **Step 4: 修正 `memory-policy.md` 第 8 行 Codex 路径残留**

将 `skills/_shared/memory-policy.md` 中：

```text
- 用户级全局 memory 通过 `SQL_EXPERT_DBA_MEMORY_DIR`、`CODEX_HOME` 或 `~/.codex` 解析，不允许写死用户绝对路径。
```

改为：

```text
- 用户级全局 memory 通过 `SQL_EXPERT_DBA_MEMORY_DIR` 覆盖，默认落点 `~/.claude/plugins/data/sql-expert-dba/memory/`，不允许写死用户绝对路径。
```

- [ ] **Step 5: 运行验收测试，确认通过**

Run:

```bash
cd /Users/dalwin/Library/CodeRepo/AI/claude-plugins/sql-expert-dba/scripts
python3 -m unittest test_skill_docs_v2 -v 2>&1 | tail -12
```

Expected: `OK`，6 个用例全过。

- [ ] **Step 6: 校验无遗留裸脚本名、无残留中性化措辞**

Run:

```bash
DST=/Users/dalwin/Library/CodeRepo/AI/claude-plugins/sql-expert-dba/skills
echo "--- 裸 memory 脚本名（应无）---"; grep -rnE '`memory_(search|capture|index)\.py`' "$DST" && echo BARE || echo no-bare
echo "--- 残留 v2 延后措辞（应无）---"; grep -rn 'v2 延后，未随本版发布\|项目上下文（v2 延后）\|（v2 延后）' "$DST" && echo STILL-DEFERRED || echo no-deferred
```

Expected: `no-bare`；`no-deferred`。

- [ ] **Step 7: 提交**

```bash
cd /Users/dalwin/Library/CodeRepo/AI/claude-plugins
git add -A && git commit -m "feat(sql-expert-dba): 还原 5 技能与 output-contract 的 v2 段落并修正 memory-policy 残留"
```

Expected: commit 成功。

---

## Task 6: 全量回归与安装验证

- [ ] **Step 1: 全量单测回归**

Run:

```bash
cd /Users/dalwin/Library/CodeRepo/AI/claude-plugins/sql-expert-dba/scripts
python3 -m unittest test_paths test_memory test_memory_v2 test_project_context test_biz_rules test_skill_docs_v2 test_auto_memory_runner 2>&1 | tail -6
```

Expected: 末尾 `OK`，无 FAIL/ERROR。

- [ ] **Step 2: A/B 端到端冒烟（临时项目）**

Run:

```bash
TMP=$(mktemp -d); mkdir -p "$TMP/sql"
printf 'CREATE TABLE orders (id INT PRIMARY KEY, user_id INT, created_at DATETIME, KEY idx_user (user_id));\n' > "$TMP/sql/schema.sql"
S=/Users/dalwin/Library/CodeRepo/AI/claude-plugins/sql-expert-dba/scripts
python3 "$S/project_context_index.py" --project-dir "$TMP" --rebuild | python3 -c 'import json,sys;d=json.load(sys.stdin);print("index:",d["status"],d["tables"])'
python3 "$S/project_context_search.py" --project-dir "$TMP" --table orders | python3 -c 'import json,sys;d=json.load(sys.stdin);print("search:",d["status"],[t["name"] for t in d["tables"]])'
python3 "$S/biz_rules_capture.py" --project-dir "$TMP" --module orders --title "GMV口径" --rule-type metric_definition --tables orders --body "GMV=已支付订单金额合计" | python3 -c 'import json,sys;d=json.load(sys.stdin);print("biz:",d["status"],d.get("ignore_status"))'
grep -q 'sql/biz-rules/' "$TMP/.gitignore" && echo "gitignore-ok"
rm -rf "$TMP"
```

Expected: `index: indexed ['orders']`；`search: ok ['orders']`；`biz: captured updated`；`gitignore-ok`。

- [ ] **Step 3: 重新安装并确认 hooks 被发现**

Run:

```bash
claude plugin marketplace update dalwin-local-plugins 2>&1 | tail -2 || claude plugin marketplace add /Users/dalwin/Library/CodeRepo/AI/claude-plugins 2>&1 | tail -2
claude plugin install sql-expert-dba@dalwin-local-plugins 2>&1 | tail -2
claude plugin list 2>&1 | grep -i sql-expert-dba
```

Expected: 安装/更新成功；`claude plugin list` 含 `sql-expert-dba`（v1.1.0）。

> 交互冒烟（人工，新会话）：SQL 会话结束时 Stop hook 应注入一次沉淀提醒；非 SQL 会话无注入。详见 spec §8.6，此项不阻塞计划。

---

## Task 7: 实施日志

**Files:**
- Create: `dalwin-workflow/docs/superpowers/plans/logs/2026-06-04-sql-expert-dba-claude-plugin-v2.md`

- [ ] **Step 1: 写实施日志**

按模板写入，将「实测」替换为真实结果：成果（v2 三块 + 升版 1.1.0）、范围、适配点（C 重写为 Stop hook、capture-log 幂等、技能还原）、验证结果（全量单测 OK 数、A/B 冒烟、安装）、对账提醒（与 Codex 两份独立，D 留 v3）。

- [ ] **Step 2: 提交日志**

```bash
cd /Users/dalwin/Documents/AI/dalwin-workflow
git add docs/superpowers/plans/logs/2026-06-04-sql-expert-dba-claude-plugin-v2.md
git commit -m "docs(dalwin-workflow): 记录 sql-expert-dba Claude 插件 v2 迭代实施"
```

Expected: commit 成功。

---

## Plan Completion Verification

- [ ] **Step 1: 插件仓库提交历史**

Run: `git -C /Users/dalwin/Library/CodeRepo/AI/claude-plugins log --oneline | head -8`
Expected: 含 Task 1–5 的 5 个 feat 提交。

- [ ] **Step 2: 最终结构核对**

Run:

```bash
find /Users/dalwin/Library/CodeRepo/AI/claude-plugins/sql-expert-dba -type f -not -path '*/.git/*' \( -name '*.py' -o -name '*.json' \) | sort
```

Expected: scripts 含 11 个 `.py`（5 核心 + 2 project_context + 3 biz_rules + auto_memory_runner）+ 6 个 `test_*.py`；含 `hooks/hooks.json`。

## Rollback Summary

- 代码回滚：`git -C /Users/dalwin/Library/CodeRepo/AI/claude-plugins reset --hard <v1 末次 commit 5b607b4>`。
- 卸载：`claude plugin uninstall sql-expert-dba@dalwin-local-plugins`。
- 运行时数据不受影响（capture-log 仅追加 guard 标记）。
- Codex 版插件全程未改动。
