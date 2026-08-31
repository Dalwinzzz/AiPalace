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
        self.assertIn("sanitiz", stderr.lower())


if __name__ == "__main__":
    unittest.main()
