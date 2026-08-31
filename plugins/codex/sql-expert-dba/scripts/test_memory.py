#!/usr/bin/env python3
"""
Automated tests for SQL Expert DBA memory subsystem.

Covers:
1. Index rebuild vs validate consistency
2. Pattern search through the index
3. Pattern search through scan fallback
4. Chinese duplicate detection behavior
5. Approved vs candidate routing policy
6. Malformed or incomplete front matter handling

Usage:
    python3 test_memory.py
    python3 -m pytest test_memory.py -v
"""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent
MEMORY_INDEX = SCRIPTS_DIR / "memory_index.py"
MEMORY_SEARCH = SCRIPTS_DIR / "memory_search.py"
MEMORY_CAPTURE = SCRIPTS_DIR / "memory_capture.py"

# Seed entry used across tests
SEED_RULE = """\
---
id: rule-001
title: 隐式类型转换导致索引失效
type: rule
workflow: sql-query-optimizer
dialect: mysql
tags: [index, type-conversion, performance]
problem_pattern: WHERE 条件中字段类型与比较值类型不一致
preconditions: 索引字段为字符串类型
conclusion: MySQL 会对索引字段做隐式类型转换导致全表扫描
boundaries: 仅影响字符串字段比较数字场景
confidence: high
review_status: approved
last_reviewed_at: 2026-04-09
origin_skill: sql-query-optimizer
capture_mode: auto_background
---

# 隐式类型转换导致索引失效
"""

SEED_TEMPLATE = """\
---
id: template-001
title: 日统计报表基础模板
type: template
workflow: sql-report-query-builder
dialect: universal
tags: [report, statistics, template]
problem_pattern: 需要按日期维度统计业务指标
preconditions: 存在业务主表
conclusion: 提供通用日统计报表 SQL 模板
boundaries: 仅适用于单表日粒度统计
confidence: high
review_status: approved
last_reviewed_at: 2026-04-09
origin_skill: sql-report-query-builder
capture_mode: explicit_user_requested
---

# 日统计报表基础模板
"""


def _make_memory_dir(tmp: Path) -> Path:
    """Create a memory directory with seed files."""
    mem = tmp / "memory"
    mem.mkdir()
    for subdir in ("rules", "templates", "candidates", "glossary", "cases"):
        (mem / subdir).mkdir()
    (mem / "rules" / "rule-001-implicit-type-conversion.md").write_text(SEED_RULE)
    (mem / "templates" / "template-001-daily-statistics.md").write_text(SEED_TEMPLATE)
    return mem


def _run_script(script: Path, args: list[str]) -> dict:
    """Run a memory script and parse JSON output."""
    result = subprocess.run(
        [sys.executable, str(script)] + args,
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"{script.name} failed: {result.stderr}")
    return json.loads(result.stdout)


class TestIndexConsistency(unittest.TestCase):
    """Test 1: Index rebuild vs validate consistency."""

    def test_rebuild_then_validate(self):
        with tempfile.TemporaryDirectory() as td:
            mem = _make_memory_dir(Path(td))
            _run_script(MEMORY_INDEX, ["--memory-dir", str(mem), "--rebuild"])
            result = _run_script(MEMORY_INDEX, ["--memory-dir", str(mem), "--validate"])
            self.assertTrue(result["consistent"], f"Issues: {result.get('issues')}")
            self.assertEqual(result["total_indexed"], 2)
            self.assertEqual(result["total_files"], 2)

    def test_rebuild_includes_new_fields(self):
        """Index entries should contain problem_pattern and conclusion."""
        with tempfile.TemporaryDirectory() as td:
            mem = _make_memory_dir(Path(td))
            _run_script(MEMORY_INDEX, ["--memory-dir", str(mem), "--rebuild"])
            index = json.loads((mem / "index.json").read_text())
            rule = next(e for e in index["entries"] if e["id"] == "rule-001")
            self.assertIn("problem_pattern", rule)
            self.assertIn("conclusion", rule)
            self.assertIn("全表扫描", rule["conclusion"])

    def test_validate_detects_corrupted_conclusion(self):
        """Validate should catch corrupted search-relevant fields."""
        with tempfile.TemporaryDirectory() as td:
            mem = _make_memory_dir(Path(td))
            _run_script(MEMORY_INDEX, ["--memory-dir", str(mem), "--rebuild"])
            # Corrupt the conclusion field in index.json
            index = json.loads((mem / "index.json").read_text())
            for e in index["entries"]:
                if e["id"] == "rule-001":
                    e["conclusion"] = "CORRUPTED"
            (mem / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=2))
            result = _run_script(MEMORY_INDEX, ["--memory-dir", str(mem), "--validate"])
            self.assertFalse(result["consistent"])
            fields = [i["field"] for i in result["issues"] if i["type"] == "field_mismatch"]
            self.assertIn("conclusion", fields)

    def test_validate_detects_corrupted_review_status(self):
        """Validate should catch corrupted review_status."""
        with tempfile.TemporaryDirectory() as td:
            mem = _make_memory_dir(Path(td))
            _run_script(MEMORY_INDEX, ["--memory-dir", str(mem), "--rebuild"])
            index = json.loads((mem / "index.json").read_text())
            for e in index["entries"]:
                if e["id"] == "rule-001":
                    e["review_status"] = "wrong_status"
            (mem / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=2))
            result = _run_script(MEMORY_INDEX, ["--memory-dir", str(mem), "--validate"])
            self.assertFalse(result["consistent"])
            fields = [i["field"] for i in result["issues"] if i["type"] == "field_mismatch"]
            self.assertIn("review_status", fields)


