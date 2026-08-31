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


def run_process(script: Path, args: list[str], env: dict[str, str] | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(script)] + args,
        capture_output=True,
        text=True,
        env=env,
    )


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
            self.assertIn("approved/rules/", result["file"])

    def test_explicit_capture_without_boundaries_goes_to_candidate(self):
        with tempfile.TemporaryDirectory() as td:
            env = os.environ.copy()
            env["SQL_EXPERT_DBA_MEMORY_DIR"] = str(Path(td) / "global-memory")
            result = run_json(MEMORY_CAPTURE, [
                "--title", "缺少边界的显式沉淀",
                "--type", "rule",
                "--workflow", "sql-query-optimizer",
                "--problem-pattern", "SELECT star in production query",
                "--conclusion", "Use explicit projection",
                "--capture-mode", "explicit_user_requested",
            ], env=env)
            self.assertEqual(result["review_status"], "candidate")
            self.assertIn("candidates/rules/", result["file"])

    def test_explicit_low_confidence_goes_to_candidate(self):
        with tempfile.TemporaryDirectory() as td:
            env = os.environ.copy()
            env["SQL_EXPERT_DBA_MEMORY_DIR"] = str(Path(td) / "global-memory")
            result = run_json(MEMORY_CAPTURE, [
                "--title", "低置信度显式沉淀",
                "--type", "rule",
                "--problem-pattern", "低置信度规则需要复核",
                "--conclusion", "证据不足时进入候选区",
                "--confidence", "low",
                "--capture-mode", "explicit_user_requested",
            ], env=env)
            self.assertEqual(result["review_status"], "candidate")
            self.assertIn("candidates/rules/", result["file"])

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

    def test_auto_automation_forces_candidate(self):
        with tempfile.TemporaryDirectory() as td:
            env = os.environ.copy()
            env["SQL_EXPERT_DBA_MEMORY_DIR"] = str(Path(td) / "global-memory")
            result = run_json(MEMORY_CAPTURE, [
                "--title", "自动化候选",
                "--type", "template",
                "--problem-pattern", "自动化沉淀的模板需要复核",
                "--conclusion", "自动化路径只能进入候选区",
                "--capture-mode", "auto_automation",
                "--force-approved",
                "--promotion-reason", "high-reuse-template",
            ], env=env)
            self.assertEqual(result["review_status"], "candidate")
            self.assertIn("candidates/templates/", result["file"])

    def test_auto_background_forces_candidate_when_explicit(self):
        with tempfile.TemporaryDirectory() as td:
            mem = Path(td) / "global-memory"
            result = run_json(MEMORY_CAPTURE, [
                "--memory-dir", str(mem),
                "--title", "后台自动候选",
                "--type", "case",
                "--problem-pattern", "显式 auto_background 不能强制审核通过",
                "--conclusion", "后台兼容模式仍应进入候选区",
                "--capture-mode", "auto_background",
                "--force-approved",
            ])
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

    def test_rejects_unsanitized_global_memory_tags(self):
        with tempfile.TemporaryDirectory() as td:
            mem = Path(td) / "global-memory"
            result = run_json(MEMORY_CAPTURE, [
                "--memory-dir", str(mem),
                "--title", "标签包含真实表名",
                "--type", "rule",
                "--tags", "orders,report",
                "--problem-pattern", "统计报表标签需要脱敏",
                "--conclusion", "全局记忆标签不能保留真实项目标识",
                "--capture-mode", "explicit_user_requested",
                "--forbidden-token", "orders",
            ])
            self.assertEqual(result["status"], "skipped")
            self.assertEqual(result["reason"], "unsanitized_global_memory")
            self.assertEqual(list(mem.rglob("*.md")), [])

    def test_rejects_unsanitized_global_memory_metadata(self):
        with tempfile.TemporaryDirectory() as td:
            mem = Path(td) / "global-memory"
            result = run_json(MEMORY_CAPTURE, [
                "--memory-dir", str(mem),
                "--title", "元数据包含项目标识",
                "--type", "rule",
                "--workflow", "secret_project",
                "--origin-skill", "secret_project",
                "--problem-pattern", "元数据也需要脱敏",
                "--conclusion", "workflow 和 origin_skill 会持久化",
                "--capture-mode", "explicit_user_requested",
                "--forbidden-token", "secret_project",
            ])
            self.assertEqual(result["status"], "skipped")
            self.assertEqual(result["reason"], "unsanitized_global_memory")
            self.assertEqual(list(mem.rglob("*.md")), [])

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

    def test_search_includes_candidates_only_when_requested(self):
        with tempfile.TemporaryDirectory() as td:
            global_mem = Path(td) / "global"
            (global_mem / "approved" / "rules").mkdir(parents=True)
            (global_mem / "candidates" / "rules").mkdir(parents=True)
            approved_entry = """---
id: approved-001
title: 审核规则
type: rule
workflow: sql-query-optimizer
dialect: universal
tags: [index]
problem_pattern: 候选过滤测试
conclusion: approved
review_status: approved
---

# 审核规则
"""
            candidate_entry = approved_entry.replace("approved-001", "candidate-001").replace("approved", "candidate")
            (global_mem / "approved" / "rules" / "approved.md").write_text(approved_entry, encoding="utf-8")
            (global_mem / "candidates" / "rules" / "candidate.md").write_text(candidate_entry, encoding="utf-8")

            default_results = run_json(MEMORY_SEARCH, [
                "--memory-dir", str(global_mem),
                "--seed-memory-dir", str(Path(td) / "missing-seed"),
                "--pattern", "候选过滤测试",
            ])
            self.assertEqual({entry["id"] for entry in default_results}, {"approved-001"})

            all_results = run_json(MEMORY_SEARCH, [
                "--memory-dir", str(global_mem),
                "--seed-memory-dir", str(Path(td) / "missing-seed"),
                "--pattern", "候选过滤测试",
                "--include-candidates",
            ])
            self.assertEqual({entry["id"] for entry in all_results}, {"approved-001", "candidate-001"})

    def test_search_falls_back_when_index_entry_is_structurally_damaged(self):
        with tempfile.TemporaryDirectory() as td:
            mem = Path(td) / "global"
            (mem / "approved" / "rules").mkdir(parents=True)
            (mem / "approved" / "rules" / "existing.md").write_text("""---
id: damaged-search-001
title: 损坏搜索索引已有规则
type: rule
workflow: sql-query-optimizer
dialect: universal
tags: [index]
problem_pattern: 损坏搜索索引时应扫描 Markdown
conclusion: 搜索不能信任缺少 file 的非空索引
review_status: approved
---

# 损坏搜索索引已有规则
""", encoding="utf-8")
            (mem / "index.json").write_text(
                json.dumps({"version": 2, "entries": [{"id": "stale-only"}]}),
                encoding="utf-8",
            )

            results = run_json(MEMORY_SEARCH, [
                "--memory-dir", str(mem),
                "--seed-memory-dir", str(Path(td) / "missing-seed"),
                "--pattern", "扫描 Markdown",
            ])
            self.assertEqual({entry["id"] for entry in results}, {"damaged-search-001"})

    def test_search_falls_back_when_index_tags_is_not_list(self):
        with tempfile.TemporaryDirectory() as td:
            mem = Path(td) / "global"
            (mem / "approved" / "rules").mkdir(parents=True)
            (mem / "approved" / "rules" / "existing.md").write_text("""---
id: string-tags-search-001
title: 字符串标签索引已有规则
type: rule
workflow: sql-query-optimizer
dialect: universal
tags: [index]
problem_pattern: 字符串标签索引时应扫描 Markdown
conclusion: 搜索不能让错误 tags 类型隐藏 Markdown
review_status: approved
---

# 字符串标签索引已有规则
""", encoding="utf-8")
            (mem / "index.json").write_text(
                json.dumps({
                    "version": 2,
                    "entries": [{
                        "id": "string-tags-search-001",
                        "file": "approved/rules/existing.md",
                        "title": "字符串标签索引已有规则",
                        "workflow": "sql-query-optimizer",
                        "dialect": "universal",
                        "review_status": "approved",
                        "problem_pattern": "字符串标签索引时应扫描 Markdown",
                        "conclusion": "搜索不能让错误 tags 类型隐藏 Markdown",
                        "tags": "index",
                    }],
                }),
                encoding="utf-8",
            )

            results = run_json(MEMORY_SEARCH, [
                "--memory-dir", str(mem),
                "--seed-memory-dir", str(Path(td) / "missing-seed"),
                "--tags", "index",
            ])
            self.assertEqual({entry["id"] for entry in results}, {"string-tags-search-001"})

    def test_search_falls_back_when_index_root_is_list(self):
        with tempfile.TemporaryDirectory() as td:
            mem = Path(td) / "global"
            (mem / "approved" / "rules").mkdir(parents=True)
            (mem / "approved" / "rules" / "existing.md").write_text("""---
id: list-root-search-001
title: 列表根索引已有规则
type: rule
workflow: sql-query-optimizer
dialect: universal
tags: [index]
problem_pattern: 列表根索引时应扫描 Markdown
conclusion: 搜索遇到 list root 不能崩溃
review_status: approved
---

# 列表根索引已有规则
""", encoding="utf-8")
            (mem / "index.json").write_text(
                json.dumps([{"id": "stale-only"}]),
                encoding="utf-8",
            )

            results = run_json(MEMORY_SEARCH, [
                "--memory-dir", str(mem),
                "--seed-memory-dir", str(Path(td) / "missing-seed"),
                "--pattern", "list root 不能崩溃",
            ])
            self.assertEqual({entry["id"] for entry in results}, {"list-root-search-001"})

    def test_search_falls_back_when_index_review_status_is_not_string(self):
        with tempfile.TemporaryDirectory() as td:
            mem = Path(td) / "global"
            (mem / "approved" / "rules").mkdir(parents=True)
            (mem / "approved" / "rules" / "existing.md").write_text("""---
id: bool-status-search-001
title: 布尔状态索引已有规则
type: rule
workflow: sql-query-optimizer
dialect: universal
tags: [index]
problem_pattern: 布尔 review_status 索引时应扫描 Markdown
conclusion: 搜索不能让错误状态类型隐藏 Markdown
review_status: approved
---

# 布尔状态索引已有规则
""", encoding="utf-8")
            (mem / "index.json").write_text(
                json.dumps({
                    "version": 2,
                    "entries": [{
                        "id": "bool-status-search-001",
                        "file": "approved/rules/existing.md",
                        "title": "布尔状态索引已有规则",
                        "workflow": "sql-query-optimizer",
                        "dialect": "universal",
                        "review_status": True,
                        "problem_pattern": "布尔 review_status 索引时应扫描 Markdown",
                        "conclusion": "搜索不能让错误状态类型隐藏 Markdown",
                        "tags": ["index"],
                    }],
                }),
                encoding="utf-8",
            )

            results = run_json(MEMORY_SEARCH, [
                "--memory-dir", str(mem),
                "--seed-memory-dir", str(Path(td) / "missing-seed"),
                "--pattern", "错误状态类型隐藏",
            ])
            self.assertEqual({entry["id"] for entry in results}, {"bool-status-search-001"})

    def test_search_falls_back_when_index_id_is_not_string(self):
        with tempfile.TemporaryDirectory() as td:
            mem = Path(td) / "global"
            (mem / "approved" / "rules").mkdir(parents=True)
            (mem / "approved" / "rules" / "existing.md").write_text("""---
id: id-list-search-001
title: 列表 ID 索引已有规则
type: rule
workflow: sql-query-optimizer
dialect: universal
tags: [index]
problem_pattern: 列表 id 索引时应扫描 Markdown
conclusion: 搜索不能返回非字符串 id
review_status: approved
---

# 列表 ID 索引已有规则
""", encoding="utf-8")
            (mem / "index.json").write_text(
                json.dumps({
                    "version": 2,
                    "entries": [{
                        "id": ["id-list-search-001"],
                        "file": "approved/rules/existing.md",
                        "title": "列表 ID 索引已有规则",
                        "workflow": "sql-query-optimizer",
                        "dialect": "universal",
                        "review_status": "approved",
                        "problem_pattern": "列表 id 索引时应扫描 Markdown",
                        "conclusion": "搜索不能返回非字符串 id",
                        "tags": ["index"],
                    }],
                }),
                encoding="utf-8",
            )

            results = run_json(MEMORY_SEARCH, [
                "--memory-dir", str(mem),
                "--seed-memory-dir", str(Path(td) / "missing-seed"),
                "--pattern", "非字符串 id",
            ])
            self.assertEqual({entry["id"] for entry in results}, {"id-list-search-001"})

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

    def test_capture_rebuilds_corrupt_index_before_appending(self):
        with tempfile.TemporaryDirectory() as td:
            mem = Path(td) / "global"
            (mem / "approved" / "rules").mkdir(parents=True)
            (mem / "approved" / "rules" / "existing.md").write_text("""---
id: existing-001
title: 已有规则
type: rule
workflow: sql-query-optimizer
dialect: universal
tags: [index]
problem_pattern: 已有索引规则仍应可检索
conclusion: 已有结论不能因为索引损坏而丢失
review_status: approved
---

# 已有规则
""", encoding="utf-8")
            (mem / "index.json").write_text("{not-json", encoding="utf-8")

            result = run_json(MEMORY_CAPTURE, [
                "--memory-dir", str(mem),
                "--title", "新增规则",
                "--type", "rule",
                "--problem-pattern", "新增索引规则",
                "--conclusion", "新增结论",
                "--capture-mode", "explicit_user_requested",
            ])
            self.assertEqual(result["status"], "captured")

            search_results = run_json(MEMORY_SEARCH, [
                "--memory-dir", str(mem),
                "--seed-memory-dir", str(Path(td) / "missing-seed"),
                "--pattern", "已有索引规则",
            ])
            self.assertEqual({entry["id"] for entry in search_results}, {"existing-001"})
            index = json.loads((mem / "index.json").read_text(encoding="utf-8"))
            self.assertIn("existing-001", {entry["id"] for entry in index["entries"]})

    def test_capture_rebuilds_empty_index_before_appending(self):
        with tempfile.TemporaryDirectory() as td:
            mem = Path(td) / "global"
            (mem / "approved" / "rules").mkdir(parents=True)
            (mem / "approved" / "rules" / "existing.md").write_text("""---
id: existing-empty-001
title: 空索引已有规则
type: rule
workflow: sql-query-optimizer
dialect: universal
tags: [index]
problem_pattern: 空索引场景已有规则仍应可检索
conclusion: 捕获新记忆不能隐藏已有 Markdown
review_status: approved
---

# 空索引已有规则
""", encoding="utf-8")
            (mem / "index.json").write_text(
                json.dumps({"version": 2, "last_updated": "", "entries": []}),
                encoding="utf-8",
            )

            result = run_json(MEMORY_CAPTURE, [
                "--memory-dir", str(mem),
                "--title", "空索引新增规则",
                "--type", "rule",
                "--problem-pattern", "空索引新增规则",
                "--conclusion", "新增结论",
                "--capture-mode", "explicit_user_requested",
            ])
            self.assertEqual(result["status"], "captured")

            search_results = run_json(MEMORY_SEARCH, [
                "--memory-dir", str(mem),
                "--seed-memory-dir", str(Path(td) / "missing-seed"),
                "--pattern", "空索引场景已有规则",
            ])
            self.assertEqual({entry["id"] for entry in search_results}, {"existing-empty-001"})

    def test_capture_escapes_multiline_frontmatter_and_validate_passes(self):
        with tempfile.TemporaryDirectory() as td:
            mem = Path(td) / "global"
            conclusion = "第一行结论\n第二行结论: 包含冒号"
            result = run_json(MEMORY_CAPTURE, [
                "--memory-dir", str(mem),
                "--title", "多行结论",
                "--type", "case",
                "--problem-pattern", "多行 front matter 不应截断",
                "--conclusion", conclusion,
                "--capture-mode", "explicit_user_requested",
            ])
            self.assertEqual(result["status"], "captured")

            validate = run_json(MEMORY_INDEX, ["--memory-dir", str(mem), "--validate"])
            self.assertTrue(validate["consistent"], validate.get("issues"))
            index = json.loads((mem / "index.json").read_text(encoding="utf-8"))
            entry = next(item for item in index["entries"] if item["id"] == result["id"])
            self.assertEqual(entry["conclusion"], "第一行结论\\n第二行结论: 包含冒号")

    def test_capture_normalizes_multiline_tags_and_validate_passes(self):
        with tempfile.TemporaryDirectory() as td:
            mem = Path(td) / "global"
            result = run_json(MEMORY_CAPTURE, [
                "--memory-dir", str(mem),
                "--title", "多行标签",
                "--type", "rule",
                "--tags", "index\nslow,report",
                "--problem-pattern", "多行 tags 不应破坏 front matter",
                "--conclusion", "tags 中的换行应被空格替换",
                "--capture-mode", "explicit_user_requested",
            ])
            self.assertEqual(result["status"], "captured")

            validate = run_json(MEMORY_INDEX, ["--memory-dir", str(mem), "--validate"])
            self.assertTrue(validate["consistent"], validate.get("issues"))
            index = json.loads((mem / "index.json").read_text(encoding="utf-8"))
            entry = next(item for item in index["entries"] if item["id"] == result["id"])
            self.assertEqual(entry["tags"], ["index slow", "report"])
            self.assertFalse(any("\n" in tag or "\r" in tag for tag in entry["tags"]))

    def test_validate_reports_structurally_damaged_index_without_crashing(self):
        with tempfile.TemporaryDirectory() as td:
            mem = Path(td) / "global"
            (mem / "approved" / "rules").mkdir(parents=True)
            (mem / "approved" / "rules" / "existing.md").write_text("""---
id: damaged-existing-001
title: 损坏索引已有规则
type: rule
workflow: sql-query-optimizer
dialect: universal
tags: [index]
problem_pattern: 结构损坏索引下已有规则仍应恢复
conclusion: validate 应报告问题而不是崩溃
review_status: approved
---

# 损坏索引已有规则
""", encoding="utf-8")
            (mem / "index.json").write_text(
                json.dumps({"version": 2, "entries": [{"id": "x"}]}),
                encoding="utf-8",
            )

            validate_process = run_process(MEMORY_INDEX, ["--memory-dir", str(mem), "--validate"])
            self.assertEqual(validate_process.returncode, 0, validate_process.stderr)
            validate = json.loads(validate_process.stdout)
            self.assertFalse(validate["consistent"])
            self.assertGreater(validate["issues_count"], 0)

            result = run_json(MEMORY_CAPTURE, [
                "--memory-dir", str(mem),
                "--title", "结构损坏索引新增规则",
                "--type", "rule",
                "--problem-pattern", "结构损坏索引新增规则",
                "--conclusion", "capture 应重建并保留已有文件",
                "--capture-mode", "explicit_user_requested",
            ])
            self.assertEqual(result["status"], "captured")

            search_results = run_json(MEMORY_SEARCH, [
                "--memory-dir", str(mem),
                "--seed-memory-dir", str(Path(td) / "missing-seed"),
                "--pattern", "结构损坏索引下已有规则",
            ])
            self.assertEqual({entry["id"] for entry in search_results}, {"damaged-existing-001"})

    def test_explicit_missing_memory_dir_errors(self):
        with tempfile.TemporaryDirectory() as td:
            missing = Path(td) / "does-not-exist"
            result = run_process(MEMORY_SEARCH, [
                "--memory-dir", str(missing),
                "--seed-memory-dir", str(Path(td) / "missing-seed"),
                "--pattern", "anything",
            ])
            self.assertNotEqual(result.returncode, 0)
            payload = json.loads(result.stdout)
            self.assertIn("Memory directory not found", payload["error"])


if __name__ == "__main__":
    unittest.main()
