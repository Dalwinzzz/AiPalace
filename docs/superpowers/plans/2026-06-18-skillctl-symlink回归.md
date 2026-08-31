# skillctl 回归 symlink + doctor 增强 + --fix 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 `tools/skillctl.py` 的 sync 派生形态从硬拷贝改回 symlink（承接 ADR-0005），并按治理 spec §5.7/§5.8 增强 doctor（门槛校验 + 悬挂/孤儿检测）与新增 `--fix`。

**Architecture:** 受管判定从"目录内 `.aipalace-managed` 文件标记"改为"**软链指向判定**"——软链且 realpath 落在仓库 `skills/` 内即本工具派生（兼容旧 copytree 残留的标记目录，便于迁移清理）。sync 用 `os.symlink` 替代 `copytree`，prune 与 `--fix` 只动受管对象、对用户手建物保护跳过（守 P6 零误删）。

**Tech Stack:** Python 3 标准库（os/re/sys/shutil）；pytest（tmp_path + monkeypatch 注入临时 ROOT/SKILLS/REG/mounts）。

## Global Constraints

- 仅用 Python 标准库，不引第三方依赖（pytest 仅测试用）。
- 受管判定 = 软链且指向 `SKILLS` 内 **或** 目录含 `.aipalace-managed`（兼容旧拷贝）。
- 零误删：只回收受管对象；非受管（真实目录、指向 SKILLS 外的软链）一律保护跳过。
- category 封闭集合 = `{workflow, method, sql, stack, docs, design, diagram, media, meta}`。
- 双 mount 行为不变（`~/.claude/skills` + `~/.codex/skills`，测试用 tmp 替身）。
- `--fix` 默认 dry-run，须 `--apply` 才落盘。

---

### Task 1: 测试脚手架 + `is_managed()` 受管判定

**Files:**
- Modify: `tools/skillctl.py`（新增 `is_managed()`；line 31 `MARK` 常量保留）
- Create: `tests/test_skillctl.py`
- Create: `tests/conftest.py`

**Interfaces:**
- Produces: `is_managed(path) -> bool`；fixture `palace(tmp_path, monkeypatch)` 返回一个对象，含 `.skills`(仓库 skills 真身根)、`.mounts`(挂载点 list)、`.add_skill(key, source, category, tier)`、`.write_registry()`。

- [ ] **Step 1: 写 conftest fixture**

```python
# tests/conftest.py
import os, sys, importlib, pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))

class Palace:
    def __init__(self, root, monkeypatch):
        self.root = root
        self.skills = os.path.join(root, "skills")
        self.reg = os.path.join(root, "registry.yaml")
        self.mounts = [os.path.join(root, "m_claude"), os.path.join(root, "m_codex")]
        os.makedirs(self.skills, exist_ok=True)
        self._skills = {}   # key -> dict(source,category,tier)
        self._mp = monkeypatch

    def add_skill(self, key, source, category, tier, cls="mine", with_skillmd=True, source_doc=False):
        # 真身布局：mine → skills/mine/<skill>；community/enterprise → skills/<cls>/<source>/<skill>
        rel = key[len(source)+1:] if key.startswith(source + "/") else key
        if cls == "mine":
            d = os.path.join(self.skills, "mine", os.path.basename(rel))
        else:
            d = os.path.join(self.skills, cls, source, os.path.basename(rel))
        os.makedirs(d, exist_ok=True)
        if with_skillmd:
            open(os.path.join(d, "SKILL.md"), "w").write(f"---\nname: {os.path.basename(rel)}\ndescription: test\n---\n")
        if source_doc:
            open(os.path.join(d, "_SOURCE.md"), "w").write("upstream: 待补\n")
        self._skills[key] = dict(source=source, category=category, tier=tier)
        return d

    def write_registry(self):
        lines = ["mounts:"]
        for m in self.mounts: lines.append(f'  - "{m}"')
        lines += ["sources:"]
        for s in sorted({i["source"] for i in self._skills.values()}):
            lines.append(f'  {s}: "src {s}"')
        lines += ["categories:", '  workflow: "x"', "skills:"]
        for k, i in self._skills.items():
            lines.append(f'  {k}: {{source: {i["source"]}, category: {i["category"]}, tier: {i["tier"]}}}')
        open(self.reg, "w").write("\n".join(lines) + "\n")

    def reload(self):
        import skillctl; importlib.reload(skillctl)
        self._mp.setattr(skillctl, "ROOT", self.root)
        self._mp.setattr(skillctl, "SKILLS", self.skills)
        self._mp.setattr(skillctl, "REG", self.reg)
        return skillctl

@pytest.fixture
def palace(tmp_path, monkeypatch):
    return Palace(str(tmp_path), monkeypatch)
```

