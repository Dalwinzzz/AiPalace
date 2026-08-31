#!/usr/bin/env python3
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent
CAPTURE = SCRIPTS_DIR / "biz_rules_capture.py"
SEARCH = SCRIPTS_DIR / "biz_rules_search.py"
GIT_GUARD = SCRIPTS_DIR / "biz_rules_git_guard.py"


def run_json(script: Path, args: list[str], cwd: Path | None = None) -> dict | list:
    result = subprocess.run(
        [sys.executable, str(script)] + args,
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise AssertionError(
            f"{script.name} failed\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )
    return json.loads(result.stdout)


def git(project: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git"] + args,
        cwd=project,
        capture_output=True,
        text=True,
        check=True,
    )


class TestBizRules(unittest.TestCase):
    def test_capture_writes_module_rule_and_indexes(self):
        with tempfile.TemporaryDirectory() as td:
            project = Path(td)
            result = run_json(
                CAPTURE,
                [
                    "--project-dir",
                    str(project),
                    "--module",
                    "order",
                    "--title",
                    "paid order daily statistics",
                    "--rule-type",
                    "metric_definition",
                    "--tables",
                    "orders,order_items",
                    "--fields",
                    "orders.paid_at,orders.status",
                    "--source-workflow",
                    "sql-report-query-builder",
                    "--capture-mode",
                    "explicit_user_requested",
                    "--confidence",
                    "high",
                    "--body",
                    "Paid orders use status=paid and paid_at as the business date.",
                ],
            )

            self.assertEqual(result["status"], "captured")
            self.assertEqual(result["module"], "order")
            self.assertTrue((project / "sql" / "biz-rules" / "order").is_dir())

            rule_path = project / "sql" / "biz-rules" / result["file"]
            content = rule_path.read_text(encoding="utf-8")
            self.assertIn("rule_type: metric_definition", content)
            self.assertIn("tables: [orders, order_items]", content)

            table_index = json.loads(
                (project / "sql" / "biz-rules" / "table-index.json").read_text(
                    encoding="utf-8"
                )
            )
            module_index = json.loads(
                (project / "sql" / "biz-rules" / "module-index.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertIn("orders", table_index["tables"])
            self.assertIn("order", module_index["modules"])
            self.assertEqual(table_index["tables"]["orders"][0]["file"], result["file"])

    def test_capture_adds_biz_rules_gitignore_rule(self):
        with tempfile.TemporaryDirectory() as td:
            project = Path(td)
            result = run_json(
                CAPTURE,
                [
                    "--project-dir",
                    str(project),
                    "--module",
                    "order",
                    "--title",
                    "paid order daily statistics",
                    "--rule-type",
                    "metric_definition",
                    "--tables",
                    "orders",
                    "--fields",
                    "orders.paid_at,orders.status",
                    "--source-workflow",
                    "sql-report-query-builder",
                    "--body",
                    "Paid orders use status=paid and paid_at as the business date.",
                ],
            )

            self.assertEqual(result["status"], "captured")
            self.assertEqual(result["ignore_status"], "updated")
            self.assertIn(
                "/sql/biz-rules/",
                (project / ".gitignore").read_text(encoding="utf-8"),
            )

    def test_unknown_module_routes_to_uncategorized(self):
        for raw_module in ("  ", "unknown"):
            with self.subTest(raw_module=raw_module):
                with tempfile.TemporaryDirectory() as td:
                    project = Path(td)
                    result = run_json(
                        CAPTURE,
                        [
                            "--project-dir",
                            str(project),
                            "--module",
                            raw_module,
                            "--title",
                            "unclassified metric",
                            "--rule-type",
                            "metric_definition",
                            "--tables",
                            "events",
                            "--source-workflow",
                            "sql-report-query-builder",
                            "--body",
                            "Events are counted by event_time.",
                        ],
                    )

                    self.assertEqual(result["status"], "captured")
                    self.assertEqual(result["module"], "uncategorized")
                    self.assertTrue(result["file"].startswith("uncategorized/"))

    def test_automatic_capture_skips_when_required_context_missing(self):
        with tempfile.TemporaryDirectory() as td:
            project = Path(td)
            result = run_json(
                CAPTURE,
                [
                    "--project-dir",
                    str(project),
                    "--title",
                    "auto missing context rule",
                    "--rule-type",
                    "metric_definition",
                    "--capture-mode",
                    "automatic",
                    "--body",
                    "Paid orders require status=paid.",
                ],
            )

            self.assertEqual(result["status"], "skipped")
            self.assertEqual(result["reason"], "insufficient_automatic_context")
            self.assertIn("module", result["missing_context"])
            self.assertIn("tables", result["missing_context"])
            self.assertIn("source_workflow", result["missing_context"])
            self.assertFalse((project / "sql" / "biz-rules").exists())

    def test_automatic_capture_skips_placeholder_context_values(self):
        cases = [
            ("tables", "unknown", "Paid orders require status=paid."),
            ("tables", "n/a", "Paid orders require status=paid."),
            ("final_rule_conclusion", "orders", "unknown"),
        ]
        for missing_field, tables, body in cases:
            with self.subTest(missing_field=missing_field, tables=tables, body=body):
                with tempfile.TemporaryDirectory() as td:
                    project = Path(td)
                    result = run_json(
                        CAPTURE,
                        [
                            "--project-dir",
                            str(project),
                            "--module",
                            "order",
                            "--title",
                            "auto placeholder context rule",
                            "--rule-type",
                            "metric_definition",
                            "--tables",
                            tables,
                            "--source-workflow",
                            "sql-report-query-builder",
                            "--capture-mode",
                            "auto_hook",
                            "--body",
                            body,
                        ],
                    )

                    self.assertEqual(result["status"], "skipped")
                    self.assertEqual(result["reason"], "insufficient_automatic_context")
                    self.assertIn(missing_field, result["missing_context"])
                    self.assertFalse((project / "sql" / "biz-rules").exists())

    def test_automatic_capture_skips_when_workspace_missing(self):
        with tempfile.TemporaryDirectory() as td:
            project = Path(td) / "missing-project"
            result = run_json(
                CAPTURE,
                [
                    "--project-dir",
                    str(project),
                    "--module",
                    "order",
                    "--title",
                    "auto missing workspace rule",
                    "--rule-type",
                    "metric_definition",
                    "--tables",
                    "orders",
                    "--source-workflow",
                    "sql-report-query-builder",
                    "--capture-mode",
                    "auto_hook",
                    "--body",
                    "Paid orders require status=paid.",
                ],
            )

            self.assertEqual(result["status"], "skipped")
            self.assertEqual(result["reason"], "insufficient_automatic_context")
            self.assertIn("workspace", result["missing_context"])
            self.assertFalse(project.exists())

    def test_automatic_capture_with_required_context_writes_rule(self):
        with tempfile.TemporaryDirectory() as td:
            project = Path(td)
            result = run_json(
                CAPTURE,
                [
                    "--project-dir",
                    str(project),
                    "--module",
                    "order",
                    "--title",
                    "auto paid order rule",
                    "--rule-type",
                    "metric_definition",
                    "--tables",
                    "orders",
                    "--source-workflow",
                    "sql-report-query-builder",
                    "--capture-mode",
                    "auto_hook",
                    "--body",
                    "Paid orders require status=paid.",
                ],
            )

            self.assertEqual(result["status"], "captured")
            self.assertEqual(result["module"], "order")
            self.assertEqual(result["tables"], ["orders"])
            self.assertTrue((project / "sql" / "biz-rules" / result["file"]).is_file())

    def test_search_by_table_finds_rule(self):
        with tempfile.TemporaryDirectory() as td:
            project = Path(td)
            run_json(
                CAPTURE,
                [
                    "--project-dir",
                    str(project),
                    "--module",
                    "order",
                    "--title",
                    "paid order rule",
                    "--rule-type",
                    "metric_definition",
                    "--tables",
                    "orders",
                    "--fields",
                    "orders.status",
                    "--source-workflow",
                    "sql-report-query-builder",
                    "--body",
                    "Paid orders require status=paid.",
                ],
            )

            result = run_json(SEARCH, ["--project-dir", str(project), "--table", "orders"])

            self.assertEqual(result["status"], "ok")
            self.assertEqual(len(result["rules"]), 1)
            self.assertEqual(result["rules"][0]["module"], "order")

    def test_search_by_field_rule_type_and_keyword_finds_rule(self):
        with tempfile.TemporaryDirectory() as td:
            project = Path(td)
            run_json(
                CAPTURE,
                [
                    "--project-dir",
                    str(project),
                    "--module",
                    "order",
                    "--title",
                    "refund reconciliation rule",
                    "--rule-type",
                    "reconciliation_rule",
                    "--tables",
                    "refunds,orders",
                    "--fields",
                    "refunds.refund_amount,orders.pay_amount",
                    "--source-workflow",
                    "sql-report-query-builder",
                    "--body",
                    "Refund reconciliation compares refund_amount to pay_amount.",
                ],
            )

            result = run_json(
                SEARCH,
                [
                    "--project-dir",
                    str(project),
                    "--field",
                    "refunds.refund_amount",
                    "--rule-type",
                    "reconciliation_rule",
                    "--keyword",
                    "pay_amount",
                ],
            )

            self.assertEqual(result["status"], "ok")
            self.assertEqual([rule["title"] for rule in result["rules"]], ["refund reconciliation rule"])

    def test_handwritten_scalar_tables_and_fields_are_normalized(self):
        with tempfile.TemporaryDirectory() as td:
            project = Path(td)
            module_dir = project / "sql" / "biz-rules" / "order"
            module_dir.mkdir(parents=True)
            (module_dir / "manual.md").write_text(
                """---
id: "biz-rule-manual"
title: "manual paid order rule"
module: "order"
tables: orders
fields: orders.status, orders.paid_at
rule_type: metric_definition
source_workflow: "manual"
capture_mode: "manual"
confidence: "medium"
review_status: "approved"
last_reviewed_at: "2026-05-09"
---

Paid orders use status and paid_at.
""",
                encoding="utf-8",
            )

            run_json(
                CAPTURE,
                [
                    "--project-dir",
                    str(project),
                    "--module",
                    "order",
                    "--title",
                    "order status semantics",
                    "--rule-type",
                    "field_semantics",
                    "--tables",
                    "orders",
                    "--fields",
                    "orders.status",
                    "--source-workflow",
                    "sql-schema-reviewer",
                    "--body",
                    "orders.status stores the order lifecycle state.",
                ],
            )
            table_index = json.loads(
                (project / "sql" / "biz-rules" / "table-index.json").read_text(
                    encoding="utf-8"
                )
            )
            search = run_json(
                SEARCH,
                ["--project-dir", str(project), "--field", "orders.paid_at"],
            )

            self.assertIn("orders", table_index["tables"])
            self.assertNotIn("o", table_index["tables"])
            manual_entry = next(
                entry
                for entry in table_index["tables"]["orders"]
                if entry["id"] == "biz-rule-manual"
            )
            self.assertEqual(manual_entry["tables"], ["orders"])
            self.assertEqual(manual_entry["fields"], ["orders.status", "orders.paid_at"])
            self.assertEqual([rule["id"] for rule in search["rules"]], ["biz-rule-manual"])

    def test_title_quotes_and_backslashes_remain_readable(self):
        with tempfile.TemporaryDirectory() as td:
            project = Path(td)
            title = 'daily "paid" path C:\\reports'
            result = run_json(
                CAPTURE,
                [
                    "--project-dir",
                    str(project),
                    "--module",
                    "order",
                    "--title",
                    title,
                    "--rule-type",
                    "report_template",
                    "--tables",
                    "orders",
                    "--source-workflow",
                    "sql-report-query-builder",
                    "--body",
                    "Daily paid order report template.",
                ],
            )
            search = run_json(SEARCH, ["--project-dir", str(project), "--table", "orders"])
            module_index = json.loads(
                (project / "sql" / "biz-rules" / "module-index.json").read_text(
                    encoding="utf-8"
                )
            )

            self.assertEqual(result["status"], "captured")
            self.assertEqual(search["rules"][0]["title"], title)
            self.assertEqual(module_index["modules"]["order"][0]["title"], title)

    def test_keyword_search_matches_raw_quotes_and_backslashes(self):
        with tempfile.TemporaryDirectory() as td:
            project = Path(td)
            title = 'daily "paid" path C:\\reports\\q'
            body = 'Template for daily "paid" exports under C:\\reports\\q.'
            run_json(
                CAPTURE,
                [
                    "--project-dir",
                    str(project),
                    "--module",
                    "order",
                    "--title",
                    title,
                    "--rule-type",
                    "report_template",
                    "--tables",
                    "orders",
                    "--source-workflow",
                    "sql-report-query-builder",
                    "--body",
                    body,
                ],
            )

            by_quoted_word = run_json(
                SEARCH,
                ["--project-dir", str(project), "--keyword", '"paid"'],
            )
            by_path = run_json(
                SEARCH,
                ["--project-dir", str(project), "--keyword", "C:\\reports\\q"],
            )

            self.assertEqual([rule["title"] for rule in by_quoted_word["rules"]], [title])
            self.assertEqual([rule["title"] for rule in by_path["rules"]], [title])

    def test_duplicate_rule_is_detected_without_second_write(self):
        with tempfile.TemporaryDirectory() as td:
            project = Path(td)
            args = [
                "--project-dir",
                str(project),
                "--module",
                "order",
                "--title",
                "paid order rule",
                "--rule-type",
                "metric_definition",
                "--tables",
                "orders",
                "--fields",
                "orders.status",
                "--source-workflow",
                "sql-report-query-builder",
                "--body",
                "Paid orders require status=paid.",
            ]
            first = run_json(CAPTURE, args)
            second = run_json(CAPTURE, args)

            self.assertEqual(first["status"], "captured")
            self.assertEqual(second["status"], "duplicate")
            self.assertEqual(second["existing_file"], first["file"])
            self.assertEqual(
                len(list((project / "sql" / "biz-rules" / "order").glob("*.md"))),
                1,
            )

    def test_conflicting_metric_rule_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as td:
            project = Path(td)
            run_json(
                CAPTURE,
                [
                    "--project-dir",
                    str(project),
                    "--module",
                    "order",
                    "--title",
                    "paid order rule",
                    "--rule-type",
                    "metric_definition",
                    "--tables",
                    "orders",
                    "--fields",
                    "orders.status",
                    "--source-workflow",
                    "sql-report-query-builder",
                    "--body",
                    "Paid orders require status=paid.",
                ],
            )
            conflict = run_json(
                CAPTURE,
                [
                    "--project-dir",
                    str(project),
                    "--module",
                    "order",
                    "--title",
                    "settled order rule",
                    "--rule-type",
                    "metric_definition",
                    "--tables",
                    "orders",
                    "--fields",
                    "orders.status",
                    "--source-workflow",
                    "sql-report-query-builder",
                    "--body",
                    "Paid orders require status=settled.",
                ],
            )

            self.assertEqual(conflict["status"], "conflict")
            self.assertIn("existing_file", conflict)
            self.assertEqual(
                len(list((project / "sql" / "biz-rules" / "order").glob("*.md"))),
                1,
            )

    def test_same_key_conflicting_metric_rule_is_not_treated_as_duplicate(self):
        with tempfile.TemporaryDirectory() as td:
            project = Path(td)
            run_json(
                CAPTURE,
                [
                    "--project-dir",
                    str(project),
                    "--module",
                    "order",
                    "--title",
                    "paid order rule",
                    "--rule-type",
                    "metric_definition",
                    "--tables",
                    "orders",
                    "--fields",
                    "orders.status",
                    "--source-workflow",
                    "sql-report-query-builder",
                    "--body",
                    "Paid orders require status=paid.",
                ],
            )
            conflict = run_json(
                CAPTURE,
                [
                    "--project-dir",
                    str(project),
                    "--module",
                    "order",
                    "--title",
                    "paid order rule",
                    "--rule-type",
                    "metric_definition",
                    "--tables",
                    "orders",
                    "--fields",
                    "orders.status",
                    "--source-workflow",
                    "sql-report-query-builder",
                    "--body",
                    "Paid orders require status=settled.",
                ],
            )

            self.assertEqual(conflict["status"], "conflict")
            self.assertIn("existing_file", conflict)
            self.assertEqual(
                len(list((project / "sql" / "biz-rules" / "order").glob("*.md"))),
                1,
            )

    def test_same_key_metric_conflict_with_different_fields_is_not_duplicate(self):
        with tempfile.TemporaryDirectory() as td:
            project = Path(td)
            run_json(
                CAPTURE,
                [
                    "--project-dir",
                    str(project),
                    "--module",
                    "order",
                    "--title",
                    "paid order rule",
                    "--rule-type",
                    "metric_definition",
                    "--tables",
                    "orders",
                    "--fields",
                    "orders.status",
                    "--source-workflow",
                    "sql-report-query-builder",
                    "--body",
                    "Paid orders require status=paid.",
                ],
            )
            conflict = run_json(
                CAPTURE,
                [
                    "--project-dir",
                    str(project),
                    "--module",
                    "order",
                    "--title",
                    "paid order rule",
                    "--rule-type",
                    "metric_definition",
                    "--tables",
                    "orders",
                    "--fields",
                    "orders.paid_at",
                    "--source-workflow",
                    "sql-report-query-builder",
                    "--body",
                    "Paid orders require paid_at IS NOT NULL.",
                ],
            )

            self.assertEqual(conflict["status"], "conflict")
            self.assertIn("existing_file", conflict)
            self.assertEqual(
                len(list((project / "sql" / "biz-rules" / "order").glob("*.md"))),
                1,
            )

    def test_git_guard_adds_ignore_rule(self):
        with tempfile.TemporaryDirectory() as td:
            project = Path(td)
            (project / "sql" / "biz-rules").mkdir(parents=True)
            result = run_json(GIT_GUARD, ["--project-dir", str(project), "--ensure-ignore"])

            self.assertEqual(result["ignore_status"], "updated")
            self.assertIn(
                "/sql/biz-rules/",
                (project / ".gitignore").read_text(encoding="utf-8"),
            )

    def test_git_guard_detects_tracked_rules_but_does_not_untrack_by_default(self):
        with tempfile.TemporaryDirectory() as td:
            project = Path(td)
            git(project, ["init"])
            rules_dir = project / "sql" / "biz-rules"
            rules_dir.mkdir(parents=True)
            (rules_dir / "tracked.md").write_text("tracked", encoding="utf-8")
            git(project, ["add", "sql/biz-rules/tracked.md"])

            result = run_json(GIT_GUARD, ["--project-dir", str(project), "--ensure-ignore"])
            tracked = git(project, ["ls-files", "sql/biz-rules"]).stdout.strip()

            self.assertTrue(result["tracked"])
            self.assertEqual(result["untrack_status"], "not_requested")
            self.assertEqual(tracked, "sql/biz-rules/tracked.md")

    def test_git_guard_untracks_only_with_explicit_flag(self):
        with tempfile.TemporaryDirectory() as td:
            project = Path(td)
            git(project, ["init"])
            rules_dir = project / "sql" / "biz-rules"
            rules_dir.mkdir(parents=True)
            (rules_dir / "tracked.md").write_text("tracked", encoding="utf-8")
            git(project, ["add", "sql/biz-rules/tracked.md"])

            result = run_json(
                GIT_GUARD,
                ["--project-dir", str(project), "--ensure-ignore", "--untrack"],
            )
            tracked = git(project, ["ls-files", "sql/biz-rules"]).stdout.strip()

            self.assertTrue(result["tracked"])
            self.assertEqual(result["untrack_status"], "untracked")
            self.assertEqual(tracked, "")
            self.assertTrue((rules_dir / "tracked.md").exists())

    def test_capture_rejects_sql_symlink_escape(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            project = root / "project"
            project.mkdir()
            external_sql = root / "external-sql"
            external_sql.mkdir()
            try:
                (project / "sql").symlink_to(external_sql, target_is_directory=True)
            except (NotImplementedError, OSError) as exc:
                raise unittest.SkipTest(f"symlink unavailable: {exc}") from exc

            result = run_json(
                CAPTURE,
                [
                    "--project-dir",
                    str(project),
                    "--module",
                    "order",
                    "--title",
                    "paid order rule",
                    "--rule-type",
                    "metric_definition",
                    "--tables",
                    "orders",
                    "--source-workflow",
                    "sql-report-query-builder",
                    "--body",
                    "Paid orders require status=paid.",
                ],
            )

            self.assertEqual(result["status"], "disabled")
            self.assertEqual(result["reason"], "sql_dir_symlink_escape")
            self.assertFalse((external_sql / "biz-rules").exists())

    def test_capture_rejects_gitignore_symlink_escape(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            project = root / "project"
            project.mkdir()
            external_gitignore = root / "outside-gitignore"
            external_gitignore.write_text("sentinel\n", encoding="utf-8")
            try:
                (project / ".gitignore").symlink_to(external_gitignore)
            except (NotImplementedError, OSError) as exc:
                raise unittest.SkipTest(f"symlink unavailable: {exc}") from exc

            result = run_json(
                CAPTURE,
                [
                    "--project-dir",
                    str(project),
                    "--module",
                    "order",
                    "--title",
                    "paid order rule",
                    "--rule-type",
                    "metric_definition",
                    "--tables",
                    "orders",
                    "--source-workflow",
                    "sql-report-query-builder",
                    "--body",
                    "Paid orders require status=paid.",
                ],
            )

            self.assertEqual(result["status"], "disabled")
            self.assertEqual(result["reason"], "gitignore_symlink_escape")
            self.assertEqual(external_gitignore.read_text(encoding="utf-8"), "sentinel\n")
            self.assertFalse((project / "sql").exists())

    def test_capture_rejects_module_dir_symlink_inside_project(self):
        with tempfile.TemporaryDirectory() as td:
            project = Path(td)
            biz_rules = project / "sql" / "biz-rules"
            target = project / "module-target"
            biz_rules.mkdir(parents=True)
            target.mkdir()
            try:
                (biz_rules / "order").symlink_to(target, target_is_directory=True)
            except (NotImplementedError, OSError) as exc:
                raise unittest.SkipTest(f"symlink unavailable: {exc}") from exc

            result = run_json(
                CAPTURE,
                [
                    "--project-dir",
                    str(project),
                    "--module",
                    "order",
                    "--title",
                    "paid order rule",
                    "--rule-type",
                    "metric_definition",
                    "--tables",
                    "orders",
                    "--source-workflow",
                    "sql-report-query-builder",
                    "--body",
                    "Paid orders require status=paid.",
                ],
            )

            self.assertEqual(result["status"], "disabled")
            self.assertEqual(result["reason"], "module_dir_symlink_escape")
            self.assertEqual(list(target.iterdir()), [])

    def test_capture_rejects_table_index_symlink_inside_project(self):
        with tempfile.TemporaryDirectory() as td:
            project = Path(td)
            biz_rules = project / "sql" / "biz-rules"
            biz_rules.mkdir(parents=True)
            sentinel = project / "table-index-sentinel.json"
            sentinel.write_text("sentinel\n", encoding="utf-8")
            try:
                (biz_rules / "table-index.json").symlink_to(sentinel)
            except (NotImplementedError, OSError) as exc:
                raise unittest.SkipTest(f"symlink unavailable: {exc}") from exc

            result = run_json(
                CAPTURE,
                [
                    "--project-dir",
                    str(project),
                    "--module",
                    "order",
                    "--title",
                    "paid order rule",
                    "--rule-type",
                    "metric_definition",
                    "--tables",
                    "orders",
                    "--source-workflow",
                    "sql-report-query-builder",
                    "--body",
                    "Paid orders require status=paid.",
                ],
            )

            self.assertEqual(result["status"], "disabled")
            self.assertEqual(result["reason"], "index_file_symlink_escape")
            self.assertEqual(sentinel.read_text(encoding="utf-8"), "sentinel\n")
            self.assertFalse((biz_rules / "order").exists())

    def test_capture_rejects_existing_rule_file_symlink(self):
        with tempfile.TemporaryDirectory() as td:
            project = Path(td)
            module_dir = project / "sql" / "biz-rules" / "order"
            module_dir.mkdir(parents=True)
            sentinel = project / "linked-rule.md"
            sentinel.write_text("sentinel\n", encoding="utf-8")
            try:
                (module_dir / "linked.md").symlink_to(sentinel)
            except (NotImplementedError, OSError) as exc:
                raise unittest.SkipTest(f"symlink unavailable: {exc}") from exc

            result = run_json(
                CAPTURE,
                [
                    "--project-dir",
                    str(project),
                    "--module",
                    "order",
                    "--title",
                    "paid order rule",
                    "--rule-type",
                    "metric_definition",
                    "--tables",
                    "orders",
                    "--source-workflow",
                    "sql-report-query-builder",
                    "--body",
                    "Paid orders require status=paid.",
                ],
            )

            self.assertEqual(result["status"], "disabled")
            self.assertEqual(result["reason"], "rule_file_symlink_escape")
            self.assertEqual(sentinel.read_text(encoding="utf-8"), "sentinel\n")
            self.assertEqual([path.name for path in module_dir.iterdir()], ["linked.md"])

    def test_search_rejects_table_index_symlink_inside_project(self):
        with tempfile.TemporaryDirectory() as td:
            project = Path(td)
            run_json(
                CAPTURE,
                [
                    "--project-dir",
                    str(project),
                    "--module",
                    "order",
                    "--title",
                    "paid order rule",
                    "--rule-type",
                    "metric_definition",
                    "--tables",
                    "orders",
                    "--source-workflow",
                    "sql-report-query-builder",
                    "--body",
                    "Paid orders require status=paid.",
                ],
            )
            table_index = project / "sql" / "biz-rules" / "table-index.json"
            table_index.unlink()
            sentinel = project / "table-index-sentinel.json"
            sentinel.write_text("sentinel\n", encoding="utf-8")
            try:
                table_index.symlink_to(sentinel)
            except (NotImplementedError, OSError) as exc:
                raise unittest.SkipTest(f"symlink unavailable: {exc}") from exc

            result = run_json(SEARCH, ["--project-dir", str(project), "--table", "orders"])

            self.assertEqual(result["status"], "disabled")
            self.assertEqual(result["reason"], "index_file_symlink_escape")

    def test_git_guard_rejects_gitignore_symlink_escape(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            project = root / "project"
            project.mkdir()
            external_gitignore = root / "outside-gitignore"
            external_gitignore.write_text("sentinel\n", encoding="utf-8")
            try:
                (project / ".gitignore").symlink_to(external_gitignore)
            except (NotImplementedError, OSError) as exc:
                raise unittest.SkipTest(f"symlink unavailable: {exc}") from exc

            result = run_json(GIT_GUARD, ["--project-dir", str(project), "--ensure-ignore"])

            self.assertEqual(result["status"], "disabled")
            self.assertEqual(result["reason"], "gitignore_symlink_escape")
            self.assertEqual(external_gitignore.read_text(encoding="utf-8"), "sentinel\n")

    def test_git_guard_rejects_gitignore_symlink_inside_project(self):
        with tempfile.TemporaryDirectory() as td:
            project = Path(td)
            project.mkdir(exist_ok=True)
            sentinel = project / "inside-gitignore-target"
            sentinel.write_text("sentinel\n", encoding="utf-8")
            try:
                (project / ".gitignore").symlink_to(sentinel)
            except (NotImplementedError, OSError) as exc:
                raise unittest.SkipTest(f"symlink unavailable: {exc}") from exc

            result = run_json(GIT_GUARD, ["--project-dir", str(project), "--ensure-ignore"])

            self.assertEqual(result["status"], "disabled")
            self.assertEqual(result["reason"], "gitignore_symlink_escape")
            self.assertEqual(sentinel.read_text(encoding="utf-8"), "sentinel\n")


if __name__ == "__main__":
    unittest.main()
