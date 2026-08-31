#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))
from paths import resolve_project_sql_dir


SUPPORTED_EXTENSIONS = {".sql", ".ddl", ".explain", ".log", ".txt", ".md"}
INDEX_VERSION = 1
INDEX_FILE_NAMES = ("file-digests.json", "context-index.json", "table-index.json")

CONSTRAINT_STARTERS = {
    "constraint",
    "primary",
    "unique",
    "key",
    "index",
    "foreign",
    "check",
    "exclude",
}

CREATE_TABLE_RE = re.compile(
    r"\bcreate\s+(?:temporary\s+)?table\s+(?:if\s+not\s+exists\s+)?"
    r"(?P<name>(?:[`\"\[]?[A-Za-z_][\w$]*[`\"\]]?\.)?[`\"\[]?[A-Za-z_][\w$]*[`\"\]]?)\s*\(",
    re.IGNORECASE,
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def json_dump(data: dict[str, Any], path: Path) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def clean_identifier(identifier: str) -> str:
    value = identifier.strip().strip(",")
    parts = []
    for part in value.split("."):
        cleaned = part.strip().strip("`\"[]")
        if cleaned:
            parts.append(cleaned)
    return ".".join(parts)


def first_identifier(value: str) -> tuple[str, int] | None:
    match = re.match(
        r"\s*(?:`([^`]+)`|\"([^\"]+)\"|\[([^\]]+)\]|([A-Za-z_][\w$]*))",
        value,
    )
    if not match:
        return None
    return next(group for group in match.groups() if group), match.end()


def append_unique(items: list[str], value: str) -> None:
    if value and value not in items:
        items.append(value)


def extend_unique(items: list[str], values: list[str]) -> None:
    for value in values:
        append_unique(items, value)


def should_index(path: Path, sql_dir: Path) -> bool:
    try:
        rel = path.relative_to(sql_dir)
    except ValueError:
        return False
    if path.is_symlink():
        return False
    if not path.is_file():
        return False
    if "biz-rules" in rel.parts:
        return False
    if any(part.startswith(".") for part in rel.parts):
        return False
    return path.suffix.lower() in SUPPORTED_EXTENSIONS


def read_text_if_supported(path: Path) -> tuple[str, bytes] | None:
    try:
        data = path.read_bytes()
    except OSError:
        return None

    sample = data[:4096]
    if b"\x00" in sample:
        return None

    text = data.decode("utf-8", errors="replace")
    replacement_count = text.count("\ufffd")
    if replacement_count > max(1, len(text) // 100):
        return None
    return text, data


def file_digest(path: Path, sql_dir: Path, data: bytes) -> dict[str, Any]:
    stat = path.stat()
    rel = path.relative_to(sql_dir).as_posix()
    return {
        "path": rel,
        "mtime": stat.st_mtime,
        "size": stat.st_size,
        "hash": hashlib.sha256(data).hexdigest(),
    }


def matching_close_paren(text: str, open_idx: int) -> int | None:
    depth = 0
    quote: str | None = None
    escaped = False
    i = open_idx
    while i < len(text):
        char = text[i]
        nxt = text[i + 1] if i + 1 < len(text) else ""

        if quote:
            if quote == "'" and char == "\\" and not escaped:
                escaped = True
                i += 1
                continue
            if char == quote and not escaped:
                quote = None
            escaped = False
            i += 1
            continue

        if char in ("'", '"', "`"):
            quote = char
            i += 1
            continue
        if char == "-" and nxt == "-":
            newline = text.find("\n", i + 2)
            i = len(text) if newline == -1 else newline + 1
            continue
        if char == "/" and nxt == "*":
            end = text.find("*/", i + 2)
            i = len(text) if end == -1 else end + 2
            continue
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return None


def split_top_level_csv(value: str) -> list[str]:
    parts: list[str] = []
    start = 0
    depth = 0
    quote: str | None = None
    i = 0
    while i < len(value):
        char = value[i]
        if quote:
            if char == quote:
                quote = None
            i += 1
            continue
        if char in ("'", '"', "`"):
            quote = char
            i += 1
            continue
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
        elif char == "," and depth == 0:
            parts.append(value[start:i].strip())
            start = i + 1
        i += 1
    tail = value[start:].strip()
    if tail:
        parts.append(tail)
    return parts


def parse_column_list(value: str) -> list[str]:
    columns: list[str] = []
    for raw_column in split_top_level_csv(value):
        parsed = first_identifier(raw_column.strip())
        if not parsed:
            continue
        name, end = parsed
        rest = raw_column[end:].lstrip()
        if rest.startswith("(") and name.upper() in {
            "LOWER",
            "UPPER",
            "COALESCE",
            "CAST",
            "DATE",
            "YEAR",
            "MONTH",
        }:
            continue
        append_unique(columns, clean_identifier(name))
    return columns


def parse_primary_key(segment: str) -> list[str]:
    match = re.search(
        r"(?:constraint\s+[`\"\[]?[A-Za-z_][\w$]*[`\"\]]?\s+)?primary\s+key"
        r"(?:\s+using\s+\w+)?\s*\((?P<columns>[^)]+)\)",
        segment,
        re.IGNORECASE,
    )
    if not match:
        return []
    return parse_column_list(match.group("columns"))


def parse_index(segment: str) -> tuple[str, list[str]] | None:
    match = re.search(
        r"(?:unique\s+|fulltext\s+|spatial\s+)?(?:key|index)\s+"
        r"(?P<name>[`\"\[]?[A-Za-z_][\w$]*[`\"\]]?)"
        r"(?:\s+using\s+\w+)?\s*\((?P<columns>[^)]+)\)",
        segment,
        re.IGNORECASE,
    )
    if not match:
        return None
    return clean_identifier(match.group("name")), parse_column_list(match.group("columns"))


def parse_foreign_key(segment: str) -> dict[str, Any] | None:
    match = re.search(
        r"(?:constraint\s+(?P<name>[`\"\[]?[A-Za-z_][\w$]*[`\"\]]?)\s+)?"
        r"foreign\s+key\s*\((?P<columns>[^)]+)\)\s+references\s+"
        r"(?P<ref_table>(?:[`\"\[]?[A-Za-z_][\w$]*[`\"\]]?\.)?[`\"\[]?[A-Za-z_][\w$]*[`\"\]]?)"
        r"\s*\((?P<ref_columns>[^)]+)\)",
        segment,
        re.IGNORECASE,
    )
    if not match:
        return None
    return {
        "name": clean_identifier(match.group("name") or ""),
        "columns": parse_column_list(match.group("columns")),
        "references_table": clean_identifier(match.group("ref_table")),
        "references_columns": parse_column_list(match.group("ref_columns")),
    }


def parse_column(segment: str) -> dict[str, Any] | None:
    parsed = first_identifier(segment)
    if not parsed:
        return None
    name, end = parsed
    if name.lower() in CONSTRAINT_STARTERS:
        return None

    remainder = segment[end:].strip()
    if not remainder:
        return None
    constraint_match = re.search(
        r"\b(not\s+null|null|default|primary\s+key|unique|references|comment|collate|"
        r"generated|auto_increment|identity|constraint|check)\b",
        remainder,
        re.IGNORECASE,
    )
    column_type = (
        remainder[: constraint_match.start()].strip()
        if constraint_match
        else remainder.strip()
    )
    return {
        "name": clean_identifier(name),
        "type": column_type,
        "nullable": not bool(re.search(r"\bnot\s+null\b", remainder, re.IGNORECASE)),
        "primary_key": bool(re.search(r"\bprimary\s+key\b", remainder, re.IGNORECASE)),
        "references": parse_inline_reference(remainder),
    }


def parse_inline_reference(remainder: str) -> dict[str, Any] | None:
    match = re.search(
        r"\breferences\s+"
        r"(?P<ref_table>(?:[`\"\[]?[A-Za-z_][\w$]*[`\"\]]?\.)?[`\"\[]?[A-Za-z_][\w$]*[`\"\]]?)"
        r"\s*\((?P<ref_columns>[^)]+)\)",
        remainder,
        re.IGNORECASE,
    )
    if not match:
        return None
    return {
        "references_table": clean_identifier(match.group("ref_table")),
        "references_columns": parse_column_list(match.group("ref_columns")),
    }


def empty_table_entry(name: str, source: str) -> dict[str, Any]:
    return {
        "name": name,
        "columns": [],
        "column_details": {},
        "primary_keys": [],
        "indexes": {},
        "foreign_keys": [],
        "sources": [source],
        "related_explain_files": [],
        "related_slow_sql_files": [],
        "features": [],
    }


def foreign_key_exists(items: list[dict[str, Any]], candidate: dict[str, Any]) -> bool:
    return any(json.dumps(item, sort_keys=True) == json.dumps(candidate, sort_keys=True) for item in items)


def extract_create_tables(text: str, source: str) -> dict[str, dict[str, Any]]:
    tables: dict[str, dict[str, Any]] = {}
    for match in CREATE_TABLE_RE.finditer(text):
        table_name = clean_identifier(match.group("name"))
        close_idx = matching_close_paren(text, match.end() - 1)
        if close_idx is None:
            continue
        body = text[match.end() : close_idx]
        table = empty_table_entry(table_name, source)

        for segment in split_top_level_csv(body):
            normalized_segment = segment.strip().rstrip(",")
            if not normalized_segment:
                continue

            primary_keys = parse_primary_key(normalized_segment)
            extend_unique(table["primary_keys"], primary_keys)

            foreign_key = parse_foreign_key(normalized_segment)
            if foreign_key and not foreign_key_exists(table["foreign_keys"], foreign_key):
                table["foreign_keys"].append(foreign_key)

            index = parse_index(normalized_segment)
            if index:
                index_name, columns = index
                table["indexes"][index_name] = columns

            column = parse_column(normalized_segment)
            if not column:
                continue
            column_name = column["name"]
            append_unique(table["columns"], column_name)
            table["column_details"][column_name] = {
                "type": column["type"],
                "nullable": column["nullable"],
            }
            if column["primary_key"]:
                append_unique(table["primary_keys"], column_name)
            if column["references"]:
                inline_fk = {
                    "name": "",
                    "columns": [column_name],
                    **column["references"],
                }
                if not foreign_key_exists(table["foreign_keys"], inline_fk):
                    table["foreign_keys"].append(inline_fk)

        tables[table_name] = table
    return tables


def merge_table_entry(target: dict[str, Any], source: dict[str, Any]) -> None:
    extend_unique(target["columns"], source.get("columns", []))
    target["column_details"].update(source.get("column_details", {}))
    extend_unique(target["primary_keys"], source.get("primary_keys", []))
    target["indexes"].update(source.get("indexes", {}))
    for foreign_key in source.get("foreign_keys", []):
        if not foreign_key_exists(target["foreign_keys"], foreign_key):
            target["foreign_keys"].append(foreign_key)
    extend_unique(target["sources"], source.get("sources", []))
    extend_unique(target["related_explain_files"], source.get("related_explain_files", []))
    extend_unique(target["related_slow_sql_files"], source.get("related_slow_sql_files", []))
    extend_unique(target["features"], source.get("features", []))


def extract_features(text: str, rel_path: str) -> list[str]:
    lower = text.lower()
    path_lower = rel_path.lower()
    features: list[str] = []

    checks = [
        ("using_filesort", "using filesort" in lower),
        ("using_temporary", "using temporary" in lower),
        ("full_table_scan", bool(re.search(r"\btype\s*[:=]\s*all\b", lower)) or "full table scan" in lower),
        ("query_time", "query_time" in lower or "query time" in lower),
        ("lock_time", "lock_time" in lower or "lock time" in lower),
        ("rows_examined", "rows_examined" in lower or "rows examined" in lower),
        ("slow_query", "slow" in path_lower or "query_time" in lower),
        ("explain_plan", rel_path.lower().endswith(".explain") or bool(re.search(r"\bexplain\b", lower))),
        ("select_statement", bool(re.search(r"\bselect\b", lower))),
    ]
    for feature, present in checks:
        if present:
            features.append(feature)
    return features


def infer_dialect(texts: list[str]) -> str:
    combined = "\n".join(texts).lower()
    mysql_score = sum(
        token in combined
        for token in ("`", "engine=", "auto_increment", "using filesort", "query_time")
    )
    postgres_score = sum(
        token in combined
        for token in ("serial", "bigserial", "public.", "::", "generated by default as identity")
    )
    if mysql_score > postgres_score and mysql_score > 0:
        return "mysql"
    if postgres_score > 0:
        return "postgresql"
    return "unknown"


def classify_file(rel_path: str, suffix: str, text: str, tables: dict[str, Any], features: list[str]) -> str:
    lower_path = rel_path.lower()
    lower_text = text.lower()
    if tables:
        return "ddl"
    if suffix == ".ddl":
        return "ddl"
    if suffix == ".explain" or "explain_plan" in features:
        return "explain"
    if suffix == ".log" or "slow" in lower_path or "query_time" in lower_text:
        return "slow_sql"
    if suffix in {".md", ".txt"}:
        return "note"
    return "sql"


def contains_identifier(haystack: str, identifier: str) -> bool:
    escaped = re.escape(identifier.lower())
    return bool(re.search(rf"(?<![\w$]){escaped}(?![\w$])", haystack.lower()))


def find_related_tables(text: str, rel_path: str, table_names: list[str]) -> list[str]:
    haystack = f"{rel_path}\n{text}".lower()
    related: list[str] = []
    for table_name in table_names:
        candidates = [table_name]
        if "." in table_name:
            candidates.append(table_name.split(".")[-1])
        if any(contains_identifier(haystack, candidate) for candidate in candidates):
            related.append(table_name)
    return related


def build_project_context(project_dir: Path) -> dict[str, Any]:
    sql_dir = resolve_project_sql_dir(project_dir)
    indexed_at = utc_now()
    table_index: dict[str, Any] = {
        "version": INDEX_VERSION,
        "last_indexed_at": indexed_at,
        "tables": {},
    }
    file_digests: dict[str, Any] = {
        "version": INDEX_VERSION,
        "last_indexed_at": indexed_at,
        "files": {},
    }
    context_index: dict[str, Any] = {
        "version": INDEX_VERSION,
        "last_indexed_at": indexed_at,
        "dialect": "unknown",
        "indexed_files": [],
        "ddl_files": [],
        "explain_files": [],
        "slow_sql_files": [],
        "notes_files": [],
        "ddl_coverage": {"tables": 0, "files": 0},
        "files": [],
    }
    texts: list[str] = []
    file_texts: dict[str, str] = {}

    for path in sorted(sql_dir.rglob("*")):
        if not should_index(path, sql_dir):
            continue
        read_result = read_text_if_supported(path)
        if read_result is None:
            continue
        text, data = read_result
        rel_path = path.relative_to(sql_dir).as_posix()
        texts.append(text)
        file_texts[rel_path] = text
        file_digests["files"][rel_path] = file_digest(path, sql_dir, data)

        tables = extract_create_tables(text, rel_path)
        for table_name, table in tables.items():
            if table_name not in table_index["tables"]:
                table_index["tables"][table_name] = table
            else:
                merge_table_entry(table_index["tables"][table_name], table)

        features = extract_features(text, rel_path)
        kind = classify_file(rel_path, path.suffix.lower(), text, tables, features)
        record = {
            "path": rel_path,
            "extension": path.suffix.lower(),
            "kind": kind,
            "tables": list(tables),
            "features": features,
        }
        context_index["files"].append(record)
        context_index["indexed_files"].append(rel_path)
        if kind == "ddl":
            context_index["ddl_files"].append(rel_path)
        elif kind == "explain":
            context_index["explain_files"].append(rel_path)
        elif kind == "slow_sql":
            context_index["slow_sql_files"].append(rel_path)
        elif kind == "note":
            context_index["notes_files"].append(rel_path)

    table_names = list(table_index["tables"])
    for record in context_index["files"]:
        rel_path = record["path"]
        related_tables = find_related_tables(file_texts.get(rel_path, ""), rel_path, table_names)
        extend_unique(record["tables"], related_tables)
        if record["kind"] == "explain":
            for table_name in related_tables:
                append_unique(table_index["tables"][table_name]["related_explain_files"], rel_path)
                extend_unique(table_index["tables"][table_name]["features"], record["features"])
        elif record["kind"] == "slow_sql":
            for table_name in related_tables:
                append_unique(table_index["tables"][table_name]["related_slow_sql_files"], rel_path)
                extend_unique(table_index["tables"][table_name]["features"], record["features"])

    context_index["dialect"] = infer_dialect(texts)
    context_index["ddl_coverage"] = {
        "tables": len(table_index["tables"]),
        "files": len(context_index["ddl_files"]),
    }
    return {
        "file_digests": file_digests,
        "context_index": context_index,
        "table_index": table_index,
    }


def index_file_symlink(index_dir: Path) -> Path | None:
    for file_name in INDEX_FILE_NAMES:
        path = index_dir / file_name
        if path.is_symlink():
            return path
    return None


def persist_indexes(sql_dir: Path, indexes: dict[str, Any]) -> tuple[bool, str]:
    index_dir = sql_dir / ".index"
    if index_dir.is_symlink():
        return False, "index_dir_symlink"
    if index_file_symlink(index_dir) is not None:
        return False, "index_file_symlink"
    try:
        index_dir.mkdir(parents=True, exist_ok=True)
        if index_file_symlink(index_dir) is not None:
            return False, "index_file_symlink"
        json_dump(indexes["file_digests"], index_dir / "file-digests.json")
        json_dump(indexes["context_index"], index_dir / "context-index.json")
        json_dump(indexes["table_index"], index_dir / "table-index.json")
    except OSError as exc:
        return False, str(exc)
    return True, ""


def load_json(path: Path) -> dict[str, Any] | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def rebuild(project_dir: Path) -> dict[str, Any]:
    sql_dir = resolve_project_sql_dir(project_dir)
    if sql_dir.is_symlink():
        return {
            "status": "disabled",
            "reason": "sql_dir_symlink",
            "project_dir": str(project_dir),
            "sql_dir": str(sql_dir),
            "indexed_files": 0,
            "tables": [],
            "dialect": "unknown",
        }
    if not sql_dir.is_dir():
        return {
            "status": "disabled",
            "reason": "sql_dir_missing",
            "project_dir": str(project_dir),
            "sql_dir": str(sql_dir),
        }
    if (sql_dir / ".index").is_symlink():
        return {
            "status": "disabled",
            "reason": "index_dir_symlink",
            "project_dir": str(project_dir),
            "sql_dir": str(sql_dir),
            "index_dir": str(sql_dir / ".index"),
            "indexed_files": 0,
            "tables": [],
            "dialect": "unknown",
        }
    if index_file_symlink(sql_dir / ".index") is not None:
        return {
            "status": "disabled",
            "reason": "index_file_symlink",
            "project_dir": str(project_dir),
            "sql_dir": str(sql_dir),
            "index_dir": str(sql_dir / ".index"),
            "indexed_files": 0,
            "tables": [],
            "dialect": "unknown",
        }

    indexes = build_project_context(project_dir)
    persisted, error = persist_indexes(sql_dir, indexes)
    status = "indexed" if persisted else "indexed_not_persisted"
    reason = "index_write_failed"
    if error == "index_dir_symlink":
        status = "disabled"
        reason = "index_dir_symlink"
    elif error == "index_file_symlink":
        status = "disabled"
        reason = "index_file_symlink"
    result = {
        "status": status,
        "persisted": persisted,
        "project_dir": str(project_dir),
        "sql_dir": str(sql_dir),
        "index_dir": str(sql_dir / ".index"),
        "indexed_files": len(indexes["context_index"]["indexed_files"]),
        "tables": sorted(indexes["table_index"]["tables"]),
        "dialect": indexes["context_index"]["dialect"],
    }
    if error:
        result["reason"] = reason
        result["error"] = error
    return result


def validate(project_dir: Path) -> dict[str, Any]:
    sql_dir = resolve_project_sql_dir(project_dir)
    if sql_dir.is_symlink():
        return {
            "status": "disabled",
            "reason": "sql_dir_symlink",
            "project_dir": str(project_dir),
            "sql_dir": str(sql_dir),
            "consistent": False,
            "issues": [],
        }
    if not sql_dir.is_dir():
        return {
            "status": "disabled",
            "reason": "sql_dir_missing",
            "project_dir": str(project_dir),
            "sql_dir": str(sql_dir),
            "consistent": False,
            "issues": [],
        }
    if (sql_dir / ".index").is_symlink():
        return {
            "status": "disabled",
            "reason": "index_dir_symlink",
            "project_dir": str(project_dir),
            "sql_dir": str(sql_dir),
            "index_dir": str(sql_dir / ".index"),
            "consistent": False,
            "issues": [],
        }
    if index_file_symlink(sql_dir / ".index") is not None:
        return {
            "status": "disabled",
            "reason": "index_file_symlink",
            "project_dir": str(project_dir),
            "sql_dir": str(sql_dir),
            "index_dir": str(sql_dir / ".index"),
            "consistent": False,
            "issues": [],
        }

    index_dir = sql_dir / ".index"
    required = {
        "file_digests": index_dir / "file-digests.json",
        "context_index": index_dir / "context-index.json",
        "table_index": index_dir / "table-index.json",
    }
    issues: list[dict[str, Any]] = []
    loaded: dict[str, dict[str, Any]] = {}
    for name, path in required.items():
        data = load_json(path)
        if data is None:
            issues.append({"type": "missing_or_invalid_index", "file": path.name})
        else:
            loaded[name] = data

    current = build_project_context(project_dir)
    if "file_digests" in loaded:
        indexed_files = loaded["file_digests"].get("files", {})
        current_files = current["file_digests"]["files"]
        if indexed_files != current_files:
            indexed_set = set(indexed_files)
            current_set = set(current_files)
            for rel_path in sorted(current_set - indexed_set):
                issues.append({"type": "unindexed_file", "file": rel_path})
            for rel_path in sorted(indexed_set - current_set):
                issues.append({"type": "deleted_file", "file": rel_path})
            for rel_path in sorted(indexed_set & current_set):
                if indexed_files[rel_path] != current_files[rel_path]:
                    issues.append({"type": "changed_file", "file": rel_path})

    return {
        "status": "valid" if not issues else "stale",
        "project_dir": str(project_dir),
        "sql_dir": str(sql_dir),
        "consistent": not issues,
        "issues_count": len(issues),
        "issues": issues,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build or validate project ./sql context indexes")
    parser.add_argument("--project-dir", type=Path, default=Path.cwd())
    parser.add_argument("--rebuild", action="store_true", help="Rebuild ./sql/.index")
    parser.add_argument("--validate", action="store_true", help="Validate existing ./sql/.index")
    args = parser.parse_args()

    project_dir = args.project_dir.expanduser().resolve()
    if args.validate:
        result = validate(project_dir)
    else:
        result = rebuild(project_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
