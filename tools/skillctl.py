#!/usr/bin/env python3
"""skillctl —— AiPalace skill 中央管理工具

借鉴 garveyhu/awesome-skills 的 skill-management 方法论（来源→分类→skill + 单一
registry.yaml + tier 控 token + sync/doctor 防腐化），但针对本地实测做了三处关键改造：

  1) sync 落地形态 = 软链（symlink），派生回仓库真身。
     ADR-0005 实测：软链 skill 在 / 斜杠菜单完整可见；#14836 仅影响 /skills 管理
     命令列表，不影响自动触发与 / 菜单，原先切硬拷贝的前提已证伪，回归 symlink。
  2) 支持 source 内带子路径的 skill key（如 garveyhu/style-vault），适配三级保真目录。
  3) prune/fix 只回收「受管标记」条目（软链指向仓库 SKILLS 内，或旧拷贝残留含
     .aipalace-managed 标记），绝不触碰用户手建的软链 / 真实 skill。
     受管判定靠 is_managed()：优先软链指向校验；兼容旧 copytree 残留的 .aipalace-managed。

放置约定： <root>/tools/skillctl.py ，单一事实源 <root>/registry.yaml
物理结构： <root>/skills/<source>/<...>/<skill>/SKILL.md

tier 四层：
  core    进全局挂载（~/.claude/skills & ~/.codex/skills）；/ 菜单可见；优先加载
  extra   同上；按需加载
  project 移出全局，仅 opt-in mount 至指定项目（.claude/skills + .agents/skills 双发现路径，ADR-0015）；不进全局挂载
  parked  仅在仓库内备份，不挂载、不占 token 预算

扁平镜像（flat_mirror）：仅 core skill 拍平软链至单一目录（不含 core 层），
供支持"默认加载层"的 agent runtime 使用；路径在 registry 顶部 flat_mirror: 声明。

用法（不带参数 = stats 总览）:
  python3 tools/skillctl.py              一眼总览：来源/分类/层级分布 + 挂载健康
  python3 tools/skillctl.py sync         据 registry 把 core+extra 软链派生进各 mounts
  python3 tools/skillctl.py doctor       体检：缺 SKILL.md / category 越界 / 悬挂软链 / 孤儿
  python3 tools/skillctl.py fix          清悬挂受管软链（dry-run；加 --apply 真正删除）
  python3 tools/skillctl.py sync --dry   只打印将要做的事，不落盘（强烈建议先 --dry）
  python3 tools/skillctl.py mount <项目>   把该项目的 project skill 挂至 umbrella + 其下每个 git 仓根的
                                          .claude/skills（Claude Code）与 .agents/skills（Codex）（ADR-0010 / ADR-0015）
  python3 tools/skillctl.py unmount <项目> 清除该项目 umbrella + 各 git 仓根双发现目录下的受管软链
                                          （mount/unmount 加 --no-recurse 回退「仅 umbrella」旧行为）

⚠️ 本工具会写入 ~/.claude/skills 与 ~/.codex/skills。首次务必先 `sync --dry` 预览。
"""
import os, re, sys, shutil

ROOT  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILLS = os.path.join(ROOT, "skills")
REG    = os.path.join(ROOT, "registry.yaml")
MARK   = ".aipalace-managed"   # 受管标记文件，prune 只动带此标记的目录

C = dict(grn="\033[32m", red="\033[31m", yel="\033[33m", dim="\033[2m", rst="\033[0m")
def c(s, col): return f"{C[col]}{s}{C['rst']}"