class TestPatternSearchViaIndex(unittest.TestCase):
    """Test 2: Pattern search through the index."""

    def test_search_by_conclusion_keyword(self):
        """Search for a keyword in conclusion field via index."""
        with tempfile.TemporaryDirectory() as td:
            mem = _make_memory_dir(Path(td))
            _run_script(MEMORY_INDEX, ["--memory-dir", str(mem), "--rebuild"])
            results = _run_script(MEMORY_SEARCH, [
                "--memory-dir", str(mem), "--pattern", "全表扫描",
            ])
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0]["id"], "rule-001")

    def test_search_by_problem_pattern_keyword(self):
        """Search for a keyword in problem_pattern field via index."""
        with tempfile.TemporaryDirectory() as td:
            mem = _make_memory_dir(Path(td))
            _run_script(MEMORY_INDEX, ["--memory-dir", str(mem), "--rebuild"])
            results = _run_script(MEMORY_SEARCH, [
                "--memory-dir", str(mem), "--pattern", "字段类型",
            ])
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0]["id"], "rule-001")

    def test_search_by_title(self):
        with tempfile.TemporaryDirectory() as td:
            mem = _make_memory_dir(Path(td))
            _run_script(MEMORY_INDEX, ["--memory-dir", str(mem), "--rebuild"])
            results = _run_script(MEMORY_SEARCH, [
                "--memory-dir", str(mem), "--pattern", "日统计",
            ])
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0]["id"], "template-001")


class TestPatternSearchViaScan(unittest.TestCase):
    """Test 3: Pattern search through scan fallback (no index)."""

    def test_search_without_index(self):
        with tempfile.TemporaryDirectory() as td:
            mem = _make_memory_dir(Path(td))
            # No index built — should fall back to file scan
            results = _run_script(MEMORY_SEARCH, [
                "--memory-dir", str(mem), "--pattern", "全表扫描", "--status", "all",
            ])
            self.assertEqual(len(results), 1)


class TestChineseDuplicateDetection(unittest.TestCase):
    """Test 4: Chinese duplicate detection behavior."""

    def test_exact_chinese_duplicate(self):
        """Identical Chinese problem_pattern should be detected as duplicate."""
        with tempfile.TemporaryDirectory() as td:
            mem = _make_memory_dir(Path(td))
            (mem / "index.json").write_text(json.dumps({"version": 1, "entries": [], "last_updated": ""}))
            result = _run_script(MEMORY_CAPTURE, [
                "--memory-dir", str(mem),
                "--title", "重复测试",
                "--type", "rule",
                "--problem-pattern", "WHERE 条件中字段类型与比较值类型不一致",
                "--conclusion", "test",
                "--confidence", "medium",
            ])
            self.assertEqual(result["status"], "skipped")
            self.assertEqual(result["reason"], "duplicate_detected")

    def test_pure_chinese_duplicate(self):
        """Pure Chinese strings without spaces should be detected."""
        with tempfile.TemporaryDirectory() as td:
            mem = _make_memory_dir(Path(td))
            (mem / "index.json").write_text(json.dumps({"version": 1, "entries": [], "last_updated": ""}))
            # Add a Chinese-only entry
            (mem / "rules" / "test-chinese.md").write_text("""\
---
id: test-cn
title: 中文测试
type: rule
problem_pattern: 统计口径不一致导致重复计数
conclusion: 修复口径
review_status: candidate
---
""")
            result = _run_script(MEMORY_CAPTURE, [
                "--memory-dir", str(mem),
                "--title", "另一个重复",
                "--type", "rule",
                "--problem-pattern", "统计口径不一致导致重复计数",
                "--conclusion", "test",
                "--confidence", "medium",
            ])
            self.assertEqual(result["status"], "skipped")
            self.assertEqual(result["reason"], "duplicate_detected")

    def test_different_pattern_not_duplicate(self):
        """Sufficiently different patterns should not be flagged."""
        with tempfile.TemporaryDirectory() as td:
            mem = _make_memory_dir(Path(td))
            (mem / "index.json").write_text(json.dumps({"version": 1, "entries": [], "last_updated": ""}))
            result = _run_script(MEMORY_CAPTURE, [
                "--memory-dir", str(mem),
                "--title", "完全不同",
                "--type", "case",
                "--problem-pattern", "数据库连接池耗尽导致超时",
                "--conclusion", "调整连接池配置",
                "--confidence", "medium",
            ])
            self.assertEqual(result["status"], "captured")


