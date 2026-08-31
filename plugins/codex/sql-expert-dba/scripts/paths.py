#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping


ENTRY_TYPES = ("rules", "cases", "templates", "glossary")


def resolve_plugin_dir() -> Path:
    """Return the sql-expert-dba plugin root."""
    return Path(__file__).resolve().parent.parent


# 真源位置与重装不丢说明：
#   Codex 版落点：~/.codex/memories/sql-expert-dba/（或 CODEX_HOME/memories/sql-expert-dba/）
#   Claude 版落点：~/.claude/plugins/data/sql-expert-dba/memory/
#   两版落点均与插件源码物理分离——插件重装/升级不影响已沉淀记忆。
#   可用 SQL_EXPERT_DBA_MEMORY_DIR 环境变量覆盖（优先级最高）。
def resolve_user_memory_dir(
    env: Mapping[str, str] | None = None,
    home: Path | None = None,
) -> Path:
    """Resolve the portable user-level SQL Expert DBA memory directory."""
    current_env = os.environ if env is None else env

    custom_memory_dir = current_env.get("SQL_EXPERT_DBA_MEMORY_DIR")
    if custom_memory_dir:
        return Path(custom_memory_dir).expanduser()

    codex_home = current_env.get("CODEX_HOME")
    if codex_home:
        return Path(codex_home).expanduser() / "memories" / "sql-expert-dba"

    user_home = Path.home() if home is None else Path(home).expanduser()
    return user_home / ".codex" / "memories" / "sql-expert-dba"


def resolve_project_sql_dir(cwd: str | Path | None = None) -> Path:
    """Resolve the current project's ./sql directory."""
    project_root = Path.cwd() if cwd is None else Path(cwd)
    return project_root / "sql"


def resolve_biz_rules_dir(cwd: str | Path | None = None) -> Path:
    """Resolve the current project's ./sql/biz-rules directory."""
    return resolve_project_sql_dir(cwd) / "biz-rules"


def ensure_global_memory_dirs(memory_dir: Path) -> None:
    """Create the v2 global memory directory layout if it is missing."""
    memory_root = Path(memory_dir).expanduser()
    memory_root.mkdir(parents=True, exist_ok=True)

    for status in ("approved", "candidates"):
        for entry_type in ENTRY_TYPES:
            (memory_root / status / entry_type).mkdir(parents=True, exist_ok=True)

    index_path = memory_root / "index.json"
    if not index_path.exists():
        index = {
            "version": 2,
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "entries": [],
        }
        index_path.write_text(
            json.dumps(index, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    log_path = memory_root / "capture-log.jsonl"
    if not log_path.exists():
        log_path.write_text("", encoding="utf-8")
