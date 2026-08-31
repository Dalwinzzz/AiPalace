#!/usr/bin/env python3
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent
INDEX = SCRIPTS_DIR / "project_context_index.py"
SEARCH = SCRIPTS_DIR / "project_context_search.py"


def run_json(script: Path, args: list[str]) -> dict | list:
    result = subprocess.run(
        [sys.executable, str(script)] + args,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise AssertionError(
            f"{script.name} failed\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )
    return json.loads(result.stdout)


class TestProjectContext(unittest.TestCase):
    def test_rebuild_indexes_supported_sql_files(self):
        with tempfile.TemporaryDirectory() as td:
            project = Path(td)
            ddl_dir = project / "sql" / "ddl"
            ddl_dir.mkdir(parents=True)
            (ddl_dir / "schema.sql").write_text(
                """
CREATE TABLE orders (
  id bigint primary key,
  user_id bigint not null,
  status varchar(32),
  paid_at datetime,
  pay_amount decimal(10,2),
  KEY idx_orders_user_id (user_id),
  KEY idx_orders_paid_at (paid_at)
);
""",
                encoding="utf-8",
            )
            explain_dir = project / "sql" / "explain"
            explain_dir.mkdir()
            (explain_dir / "orders.explain").write_text(
                "table: orders\ntype: ALL\nExtra: Using filesort",
                encoding="utf-8",
            )

            result = run_json(INDEX, ["--project-dir", str(project), "--rebuild"])

            self.assertEqual(result["status"], "indexed")
            table_index = json.loads(
                (project / "sql" / ".index" / "table-index.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertIn("orders", table_index["tables"])
            self.assertIn("user_id", table_index["tables"]["orders"]["columns"])
            self.assertIn("idx_orders_user_id", table_index["tables"]["orders"]["indexes"])
            self.assertIn(
                "explain/orders.explain",
                table_index["tables"]["orders"]["related_explain_files"],
            )
            self.assertIn("using_filesort", table_index["tables"]["orders"]["features"])

    def test_search_returns_table_context(self):
        with tempfile.TemporaryDirectory() as td:
            project = Path(td)
            sql_dir = project / "sql"
            sql_dir.mkdir()
            (sql_dir / "schema.ddl").write_text(
                "CREATE TABLE users (id bigint primary key, name varchar(64));",
                encoding="utf-8",
            )
            run_json(INDEX, ["--project-dir", str(project), "--rebuild"])

            result = run_json(SEARCH, ["--project-dir", str(project), "--table", "users"])

            self.assertEqual(result["status"], "ok")
            self.assertEqual(result["tables"][0]["name"], "users")
            self.assertIn("id", result["tables"][0]["columns"])

    def test_search_by_field_and_keyword_from_indexes(self):
        with tempfile.TemporaryDirectory() as td:
            project = Path(td)
            sql_dir = project / "sql"
            sql_dir.mkdir()
            (sql_dir / "schema.sql").write_text(
                """
CREATE TABLE users (
  id bigint primary key,
  email varchar(128),
  KEY idx_users_email (email)
);
CREATE TABLE orders (
  id bigint primary key,
  user_id bigint,
  note text,
  KEY idx_orders_user_id (user_id)
);
""",
                encoding="utf-8",
            )
            run_json(INDEX, ["--project-dir", str(project), "--rebuild"])

            by_field = run_json(
                SEARCH, ["--project-dir", str(project), "--field", "email"]
            )
            self.assertEqual([table["name"] for table in by_field["tables"]], ["users"])

            by_keyword = run_json(
                SEARCH, ["--project-dir", str(project), "--keyword", "idx_orders_user_id"]
            )
            self.assertEqual([table["name"] for table in by_keyword["tables"]], ["orders"])

    def test_ignores_biz_rules_hidden_dirs_and_unsupported_files(self):
        with tempfile.TemporaryDirectory() as td:
            project = Path(td)
            sql_dir = project / "sql"
            sql_dir.mkdir()
            (sql_dir / "schema.sql").write_text(
                "CREATE TABLE users (id bigint primary key);",
                encoding="utf-8",
            )
            biz_rules = sql_dir / "biz-rules"
            biz_rules.mkdir()
            (biz_rules / "rules.md").write_text(
                "CREATE TABLE leaked_rules (id bigint primary key);",
                encoding="utf-8",
            )
            hidden_dir = sql_dir / ".hidden"
            hidden_dir.mkdir()
            (hidden_dir / "hidden.sql").write_text(
                "CREATE TABLE hidden_table (id bigint primary key);",
                encoding="utf-8",
            )
            (sql_dir / "unsupported.csv").write_text(
                "CREATE TABLE csv_table (id bigint primary key);",
                encoding="utf-8",
            )

            result = run_json(INDEX, ["--project-dir", str(project), "--rebuild"])

            self.assertEqual(result["indexed_files"], 1)
            table_index = json.loads(
                (sql_dir / ".index" / "table-index.json").read_text(encoding="utf-8")
            )
            self.assertEqual(set(table_index["tables"]), {"users"})

    def test_rebuild_ignores_symlink_file_that_targets_outside_sql_dir(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            project = root / "project"
            sql_dir = project / "sql"
            sql_dir.mkdir(parents=True)
            external_file = root / "external.sql"
            external_file.write_text(
                "CREATE TABLE external_leak (id bigint primary key);",
                encoding="utf-8",
            )

            try:
                (sql_dir / "link.sql").symlink_to(external_file)
            except (NotImplementedError, OSError) as exc:
                raise unittest.SkipTest(f"symlink unavailable: {exc}") from exc

            run_json(INDEX, ["--project-dir", str(project), "--rebuild"])

            table_index = json.loads(
                (sql_dir / ".index" / "table-index.json").read_text(encoding="utf-8")
            )
            self.assertNotIn("external_leak", table_index["tables"])

    def test_rebuild_rejects_root_sql_symlink_directory(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            project = root / "project"
            project.mkdir()
            external_sql = root / "external-sql"
            external_sql.mkdir()
            (external_sql / "leak.sql").write_text(
                "CREATE TABLE root_escape (id bigint primary key);",
                encoding="utf-8",
            )

            try:
                (project / "sql").symlink_to(external_sql, target_is_directory=True)
            except (NotImplementedError, OSError) as exc:
                raise unittest.SkipTest(f"symlink unavailable: {exc}") from exc

            index_result = run_json(INDEX, ["--project-dir", str(project), "--rebuild"])
            search_result = run_json(
                SEARCH, ["--project-dir", str(project), "--table", "root_escape"]
            )

            self.assertEqual(index_result["status"], "disabled")
            self.assertEqual(index_result["reason"], "sql_dir_symlink")
            self.assertEqual(index_result["tables"], [])
            self.assertEqual(search_result["status"], "disabled")
            self.assertEqual(search_result["reason"], "sql_dir_symlink")
            self.assertEqual(search_result["tables"], [])
            self.assertFalse((external_sql / ".index" / "table-index.json").exists())

    def test_rebuild_and_search_reject_index_symlink_directory(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            project = root / "project"
            sql_dir = project / "sql"
            sql_dir.mkdir(parents=True)
            (sql_dir / "schema.sql").write_text(
                "CREATE TABLE local_table (id bigint primary key);",
                encoding="utf-8",
            )
            external_index = root / "external-index"
            external_index.mkdir()

            try:
                (sql_dir / ".index").symlink_to(external_index, target_is_directory=True)
            except (NotImplementedError, OSError) as exc:
                raise unittest.SkipTest(f"symlink unavailable: {exc}") from exc

            index_result = run_json(INDEX, ["--project-dir", str(project), "--rebuild"])
            validate_result = run_json(INDEX, ["--project-dir", str(project), "--validate"])
            search_result = run_json(
                SEARCH, ["--project-dir", str(project), "--table", "anything"]
            )

            self.assertEqual(index_result["status"], "disabled")
            self.assertEqual(index_result["reason"], "index_dir_symlink")
            self.assertEqual(validate_result["status"], "disabled")
            self.assertEqual(validate_result["reason"], "index_dir_symlink")
            self.assertEqual(list(external_index.iterdir()), [])
            self.assertEqual(search_result["status"], "disabled")
            self.assertEqual(search_result["reason"], "index_dir_symlink")
            self.assertEqual(search_result["tables"], [])

    def test_rebuild_rejects_index_child_file_symlink(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            project = root / "project"
            sql_dir = project / "sql"
            index_dir = sql_dir / ".index"
            index_dir.mkdir(parents=True)
            (sql_dir / "schema.sql").write_text(
                "CREATE TABLE local_table (id bigint primary key);",
                encoding="utf-8",
            )
            external_file = root / "external-file-digests.json"
            external_file.write_text("external sentinel", encoding="utf-8")

            try:
                (index_dir / "file-digests.json").symlink_to(external_file)
            except (NotImplementedError, OSError) as exc:
                raise unittest.SkipTest(f"symlink unavailable: {exc}") from exc

            index_result = run_json(INDEX, ["--project-dir", str(project), "--rebuild"])
            validate_result = run_json(INDEX, ["--project-dir", str(project), "--validate"])

            self.assertEqual(index_result["status"], "disabled")
            self.assertEqual(index_result["reason"], "index_file_symlink")
            self.assertEqual(validate_result["status"], "disabled")
            self.assertEqual(validate_result["reason"], "index_file_symlink")
            self.assertEqual(external_file.read_text(encoding="utf-8"), "external sentinel")
            self.assertFalse((index_dir / "context-index.json").exists())
            self.assertFalse((index_dir / "table-index.json").exists())

    def test_search_rejects_index_child_file_symlink(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            project = root / "project"
            sql_dir = project / "sql"
            index_dir = sql_dir / ".index"
            index_dir.mkdir(parents=True)
            external_table_index = root / "external-table-index.json"
            external_table_index.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "tables": {
                            "outside_table": {
                                "name": "outside_table",
                                "columns": ["id"],
                                "sources": ["outside.sql"],
                            }
                        },
                    }
                ),
                encoding="utf-8",
            )
            (index_dir / "context-index.json").write_text(
                json.dumps({"version": 1, "dialect": "unknown"}),
                encoding="utf-8",
            )

            try:
                (index_dir / "table-index.json").symlink_to(external_table_index)
            except (NotImplementedError, OSError) as exc:
                raise unittest.SkipTest(f"symlink unavailable: {exc}") from exc

            search_result = run_json(
                SEARCH, ["--project-dir", str(project), "--table", "outside_table"]
            )

            self.assertEqual(search_result["status"], "disabled")
            self.assertEqual(search_result["reason"], "index_file_symlink")
            self.assertEqual(search_result["tables"], [])

    def test_missing_sql_directory_returns_structured_json(self):
        with tempfile.TemporaryDirectory() as td:
            project = Path(td)

            index_result = run_json(INDEX, ["--project-dir", str(project), "--rebuild"])
            search_result = run_json(SEARCH, ["--project-dir", str(project), "--table", "users"])

            self.assertEqual(index_result["status"], "disabled")
            self.assertEqual(index_result["reason"], "sql_dir_missing")
            self.assertEqual(search_result["status"], "disabled")
            self.assertEqual(search_result["reason"], "sql_dir_missing")


if __name__ == "__main__":
    unittest.main()