def load_registry():
    txt = open(REG, encoding="utf-8").read()
    mounts, sources, projects, flat_mirror, sec = [], [], {}, None, None
    for ln in txt.splitlines():
        fm = re.match(r'^flat_mirror:\s*(.+?)\s*(?:#.*)?$', ln)
        if fm: flat_mirror = os.path.expanduser(fm.group(1).strip().strip('"\'')); continue
        h = re.match(r'^(mounts|sources|categories|skills|projects):', ln)
        if h: sec = h.group(1); continue
        if sec == "mounts":
            m = re.match(r'^\s*-\s*(.+?)\s*(?:#.*)?$', ln)
            if m: mounts.append(os.path.expanduser(m.group(1).strip().strip('"\'')))
        elif sec == "sources":
            m = re.match(r'^\s{2}([A-Za-z0-9_-]+):\s*"', ln)
            if m: sources.append(m.group(1))
        elif sec == "projects":
            m = re.match(r'^\s{2}([A-Za-z0-9_-]+):\s*(.+?)\s*(?:#.*)?$', ln)
            if m: projects[m.group(1)] = os.path.expanduser(m.group(2).strip().strip('"\''))
    skills = {}
    # key 允许含 '/'（如 garveyhu/style-vault）
    for m in re.finditer(
        r'^\s{2}([A-Za-z0-9_./-]+):\s*\{source:\s*([A-Za-z0-9_-]+),\s*'
        r'category:\s*([A-Za-z0-9_-]+),\s*tier:\s*([A-Za-z0-9_-]+)'
        r'(?:,\s*project:\s*([A-Za-z0-9_,-]+))?', txt, re.M):
        key, src, cat, tier, proj = m.groups()
        # project 支持多值（逗号分隔，如 zhijin,zhijin_etl）→ 统一存为 list（无则空 list）
        projs = [p.strip() for p in proj.split(",") if p.strip()] if proj else []
        skills[key] = dict(source=src, category=cat, tier=tier, project=projs)
    return mounts, sources, skills, projects, flat_mirror


def skill_dir(key, info):
    """registry key → 磁盘真身目录。key 可能形如 'garveyhu/style-vault' 或 'biz-workflow'。
    去掉与 source 同名的前缀段后，剩余即 source 目录内的相对路径。"""
    rel = key
    if rel.startswith(info["source"] + "/"):
        rel = rel[len(info["source"]) + 1:]
    # source 目录可能在 skills/<source>（mine）、skills/community/<source>（community 各源）
    # 或 skills/enterprise/<source>（公司内部，如 zhijin）。
    src_root = None
    for c in (os.path.join(SKILLS, info["source"]),
              os.path.join(SKILLS, "community", info["source"]),
              os.path.join(SKILLS, "enterprise", info["source"])):
        if os.path.isdir(c): src_root = c; break
    if src_root is None:
        return os.path.join(SKILLS, info["source"], rel)  # 不存在，交 doctor 报缺
    # 直接路径命中 → 返回；否则在 source 内递归按 basename 定位含 SKILL.md 的目录
    cand = os.path.join(src_root, rel)
    if os.path.isfile(os.path.join(cand, "SKILL.md")):
        return cand
    base = os.path.basename(rel)
    for dp, _, fs in os.walk(src_root):
        if "SKILL.md" in fs and os.path.basename(dp) == base:
            return dp
    return cand  # 不存在时返回直观路径，交 doctor 报缺


def mount_name(key):
    """挂载到 agent 目录时的条目名（取 basename，避免 / 进目录名）。"""
    return os.path.basename(key)


def is_managed(path):
    """受管判定：本工具派生物。symlink 模式 = 软链且指向仓库 SKILLS 内；
    兼容旧 copytree 残留 = 目录内含 .aipalace-managed 标记。"""
    if os.path.islink(path):
        real = os.path.realpath(path)
        return real == SKILLS or real.startswith(SKILLS + os.sep)
    if os.path.isdir(path):
        return os.path.isfile(os.path.join(path, MARK))
    return False


