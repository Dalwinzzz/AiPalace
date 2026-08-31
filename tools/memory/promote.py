#!/usr/bin/env python3
"""promote.py — 审批执行:把 candidates.md 勾成 [x] 的候选晋升到 dest。

只执行人勾选的;dest 白名单落盘前复验;UPDATE 也只追加标注不覆盖原文(安全优先);
写后行内标 ✅done 防重复晋升;DREAMS 留痕。**不做 git 操作**——提交由 /ai-palace 按纪律
只暂存具体文件(禁 add -A)。

用法:
  python3 tools/memory/promote.py            # 晋升所有 [x]
  python3 tools/memory/promote.py --dry-run  # 只看会做什么
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core import VAULT, load_config, validate_dest  # noqa: E402

CAND_LINE = re.compile(r"^- \[([ xX])\]\s+(.*?)\s*<!--cand\s+(\{.*?\})\s*-->\s*$")
UPDATED_RE = re.compile(r"^(updated:\s*).*$", re.MULTILINE)

_VALID_TYPES = {"identity", "preference", "principle", "decision", "feedback",
                 "project", "source", "map", "journal"}


def bump_updated(text: str, today: str) -> str:
    return UPDATED_RE.sub(rf"\g<1>{today}", text, count=1)


def _stamp(meta: dict, today: str) -> str:
    """条目行尾留痕。

    只留日期（判断新鲜度要用）与「待人工合并」这个待办信号。score/freq 是晋升过程的
    中间量、写出去从没人读回，属 vault 禁止的过程性描述（见 vault/CLAUDE.md 维护宪法），
    不再落盘——需要复盘打分去看 04-FEEDBACK/DREAMS.md。
    """
    tag = "·UPDATE 待人工合并" if meta.get("action") == "UPDATE" else ""
    return f"({today}{tag})"


def _clamp_type(raw_type: object) -> str:
    t = str(raw_type or "")
    if t in _VALID_TYPES:
        return t
    if t == "correction":
        return "feedback"
    return "project"


def _new_note(path: Path, stmt: str, meta: dict, today: str) -> str:
    title = path.stem
    return (f"---\ntitle: {title}\ntype: {_clamp_type(meta.get('type'))}\n"
            f"scope: {meta.get('scope', 'global')}\nstatus: active\n"
            f"confidence: {meta.get('conf', 'medium')}\ncreated: {today}\n"
            f"updated: {today}\nlast_confirmed: {today}\nsource: [ai-palace 晋升]\n---\n\n"
            f"# {title}\n\n## 蒸馏晋升\n\n- {stmt} {_stamp(meta, today)}\n")


def apply_one(vault: Path, stmt: str, meta: dict, cfg: dict, dry: bool) -> str:
    """落一条候选到 dest;返回结果描述(⚠️ 开头 = 跳过,不标 done)。"""
    dest = str(meta.get("dest", ""))
    reason = validate_dest(dest, cfg)
    if reason:
        return f"⚠️ 跳过({reason}):{dest}"
    today = datetime.now().date().isoformat()
    path = vault / dest
    if not path.exists():
        if dest in cfg["routing"]["rules_files"]:
            return f"⚠️ 跳过(00-RULES 文件缺失,不代建):{dest}"
        if not dry:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(_new_note(path, stmt, meta, today), encoding="utf-8")
        return f"新建 {dest}(记得给 INDEX 决策树接线)"
    # 00-RULES 只进文末暂存段,不动正文结构(spec D6/D8)
    section = "## 蒸馏晋升(待归位)" if dest in cfg["routing"]["rules_files"] else "## 蒸馏晋升"
    if not dry:
        text = path.read_text(encoding="utf-8")
        if section not in text:
            text = text.rstrip() + f"\n\n{section}\n"
        text = text.rstrip() + f"\n- {stmt} {_stamp(meta, today)}\n"
        path.write_text(bump_updated(text, today), encoding="utf-8")
    verb = "UPDATE(追加标注)" if meta.get("action") == "UPDATE" else "追加"
    return f"{verb} → {dest}"


def promote(dry: bool, vault: Path | None = None, cfg: dict | None = None) -> int:
    v = vault or VAULT
    cfg = cfg or load_config()
    candidates = v / "04-FEEDBACK" / "candidates.md"
    dreams = v / "04-FEEDBACK" / "DREAMS.md"
    src = candidates.read_text(encoding="utf-8")
    out_lines: list[str] = []
    results: list[str] = []
    promoted = 0
    for line in src.splitlines():
        m = CAND_LINE.match(line)
        if not m or m.group(1).lower() != "x":
            out_lines.append(line)
            continue
        stmt = m.group(2).strip()
        try:
            meta = json.loads(m.group(3))
        except json.JSONDecodeError:
            out_lines.append(line)
            results.append("?: ⚠️ 跳过(cand 元数据损坏)")
            continue
        if meta.get("action") in ("NOOP",):
            out_lines.append(line)
            results.append(f"{meta.get('id', '?')}: ⚠️ 跳过(action={meta.get('action')})")
            continue
        res = apply_one(v, stmt, meta, cfg, dry)
        results.append(f"{meta.get('id', '?')}: {res}")
        if res.startswith("⚠️") or dry:
            out_lines.append(line)
        else:
            out_lines.append(line.replace("<!--cand", "✅<!--done"))
            promoted += 1

    if not results:
        print("[promote] 没有勾选 [x] 的候选。先在 candidates.md 勾选,或让 /ai-palace 代勾。")
        return 0
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    log = (f"\n## {ts} · promote(人已审批){'(dry-run)' if dry else ''}\n"
           + "".join(f"- {r}\n" for r in results))
    print(log)
    if dry:
        print("[dry-run] 未写入。")
        return 0
    candidates.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
    prev = dreams.read_text(encoding="utf-8") if dreams.exists() else ""
    dreams.write_text(prev + log, encoding="utf-8")
    print(f"[promote] 完成:{promoted} 条晋升,{len(results) - promoted} 条跳过。")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="晋升已审批([x])的记忆候选")
    ap.add_argument("--dry-run", action="store_true", help="只看会做什么,不写")
    return promote(dry=ap.parse_args().dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
