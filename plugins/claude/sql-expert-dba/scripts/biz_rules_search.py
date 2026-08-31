#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))
from _frontmatter import get_body, parse_frontmatter
from paths import resolve_biz_rules_dir, resolve_project_sql_dir


INDEX_FILE_NAMES = ("table-index.json", "module-index.json")


def is_within(path: Path, root: Path) -> bool:
    try:
        path.resolve(strict=False).relative_to(root.resolve(strict=False))
    except ValueError:
        return False
    return True


def symlink_escapes(path: Path, root: Path) -> bool:
    return path.is_symlink()


def disabled(reason: str, project_dir: Path, **extra: Any) -> dict[str, Any]:
    result = {
        "status": "disabled",
        "reason": reason,
        "project_dir": str(project_dir),
        "rules": [],
    }
    result.update(extra)
    return result


def check_symlink_escapes(project_dir: Path) -> dict[str, Any] | None:
    sql_dir = resolve_project_sql_dir(project_dir)
    biz_dir = resolve_biz_rules_dir(project_dir)

    if symlink_escapes(sql_dir, project_dir):
        return disabled(
            "sql_dir_symlink_escape",
            project_dir,
            sql_dir=str(sql_dir),
            target=str(sql_dir.resolve(strict=False)),
        )
    if symlink_escapes(biz_dir, project_dir):
        return disabled(
            "biz_rules_dir_symlink_escape",
            project_dir,
            biz_rules_dir=str(biz_dir),
            target=str(biz_dir.resolve(strict=False)),
        )
    if biz_dir.exists():
        for child in biz_dir.iterdir():
            if child.is_dir() and symlink_escapes(child, project_dir):
                return disabled(
                    "module_dir_symlink_escape",
                    project_dir,
                    module_dir=str(child),
                    target=str(child.resolve(strict=False)),
                )
        for name in INDEX_FILE_NAMES:
            index_path = biz_dir / name
            if symlink_escapes(index_path, project_dir):
                return disabled(
                    "index_file_symlink_escape",
                    project_dir,
                    index_file=str(index_path),
                    target=str(index_path.resolve(strict=False)),
                )
    return None


def find_rule_files(biz_dir: Path, project_dir: Path) -> tuple[list[Path], dict[str, Any] | None]:
    files: list[Path] = []
    for module_dir in sorted(biz_dir.iterdir()):
        if not module_dir.is_dir():
            continue
        if symlink_escapes(module_dir, project_dir):
            return [], disabled(
                "module_dir_symlink_escape",
                project_dir,
                module_dir=str(module_dir),
                target=str(module_dir.resolve(strict=False)),
            )
        for filepath in sorted(module_dir.glob("*.md")):
            if symlink_escapes(filepath, project_dir):
                return [], disabled(
                    "rule_file_symlink_escape",
                    project_dir,
                    rule_file=str(filepath),
                    target=str(filepath.resolve(strict=False)),
                )
            if filepath.is_file():
                files.append(filepath)
    return files, None


def as_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [item for item in (str(item).strip() for item in value) if item]
    if value is None:
        return []
    if isinstance(value, str):
        return [item for item in (part.strip() for part in value.split(",")) if item]
    text = str(value).strip()
    return [text] if text else []


def rule_result(filepath: Path, biz_dir: Path) -> dict[str, Any] | None:
    fm = parse_frontmatter(filepath)
    if not fm:
        return None
    return {
        "file": filepath.relative_to(biz_dir).as_posix(),
        "id": str(fm.get("id", "")),
        "title": str(fm.get("title", "")),
        "module": str(fm.get("module", "")),
        "tables": as_list(fm.get("tables", [])),
        "fields": as_list(fm.get("fields", [])),
        "rule_type": str(fm.get("rule_type", "")),
        "source_workflow": str(fm.get("source_workflow", "")),
        "capture_mode": str(fm.get("capture_mode", "")),
        "confidence": str(fm.get("confidence", "")),
        "review_status": str(fm.get("review_status", "")),
        "last_reviewed_at": str(fm.get("last_reviewed_at", "")),
        "_body": get_body(filepath),
    }


def normalized(value: str) -> str:
    return value.strip().lower()


def table_matches(rule: dict[str, Any], table: str) -> bool:
    query = normalized(table)
    return any(normalized(item) == query for item in rule.get("tables", []))


def field_matches(rule: dict[str, Any], field: str) -> bool:
    query = normalized(field)
    if "." in query:
        return any(normalized(item) == query for item in rule.get("fields", []))
    return any(normalized(item).split(".")[-1] == query for item in rule.get("fields", []))


def scalar_values(value: Any) -> list[str]:
    if isinstance(value, dict):
        values: list[str] = []
        for child in value.values():
            values.extend(scalar_values(child))
        return values
    if isinstance(value, list):
        values = []
        for child in value:
            values.extend(scalar_values(child))
        return values
    if value is None:
        return []
    return [str(value)]


def keyword_matches(rule: dict[str, Any], keyword: str) -> bool:
    needle = keyword.lower()
    searchable = " ".join(
        scalar_values(
            {
                key: value
                for key, value in rule.items()
                if key in {"title", "module", "tables", "fields", "rule_type", "_body"}
            }
        )
    ).lower()
    return needle in searchable


def matches(rule: dict[str, Any], args: argparse.Namespace) -> bool:
    if args.module and normalized(rule.get("module", "")) != normalized(args.module):
        return False
    if args.table and not table_matches(rule, args.table):
        return False
    if args.field and not field_matches(rule, args.field):
        return False
    if args.rule_type and normalized(rule.get("rule_type", "")) != normalized(args.rule_type):
        return False
    if args.keyword and not keyword_matches(rule, args.keyword):
        return False
    return True


def public_rule(rule: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in rule.items() if not key.startswith("_")}


def search(project_dir: Path, args: argparse.Namespace) -> dict[str, Any]:
    if not project_dir.exists():
        return disabled("project_dir_missing", project_dir)

    safety_error = check_symlink_escapes(project_dir)
    if safety_error:
        return safety_error

    sql_dir = resolve_project_sql_dir(project_dir)
    biz_dir = resolve_biz_rules_dir(project_dir)
    if not sql_dir.exists():
        return disabled("sql_dir_missing", project_dir, sql_dir=str(sql_dir))
    if not biz_dir.exists():
        return disabled("biz_rules_dir_missing", project_dir, biz_rules_dir=str(biz_dir))

    files, file_error = find_rule_files(biz_dir, project_dir)
    if file_error:
        return file_error

    rules: list[dict[str, Any]] = []
    for filepath in files:
        rule = rule_result(filepath, biz_dir)
        if rule and matches(rule, args):
            rules.append(public_rule(rule))

    return {
        "status": "ok",
        "project_dir": str(project_dir),
        "biz_rules_dir": str(biz_dir),
        "query": {
            "module": args.module,
            "table": args.table,
            "field": args.field,
            "rule_type": args.rule_type,
            "keyword": args.keyword,
        },
        "rules": rules,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Search project business SQL rules")
    parser.add_argument("--project-dir", type=Path, default=Path.cwd())
    parser.add_argument("--module")
    parser.add_argument("--table")
    parser.add_argument("--field")
    parser.add_argument("--rule-type")
    parser.add_argument("--keyword")
    args = parser.parse_args()

    project_dir = args.project_dir.expanduser().resolve(strict=False)
    print(json.dumps(search(project_dir, args), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
