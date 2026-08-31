# tests/test_skillctl.py
import os

# ── sync 测试 ──────────────────────────────────────────────────────────────

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

# ── is_managed 测试 ────────────────────────────────────────────────────────

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

# ── doctor 门槛校验测试 ────────────────────────────────────────────────────

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

def test_doctor_enterprise_needs_source_doc(palace):
    palace.add_skill("acme/baz", "acme", "method", "parked", cls="enterprise", source_doc=False)
    palace.write_registry(); sk = palace.reload()
    assert sk.doctor() == 1

# ── doctor 悬挂软链 + 孤儿检测 ────────────────────────────────────────────

def test_doctor_dangling_link(palace, capsys):
    import shutil as _sh
    d = palace.add_skill("foo", "mine", "workflow", "core")
    palace.write_registry(); sk = palace.reload()
    sk.sync(dry=False)
    _sh.rmtree(d)        # 真身被删 → 软链悬挂
    assert sk.doctor() == 1
    out = capsys.readouterr().out
    assert "悬挂软链" in out

def test_doctor_orphan_is_warning_not_error(palace, capsys):
    palace.add_skill("foo", "mine", "workflow", "core")
    palace.write_registry(); sk = palace.reload()
    # 造一个未登记真身
    orphan = os.path.join(palace.skills, "mine", "ghost")
    os.makedirs(orphan); open(os.path.join(orphan, "SKILL.md"), "w").write("---\nname: ghost\n---\n")
    rc = sk.doctor()
    out = capsys.readouterr().out
    assert rc == 0 and "孤儿" in out

# ── fix 测试 ──────────────────────────────────────────────────────────────

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

# ── is_managed 兼容旧 .aipalace-managed 标记 ──────────────────────────────

def test_is_managed_marker_dir(palace):
    palace.write_registry(); sk = palace.reload()
    d = os.path.join(sk.SKILLS, "legacy"); os.makedirs(d)
    open(os.path.join(d, ".aipalace-managed"), "w").write("x")
    assert sk.is_managed(d) is True

# ── sync 扁平镜像 + project 不进全局 ──────────────────────────────────────

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

# ── mount / unmount 测试 ──────────────────────────────────────────────────

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

def test_mount_multi_project(palace, tmp_path):
    """一个 project skill 声明多个项目（逗号分隔）→ mount 各项目均建软链。"""
    a = str(tmp_path / "a"); b = str(tmp_path / "b"); os.makedirs(a); os.makedirs(b)
    palace.set_projects(pa=a, pb=b)
    palace.add_skill("p1", "mine", "sql", "project", project="pa,pb")
    palace.write_registry(); sk = palace.reload()
    _, _, skills, _, _ = sk.load_registry()
    assert skills["p1"]["project"] == ["pa", "pb"]      # 逗号分隔解析成 list
    sk.mount("pa", dry=False); sk.mount("pb", dry=False)
    la = os.path.join(a, ".claude", "skills", "p1")
    lb = os.path.join(b, ".claude", "skills", "p1")
    assert os.path.islink(la) and os.path.exists(la)     # 挂到项目 a
    assert os.path.islink(lb) and os.path.exists(lb)     # 也挂到项目 b
    assert sk.doctor() == 0                              # 两 project key 均声明 → 绿

def test_doctor_multi_project_partial_undeclared(palace, tmp_path):
    """多项目中有一个未在 projects: 声明 → doctor 报错。"""
    a = str(tmp_path / "a"); os.makedirs(a)
    palace.set_projects(pa=a)                            # pb 未声明
    palace.add_skill("p1", "mine", "sql", "project", project="pa,pb")
    palace.write_registry(); sk = palace.reload()
    assert sk.doctor() == 1

def test_mount_protects_foreign(palace, tmp_path):
    proj = str(tmp_path / "syzh"); os.makedirs(os.path.join(proj, ".claude", "skills"))
    foreign = os.path.join(proj, ".claude", "skills", "hand")
    os.symlink(str(tmp_path / "outside"), foreign)
    palace.set_projects(syzh=proj)
    palace.add_skill("p1", "mine", "sql", "project", project="syzh")
    palace.write_registry(); sk = palace.reload()
    sk.unmount("syzh", dry=False)
    assert os.path.lexists(foreign)   # 非受管手建软链不被 unmount 误删

# ── doctor project 校验 ───────────────────────────────────────────────────

def test_doctor_project_must_declare(palace):
    # tier:project 但 project 字段指向未声明项目（ghost 未在 projects 段）
    palace.add_skill("p1", "mine", "sql", "project", project="ghost")
    palace.write_registry(); sk = palace.reload()
    assert sk.doctor() == 1

def test_doctor_project_ok(palace, tmp_path):
    proj = str(tmp_path / "syzh"); os.makedirs(proj)
    palace.set_projects(syzh=proj)
    palace.add_skill("p1", "mine", "sql", "project", project="syzh")
    palace.write_registry(); sk = palace.reload()
    assert sk.doctor() == 0

# ── load_registry projects/flat_mirror/project 字段 ───────────────────────

# ── git_roots 枚举（ADR-0010）────────────────────────────────────────────

def test_git_roots_finds_nested_independent_repos(palace, tmp_path):
    sk = palace.reload()
    base = tmp_path / "umb"
    r1 = base / "a" / "repo1"; r2 = base / "b" / "c" / "repo2"
    for r in (r1, r2): (r / ".git").mkdir(parents=True)
    roots = set(sk.git_roots(str(base)))
    assert str(r1) in roots and str(r2) in roots          # 不同深度的独立仓都命中

