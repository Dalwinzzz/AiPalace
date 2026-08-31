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
