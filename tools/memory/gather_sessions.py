#!/usr/bin/env python3
"""gather_sessions.py — M5-B sweep 纯读取器(无 LLM、无 subprocess)。

扫 claude/codex 历史会话 jsonl 里近 N 天、未入 ledger 的文件,导出 user 发言 blob 到
stdout,供**在场 agent** 抽候选(抽取不在本脚本内——脚本只读)。
ledger(.sweep-ledger.json)是机器本地状态,gitignore,Mac/Windows 各自独立。

用法:
  python3 tools/memory/gather_sessions.py                  # 预览 blob(不记账)
  python3 tools/memory/gather_sessions.py --commit-ledger  # 导出并记账(下次跳过)
  python3 tools/memory/gather_sessions.py --days 14        # 覆盖扫描天数
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core import HERE, load_config  # noqa: E402

LEDGER = HERE / ".sweep-ledger.json"


def walk_user_text(obj: object) -> list[str]:
    """从任意嵌套 json 捞 role=user 文本(兼容 claude/codex 多种 transcript schema)。"""
    found: list[str] = []

    def content_to_text(content: object) -> str:
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts = []
            for b in content:
                if isinstance(b, dict) and b.get("type") in (None, "text", "input_text") \
                        and isinstance(b.get("text"), str):
                    parts.append(b["text"])
                elif isinstance(b, str):
                    parts.append(b)
            return "\n".join(parts)
        return ""

    def walk(o: object) -> None:
        if isinstance(o, dict):
            if (o.get("role") or o.get("type")) == "user" and "content" in o:
                t = content_to_text(o["content"])
                if t.strip():
                    found.append(t.strip())
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)

    walk(obj)
    return found


def recent_files(roots: list[Path], pattern: str, days: int, limit: int,
                 now: float | None = None) -> list[Path]:
    cutoff = (now or time.time()) - days * 86400
    cands: list[tuple[float, Path]] = []
    for root in roots:
        if not root.exists():
            continue
        for fp in root.rglob(pattern):
            try:
                mt = fp.stat().st_mtime
            except OSError:
                continue
            if mt >= cutoff:
                cands.append((mt, fp))
    cands.sort(reverse=True)
    return [fp for _, fp in cands[:limit]]


def load_ledger(path: Path) -> dict:
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict) and isinstance(data.get("swept"), dict):
                return data
        except json.JSONDecodeError:
            pass
    return {"swept": {}}


def save_ledger(path: Path, ledger: dict) -> None:
    path.write_text(json.dumps(ledger, ensure_ascii=False, indent=1), encoding="utf-8")


def _extract(fp: Path, max_turns: int) -> list[str]:
    out: list[str] = []
    try:
        for line in fp.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            for t in walk_user_text(obj):
                out.append(t[:2000])
                if len(out) >= max_turns:
                    return out
    except OSError:
        pass
    return out


def gather(cfg: dict, days: int | None, commit_ledger: bool,
           ledger_path: Path | None = None, now: float | None = None) -> str:
    sw = cfg["sweep"]
    days = days if days is not None else sw["days"]
    lpath = ledger_path or LEDGER
    ledger = load_ledger(lpath)
    sources = [("claude", [Path(sw["claude_projects"]).expanduser()], "*.jsonl"),
               ("codex", [Path(p).expanduser() for p in sw["codex_sessions"]], "rollout-*.jsonl")]
    chunks: list[str] = []
    for name, roots, pattern in sources:
        for fp in recent_files(roots, pattern, days, sw["max_files"], now=now):
            key = str(fp)
            if key in ledger["swept"]:
                continue
            texts = _extract(fp, sw["max_user_turns_per_file"])
            if texts:
                chunks.append(f"=== [{name} {fp.stem}] ===\n" + "\n".join(texts))
                ledger["swept"][key] = time.strftime("%Y-%m-%dT%H:%M:%S")
    if commit_ledger:
        save_ledger(lpath, ledger)
    return "\n\n".join(chunks)


def main() -> int:
    ap = argparse.ArgumentParser(description="sweep 漏网会话读取器(纯读)")
    ap.add_argument("--days", type=int, default=None)
    ap.add_argument("--commit-ledger", action="store_true", help="导出并记账(下次跳过)")
    args = ap.parse_args()
    blob = gather(load_config(), args.days, args.commit_ledger)
    if not blob:
        print("[sweep] 没有新的漏网会话。")
        return 0
    print(blob)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
