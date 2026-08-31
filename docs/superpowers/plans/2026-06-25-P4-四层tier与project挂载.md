# P4 四层 tier + 扁平镜像 + project 挂载 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax.

**Goal:** 把 garveyhu skill-management 新版同步进 AiPalace：四层 tier（加 `project`）+ 扁平镜像（core 拍平、不包 core 层）+ `skillctl mount/unmount <项目>`，机制就绪、不碰现役挂载（承接 ADR-0006）。

**Architecture:** 在现有 `tools/skillctl.py`（P1 symlink 版，279 行）上扩展：`load_registry` 多解析 `projects:` 段 / `flat_mirror` / skill 的可选 `project:` 字段；`sync` 增生成扁平镜像（仅 core、拍平软链）；新增 `mount/unmount <项目>` 把 `tier:project` skill opt-in 软链进 `<项目>/.claude/skills/`；`stats/doctor` 显示并校验 project。所有写盘均经 `is_managed` 受管保护，测试用 `tmp_path` 隔离、不触现役。

**Tech Stack:** Python 标准库；pytest（tmp_path + monkeypatch，复用 tests/conftest.py 的 Palace fixture）。

## Global Constraints

- 仅 Python 标准库。
- **本轮机制就绪、不碰现役**：扁平镜像 / mount 能力 + tmp 测试，绝不向真实 `~/.agents`、`~/.claude`、`~/.codex` 落盘。
- 四层 tier = `core / extra / project / parked`；`project` 移出全局挂载点（不进 mounts、不进扁平镜像）。
- 扁平镜像（`flat_mirror`）只放 `core`，**拍平成一层、不包 core 目录层**（`<flat_mirror>/<name>`）。
- project skill 挂载名 = `SKILL.md` 的 `name`（ADR-0006 实测：斜杠菜单按 name 显示）。
- 受管判定走现有 `is_managed`；prune/mount/unmount 绝不碰非受管对象（守 P6 零误删）。
- `load_registry` 返回扩展为 `(mounts, sources, skills, projects, flat_mirror)`，所有调用者同步更新解包。
- commit-msg hook 强制 `<type>(<scope>): <subject>`。

---

### Task 1: load_registry 扩展（projects / flat_mirror / project 字段）

**Files:**
- Modify: `tools/skillctl.py:38-57`（load_registry）+ 所有调用者解包（sync/stats/doctor/fix）
- Modify: `tests/conftest.py`（Palace fixture 支持 projects/flat_mirror/project）
- Modify: `tests/test_skillctl.py`

**Interfaces:**
- Produces: `load_registry() -> (mounts, sources, skills, projects, flat_mirror)`。`skills[key]` 增可选 `project` 键（无则 None）。`projects` 为 `{<名>: <绝对路径>}`，`flat_mirror` 为 str 或 None。

- [ ] **Step 1: 扩展 conftest Palace fixture**

在 `tests/conftest.py` 的 `Palace` 增项目/扁平镜像支持。`add_skill` 增 `project=None` 参数；新增 `set_projects(**name_to_path)`、`set_flat_mirror(path)`；`write_registry` 输出 `flat_mirror`、`projects:` 段、skill 行带可选 `project:`：

```python
    def __init__(self, root, monkeypatch):
        # …现有字段…
        self._projects = {}
        self._flat = None

    def add_skill(self, key, source, category, tier, cls="mine", with_skillmd=True, source_doc=False, project=None):
        # …现有真身落盘逻辑不变…
        self._skills[key] = dict(source=source, category=category, tier=tier, project=project)
        return d

    def set_projects(self, **kw): self._projects.update(kw)
    def set_flat_mirror(self, path): self._flat = path

    def write_registry(self):
        lines = []
        if self._flat: lines.append(f'flat_mirror: "{self._flat}"')
        lines.append("mounts:")
        for m in self.mounts: lines.append(f'  - "{m}"')
        if self._projects:
            lines.append("projects:")
            for n, p in self._projects.items(): lines.append(f'  {n}: "{p}"')
        lines.append("sources:")
        for s in sorted({i["source"] for i in self._skills.values()}):
            lines.append(f'  {s}: "src {s}"')
        lines += ["categories:", '  workflow: "x"', "skills:"]
        for k, i in self._skills.items():
            extra = f', project: {i["project"]}' if i.get("project") else ""
            lines.append(f'  {k}: {{source: {i["source"]}, category: {i["category"]}, tier: {i["tier"]}{extra}}}')
        open(self.reg, "w").write("\n".join(lines) + "\n")
```

- [ ] **Step 2: 写 load_registry 失败测试**

