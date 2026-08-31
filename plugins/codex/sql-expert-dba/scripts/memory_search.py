#!/usr/bin/env python3
"""
Search memory entries by workflow, dialect, tags, pattern, and status.

Usage:
    python3 memory_search.py --memory-dir ../memory --status all
    python3 memory_search.py --memory-dir ../memory --workflow sql-query-optimizer --tags index,performance
    python3 memory_search.py --memory-dir ../memory --pattern "索引" --dialect mysql
"""

import argparse
import json
import sys
from pathlib import Path

# Allow importing _frontmatter from same directory
sys.path.insert(0, str(Path(__file__).parent))
from _frontmatter import parse_frontmatter
from paths import resolve_plugin_dir, resolve_user_memory_dir


INDEX_ENTRY_REQUIRED_FIELDS = (
    "id",
    "file",
    "title",
    "workflow",
    "dialect",
    "review_status",
    "problem_pattern",
    "conclusion",
    "tags",
)

INDEX_ENTRY_STRING_FIELDS = (
    "title",
    "problem_pattern",
    "conclusion",
    "workflow",
    "dialect",
    "review_status",
)


def is_valid_index_entry(entry) -> bool:
    """Validate index entry structure before trusting it for filtering."""
    if not isinstance(entry, dict):
        return False
    if any(field not in entry for field in INDEX_ENTRY_REQUIRED_FIELDS):
        return False
    if not isinstance(entry["id"], str):
        return False
    if not isinstance(entry["tags"], list):
        return False
    if any(not isinstance(tag, str) for tag in entry["tags"]):
        return False
    if not isinstance(entry["file"], str):
        return False
    for field in INDEX_ENTRY_STRING_FIELDS:
        if field in entry and not isinstance(entry[field], str):
            return False
    return True


def find_memory_files(memory_dir: Path) -> list[Path]:
    """Discover all .md files across v1 seed and v2 global layouts."""
    if not memory_dir.is_dir():
        return []

    files = []
    for f in sorted(memory_dir.rglob("*.md")):
        if f.name.lower() == "readme.md":
            continue
        rel_parts = f.relative_to(memory_dir).parts
        if any(part.startswith(".") for part in rel_parts):
            continue
        files.append(f)
    return files


def matches_filter(entry: dict, args: argparse.Namespace) -> bool:
    """Check if a memory entry matches all active filters."""
    # Status filter
    status = entry.get("review_status", "candidate")
    if args.status != "all" and status != args.status:
        return False

    # Workflow filter
    if args.workflow and entry.get("workflow") != args.workflow:
        return False

    # Dialect filter
    if args.dialect:
        entry_dialect = entry.get("dialect", "")
        if entry_dialect != args.dialect and entry_dialect != "universal":
            return False

    # Tags filter (intersection — entry must contain ALL requested tags)
    if args.tags:
        requested = set(t.strip() for t in args.tags.split(","))
        entry_tags = set(entry.get("tags", []))
        if not requested.issubset(entry_tags):
            return False

    # Pattern filter (keyword search in problem_pattern, title, conclusion)
    if args.pattern:
        pattern = args.pattern.lower()
        searchable = " ".join(
            str(entry.get(f, ""))
            for f in ("title", "problem_pattern", "conclusion", "tags")
        ).lower()
        if pattern not in searchable:
            return False

    return True


def search_via_index(memory_dir: Path, args: argparse.Namespace) -> list[dict] | None:
    """Try fast search via index.json. Returns None if index unusable."""
    if not memory_dir.is_dir():
        return []

    index_path = memory_dir / "index.json"
    if not index_path.exists():
        return None

    try:
        data = json.loads(index_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None

    if not isinstance(data, dict):
        return None

    entries = data.get("entries", [])
    if not isinstance(entries, list):
        return None

    if not entries:
        return None  # Empty index — fall back to scan

    for entry in entries:
        if not is_valid_index_entry(entry):
            return None

    results = []
    for entry in entries:
        if matches_filter(entry, args):
            results.append(entry)

    return results


def search_via_scan(memory_dir: Path, args: argparse.Namespace) -> list[dict]:
    """Full scan of memory files, parsing front matter."""
    results = []
    for filepath in find_memory_files(memory_dir):
        entry = parse_frontmatter(filepath)
        if not entry:
            continue
        entry["_file"] = str(filepath.relative_to(memory_dir))
        if matches_filter(entry, args):
            results.append(entry)
    return results


def search_memory_dir(memory_dir: Path, args: argparse.Namespace) -> list[dict]:
    """Search one memory directory, preferring index and falling back to scan."""
    if not memory_dir.is_dir():
        return []

    results = search_via_index(memory_dir, args)
    if results is None:
        results = search_via_scan(memory_dir, args)
    return results


def merge_results(result_sets: list[list[dict]]) -> list[dict]:
    """Merge layered memory results, deduplicating by entry id."""
    merged: dict[str, dict] = {}
    for results in result_sets:
        for entry in results:
            entry_id = str(entry.get("id", ""))
            if not entry_id:
                continue
            merged.setdefault(entry_id, entry)
    return list(merged.values())


def main():
    parser = argparse.ArgumentParser(
        description="Search SQL Expert DBA memory entries"
    )
    parser.add_argument(
        "--memory-dir", type=Path,
        help="User-level global memory directory"
    )
    parser.add_argument(
        "--seed-memory-dir", type=Path,
        help="Plugin seed memory directory"
    )
    parser.add_argument(
        "--include-candidates", action="store_true",
        help="Include candidate entries"
    )
    parser.add_argument("--workflow", help="Filter by workflow name")
    parser.add_argument("--dialect", help="Filter by dialect (mysql/postgresql/universal)")
    parser.add_argument("--tags", help="Filter by tags (comma-separated, entry must match ALL)")
    parser.add_argument("--pattern", help="Keyword search in title/problem_pattern/conclusion")
    parser.add_argument(
        "--status", default="approved",
        choices=["approved", "candidate", "all"],
        help="Filter by review_status (default: approved)"
    )
    parser.add_argument("--limit", type=int, default=50, help="Max results (default: 50)")

    args = parser.parse_args()

    explicit_memory_dir = args.memory_dir is not None
    if args.memory_dir is None:
        args.memory_dir = resolve_user_memory_dir()
    if args.seed_memory_dir is None:
        args.seed_memory_dir = resolve_plugin_dir() / "memory"
    if args.include_candidates:
        args.status = "all"

    args.memory_dir = args.memory_dir.expanduser()
    args.seed_memory_dir = args.seed_memory_dir.expanduser()

    if explicit_memory_dir and not args.memory_dir.is_dir():
        print(json.dumps({"error": f"Memory directory not found: {args.memory_dir}"}))
        sys.exit(1)

    result_sets = [
        search_memory_dir(args.seed_memory_dir, args),
        search_memory_dir(args.memory_dir, args),
    ]
    results = merge_results(result_sets)

    # Apply limit
    results = results[: args.limit]

    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
