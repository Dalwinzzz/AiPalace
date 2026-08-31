#!/usr/bin/env python3
"""TDD for core.py —— 手动飞轮蒸馏内核(解析层)。

stdlib unittest,零依赖:python3 -m unittest discover -s tools/memory -v
"""
import os
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import core  # noqa: E402

CFG = {
    "sources": {"scan_days": 3},
    "scoring": {"w_relevance": 0.30, "w_frequency": 0.24, "w_diversity": 0.15,
                "w_recency": 0.15, "w_consolidation": 0.10, "w_richness": 0.06,
                "promote_threshold": 0.50, "min_freq_global": 2,
                "merge_similarity": 0.78, "dedupe_similarity": 0.72, "noop_similarity": 0.92},
    "routing": {"rules_files": ["00-RULES/ops.md", "00-RULES/dev.md"],
                "projects_prefixes": ["01-PROJECTS/workflow/", "01-PROJECTS/enterprise/"]},
}

TODAY = date(2026, 7, 2)


class ParseJournal(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.jdir = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)

    def _write(self, stem: str, body: str) -> None:
        (self.jdir / f"{stem}.md").write_text(body, encoding="utf-8")

    def test_prefix_sig_and_tolerance(self):
        self._write("2026-07-02", "\n".join([
            '- 偏好: 记忆内核零依赖 <!--sig {"type":"preference","scope":"global","dest":"00-RULES/ops.md","source":"claude"}-->',
            "- 决策: 沉淀走飞轮",
            "- 观察: 今天讨论了 M5",
            '- 纠正: 别用 pytest <!--sig {坏json-->',
            "普通行不解析",
        ]))
        sigs = core.parse_journal(self.jdir, days=3, today=TODAY)
        self.assertEqual(len(sigs), 4)  # 普通行被跳过
        self.assertEqual(sigs[0].kind, "preference")
        self.assertEqual(sigs[0].sig["dest"], "00-RULES/ops.md")
        self.assertEqual(sigs[1].kind, "decision")
        self.assertEqual(sigs[1].sig, {})          # 无 sig
        self.assertEqual(sigs[2].kind, "observation")
        self.assertEqual(sigs[3].sig, {})          # 坏 sig 容错为无 sig
        self.assertEqual(sigs[0].date, "2026-07-02")

    def test_days_window(self):
        self._write("2026-07-01", "- 决策: 窗口内")
        self._write("2026-06-01", "- 决策: 窗口外")
        sigs = core.parse_journal(self.jdir, days=3, today=TODAY)
        self.assertEqual([s.text for s in sigs], ["窗口内"])

    def test_missing_dir_returns_empty(self):
        sigs = core.parse_journal(self.jdir / "nope", days=3, today=TODAY)
        self.assertEqual(sigs, [])


class SignalsToCandidates(unittest.TestCase):
    def test_observation_skipped_and_fallbacks(self):
        sigs = [
            core.Signal(text="观察内容", kind="observation", date="2026-07-02", sig={}),
            core.Signal(text="全局偏好", kind="preference", date="2026-07-02", sig={}),
            core.Signal(text="项目决策", kind="decision", date="2026-07-02",
                        sig={"scope": "project:workflow/ai-workflow",
                             "dest": "01-PROJECTS/workflow/ai-workflow.md", "source": "codex"}),
        ]
        cands = core.signals_to_candidates(sigs)
        self.assertEqual(len(cands), 2)
        c0, c1 = cands
        self.assertEqual((c0.scope, c0.dest, c0.sources, c0.signed),
                         ("global", "00-RULES/ops.md", ["journal"], False))
        self.assertEqual((c1.dest, c1.sources, c1.signed),
                         ("01-PROJECTS/workflow/ai-workflow.md", ["codex"], True))

    def test_infer_dest(self):
        self.assertEqual(core.infer_dest("project:enterprise/zhijin"),
                         "01-PROJECTS/enterprise/zhijin.md")
        self.assertEqual(core.infer_dest("global"), "00-RULES/ops.md")


