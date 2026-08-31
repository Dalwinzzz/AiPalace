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
        self.assert_contains(contract, "不得作为第 7 个顶层段落")

    def test_router_mentions_project_context_indexing(self):
        router = SKILLS_DIR / "sql-expert-router" / "SKILL.md"
        self.assert_contains(router, "./sql/.index/")
        self.assert_contains(router, "biz-rules")

    def test_report_builder_mentions_business_rule_reuse_and_conflicts(self):
        report = SKILLS_DIR / "sql-report-query-builder" / "SKILL.md"
        self.assert_contains(report, "如当前项目存在")
        self.assert_contains(report, "`./sql/` 或相关索引")
        self.assert_contains(report, "./sql/.index/table-index.json")
        self.assert_contains(report, "biz-rules/table-index.json")
        self.assert_contains(report, "口径冲突")

    def test_schema_reviewer_mentions_existing_schema_context(self):
        reviewer = SKILLS_DIR / "sql-schema-reviewer" / "SKILL.md"
        self.assert_contains(reviewer, "现有 `./sql/` schema context")
        self.assert_contains(reviewer, "全局 memory 沉淀必须去敏")
        self.assert_contains(reviewer, "项目业务规则沉淀保持真实表名和字段名")

    def test_workflow_docs_do_not_allow_background_approved_writes(self):
        for path in sorted(SKILLS_DIR.glob("sql-*/SKILL.md")):
            content = path.read_text(encoding="utf-8")
            self.assertNotIn("可直接 `approved`", content)
            self.assertNotIn("candidate 或 approved", content)

    def test_shared_shard_files_exist(self):
        shared = SKILLS_DIR / "_shared"
        self.assertTrue((shared / "memory-policy.codex.md").exists(),
                        "memory-policy.codex.md missing")
        self.assertTrue((shared / "memory-policy.claude.md").exists(),
                        "memory-policy.claude.md missing")

    def test_memory_policy_unified_wording(self):
        policy = SKILLS_DIR / "_shared" / "memory-policy.md"
        content = policy.read_text(encoding="utf-8")
        # 新措辞必须存在
        self.assertIn("收尾记忆自评估（强制动作，静默执行）", content)
        self.assertIn("📌 已沉淀：", content)
        self.assertIn("TOOL-VARIANT: memory-policy", content)
        # 旧措辞必须不存在
        self.assertNotIn("收尾评估流程（强制表态）", content)
        self.assertNotIn("增强路径落盘指示", content)
        self.assertNotIn("last-context.json", content)


    def test_output_contract_no_mandatory_memory_section(self):
        contract = SKILLS_DIR / "_shared" / "output-contract.md"
        content = contract.read_text(encoding="utf-8")
        # 旧措辞必须不存在
        self.assertNotIn("记忆判定（必填，三选一", content)
        self.assertNotIn("缺此段视为任务未完成", content)
        self.assertNotIn("last-context.json", content)
        self.assertNotIn("Stop hook", content)
        # 新措辞必须存在
        self.assertIn("沉淀结果（仅写入时输出）", content)
        self.assertIn("workflow 收尾执行记忆自评估", content)


    def test_skill_unified_memory_wording(self):
        for path in sorted(SKILLS_DIR.glob("sql-*/SKILL.md")):
            content = path.read_text(encoding="utf-8")
            self.assertNotIn("后台记忆评估", content,
                             f"{path}: old '后台记忆评估' wording found")
            self.assertNotIn("无相关已沉淀记忆", content,
                             f"{path}: old '无相关已沉淀记忆' wording found")
            self.assertNotIn("Memory 检索（读取闭环，强制）", content,
                             f"{path}: old Memory 检索 wording found")

    def test_router_skill_hit_only_visible_wording(self):
        router = SKILLS_DIR / "sql-expert-router" / "SKILL.md"
        content = router.read_text(encoding="utf-8")
        self.assertIn("分诊前记忆检索（强制动作，命中才可见）", content)
        self.assertIn("TOOL-VARIANT: memory-policy", content)

    def test_workflow_skills_silent_eval_wording(self):
        for skill in ["sql-query-optimizer", "sql-error-diagnostician",
                      "sql-schema-reviewer", "sql-report-query-builder"]:
            path = SKILLS_DIR / skill / "SKILL.md"
            content = path.read_text(encoding="utf-8")
            self.assertIn("收尾记忆自评估（强制动作，静默执行）", content,
                          f"{path}: missing unified memory wording")
            self.assertIn("TOOL-VARIANT: memory-policy", content,
                          f"{path}: missing TOOL-VARIANT marker")

    def test_check_dual_sync_script_exists(self):
        sync_script = PLUGIN_DIR / "scripts" / "check_dual_sync.py"
        self.assertTrue(sync_script.exists(), "check_dual_sync.py missing")


if __name__ == "__main__":
    unittest.main()
