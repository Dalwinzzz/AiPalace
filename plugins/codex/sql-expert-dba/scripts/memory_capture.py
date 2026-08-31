#!/usr/bin/env python3
"""
Capture and persist memory entries with value judgment, dedup, and routing.

Usage:
    python3 memory_capture.py --memory-dir ../memory \\
        --title "隐式类型转换陷阱" \\
        --type rule \\
        --workflow sql-query-optimizer \\
        --dialect mysql \\
        --tags "index,type-conversion" \\
        --problem-pattern "VARCHAR字段与数字比较导致索引失效" \\
        --conclusion "确保WHERE条件参数类型与字段类型一致" \\
        --boundaries "仅影响字符串字段比数字场景" \\
        --confidence high \\
        --origin-skill sql-query-optimizer \\
        --capture-mode auto_background
"""

import argparse
import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _frontmatter import parse_frontmatter
from paths import ensure_global_memory_dirs, resolve_user_memory_dir
from sanitize import check as sanitize_check


# Types that go to their own named directory when approved
TYPE_DIR_MAP = {
    "rule": "rules",
    "case": "cases",
    "template": "templates",
    "glossary": "glossary",
}

# Conditions for auto-approved status
AUTO_APPROVED_PATTERNS = {
    "high-universal-rule",
    "stable-error-pattern",
    "high-reuse-template",
    "cross-dialect-rule",
    "general-optimization-rule",
}

AUTO_CAPTURE_MODES = {"auto_hook", "auto_automation"}


def generate_id(entry_type: str) -> str:
    """Generate a unique ID: {type}-{timestamp_hash}."""
    ts = str(time.time()).encode()
    short_hash = hashlib.md5(ts).hexdigest()[:6]
    return f"{entry_type}-{short_hash}"


def slugify(title: str, max_len: int = 40) -> str:
    """Create a filesystem-safe slug from title."""
    slug = title.lower().strip()
    # Replace common separators
    for ch in " /\\:：，。、？！()（）[]【】":
        slug = slug.replace(ch, "-")
    # Remove consecutive dashes
    while "--" in slug:
        slug = slug.replace("--", "-")
    slug = slug.strip("-")
    # Truncate
    if len(slug) > max_len:
        slug = slug[:max_len].rstrip("-")
    return slug or "untitled"


def _bigrams(text: str) -> set[str]:
    """Extract character bigrams from text (CJK-aware, zero dependencies)."""
    normalized = text.lower().strip()
    if len(normalized) < 2:
        return {normalized} if normalized else set()
    return {normalized[i:i + 2] for i in range(len(normalized) - 1)}


def _memory_markdown_files(memory_dir: Path) -> list[Path]:
    """Discover memory Markdown files across v1 and v2 layouts."""
    if not memory_dir.is_dir():
        return []
    files = []
    for filepath in sorted(memory_dir.rglob("*.md")):
        if filepath.name.lower() == "readme.md":
            continue
        rel_parts = filepath.relative_to(memory_dir).parts
        if any(part.startswith(".") for part in rel_parts):
            continue
        files.append(filepath)
    return files


def check_duplicate(memory_dir: Path, problem_pattern: str, entry_type: str) -> bool:
    """Check for existing entries with highly similar problem_pattern.

    Returns True if a potential duplicate is found.
    Uses character bigram similarity — works for both CJK and Latin text.
    """
    if not problem_pattern:
        return False

    target_bg = _bigrams(problem_pattern)
    if not target_bg:
        return False

    for f in _memory_markdown_files(memory_dir):
        fm = parse_frontmatter(f)
        if not fm:
            continue
        existing_pattern = str(fm.get("problem_pattern", ""))
        existing_bg = _bigrams(existing_pattern)
        if not existing_bg:
            continue
        overlap = len(target_bg & existing_bg)
        similarity = overlap / max(len(target_bg), len(existing_bg))
        if similarity > 0.7:
            return True
    return False


def contains_forbidden_tokens(args: argparse.Namespace) -> bool:
    """Return True if a forbidden token appears in persisted memory fields."""
    tokens = [token.lower() for token in (args.forbidden_token or []) if token]
    if not tokens:
        return False

    text = " ".join(
        str(value or "")
        for value in (
            args.title,
            args.type,
            args.workflow,
            args.dialect,
            args.tags,
            args.problem_pattern,
            args.preconditions,
            args.conclusion,
            args.boundaries,
            args.example,
            args.anti_example,
            args.confidence,
            args.origin_skill,
            args.capture_mode,
        )
    ).lower()
    return any(token in text for token in tokens)