- [ ] **Step 2: 写 `is_managed` 的失败测试**

```python
# tests/test_skillctl.py
import os

def test_is_managed_symlink_into_skills(palace):
    d = palace.add_skill("foo", "mine", "workflow", "core")
    palace.write_registry()
    sk = palace.reload()
    link = os.path.join(palace.mounts[0], "foo")
    os.makedirs(palace.mounts[0]); os.symlink(d, link)
    assert sk.is_managed(link) is True

def test_is_managed_foreign_symlink(palace, tmp_path):
    palace.write_registry(); sk = palace.reload()
    outside = tmp_path / "outside"; outside.mkdir()
    link = os.path.join(palace.root, "x"); os.symlink(str(outside), link)
    assert sk.is_managed(link) is False

def test_is_managed_real_dir_false(palace):
    palace.write_registry(); sk = palace.reload()
    real = os.path.join(palace.root, "realdir"); os.makedirs(real)
    assert sk.is_managed(real) is False
```

- [ ] **Step 3: 运行测试确认失败**

Run: `cd /Users/dalwin/Library/CodeRepo/AI/AiPalace && python3 -m pytest tests/test_skillctl.py -v`
Expected: FAIL with `AttributeError: module 'skillctl' has no attribute 'is_managed'`

- [ ] **Step 4: 实现 `is_managed`（加在 `mount_name` 之后，约 line 88）**

```python
def is_managed(path):
    """受管判定：本工具派生物。symlink 模式 = 软链且指向仓库 SKILLS 内；
    兼容旧 copytree 残留 = 目录内含 .aipalace-managed 标记。"""
    if os.path.islink(path):
        real = os.path.realpath(path)
        return real == SKILLS or real.startswith(SKILLS + os.sep)
    if os.path.isdir(path):
        return os.path.isfile(os.path.join(path, MARK))
    return False
```

- [ ] **Step 5: 运行测试确认通过**

Run: `python3 -m pytest tests/test_skillctl.py -v`
Expected: 3 passed

- [ ] **Step 6: Commit**

```bash
git add tools/skillctl.py tests/conftest.py tests/test_skillctl.py
git commit -m "test(skillctl): 加测试脚手架与 is_managed 指向判定"
```

---

### Task 2: `sync()` 回归 symlink

**Files:**
- Modify: `tools/skillctl.py:90-129`（`sync` 函数体）
- Modify: `tests/test_skillctl.py`

**Interfaces:**
- Consumes: `is_managed()`（Task 1）。
- Produces: `sync(dry=False)` 行为：受管/缺失对应 mount 下创建软链 `dst -> skill_dir(src)`；遇非受管条目保护跳过；prune 删受管但不在 linked 的软链。

- [ ] **Step 1: 写 sync 的失败测试**

```python
def test_sync_creates_symlink(palace):
    d = palace.add_skill("foo", "mine", "workflow", "core")
    palace.write_registry(); sk = palace.reload()
    sk.sync(dry=False)
    link = os.path.join(palace.mounts[0], "foo")
    assert os.path.islink(link)
    assert os.path.realpath(link) == os.path.realpath(d)

def test_sync_protects_foreign(palace, tmp_path):
    palace.add_skill("foo", "mine", "workflow", "core")
    palace.write_registry(); sk = palace.reload()
    os.makedirs(palace.mounts[0])
    foreign_target = tmp_path / "ft"; foreign_target.mkdir()
    foreign = os.path.join(palace.mounts[0], "foo")
    os.symlink(str(foreign_target), foreign)        # 用户手建、指向 SKILLS 外
    sk.sync(dry=False)
    assert os.path.realpath(foreign) == os.path.realpath(str(foreign_target))  # 未被覆盖

def test_sync_prunes_managed_only(palace):
    palace.add_skill("foo", "mine", "workflow", "core")
    palace.write_registry(); sk = palace.reload()
    sk.sync(dry=False)
    stale = os.path.join(palace.mounts[0], "stale")    # 受管软链（指向 SKILLS 内）但未登记
    os.symlink(palace.skills, stale)
    sk.sync(dry=False)
    assert not os.path.lexists(stale)                  # 被 prune
    assert os.path.islink(os.path.join(palace.mounts[0], "foo"))  # 在册保留
```

