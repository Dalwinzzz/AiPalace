#!/usr/bin/env python3
"""core.py — AiPalace 手动飞轮蒸馏内核(确定性)。

journal(capture) → merge → 六维打分 → 去重(ADD/UPDATE/NOOP) → gate → candidates.md 草稿。
铁律:本脚本不调任何 LLM;打分/去重/把门/写盘全部可复算;绝不直接改 00-RULES 正文。
六维公式/阈值移植同事 MemoryPalace _engine/distill.py(spec 2026-07-02 D5)。

用法(仓库任意位置):
  python3 tools/memory/core.py distill              # 蒸馏:追加 candidates.md + DREAMS 留痕
  python3 tools/memory/core.py distill --shadow     # 只打印,不落盘
  python3 tools/memory/core.py distill --days 7     # 覆盖扫描天数
"""
from __future__ import annotations

import argparse
import json
import re
import tomllib
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from difflib import SequenceMatcher
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
VAULT = REPO / "vault" / "memory"

PREFIX_TYPE = {"偏好": "preference", "决策": "decision", "纠正": "correction", "观察": "observation"}
JOURNAL_LINE = re.compile(
    r"^\s*-\s*(偏好|决策|纠正|观察)\s*[:：]\s*(.+?)\s*(?:<!--sig\s+(\{.*?\})\s*-->)?\s*$"
)


@dataclass
class Signal:
    text: str
    kind: str            # preference / decision / correction / observation
    date: str            # YYYY-MM-DD(journal 文件名)
    sig: dict = field(default_factory=dict)


@dataclass
class Candidate:
    statement: str
    ctype: str
    scope: str           # global / project:<域/子域>
    dest: str            # vault 相对路径
    signed: bool = False
    freq: int = 1
    sources: list[str] = field(default_factory=list)
    dates: set[str] = field(default_factory=set)
    score: float = 0.0
    sub: dict[str, float] = field(default_factory=dict)
    action: str = "ADD"  # ADD / UPDATE / NOOP / INVALID
    conf: str = "low"
    invalid_reason: str = ""


def load_config(path: Path | None = None) -> dict:
    with open(path or (HERE / "config.toml"), "rb") as f:
        return tomllib.load(f)


def parse_journal(journal_dir: Path, days: int, today: date) -> list[Signal]:
    wanted = {(today - timedelta(days=i)).isoformat() for i in range(days)}
    out: list[Signal] = []
    for md in sorted(journal_dir.glob("*.md")):
        if md.stem not in wanted:
            continue
        for line in md.read_text(encoding="utf-8").splitlines():
            m = JOURNAL_LINE.match(line)
            if not m:
                continue
            sig: dict = {}
            if m.group(3):
                try:
                    parsed = json.loads(m.group(3))
                    if isinstance(parsed, dict):
                        sig = parsed
                except json.JSONDecodeError:
                    pass  # 坏 sig 容错为无 sig
            out.append(Signal(text=m.group(2).strip(), kind=PREFIX_TYPE[m.group(1)],
                              date=md.stem, sig=sig))
    return out


def infer_dest(scope: str) -> str:
    """无 sig 时的确定性缺省路由(审批时用户可改)。ops.md 为按需层,不污染 always-on 卡。"""
    if scope.startswith("project:"):
        return f"01-PROJECTS/{scope.split(':', 1)[1]}.md"
    return "00-RULES/ops.md"


def signals_to_candidates(signals: list[Signal]) -> list[Candidate]:
    out: list[Candidate] = []
    for s in signals:
        if s.kind == "observation":
            continue  # 观察只留底,不进候选
        scope = str(s.sig.get("scope") or "global")
        out.append(Candidate(
            statement=s.text,
            ctype=str(s.sig.get("type") or s.kind),
            scope=scope,
            dest=str(s.sig.get("dest") or infer_dest(scope)),
            signed=bool(s.sig),
            sources=[str(s.sig.get("source") or "journal")],
            dates={s.date},
        ))
    return out


def validate_dest(dest: str, cfg: dict) -> str:
    """dest 白名单校验:合法返回空串,非法返回原因。"""
    r = cfg["routing"]
    if ".." in dest or dest.startswith(("/", "~")):
        return "路径越界"
    if dest in r["rules_files"]:
        return ""
    if dest.endswith(".md") and any(dest.startswith(p) for p in r["projects_prefixes"]):
        return ""
    return "不在 routing 白名单"