def determine_status(
    entry_type: str,
    confidence: str,
    capture_mode: str,
    force_approved: bool,
    promotion_reason: str | None = None,
    capture_mode_explicit: bool = True,
    approved_validation_passed: bool = False,
) -> str:
    """Determine whether entry goes to approved or candidate.

    Per spec §9.5, auto-approval requires an explicit promotion reason
    from the allowed set. High confidence alone is not sufficient.
    """
    if capture_mode in AUTO_CAPTURE_MODES:
        return "candidate"

    if capture_mode == "auto_background" and capture_mode_explicit:
        return "candidate"

    if capture_mode == "explicit_user_requested":
        if confidence in ("medium", "high") and approved_validation_passed:
            return "approved"
        return "candidate"

    if force_approved and approved_validation_passed:
        return "approved"

    if (
        promotion_reason
        and promotion_reason in AUTO_APPROVED_PATTERNS
        and approved_validation_passed
    ):
        return "approved"

    # Everything else starts as candidate
    return "candidate"


def determine_directory(memory_dir: Path, entry_type: str, status: str) -> Path:
    """Determine the target directory for the entry."""
    status_dir = "approved" if status == "approved" else "candidates"
    dir_name = TYPE_DIR_MAP.get(entry_type, "cases")
    return memory_dir / status_dir / dir_name


def approved_validation_passed(args: argparse.Namespace) -> bool:
    """Approved entries need a reusable problem, conclusion, and scope boundary."""
    return all(
        str(getattr(args, field, "") or "").strip()
        for field in ("problem_pattern", "conclusion", "boundaries")
    )


def normalize_frontmatter_scalar(value: object) -> str:
    """Normalize scalar metadata so the local front matter parser reads it safely."""
    text = "" if value is None else str(value)
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\n", "\\n")
    text = text.replace('"', '\\"')
    return text


def normalize_tag_scalar(value: object) -> str:
    """Normalize one tag for front matter arrays and index metadata."""
    text = "" if value is None else str(value)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return " ".join(text.split())


def parse_tags(tags: str | None) -> list[str]:
    """Split comma-separated tags and normalize each scalar value."""
    if not tags:
        return []
    return [tag for tag in (normalize_tag_scalar(part) for part in tags.split(",")) if tag]


def quote_frontmatter_scalar(value: object) -> str:
    """Quote a scalar value for the YAML-like subset used by memory files."""
    return f'"{normalize_frontmatter_scalar(value)}"'


def build_frontmatter(args: argparse.Namespace, entry_id: str, status: str) -> str:
    """Build YAML front matter string."""
    tags_str = f"[{', '.join(parse_tags(args.tags))}]" if args.tags else "[]"
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    return f"""---
id: {quote_frontmatter_scalar(entry_id)}
title: {quote_frontmatter_scalar(args.title)}
type: {quote_frontmatter_scalar(args.type)}
workflow: {quote_frontmatter_scalar(args.workflow or 'unknown')}
dialect: {quote_frontmatter_scalar(args.dialect or 'universal')}
tags: {tags_str}
problem_pattern: {quote_frontmatter_scalar(args.problem_pattern)}
preconditions: {quote_frontmatter_scalar(args.preconditions)}
conclusion: {quote_frontmatter_scalar(args.conclusion)}
boundaries: {quote_frontmatter_scalar(args.boundaries)}
example: {quote_frontmatter_scalar(args.example)}
anti_example: {quote_frontmatter_scalar(args.anti_example)}
confidence: {quote_frontmatter_scalar(args.confidence)}
review_status: {quote_frontmatter_scalar(status)}
last_reviewed_at: {quote_frontmatter_scalar(now)}
origin_skill: {quote_frontmatter_scalar(args.origin_skill or 'unknown')}
capture_mode: {quote_frontmatter_scalar(args.capture_mode)}
---"""


def build_index_entry(filepath: Path, fm: dict, memory_dir: Path) -> dict:
    """Build an index entry from parsed front matter."""
    entry = {
        "id": fm.get("id", ""),
        "title": fm.get("title", ""),
        "type": fm.get("type", ""),
        "workflow": fm.get("workflow", ""),
        "dialect": fm.get("dialect", ""),
        "tags": fm.get("tags", []),
        "review_status": fm.get("review_status", ""),
        "problem_pattern": fm.get("problem_pattern", ""),
        "conclusion": fm.get("conclusion", ""),
        "file": str(filepath.relative_to(memory_dir)),
    }
    return entry


def rebuild_index_entries(memory_dir: Path) -> list[dict]:
    """Rebuild index entries from Markdown files on disk."""
    entries = []
    for filepath in _memory_markdown_files(memory_dir):
        fm = parse_frontmatter(filepath)
        if fm and fm.get("id"):
            entries.append(build_index_entry(filepath, fm, memory_dir))
    return entries