def sync(dry=False):
    mounts, sources, skills, projects, flat_mirror = load_registry()
    linked = {k: i for k, i in skills.items() if i["tier"] in ("core", "extra")}
    tag = c("[dry-run] ", "yel") if dry else ""
    for mnt in mounts:
        if not dry: os.makedirs(mnt, exist_ok=True)
        made = updated = skipped = 0
        names = {}
        for k, i in sorted(linked.items()):
            nm = mount_name(k)
            if nm in names:
                print(c(f"  ⚠ 同名冲突 {nm}：{names[nm]} vs {k} —— 跳过后者，请在 registry 改 tier", "yel"))
                skipped += 1; continue
            names[nm] = k
            src = skill_dir(k, i)
            dst = os.path.join(mnt, nm)
            if not os.path.isfile(os.path.join(src, "SKILL.md")):
                print(c(f"  ✗ 源缺 SKILL.md，跳过：{k}", "red")); skipped += 1; continue
            if os.path.lexists(dst):
                if is_managed(dst):
                    if not dry:
                        if os.path.islink(dst): os.unlink(dst)
                        else: shutil.rmtree(dst)   # 旧 copytree 残留
                    updated += 1
                else:
                    print(c(f"  ⚠ 已存在非受管条目，保护跳过：{dst}", "yel")); skipped += 1; continue
            else:
                made += 1
            if not dry:
                # target 为绝对路径（skill_dir 返回绝对路径）；仓库整体迁移/改路径后
                # 受管软链会悬挂，恢复方式是重跑 sync（会替换旧链接）。
                os.symlink(src, dst)
        pruned = 0
        if os.path.isdir(mnt):
            keep = set(names)
            for e in os.listdir(mnt):
                p = os.path.join(mnt, e)
                if is_managed(p) and e not in keep:
                    if not dry:
                        if os.path.islink(p): os.unlink(p)
                        else: shutil.rmtree(p)
                    pruned += 1
        print(c(f"{tag}✓ {mnt}：新建 {made} / 更新 {updated} / 跳过 {skipped} / prune {pruned}", "grn"))

    # 扁平镜像：仅 core 拍平软链（不包 core 层），本轮路径来自 registry flat_mirror
    if flat_mirror:
        core = {k: i for k, i in skills.items() if i["tier"] == "core"}
        if not dry: os.makedirs(flat_mirror, exist_ok=True)
        fmade = fpruned = 0
        fnames = {}
        for k, i in sorted(core.items()):
            nm = mount_name(k); fnames[nm] = k
            src = skill_dir(k, i); dst = os.path.join(flat_mirror, nm)
            if not os.path.isfile(os.path.join(src, "SKILL.md")): continue
            if os.path.lexists(dst):
                if is_managed(dst):
                    if not dry and os.path.islink(dst): os.unlink(dst)
                else: continue
            if not dry: os.symlink(src, dst); fmade += 1
        if os.path.isdir(flat_mirror):
            for e in os.listdir(flat_mirror):
                p = os.path.join(flat_mirror, e)
                if is_managed(p) and e not in fnames:
                    if not dry and os.path.islink(p): os.unlink(p)
                    fpruned += 1
        print(c(f"{tag}✓ 扁平镜像 {flat_mirror}：core {fmade} / prune {fpruned}", "grn"))


