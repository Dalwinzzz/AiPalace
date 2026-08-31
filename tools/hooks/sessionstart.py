#!/usr/bin/env python3
"""SessionStart hook（受管单一源，双工具共用）。

输出 = cwd 工作域打分（门 a：pack 技能建议）＋ always-on 注入 AiPalace
`vault/memory/INDEX.md`（always-on 决策树，渐进披露）。

pack 推荐为 registry 驱动（P2 单一源）：公司域动态拉取 `project:zhijin` 的
project skill（ownerpowers/biz-workflow 等不再漏、随 registry 增减不漂移），
补充项校验 registry 存在性、漂移名自动剔除；`+` 前缀为 registry 外的
superpowers/MCP 兜底推荐（恒保留）。详见 DOMAIN_PROJECT / DOMAIN_EXTRA / build_pack。

ADR-0007：以 AiPalace INDEX 注入取代旧 dalwin-workflow domain-context 扁平指针。
现役 ~/.claude/hooks/sessionstart-domain.py、~/.codex/hooks/sessionstart-domain.py
由本文件软链派生；脚本经 realpath 解回 AiPalace，故软链/副本/异常 cwd 下均可定位 context。

context root 解析顺序：AIPALACE_CONTEXT 环境变量 → realpath(__file__) 上溯 → 硬编码兜底。
"""
import json
import os
import sys
from pathlib import Path

_HERE = os.path.dirname(os.path.realpath(__file__))          # AiPalace/tools/hooks
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.normpath(os.path.join(_HERE, "..")))  # AiPalace/tools（导入 skillctl）
from inject_index import inject_index  # noqa: E402  复用 INDEX 拼接（单一实现）

THRESHOLD = 0.5
NOISE_FLOOR = 0.3

# ── pack 推荐：registry 驱动（P2 单一源），不再硬编码 skill 名清单 ──────────────
# DOMAIN_PROJECT：cwd 工作域 ↔ registry project。公司域动态拉取该 project 的全部
#   project skill（ownerpowers/biz-workflow 等自动出现、随 registry 增减不漂移）。
DOMAIN_PROJECT = {"java/spring": "zhijin"}

# DOMAIN_EXTRA：各域补充推荐。
#   - 裸名 = registry 内 skill 的 basename，脚本校验存在性，漂移则自动剔除；
#   - '+' 前缀 = registry 外的 superpowers/MCP/bundled 兜底推荐，恒保留，输出去前缀。
DOMAIN_EXTRA = {
    "java/spring": ["git-merge-conductor", "grill-with-docs",
                    "+requesting-code-review", "+security-review"],
    "ai_build":    ["skill-management", "skill-security-audit", "find-skills",
                    "git-merge-conductor", "+skill-creator"],
    "knowledge":   ["deep-research", "html-diagram", "docx", "+notion-search"],
    "learning":    ["grill-me", "deep-research", "+claude-api"],
}

PACK_ID = {
    "java/spring": "java",
    "ai_build": "ai-build",
    "knowledge": "knowledge",
    "learning": "learning",
}


def mount_name(key: str) -> str:
    """registry key → 挂载/显示名（取 basename，与 skillctl 一致）。"""
    return os.path.basename(key)


def _registry_skills() -> dict:
    """读 AiPalace/registry.yaml 的 skill 段；不可用时返回 {} 优雅降级。"""
    try:
        import skillctl  # noqa: PLC0415
        _, _, skills, _, _ = skillctl.load_registry()
        return skills
    except Exception:
        return {}


def build_pack(domain: str, skills: dict | None = None) -> list:
    """组装某工作域的推荐 skill 列表（registry 驱动）。
    = sorted(该域映射 project 的 project skill) + 校验后的 DOMAIN_EXTRA。"""
    if skills is None:
        skills = _registry_skills()
    names = {mount_name(k) for k in skills}
    out = []
    proj = DOMAIN_PROJECT.get(domain)
    if proj:
        out += sorted(mount_name(k) for k, i in skills.items() if i.get("project") == proj)
    for e in DOMAIN_EXTRA.get(domain, []):
        nm = e[1:] if e.startswith("+") else e
        if (e.startswith("+") or e in names) and nm not in out:
            out.append(nm)
    return out

_HARDCODED_CONTEXT = os.path.expanduser("~/Library/CodeRepo/AI/AiPalace/vault/memory")