class ValidateDest(unittest.TestCase):
    def test_whitelist(self):
        self.assertEqual(core.validate_dest("00-RULES/ops.md", CFG), "")
        self.assertEqual(core.validate_dest("01-PROJECTS/workflow/ai-workflow.md", CFG), "")
        self.assertNotEqual(core.validate_dest("00-RULES/identity.md", CFG), "")   # 不在本测试白名单
        self.assertNotEqual(core.validate_dest("02-SOURCES/x.md", CFG), "")
        self.assertNotEqual(core.validate_dest("../etc/passwd", CFG), "")
        self.assertNotEqual(core.validate_dest("01-PROJECTS/workflow/x.txt", CFG), "")


class MergeAndScore(unittest.TestCase):
    def _cand(self, stmt, **kw):
        base = dict(statement=stmt, ctype="preference", scope="global",
                    dest="00-RULES/ops.md", sources=["journal"], dates={"2026-07-02"})
        base.update(kw)
        return core.Candidate(**base)

    def test_merge_accumulates_and_latest_sig_wins(self):
        a = self._cand("记忆内核必须零依赖标准库", sources=["claude"], dates={"2026-07-01"})
        b = self._cand("记忆内核必须零依赖标准库!", sources=["codex"], dates={"2026-07-02"},
                       signed=True, dest="00-RULES/dev.md", scope="global")
        c = self._cand("完全无关的另一条")
        merged = core.merge([a, b, c], threshold=0.78)
        self.assertEqual(len(merged), 2)
        hit = merged[0]
        self.assertEqual(hit.freq, 2)
        self.assertEqual(hit.sources, ["claude", "codex"])
        self.assertEqual(hit.dates, {"2026-07-01", "2026-07-02"})
        self.assertEqual(hit.dest, "00-RULES/dev.md")   # 显式 sig 的后来者覆盖路由

    def test_score_deterministic_and_actions(self):
        cands = [self._cand("总是在 Java 修复时保持最小改动不做抽象", freq=2,
                            sources=["claude", "codex"], dates={"2026-07-02"})]
        sims = {"rules": 0.40, "dedup": 0.80}
        fake_sim = lambda stmt, corpus: sims["rules"] if corpus == ["R"] else sims["dedup"]
        core.score_all(cands, ["R"], ["D"], CFG, today=TODAY, sim=fake_sim)
        first = (cands[0].score, dict(cands[0].sub), cands[0].action, cands[0].conf)
        core.score_all(cands, ["R"], ["D"], CFG, today=TODAY, sim=fake_sim)
        self.assertEqual(first, (cands[0].score, dict(cands[0].sub), cands[0].action, cands[0].conf))
        # freq=2=max_freq → frequency=1.0;rel=.4;div=2/3;rec=1.0;cons=.4;rich=min(1,len/60)
        self.assertEqual(cands[0].action, "UPDATE")     # 0.72 ≤ 0.80 < 0.92
        self.assertAlmostEqual(cands[0].sub["frequency"], 1.0)
        self.assertAlmostEqual(cands[0].sub["diversity"], 2 / 3, places=6)

    def test_noop_add_and_invalid(self):
        noop = self._cand("与库里几乎一样的条目")
        add = self._cand("全新的条目")
        bad = self._cand("落点非法的条目", dest="03-MAPS/x.md")
        table = {"与库里几乎一样的条目": 0.95, "全新的条目": 0.10, "落点非法的条目": 0.10}
        fake_sim = lambda stmt, corpus: table[stmt]
        core.score_all([noop, add, bad], [], [], CFG, today=TODAY, sim=fake_sim)
        self.assertEqual(noop.action, "NOOP")
        self.assertEqual(add.action, "ADD")
        self.assertEqual(bad.action, "INVALID")
        self.assertEqual(bad.invalid_reason, "不在 routing 白名单")

    def test_gate_threshold_minfreq_and_noop(self):
        high_global_f1 = self._cand("高分但全局只出现一次", score=0.80, freq=1)
        high_global_f2 = self._cand("高分全局出现两次", score=0.80, freq=2)
        high_project = self._cand("高分项目级一次", score=0.80, freq=1,
                                  scope="project:workflow/x",
                                  dest="01-PROJECTS/workflow/x.md")
        low = self._cand("低分", score=0.30, freq=3)
        noop = self._cand("重复", score=0.90, freq=3, action="NOOP")
        passed, deferred = core.gate([high_global_f1, high_global_f2, high_project, low, noop], CFG)
        self.assertEqual([c.statement for c in passed], ["高分全局出现两次", "高分项目级一次"])
        self.assertEqual(len(deferred), 3)

    def test_load_corpus_filters_markdown_noise(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "a.md"
            p.write_text("# 标题\n| 表格 | 行 |\n> 引用\n- 这是一条足够长的正文语料内容\n短\n",
                         encoding="utf-8")
            corpus = core.load_corpus([Path(td)])
            self.assertEqual(corpus, ["这是一条足够长的正文语料内容"])


class RenderAndDistill(unittest.TestCase):
    def _mk_vault(self, td: str) -> Path:
        v = Path(td)
        (v / "00-RULES").mkdir(parents=True)
        (v / "00-RULES" / "ops.md").write_text(
            "---\ntitle: ops\nupdated: 2026-07-01\n---\n- 沉淀目标是 vault 记忆层的既有语料内容\n",
            encoding="utf-8")
        (v / "01-PROJECTS" / "workflow").mkdir(parents=True)
        j = v / "04-FEEDBACK" / "journal"
        j.mkdir(parents=True)
        (v / "04-FEEDBACK" / "candidates.md").write_text("# 队列\n", encoding="utf-8")
        (v / "04-FEEDBACK" / "DREAMS.md").write_text("# DREAMS\n", encoding="utf-8")
        (j / "2026-07-01.md").write_text(
            '- 决策: vault 沉淀统一改走 ai-palace 手动飞轮 <!--sig {"type":"decision","scope":"global","dest":"00-RULES/ops.md","source":"claude"}-->\n',
            encoding="utf-8")
        (j / "2026-07-02.md").write_text(
            '- 决策: vault 沉淀统一改走 ai-palace 手动飞轮 <!--sig {"type":"decision","scope":"global","dest":"00-RULES/ops.md","source":"codex"}-->\n'
            "- 观察: 只留底不进候选\n",
            encoding="utf-8")
        return v

    def test_render_block_protocol(self):
        c = core.Candidate(statement="测试候选", ctype="decision", scope="global",
                           dest="00-RULES/ops.md", freq=2, sources=["claude"],
                           dates={"2026-07-02"}, score=0.61, conf="medium",
                           sub={"relevance": 0.4, "frequency": 1.0, "diversity": 0.33,
                                "recency": 1.0, "consolidation": 0.4, "richness": 0.5},
                           action="INVALID", invalid_reason="不在 routing 白名单")
        block = core.render_block([c], run_id="20260702-1130")
        self.assertIn('- [ ] 测试候选 <!--cand {"id": "c20260702-1130-01"', block)
        self.assertIn("⚠️ 不在 routing 白名单", block)
        self.assertIn("六维:", block)
        import json as _json
        meta = _json.loads(block.split("<!--cand ", 1)[1].split("-->", 1)[0])
        self.assertEqual(meta["action"], "INVALID")

    def test_distill_end_to_end_and_shadow(self):
        from argparse import Namespace
        with tempfile.TemporaryDirectory() as td:
            v = self._mk_vault(td)
            args = Namespace(days=3, shadow=True, today="2026-07-02")
            self.assertEqual(core.distill(args, vault=v, cfg=CFG), 0)
            self.assertEqual((v / "04-FEEDBACK" / "candidates.md").read_text(encoding="utf-8"),
                             "# 队列\n")  # shadow 不落盘
            args = Namespace(days=3, shadow=False, today="2026-07-02")
            self.assertEqual(core.distill(args, vault=v, cfg=CFG), 0)
            cand_text = (v / "04-FEEDBACK" / "candidates.md").read_text(encoding="utf-8")
            dreams_text = (v / "04-FEEDBACK" / "DREAMS.md").read_text(encoding="utf-8")
            # 同一决策两天两来源:freq=2 过 global 门,进候选
            self.assertIn("vault 沉淀统一改走 ai-palace 手动飞轮", cand_text)
            self.assertIn('"freq": 2', cand_text)
            self.assertIn("· distill", dreams_text)
            self.assertNotIn("只留底不进候选", cand_text)   # 观察不进候选


if __name__ == "__main__":
    unittest.main()
