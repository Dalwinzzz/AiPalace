#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))
from _frontmatter import get_body, parse_frontmatter
from biz_rules_git_guard import (
    check_symlink_escapes as check_git_guard_symlink_escapes,
    ensure_ignore,
)
from paths import resolve_biz_rules_dir, resolve_project_sql_dir


RULE_TYPES = {
    "metric_definition",
    "field_semantics",
    "table_relationship",
    "report_template",
    "exclusion_rule",
    "reconciliation_rule",
}
INDEX_FILE_NAMES = ("table-index.json", "module-index.json")
AUTOMATIC_CAPTURE_MODES = {"automatic", "auto_hook", "auto_automation"}
MISSING_CONTEXT_VALUES = {"", "unknown", "none", "null", "n/a", "na", "uncategorized"}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def json_dump(data: dict[str, Any], path: Path) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def normalize_list(value: Any) -> list[str]:
    if not value:
        return []
    if isinstance(value, list):
        items: list[str] = []
        for raw_item in value:
            item = str(raw_item).strip()
            if item and item not in items:
                items.append(item)
        return items
    if not isinstance(value, str):
        return [str(value).strip()]

    items: list[str] = []
    for raw_item in value.split(","):
        item = raw_item.strip()
        if item and item not in items:
            items.append(item)
    return items


def module_slug(module: str | None) -> str:
    raw = "" if module is None else module.strip()
    if raw.lower() in MISSING_CONTEXT_VALUES - {"uncategorized"}:
        return "uncategorized"
    cleaned = "".join(ch.lower() if ch.isalnum() else "-" for ch in raw)
    while "--" in cleaned:
        cleaned = cleaned.replace("--", "-")
    return cleaned.strip("-") or "uncategorized"


def slugify(value: str, max_len: int = 80) -> str:
    cleaned = "".join(ch.lower() if ch.isalnum() else "-" for ch in value.strip())
    while "--" in cleaned:
        cleaned = cleaned.replace("--", "-")
    cleaned = cleaned.strip("-")
    if len(cleaned) > max_len:
        cleaned = cleaned[:max_len].rstrip("-")
    return cleaned or "untitled"


def normalize_title(value: str) -> str:
    return " ".join(part for part in slugify(value, max_len=200).split("-") if part)


def normalized_set(values: list[str]) -> set[str]:
    return {value.lower() for value in values}


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
    }
    result.update(extra)
    return result


def missing_context_value(value: str | None) -> bool:
    return (value or "").strip().lower() in MISSING_CONTEXT_VALUES


def missing_list_context(values: list[str]) -> bool:
    return not values or any(missing_context_value(value) for value in values)


def is_automatic_capture(args: argparse.Namespace) -> bool:
    if (args.capture_mode or "").strip().lower() not in AUTOMATIC_CAPTURE_MODES:
        return False
    return True


def automatic_context_gaps(args: argparse.Namespace, project_dir_exists: bool) -> list[str]:
    if not is_automatic_capture(args):
        return []

    gaps: list[str] = []
    if not project_dir_exists:
        gaps.append("workspace")
    if missing_context_value(args.module):
        gaps.append("module")
    if missing_list_context(args.tables):
        gaps.append("tables")
    if missing_context_value(args.source_workflow):
        gaps.append("source_workflow")
    if missing_context_value(args.body):
        gaps.append("final_rule_conclusion")
    return gaps