```python
def test_load_registry_projects_and_flat(palace):
    palace.set_flat_mirror("/tmp/flat")
    palace.set_projects(syzh="/tmp/proj/syzh")
    palace.add_skill("biz", "mine", "workflow", "core")
    palace.add_skill("syzh-tool", "mine", "sql", "project", project="syzh")
    palace.write_registry(); sk = palace.reload()
    mounts, sources, skills, projects, flat = sk.load_registry()
    assert flat == "/tmp/flat"
    assert projects == {"syzh": "/tmp/proj/syzh"}
    assert skills["syzh-tool"]["project"] == "syzh"
    assert skills["syzh-tool"]["tier"] == "project"
    assert skills["biz"]["project"] is None
```

- [ ] **Step 3: 运行确认失败**

Run: `.venv/bin/python -m pytest tests/test_skillctl.py::test_load_registry_projects_and_flat -v`
Expected: FAIL（load_registry 返回 3 元组，无法解包 5 个）

- [ ] **Step 4: 改 load_registry（替换 38-57 行函数体）**

```python
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
    for m in re.finditer(
        r'^\s{2}([A-Za-z0-9_./-]+):\s*\{source:\s*([A-Za-z0-9_-]+),\s*'
        r'category:\s*([A-Za-z0-9_-]+),\s*tier:\s*([A-Za-z0-9_-]+)'
        r'(?:,\s*project:\s*([A-Za-z0-9_-]+))?', txt, re.M):
        key, src, cat, tier, proj = m.groups()
        skills[key] = dict(source=src, category=cat, tier=tier, project=proj)
    return mounts, sources, skills, projects, flat_mirror
```

- [ ] **Step 5: 更新所有调用者解包**

`sync`/`stats`/`doctor`/`fix` 里 `mounts, sources, skills = load_registry()` 改为 `mounts, sources, skills, projects, flat_mirror = load_registry()`（本 task 不改这些函数的逻辑，仅解包；未用变量可保留）。

- [ ] **Step 6: 运行确认通过 + 不回归**

Run: `.venv/bin/python -m pytest tests/test_skillctl.py -v`
Expected: 原 14 + 新 1 全绿。

- [ ] **Step 7: Commit**

```bash
git add tools/skillctl.py tests/conftest.py tests/test_skillctl.py
git commit -m "feat(skillctl): load_registry 支持 projects/flat_mirror/project 字段"
```

---

### Task 2: sync 生成扁平镜像（core 拍平）+ project 移出全局

**Files:**
- Modify: `tools/skillctl.py`（sync）
- Modify: `tests/test_skillctl.py`

**Interfaces:**
- Consumes: `load_registry`（Task 1）、`is_managed`、`skill_dir`、`mount_name`。
- Produces: `sync(dry)` 在 `flat_mirror`（若声明）下为每个 `core` skill 建拍平软链 `<flat_mirror>/<name>`；`tier:project` 不进 mounts、不进扁平镜像（现有 prune 会把已挂载的 project 移出）。

- [ ] **Step 1: 写失败测试**

```python
def test_sync_flat_mirror_core_only(palace, tmp_path):
    flat = str(tmp_path / "flat"); palace.set_flat_mirror(flat)
    palace.add_skill("c1", "mine", "workflow", "core")
    palace.add_skill("e1", "mine", "docs", "extra")
    palace.write_registry(); sk = palace.reload()
    sk.sync(dry=False)
    assert os.path.islink(os.path.join(flat, "c1"))         # core 进扁平镜像
    assert not os.path.lexists(os.path.join(flat, "e1"))    # extra 不进扁平镜像

def test_sync_project_not_in_global(palace):
    palace.set_projects(syzh="/tmp/x")
    palace.add_skill("p1", "mine", "sql", "project", project="syzh")
    palace.add_skill("c1", "mine", "workflow", "core")
    palace.write_registry(); sk = palace.reload()
    sk.sync(dry=False)
    assert not os.path.lexists(os.path.join(palace.mounts[0], "p1"))  # project 不进全局
    assert os.path.islink(os.path.join(palace.mounts[0], "c1"))
```

- [ ] **Step 2: 运行确认失败**

Run: `.venv/bin/python -m pytest tests/test_skillctl.py -v -k "flat_mirror or project_not_in_global"`
Expected: FAIL（sync 尚不处理 flat_mirror）

- [ ] **Step 3: 抽出软链辅助 + sync 增扁平镜像**

在 `sync` 之前加一个把「{key:info} 子集软链进某目标目录」的辅助，sync 末尾对 flat_mirror 调它（仅 core）。在 `tools/skillctl.py` 的 `sync` 函数末尾（最后一个 mount 循环之后）追加：

```python
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
```

（注：`tier:project` 因 `linked` 只取 core+extra，本就不进 mounts；若曾被挂载，mount 循环的 prune 会移出——现有逻辑已覆盖，无需改。）

- [ ] **Step 4: 运行确认通过**

Run: `.venv/bin/python -m pytest tests/test_skillctl.py -v`
Expected: 全绿。

