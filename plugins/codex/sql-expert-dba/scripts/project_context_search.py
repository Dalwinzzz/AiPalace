#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))
from paths import resolve_project_sql_dir
from project_context_index import clean_identifier, index_file_symlink


def load_json(path: Path) -> dict[str, Any] | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def normalize_query(value: str) -> str:
    return clean_identifier(value).lower()


def table_matches(table_name: str, query: str) -> bool:
    normalized_name = table_name.lower()
    normalized_query = normalize_query(query)
    return normalized_name == normalized_query or normalized_name.split(".")[-1] == normalized_query


def field_matches(table_name: str, table: dict[str, Any], query: str) -> bool:
    normalized_query = normalize_query(query)
    if "." in normalized_query:
        table_query, field_query = normalized_query.rsplit(".", 1)
        if not table_matches(table_name, table_query):
            return False
    else:
        field_query = normalized_query

    columns = {str(column).lower() for column in table.get("columns", [])}
    if field_query in columns:
        return True

    for index_columns in table.get("indexes", {}).values():
        if field_query in {str(column).lower() for column in index_columns}:
            return True
    return False


def keyword_matches(table_name: str, table: dict[str, Any], keyword: str) -> bool:
    needle = keyword.lower()
    searchable = json.dumps({"name": table_name, **table}, ensure_ascii=False).lower()
    return needle in searchable


def table_result(table_name: str, table: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": table.get("name", table_name),
        "columns": table.get("columns", []),
        "primary_keys": table.get("primary_keys", []),
        "indexes": table.get("indexes", {}),
        "foreign_keys": table.get("foreign_keys", []),
        "sources": table.get("sources", []),
        "related_explain_files": table.get("related_explain_files", []),
        "related_slow_sql_files": table.get("related_slow_sql_files", []),
        "features": table.get("features", []),
    }


def search_tables(table_index: dict[str, Any], args: argparse.Namespace) -> list[dict[str, Any]]:
    tables = table_index.get("tables", {})
    if not isinstance(tables, dict):
        return []

    matched: dict[str, dict[str, Any]] = {}
    has_filters = bool(args.table or args.field or args.keyword)
    for table_name, table in tables.items():
        if not isinstance(table, dict):
            continue
        matches = not has_filters
        if args.table and any(table_matches(table_name, query) for query in args.table):
            matches = True
        if args.field and any(field_matches(table_name, table, query) for query in args.field):
            matches = True
        if args.keyword and keyword_matches(table_name, table, args.keyword):
            matches = True
        if matches:
            matched[table_name] = table_result(table_name, table)
    return list(matched.values())


def collect_matched_files(tables: list[dict[str, Any]]) -> list[str]:
    files: list[str] = []
    for table in tables:
        for key in ("sources", "related_explain_files", "related_slow_sql_files"):
            for rel_path in table.get(key, []):
                if rel_path not in files:
                    files.append(rel_path)
    return files


def search(project_dir: Path, args: argparse.Namespace) -> dict[str, Any]:
    sql_dir = resolve_project_sql_dir(project_dir)
    if sql_dir.is_symlink():
        return {
            "status": "disabled",
            "reason": "sql_dir_symlink",
            "project_dir": str(project_dir),
            "sql_dir": str(sql_dir),
            "tables": [],
        }
    if not sql_dir.is_dir():
        return {
            "status": "disabled",
            "reason": "sql_dir_missing",
            "project_dir": str(project_dir),
            "sql_dir": str(sql_dir),
            "tables": [],
        }

    index_dir = sql_dir / ".index"
    if index_dir.is_symlink():
        return {
            "status": "disabled",
            "reason": "index_dir_symlink",
            "project_dir": str(project_dir),
            "sql_dir": str(sql_dir),
            "index_dir": str(index_dir),
            "tables": [],
        }
    if index_file_symlink(index_dir) is not None:
        return {
            "status": "disabled",
            "reason": "index_file_symlink",
            "project_dir": str(project_dir),
            "sql_dir": str(sql_dir),
            "index_dir": str(index_dir),
            "tables": [],
        }

    table_index = load_json(index_dir / "table-index.json")
    context_index = load_json(index_dir / "context-index.json")
    if table_index is None or context_index is None:
        return {
            "status": "missing_index",
            "reason": "index_files_missing",
            "project_dir": str(project_dir),
            "sql_dir": str(sql_dir),
            "tables": [],
        }

    tables = search_tables(table_index, args)
    matched_files = collect_matched_files(tables)
    return {
        "status": "ok",
        "project_dir": str(project_dir),
        "sql_dir": str(sql_dir),
        "query": {
            "tables": args.table,
            "fields": args.field,
            "keyword": args.keyword,
        },
        "tables": tables,
        "matched_files": matched_files,
        "context": {
            "dialect": context_index.get("dialect", "unknown"),
            "explain_files": context_index.get("explain_files", []),
            "slow_sql_files": context_index.get("slow_sql_files", []),
            "notes_files": context_index.get("notes_files", []),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Search project ./sql context indexes")
    parser.add_argument("--project-dir", type=Path, default=Path.cwd())
    parser.add_argument("--table", action="append", default=[])
    parser.add_argument("--field", action="append", default=[])
    parser.add_argument("--keyword")
    args = parser.parse_args()

    project_dir = args.project_dir.expanduser().resolve()
    result = search(project_dir, args)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
