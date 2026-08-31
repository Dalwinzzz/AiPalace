#!/usr/bin/env python3
"""TDD for gather_sessions.py —— sweep 纯读取器(无 LLM/subprocess)。"""
import json
import os
import sys
import tempfile
import time
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gather_sessions as gs  # noqa: E402


class WalkUserText(unittest.TestCase):
    def test_claude_and_codex_schemas(self):
        claude_obj = {"type": "user", "message": {"role": "user", "content": [
            {"type": "text", "text": "修一下这个 bug"}]}}
        codex_obj = {"payload": {"type": "message", "role": "user", "content": [
            {"type": "input_text", "text": "别用 pytest,用 unittest"}]}}
        self.assertEqual(gs.walk_user_text(claude_obj), ["修一下这个 bug"])
        self.assertEqual(gs.walk_user_text(codex_obj), ["别用 pytest,用 unittest"])
        self.assertEqual(gs.walk_user_text({"role": "assistant", "content": "回答"}), [])


class Gather(unittest.TestCase):
    def _mk(self, td: str):
        root = Path(td)
        cdir = root / "claude" / "proj"
        cdir.mkdir(parents=True)
        f = cdir / "s1.jsonl"
        f.write_text(json.dumps(
            {"type": "user", "message": {"role": "user", "content": "记住:提交前跑全量测试"}},
            ensure_ascii=False) + "\n", encoding="utf-8")
        cfg = {"sweep": {"days": 7, "max_files": 40, "max_user_turns_per_file": 60,
                         "claude_projects": str(root / "claude"),
                         "codex_sessions": [str(root / "codex")]}}
        return root, f, cfg

    def test_blob_ledger_and_skip(self):
        with tempfile.TemporaryDirectory() as td:
            root, f, cfg = self._mk(td)
            ledger = root / "ledger.json"
            blob = gs.gather(cfg, days=None, commit_ledger=True, ledger_path=ledger)
            self.assertIn("提交前跑全量测试", blob)
            self.assertIn(str(f), json.loads(ledger.read_text(encoding="utf-8"))["swept"])
            blob2 = gs.gather(cfg, days=None, commit_ledger=False, ledger_path=ledger)
            self.assertEqual(blob2, "")   # 已入账,跳过

    def test_mtime_cutoff(self):
        with tempfile.TemporaryDirectory() as td:
            root, f, cfg = self._mk(td)
            old = time.time() - 30 * 86400
            os.utime(f, (old, old))
            blob = gs.gather(cfg, days=7, commit_ledger=False,
                             ledger_path=root / "ledger.json")
            self.assertEqual(blob, "")

    def test_codex_real_schema_extracted(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            xdir = root / "codex" / "2026" / "07" / "02"
            xdir.mkdir(parents=True)
            f = xdir / "rollout-s2.jsonl"
            f.write_text(json.dumps(
                {"payload": {"type": "message", "role": "user", "content": [
                    {"type": "input_text", "text": "别用 pytest,用 unittest"}]}},
                ensure_ascii=False) + "\n", encoding="utf-8")
            cfg = {"sweep": {"days": 7, "max_files": 40, "max_user_turns_per_file": 60,
                             "claude_projects": str(root / "claude"),
                             "codex_sessions": [str(root / "codex")]}}
            blob = gs.gather(cfg, days=None, commit_ledger=False,
                             ledger_path=root / "ledger.json")
            self.assertIn("别用 pytest,用 unittest", blob)
            self.assertIn("[codex rollout-s2]", blob)

    def test_empty_extraction_not_ledgered(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            cdir = root / "claude" / "proj"
            cdir.mkdir(parents=True)
            f = cdir / "assistant-only.jsonl"
            f.write_text(json.dumps(
                {"type": "assistant", "message": {"role": "assistant", "content": "回答"}},
                ensure_ascii=False) + "\n", encoding="utf-8")
            cfg = {"sweep": {"days": 7, "max_files": 40, "max_user_turns_per_file": 60,
                             "claude_projects": str(root / "claude"),
                             "codex_sessions": [str(root / "codex")]}}
            ledger = root / "ledger.json"
            blob = gs.gather(cfg, days=None, commit_ledger=True, ledger_path=ledger)
            self.assertEqual(blob, "")
            self.assertNotIn(str(f), json.loads(ledger.read_text(encoding="utf-8"))["swept"])


if __name__ == "__main__":
    unittest.main()
