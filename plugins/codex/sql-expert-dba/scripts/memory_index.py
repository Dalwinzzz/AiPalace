#!/usr/bin/env python3
"""
Build, rebuild, or validate the memory index (index.json).

Usage:
    python3 memory_index.py --memory-dir ../memory --rebuild
    python3 memory_index.py --memory-dir ../memory --validate
    python3 memory_index.py --memory-dir ../memory   # incremental update
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _frontmatter import parse_frontmatter


INDEX_FIELDS = ("id", "title", "type", "workflow", "dialect", "tags", "review_status", "problem_pattern", "conclusion")


def find_memory_files(memory_dir: Path) -> list[Path]:
    """Discover memory Markdown files across v1 seed and v2 global layouts."""
    files: list[Path] = []
    for filepath in sorted(memory_dir.rglob("*.md")):
        if filepath.name.lower() == "readme.md":
            continue
        rel_parts = filepath.relative_to(memory_dir).parts
        if any(part.startswith(".") for part in rel_parts):
            continue
        files.append(filepath)
    return files


def scan_memory_files(memory_dir: Path) -> list[tuple[Path, dict]]:
    """Scan all memory .md files and parse their front matter."""
    results = []
    for f in find_memory_files(memory_dir):
        fm = parse_frontmatter(f)
        if fm and fm.get("id"):
            results.append((f, fm))
    return results


def build_index_entry(filepath: Path, fm: dict, memory_dir: Path) -> dict:
    """Build an index entry from a file's front matter."""
    entry = {}
    for field in INDEX_FIELDS:
        entry[field] = fm.get(field, "")
    entry["file"] = str(filepath.relative_to(memory_dir))
    return entry


def load_index(memory_dir: Path) -> dict:
    """Load existing index.json or return empty structure."""
    index_path = memory_dir / "index.json"
    if index_path.exists():
        try:
            data = json.loads(index_path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
            return {
                "version": 2,
                "last_updated": "",
                "entries": [],
                "_invalid_index": "index root must be an object",
            }
        except (json.JSONDecodeError, OSError):
            pass
    return {"version": 2, "last_updated": "", "entries": []}


def save_index(memory_dir: Path, data: dict):
    """Write index.json."""
    data["last_updated"] = datetime.now(timezone.utc).isoformat()
    index_path = memory_dir / "index.json"
    index_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def rebuild(memory_dir: Path) -> dict:
    """Full rebuild of index from filesystem scan."""
    files = scan_memory_files(memory_dir)
    entries = [build_index_entry(fp, fm, memory_dir) for fp, fm in files]
    data = {"version": 2, "entries": entries}
    save_index(memory_dir, data)
    return data


def incremental_update(memory_dir: Path) -> dict:
    """Update index: add new files, remove deleted files."""
    data = load_index(memory_dir)
    data["version"] = 2
    if not isinstance(data.get("entries"), list):
        data["entries"] = []
    existing_entries = {
        e["file"]: e
        for e in data.get("entries", [])
        if isinstance(e, dict) and e.get("file")
    }

    scanned = scan_memory_files(memory_dir)
    scanned_files = set()

    added = 0
    updated = 0
    for fp, fm in scanned:
        rel = str(fp.relative_to(memory_dir))
        scanned_files.add(rel)
        entry = build_index_entry(fp, fm, memory_dir)
        if rel not in existing_entries:
            data["entries"].append(entry)
            added += 1
        elif existing_entries[rel] != entry:
            existing_entries[rel].update(entry)
            updated += 1

    before = len(data["entries"])
    data["entries"] = [
        e for e in data["entries"]
        if isinstance(e, dict) and e.get("file") in scanned_files
    ]
    removed = before - len(data["entries"])

    save_index(memory_dir, data)

    print(json.dumps({
        "action": "incremental_update",
        "added": added,
        "updated": updated,
        "removed": removed,
        "total": len(data["entries"]),
    }, ensure_ascii=False, indent=2))

    return data


def validate(memory_dir: Path) -> dict:
    """Validate index consistency against filesystem."""
    raw_data = load_index(memory_dir)
    data = raw_data if isinstance(raw_data, dict) else {"version": 2, "entries": []}
    scanned = scan_memory_files(memory_dir)
    scanned_map = {str(fp.relative_to(memory_dir)): fm for fp, fm in scanned}

    issues = []
    raw_entries = data.get("entries", [])
    entries = raw_entries if isinstance(raw_entries, list) else []
    if data.get("_invalid_index"):
        issues.append({
            "type": "invalid_index_structure",
            "message": data["_invalid_index"],
        })
    if not isinstance(raw_entries, list):
        issues.append({
            "type": "invalid_index_structure",
            "message": "index entries must be a list",
        })

    # Check for index entries without files
    for idx, entry in enumerate(entries):
        if not isinstance(entry, dict):
            issues.append({
                "type": "invalid_index_entry",
                "index": idx,
                "message": "Index entry must be an object",
            })
            continue
        filepath = entry.get("file", "")
        if not filepath:
            issues.append({
                "type": "invalid_index_entry",
                "id": entry.get("id"),
                "message": "Index entry is missing file",
            })
            continue
        if filepath not in scanned_map:
            issues.append({
                "type": "orphan_index_entry",
                "id": entry.get("id"),
                "file": filepath,
                "message": "Index entry has no corresponding file",
            })

    # Check for files without index entries
    indexed_files = {
        e["file"]
        for e in entries
        if isinstance(e, dict) and e.get("file")
    }
    for rel_path in scanned_map:
        if rel_path not in indexed_files:
            issues.append({
                "type": "unindexed_file",
                "file": rel_path,
                "message": "File exists but is not in index",
            })

    # Check for field mismatches
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        filepath = entry.get("file", "")
        if filepath in scanned_map:
            fm = scanned_map[filepath]
            for field in ("id", "title", "type", "workflow", "dialect", "problem_pattern", "conclusion", "tags", "review_status"):
                if str(entry.get(field, "")) != str(fm.get(field, "")):
                    issues.append({
                        "type": "field_mismatch",
                        "file": filepath,
                        "field": field,
                        "index_value": entry.get(field),
                        "file_value": fm.get(field),
                    })

    result = {
        "action": "validate",
        "total_indexed": len(entries),
        "total_files": len(scanned_map),
        "issues_count": len(issues),
        "issues": issues,
        "consistent": len(issues) == 0,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result


def main():
    parser = argparse.ArgumentParser(
        description="Build, rebuild, or validate memory index"
    )
    parser.add_argument("--memory-dir", required=True, type=Path)
    parser.add_argument(
        "--rebuild", action="store_true",
        help="Full rebuild of index from filesystem"
    )
    parser.add_argument(
        "--validate", action="store_true",
        help="Validate index consistency without modifying"
    )

    args = parser.parse_args()

    if not args.memory_dir.is_dir():
        print(json.dumps({"error": f"Memory directory not found: {args.memory_dir}"}))
        sys.exit(1)

    if args.rebuild:
        data = rebuild(args.memory_dir)
        print(json.dumps({
            "action": "rebuild",
            "total": len(data["entries"]),
            "entries": [e["id"] for e in data["entries"]],
        }, ensure_ascii=False, indent=2))
    elif args.validate:
        validate(args.memory_dir)
    else:
        incremental_update(args.memory_dir)


if __name__ == "__main__":
    main()
