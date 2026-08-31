#!/usr/bin/env python3
"""
Lightweight YAML front matter parser for memory files.

Zero external dependencies — parses the subset of YAML used by
SQL Expert DBA memory entries (strings, arrays, basic types).
"""

from pathlib import Path
from typing import Any


def parse_frontmatter(filepath: Path) -> dict[str, Any]:
    """Parse YAML front matter between --- delimiters.

    Supports:
    - String values (bare and quoted)
    - Array values in [a, b, c] format
    - Basic types: null, true/false, integers, floats
    - Multi-line quoted strings with \\n escapes

    Returns empty dict if no valid front matter found.
    """
    text = filepath.read_text(encoding="utf-8")
    lines = text.split("\n")

    # Find front matter boundaries
    if not lines or lines[0].strip() != "---":
        return {}

    end_idx = -1
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end_idx = i
            break

    if end_idx < 0:
        return {}

    fm_lines = lines[1:end_idx]
    return _parse_yaml_lines(fm_lines)


def _parse_yaml_lines(lines: list[str]) -> dict[str, Any]:
    """Parse simple YAML key-value lines."""
    result: dict[str, Any] = {}

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        colon_idx = stripped.find(":")
        if colon_idx < 0:
            continue

        key = stripped[:colon_idx].strip()
        raw_value = stripped[colon_idx + 1:].strip()

        result[key] = _parse_value(raw_value)

    return result


def _parse_value(raw: str) -> Any:
    """Parse a YAML value string into a Python object."""
    if not raw or raw == "~" or raw.lower() == "null":
        return None

    # Boolean
    if raw.lower() in ("true", "yes"):
        return True
    if raw.lower() in ("false", "no"):
        return False

    # Array: [item1, item2, ...]
    if raw.startswith("[") and raw.endswith("]"):
        inner = raw[1:-1].strip()
        if not inner:
            return []
        items = []
        for item in inner.split(","):
            items.append(_parse_scalar(item.strip()))
        return items

    return _parse_scalar(raw)


def _parse_scalar(raw: str) -> str | int | float:
    """Parse a scalar value — try int, float, then fall back to string."""
    # Remove surrounding quotes
    if len(raw) >= 2:
        if (raw[0] == '"' and raw[-1] == '"') or (raw[0] == "'" and raw[-1] == "'"):
            return raw[1:-1]

    # Try integer
    try:
        return int(raw)
    except ValueError:
        pass

    # Try float
    try:
        return float(raw)
    except ValueError:
        pass

    return raw


def get_body(filepath: Path) -> str:
    """Return the Markdown body after front matter."""
    text = filepath.read_text(encoding="utf-8")
    lines = text.split("\n")

    if not lines or lines[0].strip() != "---":
        return text

    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return "\n".join(lines[i + 1:]).strip()

    return text