def check_existing_symlink_escapes(
    project_dir: Path,
    module: str,
) -> dict[str, Any] | None:
    sql_dir = resolve_project_sql_dir(project_dir)
    biz_dir = resolve_biz_rules_dir(project_dir)
    module_dir = biz_dir / module

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
    if symlink_escapes(module_dir, project_dir):
        return disabled(
            "module_dir_symlink_escape",
            project_dir,
            module_dir=str(module_dir),
            target=str(module_dir.resolve(strict=False)),
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
            if child.is_dir():
                for rule_file in child.glob("*.md"):
                    if symlink_escapes(rule_file, project_dir):
                        return disabled(
                            "rule_file_symlink_escape",
                            project_dir,
                            rule_file=str(rule_file),
                            target=str(rule_file.resolve(strict=False)),
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


def ensure_rule_dirs(project_dir: Path, module: str) -> tuple[Path, Path, Path]:
    sql_dir = resolve_project_sql_dir(project_dir)
    biz_dir = resolve_biz_rules_dir(project_dir)
    module_dir = biz_dir / module
    sql_dir.mkdir(exist_ok=True)
    biz_dir.mkdir(exist_ok=True)
    module_dir.mkdir(exist_ok=True)
    return sql_dir, biz_dir, module_dir


def yaml_scalar(value: object) -> str:
    text = "" if value is None else str(value)
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\n", "\\n")
    return f'"{text}"'


def yaml_list(values: list[str]) -> str:
    if not values:
        return "[]"
    rendered = []
    for value in values:
        if all(ch.isalnum() or ch in "._-$" for ch in value):
            rendered.append(value)
        else:
            rendered.append(yaml_scalar(value))
    return f"[{', '.join(rendered)}]"


def generate_id(module: str, rule_type: str, title: str) -> str:
    seed = f"{time.time_ns()}|{module}|{rule_type}|{title}".encode("utf-8")
    return f"biz-rule-{hashlib.sha256(seed).hexdigest()[:10]}"


def build_frontmatter(args: argparse.Namespace, entry_id: str, module: str) -> str:
    return "\n".join(
        [
            "---",
            f"id: {yaml_scalar(entry_id)}",
            f"title: {yaml_scalar(args.title)}",
            f"module: {yaml_scalar(module)}",
            f"tables: {yaml_list(args.tables)}",
            f"fields: {yaml_list(args.fields)}",
            f"rule_type: {args.rule_type}",
            f"source_workflow: {yaml_scalar(args.source_workflow or 'unknown')}",
            f"capture_mode: {yaml_scalar(args.capture_mode or 'manual')}",
            f"confidence: {yaml_scalar(args.confidence or 'medium')}",
            f"review_status: {yaml_scalar(args.review_status or 'approved')}",
            f"last_reviewed_at: {yaml_scalar(args.last_reviewed_at or today())}",
            "---",
        ]
    )


def find_rule_files(biz_dir: Path, project_dir: Path) -> list[Path]:
    if not biz_dir.is_dir():
        return []

    files: list[Path] = []
    for module_dir in sorted(biz_dir.iterdir()):
        if not module_dir.is_dir():
            continue
        if symlink_escapes(module_dir, project_dir):
            continue
        for filepath in sorted(module_dir.glob("*.md")):
            if symlink_escapes(filepath, project_dir):
                continue
            if filepath.is_file():
                files.append(filepath)
    return files


def read_rules(biz_dir: Path, project_dir: Path) -> list[dict[str, Any]]:
    rules: list[dict[str, Any]] = []
    for filepath in find_rule_files(biz_dir, project_dir):
        fm = parse_frontmatter(filepath)
        if not fm:
            continue
        rel = filepath.relative_to(biz_dir).as_posix()
        rules.append({"file": rel, "frontmatter": fm, "body": get_body(filepath)})
    return rules


def rule_key(module: str, rule_type: str, tables: list[str], title: str) -> tuple[str, str, tuple[str, ...], str]:
    return (
        module.lower(),
        rule_type.lower(),
        tuple(sorted(normalized_set(tables))),
        normalize_title(title),
    )


def existing_key(rule: dict[str, Any]) -> tuple[str, str, tuple[str, ...], str]:
    fm = rule["frontmatter"]
    return rule_key(
        str(fm.get("module", "")),
        str(fm.get("rule_type", "")),
        normalize_list(fm.get("tables")),
        str(fm.get("title", "")),
    )


def detect_duplicate(rules: list[dict[str, Any]], candidate_key: tuple[str, str, tuple[str, ...], str]) -> dict[str, Any] | None:
    for rule in rules:
        if existing_key(rule) == candidate_key:
            return rule
    return None


def normalize_body(value: str) -> str:
    return " ".join(value.split()).lower()


def body_differs(rule: dict[str, Any], body: str) -> bool:
    return normalize_body(str(rule.get("body", ""))) != normalize_body(body)


def detect_conflict(
    rules: list[dict[str, Any]],
    module: str,
    rule_type: str,
    tables: list[str],
    fields: list[str],
    body: str,
) -> dict[str, Any] | None:
    if rule_type != "metric_definition":
        return None

    candidate_tables = normalized_set(tables)
    candidate_fields = normalized_set(fields)
    normalized_body = " ".join(body.split()).lower()
    for rule in rules:
        fm = rule["frontmatter"]
        if str(fm.get("module", "")).lower() != module.lower():
            continue
        if str(fm.get("rule_type", "")).lower() != "metric_definition":
            continue

        existing_tables = normalized_set(normalize_list(fm.get("tables")))
        if existing_tables != candidate_tables:
            continue

        existing_fields = normalized_set(normalize_list(fm.get("fields")))
        fields_overlap = (
            bool(candidate_fields and existing_fields and candidate_fields & existing_fields)
            or not candidate_fields
            or not existing_fields
        )
        existing_body = normalize_body(str(rule.get("body", "")))
        if fields_overlap and existing_body and existing_body != normalized_body:
            return rule
    return None


def next_rule_path(module_dir: Path, title: str) -> Path:
    stem = slugify(title)
    candidate = module_dir / f"{stem}.md"
    counter = 2
    while candidate.exists() or candidate.is_symlink():
        candidate = module_dir / f"{stem}-{counter}.md"
        counter += 1
    return candidate


def index_entry(rule: dict[str, Any]) -> dict[str, Any]:
    fm = rule["frontmatter"]
    return {
        "id": str(fm.get("id", "")),
        "title": str(fm.get("title", "")),
        "module": str(fm.get("module", "")),
        "tables": normalize_list(fm.get("tables")),
        "fields": normalize_list(fm.get("fields")),
        "rule_type": str(fm.get("rule_type", "")),
        "source_workflow": str(fm.get("source_workflow", "")),
        "capture_mode": str(fm.get("capture_mode", "")),
        "confidence": str(fm.get("confidence", "")),
        "review_status": str(fm.get("review_status", "")),
        "last_reviewed_at": str(fm.get("last_reviewed_at", "")),
        "file": str(rule["file"]),
    }


def rebuild_indexes(biz_dir: Path, project_dir: Path) -> dict[str, Any]:
    rules = read_rules(biz_dir, project_dir)
    table_index: dict[str, Any] = {
        "version": 1,
        "last_updated": utc_now(),
        "tables": {},
    }
    module_index: dict[str, Any] = {
        "version": 1,
        "last_updated": utc_now(),
        "modules": {},
    }

    for rule in rules:
        entry = index_entry(rule)
        module_index["modules"].setdefault(entry["module"], []).append(entry)
        for table in entry["tables"]:
            table_index["tables"].setdefault(table, []).append(entry)

    json_dump(table_index, biz_dir / "table-index.json")
    json_dump(module_index, biz_dir / "module-index.json")
    return {"table_index": table_index, "module_index": module_index}


def capture(project_dir: Path, args: argparse.Namespace) -> dict[str, Any]:
    args.tables = normalize_list(args.tables)
    args.fields = normalize_list(args.fields)

    missing_context = automatic_context_gaps(args, project_dir.exists())
    if missing_context:
        return {
            "status": "skipped",
            "reason": "insufficient_automatic_context",
            "missing_context": missing_context,
            "capture_mode": args.capture_mode,
            "project_dir": str(project_dir),
        }

    if not project_dir.exists():
        return {"status": "error", "reason": "project_dir_missing", "project_dir": str(project_dir)}

    args.rule_type = (args.rule_type or "").strip().lower()
    if args.rule_type not in RULE_TYPES:
        return {
            "status": "error",
            "reason": "invalid_rule_type",
            "supported_rule_types": sorted(RULE_TYPES),
        }

    module = module_slug(args.module)

    safety_error = check_git_guard_symlink_escapes(project_dir)
    if safety_error:
        return safety_error

    safety_error = check_existing_symlink_escapes(project_dir, module)
    if safety_error:
        return safety_error

    _, biz_dir, module_dir = ensure_rule_dirs(project_dir, module)

    safety_error = check_existing_symlink_escapes(project_dir, module)
    if safety_error:
        return safety_error

    existing_rules = read_rules(biz_dir, project_dir)
    conflict = detect_conflict(
        existing_rules,
        module,
        args.rule_type,
        args.tables,
        args.fields,
        args.body,
    )
    if conflict:
        return {
            "status": "conflict",
            "module": module,
            "existing_file": conflict["file"],
            "reason": "metric_definition_conflict",
        }

    candidate_key = rule_key(module, args.rule_type, args.tables, args.title)
    duplicate = detect_duplicate(existing_rules, candidate_key)
    if duplicate:
        if args.rule_type == "metric_definition" and body_differs(duplicate, args.body):
            return {
                "status": "conflict",
                "module": module,
                "existing_file": duplicate["file"],
                "reason": "metric_definition_conflict",
            }
        return {
            "status": "duplicate",
            "module": module,
            "existing_file": duplicate["file"],
            "reason": "duplicate_rule_key",
        }

    entry_id = generate_id(module, args.rule_type, args.title)
    rule_path = next_rule_path(module_dir, args.title)
    if symlink_escapes(rule_path, project_dir):
        return disabled(
            "rule_file_symlink_escape",
            project_dir,
            rule_file=str(rule_path),
            target=str(rule_path.resolve(strict=False)),
        )

    rule_path.write_text(
        build_frontmatter(args, entry_id, module) + "\n\n" + args.body.strip() + "\n",
        encoding="utf-8",
    )

    safety_error = check_existing_symlink_escapes(project_dir, module)
    if safety_error:
        return safety_error

    indexes = rebuild_indexes(biz_dir, project_dir)
    ignore_status = ensure_ignore(project_dir)
    rel_file = rule_path.relative_to(biz_dir).as_posix()
    return {
        "status": "captured",
        "id": entry_id,
        "module": module,
        "file": rel_file,
        "rule_type": args.rule_type,
        "tables": args.tables,
        "fields": args.fields,
        "ignore_status": ignore_status,
        "table_index_entries": sum(len(entries) for entries in indexes["table_index"]["tables"].values()),
        "module_index_entries": sum(len(entries) for entries in indexes["module_index"]["modules"].values()),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Capture project business SQL rules")
    parser.add_argument("--project-dir", type=Path, default=Path.cwd())
    parser.add_argument("--module", default="uncategorized")
    parser.add_argument("--title", required=True)
    parser.add_argument("--rule-type", required=True)
    parser.add_argument("--tables", default="")
    parser.add_argument("--fields", default="")
    parser.add_argument("--source-workflow", default="unknown")
    parser.add_argument("--capture-mode", default="manual")
    parser.add_argument("--confidence", default="medium")
    parser.add_argument("--review-status", default="approved")
    parser.add_argument("--last-reviewed-at")
    parser.add_argument("--body", required=True)
    args = parser.parse_args()

    project_dir = args.project_dir.expanduser().resolve(strict=False)
    print(json.dumps(capture(project_dir, args), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