def test_git_roots_skips_noise_dirs(palace, tmp_path):
    sk = palace.reload()
    base = tmp_path / "umb"
    noise = base / "node_modules" / "pkg"; (noise / ".git").mkdir(parents=True)
    real = base / "svc"; (real / ".git").mkdir(parents=True)
    roots = set(sk.git_roots(str(base)))
    assert str(real) in roots
    assert str(noise) not in roots                        # node_modules 内的 .git 被剪枝

def test_git_roots_skips_claude_worktrees(palace, tmp_path):
    sk = palace.reload()
    repo = tmp_path / "umb" / "svc"; (repo / ".git").mkdir(parents=True)
    wt = repo / ".claude" / "worktrees" / "task1"; (wt / ".git").mkdir(parents=True)
    roots = set(sk.git_roots(str(tmp_path / "umb")))
    assert str(repo) in roots
    assert str(wt) not in roots                           # .claude/worktrees 临时仓不挂

def test_git_roots_dotgit_as_file(palace, tmp_path):
    sk = palace.reload()
    base = tmp_path / "umb"; sub = base / "submod"; sub.mkdir(parents=True)
    (sub / ".git").write_text("gitdir: /elsewhere")       # submodule/worktree 形态
    assert str(sub) in set(sk.git_roots(str(base)))

def test_git_roots_base_missing_returns_empty(palace, tmp_path):
    sk = palace.reload()
    assert sk.git_roots(str(tmp_path / "nope")) == []

# ── mount/unmount 递归至 git 仓根（ADR-0010）─────────────────────────────

def test_mount_recurses_into_nested_git_root(palace, tmp_path):
    umbrella = str(tmp_path / "ZhiJin")
    sub = os.path.join(umbrella, "SunkidCloud", "skcactivity")
    os.makedirs(os.path.join(sub, ".git"))                # 子目录是独立 git 仓
    palace.set_projects(zhijin=umbrella)
    palace.add_skill("p1", "mine", "sql", "project", project="zhijin")
    palace.write_registry(); sk = palace.reload()
    sk.mount("zhijin", dry=False)
    assert os.path.islink(os.path.join(umbrella, ".claude", "skills", "p1"))   # umbrella
    assert os.path.islink(os.path.join(sub, ".claude", "skills", "p1"))        # 子 git 根

def test_mount_no_recurse_umbrella_only(palace, tmp_path):
    umbrella = str(tmp_path / "ZhiJin")
    sub = os.path.join(umbrella, "svc"); os.makedirs(os.path.join(sub, ".git"))
    palace.set_projects(zhijin=umbrella)
    palace.add_skill("p1", "mine", "sql", "project", project="zhijin")
    palace.write_registry(); sk = palace.reload()
    sk.mount("zhijin", dry=False, recurse=False)
    assert os.path.islink(os.path.join(umbrella, ".claude", "skills", "p1"))
    assert not os.path.lexists(os.path.join(sub, ".claude", "skills", "p1"))   # --no-recurse 不下沉

def test_unmount_recurse_cleans_nested_git_root(palace, tmp_path):
    umbrella = str(tmp_path / "ZhiJin")
    sub = os.path.join(umbrella, "svc"); os.makedirs(os.path.join(sub, ".git"))
    palace.set_projects(zhijin=umbrella)
    palace.add_skill("p1", "mine", "sql", "project", project="zhijin")
    palace.write_registry(); sk = palace.reload()
    sk.mount("zhijin", dry=False)
    sub_link = os.path.join(sub, ".claude", "skills", "p1")
    assert os.path.islink(sub_link)
    sk.unmount("zhijin", dry=False)
    assert not os.path.lexists(sub_link)                  # 子 git 根的受管软链也被清

def test_mount_recurse_protects_foreign_in_git_root(palace, tmp_path):
    umbrella = str(tmp_path / "ZhiJin")
    sub = os.path.join(umbrella, "svc")
    skdir = os.path.join(sub, ".claude", "skills"); os.makedirs(skdir)
    os.makedirs(os.path.join(sub, ".git"))
    foreign = os.path.join(skdir, "hand")
    os.symlink(str(tmp_path / "outside"), foreign)        # 子 git 根内用户手建软链
    palace.set_projects(zhijin=umbrella)
    palace.add_skill("p1", "mine", "sql", "project", project="zhijin")
    palace.write_registry(); sk = palace.reload()
    sk.mount("zhijin", dry=False)
    sk.unmount("zhijin", dry=False)
    assert os.path.lexists(foreign)                       # 非受管手建物不被误删

def test_load_registry_projects_and_flat(palace):
    palace.set_flat_mirror("/tmp/flat")
    palace.set_projects(syzh="/tmp/proj/syzh")
    palace.add_skill("biz", "mine", "workflow", "core")
    palace.add_skill("syzh-tool", "mine", "sql", "project", project="syzh")
    palace.write_registry(); sk = palace.reload()
    mounts, sources, skills, projects, flat = sk.load_registry()
    assert flat == "/tmp/flat"
    assert projects == {"syzh": "/tmp/proj/syzh"}
    assert skills["syzh-tool"]["project"] == ["syzh"]   # 多值支持：project 统一存 list
    assert skills["syzh-tool"]["tier"] == "project"
    assert skills["biz"]["project"] == []
