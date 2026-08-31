#!/usr/bin/env python3
"""TDD for sessionstart.py —— 合并 cwd 域打分 + AiPalace INDEX 注入的 SessionStart hook。

stdlib unittest，零依赖：python3 -m unittest tools.hooks.test_sessionstart
或在本目录：python3 -m unittest test_sessionstart
"""
import contextlib
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sessionstart  # noqa: E402


class ComputeConfidence(unittest.TestCase):
    def _score(self, path):
        return sessionstart.compute_confidence(Path(path))

    def test_java_project_scores_primary(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "pom.xml").write_text("<project/>")
            (Path(d) / "mvnw").write_text("")
            self.assertGreaterEqual(self._score(d)["java/spring"], 0.5)

    def test_aipalace_dir_scores_ai_build(self):
        # ADR-0007 新增信号：cwd 含 AiPalace → 识别为 ai_build 域（可见，≥噪声地板）
        scores = self._score("/Users/dalwin/Library/CodeRepo/AI/AiPalace")
        self.assertGreaterEqual(scores["ai_build"], 0.3)

    def test_plain_dir_has_no_domain(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertTrue(all(v < 0.3 for v in self._score(d).values()))


class FormatDomain(unittest.TestCase):
    def test_no_domain_message(self):
        out = sessionstart.format_domain(
            {"java/spring": 0.0, "ai_build": 0.0, "knowledge": 0.0, "learning": 0.0},
            Path("/tmp/x"),
        )
        self.assertIn("无主域", out)

    def test_single_primary_java(self):
        out = sessionstart.format_domain(
            {"java/spring": 0.9, "ai_build": 0.0, "knowledge": 0.0, "learning": 0.0},
            Path("/x"),
        )
        self.assertIn("[工作域]", out)
        self.assertIn("java/spring=0.90", out)
        self.assertIn("pack-java", out)

    def test_old_domain_context_pointers_removed(self):
        # ADR-0007：旧 DOMAIN_CONTEXT 扁平指针被 memory/INDEX.md 取代，不应再出现
        out = sessionstart.format_domain(
            {"java/spring": 0.9, "ai_build": 0.0, "knowledge": 0.0, "learning": 0.0},
            Path("/x"),
        )
        self.assertNotIn("syzh.md", out)
        self.assertNotIn("glossary.md", out)
        self.assertNotIn("dalwin-workflow", out)


class BuildPack(unittest.TestCase):
    def test_java_pack_includes_zhijin_project_skills(self):
        # registry 驱动：java/spring 动态含 project:zhijin 的 skill（修复旧清单漏掉它们）
        pack = sessionstart.build_pack("java/spring")
        self.assertIn("ownerpowers", pack)
        self.assertIn("biz-workflow", pack)

    def test_drops_drifted_registry_names(self):
        # 仅提供 git-merge-conductor：DOMAIN_EXTRA 里不在 registry 的裸名应被剔除
        skills = {"git-merge-conductor": dict(source="mine", category="method",
                                              tier="core", project=None)}
        pack = sessionstart.build_pack("java/spring", skills)
        self.assertIn("git-merge-conductor", pack)
        self.assertNotIn("grill-with-docs", pack)        # 不在所给 registry → 剔除

    def test_keeps_bundled_prefixed_even_with_empty_registry(self):
        pack = sessionstart.build_pack("java/spring", {})
        self.assertIn("requesting-code-review", pack)     # '+' 兜底名恒保留
        self.assertNotIn("+requesting-code-review", pack)  # 输出已去前缀

    def test_project_skills_sorted_first(self):
        skills = {
            "ownerpowers": dict(source="mine", category="workflow", tier="project", project="zhijin"),
            "biz-workflow": dict(source="mine", category="workflow", tier="project", project="zhijin"),
        }
        pack = sessionstart.build_pack("java/spring", skills)
        self.assertEqual(pack[:2], ["biz-workflow", "ownerpowers"])  # project skill 排前且有序


class ResolveContextRoot(unittest.TestCase):
    def test_env_override_wins(self):
        with tempfile.TemporaryDirectory() as d:
            os.environ["AIPALACE_CONTEXT"] = d
            try:
                self.assertEqual(sessionstart.resolve_context_root(), d)
            finally:
                del os.environ["AIPALACE_CONTEXT"]

    def test_realpath_derivation_resolves_to_existing_context(self):
        os.environ.pop("AIPALACE_CONTEXT", None)
        root = sessionstart.resolve_context_root()
        self.assertTrue(root.endswith(os.path.join("vault", "memory")))
        self.assertTrue(os.path.isdir(root), f"{root} 应为存在的目录")


class BuildOutput(unittest.TestCase):
    def _ctx(self, tmp):
        ctx = Path(tmp) / "vault" / "memory"
        ctx.mkdir(parents=True)
        (ctx / "INDEX.md").write_text("# VAULT-INDEX-MARKER", encoding="utf-8")
        return str(ctx)

    def test_includes_domain_hint_and_vault_index(self):
        with tempfile.TemporaryDirectory() as d:
            out = sessionstart.build_output(Path("/some/plain"), self._ctx(d))
            self.assertIn("[工作域]", out)
            self.assertIn("VAULT-INDEX-MARKER", out)

    def test_operating_rules_injected_before_index(self):
        with tempfile.TemporaryDirectory() as d:
            ctx = self._ctx(d)
            rules_dir = Path(ctx) / "00-RULES"
            rules_dir.mkdir()
            (rules_dir / "operating-rules.md").write_text("[操作规则]-MARKER", encoding="utf-8")
            out = sessionstart.build_output(Path("/some/plain"), ctx)
            self.assertIn("[操作规则]-MARKER", out)
            self.assertLess(out.index("[操作规则]-MARKER"), out.index("VAULT-INDEX-MARKER"))


class MainIntegration(unittest.TestCase):
    def test_main_emits_valid_sessionstart_json_with_index(self):
        with tempfile.TemporaryDirectory() as d:
            ctx = Path(d) / "vault" / "memory"
            ctx.mkdir(parents=True)
            (ctx / "INDEX.md").write_text("# VMARK", encoding="utf-8")
            os.environ["AIPALACE_CONTEXT"] = str(ctx)
            try:
                buf = io.StringIO()
                with contextlib.redirect_stdout(buf):
                    sessionstart.main(stdin=io.StringIO(json.dumps({"cwd": "/some/plain"})))
                payload = json.loads(buf.getvalue())
                hso = payload["hookSpecificOutput"]
                self.assertEqual(hso["hookEventName"], "SessionStart")
                self.assertIn("VMARK", hso["additionalContext"])
            finally:
                del os.environ["AIPALACE_CONTEXT"]

    def test_main_survives_bad_stdin(self):
        # stdin 非法 JSON 时不抛、仍输出合法 SessionStart（always-on 注入兜底）
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            sessionstart.main(stdin=io.StringIO("not-json"))
        payload = json.loads(buf.getvalue())
        self.assertEqual(payload["hookSpecificOutput"]["hookEventName"], "SessionStart")


if __name__ == "__main__":
    unittest.main()
