#!/usr/bin/env python3
"""
Cross-version zero-diff validator for sql-expert-dba shared layer.

Validates:
1. Fully-shared files are byte-identical between Codex and Claude versions.
2. Both versions' _shared/ directories have the same file name set.
3. No unsharded tool-variant patterns remain in shared-layer files.

Usage:
    python3 check_dual_sync.py [--codex-root PATH] [--claude-root PATH]

Defaults:
    Codex root:  ~/.agents/plugins/sql-expert-dba
    Claude root: ~/Library/CodeRepo/AI/claude-plugins/sql-expert-dba
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

CODEX_DEFAULT = Path("~/.agents/plugins/sql-expert-dba").expanduser()
CLAUDE_DEFAULT = Path("~/Library/CodeRepo/AI/claude-plugins/sql-expert-dba").expanduser()

# Files that must be byte-identical between both versions
SHARED_LAYER_FILES: list[str] = [
    "skills/_shared/memory-policy.md",
    "skills/_shared/output-contract.md",
    "skills/_shared/dialect-guidelines.md",
    "skills/_shared/missing-input-checklists.md",
    "skills/sql-expert-router/SKILL.md",
    "skills/sql-query-optimizer/SKILL.md",
    "skills/sql-error-diagnostician/SKILL.md",
    "skills/sql-schema-reviewer/SKILL.md",
    "skills/sql-report-query-builder/SKILL.md",
    "scripts/memory_capture.py",
    "scripts/memory_search.py",
    "scripts/memory_promote.py",
    "scripts/sanitize.py",
    "scripts/paths.py",
    "scripts/_frontmatter.py",
]

# Patterns that must NOT appear in shared-layer files (indicate unsharded differences).
# Note: "~/.codex/memories" and "~/.claude/plugins/data" are intentionally omitted here
# because they appear in paths.py as legitimate shared fallback-path logic and documentation
# comments — both versions carry identical copies of these strings.
# Only variable-interpolation forms (e.g. "${CLAUDE_PLUGIN_ROOT}") signal true divergence.
FORBIDDEN_PATTERNS: list[str] = [
    "${CLAUDE_PLUGIN_ROOT}",
    "$CODEX_HOME",
]


def check_zero_diff(codex_root: Path, claude_root: Path) -> list[str]:
    errors: list[str] = []
    for rel_path in SHARED_LAYER_FILES:
        codex_file = codex_root / rel_path
        claude_file = claude_root / rel_path
        if not codex_file.exists():
            errors.append(f"MISSING in Codex: {rel_path}")
            continue
        if not claude_file.exists():
            errors.append(f"MISSING in Claude: {rel_path}")
            continue
        codex_text = codex_file.read_text(encoding="utf-8")
        claude_text = claude_file.read_text(encoding="utf-8")
        if codex_text != claude_text:
            errors.append(f"DIFF: {rel_path} — not byte-identical between versions")
    return errors


def check_shared_dir_parity(codex_root: Path, claude_root: Path) -> list[str]:
    errors: list[str] = []
    codex_shared = codex_root / "skills" / "_shared"
    claude_shared = claude_root / "skills" / "_shared"
    codex_files = {f.name for f in codex_shared.glob("*.md")} if codex_shared.is_dir() else set()
    claude_files = {f.name for f in claude_shared.glob("*.md")} if claude_shared.is_dir() else set()
    only_codex = codex_files - claude_files
    only_claude = claude_files - codex_files
    if only_codex:
        errors.append(f"_shared/ files only in Codex: {sorted(only_codex)}")
    if only_claude:
        errors.append(f"_shared/ files only in Claude: {sorted(only_claude)}")
    return errors


def check_no_unsharded_patterns(codex_root: Path) -> list[str]:
    errors: list[str] = []
    for rel_path in SHARED_LAYER_FILES:
        f = codex_root / rel_path
        if not f.exists():
            continue
        text = f.read_text(encoding="utf-8")
        for pattern in FORBIDDEN_PATTERNS:
            if pattern in text:
                errors.append(f"UNSHARDED PATTERN '{pattern}' in {rel_path}")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate dual-version zero-diff for sql-expert-dba"
    )
    parser.add_argument("--codex-root", type=Path, default=CODEX_DEFAULT)
    parser.add_argument("--claude-root", type=Path, default=CLAUDE_DEFAULT)
    args = parser.parse_args()

    all_errors: list[str] = []
    all_errors += check_zero_diff(args.codex_root, args.claude_root)
    all_errors += check_shared_dir_parity(args.codex_root, args.claude_root)
    all_errors += check_no_unsharded_patterns(args.codex_root)

    if all_errors:
        print("SYNC CHECK FAILED:")
        for err in all_errors:
            print(f"  ✗ {err}")
        sys.exit(1)
    else:
        print(f"SYNC CHECK PASSED — {len(SHARED_LAYER_FILES)} shared files verified.")


if __name__ == "__main__":
    main()