- [ ] **Step 2: 运行确认失败**

Run: `python3 -m pytest tests/test_skillctl.py::test_sync_creates_symlink -v`
Expected: FAIL（当前 sync 用 copytree，`os.path.islink` 为 False）

- [ ] **Step 3: 替换 sync 的创建/prune 逻辑**

把 `tools/skillctl.py:90-129` 整个 `sync` 函数替换为：

```python
def sync(dry=False):
    mounts, sources, skills = load_registry()
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
            if not dry: os.symlink(src, dst)
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
```

- [ ] **Step 4: 运行全部 sync 测试确认通过**

Run: `python3 -m pytest tests/test_skillctl.py -v -k sync`
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add tools/skillctl.py tests/test_skillctl.py
git commit -m "refactor(skillctl): sync 回归 symlink 派生（承接 ADR-0005）"
```

---

### Task 3: `doctor()` 门槛校验（category + 溯源标注）

**Files:**
- Modify: `tools/skillctl.py`（新增 `CATEGORIES`、`class_of()`、`has_source_doc()`；改 `doctor` 检查段）
- Modify: `tests/test_skillctl.py`

**Interfaces:**
- Produces: `class_of(d) -> "mine"|"community"|"enterprise"|None`；`has_source_doc(d) -> bool`；`doctor()` 对 category 越界、community 缺 `_SOURCE.md`、enterprise 缺标注报错（返回非 0）。

- [ ] **Step 1: 写失败测试**

```python
def test_doctor_category_out_of_set(palace):
    palace.add_skill("foo", "mine", "BOGUS", "core")
    palace.write_registry(); sk = palace.reload()
    assert sk.doctor() == 1

def test_doctor_community_needs_source_doc(palace):
    palace.add_skill("garveyhu/bar", "garveyhu", "docs", "parked", cls="community", source_doc=False)
    palace.write_registry(); sk = palace.reload()
    assert sk.doctor() == 1

def test_doctor_community_with_source_doc_ok(palace):
    palace.add_skill("garveyhu/bar", "garveyhu", "docs", "parked", cls="community", source_doc=True)
    palace.write_registry(); sk = palace.reload()
    assert sk.doctor() == 0
```

- [ ] **Step 2: 运行确认失败**

Run: `python3 -m pytest tests/test_skillctl.py -v -k "doctor_category or doctor_community"`
Expected: FAIL（当前 doctor 不查 category/溯源）

- [ ] **Step 3: 加常量与辅助函数（`doctor` 之前），并扩 doctor 检查段**

在 `doctor` 函数前加：

```python
CATEGORIES = {"workflow", "method", "sql", "stack", "docs", "design", "diagram", "media", "meta"}

def class_of(d):
    """真身目录属哪个顶层 class（skills/<class>/...）。"""
    rel = os.path.relpath(d, SKILLS)
    top = rel.split(os.sep)[0]
    return top if top in ("mine", "community", "enterprise") else None

def has_source_doc(d):
    """skill 目录或其父级（source 层）有 _SOURCE.md。"""
    cur = d
    for _ in range(3):
        if os.path.isfile(os.path.join(cur, "_SOURCE.md")): return True
        cur = os.path.dirname(cur)
    return False
```

在 `doctor` 的 `for k, i in skills.items():` 循环里，缺 SKILL.md 检查之后追加：

```python
        if i["category"] not in CATEGORIES:
            problems.append(f"category 越界: {k} → {i['category']}（不在封闭集合）")
        cls = class_of(d)
        if cls == "community" and not has_source_doc(d):
            problems.append(f"community 缺 _SOURCE.md: {k}")
        if cls == "enterprise" and not has_source_doc(d):
            problems.append(f"enterprise 缺标注: {k}")