def update_index(memory_dir: Path, entry: dict):
    """Add entry to index.json."""
    index_path = memory_dir / "index.json"
    entries = [
        item for item in rebuild_index_entries(memory_dir)
        if item.get("file") != entry.get("file")
    ]
    entries.append(entry)
    data = {"version": 2, "entries": entries}
    data["last_updated"] = datetime.now(timezone.utc).isoformat()

    index_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main():
    parser = argparse.ArgumentParser(
        description="Capture and persist SQL Expert DBA memory entries"
    )
    parser.add_argument("--memory-dir", type=Path, help="User-level global memory directory")
    parser.add_argument("--title", required=True, help="Memory entry title")
    parser.add_argument(
        "--type", required=True,
        choices=["rule", "case", "template", "glossary"],
        help="Entry type"
    )
    parser.add_argument("--workflow", help="Source workflow name")
    parser.add_argument("--dialect", help="SQL dialect")
    parser.add_argument("--tags", help="Comma-separated tags")
    parser.add_argument("--problem-pattern", help="Problem pattern description")
    parser.add_argument("--preconditions", help="Preconditions for the problem")
    parser.add_argument("--conclusion", help="Conclusion/recommendation")
    parser.add_argument("--boundaries", help="Applicability boundaries")
    parser.add_argument("--example", help="Positive example")
    parser.add_argument("--anti-example", help="Negative example")
    parser.add_argument(
        "--confidence", default="medium",
        choices=["low", "medium", "high"],
        help="Confidence level (default: medium)"
    )
    parser.add_argument("--origin-skill", help="Originating skill name")
    parser.add_argument(
        "--capture-mode", default="auto_background",
        choices=["explicit_user_requested", "auto_hook", "auto_automation", "auto_background"],
        help="Capture mode"
    )
    parser.add_argument(
        "--forbidden-token", action="append",
        help="Token that must not appear in sanitized global memory"
    )
    parser.add_argument(
        "--allow-token", action="append",
        help="Token to allow despite matching a sensitive pattern (false-positive bypass)"
    )
    parser.add_argument(
        "--force-approved", action="store_true",
        help="Force entry directly to approved status"
    )
    parser.add_argument(
        "--promotion-reason",
        choices=sorted(AUTO_APPROVED_PATTERNS),
        help="Reason for auto-promotion to approved (must be from allowed set)"
    )

    args = parser.parse_args()
    capture_mode_explicit = any(
        arg == "--capture-mode" or arg.startswith("--capture-mode=")
        for arg in sys.argv[1:]
    )

    if args.memory_dir is None:
        args.memory_dir = resolve_user_memory_dir()
    args.memory_dir = args.memory_dir.expanduser()
    ensure_global_memory_dirs(args.memory_dir)

    _scan_text = " ".join(
        str(value or "")
        for value in (
            args.title,
            args.type,
            args.workflow,
            args.dialect,
            args.tags,
            args.problem_pattern,
            args.preconditions,
            args.conclusion,
            args.boundaries,
            args.example,
            args.anti_example,
            args.confidence,
            args.origin_skill,
            args.capture_mode,
        )
    )
    _sanitize_result = sanitize_check(
        _scan_text,
        forbidden_tokens=args.forbidden_token or [],
        allow_tokens=getattr(args, "allow_token", None) or [],
        biz_rules=False,
    )
    if not _sanitize_result.ok:
        print(json.dumps({
            "status": "skipped",
            "reason": "unsanitized_global_memory",
            "title": args.title,
            "detail": _sanitize_result.message,
        }, ensure_ascii=False, indent=2))
        return

    # Dedup check
    if check_duplicate(args.memory_dir, args.problem_pattern or "", args.type):
        result = {
            "status": "skipped",
            "reason": "duplicate_detected",
            "title": args.title,
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    # Generate ID and determine routing
    entry_id = generate_id(args.type)
    status = determine_status(
        args.type,
        args.confidence,
        args.capture_mode,
        args.force_approved,
        args.promotion_reason,
        capture_mode_explicit,
        approved_validation_passed(args),
    )
    target_dir = determine_directory(args.memory_dir, args.type, status)
    target_dir.mkdir(parents=True, exist_ok=True)

    # Build file content
    frontmatter = build_frontmatter(args, entry_id, status)
    slug = slugify(args.title)
    filename = f"{args.type}-{entry_id.split('-')[1]}-{slug}.md"
    filepath = target_dir / filename

    body = f"\n\n# {args.title}\n\n{args.conclusion or ''}\n"
    filepath.write_text(frontmatter + body, encoding="utf-8")

    # Build index entry
    tags_list = parse_tags(args.tags)
    index_entry = {
        "id": entry_id,
        "title": normalize_frontmatter_scalar(args.title),
        "type": normalize_frontmatter_scalar(args.type),
        "workflow": normalize_frontmatter_scalar(args.workflow or "unknown"),
        "dialect": normalize_frontmatter_scalar(args.dialect or "universal"),
        "tags": tags_list,
        "review_status": status,
        "problem_pattern": normalize_frontmatter_scalar(args.problem_pattern),
        "conclusion": normalize_frontmatter_scalar(args.conclusion),
        "file": str(filepath.relative_to(args.memory_dir)),
    }
    update_index(args.memory_dir, index_entry)

    result = {
        "status": "captured",
        "review_status": status,
        "id": entry_id,
        "file": str(filepath.relative_to(args.memory_dir)),
        "title": args.title,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
