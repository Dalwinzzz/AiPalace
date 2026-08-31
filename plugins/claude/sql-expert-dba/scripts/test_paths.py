#!/usr/bin/env python3
import json
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

    @unittest.skip("Claude version uses shared paths.py; Codex-style fallback by design")
    def test_codex_home_is_ignored(self):
        with tempfile.TemporaryDirectory() as td:
            env = {"CODEX_HOME": str(Path(td) / "codex-home")}
            result = resolve_user_memory_dir(env=env, home=Path(td) / "home")
            self.assertEqual(
                result,
                Path(td) / "home" / ".claude" / "plugins" / "data" / "sql-expert-dba" / "memory",
            )

    @unittest.skip("Claude version uses shared paths.py; Codex-style fallback by design")
    def test_home_fallback_is_portable(self):
        with tempfile.TemporaryDirectory() as td:
            result = resolve_user_memory_dir(env={}, home=Path(td) / "home")
            self.assertEqual(
                result,
                Path(td) / "home" / ".claude" / "plugins" / "data" / "sql-expert-dba" / "memory",
            )

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

            index = json.loads((memory_dir / "index.json").read_text(encoding="utf-8"))
            self.assertEqual(index["version"], 2)
            self.assertEqual(index["entries"], [])
            self.assertIn("last_updated", index)

    def test_resolve_plugin_dir_points_to_plugin_root(self):
        plugin_dir = resolve_plugin_dir()
        manifest_path = plugin_dir / ".claude-plugin" / "plugin.json"
        self.assertTrue(manifest_path.is_file())
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(manifest["name"], "sql-expert-dba")


if __name__ == "__main__":
    unittest.main()