```

- [ ] **Step 4: 运行确认通过**

Run: `python3 -m pytest tests/test_skillctl.py -v -k doctor`
Expected: all doctor tests passed

- [ ] **Step 5: Commit**

```bash
git add tools/skillctl.py tests/test_skillctl.py
git commit -m "feat(skillctl): doctor 增加 category 封闭集与溯源标注门槛"
```

---

### Task 4: `doctor()` 悬挂软链 + 孤儿检测

**Files:**
- Modify: `tools/skillctl.py`（`doctor` 追加两段；新增 `warnings` 列表与输出）
- Modify: `tests/test_skillctl.py`

**Interfaces:**
- Consumes: `is_managed()`、`skill_dir()`。
- Produces: `doctor()` 对受管悬挂软链报错；对 `skills/` 下有 SKILL.md 但 registry 未登记的真身报 **warning**（不影响返回码）。

- [ ] **Step 1: 写失败测试**

```python
def test_doctor_dangling_link(palace):
    d = palace.add_skill("foo", "mine", "workflow", "core")
    palace.write_registry(); sk = palace.reload()
    sk.sync(dry=False)
    import shutil as _sh; _sh.rmtree(d)        # 真身被删 → 软链悬挂
    assert sk.doctor() == 1

def test_doctor_orphan_is_warning_not_error(palace, capsys):
    palace.add_skill("foo", "mine", "workflow", "core")
    palace.write_registry(); sk = palace.reload()
    # 造一个未登记真身
    orphan = os.path.join(palace.skills, "mine", "ghost")
    os.makedirs(orphan); open(os.path.join(orphan, "SKILL.md"), "w").write("---\nname: ghost\n---\n")
    rc = sk.doctor()
    out = capsys.readouterr().out
    assert rc == 0 and "孤儿" in out
```

- [ ] **Step 2: 运行确认失败**

Run: `python3 -m pytest tests/test_skillctl.py -v -k "dangling or orphan"`
Expected: FAIL

- [ ] **Step 3: 在 doctor 里加 warnings + 两段检测**

把 `doctor` 开头 `problems = []` 改为 `problems, warnings = [], []`。在挂载名冲突检测之后、打印之前追加：

```python
    # 悬挂软链：受管软链但目标已不存在
    for mnt in mounts:
        if not os.path.isdir(mnt): continue
        for e in os.listdir(mnt):
            p = os.path.join(mnt, e)
            if is_managed(p) and not os.path.exists(p):
                problems.append(f"悬挂软链: {os.path.basename(mnt)}/{e}（指向真身已不存在）")
    # 孤儿：skills/ 下有 SKILL.md 但未登记
    registered = {os.path.realpath(skill_dir(k, i)) for k, i in skills.items()}
    for dp, _, fs in os.walk(SKILLS):
        if "SKILL.md" in fs and os.path.realpath(dp) not in registered:
            warnings.append(f"孤儿(未登记): {os.path.relpath(dp, SKILLS)}")
```

把 doctor 末尾输出改为：

```python
    print(c(f"\ndoctor {len(skills)} skill / {len(sources)} 来源 / {len(mounts)} 挂载", "dim"))
    for w in warnings: print(c("   ⚠ " + w, "yel"))
    if not problems:
        print(c("✓ 全部通过，无漂移", "grn")); return 0
    print(c(f"✗ {len(problems)} 处问题：", "red"))
    for p in problems: print("   - " + p)
    return 1
