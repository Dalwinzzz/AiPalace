# SQL Expert DBA v2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement SQL Expert DBA v2 from [docs/superpowers/specs/2026-05-08-sql-expert-dba-v2-design.md](../specs/2026-05-08-sql-expert-dba-v2-design.md): portable global memory, guarded auto capture, project SQL context indexing, and project business rule capture.

**Architecture:** Keep SQL reasoning in skills. Keep scripts focused on path resolution, persistence, indexing, searching, deduplication, and Git governance. Runtime storage is split into plugin seed memory, user-level global memory, and project-local `./sql/` context plus `./sql/biz-rules/`.

**Tech Stack:** Python 3 standard library only, Markdown skill docs, JSON indexes, YAML-like front matter via existing `_frontmatter.py`, Git CLI for explicit business rule untracking.

---

## Scope Check

The v2 spec spans several subsystems, but they share one path model and one memory governance model. Implement this as one plan with independently testable tasks in this order:

1. Portable paths and directory creation.
2. Global memory search/capture/index refactor.
3. Guarded automatic memory runner.
4. Project SQL context indexing and search.
5. Project business rules and Git guard.
6. Skill documentation integration.
7. Full verification.

Each task should leave the repository in a working state and should be committed separately.

## File Structure

- Create `plugins/sql-expert-dba/scripts/paths.py`: portable path resolution and directory creation.
- Modify `plugins/sql-expert-dba/scripts/memory_search.py`: search seed memory plus user-level global memory.
- Modify `plugins/sql-expert-dba/scripts/memory_capture.py`: write user-level global memory by default, enforce auto candidate routing, reject unsanitized global entries.
- Modify `plugins/sql-expert-dba/scripts/memory_index.py`: support v2 approved/candidates layout while preserving v1 seed memory compatibility.
- Create `plugins/sql-expert-dba/scripts/auto_memory_runner.py`: Hook/Automation entry point with context sufficiency checks.
- Create `plugins/sql-expert-dba/scripts/project_context_index.py`: build and validate `./sql/.index/`.
- Create `plugins/sql-expert-dba/scripts/project_context_search.py`: retrieve project SQL context from indexes.
- Create `plugins/sql-expert-dba/scripts/biz_rules_capture.py`: write `./sql/biz-rules/` Markdown rules and indexes.
- Create `plugins/sql-expert-dba/scripts/biz_rules_search.py`: search project business rules.
- Create `plugins/sql-expert-dba/scripts/biz_rules_git_guard.py`: maintain `.gitignore`, detect tracked rules, and explicitly untrack when authorized.
- Create tests under `plugins/sql-expert-dba/scripts/`:
  - `test_paths.py`
  - `test_memory_v2.py`
  - `test_auto_memory_runner.py`
  - `test_project_context.py`
  - `test_biz_rules.py`
  - `test_skill_docs_v2.py`
- Modify skill docs under `plugins/sql-expert-dba/skills/` so every workflow knows when to use global memory, project context, and business rules.

---

### Task 1: Portable Path Resolution

**Files:**

- Create: `plugins/sql-expert-dba/scripts/paths.py`
- Create: `plugins/sql-expert-dba/scripts/test_paths.py`

- [ ] **Step 1: Write failing tests for path resolution**

Create `plugins/sql-expert-dba/scripts/test_paths.py` with these tests:

```python
#!/usr/bin/env python3
import os
import tempfile
import unittest
from pathlib import Path

from paths import (
    ensure_global_memory_dirs,
    resolve_biz_rules_dir,
    resolve_plugin_dir,
    resolve_project_sql_dir,
    resolve_user_memory_dir,
)


class TestPathResolution(unittest.TestCase):
    def test_sql_expert_memory_dir_env_wins(self):
        with tempfile.TemporaryDirectory() as td:
            env = {
                "SQL_EXPERT_DBA_MEMORY_DIR": str(Path(td) / "custom-memory"),
                "CODEX_HOME": str(Path(td) / "codex-home"),
            }
            result = resolve_user_memory_dir(env=env, home=Path(td) / "home")
            self.assertEqual(result, Path(td) / "custom-memory")

    def test_codex_home_used_when_custom_env_missing(self):
        with tempfile.TemporaryDirectory() as td:
            env = {"CODEX_HOME": str(Path(td) / "codex-home")}
            result = resolve_user_memory_dir(env=env, home=Path(td) / "home")
            self.assertEqual(result, Path(td) / "codex-home" / "memories" / "sql-expert-dba")

    def test_home_fallback_is_portable(self):
        with tempfile.TemporaryDirectory() as td:
            result = resolve_user_memory_dir(env={}, home=Path(td) / "home")
            self.assertEqual(result, Path(td) / "home" / ".codex" / "memories" / "sql-expert-dba")

    def test_project_paths_are_relative_to_cwd(self):
        with tempfile.TemporaryDirectory() as td:
            cwd = Path(td) / "project"
            self.assertEqual(resolve_project_sql_dir(cwd), cwd / "sql")
            self.assertEqual(resolve_biz_rules_dir(cwd), cwd / "sql" / "biz-rules")

    def test_ensure_global_memory_dirs_creates_v2_layout(self):
        with tempfile.TemporaryDirectory() as td:
            memory_dir = Path(td) / "memory"
            ensure_global_memory_dirs(memory_dir)
            for status in ("approved", "candidates"):
                for entry_type in ("rules", "cases", "templates", "glossary"):
                    self.assertTrue((memory_dir / status / entry_type).is_dir())
            self.assertTrue((memory_dir / "index.json").is_file())
            self.assertTrue((memory_dir / "capture-log.jsonl").is_file())

    def test_resolve_plugin_dir_points_to_plugin_root(self):
        plugin_dir = resolve_plugin_dir()
        self.assertEqual(plugin_dir.name, "sql-expert-dba")
        self.assertTrue((plugin_dir / ".codex-plugin" / "plugin.json").is_file())


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests and verify they fail**

Run:

```bash
python3 plugins/sql-expert-dba/scripts/test_paths.py
```

Expected: fail with `ModuleNotFoundError: No module named 'paths'`.

- [ ] **Step 3: Implement `paths.py`**

Create `plugins/sql-expert-dba/scripts/paths.py`:

```python
#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path


