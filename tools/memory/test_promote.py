#!/usr/bin/env python3
"""TDD for promote.py —— 审批执行:只动 [x],白名单复验,追加不覆盖,done 防重。"""
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import promote  # noqa: E402

CFG = {
    "routing": {"rules_files": ["00-RULES/ops.md"],
                "projects_prefixes": ["01-PROJECTS/workflow/"]},
}

CAND = ('- [{mark}] {stmt} <!--cand {{"id":"c1-01","action":"{action}","dest":"{dest}",'
        '"type":"decision","scope":"global","freq":2,"score":0.61,"conf":"medium"}}-->')


class Promote(unittest.TestCase):
    def _mk_vault(self, td: str, cand_lines: list[str]) -> Path:
        v = Path(td)
        (v / "00-RULES").mkdir(parents=True)
        (v / "00-RULES" / "ops.md").write_text(
            "---\ntitle: ops\nupdated: 2026-07-01\n---\n\n# 运维规则\n\n- 既有内容\n",
            encoding="utf-8")
        (v / "01-PROJECTS" / "workflow").mkdir(parents=True)
        fb = v / "04-FEEDBACK"
        fb.mkdir(parents=True)
        (fb / "candidates.md").write_text("# 队列\n\n" + "\n".join(cand_lines) + "\n",
                                          encoding="utf-8")
        (fb / "DREAMS.md").write_text("# DREAMS\n", encoding="utf-8")
        return v

    def test_only_checked_promoted_and_done_marked(self):
        lines = [
            CAND.format(mark=" ", stmt="未勾选不动", action="ADD", dest="00-RULES/ops.md"),
            CAND.format(mark="x", stmt="勾选晋升", action="ADD", dest="00-RULES/ops.md"),
        ]
        with tempfile.TemporaryDirectory() as td:
            v = self._mk_vault(td, lines)
            self.assertEqual(promote.promote(dry=False, vault=v, cfg=CFG), 0)
            ops = (v / "00-RULES" / "ops.md").read_text(encoding="utf-8")
            cand = (v / "04-FEEDBACK" / "candidates.md").read_text(encoding="utf-8")
            dreams = (v / "04-FEEDBACK" / "DREAMS.md").read_text(encoding="utf-8")
            self.assertIn("## 蒸馏晋升(待归位)", ops)
            self.assertIn("- 勾选晋升 (", ops)
            self.assertNotIn("未勾选不动 (", ops)
            self.assertIn("- 既有内容", ops)                     # 追加不覆盖
            self.assertRegex(ops, r"updated: \d{4}-\d{2}-\d{2}")
            self.assertNotIn("updated: 2026-07-01", ops)         # updated 已刷新
            self.assertEqual(cand.count("✅<!--done"), 1)
            self.assertIn("· promote", dreams)

    def test_new_project_note_created_with_frontmatter(self):
        lines = [CAND.format(mark="x", stmt="新项目条目", action="ADD",
                             dest="01-PROJECTS/workflow/new-topic.md")]
        with tempfile.TemporaryDirectory() as td:
            v = self._mk_vault(td, lines)
            promote.promote(dry=False, vault=v, cfg=CFG)
            note = (v / "01-PROJECTS" / "workflow" / "new-topic.md").read_text(encoding="utf-8")
            self.assertIn("title: new-topic", note)
            self.assertIn("source: [ai-palace 晋升]", note)
            self.assertIn("## 蒸馏晋升", note)

    def test_new_note_type_correction_clamped_to_feedback(self):
        cand = ('- [x] 纠正类新建 <!--cand {"id":"c1-01","action":"ADD",'
                '"dest":"01-PROJECTS/workflow/corr-topic.md","type":"correction",'
                '"scope":"global","freq":2,"score":0.61,"conf":"medium"}-->')
        with tempfile.TemporaryDirectory() as td:
            v = self._mk_vault(td, [cand])
            promote.promote(dry=False, vault=v, cfg=CFG)
            note = (v / "01-PROJECTS" / "workflow" / "corr-topic.md").read_text(encoding="utf-8")
            self.assertIn("type: feedback", note)

    def test_invalid_noop_and_corrupt_skipped_not_done(self):
        lines = [
            CAND.format(mark="x", stmt="非法落点", action="INVALID", dest="03-MAPS/x.md"),
            CAND.format(mark="x", stmt="已存在", action="NOOP", dest="00-RULES/ops.md"),
            '- [x] 元数据损坏 <!--cand {坏}-->',
            CAND.format(mark="x", stmt="白名单外", action="ADD", dest="02-SOURCES/y.md"),
        ]
        with tempfile.TemporaryDirectory() as td:
            v = self._mk_vault(td, lines)
            promote.promote(dry=False, vault=v, cfg=CFG)
            cand = (v / "04-FEEDBACK" / "candidates.md").read_text(encoding="utf-8")
            ops = (v / "00-RULES" / "ops.md").read_text(encoding="utf-8")
            self.assertNotIn("✅<!--done", cand)      # 全部跳过,无一标 done
            self.assertNotIn("非法落点", ops)

    def test_invalid_action_recovers_when_dest_fixed(self):
        lines = [CAND.format(mark="x", stmt="dest 已修好", action="INVALID",
                             dest="00-RULES/ops.md")]
        with tempfile.TemporaryDirectory() as td:
            v = self._mk_vault(td, lines)
            promote.promote(dry=False, vault=v, cfg=CFG)
            cand = (v / "04-FEEDBACK" / "candidates.md").read_text(encoding="utf-8")
            ops = (v / "00-RULES" / "ops.md").read_text(encoding="utf-8")
            self.assertIn("✅<!--done", cand)          # dest 合法 → 正常晋升+标 done
            self.assertIn("- dest 已修好 (", ops)

    def test_invalid_action_still_skipped_when_dest_still_illegal(self):
        lines = [CAND.format(mark="x", stmt="dest 仍非法", action="INVALID",
                             dest="03-MAPS/x.md")]
        with tempfile.TemporaryDirectory() as td:
            v = self._mk_vault(td, lines)
            promote.promote(dry=False, vault=v, cfg=CFG)
            cand = (v / "04-FEEDBACK" / "candidates.md").read_text(encoding="utf-8")
            self.assertNotIn("✅<!--done", cand)       # dest 仍非法 → 跳过且不标 done

    def test_dry_run_writes_nothing(self):
        lines = [CAND.format(mark="x", stmt="演习", action="ADD", dest="00-RULES/ops.md")]
        with tempfile.TemporaryDirectory() as td:
            v = self._mk_vault(td, lines)
            before = (v / "00-RULES" / "ops.md").read_text(encoding="utf-8")
            promote.promote(dry=True, vault=v, cfg=CFG)
            self.assertEqual((v / "00-RULES" / "ops.md").read_text(encoding="utf-8"), before)
            self.assertNotIn("✅<!--done",
                             (v / "04-FEEDBACK" / "candidates.md").read_text(encoding="utf-8"))

    def test_done_line_not_reprocessed(self):
        done_line = ('- [x] 已晋升过 ✅<!--done {"id":"c0-01","action":"ADD",'
                     '"dest":"00-RULES/ops.md"}-->')
        with tempfile.TemporaryDirectory() as td:
            v = self._mk_vault(td, [done_line])
            promote.promote(dry=False, vault=v, cfg=CFG)
            ops = (v / "00-RULES" / "ops.md").read_text(encoding="utf-8")
            self.assertNotIn("已晋升过", ops)


if __name__ == "__main__":
    unittest.main()
