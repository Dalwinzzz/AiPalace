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
        self._skills = {}   # key -> dict(source,category,tier,project)
        self._projects = {}
        self._flat = None
        self._mp = monkeypatch

    def add_skill(self, key, source, category, tier, cls="mine", with_skillmd=True, source_doc=False, project=None):
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
        lines += ["sources:"]
        for s in sorted({i["source"] for i in self._skills.values()}):
            lines.append(f'  {s}: "src {s}"')
        lines += ["categories:", '  workflow: "x"', "skills:"]
        for k, i in self._skills.items():
            extra = f', project: {i["project"]}' if i.get("project") else ""
            lines.append(f'  {k}: {{source: {i["source"]}, category: {i["category"]}, tier: {i["tier"]}{extra}}}')
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
