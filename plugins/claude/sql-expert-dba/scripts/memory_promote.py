#!/usr/bin/env python3
"""
Promote a candidate memory entry to approved after field validation and sanitize check.

Usage:
    python3 memory_promote.py --list-candidates
    python3 memory_promote.py --id <memory-id> [--allow-token <tok>]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _frontmatter import parse_frontmatter
from paths import ensure_global_memory_dirs, resolve_user_memory_dir
from sanitize import check as sanitize_check

REQUIRED_FIELDS = ("id", "title", "type", "problem_pattern", "conclusion", "boundaries")


def _candidate_files(memory_dir: Path) -> list[Path]:
    candidates_root = memory_dir / "candidates"
    if not candidates_root.is_dir():
        return []
    return sorted(candidates_root.rglob("*.md"))


def find_candidate(memory_dir: Path, memory_id: str) -> Path | None:
    for f in _candidate_files(memory_dir):
        fm = parse_frontmatter(f)
        if fm and fm.get("id") == memory_id:
            return f
    return None


def list_candidates(memory_dir: Path) -> None:
    files = _candidate_files(memory_dir)
    if not files:
        print("No candidates found.")
        return
    print(f"{'ID':<20} {'Type':<12} {'Title'}")
    print("-" * 70)
    for f in files:
        fm = parse_frontmatter(f)
        if fm:
            print(f"{fm.get('id',''):<20} {fm.get('type',''):<12} {fm.get('title','')}")


def promote(memory_dir: Path, memory_id: str, allow_tokens: list[str]) -> None:
    candidate_path = find_candidate(memory_dir, memory_id)
    if candidate_path is None:
        print(f"Error: candidate with id '{memory_id}' not found in {memory_dir}/candidates/",
              file=sys.stderr)
        sys.exit(1)

    fm = parse_frontmatter(candidate_path)
    if fm is None:
        print(f"Error: could not parse frontmatter from {candidate_path}", file=sys.stderr)
        sys.exit(1)

    missing = [f for f in REQUIRED_FIELDS if not str(fm.get(f, "") or "").strip()]
    if missing:
        print(f"Error: missing required fields for promotion: {missing}", file=sys.stderr)
        sys.exit(1)

    scan_text = " ".join(str(fm.get(f, "") or "") for f in (
        "title", "type", "workflow", "dialect", "tags",
        "problem_pattern", "preconditions", "conclusion",
        "boundaries", "example", "anti_example",
    ))
    result = sanitize_check(scan_text, allow_tokens=allow_tokens, biz_rules=False)
    if not result.ok:
        print(f"Error: sanitize check failed — {result.message}", file=sys.stderr)
        sys.exit(1)

    rel = candidate_path.relative_to(memory_dir / "candidates")
    approved_path = memory_dir / "approved" / rel
    approved_path.parent.mkdir(parents=True, exist_ok=True)

    text = candidate_path.read_text(encoding="utf-8")
    text = text.replace('review_status: "candidate"', 'review_status: "approved"', 1)
    approved_path.write_text(text, encoding="utf-8")
    candidate_path.unlink()

    _update_index(memory_dir, memory_id, approved_path)

    result_data = {
        "status": "promoted",
        "id": memory_id,
        "review_status": "approved",
        "file": str(approved_path.relative_to(memory_dir)),
    }
    print(json.dumps(result_data, ensure_ascii=False, indent=2))


def _update_index(memory_dir: Path, memory_id: str, approved_path: Path) -> None:
    index_path = memory_dir / "index.json"
    if not index_path.exists():
        return
    data = json.loads(index_path.read_text(encoding="utf-8"))
    entries = data.get("entries", [])
    for entry in entries:
        if entry.get("id") == memory_id:
            entry["review_status"] = "approved"
            entry["file"] = str(approved_path.relative_to(memory_dir))
            break
    index_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                          encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Promote candidate memory entry to approved")
    parser.add_argument("--memory-dir", type=Path, help="User-level global memory directory")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--list-candidates", action="store_true",
                       help="List all candidate entries")
    group.add_argument("--id", help="Memory ID to promote")
    parser.add_argument("--allow-token", action="append", dest="allow_tokens",
                        help="Token to allow despite matching a sensitive pattern")
    args = parser.parse_args()

    if args.memory_dir is None:
        args.memory_dir = resolve_user_memory_dir()
    args.memory_dir = args.memory_dir.expanduser()
    ensure_global_memory_dirs(args.memory_dir)

    if args.list_candidates:
        list_candidates(args.memory_dir)
    else:
        promote(args.memory_dir, args.id, args.allow_tokens or [])


if __name__ == "__main__":
    main()