def stats():
    mounts, sources, skills, projects, flat_mirror = load_registry()
    if not skills: print("registry 为空"); return
    by_src, by_cat, by_tier = {}, {}, {"core": 0, "extra": 0, "project": 0, "parked": 0}
    for i in skills.values():
        by_src[i["source"]] = by_src.get(i["source"], 0) + 1
        by_cat[i["category"]] = by_cat.get(i["category"], 0) + 1
        by_tier[i["tier"]] = by_tier.get(i["tier"], 0) + 1

    def bar(n, mx, w=22):
        f = round(n / mx * w) if mx else 0
        return c("█" * f, "grn") + c("░" * (w - f), "dim")

    print("\n" + c("━━━ AiPalace Skill 生态 " + "━" * 26, "grn"))
    print(f"  {len(skills)} skill · {len(sources)} 来源 · {len(by_cat)} 分类 · "
          f"core {by_tier['core']} / extra {by_tier['extra']} / project {by_tier.get('project',0)} / parked {by_tier['parked']}")
    print(c("\n  来源", "dim")); mxs = max(by_src.values())
    for s in sources:
        n = by_src.get(s, 0)
        print(f"    {s:<18}{n:>3}  {bar(n, mxs)}")
    print(c("\n  分类（按 skill 数）", "dim")); mxc = max(by_cat.values())
    for k in sorted(by_cat, key=lambda x: -by_cat[x]):
        print(f"    {k:<18}{by_cat[k]:>3}  {bar(by_cat[k], mxc)}")
    print(c("\n  挂载健康", "dim"))
    linked = {k for k, i in skills.items() if i["tier"] in ("core", "extra")}
    for mnt in mounts:
        managed = foreign = 0
        if os.path.isdir(mnt):
            for e in sorted(os.listdir(mnt)):
                if e == ".DS_Store": continue
                p = os.path.join(mnt, e)
                if is_managed(p): managed += 1
                elif os.path.islink(p) or os.path.isdir(p): foreign += 1
        nm = os.path.basename(mnt.rstrip("/"))
        print(f"    {nm:<14} 受管 {managed:>3} · 非受管(既有) {foreign:>3}")
    print(c(f"\n  应挂载(core+extra) {len(linked)} 个；parked 仅备份 {by_tier['parked']} 个\n", "dim"))
    # project 级 + 扁平镜像
    proj_skills = [k for k, i in skills.items() if i["tier"] == "project"]
    if proj_skills or projects:
        print(c("  项目级 skill（移出全局，opt-in mount）", "dim"))
        for k in sorted(proj_skills):
            print(f"    {mount_name(k):<22} → 项目 {','.join(skills[k]['project']) or '(未声明)'}")
    if flat_mirror:
        print(c(f"\n  扁平镜像（core 拍平默认层）: {flat_mirror}", "dim"))
    print()


CATEGORIES = {"workflow", "method", "sql", "stack", "docs", "design", "diagram", "media", "meta"}

def class_of(d):
    """真身目录属哪个顶层 class（skills/<class>/...）。"""
    rel = os.path.relpath(d, SKILLS)
    top = rel.split(os.sep)[0]
    return top if top in ("mine", "community", "enterprise") else None

def has_source_doc(d):
    """skill 目录或其父级（source 层）有 _SOURCE.md。"""
    cur = d
    # range(3) 深度不变量：向上覆盖 skill dir → source dir → class dir
    # 对应目录结构 skills/<class>/<source>/<skill>；若未来目录层级加深，
    # 需同步增大此值，或改为向上走到 SKILLS 根停止。
    for _ in range(3):
        if os.path.isfile(os.path.join(cur, "_SOURCE.md")): return True
        cur = os.path.dirname(cur)
    return False


