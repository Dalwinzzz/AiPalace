#!/usr/bin/env python3
"""InstructionsLoaded 审计探针（临时诊断工具，非常驻机制）。

把每次指令文件加载事件追加成一行 JSONL，用来回答"到底什么被注入了、为什么被注入"。
只记元信息 + 内容长度，不落 file_content 全文（避免日志里堆一份指令副本）。

用法：临时注册进 ~/.claude/settings.json 的 InstructionsLoaded（matcher: ""），
跑完实测即摘除。日志路径由 AIPALACE_AUDIT_LOG 指定，默认 /tmp/instructions-audit.jsonl。
"""
import json
import os
import sys
from datetime import datetime

LOG = os.environ.get("AIPALACE_AUDIT_LOG", "/tmp/instructions-audit.jsonl")


def main() -> None:
    try:
        data = json.loads(sys.stdin.read() or "{}")
    except (json.JSONDecodeError, ValueError):
        data = {}

    content = data.get("file_content") or ""
    record = {
        "ts": datetime.now().isoformat(timespec="seconds"),
        "session": (data.get("session_id") or "")[:8],
        "reason": data.get("load_reason"),
        "cwd": data.get("cwd"),
        "file": data.get("file_path"),
        "chars": len(content),
        "memory_type": data.get("memory_type"),
        "globs": data.get("globs"),
        "trigger": data.get("trigger_file_path"),
    }
    try:
        with open(LOG, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    except OSError:
        pass


if __name__ == "__main__":
    main()