def resolve_context_root() -> str:
    """AIPALACE_CONTEXT env → realpath 上溯派生 → 硬编码兜底。"""
    env = os.environ.get("AIPALACE_CONTEXT")
    if env:
        return env
    here = os.path.dirname(os.path.realpath(__file__))            # AiPalace/tools/hooks
    derived = os.path.normpath(os.path.join(here, "..", "..", "vault", "memory"))
    if os.path.isdir(derived):
        return derived
    return _HARDCODED_CONTEXT


def has_marker(cwd: Path, marker: str, max_up: int = 5) -> bool:
    p = cwd
    for _ in range(max_up):
        if (p / marker).exists():
            return True
        if p.parent == p:
            break
        p = p.parent
    return False


def has_glob(cwd: Path, pattern: str) -> bool:
    try:
        return any(cwd.glob(pattern))
    except (OSError, ValueError):
        return False


def compute_confidence(cwd: Path) -> dict:
    cwd_str = str(cwd)
    scores = {}

    # java/spring（含 Maven monorepo：cwd 自身无 pom.xml 但子目录有）
    s = 0.0
    if has_marker(cwd, "pom.xml"): s += 0.5
    if has_glob(cwd, "*/pom.xml"): s += 0.3
    if has_marker(cwd, "mvnw"): s += 0.2
    if has_marker(cwd, "src/main/java"): s += 0.3
    if has_glob(cwd, "*/src/main/java"): s += 0.2
    if has_marker(cwd, ".idea"): s += 0.1
    scores["java/spring"] = min(s, 1.0)

    # ai_build
    s = 0.0
    if "AiPalace" in cwd_str: s += 0.4          # ADR-0007：AiPalace 即 AI 构建域主场
    if "awesome-skills" in cwd_str: s += 0.4
    if "superpowers/skills" in cwd_str: s += 0.4
    if ".claude/skills" in cwd_str or ".codex/skills" in cwd_str: s += 0.4
    if cwd.name.startswith("skill-"): s += 0.3
    if "AI" in cwd.parts: s += 0.2
    scores["ai_build"] = min(s, 1.0)

    # knowledge
    s = 0.0
    if "/docs/" in cwd_str or cwd_str.endswith("/docs"): s += 0.15
    if "/wiki/" in cwd_str or cwd_str.endswith("/wiki"): s += 0.3
    if "Notion" in cwd_str or "notion" in cwd_str: s += 0.5
    scores["knowledge"] = min(s, 1.0)

    # learning
    s = 0.0
    if has_marker(cwd, "go.mod"): s += 0.6
    if has_glob(cwd, "*.go"): s += 0.4
    low = cwd_str.lower()
    if any(kw in low for kw in ["learn", "/study/", "/学习/"]): s += 0.3
    scores["learning"] = min(s, 1.0)

    return scores


def format_domain(scores: dict, cwd: Path) -> str:
    """门 a：cwd 打分 → [工作域] 行 + pack 技能建议（registry 驱动，不含旧 DOMAIN_CONTEXT 指针）。"""
    visible = {k: v for k, v in scores.items() if v >= NOISE_FLOOR}
    if not visible:
        return f"[工作域] cwd={cwd}: 无主域；仅 spine 可用"

    primary = sorted([k for k, v in visible.items() if v >= THRESHOLD],
                     key=lambda k: -visible[k])
    if not primary:
        cands = ", ".join(f"{k}={visible[k]:.2f}"
                          for k in sorted(visible, key=lambda k: -visible[k]))
        return f"[工作域] cwd={cwd}: {cands}（无主域，仅 spine 可用）"

    skills = _registry_skills()   # 一次加载，多主域共用
    if len(primary) == 1:
        k = primary[0]
        members = ", ".join(build_pack(k, skills))
        return f"[工作域] {k}={visible[k]:.2f}; pack-{PACK_ID[k]}: {members}"

    lines = ["[工作域] " + ", ".join(f"{k}={visible[k]:.2f}" for k in primary)]
    for k in primary:
        lines.append(f"  pack-{PACK_ID[k]}: {', '.join(build_pack(k, skills))}")
    return "\n".join(lines)


def build_output(cwd: Path, context_root: str) -> str:
    """合并：工作域提示 ＋ always-on INDEX 注入。"""
    domain = format_domain(compute_confidence(cwd), cwd)
    index = inject_index(context_root)
    return f"{domain}\n\n{index}" if index else domain


def main(stdin=None) -> None:
    stdin = stdin if stdin is not None else sys.stdin
    try:
        data = json.loads(stdin.read() or "{}")
        cwd = Path(data.get("cwd") or os.getcwd())
    except (json.JSONDecodeError, ValueError, OSError, AttributeError):
        cwd = Path(os.getcwd())

    context = build_output(cwd, resolve_context_root())
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": context,
        }
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
