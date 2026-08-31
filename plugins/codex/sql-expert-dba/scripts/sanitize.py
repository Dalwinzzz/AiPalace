#!/usr/bin/env python3
"""
Sensitive-pattern scanner for SQL Expert DBA global memory entries.

Scope:
  - Applied to global memory (candidates + approved).
  - NOT applied to biz-rules/ (real table names are allowed there).

Usage (programmatic):
    from sanitize import check, CheckResult
    result = check(text, forbidden_tokens=["real_table"], allow_tokens=["13800000000"])
    if not result.ok:
        raise ValueError(result.message)

CLI usage (for manual testing):
    python3 sanitize.py --text "some text" [--forbidden-token tok] [--allow-token tok]
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass


# Built-in sensitive patterns (global memory only)
_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("phone", re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)")),
    ("email", re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")),
    ("id_card", re.compile(r"(?<!\d)\d{17}[\dXx](?!\d)")),
    ("ip", re.compile(r"(?<!\d)(?:\d{1,3}\.){3}\d{1,3}(?!\d)")),
]


@dataclass
class CheckResult:
    ok: bool
    pattern: str = ""
    matched: str = ""
    message: str = ""


def check(
    text: str,
    *,
    forbidden_tokens: list[str] | None = None,
    allow_tokens: list[str] | None = None,
    biz_rules: bool = False,
) -> CheckResult:
    """Scan text for sensitive patterns.

    Args:
        text: Content to scan.
        forbidden_tokens: Additional tokens that must not appear.
        allow_tokens: Tokens to explicitly allow (false-positive bypass).
        biz_rules: If True, skip built-in pattern scan (biz-rules scope).

    Returns:
        CheckResult with ok=True if text is clean.
    """
    allow_set = {t.lower() for t in (allow_tokens or [])}

    if not biz_rules:
        for pattern_name, regex in _PATTERNS:
            match = regex.search(text)
            if match:
                matched = match.group(0)
                if matched.lower() in allow_set:
                    continue
                return CheckResult(
                    ok=False,
                    pattern=pattern_name,
                    matched=matched,
                    message=(
                        f"Sensitive pattern '{pattern_name}' detected: {matched!r}. "
                        f"Remove the sensitive content or use --allow-token to bypass."
                    ),
                )

    for token in (forbidden_tokens or []):
        if not token:
            continue
        if token.lower() in allow_set:
            continue
        if token.lower() in text.lower():
            return CheckResult(
                ok=False,
                pattern="forbidden_token",
                matched=token,
                message=(
                    f"Forbidden token {token!r} found in text. "
                    f"Remove or use --allow-token to bypass."
                ),
            )

    return CheckResult(ok=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Sanitize check for memory entry text")
    parser.add_argument("--text", required=True, help="Text to scan")
    parser.add_argument("--forbidden-token", action="append", dest="forbidden_tokens",
                        help="Additional forbidden token (repeatable)")
    parser.add_argument("--allow-token", action="append", dest="allow_tokens",
                        help="Token to allow despite matching a pattern (repeatable)")
    parser.add_argument("--biz-rules", action="store_true",
                        help="Skip built-in pattern scan (biz-rules scope)")
    args = parser.parse_args()

    result = check(
        args.text,
        forbidden_tokens=args.forbidden_tokens,
        allow_tokens=args.allow_tokens,
        biz_rules=args.biz_rules,
    )
    if result.ok:
        print("OK: text is clean")
    else:
        print(f"BLOCKED: {result.message}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
