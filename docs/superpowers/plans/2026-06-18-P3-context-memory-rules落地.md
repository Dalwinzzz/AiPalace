# P3 context/memory/rules 落地 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax.

**Goal:** 把 `AiPalace/context/` 按治理规范重组为四分内容资产的物理结构——rules 正名、context 拆 self+INDEX、memory 三级 5 域+INDEX，并准备双工具 SessionStart hook 脚本（注入 INDEX）。

**Architecture:** `context/` 作为个人上下文层容器，下设：context 自身的 `INDEX.md` + `self/<what>.md`（关于"我"，软自选）、`rules/`（硬配置域规约）、`memory/`（INDEX + 三级 5 域知识）。hook 脚本放 `tools/hooks/`，仓库内准备、不注册到现役 `~/.claude`/`~/.codex`（注册属 SOT 切换 final-spec）。

**Tech Stack:** Markdown 内容 + Python hook 脚本（stdlib）。重组用 `git mv` 保留历史。验证 = 结构正确 + 原内容零丢失 + INDEX 链接有效 + hook 脚本 pytest。

## Global Constraints

- 只动 `AiPalace/context/` 与 `AiPalace/tools/hooks/`，**不碰现役 `~/.claude`、`~/.codex`、`~/.agents` 配置**（SOT 切换属 final-spec）。
- 重组**零内容丢失**：拆分/移动后，原 CLAUDE.md / memory 各文件的每条信息都要落到某个新文件，可被 INDEX 指向。
- memory L1 域封闭 = `projects / tech / workflow / reference / enterprise`；enterprise 二级=公司名、三级=项目/模块.md。
- INDEX = 条件决策树（when→what）：context/INDEX 指向 self/*；memory/INDEX 指向 memory 三级条目。整树注入（裁剪留演进）。
- rules 保留 `paths:` frontmatter（硬触发条件）。
- 移动用 `git mv`。commit 用 `<type>(<scope>): <subject>`。

---

### Task 1: rules 正名（建 context/rules/）

**Files:**
- Move: `context/java-spring.md` → `context/rules/java-spring.md`
- Move: `context/frontend-web.md` → `context/rules/frontend-web.md`
- Create: `context/rules/README.md`

**Interfaces:**
- Produces: `context/rules/` 目录，含两个硬配置域规约 + 一个说明。

- [ ] **Step 1: git mv 两个 rule 文件**

```bash
cd /Users/dalwin/Library/CodeRepo/AI/AiPalace
mkdir -p context/rules
git mv context/java-spring.md context/rules/java-spring.md
git mv context/frontend-web.md context/rules/frontend-web.md
```

- [ ] **Step 2: 写 context/rules/README.md**

简短说明：rules = 硬配置域规约（path-scoped 匹配即必注），区别于 self（软自选）与 memory（按需）。列当前两条 rule 及其 `paths:` 触发条件（读两文件的 frontmatter 填）。链接 `docs/governance/content-assets/rules.md` 规范。

- [ ] **Step 3: 验证**

确认两 rule 文件 frontmatter（`paths:`）完整保留；`grep -l "paths:" context/rules/*.md` 列出两文件。

- [ ] **Step 4: Commit**

```bash
git add -A context/rules
git commit -m "refactor(context): rules 正名，java-spring/frontend-web 归 context/rules"
```

---

### Task 2: context 拆 self + INDEX

**Files:**
- Create: `context/self/identity.md`、`context/self/tech-stack.md`、`context/self/workflow-style.md`
- Create: `context/INDEX.md`
- Remove: `context/CLAUDE.md`（内容拆分后删；信息零丢失）
- Reference: 现有 `context/CLAUDE.md`（53 行，含 Me/项目/技术栈/本地配置/AI工作流/术语）

**Interfaces:**
- Consumes: 无。
- Produces: `context/self/<what>.md`（关于"我"的画像，按维度拆）；`context/INDEX.md`（条件决策树，约束 when 看哪个 self/*）。

- [ ] **Step 1: 拆 CLAUDE.md 成 self/<what>.md**

Read context/CLAUDE.md，按维度拆（零丢失）：
- `self/identity.md`：Me（身份/角色/Go 转型目标）+ 项目代号表（syzh/skc/Go转型 的一句话定位，深度指向 memory）。
- `self/tech-stack.md`：技术栈表（Java 主力 / Go 在学 / 中间件 / 工具）。
- `self/workflow-style.md`：AI 工作流（采纳的 skill 列表 + 决策点①②）+ 常用术语表（指向 memory/reference/glossary 深度）。
- 「⚠️ 本地关键配置（Maven/JDK）」这种**硬约束**——它其实是 rules 性质（写 Java 必遵守），放进 `context/rules/java-spring.md`（若该文件已含则不重复；只在 self/identity 留一句指针"Java 本地配置见 rules/java-spring.md"）。

- [ ] **Step 2: 写 context/INDEX.md（条件决策树）**

写一棵 always-on 注入的轻量决策树，形如「当任务涉及 X → Read context/self/Y.md」：
- 始终：identity（我是谁）轻量可参考。
- 涉及技术选型/栈相关 → self/tech-stack.md。
- 涉及 AI 工作流/skill 编排/提交决策 → self/workflow-style.md。
- 注明：rules（java-spring/frontend-web）由 path-scoped 硬触发，不在本 INDEX；深度项目/术语知识在 memory/INDEX.md。

- [ ] **Step 3: 删 CLAUDE.md（确认零丢失后）**

逐节核对 CLAUDE.md 每块都已落到 self/* 或 rules/ 或被 INDEX 指向，再 `git rm context/CLAUDE.md`。

- [ ] **Step 4: 验证**

`grep -r "syzh\\|Go 转型\\|决策点\\|Maven" context/self context/rules` 确认关键信息未丢；INDEX.md 链接的 self/* 文件均存在。

- [ ] **Step 5: Commit**

```bash
git add -A context/
git commit -m "refactor(context): CLAUDE.md 拆为 self/<what> + context/INDEX 决策树"
```

---

### Task 3: memory 三级 5 域重组 + INDEX

**Files:**
- Move/Create: `context/memory/enterprise/zhijin/syzh.md`、`context/memory/projects/career/go-transition.md`、`context/memory/workflow/ai-workflow.md`、`context/memory/reference/glossary.md`、`context/memory/tech/.gitkeep`
- Create: `context/memory/INDEX.md`
- Reference: 现有 `context/memory/{ai-workflow.md, glossary.md, projects/{syzh,go-transition}.md}`

**Interfaces:**
- Produces: memory 三级 5 域结构 + `memory/INDEX.md`（同构多级决策树）。

- [ ] **Step 1: git mv 重组现有 memory 文件到 5 域**

```bash
cd /Users/dalwin/Library/CodeRepo/AI/AiPalace/context/memory
mkdir -p enterprise/zhijin projects/career workflow reference tech
git mv projects/syzh.md enterprise/zhijin/syzh.md
git mv projects/go-transition.md projects/career/go-transition.md
git mv ai-workflow.md workflow/ai-workflow.md
git mv glossary.md reference/glossary.md
rmdir projects 2>/dev/null || true
touch tech/.gitkeep
```
（注：syzh 属智金公司项目 → enterprise/zhijin；go-transition 是个人职业转型 → projects/career；tech 暂空浅填。）

- [ ] **Step 2: 写 context/memory/INDEX.md（同构多级决策树）**

写 always-on 注入的 memory 决策树，命中到具体条目才 pull：
- [域 projects·个人项目] 涉及 Go 转型/职业 → projects/career/go-transition.md
- [域 enterprise·公司项目] 涉及 智金/SKC/syzh/智慧托育 → enterprise/zhijin/syzh.md
- [域 tech·技术深度] 涉及 Go/Java 深度知识点 → tech/*（暂空，浅填）
- [域 workflow] 涉及 AI 工作流细节 → workflow/ai-workflow.md
- [域 reference] 遇术语不解 → reference/glossary.md
注明三门并集触发（cwd 打分 ∪ 模型读树语义 ∪ 任务描述匹配）；当前整树注入。

- [ ] **Step 3: 验证**

`find context/memory -name '*.md'` 确认 5 域结构正确、4 个原内容文件都在新位置；INDEX.md 指向的条目均存在；原 memory 顶层无遗留 ai-workflow.md/glossary.md。

- [ ] **Step 4: Commit**

```bash
git add -A context/memory
git commit -m "refactor(context): memory 重组三级 5 域 + memory/INDEX 决策树"
```

---

### Task 4: 双工具 SessionStart hook 脚本（注入 INDEX）

**Files:**
- Create: `tools/hooks/inject_index.py`
- Create: `tests/test_inject_index.py`
- Reference: spec §6.5/§7.1（注入机制）

**Interfaces:**
- Produces: `inject_index(context_root) -> str`（读 context/INDEX.md + memory/INDEX.md，拼成注入文本）；CLI 入口按双工具 SessionStart hook 约定输出（Claude `additionalContext` JSON / Codex 等价）。

- [ ] **Step 1: 写失败测试**

```python
# tests/test_inject_index.py
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools", "hooks"))

def test_inject_index_combines_both(tmp_path):
    import inject_index
    ctx = tmp_path / "context"; (ctx / "memory").mkdir(parents=True)
    (ctx / "INDEX.md").write_text("# context INDEX\n- identity\n")
    (ctx / "memory" / "INDEX.md").write_text("# memory INDEX\n- glossary\n")
    out = inject_index.inject_index(str(ctx))
    assert "context INDEX" in out and "memory INDEX" in out

def test_inject_index_missing_returns_empty(tmp_path):
    import inject_index
    out = inject_index.inject_index(str(tmp_path / "nope"))
    assert out == ""
```

- [ ] **Step 2: 运行确认失败**

Run: `.venv/bin/python -m pytest tests/test_inject_index.py -v`
Expected: FAIL（inject_index 不存在）

- [ ] **Step 3: 实现 inject_index.py**

```python
#!/usr/bin/env python3
"""SessionStart hook：把 context/INDEX.md + memory/INDEX.md 拼成 always-on 注入文本。
双工具通用：Claude 经 additionalContext、Codex 经 SessionStart hook 输出同一文本。
仓库内准备；实际注册到 ~/.claude/hooks、~/.codex/hooks 属 SOT 切换 final-spec。"""
import os, json, sys

def inject_index(context_root):
    parts = []
    for rel in ("INDEX.md", os.path.join("memory", "INDEX.md")):
        p = os.path.join(context_root, rel)
        if os.path.isfile(p):
            parts.append(open(p, encoding="utf-8").read().strip())
    return "\n\n".join(parts)

def main():
    root = os.environ.get("AIPALACE_CONTEXT") or os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "context")
    text = inject_index(root)
    # Claude SessionStart 约定：additionalContext
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "SessionStart", "additionalContext": text}}, ensure_ascii=False))

if __name__ == "__main__":
    main()
```

- [ ] **Step 4: 运行确认通过**

Run: `.venv/bin/python -m pytest tests/test_inject_index.py -v`
Expected: 2 passed

- [ ] **Step 5: 真身自检（仓库内，不注册）**

Run: `AIPALACE_CONTEXT=context .venv/bin/python tools/hooks/inject_index.py`
Expected: 打印含 context INDEX + memory INDEX 的 JSON。确认能读到 Task 2/3 写的两个 INDEX。

- [ ] **Step 6: Commit**

```bash
git add tools/hooks/inject_index.py tests/test_inject_index.py
git commit -m "feat(hooks): 双工具 SessionStart 注入 context/memory INDEX 脚本"
```

---

## Self-Review（执行者完成后核对）

- [ ] context/ 下结构：INDEX.md + self/ + rules/ + memory/，CLAUDE.md 已删且内容零丢失。
- [ ] memory/ 五域结构正确，4 个原内容文件各就位，无顶层遗留。
- [ ] context/INDEX.md 与 memory/INDEX.md 都是 when→what 决策树，指向的文件均存在。
- [ ] inject_index 测试通过，真身自检能拼出两个 INDEX。
- [ ] 全程未触碰 ~/.claude、~/.codex、~/.agents。