```

- [ ] **Step 4: 运行确认通过**

Run: `python3 -m pytest tests/test_skillctl.py -v`
Expected: all passed

- [ ] **Step 5: Commit**

```bash
git add tools/skillctl.py tests/test_skillctl.py
git commit -m "feat(skillctl): doctor 增加悬挂软链报错与孤儿 warning"
```

---

### Task 5: `--fix` 清悬挂软链 + stats 受管判定 + 文档同步

**Files:**
- Modify: `tools/skillctl.py`（新增 `fix()`；`main` 加分支；`stats` 受管判定改 `is_managed`；模块 docstring）
- Modify: `tests/test_skillctl.py`
- Modify: `registry.yaml`（头注释）、`README.md`（三层加载/安全保证段）

**Interfaces:**
- Consumes: `is_managed()`。
- Produces: `fix(dry=True)` 清理受管悬挂软链，dry 默认；`main()` 支持 `fix` / `fix --apply`。

- [ ] **Step 1: 写失败测试**

```python
def test_fix_dry_keeps_then_apply_removes(palace, capsys):
    d = palace.add_skill("foo", "mine", "workflow", "core")
    palace.write_registry(); sk = palace.reload()
    sk.sync(dry=False)
    link = os.path.join(palace.mounts[0], "foo")
    import shutil as _sh; _sh.rmtree(d)           # 悬挂
    sk.fix(dry=True)
    assert os.path.lexists(link)                  # dry 不删
    sk.fix(dry=False)
    assert not os.path.lexists(link)              # apply 删
```

- [ ] **Step 2: 运行确认失败**

Run: `python3 -m pytest tests/test_skillctl.py::test_fix_dry_keeps_then_apply_removes -v`
Expected: FAIL（`module 'skillctl' has no attribute 'fix'`）

- [ ] **Step 3: 实现 `fix`（加在 `doctor` 之后）**

```python
def fix(dry=True):
    """安全自动修：只清『受管 + 悬挂』软链。绝不碰非受管对象、不自动登记孤儿。"""
    mounts, _, _ = load_registry()
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
```

- [ ] **Step 4: `main` 加 fix 分支 + stats 受管判定改 is_managed**

`main` 的分支里加（在 `doctor` 分支后）：

```python
    elif cmd == "fix": fix(dry=("--apply" not in args))
```

`stats` 的 line 163 `if os.path.isdir(p) and os.path.isfile(os.path.join(p, MARK)): managed += 1` 改为：

```python
                if is_managed(p): managed += 1
                elif os.path.islink(p) or os.path.isdir(p): foreign += 1
```

- [ ] **Step 5: 运行全部测试确认通过**

Run: `python3 -m pytest tests/test_skillctl.py -v`
Expected: all passed

- [ ] **Step 6: 同步模块 docstring 与 registry/README 表述**

- `tools/skillctl.py` 顶部 docstring 第 7–13 行（讲 copytree 理由那段）改为：sync 落地 = **symlink**（ADR-0005 实测软链 skill 在 `/` 斜杠菜单正常可见，#14836 仅影响 `/skills` 管理命令）；受管判定靠指向；新增 `doctor` 门槛校验与 `fix`。把用法段的 `sync ... 硬拷贝` 改 `软链`。
- `registry.yaml` 头注释（line 2–12）：删"落地形态改为硬拷贝以规避 symlink bug"，改为"sync 软链派生回仓库真身（ADR-0005）"。
- `README.md`：「三层加载策略」「关于 sync 的安全保证」两节中"硬拷贝/copytree"表述改为 symlink，并指明受管判定靠软链指向、`--fix` 清悬挂。

- [ ] **Step 7: 跑一次真实 dry 自检（不落盘）**

Run: `python3 tools/skillctl.py sync --dry && python3 tools/skillctl.py doctor`
Expected: sync --dry 打印将创建的软链、对现有非受管软链"保护跳过"；doctor 列出真实仓库的 warning/problem（人工确认合理）。

- [ ] **Step 8: Commit**

```bash
git add tools/skillctl.py tests/test_skillctl.py registry.yaml README.md
git commit -m "feat(skillctl): 新增 --fix 清悬挂软链，stats/docstring/registry/README 同步 symlink"
```

---

## 自检清单（执行者完成后核对）

- [ ] `python3 -m pytest tests/ -v` 全绿。
- [ ] `python3 tools/skillctl.py sync --dry` 对现有 `~/.claude/skills` 的非受管软链全部"保护跳过"，不误删。
- [ ] `grep -ri "硬拷贝\|copytree" tools/skillctl.py registry.yaml README.md` 仅剩"旧 copytree 残留兼容"等必要表述。
- [ ] doctor 对真实仓库的 community/enterprise 溯源缺失、category 越界如实报出。