class TestApprovedRouting(unittest.TestCase):
    """Test 5: Approved vs candidate routing policy."""

    def test_high_confidence_without_reason_goes_to_candidate(self):
        """confidence=high without promotion-reason should route to candidate."""
        with tempfile.TemporaryDirectory() as td:
            mem = _make_memory_dir(Path(td))
            (mem / "index.json").write_text(json.dumps({"version": 1, "entries": [], "last_updated": ""}))
            result = _run_script(MEMORY_CAPTURE, [
                "--memory-dir", str(mem),
                "--title", "路由测试A",
                "--type", "rule",
                "--confidence", "high",
                "--problem-pattern", "路由测试模式A不重复的内容",
                "--conclusion", "test routing",
            ])
            self.assertEqual(result["review_status"], "candidate")

    def test_with_valid_promotion_reason_goes_to_approved(self):
        """Valid promotion-reason plus boundaries should route to approved."""
        with tempfile.TemporaryDirectory() as td:
            mem = _make_memory_dir(Path(td))
            (mem / "index.json").write_text(json.dumps({"version": 1, "entries": [], "last_updated": ""}))
            result = _run_script(MEMORY_CAPTURE, [
                "--memory-dir", str(mem),
                "--title", "路由测试B",
                "--type", "rule",
                "--confidence", "high",
                "--problem-pattern", "路由测试模式B不同的内容",
                "--conclusion", "test routing",
                "--boundaries", "validated reusable routing boundary",
                "--promotion-reason", "high-universal-rule",
            ])
            self.assertEqual(result["review_status"], "approved")

    def test_force_approved_overrides(self):
        """--force-approved requires approved validation fields."""
        with tempfile.TemporaryDirectory() as td:
            mem = _make_memory_dir(Path(td))
            (mem / "index.json").write_text(json.dumps({"version": 1, "entries": [], "last_updated": ""}))
            result = _run_script(MEMORY_CAPTURE, [
                "--memory-dir", str(mem),
                "--title", "路由测试C",
                "--type", "case",
                "--confidence", "low",
                "--problem-pattern", "路由测试模式C强制批准",
                "--conclusion", "test",
                "--boundaries", "validated force-approved boundary",
                "--force-approved",
            ])
            self.assertEqual(result["review_status"], "approved")


class TestMalformedFrontmatter(unittest.TestCase):
    """Test 6: Malformed or incomplete front matter handling."""

    def test_no_frontmatter(self):
        """Files without front matter should be ignored by index."""
        with tempfile.TemporaryDirectory() as td:
            mem = _make_memory_dir(Path(td))
            (mem / "rules" / "bad-no-fm.md").write_text("# Just a title\nNo front matter here.\n")
            _run_script(MEMORY_INDEX, ["--memory-dir", str(mem), "--rebuild"])
            index = json.loads((mem / "index.json").read_text())
            ids = [e["id"] for e in index["entries"]]
            self.assertNotIn("", ids)
            # Only the 2 seed entries should be indexed
            self.assertEqual(len(index["entries"]), 2)

    def test_incomplete_frontmatter_missing_id(self):
        """Entries without an id field should not be indexed."""
        with tempfile.TemporaryDirectory() as td:
            mem = _make_memory_dir(Path(td))
            (mem / "rules" / "bad-no-id.md").write_text("""\
---
title: Missing ID
type: rule
---

# Missing ID
""")
            _run_script(MEMORY_INDEX, ["--memory-dir", str(mem), "--rebuild"])
            index = json.loads((mem / "index.json").read_text())
            self.assertEqual(len(index["entries"]), 2)

    def test_empty_file(self):
        """Empty files should not crash the indexer."""
        with tempfile.TemporaryDirectory() as td:
            mem = _make_memory_dir(Path(td))
            (mem / "rules" / "empty.md").write_text("")
            result = _run_script(MEMORY_INDEX, ["--memory-dir", str(mem), "--rebuild"])
            self.assertEqual(result["total"], 2)


if __name__ == "__main__":
    unittest.main()