- [ ] **Step 5: Commit**

```bash
git add tools/skillctl.py tests/test_skillctl.py
git commit -m "feat(skillctl): sync 生成 core 扁平镜像，project 移出全局"
```

---

### Task 3: mount/unmount <项目>

**Files:**
- Modify: `tools/skillctl.py`（新增 `mount`/`unmount`；main 加分支）
- Modify: `tests/test_skillctl.py`

**Interfaces:**
- Produces: `mount(proj, dry=False)` 把 `tier:project` 且 `project==proj` 的 skill 软链进 `<projects[proj]>/.claude/skills/<name>`；`unmount(proj, dry=False)` 移除该目录下受管软链。main 支持 `mount <proj>` / `unmount <proj>`。

- [ ] **Step 1: 写失败测试**

```python
def test_mount_unmount_project(palace, tmp_path):
    proj = str(tmp_path / "syzh"); os.makedirs(proj)
    palace.set_projects(syzh=proj)
    palace.add_skill("p1", "mine", "sql", "project", project="syzh")
    palace.write_registry(); sk = palace.reload()
    sk.mount("syzh", dry=False)
    link = os.path.join(proj, ".claude", "skills", "p1")
    assert os.path.islink(link) and os.path.exists(link)
    sk.unmount("syzh", dry=False)
    assert not os.path.lexists(link)

def test_mount_protects_foreign(palace, tmp_path):
    proj = str(tmp_path / "syzh"); os.makedirs(os.path.join(proj, ".claude", "skills"))
    foreign = os.path.join(proj, ".claude", "skills", "hand"); 
    os.symlink(str(tmp_path / "outside"), foreign)
    palace.set_projects(syzh=proj)
    palace.add_skill("p1", "mine", "sql", "project", project="syzh")
    palace.write_registry(); sk = palace.reload()
    sk.unmount("syzh", dry=False)
    assert os.path.lexists(foreign)   # 非受管手建软链不被 unmount 误删
```

- [ ] **Step 2: 运行确认失败**

Run: `.venv/bin/python -m pytest tests/test_skillctl.py -v -k "mount"`
Expected: FAIL（无 mount/unmount）

- [ ] **Step 3: 实现 mount/unmount（加在 fix 之后）**

```python
def _project_skill_dir(proj):
    _, _, _, projects, _ = load_registry()
    base = projects.get(proj)
    return os.path.join(base, ".claude", "skills") if base else None

def mount(proj, dry=False):
    mounts, sources, skills, projects, _ = load_registry()
    if proj not in projects:
        print(c(f"✗ 未声明的项目: {proj}（registry projects: 段缺）", "red")); return 1
    dstdir = os.path.join(projects[proj], ".claude", "skills")
    tag = c("[dry-run] ", "yel") if dry else ""
    if not dry: os.makedirs(dstdir, exist_ok=True)
    n = 0
    for k, i in sorted(skills.items()):
        if i["tier"] != "project" or i.get("project") != proj: continue
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
    print(c(f"{tag}✓ mount {proj}：{dstdir} 挂 {n} 个 project skill", "grn")); return 0

def unmount(proj, dry=False):
    _, _, _, projects, _ = load_registry()
    if proj not in projects:
        print(c(f"✗ 未声明的项目: {proj}", "red")); return 1
    dstdir = os.path.join(projects[proj], ".claude", "skills")
    tag = c("[dry-run] ", "yel") if dry else ""
    n = 0
    if os.path.isdir(dstdir):
        for e in os.listdir(dstdir):
            p = os.path.join(dstdir, e)
            if is_managed(p):
                if not dry and os.path.islink(p): os.unlink(p)
                n += 1
    print(c(f"{tag}✓ unmount {proj}：清 {n} 个受管软链", "grn")); return 0
```

- [ ] **Step 4: main 加 mount/unmount 分支**

`main` 里 `fix` 分支之后追加：

```python
    elif cmd == "mount" and len(args) > 1: sys.exit(mount(args[1], dry=("--dry" in args)))
    elif cmd == "unmount" and len(args) > 1: sys.exit(unmount(args[1], dry=("--dry" in args)))
```

- [ ] **Step 5: 运行确认通过**

Run: `.venv/bin/python -m pytest tests/test_skillctl.py -v`
Expected: 全绿。

- [ ] **Step 6: Commit**

```bash
git add tools/skillctl.py tests/test_skillctl.py
git commit -m "feat(skillctl): 新增 mount/unmount 项目级 skill 命令"
```

---

### Task 4: stats/doctor 显示 project + docstring/registry/governance 同步

**Files:**
- Modify: `tools/skillctl.py`（stats 显示 project/扁平镜像；doctor 加 project 校验；docstring）
- Modify: `registry.yaml`（加 flat_mirror 注释占位 + projects 段注释 + tier 说明四层）
- Modify: `docs/governance/content-assets/skills.md`（四层 tier + 扁平镜像 + 挂载名=name）
- Modify: `tests/test_skillctl.py`