# ---------- 合并 / 语料 / 打分 / 把门 ----------
def norm(a: str) -> str:
    return re.sub(r"\s+", "", a.lower())


def merge(cands: list[Candidate], threshold: float) -> list[Candidate]:
    """语义相近候选合并:freq/sources/dates 累加;显式 sig 的后来者覆盖路由提议。"""
    merged: list[Candidate] = []
    for c in cands:
        hit = None
        for m in merged:
            if SequenceMatcher(None, norm(c.statement), norm(m.statement)).ratio() >= threshold:
                hit = m
                break
        if hit:
            hit.freq += 1
            hit.sources = sorted(set(hit.sources + c.sources))
            hit.dates |= c.dates
            if c.signed:
                hit.ctype, hit.scope, hit.dest, hit.signed = c.ctype, c.scope, c.dest, True
        else:
            merged.append(c)
    return merged


def load_corpus(roots: list[Path]) -> list[str]:
    out: list[str] = []
    for root in roots:
        if not root.exists():
            continue
        for md in sorted(root.rglob("*.md")):
            for line in md.read_text(encoding="utf-8", errors="ignore").splitlines():
                line = line.strip(" -*")
                if 6 <= len(line) <= 200 and not line.startswith(("#", "|", "---", ">", "```")):
                    out.append(line)
    return out


def best_similarity(stmt: str, corpus: list[str]) -> float:
    s = norm(stmt)
    return max((SequenceMatcher(None, s, norm(c)).ratio() for c in corpus), default=0.0)


def score_all(cands: list[Candidate], rules_corpus: list[str], dedup_corpus: list[str],
              cfg: dict, today: date, sim=best_similarity, days: int | None = None) -> None:
    """六维加权(公式移植 distill.py):rel 用 00-RULES 语料;dedup 用全 vault 语料。"""
    w = cfg["scoring"]
    days = days if days is not None else cfg["sources"]["scan_days"]
    max_freq = max((c.freq for c in cands), default=1)
    for c in cands:
        rel = sim(c.statement, rules_corpus)
        freq = min(1.0, c.freq / max(2, max_freq))
        div = min(1.0, len(set(c.sources)) / 3.0)
        newest = max((date.fromisoformat(d) for d in c.dates), default=today)
        rec = max(0.0, 1.0 - (today - newest).days / max(1, days))
        cons = rel
        rich = min(1.0, len(c.statement) / 60.0)
        c.sub = {"relevance": rel, "frequency": freq, "diversity": div,
                 "recency": rec, "consolidation": cons, "richness": rich}
        c.score = round(w["w_relevance"] * rel + w["w_frequency"] * freq + w["w_diversity"] * div
                        + w["w_recency"] * rec + w["w_consolidation"] * cons + w["w_richness"] * rich, 3)
        dup = sim(c.statement, dedup_corpus)
        if dup >= w["noop_similarity"]:
            c.action = "NOOP"
        elif dup >= w["dedupe_similarity"]:
            c.action = "UPDATE"
        else:
            c.action = "ADD"
        c.conf = "high" if c.score >= 0.66 else "medium" if c.score >= 0.5 else "low"
        reason = validate_dest(c.dest, cfg)
        if reason:
            c.action, c.invalid_reason = "INVALID", reason


def gate(cands: list[Candidate], cfg: dict) -> tuple[list[Candidate], list[Candidate]]:
    """确定性晋升门:NOOP 暂缓;达阈值放行;global 且 freq 不足强制暂缓。"""
    w = cfg["scoring"]
    passed: list[Candidate] = []
    deferred: list[Candidate] = []
    for c in cands:
        if c.action == "NOOP":
            deferred.append(c)
            continue
        ok = c.score >= w["promote_threshold"]
        if c.scope == "global" and c.freq < w["min_freq_global"]:
            ok = False
        (passed if ok else deferred).append(c)
    passed.sort(key=lambda x: x.score, reverse=True)
    return passed, deferred