ENTRY_TYPES = ("rules", "cases", "templates", "glossary")


def resolve_plugin_dir() -> Path:
    """Return the sql-expert-dba plugin root."""
    return Path(__file__).resolve().parent.parent


def resolve_user_memory_dir(
    env: dict[str, str] | None = None,
    home: Path | None = None,
) -> Path:
    """Resolve portable user-level SQL Expert DBA memory directory."""
    env = os.environ if env is None else env
    if env.get("SQL_EXPERT_DBA_MEMORY_DIR"):
        return Path(env["SQL_EXPERT_DBA_MEMORY_DIR"]).expanduser()
    if env.get("CODEX_HOME"):
        return Path(env["CODEX_HOME"]).expanduser() / "memories" / "sql-expert-dba"
    return (home or Path.home()) / ".codex" / "memories" / "sql-expert-dba"


def resolve_project_sql_dir(cwd: str | Path | None = None) -> Path:
    """Resolve current project's ./sql directory."""
    root = Path.cwd() if cwd is None else Path(cwd)
    return root.resolve() / "sql"


def resolve_biz_rules_dir(cwd: str | Path | None = None) -> Path:
    """Resolve current project's ./sql/biz-rules directory."""
    return resolve_project_sql_dir(cwd) / "biz-rules"


def ensure_global_memory_dirs(memory_dir: Path) -> None:
    """Create the v2 global memory directory layout."""
    memory_dir.mkdir(parents=True, exist_ok=True)
    for status in ("approved", "candidates"):
        for entry_type in ENTRY_TYPES:
            (memory_dir / status / entry_type).mkdir(parents=True, exist_ok=True)

    index_path = memory_dir / "index.json"
    if not index_path.exists():
        index_path.write_text(
            json.dumps(
                {
                    "version": 2,
                    "last_updated": datetime.now(timezone.utc).isoformat(),
                    "entries": [],
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

    log_path = memory_dir / "capture-log.jsonl"
    if not log_path.exists():
        log_path.write_text("", encoding="utf-8")
```

- [ ] **Step 4: Run path tests**

Run:

```bash
python3 plugins/sql-expert-dba/scripts/test_paths.py
```

Expected: all tests pass.

- [ ] **Step 5: Commit Task 1**

```bash
git add plugins/sql-expert-dba/scripts/paths.py plugins/sql-expert-dba/scripts/test_paths.py
git commit -m "feat(sql-expert-dba): add portable path resolution"
```

---

### Task 2: User-Level Global Memory Refactor

**Files:**

- Modify: `plugins/sql-expert-dba/scripts/memory_search.py`
- Modify: `plugins/sql-expert-dba/scripts/memory_capture.py`
- Modify: `plugins/sql-expert-dba/scripts/memory_index.py`
- Create: `plugins/sql-expert-dba/scripts/test_memory_v2.py`

- [ ] **Step 1: Write failing v2 memory tests**

Create `plugins/sql-expert-dba/scripts/test_memory_v2.py`:

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
MEMORY_CAPTURE = SCRIPTS_DIR / "memory_capture.py"
MEMORY_SEARCH = SCRIPTS_DIR / "memory_search.py"
MEMORY_INDEX = SCRIPTS_DIR / "memory_index.py"


def run_json(script: Path, args: list[str], env: dict[str, str] | None = None) -> dict | list:
    result = subprocess.run(
        [sys.executable, str(script)] + args,
        capture_output=True,
        text=True,
        env=env,
    )
    if result.returncode != 0:
        raise AssertionError(f"{script.name} failed\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}")
    return json.loads(result.stdout)


class TestGlobalMemoryV2(unittest.TestCase):
    def test_explicit_capture_defaults_to_approved(self):
        with tempfile.TemporaryDirectory() as td:
            env = os.environ.copy()
            env["SQL_EXPERT_DBA_MEMORY_DIR"] = str(Path(td) / "global-memory")
            result = run_json(MEMORY_CAPTURE, [
                "--title", "隐式转换导致索引失效",
                "--type", "rule",
                "--workflow", "sql-query-optimizer",
                "--dialect", "mysql",
                "--tags", "index,type-conversion",
                "--problem-pattern", "字符串列和数字条件比较导致索引失效",
                "--conclusion", "比较值类型应与字段类型一致",
                "--boundaries", "适用于 MySQL 字符串索引列",
                "--capture-mode", "explicit_user_requested",
            ], env=env)
            self.assertEqual(result["review_status"], "approved")
            self.assertTrue((Path(td) / "global-memory" / "approved" / "rules").is_dir())

    def test_auto_capture_forces_candidate(self):
        with tempfile.TemporaryDirectory() as td:
            env = os.environ.copy()
            env["SQL_EXPERT_DBA_MEMORY_DIR"] = str(Path(td) / "global-memory")
            result = run_json(MEMORY_CAPTURE, [
                "--title", "自动候选",
                "--type", "case",
                "--workflow", "sql-query-optimizer",
                "--problem-pattern", "慢查询中 OR 条件过多",
                "--conclusion", "可考虑改写为 UNION ALL 或临时集合 JOIN",
                "--capture-mode", "auto_hook",
                "--force-approved",
            ], env=env)
            self.assertEqual(result["review_status"], "candidate")
            self.assertIn("candidates/cases/", result["file"])

    def test_rejects_unsanitized_global_memory(self):
        with tempfile.TemporaryDirectory() as td:
            env = os.environ.copy()
            env["SQL_EXPERT_DBA_MEMORY_DIR"] = str(Path(td) / "global-memory")
            result = run_json(MEMORY_CAPTURE, [
                "--title", "包含真实表名",
                "--type", "rule",
                "--problem-pattern", "orders 表 pay_amount 统计口径",
                "--conclusion", "orders.pay_amount 是实付金额",
                "--capture-mode", "explicit_user_requested",
                "--forbidden-token", "orders",
                "--forbidden-token", "pay_amount",
            ], env=env)
            self.assertEqual(result["status"], "skipped")
            self.assertEqual(result["reason"], "unsanitized_global_memory")

    def test_search_reads_seed_and_global_memory(self):
        with tempfile.TemporaryDirectory() as td:
            seed = Path(td) / "seed"
            global_mem = Path(td) / "global"
            (seed / "rules").mkdir(parents=True)
            (global_mem / "approved" / "rules").mkdir(parents=True)
            (global_mem / "candidates" / "rules").mkdir(parents=True)
            seed_entry = """---
id: seed-001
title: 覆盖索引
type: rule
workflow: sql-query-optimizer
dialect: universal
tags: [index]
problem_pattern: 查询列都在联合索引中
conclusion: 可以减少回表
review_status: approved
---

# 覆盖索引
"""
            global_entry = seed_entry.replace("seed-001", "global-001").replace("覆盖索引", "隐式转换")
            (seed / "rules" / "seed.md").write_text(seed_entry, encoding="utf-8")
            (global_mem / "approved" / "rules" / "global.md").write_text(global_entry, encoding="utf-8")
            result = run_json(MEMORY_SEARCH, [
                "--memory-dir", str(global_mem),
                "--seed-memory-dir", str(seed),
                "--pattern", "索引",
            ])
            ids = {entry["id"] for entry in result}
            self.assertEqual(ids, {"seed-001", "global-001"})

    def test_index_rebuild_supports_v2_layout(self):
        with tempfile.TemporaryDirectory() as td:
            mem = Path(td) / "global"
            (mem / "approved" / "templates").mkdir(parents=True)
            (mem / "candidates" / "rules").mkdir(parents=True)
            (mem / "approved" / "templates" / "daily.md").write_text("""---
id: template-abc
title: 日统计模板
type: template
workflow: sql-report-query-builder
dialect: universal
tags: [report]
problem_pattern: 需要按天统计
conclusion: 使用日期维度聚合
review_status: approved
---

# 日统计模板
""", encoding="utf-8")
            result = run_json(MEMORY_INDEX, ["--memory-dir", str(mem), "--rebuild"])
            self.assertEqual(result["total"], 1)
            index = json.loads((mem / "index.json").read_text(encoding="utf-8"))
            self.assertEqual(index["version"], 2)
            self.assertEqual(index["entries"][0]["file"], "approved/templates/daily.md")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run new memory tests and verify failures**

Run:

```bash
python3 plugins/sql-expert-dba/scripts/test_memory_v2.py
```

Expected: failures for missing `--seed-memory-dir`, unsupported `auto_hook`, missing `--forbidden-token`, and v2 layout routing.

- [ ] **Step 3: Update `memory_capture.py`**

Implement these behavioral changes:

```python
# Add near imports
from paths import ensure_global_memory_dirs, resolve_user_memory_dir


AUTO_CAPTURE_MODES = {"auto_hook", "auto_automation"}


def contains_forbidden_tokens(args: argparse.Namespace) -> bool:
    text = " ".join(
        str(value or "")
        for value in (
            args.title,
            args.problem_pattern,
            args.preconditions,
            args.conclusion,
            args.boundaries,
            args.example,
            args.anti_example,
        )
    ).lower()
    return any(token.lower() in text for token in (args.forbidden_token or []))


def determine_status(entry_type: str, confidence: str, capture_mode: str, force_approved: bool, promotion_reason: str | None = None) -> str:
    if capture_mode in AUTO_CAPTURE_MODES:
        return "candidate"
    if capture_mode == "explicit_user_requested":
        if confidence in ("medium", "high"):
            return "approved"
        return "candidate"
    if force_approved:
        return "approved"
    if promotion_reason and promotion_reason in AUTO_APPROVED_PATTERNS:
        return "approved"
    return "candidate"


def determine_directory(memory_dir: Path, entry_type: str, status: str) -> Path:
    status_dir = "approved" if status == "approved" else "candidates"
    return memory_dir / status_dir / TYPE_DIR_MAP.get(entry_type, "cases")
```

Add parser changes:

```python
parser.add_argument("--memory-dir", type=Path, help="User-level global memory directory")
parser.add_argument("--forbidden-token", action="append", help="Token that must not appear in sanitized global memory")
parser.add_argument(
    "--capture-mode",
    default="explicit_user_requested",
    choices=["explicit_user_requested", "auto_hook", "auto_automation", "auto_background"],
)
```

Before duplicate detection:

```python
if args.memory_dir is None:
    args.memory_dir = resolve_user_memory_dir()
ensure_global_memory_dirs(args.memory_dir)

if contains_forbidden_tokens(args):
    print(json.dumps({
        "status": "skipped",
        "reason": "unsanitized_global_memory",
        "title": args.title,
    }, ensure_ascii=False, indent=2))
    return
```

When writing the file, ensure `target_dir.mkdir(parents=True, exist_ok=True)`.

- [ ] **Step 4: Update `memory_index.py` for v2 layout**

Make file discovery recurse through both v1 and v2 memory layouts:

```python
def find_memory_files(memory_dir: Path) -> list[Path]:
    files: list[Path] = []
    for filepath in sorted(memory_dir.rglob("*.md")):
        if filepath.name.lower() == "readme.md":
            continue
        if any(part.startswith(".") for part in filepath.relative_to(memory_dir).parts):
            continue
        files.append(filepath)
    return files
```

When rebuilding, write:

```python
data = {
    "version": 2,
    "last_updated": datetime.now(timezone.utc).isoformat(),
    "entries": entries,
}
```

Keep validate compatible with existing seed memory by comparing indexed fields to parsed front matter, including `problem_pattern`, `conclusion`, and `review_status`.

- [ ] **Step 5: Update `memory_search.py` for layered search**

Add arguments:

```python
parser.add_argument("--memory-dir", type=Path, help="User-level global memory directory")
parser.add_argument("--seed-memory-dir", type=Path, help="Plugin seed memory directory")
parser.add_argument("--include-candidates", action="store_true", help="Include candidate entries")
```

Resolve defaults:

```python
from paths import resolve_plugin_dir, resolve_user_memory_dir

if args.memory_dir is None:
    args.memory_dir = resolve_user_memory_dir()
if args.seed_memory_dir is None:
    args.seed_memory_dir = resolve_plugin_dir() / "memory"
if args.include_candidates:
    args.status = "all"
```

Search both directories and dedupe by `id`:

```python
def merge_results(result_sets: list[list[dict]]) -> list[dict]:
    merged: dict[str, dict] = {}
    for results in result_sets:
        for entry in results:
            merged.setdefault(str(entry.get("id")), entry)
    return list(merged.values())
```

- [ ] **Step 6: Run memory tests**

Run:

```bash
python3 plugins/sql-expert-dba/scripts/test_memory.py
python3 plugins/sql-expert-dba/scripts/test_memory_v2.py
```

Expected: both pass.

- [ ] **Step 7: Commit Task 2**

```bash
git add plugins/sql-expert-dba/scripts/memory_search.py plugins/sql-expert-dba/scripts/memory_capture.py plugins/sql-expert-dba/scripts/memory_index.py plugins/sql-expert-dba/scripts/test_memory_v2.py
git commit -m "feat(sql-expert-dba): use portable global memory"
```

---

### Task 3: Guarded Automatic Memory Runner

**Files:**

- Create: `plugins/sql-expert-dba/scripts/auto_memory_runner.py`
- Create: `plugins/sql-expert-dba/scripts/test_auto_memory_runner.py`

- [ ] **Step 1: Write failing auto runner tests**

Create `plugins/sql-expert-dba/scripts/test_auto_memory_runner.py`:

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


def run_runner(args: list[str], env: dict[str, str]) -> dict:
    result = subprocess.run(
        [sys.executable, str(RUNNER)] + args,
        capture_output=True,
        text=True,
        env=env,
    )
    if result.returncode != 0:
        raise AssertionError(f"auto runner failed\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}")
    return json.loads(result.stdout)


class TestAutoMemoryRunner(unittest.TestCase):
    def test_skips_when_required_context_missing(self):
        with tempfile.TemporaryDirectory() as td:
            context_path = Path(td) / "context.json"
            context_path.write_text(json.dumps({"workflow": "sql-query-optimizer"}), encoding="utf-8")
            env = os.environ.copy()
            env["SQL_EXPERT_DBA_MEMORY_DIR"] = str(Path(td) / "memory")
            result = run_runner(["--input", str(context_path)], env)
            self.assertEqual(result["status"], "skipped")
            self.assertEqual(result["reason"], "insufficient_context")
            self.assertFalse((Path(td) / "memory" / "candidates").exists())

    def test_auto_global_capture_writes_candidate(self):
        with tempfile.TemporaryDirectory() as td:
            context_path = Path(td) / "context.json"
            context = {
                "workflow": "sql-query-optimizer",
                "user_input": "SELECT * FROM orders WHERE user_id = 1",
                "assistant_final": "Use explicit columns and index user_id.",
                "timestamp": "2026-05-08T12:00:00Z",
                "global_candidate": {
                    "title": "SELECT star avoids covering index",
                    "type": "rule",
                    "dialect": "universal",
                    "tags": ["select-star", "index"],
                    "problem_pattern": "Production queries use SELECT *",
                    "conclusion": "Use explicit projection to reduce IO and enable covering indexes",
                    "boundaries": "Applies when query callers do not need every column",
                    "forbidden_tokens": ["orders"],
                },
            }
            context_path.write_text(json.dumps(context), encoding="utf-8")
            env = os.environ.copy()
            env["SQL_EXPERT_DBA_MEMORY_DIR"] = str(Path(td) / "memory")
            result = run_runner(["--input", str(context_path)], env)
            self.assertEqual(result["status"], "captured")
            self.assertEqual(result["review_status"], "candidate")
            self.assertIn("candidates/rules/", result["file"])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```bash
python3 plugins/sql-expert-dba/scripts/test_auto_memory_runner.py
```

Expected: fail with missing `auto_memory_runner.py`.

- [ ] **Step 3: Implement `auto_memory_runner.py`**

Create script:

```python
#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from paths import resolve_user_memory_dir


REQUIRED_CONTEXT_FIELDS = ("workflow", "user_input", "assistant_final", "timestamp")


def load_context(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def has_required_context(context: dict) -> bool:
    return all(str(context.get(field, "")).strip() for field in REQUIRED_CONTEXT_FIELDS)


def capture_global_candidate(context: dict, memory_dir: Path) -> dict:
    candidate = context.get("global_candidate") or {}
    required = ("title", "type", "problem_pattern", "conclusion")
    if not all(str(candidate.get(field, "")).strip() for field in required):
        return {"status": "skipped", "reason": "missing_global_candidate"}

    cmd = [
        sys.executable,
        str(Path(__file__).parent / "memory_capture.py"),
        "--memory-dir",
        str(memory_dir),
        "--capture-mode",
        "auto_hook",
        "--title",
        candidate["title"],
        "--type",
        candidate["type"],
        "--workflow",
        context["workflow"],
        "--problem-pattern",
        candidate["problem_pattern"],
        "--conclusion",
        candidate["conclusion"],
        "--dialect",
        candidate.get("dialect", "universal"),
        "--boundaries",
        candidate.get("boundaries", ""),
        "--tags",
        ",".join(candidate.get("tags", [])),
    ]
    for token in candidate.get("forbidden_tokens", []):
        cmd.extend(["--forbidden-token", token])

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return {"status": "error", "reason": "memory_capture_failed", "stderr": result.stderr}
    return json.loads(result.stdout)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run guarded SQL Expert DBA automatic memory capture")
    parser.add_argument("--input", required=True, type=Path, help="JSON context payload")
    parser.add_argument("--memory-dir", type=Path, help="User-level global memory directory")
    args = parser.parse_args()

    context = load_context(args.input)
    if not has_required_context(context):
        print(json.dumps({"status": "skipped", "reason": "insufficient_context"}, ensure_ascii=False, indent=2))
        return

    memory_dir = args.memory_dir or resolve_user_memory_dir()
    result = capture_global_candidate(context, memory_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run auto runner tests**

Run:

```bash
python3 plugins/sql-expert-dba/scripts/test_auto_memory_runner.py
```

Expected: all tests pass.

- [ ] **Step 5: Commit Task 3**

```bash
git add plugins/sql-expert-dba/scripts/auto_memory_runner.py plugins/sql-expert-dba/scripts/test_auto_memory_runner.py
git commit -m "feat(sql-expert-dba): add guarded auto memory runner"
```

---

### Task 4: Project SQL Context Indexing And Search

**Files:**

- Create: `plugins/sql-expert-dba/scripts/project_context_index.py`
- Create: `plugins/sql-expert-dba/scripts/project_context_search.py`
- Create: `plugins/sql-expert-dba/scripts/test_project_context.py`

- [ ] **Step 1: Write failing project context tests**

Create `plugins/sql-expert-dba/scripts/test_project_context.py`:

```python
#!/usr/bin/env python3
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent
INDEX = SCRIPTS_DIR / "project_context_index.py"
SEARCH = SCRIPTS_DIR / "project_context_search.py"


def run_json(script: Path, args: list[str]) -> dict | list:
    result = subprocess.run([sys.executable, str(script)] + args, capture_output=True, text=True)
    if result.returncode != 0:
        raise AssertionError(f"{script.name} failed\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}")
    return json.loads(result.stdout)


class TestProjectContext(unittest.TestCase):
    def test_rebuild_indexes_supported_sql_files(self):
        with tempfile.TemporaryDirectory() as td:
            project = Path(td)
            ddl_dir = project / "sql" / "ddl"
            ddl_dir.mkdir(parents=True)
            (ddl_dir / "schema.sql").write_text("""
CREATE TABLE orders (
  id bigint primary key,
  user_id bigint not null,
  status varchar(32),
  paid_at datetime,
  pay_amount decimal(10,2),
  KEY idx_orders_user_id (user_id),
  KEY idx_orders_paid_at (paid_at)
);
""", encoding="utf-8")
            (project / "sql" / "explain").mkdir()
            (project / "sql" / "explain" / "orders.explain").write_text("type: ALL\\nExtra: Using filesort", encoding="utf-8")
            result = run_json(INDEX, ["--project-dir", str(project), "--rebuild"])
            self.assertEqual(result["status"], "indexed")
            table_index = json.loads((project / "sql" / ".index" / "table-index.json").read_text(encoding="utf-8"))
            self.assertIn("orders", table_index["tables"])
            self.assertIn("user_id", table_index["tables"]["orders"]["columns"])
            self.assertIn("idx_orders_user_id", table_index["tables"]["orders"]["indexes"])

    def test_search_returns_table_context(self):
        with tempfile.TemporaryDirectory() as td:
            project = Path(td)
            ddl_dir = project / "sql"
            ddl_dir.mkdir()
            (ddl_dir / "schema.ddl").write_text("CREATE TABLE users (id bigint primary key, name varchar(64));", encoding="utf-8")
            run_json(INDEX, ["--project-dir", str(project), "--rebuild"])
            result = run_json(SEARCH, ["--project-dir", str(project), "--table", "users"])
            self.assertEqual(result["tables"][0]["name"], "users")
            self.assertIn("id", result["tables"][0]["columns"])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run project context tests and verify failure**

Run:

```bash
python3 plugins/sql-expert-dba/scripts/test_project_context.py
```

Expected: fail with missing scripts.

- [ ] **Step 3: Implement `project_context_index.py`**

Implement a zero-dependency indexer with these core functions:

```python
SUPPORTED_EXTENSIONS = {".sql", ".ddl", ".explain", ".log", ".txt", ".md"}


def should_index(path: Path, sql_dir: Path) -> bool:
    rel = path.relative_to(sql_dir)
    if "biz-rules" in rel.parts:
        return False
    if any(part.startswith(".") for part in rel.parts):
        return False
    return path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS


def extract_create_tables(text: str, source: str) -> dict:
    pattern = re.compile(r"create\\s+table\\s+`?(\\w+)`?\\s*\\((.*?)\\)\\s*;", re.I | re.S)
    tables: dict[str, dict] = {}
    for match in pattern.finditer(text):
        table_name = match.group(1)
        body = match.group(2)
        columns: list[str] = []
        indexes: dict[str, list[str]] = {}
        for raw_line in body.splitlines():
            line = raw_line.strip().rstrip(",")
            col_match = re.match(r"`?(\\w+)`?\\s+(bigint|int|varchar|datetime|timestamp|decimal|date|text|json)", line, re.I)
            if col_match:
                columns.append(col_match.group(1))
            idx_match = re.match(r"(?:key|index)\\s+`?(\\w+)`?\\s*\\(([^)]+)\\)", line, re.I)
            if idx_match:
                indexes[idx_match.group(1)] = [c.strip(" `") for c in idx_match.group(2).split(",")]
        tables[table_name] = {"columns": columns, "indexes": indexes, "sources": [source]}
    return tables
```

Write JSON files:

- `file-digests.json`
- `context-index.json`
- `table-index.json`

CLI:

```bash
python3 project_context_index.py --project-dir /path/to/project --rebuild
python3 project_context_index.py --project-dir /path/to/project --validate
```

- [ ] **Step 4: Implement `project_context_search.py`**

Implement CLI:

```python
parser.add_argument("--project-dir", type=Path, default=Path.cwd())
parser.add_argument("--table", action="append", default=[])
parser.add_argument("--field", action="append", default=[])
parser.add_argument("--keyword")
```

Return JSON:

```json
{
  "status": "ok",
  "tables": [
    {
      "name": "orders",
      "columns": ["id", "user_id"],
      "indexes": {"idx_orders_user_id": ["user_id"]},
      "sources": ["ddl/schema.sql"]
    }
  ]
}
```

- [ ] **Step 5: Run project context tests**

Run:

```bash
python3 plugins/sql-expert-dba/scripts/test_project_context.py
```

Expected: all tests pass.

- [ ] **Step 6: Commit Task 4**

```bash
git add plugins/sql-expert-dba/scripts/project_context_index.py plugins/sql-expert-dba/scripts/project_context_search.py plugins/sql-expert-dba/scripts/test_project_context.py
git commit -m "feat(sql-expert-dba): add project SQL context indexing"
```

---

### Task 5: Project Business Rules And Git Guard

**Files:**

- Create: `plugins/sql-expert-dba/scripts/biz_rules_capture.py`
- Create: `plugins/sql-expert-dba/scripts/biz_rules_search.py`
- Create: `plugins/sql-expert-dba/scripts/biz_rules_git_guard.py`
- Create: `plugins/sql-expert-dba/scripts/test_biz_rules.py`

- [ ] **Step 1: Write failing business rule tests**

Create `plugins/sql-expert-dba/scripts/test_biz_rules.py`:

```python
#!/usr/bin/env python3
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent
CAPTURE = SCRIPTS_DIR / "biz_rules_capture.py"
SEARCH = SCRIPTS_DIR / "biz_rules_search.py"
GIT_GUARD = SCRIPTS_DIR / "biz_rules_git_guard.py"


def run_json(script: Path, args: list[str], cwd: Path | None = None) -> dict | list:
    result = subprocess.run([sys.executable, str(script)] + args, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        raise AssertionError(f"{script.name} failed\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}")
    return json.loads(result.stdout)


class TestBizRules(unittest.TestCase):
    def test_capture_writes_module_rule_and_indexes(self):
        with tempfile.TemporaryDirectory() as td:
            project = Path(td)
            result = run_json(CAPTURE, [
                "--project-dir", str(project),
                "--module", "order",
                "--title", "paid order daily statistics",
                "--rule-type", "metric_definition",
                "--tables", "orders,order_items",
                "--fields", "orders.paid_at,orders.status",
                "--source-workflow", "sql-report-query-builder",
                "--capture-mode", "explicit_user_requested",
                "--confidence", "high",
                "--body", "Paid orders use status=paid and paid_at as the business date.",
            ])
            self.assertEqual(result["status"], "captured")
            self.assertEqual(result["module"], "order")
            self.assertTrue((project / "sql" / "biz-rules" / "order").is_dir())
            table_index = json.loads((project / "sql" / "biz-rules" / "table-index.json").read_text(encoding="utf-8"))
            self.assertIn("orders", table_index["tables"])

    def test_search_by_table_finds_rule(self):
        with tempfile.TemporaryDirectory() as td:
            project = Path(td)
            run_json(CAPTURE, [
                "--project-dir", str(project),
                "--module", "order",
                "--title", "paid order rule",
                "--rule-type", "metric_definition",
                "--tables", "orders",
                "--fields", "orders.status",
                "--source-workflow", "sql-report-query-builder",
                "--body", "Paid orders require status=paid.",
            ])
            result = run_json(SEARCH, ["--project-dir", str(project), "--table", "orders"])
            self.assertEqual(len(result["rules"]), 1)
            self.assertEqual(result["rules"][0]["module"], "order")

    def test_git_guard_adds_ignore_rule(self):
        with tempfile.TemporaryDirectory() as td:
            project = Path(td)
            (project / "sql" / "biz-rules").mkdir(parents=True)
            result = run_json(GIT_GUARD, ["--project-dir", str(project), "--ensure-ignore"])
            self.assertEqual(result["ignore_status"], "updated")
            self.assertIn("/sql/biz-rules/", (project / ".gitignore").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```bash
python3 plugins/sql-expert-dba/scripts/test_biz_rules.py
```

Expected: fail with missing scripts.

- [ ] **Step 3: Implement `biz_rules_capture.py`**

Core behavior:

```python
RULE_TYPES = {
    "metric_definition",
    "field_semantics",
    "table_relationship",
    "report_template",
    "exclusion_rule",
    "reconciliation_rule",
}


def normalize_list(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def module_slug(module: str) -> str:
    cleaned = "".join(ch.lower() if ch.isalnum() else "-" for ch in module.strip())
    while "--" in cleaned:
        cleaned = cleaned.replace("--", "-")
    return cleaned.strip("-") or "uncategorized"
```

Write Markdown files under `sql/biz-rules/<module>/`. Use front matter with:

- `id`
- `title`
- `module`
- `tables`
- `fields`
- `rule_type`
- `source_workflow`
- `capture_mode`
- `confidence`
- `review_status`
- `last_reviewed_at`

After writing, update:

- `sql/biz-rules/table-index.json`
- `sql/biz-rules/module-index.json`

- [ ] **Step 4: Implement `biz_rules_search.py`**

Support:

```python
parser.add_argument("--project-dir", type=Path, default=Path.cwd())
parser.add_argument("--module")
parser.add_argument("--table")
parser.add_argument("--field")
parser.add_argument("--rule-type")
parser.add_argument("--keyword")
```

Return:

```json
{
  "status": "ok",
  "rules": [
    {
      "file": "order/paid-order-rule.md",
      "title": "paid order rule",
      "module": "order",
      "tables": ["orders"],
      "rule_type": "metric_definition"
    }
  ]
}
```

- [ ] **Step 5: Implement `biz_rules_git_guard.py`**

Implement:

```python
IGNORE_LINE = "/sql/biz-rules/"


def ensure_ignore(project_dir: Path) -> str:
    gitignore = project_dir / ".gitignore"
    existing = gitignore.read_text(encoding="utf-8") if gitignore.exists() else ""
    if IGNORE_LINE in existing.splitlines():
        return "present"
    suffix = "" if not existing or existing.endswith("\n") else "\n"
    gitignore.write_text(existing + suffix + IGNORE_LINE + "\n", encoding="utf-8")
    return "updated"
```

Detect tracking:

```python
def is_tracked(project_dir: Path) -> bool:
    result = subprocess.run(
        ["git", "ls-files", "--error-unmatch", "sql/biz-rules"],
        cwd=project_dir,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0
```

Only run untrack when `--untrack` is provided:

```python
subprocess.run(["git", "rm", "--cached", "-r", "sql/biz-rules"], cwd=project_dir, check=True)
```

- [ ] **Step 6: Run business rule tests**

Run:

```bash
python3 plugins/sql-expert-dba/scripts/test_biz_rules.py
```

Expected: all tests pass.

- [ ] **Step 7: Commit Task 5**

```bash
git add plugins/sql-expert-dba/scripts/biz_rules_capture.py plugins/sql-expert-dba/scripts/biz_rules_search.py plugins/sql-expert-dba/scripts/biz_rules_git_guard.py plugins/sql-expert-dba/scripts/test_biz_rules.py
git commit -m "feat(sql-expert-dba): add project business rules"
```

---

### Task 6: Skill Documentation Integration

**Files:**

- Modify: `plugins/sql-expert-dba/skills/_shared/memory-policy.md`
- Modify: `plugins/sql-expert-dba/skills/_shared/output-contract.md`
- Modify: `plugins/sql-expert-dba/skills/sql-expert-router/SKILL.md`
- Modify: `plugins/sql-expert-dba/skills/sql-query-optimizer/SKILL.md`
- Modify: `plugins/sql-expert-dba/skills/sql-error-diagnostician/SKILL.md`
- Modify: `plugins/sql-expert-dba/skills/sql-schema-reviewer/SKILL.md`
- Modify: `plugins/sql-expert-dba/skills/sql-report-query-builder/SKILL.md`
- Create: `plugins/sql-expert-dba/scripts/test_skill_docs_v2.py`

- [ ] **Step 1: Write doc integration tests**

Create `plugins/sql-expert-dba/scripts/test_skill_docs_v2.py`:

```python
#!/usr/bin/env python3
import unittest
from pathlib import Path

PLUGIN_DIR = Path(__file__).resolve().parent.parent
SKILLS_DIR = PLUGIN_DIR / "skills"


class TestSkillDocsV2(unittest.TestCase):
    def assert_contains(self, path: Path, text: str) -> None:
        content = path.read_text(encoding="utf-8")
        self.assertIn(text, content, f"{path} should contain {text!r}")

    def test_shared_memory_policy_mentions_v2_storage_layers(self):
        policy = SKILLS_DIR / "_shared" / "memory-policy.md"
        self.assert_contains(policy, "用户级全局 memory")
        self.assert_contains(policy, "./sql/biz-rules/")
        self.assert_contains(policy, "自动沉淀只写 candidates")

    def test_output_contract_mentions_v2_optional_sections(self):
        contract = SKILLS_DIR / "_shared" / "output-contract.md"
        self.assert_contains(contract, "使用的项目上下文")
        self.assert_contains(contract, "命中的业务规则")
        self.assert_contains(contract, "沉淀结果")

    def test_router_mentions_project_context_indexing(self):
        router = SKILLS_DIR / "sql-expert-router" / "SKILL.md"
        self.assert_contains(router, "./sql/.index/")
        self.assert_contains(router, "biz-rules")

    def test_report_builder_mentions_business_rule_reuse_and_conflicts(self):
        report = SKILLS_DIR / "sql-report-query-builder" / "SKILL.md"
        self.assert_contains(report, "biz-rules/table-index.json")
        self.assert_contains(report, "口径冲突")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run doc tests and verify failure**

Run:

```bash
python3 plugins/sql-expert-dba/scripts/test_skill_docs_v2.py
```

Expected: fail because docs do not yet contain all v2 integration text.

- [ ] **Step 3: Update shared memory policy**

Add a v2 section to `plugins/sql-expert-dba/skills/_shared/memory-policy.md`:

```markdown
## v2 存储分层

- 插件内置 `memory/` 只作为 seed memory，不作为运行时沉淀真源。
- 用户级全局 memory 通过 `SQL_EXPERT_DBA_MEMORY_DIR`、`CODEX_HOME` 或 `~/.codex` 解析，不允许写死用户绝对路径。
- 项目级业务规则写入当前工作目录 `./sql/biz-rules/`。
- 全局 memory 必须去敏和抽象化。
- 项目级 `./sql/` 与 `./sql/biz-rules/` 可以保留真实表名、字段名和业务口径。
- 自动沉淀只写 candidates，显式沉淀通过校验后可写 approved。
```

- [ ] **Step 4: Update output contract**

Add optional v2 sections to `plugins/sql-expert-dba/skills/_shared/output-contract.md`:

```markdown
## v2 可选段落

### 使用的项目上下文

当回答使用了 `./sql/.index/`、DDL、EXPLAIN、慢 SQL 或项目说明时，简要列出来源文件和已使用事实。

### 命中的业务规则

当回答使用了 `./sql/biz-rules/` 时，列出业务模块、相关表和规则文件。

### 沉淀结果

当本次任务触发显式或自动沉淀时，说明写入目标、review_status 和文件路径。未触发时默认省略。
```

- [ ] **Step 5: Update workflow skill docs**

Add these concrete references:

- `sql-expert-router/SKILL.md`: mention checking `./sql/`, building `./sql/.index/`, and loading `biz-rules`.
- `sql-query-optimizer/SKILL.md`: mention using project `table-index.json` for DDL/index/EXPLAIN context.
- `sql-error-diagnostician/SKILL.md`: mention looking up tables, fields, constraints, and SQLSTATE/error codes in project context.
- `sql-schema-reviewer/SKILL.md`: mention writing project table relationships and field semantics into `biz-rules`.
- `sql-report-query-builder/SKILL.md`: mention reading `biz-rules/table-index.json`, `biz-rules/module-index.json`, and stopping on `口径冲突`.

- [ ] **Step 6: Run doc tests**

Run:

```bash
python3 plugins/sql-expert-dba/scripts/test_skill_docs_v2.py
```

Expected: all tests pass.

- [ ] **Step 7: Commit Task 6**

```bash
git add plugins/sql-expert-dba/skills plugins/sql-expert-dba/scripts/test_skill_docs_v2.py
git commit -m "docs(sql-expert-dba): document v2 runtime memory flows"
```

---

### Task 7: Full Verification And Review Prep

**Files:**

- Modify only if verification reveals a defect in files changed by Tasks 1-6.

- [ ] **Step 1: Run all plugin tests**

Run:

```bash
python3 plugins/sql-expert-dba/scripts/test_memory.py
python3 plugins/sql-expert-dba/scripts/test_paths.py
python3 plugins/sql-expert-dba/scripts/test_memory_v2.py
python3 plugins/sql-expert-dba/scripts/test_auto_memory_runner.py
python3 plugins/sql-expert-dba/scripts/test_project_context.py
python3 plugins/sql-expert-dba/scripts/test_biz_rules.py
python3 plugins/sql-expert-dba/scripts/test_skill_docs_v2.py
```

Expected: all tests pass.

- [ ] **Step 2: Run manual smoke checks**

Run:

```bash
tmpdir=$(mktemp -d)
SQL_EXPERT_DBA_MEMORY_DIR="$tmpdir/memory" python3 plugins/sql-expert-dba/scripts/memory_capture.py \
  --title "显式沉淀烟测" \
  --type rule \
  --workflow sql-query-optimizer \
  --problem-pattern "SELECT star in production query" \
  --conclusion "Use explicit projection" \
  --capture-mode explicit_user_requested
```

Expected JSON includes:

```json
{
  "status": "captured",
  "review_status": "approved"
}
```

Run:

```bash
project=$(mktemp -d)
mkdir -p "$project/sql"
printf 'CREATE TABLE orders (id bigint primary key, user_id bigint, KEY idx_user_id (user_id));\n' > "$project/sql/schema.sql"
python3 plugins/sql-expert-dba/scripts/project_context_index.py --project-dir "$project" --rebuild
python3 plugins/sql-expert-dba/scripts/project_context_search.py --project-dir "$project" --table orders
```

Expected search JSON contains table `orders` and index `idx_user_id`.

- [ ] **Step 3: Check for accidental hardcoded user paths**

Run:

```bash
rg -n "/Users/dalwin|/home/|C:\\\\" plugins/sql-expert-dba
```

Expected: no matches in implementation files. Matches in historical docs outside plugin are not part of this check.

- [ ] **Step 4: Check Git cleanliness**

Run:

```bash
git status --short
```

Expected: clean after Task 7 fixes are committed, or only intentional final changes remain.

- [ ] **Step 5: Commit Task 7 if fixes were needed**

If Task 7 required fixes:

```bash
git add plugins/sql-expert-dba
git commit -m "test(sql-expert-dba): verify v2 integration"
```

If no fixes were needed, do not create an empty commit.

---

## Execution Notes

- Do not add database connections or SQL execution.
- Do not write project-specific business terms into global memory tests except as forbidden-token rejection cases.
- Do not make background capture write approved memory.
- Do not run `git rm --cached` except in a test fixture or explicit Git guard command with `--untrack`.
- Preserve Chinese duplicate detection behavior from v1.
- Keep every script dependency-free.

## Self-Review Checklist

- Spec Section 4 maps to Tasks 1, 2, 4, and 5.
- Spec Section 5 maps to Tasks 2, 3, and 5.
- Spec Section 6 maps to Task 4.
- Spec Section 7 maps to Task 5.
- Spec Section 8 maps to Tasks 1-5.
- Spec Section 9 maps to Task 6.
- Spec Sections 10-13 map to Tasks 6 and 7.
- No task depends on hardcoded `/Users/dalwin` paths.
- Every new runtime behavior has a failing test before implementation.
- Every task has an explicit verification command and commit command.