**Interfaces:**
- Consumes: `load_registry`。
- Produces: stats 多一行 project 级统计；doctor 校验 `tier:project` 的 `project:` 必填且在 `projects:` 段中声明。

- [ ] **Step 1: 写 doctor 校验失败测试**

```python
def test_doctor_project_must_declare(palace):
    # tier:project 但 project 字段缺 / 或指向未声明项目
    palace.add_skill("p1", "mine", "sql", "project", project="ghost")  # ghost 未在 projects 段
    palace.write_registry(); sk = palace.reload()
    assert sk.doctor() == 1

def test_doctor_project_ok(palace, tmp_path):
    proj = str(tmp_path / "syzh"); os.makedirs(proj)
    palace.set_projects(syzh=proj)
    palace.add_skill("p1", "mine", "sql", "project", project="syzh")
    palace.write_registry(); sk = palace.reload()
    assert sk.doctor() == 0
```

- [ ] **Step 2: 运行确认失败**

Run: `.venv/bin/python -m pytest tests/test_skillctl.py -v -k doctor_project`
Expected: FAIL

- [ ] **Step 3: doctor 加 project 校验**

`doctor` 的 `by_tier`/category 循环里（`for k, i in skills.items():` 内、category 检查附近）追加：

```python
        if i["tier"] == "project":
            if not i.get("project"):
                problems.append(f"project 缺 project: 字段: {k}")
            elif i["project"] not in projects:
                problems.append(f"project 未声明: {k} → {i['project']}（projects: 段缺）")
```

（`projects` 已在 `doctor` 开头的 `mounts, sources, skills, projects, flat_mirror = load_registry()` 解包到位。）

- [ ] **Step 4: stats 增 project/扁平镜像统计**

`stats` 的 `by_tier` 初值加 `"project": 0`；总览行加 project 数；挂载健康下方加一段：

```python
    # project 级 + 扁平镜像
    proj_skills = [k for k, i in skills.items() if i["tier"] == "project"]
    if proj_skills or projects:
        print(c("\n  项目级 skill（移出全局，opt-in mount）", "dim"))
        for k in sorted(proj_skills):
            print(f"    {mount_name(k):<22} → 项目 {skills[k].get('project')}")
    if flat_mirror:
        print(c(f"\n  扁平镜像（core 拍平默认层）: {flat_mirror}", "dim"))
```

（`by_tier` 用 `by_tier.get(i['tier'],0)+1` 容错任意 tier；总览行 print 加 `/ project {by_tier.get('project',0)}`。）

- [ ] **Step 5: 文档同步**

- `tools/skillctl.py` docstring：用法段加 `mount/unmount <项目>`；tier 说明改四层；提扁平镜像。
- `registry.yaml`：顶部加 `# flat_mirror: ~/.agents/skills`（注释占位，说明 core 拍平默认层、本轮机制就绪不强制启用）；加 `projects:` 段注释模板；tier 注释列全四层（core/extra/project/parked）。
- `docs/governance/content-assets/skills.md`：tier 表加 **project** 第四层行（移出全局、opt-in mount）+ 新增「扁平镜像（core 默认加载层，不包 core 目录层）」与「**挂载名 = SKILL.md `name`**（斜杠菜单按 name 显示，ADR-0006 实测）」两小节，链接 ADR-0006。

- [ ] **Step 6: 运行全量 + 真实 dry 自检**

Run: `.venv/bin/python -m pytest tests/test_skillctl.py -v`（全绿）
Run: `.venv/bin/python tools/skillctl.py`（stats 不报错，能显示四层 + 项目段为空时不崩）
Run: `.venv/bin/python tools/skillctl.py doctor`（对真实仓库照常，project 段当前为空不影响）

- [ ] **Step 7: Commit**

```bash
git add tools/skillctl.py registry.yaml docs/governance/content-assets/skills.md tests/test_skillctl.py
git commit -m "feat(skillctl): stats/doctor 支持 project，文档同步四层 tier 与扁平镜像"
```

---

## 自检清单（执行者完成后核对）

- [ ] `.venv/bin/python -m pytest tests/ -v` 全绿（原 16 + 新增 project/flat 测试）。
- [ ] `load_registry` 返回 5 元组，所有调用者解包无遗漏。
- [ ] 扁平镜像只放 core、拍平不包 core 层；project 不进 mounts/扁平镜像。
- [ ] mount/unmount 对非受管软链保护跳过（零误删）。
- [ ] 全程未向真实 `~/.agents`、`~/.claude`、`~/.codex` 落盘（测试均 tmp 隔离）。
- [ ] governance/skills.md 含四层 tier + 扁平镜像 + 挂载名=name + ADR-0006 链接。