# ---------- 输出 / CLI ----------
def render_block(passed: list[Candidate], run_id: str) -> str:
    lines = [f"\n### 🟡 {run_id} 蒸馏({len(passed)} 条待审批)\n"]
    for i, c in enumerate(passed, 1):
        meta = {"id": f"c{run_id}-{i:02d}", "action": c.action, "dest": c.dest,
                "type": c.ctype, "scope": c.scope, "freq": c.freq,
                "score": c.score, "conf": c.conf}
        lines.append(f"- [ ] {c.statement} <!--cand {json.dumps(meta, ensure_ascii=False)}-->")
        warn = f" · ⚠️ {c.invalid_reason},改 dest 后再晋升" if c.action == "INVALID" else ""
        lines.append(f"  - 证据: freq={c.freq} · 来源 {', '.join(sorted(set(c.sources)))}"
                     f" · 日期 {', '.join(sorted(c.dates))}{warn}")
        lines.append("  - 六维: " + " ".join(f"{k}={v:.2f}" for k, v in c.sub.items()))
    return "\n".join(lines) + "\n"


def append_to(path: Path, block: str) -> None:
    prev = path.read_text(encoding="utf-8") if path.exists() else ""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(prev + block, encoding="utf-8")


def distill(args, vault: Path | None = None, cfg: dict | None = None) -> int:
    v = vault or VAULT
    cfg = cfg or load_config()
    days = args.days or cfg["sources"]["scan_days"]
    # sweep 补漏模式:一次性抽取的事实天然 freq=1,被 w_frequency 结构性压分,
    # 故用 [sweep].promote_threshold 单列门槛(ADR-0019)。min_freq_global 不放宽。
    sweep_mode = bool(getattr(args, "sweep", False))
    if sweep_mode:
        thr = cfg.get("sweep", {}).get("promote_threshold")
        if thr is not None:
            cfg = {**cfg, "scoring": {**cfg["scoring"], "promote_threshold": thr}}
    today = date.fromisoformat(args.today) if args.today else datetime.now().date()
    journal_dir = v / "04-FEEDBACK" / "journal"
    signals = parse_journal(journal_dir, days, today)
    cands = merge(signals_to_candidates(signals), cfg["scoring"]["merge_similarity"])
    rules_corpus = load_corpus([v / "00-RULES"])
    dedup_corpus = load_corpus([v / "00-RULES", v / "01-PROJECTS"])
    score_all(cands, rules_corpus, dedup_corpus, cfg, today, days=days)
    passed, deferred = gate(cands, cfg)

    run_id = datetime.now().strftime("%Y%m%d-%H%M")
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    mode_tag = f"(sweep·门槛 {cfg['scoring']['promote_threshold']})" if sweep_mode else ""
    summary = (
        f"\n## {ts} · distill{'(shadow)' if args.shadow else ''}{mode_tag}\n"
        f"- 扫描: journal 近 {days} 天,信号 {len(signals)} 行\n"
        f"- 候选: {len(cands)} 条(达标 {len(passed)} · 暂缓 {len(deferred)})\n"
        f"- 达标: " + (", ".join(f"「{c.statement[:24]}」{c.score}" for c in passed) or "无") + "\n"
        f"- 暂缓: " + (", ".join(f"「{c.statement[:16]}」{c.action}/{c.score}" for c in deferred) or "无") + "\n"
    )
    block = render_block(passed, run_id) if passed else ""
    print(summary)
    if block:
        print(block)
    if args.shadow:
        print("[shadow] 未落盘。")
        return 0
    if block:
        append_to(v / "04-FEEDBACK" / "candidates.md", block)
    append_to(v / "04-FEEDBACK" / "DREAMS.md", summary)
    print(f"[distill] 完成:{len(passed)} 条候选已入 candidates.md;勾 [x] 后跑 promote.py。")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="AiPalace 手动飞轮 · 确定性蒸馏内核")
    sub = ap.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("distill", help="journal → 六维打分 → candidates 草稿")
    d.add_argument("--days", type=int, default=None, help="覆盖扫描天数")
    d.add_argument("--shadow", action="store_true", help="只打印不落盘")
    d.add_argument("--sweep", action="store_true",
                   help="sweep 补漏模式:改用 [sweep].promote_threshold(freq=1 不被结构性压分)")
    d.add_argument("--today", default=None, help="锚定日期 YYYY-MM-DD(复算/测试用)")
    return distill(ap.parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