def doctor():
    mounts, sources, skills, projects, flat_mirror = load_registry()
    problems, warnings = [], []
    for k, i in skills.items():
        d = skill_dir(k, i)
        if not os.path.isdir(d):
            problems.append(f"缺真身: {k}  (找不到 {os.path.relpath(d, ROOT)})")
        else:
            if not os.path.isfile(os.path.join(d, "SKILL.md")):
                problems.append(f"缺 SKILL.md: {k}")
            cls = class_of(d)
            if cls == "community" and not has_source_doc(d):
                problems.append(f"community 缺 _SOURCE.md: {k}")
            if cls == "enterprise" and not has_source_doc(d):
                problems.append(f"enterprise 缺标注: {k}")
        if i["category"] not in CATEGORIES:
            problems.append(f"category 越界: {k} → {i['category']}（不在封闭集合）")
        if i["tier"] == "project":
            if not i["project"]:
                problems.append(f"project 缺 project: 字段: {k}")
            else:
                for pk in i["project"]:
                    if pk not in projects:
                        problems.append(f"project 未声明: {k} → {pk}（projects: 段缺）")
    linked = {k: i for k, i in skills.items() if i["tier"] in ("core", "extra")}
    seen = {}
    for k in linked:
        nm = mount_name(k)
        if nm in seen: problems.append(f"挂载名冲突: {nm}  ({seen[nm]} vs {k})")
        seen[nm] = k
    # 悬挂软链：受管软链但目标已不存在
    for mnt in mounts:
        if not os.path.isdir(mnt): continue
        for e in os.listdir(mnt):
            p = os.path.join(mnt, e)
            if is_managed(p) and not os.path.exists(p):
                problems.append(f"悬挂软链: {os.path.basename(mnt)}/{e}（指向真身已不存在）")
    # 孤儿：skills/ 下有 SKILL.md 但未登记
    # 注意：这是全深度遍历——任何含 SKILL.md 的目录（包括 skill 自带的嵌套 fixture）
    # 都会被当作未登记孤儿 warning。这是已接受的取舍。
    registered = {os.path.realpath(skill_dir(k, i)) for k, i in skills.items()}
    for dp, _, fs in os.walk(SKILLS):
        if "SKILL.md" in fs and os.path.realpath(dp) not in registered:
            warnings.append(f"孤儿(未登记): {os.path.relpath(dp, SKILLS)}")
    print(c(f"\ndoctor {len(skills)} skill / {len(sources)} 来源 / {len(mounts)} 挂载", "dim"))
    for w in warnings: print(c("   ⚠ " + w, "yel"))
    if not problems:
        print(c("✓ 全部通过，无漂移", "grn")); return 0
    print(c(f"✗ {len(problems)} 处问题：", "red"))
    for p in problems: print("   - " + p)
    return 1


def fix(dry=True):
    """安全自动修：只清『受管 + 悬挂』软链。绝不碰非受管对象、不自动登记孤儿。"""
    mounts, _, _, _, _ = load_registry()
    tag = c("[dry-run] ", "yel") if dry else ""
    total = 0
    for mnt in mounts:
        if not os.path.isdir(mnt): continue
        for e in os.listdir(mnt):
            p = os.path.join(mnt, e)
            if is_managed(p) and not os.path.exists(p):
                print(c(f"{tag}清悬挂软链: {os.path.basename(mnt)}/{e}", "yel"))
                if not dry: os.unlink(p)
                total += 1
    print(c(f"{tag}✓ 处理 {total} 个悬挂受管软链", "grn"))


# ADR-0010：project skill 须挂到每个独立 git 仓根，否则子仓会话向上遍历到自身 git 根
# 即停（两工具均只查 cwd→repo root），够不到上方伞形目录的发现目录。
# ADR-0015：两工具项目级发现路径零重叠——Claude Code 只扫 .claude/skills，
# Codex 只扫 .agents/skills（官方 docs + 0.142.5 二进制实证），故双路径各派生一份。
PROJECT_SKILL_DIRS = (os.path.join(".claude", "skills"), os.path.join(".agents", "skills"))
# 剪枝：vcs/构建产物/依赖噪声 + .claude/.codex/.agents（配置目录，其下 worktrees 是临时 git 仓，不挂）
GIT_ROOT_SKIP = {".git", ".claude", ".codex", ".agents", "node_modules", ".venv", "venv",
                 "target", "build", "dist", ".gradle", ".idea", "__pycache__", "out"}

def git_roots(base, max_depth=6):
    """枚举 base 下（含 base 本身）的所有 git 仓根：含 .git（目录或文件）的目录。
    剪枝噪声目录 + max_depth 兜底成本；不在找到的根处剪枝，以捕获嵌套独立仓。"""
    base = os.path.abspath(os.path.expanduser(base))
    if not os.path.isdir(base): return []
    base_depth = base.rstrip(os.sep).count(os.sep)
    roots = []
    for dp, dirs, _files in os.walk(base):
        if os.path.exists(os.path.join(dp, ".git")):
            roots.append(dp)
        if dp.rstrip(os.sep).count(os.sep) - base_depth >= max_depth:
            dirs[:] = []                                      # 深度兜底
        else:
            dirs[:] = [d for d in dirs if d not in GIT_ROOT_SKIP]   # 剪枝噪声
    return roots


def _mount_targets(umbrella, recurse):
    """umbrella + 其下各 git 仓根（去重保序）。"""
    targets = [umbrella]
    if recurse:
        for r in git_roots(umbrella):
            if r not in targets: targets.append(r)
    return targets


def _link_project_skills(skills, proj, dstdir, dry):
    """在单个 dstdir 下为 proj 的 project skill 建受管指针软链，返回新建数。"""
    if not dry: os.makedirs(dstdir, exist_ok=True)
    n = 0
    for k, i in sorted(skills.items()):
        if i["tier"] != "project" or proj not in i["project"]: continue
        src = skill_dir(k, i); nm = mount_name(k); dst = os.path.join(dstdir, nm)
        if not os.path.isfile(os.path.join(src, "SKILL.md")):
            print(c(f"  ✗ 源缺 SKILL.md，跳过：{k}", "red")); continue
        if os.path.lexists(dst):
            if is_managed(dst):
                if not dry and os.path.islink(dst): os.unlink(dst)
            else:
                print(c(f"  ⚠ 已存在非受管条目，保护跳过：{dst}", "yel")); continue
        if not dry: os.symlink(src, dst)
        n += 1
    return n


def mount(proj, dry=False, recurse=True):
    mounts, sources, skills, projects, _ = load_registry()
    if proj not in projects:
        print(c(f"✗ 未声明的项目: {proj}（registry projects: 段缺）", "red")); return 1
    targets = _mount_targets(projects[proj], recurse)
    tag = c("[dry-run] ", "yel") if dry else ""
    total = sum(_link_project_skills(skills, proj, os.path.join(b, d), dry)
                for b in targets for d in PROJECT_SKILL_DIRS)
    print(c(f"{tag}✓ mount {proj}：派生 {total} 条软链 / 覆盖 umbrella + {len(targets)-1} 个 git 根 × {len(PROJECT_SKILL_DIRS)} 个发现目录", "grn"))
    return 0


def unmount(proj, dry=False, recurse=True):
    _, _, _, projects, _ = load_registry()
    if proj not in projects:
        print(c(f"✗ 未声明的项目: {proj}", "red")); return 1
    targets = _mount_targets(projects[proj], recurse)
    tag = c("[dry-run] ", "yel") if dry else ""
    n = 0
    for b in targets:
        for d in PROJECT_SKILL_DIRS:
            dstdir = os.path.join(b, d)
            if not os.path.isdir(dstdir): continue
            for e in os.listdir(dstdir):
                p = os.path.join(dstdir, e)
                if is_managed(p):
                    if not dry and os.path.islink(p): os.unlink(p)
                    n += 1
    print(c(f"{tag}✓ unmount {proj}：清 {n} 个受管软链 / 覆盖 umbrella + {len(targets)-1} 个 git 根 × {len(PROJECT_SKILL_DIRS)} 个发现目录", "grn")); return 0


def main():
    args = sys.argv[1:]
    cmd = args[0] if args else "stats"
    dry = "--dry" in args
    if cmd == "sync": sync(dry=dry)
    elif cmd == "doctor": sys.exit(doctor())
    elif cmd == "fix": fix(dry=("--apply" not in args))
    elif cmd == "stats": stats()
    elif cmd == "mount" and len(args) > 1:
        sys.exit(mount(args[1], dry=("--dry" in args), recurse=("--no-recurse" not in args)))
    elif cmd == "unmount" and len(args) > 1:
        sys.exit(unmount(args[1], dry=("--dry" in args), recurse=("--no-recurse" not in args)))
    else: print(__doc__); sys.exit(2)


if __name__ == "__main__":
    main()
