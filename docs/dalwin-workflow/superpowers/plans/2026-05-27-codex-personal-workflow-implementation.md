# Codex Personal Workflow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bring Codex / Codex CLI into the personal AI workflow by repairing current drift, aligning Codex configuration with official control surfaces, and establishing cross-tool reconciliation with Claude.

**Architecture:** Codex uses its own native layers: `AGENTS.md` for stable always-on protocol, `config.toml` for features/MCP/project settings, `hooks.json` plus focused scripts for dynamic hints, `memories/` for auxiliary recall, `rules/` only for sandbox-external command approvals, and symlinked skills for shared source-of-truth. Claude and Codex share workflow intent and skill source, but do not share implementation primitives blindly.

**Tech Stack:** Codex CLI 0.130.0, TOML, JSON, Python 3 stdlib hooks, Markdown docs/logs, macOS symlinks, Git.

---

## Scope Check

This plan covers one coherent configuration migration: Codex personal workflow alignment. It touches multiple surfaces, but they are sequential and jointly verifiable: first repair drift, then codify instructions/memory boundaries, then add hooks, then converge skills and document the result. No product code is changed.

## File Structure

**Design input:**

- Read: `/Users/dalwin/Documents/AI/dalwin-workflow/docs/superpowers/specs/2026-05-27-codex-personal-workflow-design.md`

**Codex configuration files:**

- Modify: `/Users/dalwin/.codex/config.toml`  
  Responsibility: Codex feature flags, MCP server entries, plugin/project/desktop settings.
- Modify: `/Users/dalwin/.codex/AGENTS.md`  
  Responsibility: short, stable, always-on Codex behavior protocol.
- Modify: `/Users/dalwin/.codex/hooks.json`  
  Responsibility: hook event registration; preserve existing codeisland hooks.
- Create: `/Users/dalwin/.codex/hooks/sessionstart-domain.py`  
  Responsibility: deterministic cwd-based work-domain confidence hint.
- Create: `/Users/dalwin/.codex/hooks/userprompt-workflow-router.py`  
  Responsibility: deterministic user-prompt keyword hint for workflow routing.
- Create: `/Users/dalwin/.codex/hooks/precompact-memory-hint.py`  
  Responsibility: non-blocking manual compact hint.
- Modify: `/Users/dalwin/.codex/skills/git-merge-conductor`  
  Responsibility: symlink view to shared skill source.
- Inspect and modify only when diff is empty: `/Users/dalwin/.codex/skills/req-to-ai-spec`  
  Responsibility: decide whether Codex private copy can become a symlink to SOT.
- Read: `/Users/dalwin/.codex/rules/git-commit-message.rules`  
  Responsibility: confirm it remains an approval hint only.

**Shared skill source:**

- Read: `/Users/dalwin/.agents/skills/`
- Read: `/Users/dalwin/Library/CodeRepo/AI/awesome-skills/`

**Traceability logs in git repo:**

- Create: `/Users/dalwin/Documents/AI/dalwin-workflow/docs/superpowers/plans/logs/codex-phase-0-drift-repair.md`
- Create: `/Users/dalwin/Documents/AI/dalwin-workflow/docs/superpowers/plans/logs/codex-phase-1-agents-memory.md`
- Create: `/Users/dalwin/Documents/AI/dalwin-workflow/docs/superpowers/plans/logs/codex-phase-2-hooks.md`
- Create: `/Users/dalwin/Documents/AI/dalwin-workflow/docs/superpowers/plans/logs/codex-phase-3-skills-final.md`

---

## Phase 0: Baseline And Drift Repair

### Task 0.1: Capture Codex Baseline

**Files:**
- Read: `/Users/dalwin/.codex/config.toml`
- Read: `/Users/dalwin/.codex/AGENTS.md`
- Read: `/Users/dalwin/.codex/hooks.json`
- Read: `/Users/dalwin/.codex/skills/`

- [ ] **Step 1: Confirm Codex version**

Run:

```bash
codex --version
```

Expected:

```text
codex-cli 0.130.0
```

- [ ] **Step 2: Capture MCP state**

Run:

```bash
codex mcp list
```

Expected before repair: output may include `node_repl`; if `context7` or `openaiDeveloperDocs` already exists, record that in the Phase 0 log and skip adding that server in Task 0.2.

- [ ] **Step 3: Capture feature state**

Run:

```bash
codex features list
```

Expected: output contains `hooks stable true`. If it contains `memories experimental false`, Task 1.2 will enable it.

- [ ] **Step 4: Capture current skill links**

Run:

```bash
ls -la /Users/dalwin/.codex/skills
```

Expected: output shows `git-merge-conductor`, `spec-architect`, `docker-best-practices`, `req-to-ai-spec`, and `hatch-pet`.

- [ ] **Step 5: Check git working tree for traceability repo**

Run:

```bash
git -C /Users/dalwin/Documents/AI status --short
```

Expected: no staged files unless this plan file is being committed before execution. Existing unrelated changes must be left untouched.

### Task 0.2: Restore Codex MCP Servers

**Files:**
- Modify through CLI: `/Users/dalwin/.codex/config.toml`

- [ ] **Step 1: Add Context7 MCP if missing**

Run:

```bash
codex mcp get context7
```

Expected if missing:

```text
Error: No MCP server named 'context7' found.
```

If missing, run:

```bash
codex mcp add context7 -- npx -y @upstash/context7-mcp
```

Expected: command exits with status `0`.

If this command fails with DNS, registry, or network access errors, rerun the same command with escalated permissions. Expected after approval: command exits with status `0`.

- [ ] **Step 2: Add OpenAI Developer Docs MCP if missing**

Run:

```bash
codex mcp get openaiDeveloperDocs
```

Expected if missing:

```text
Error: No MCP server named 'openaiDeveloperDocs' found.
```

If missing, run:

```bash
codex mcp add openaiDeveloperDocs --url https://developers.openai.com/mcp
```

Expected: command exits with status `0`.

- [ ] **Step 3: Verify MCP servers**

Run:

```bash
codex mcp list
```

Expected: output contains all three names:

```text
node_repl
context7
openaiDeveloperDocs
```

Run:

```bash
codex mcp get context7
codex mcp get openaiDeveloperDocs
```

Expected:

- `context7` uses command `npx` and args `-y @upstash/context7-mcp`.
- `openaiDeveloperDocs` uses URL `https://developers.openai.com/mcp`.

### Task 0.3: Normalize Codex Hook Feature Flag

**Files:**
- Modify: `/Users/dalwin/.codex/config.toml`

- [ ] **Step 1: Inspect current feature block**

Run:

```bash
sed -n '1,80p' /Users/dalwin/.codex/config.toml
```

Expected before repair: `[features]` may contain `codex_hooks = true`.

- [ ] **Step 2: Patch feature key**

Apply this patch if `codex_hooks = true` is present:

```patch
*** Begin Patch
*** Update File: /Users/dalwin/.codex/config.toml
@@
 [features]
-codex_hooks = true
+hooks = true
 js_repl = false
*** End Patch
```

If `[features]` already contains `hooks = true`, do not add a duplicate.

- [ ] **Step 3: Verify feature state**

Run:

```bash
codex features list
```

Expected: output contains:

```text
hooks                                   stable             true
```

### Task 0.4: Repair High-Confidence Skill Symlink Drift

**Files:**
- Modify: `/Users/dalwin/.codex/skills/git-merge-conductor`
- Inspect: `/Users/dalwin/.codex/skills/req-to-ai-spec`
- Inspect: `/Users/dalwin/Library/CodeRepo/AI/awesome-skills/req-to-ai-spec`

- [ ] **Step 1: Confirm git-merge-conductor current target**

Run:

```bash
readlink /Users/dalwin/.codex/skills/git-merge-conductor
```

Expected before repair may be:

```text
/Users/dalwin/Documents/AI/skills/git-merge-conductor
```

- [ ] **Step 2: Backup current symlink target record**

Run:

```bash
mkdir -p /Users/dalwin/.codex/skill-link-backups/2026-05-27
readlink /Users/dalwin/.codex/skills/git-merge-conductor > /Users/dalwin/.codex/skill-link-backups/2026-05-27/git-merge-conductor.before
```

Expected: backup file exists and contains the old target path.

- [ ] **Step 3: Replace git-merge-conductor symlink**

Run:

```bash
rm /Users/dalwin/.codex/skills/git-merge-conductor
ln -s /Users/dalwin/Library/CodeRepo/AI/awesome-skills/git-merge-conductor /Users/dalwin/.codex/skills/git-merge-conductor
```

Expected:

```bash
readlink /Users/dalwin/.codex/skills/git-merge-conductor
```

prints:

```text
/Users/dalwin/Library/CodeRepo/AI/awesome-skills/git-merge-conductor
```

- [ ] **Step 4: Diff req-to-ai-spec Codex copy against SOT**

Run:

```bash
diff -ru /Users/dalwin/.codex/skills/req-to-ai-spec /Users/dalwin/Library/CodeRepo/AI/awesome-skills/req-to-ai-spec
```

Expected if identical: command exits with status `0` and no output.

If identical, run:

```bash
mkdir -p /Users/dalwin/.codex/skill-link-backups/2026-05-27
mv /Users/dalwin/.codex/skills/req-to-ai-spec /Users/dalwin/.codex/skill-link-backups/2026-05-27/req-to-ai-spec.codex-copy
ln -s /Users/dalwin/Library/CodeRepo/AI/awesome-skills/req-to-ai-spec /Users/dalwin/.codex/skills/req-to-ai-spec
```

Expected:

```bash
readlink /Users/dalwin/.codex/skills/req-to-ai-spec
```

prints:

```text
/Users/dalwin/Library/CodeRepo/AI/awesome-skills/req-to-ai-spec
```

If diff is non-empty, do not replace the directory. Save the diff for review:

```bash
diff -ru /Users/dalwin/.codex/skills/req-to-ai-spec /Users/dalwin/Library/CodeRepo/AI/awesome-skills/req-to-ai-spec > /Users/dalwin/.codex/skill-link-backups/2026-05-27/req-to-ai-spec.diff
```

Expected: diff file exists; Phase 0 log records that `req-to-ai-spec` remains Codex-private until the diff is reviewed.

### Task 0.5: Write And Commit Phase 0 Log

**Files:**
- Create: `/Users/dalwin/Documents/AI/dalwin-workflow/docs/superpowers/plans/logs/codex-phase-0-drift-repair.md`

- [ ] **Step 1: Create Phase 0 log**

Apply this patch, editing only the command-output bullet values to match the verified outputs from this execution:

```patch
*** Begin Patch
*** Add File: /Users/dalwin/Documents/AI/dalwin-workflow/docs/superpowers/plans/logs/codex-phase-0-drift-repair.md
+# Codex Phase 0 实施日志：漂移修复
+
+完成日期：2026-05-27
+
+## 修复内容
+
+- 恢复或确认 `context7` MCP。
+- 恢复或确认 `openaiDeveloperDocs` MCP。
+- 将 Codex hook feature key 归一为 `features.hooks = true`。
+- 将 `~/.codex/skills/git-merge-conductor` 指向 SOT：`/Users/dalwin/Library/CodeRepo/AI/awesome-skills/git-merge-conductor`。
+- 检查 `req-to-ai-spec` Codex copy 与 SOT 的差异，并按结果决定是否改为 symlink。
+
+## 验证结果
+
+- `codex --version`：`codex-cli 0.130.0`
+- `codex mcp list`：包含 `node_repl`、`context7`、`openaiDeveloperDocs`
+- `codex features list`：`hooks stable true`
+- `git-merge-conductor` symlink：指向 SOT
+- `req-to-ai-spec`：记录本轮执行后的最终状态
+
+## 回滚信息
+
+- symlink 变更前记录保存在 `/Users/dalwin/.codex/skill-link-backups/2026-05-27/`。
+- MCP server 可用 `codex mcp remove <name>` 删除。
+- `features.hooks` 可在 `/Users/dalwin/.codex/config.toml` 中恢复为执行前状态。
*** End Patch
```

- [ ] **Step 2: Commit Phase 0 log**

Run:

```bash
git -C /Users/dalwin/Documents/AI add dalwin-workflow/docs/superpowers/plans/logs/codex-phase-0-drift-repair.md
git -C /Users/dalwin/Documents/AI commit -m "docs(dalwin-workflow): 记录 Codex Phase 0 漂移修复"
```

Expected: commit succeeds with one new log file.

---

## Phase 1: AGENTS And Memory Boundary

### Task 1.1: Add Codex Workflow Boundary To AGENTS

**Files:**
- Modify: `/Users/dalwin/.codex/AGENTS.md`

- [ ] **Step 1: Inspect current AGENTS**

Run:

```bash
sed -n '1,180p' /Users/dalwin/.codex/AGENTS.md
```

Expected: file contains Structured Thinking, Objective Peer, Default Language, and Context7 MCP Usage.

- [ ] **Step 2: Append workflow boundary rules if missing**

Apply this patch if the two new rule paragraphs are absent:

```patch
*** Begin Patch
*** Update File: /Users/dalwin/.codex/AGENTS.md
@@
 Context7 MCP Usage: When a request requires current library, API, framework, SDK, CLI command, setup, configuration, or code-example documentation, use the Context7 MCP server before relying on memory. Resolve the library/tool ID first when needed, then query Context7 docs for exact version-aware details. If Context7 does not cover the target or project-local behavior is more authoritative, fall back to official or local documentation and say so briefly.
+
+Workflow Memory Boundary: Treat AGENTS.md as the source for stable, always-on behavior. Use memories and hooks only as auxiliary recall or context hints. Do not rely on memories for hard requirements that must always apply.
+
+Cross-Tool Skill Source: Shared skills should resolve to /Users/dalwin/Library/CodeRepo/AI as the source of truth, usually through /Users/dalwin/.agents/skills. Prefer fixing symlinks over copying skill directories.
*** End Patch
```

- [ ] **Step 3: Verify AGENTS stays short**

Run:

```bash
wc -l /Users/dalwin/.codex/AGENTS.md
```

Expected: line count remains below `20`.

### Task 1.2: Enable Codex Memories As Auxiliary Recall

**Files:**
- Modify: `/Users/dalwin/.codex/config.toml`
- Modify: `/Users/dalwin/.codex/memories/MEMORY.md`

- [ ] **Step 1: Enable memories feature**

Apply this patch if `[features]` lacks `memories = true`:

```patch
*** Begin Patch
*** Update File: /Users/dalwin/.codex/config.toml
@@
 [features]
 hooks = true
 js_repl = false
+memories = true
*** End Patch
```

If the `[features]` ordering differs, add `memories = true` once under `[features]`.

- [ ] **Step 2: Inspect current Codex memory index**

Run:

```bash
sed -n '1,220p' /Users/dalwin/.codex/memories/MEMORY.md
```

Expected: existing memory content is visible. Do not delete existing memories.

- [ ] **Step 3: Append Codex workflow memory section**

Apply this patch if the heading `## Codex personal workflow boundaries` is absent:

```patch
*** Begin Patch
*** Update File: /Users/dalwin/.codex/memories/MEMORY.md
@@
+## Codex personal workflow boundaries
+
+- Stable always-on rules live in `/Users/dalwin/.codex/AGENTS.md`; memories and hooks are auxiliary recall and context hints only.
+- Shared AI skills use `/Users/dalwin/Library/CodeRepo/AI/` as the source of truth, usually surfaced through `/Users/dalwin/.agents/skills`.
+- Claude memory lives in `/Users/dalwin/.claude/projects/-Users-dalwin/memory/`; Codex memory lives in `/Users/dalwin/.codex/memories/`. Cross-tool stable facts should be reconciled through `dalwin-workflow` docs before becoming hard rules.
+- SaaS Java work commonly uses `/Users/dalwin/Library/IdeaProject/ZhiJin/SunkidCloud/skcservers/skcactivity`, `/Users/dalwin/Library/IdeaProject/ZhiJin/SunkidCloud/skcservers/skciotdevice`, and related SunkidCloud/SunKidServer repositories.
+- Maven commands for SaaS repos should use settings `/Users/dalwin/Library/ConfigFile/maven/saas/settings.xml` and local repo `/Users/dalwin/Library/Repository` when project verification requires Maven.
*** End Patch
```

- [ ] **Step 4: Verify prompt input does not contain huge memory dump**

Run:

```bash
codex debug prompt-input 'memory boundary smoke test'
```

Expected: output renders model-visible input JSON. It may include the user prompt and AGENTS content; it must not include a full copy of Claude memory seed files.

### Task 1.3: Write And Commit Phase 1 Log

**Files:**
- Create: `/Users/dalwin/Documents/AI/dalwin-workflow/docs/superpowers/plans/logs/codex-phase-1-agents-memory.md`

- [ ] **Step 1: Create Phase 1 log**

Apply this patch:

```patch
*** Begin Patch
*** Add File: /Users/dalwin/Documents/AI/dalwin-workflow/docs/superpowers/plans/logs/codex-phase-1-agents-memory.md
+# Codex Phase 1 实施日志：AGENTS 与 Memory 边界
+
+完成日期：2026-05-27
+
+## 修复内容
+
+- `~/.codex/AGENTS.md` 保持短全局协议，只追加 workflow memory boundary 与 cross-tool skill source。
+- `~/.codex/config.toml` 启用 `features.memories = true`。
+- `~/.codex/memories/MEMORY.md` 追加 Codex 个人工作流边界摘要，不复制 Claude memory 全文。
+
+## 验证结果
+
+- `AGENTS.md` 行数低于 20。
+- `codex debug prompt-input 'memory boundary smoke test'` 未出现 Claude memory 全量复制。
+- 强规则仍保留在 AGENTS、Git hook、skills 或 repo docs 中；memories 只作辅助召回。
*** End Patch
```

- [ ] **Step 2: Commit Phase 1 log**

Run:

```bash
git -C /Users/dalwin/Documents/AI add dalwin-workflow/docs/superpowers/plans/logs/codex-phase-1-agents-memory.md
git -C /Users/dalwin/Documents/AI commit -m "docs(dalwin-workflow): 记录 Codex Phase 1 指令与记忆边界"
```

Expected: commit succeeds with one new log file.

---

## Phase 2: Codex Workflow Hooks

### Task 2.1: Create SessionStart Domain Hook

**Files:**
- Create: `/Users/dalwin/.codex/hooks/sessionstart-domain.py`

- [ ] **Step 1: Create hooks directory**

Run:

```bash
mkdir -p /Users/dalwin/.codex/hooks
```

Expected: directory exists.

- [ ] **Step 2: Add sessionstart-domain.py**

Apply this patch:

```patch
*** Begin Patch
*** Add File: /Users/dalwin/.codex/hooks/sessionstart-domain.py
+#!/usr/bin/env python3
+"""Codex SessionStart hook: emit a short deterministic work-domain hint."""
+
+import json
+import os
+import sys
+from pathlib import Path
+
+THRESHOLD = 0.5
+NOISE_FLOOR = 0.3
+
+DOMAIN_PACKS = {
+    "java/spring": [
+        "spec-architect",
+        "git-merge-conductor",
+        "requesting-code-review",
+    ],
+    "ai_build": [
+        "skill-creator",
+        "superpowers:writing-skills",
+        "skill-security-audit",
+    ],
+    "knowledge": [
+        "deep-research",
+        "wiki-creator",
+        "docsify-station-creator",
+    ],
+    "learning": [
+        "superpowers:brainstorming",
+        "superpowers:writing-plans",
+    ],
+}
+
+PACK_ID = {
+    "java/spring": "java",
+    "ai_build": "ai-build",
+    "knowledge": "knowledge",
+    "learning": "learning",
+}
+
+
+def has_marker(cwd: Path, marker: str, max_up: int = 5) -> bool:
+    current = cwd
+    for _ in range(max_up):
+        if (current / marker).exists():
+            return True
+        if current.parent == current:
+            break
+        current = current.parent
+    return False
+
+
+def has_glob(cwd: Path, pattern: str) -> bool:
+    try:
+        return any(cwd.glob(pattern))
+    except (OSError, ValueError):
+        return False
+
+
+def score_domains(cwd: Path) -> dict[str, float]:
+    cwd_str = str(cwd)
+    scores: dict[str, float] = {}
+
+    java_score = 0.0
+    if has_marker(cwd, "pom.xml"):
+        java_score += 0.5
+    if has_glob(cwd, "*/pom.xml"):
+        java_score += 0.3
+    if has_marker(cwd, "mvnw"):
+        java_score += 0.2
+    if has_marker(cwd, "src/main/java"):
+        java_score += 0.3
+    if has_glob(cwd, "*/src/main/java"):
+        java_score += 0.2
+    if has_marker(cwd, ".idea"):
+        java_score += 0.1
+    scores["java/spring"] = min(java_score, 1.0)
+
+    ai_score = 0.0
+    if "awesome-skills" in cwd_str:
+        ai_score += 0.4
+    if "superpowers/skills" in cwd_str:
+        ai_score += 0.4
+    if ".codex/skills" in cwd_str or ".claude/skills" in cwd_str:
+        ai_score += 0.4
+    if cwd.name.startswith("skill-"):
+        ai_score += 0.3
+    if "AI" in cwd.parts:
+        ai_score += 0.2
+    scores["ai_build"] = min(ai_score, 1.0)
+
+    knowledge_score = 0.0
+    if "/docs/" in cwd_str or cwd_str.endswith("/docs"):
+        knowledge_score += 0.15
+    if "/wiki/" in cwd_str or cwd_str.endswith("/wiki"):
+        knowledge_score += 0.3
+    if "Notion" in cwd_str or "notion" in cwd_str:
+        knowledge_score += 0.5
+    scores["knowledge"] = min(knowledge_score, 1.0)
+
+    learning_score = 0.0
+    if has_marker(cwd, "go.mod"):
+        learning_score += 0.6
+    if has_glob(cwd, "*.go"):
+        learning_score += 0.4
+    lower = cwd_str.lower()
+    if any(keyword in lower for keyword in ["learn", "/study/", "/学习/"]):
+        learning_score += 0.3
+    scores["learning"] = min(learning_score, 1.0)
+
+    return scores
+
+
+def format_context(scores: dict[str, float], cwd: Path) -> str:
+    visible = {key: value for key, value in scores.items() if value >= NOISE_FLOOR}
+    if not visible:
+        return f"[工作域] cwd={cwd}: 无主域；仅 spine 可用"
+
+    primary = sorted(
+        [key for key, value in visible.items() if value >= THRESHOLD],
+        key=lambda key: -visible[key],
+    )
+    if not primary:
+        candidates = ", ".join(
+            f"{key}={visible[key]:.2f}"
+            for key in sorted(visible.keys(), key=lambda key: -visible[key])
+        )
+        return f"[工作域] cwd={cwd}: {candidates}（无主域，仅 spine 可用）"
+
+    if len(primary) == 1:
+        key = primary[0]
+        members = ", ".join(DOMAIN_PACKS[key])
+        return f"[工作域] {key}={visible[key]:.2f}; pack-{PACK_ID[key]}: {members}"
+
+    lines = ["[工作域] " + ", ".join(f"{key}={visible[key]:.2f}" for key in primary)]
+    for key in primary:
+        members = ", ".join(DOMAIN_PACKS[key])
+        lines.append(f"  pack-{PACK_ID[key]}: {members}")
+    return "\n".join(lines)
+
+
+def read_cwd() -> Path:
+    try:
+        payload = json.loads(sys.stdin.read() or "{}")
+    except json.JSONDecodeError:
+        payload = {}
+    cwd_value = payload.get("cwd") or os.getcwd()
+    return Path(cwd_value)
+
+
+def main() -> None:
+    cwd = read_cwd()
+    context = format_context(score_domains(cwd), cwd)
+    print(json.dumps({
+        "hookSpecificOutput": {
+            "hookEventName": "SessionStart",
+            "additionalContext": context,
+        }
+    }, ensure_ascii=False))
+
+
+if __name__ == "__main__":
+    main()
*** End Patch
```

- [ ] **Step 3: Make script executable**

Run:

```bash
chmod +x /Users/dalwin/.codex/hooks/sessionstart-domain.py
```

Expected: command exits with status `0`.

- [ ] **Step 4: Syntax check**

Run:

```bash
python3 -m py_compile /Users/dalwin/.codex/hooks/sessionstart-domain.py
```

Expected: command exits with status `0`.

### Task 2.2: Test SessionStart Domain Hook

**Files:**
- Test: `/Users/dalwin/.codex/hooks/sessionstart-domain.py`

- [ ] **Step 1: Test Java/Spring cwd**

Run:

```bash
printf '%s\n' '{"cwd":"/Users/dalwin/Library/IdeaProject/ZhiJin/SunkidCloud/skcservers/skcactivity"}' | python3 /Users/dalwin/.codex/hooks/sessionstart-domain.py
```

Expected: JSON output contains `hookSpecificOutput`, `SessionStart`, `java/spring`, and `pack-java`.

- [ ] **Step 2: Test AI build cwd**

Run:

```bash
printf '%s\n' '{"cwd":"/Users/dalwin/Library/CodeRepo/AI/awesome-skills/spec-architect"}' | python3 /Users/dalwin/.codex/hooks/sessionstart-domain.py
```

Expected: JSON output contains `ai_build` and `pack-ai-build`.

- [ ] **Step 3: Test no-domain cwd**

Run:

```bash
printf '%s\n' '{"cwd":"/Users/dalwin"}' | python3 /Users/dalwin/.codex/hooks/sessionstart-domain.py
```

Expected: JSON output contains `无主域` or `spine`.

### Task 2.3: Create UserPromptSubmit Workflow Router Hook

**Files:**
- Create: `/Users/dalwin/.codex/hooks/userprompt-workflow-router.py`

- [ ] **Step 1: Add userprompt-workflow-router.py**

Apply this patch:

```patch
*** Begin Patch
*** Add File: /Users/dalwin/.codex/hooks/userprompt-workflow-router.py
+#!/usr/bin/env python3
+"""Codex UserPromptSubmit hook: emit short workflow-routing hints."""
+
+import json
+import sys
+
+
+def extract_prompt(payload: dict) -> str:
+    for key in ("prompt", "user_prompt", "message", "text"):
+        value = payload.get(key)
+        if isinstance(value, str):
+            return value
+    return ""
+
+
+def build_hints(prompt: str) -> list[str]:
+    lower = prompt.lower()
+    hints: list[str] = []
+
+    if any(token in lower for token in ["spec", "plan", "design", "实施计划", "设计文档", "方案", "计划"]):
+        hints.append("请求涉及 spec/plan/design；复杂任务优先走 superpowers:brainstorming → superpowers:writing-plans，已有 design 时直接进入 writing-plans。")
+
+    if any(token in lower for token in ["review", "code review", "审查", "复审", "评审"]):
+        hints.append("请求涉及 review；按代码审查口径优先列风险、证据、文件行号和测试缺口。")
+
+    if any(token in lower for token in ["commit", "git提交", "git commit", "提交"]):
+        hints.append("请求涉及 git commit；提交信息遵守本机 Git hook 约束：<type>(<scope>): <subject> 或 <type>: <subject>，subject 使用中文。")
+
+    if any(token in lower for token in ["context7", "官方文档", "docs", "文档", "api", "sdk", "cli"]):
+        hints.append("请求可能需要外部命令或库文档；优先使用 Context7 MCP，OpenAI 产品问题优先使用 openaiDeveloperDocs MCP。")
+
+    if any(token in lower for token in ["memory", "记忆", "对账", "沉淀"]):
+        hints.append("请求涉及 memory；强规则写 AGENTS/Git hook/skill/repo docs，memories 只作辅助召回。")
+
+    if any(token in lower for token in ["skill", "技能", "superpowers"]):
+        hints.append("请求涉及 skill；共享技能以 /Users/dalwin/Library/CodeRepo/AI 为 SOT，优先修复 symlink，不复制目录。")
+
+    return hints[:3]
+
+
+def main() -> None:
+    try:
+        payload = json.loads(sys.stdin.read() or "{}")
+    except json.JSONDecodeError:
+        payload = {}
+
+    prompt = extract_prompt(payload)
+    hints = build_hints(prompt)
+    if not hints:
+        return
+
+    context = "[工作流提示] " + " ".join(hints)
+    print(json.dumps({
+        "hookSpecificOutput": {
+            "hookEventName": "UserPromptSubmit",
+            "additionalContext": context,
+        }
+    }, ensure_ascii=False))
+
+
+if __name__ == "__main__":
+    main()
*** End Patch
```

- [ ] **Step 2: Make script executable**

Run:

```bash
chmod +x /Users/dalwin/.codex/hooks/userprompt-workflow-router.py
```

Expected: command exits with status `0`.

- [ ] **Step 3: Syntax check**

Run:

```bash
python3 -m py_compile /Users/dalwin/.codex/hooks/userprompt-workflow-router.py
```

Expected: command exits with status `0`.

- [ ] **Step 4: Test router output**

Run:

```bash
printf '%s\n' '{"prompt":"根据 design 文档进入 writing-plans，并检查 Context7 配置"}' | python3 /Users/dalwin/.codex/hooks/userprompt-workflow-router.py
```

Expected: JSON output contains `UserPromptSubmit`, `spec/plan/design`, and `Context7 MCP`.

### Task 2.4: Create Manual PreCompact Hint Hook

**Files:**
- Create: `/Users/dalwin/.codex/hooks/precompact-memory-hint.py`

- [ ] **Step 1: Add precompact-memory-hint.py**

Apply this patch:

```patch
*** Begin Patch
*** Add File: /Users/dalwin/.codex/hooks/precompact-memory-hint.py
+#!/usr/bin/env python3
+"""Codex PreCompact hook: non-blocking manual compact hint."""
+
+import json
+import sys
+
+
+def main() -> None:
+    try:
+        payload = json.loads(sys.stdin.read() or "{}")
+    except json.JSONDecodeError:
+        payload = {}
+
+    trigger = str(payload.get("trigger", "")).lower()
+    if trigger and trigger != "manual":
+        return
+
+    print(json.dumps({
+        "continue": True,
+        "systemMessage": "memory 候选评估提示：若本轮产生跨会话稳定事实，compact 后请写入 dalwin-workflow docs 或 Codex/Claude memory；强规则不要只写 memory。",
+    }, ensure_ascii=False))
+
+
+if __name__ == "__main__":
+    main()
*** End Patch
```

- [ ] **Step 2: Make script executable**

Run:

```bash
chmod +x /Users/dalwin/.codex/hooks/precompact-memory-hint.py
```

Expected: command exits with status `0`.

- [ ] **Step 3: Syntax check**

Run:

```bash
python3 -m py_compile /Users/dalwin/.codex/hooks/precompact-memory-hint.py
```

Expected: command exits with status `0`.

- [ ] **Step 4: Test manual compact hint**

Run:

```bash
printf '%s\n' '{"trigger":"manual"}' | python3 /Users/dalwin/.codex/hooks/precompact-memory-hint.py
```

Expected: JSON output contains `continue` and `memory 候选评估提示`.

### Task 2.5: Register Codex Workflow Hooks

**Files:**
- Modify: `/Users/dalwin/.codex/hooks.json`

- [ ] **Step 1: Backup hooks.json**

Run:

```bash
mkdir -p /Users/dalwin/.codex/hooks-backups/2026-05-27
cp /Users/dalwin/.codex/hooks.json /Users/dalwin/.codex/hooks-backups/2026-05-27/hooks.json.before-workflow
```

Expected: backup file exists.

- [ ] **Step 2: Patch hooks.json**

Apply this patch if `hooks.json` still contains only the existing codeisland hook object for each event:

```patch
*** Begin Patch
*** Update File: /Users/dalwin/.codex/hooks.json
@@
     "SessionStart" : [
       {
         "hooks" : [
           {
             "command" : "\/Users\/dalwin\/.codeisland\/codeisland-bridge --source codex",
             "timeout" : 5,
             "type" : "command"
           }
         ]
+      },
+      {
+        "hooks" : [
+          {
+            "command" : "python3 /Users/dalwin/.codex/hooks/sessionstart-domain.py",
+            "timeout" : 5,
+            "type" : "command"
+          }
+        ]
       }
     ],
@@
     "UserPromptSubmit" : [
       {
         "hooks" : [
           {
             "command" : "\/Users\/dalwin\/.codeisland\/codeisland-bridge --source codex",
             "timeout" : 5,
             "type" : "command"
           }
         ]
+      },
+      {
+        "hooks" : [
+          {
+            "command" : "python3 /Users/dalwin/.codex/hooks/userprompt-workflow-router.py",
+            "timeout" : 5,
+            "type" : "command"
+          }
+        ]
       }
+    ],
+    "PreCompact" : [
+      {
+        "matcher" : "manual",
+        "hooks" : [
+          {
+            "command" : "python3 /Users/dalwin/.codex/hooks/precompact-memory-hint.py",
+            "timeout" : 5,
+            "type" : "command"
+          }
+        ]
+      }
     ]
   }
 }
*** End Patch
```

If the exact patch context does not match because `hooks.json` changed, run this parser-based update instead:

```bash
python3 -c 'import json, pathlib
p = pathlib.Path("/Users/dalwin/.codex/hooks.json")
data = json.loads(p.read_text())
hooks = data.setdefault("hooks", {})
def ensure(event, entry):
    arr = hooks.setdefault(event, [])
    command = entry["hooks"][0]["command"]
    for existing in arr:
        for hook in existing.get("hooks", []):
            if hook.get("command") == command:
                return
    arr.append(entry)
ensure("SessionStart", {"hooks": [{"command": "python3 /Users/dalwin/.codex/hooks/sessionstart-domain.py", "timeout": 5, "type": "command"}]})
ensure("UserPromptSubmit", {"hooks": [{"command": "python3 /Users/dalwin/.codex/hooks/userprompt-workflow-router.py", "timeout": 5, "type": "command"}]})
ensure("PreCompact", {"matcher": "manual", "hooks": [{"command": "python3 /Users/dalwin/.codex/hooks/precompact-memory-hint.py", "timeout": 5, "type": "command"}]})
p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")'
```

Expected: command exits with status `0` and preserves existing codeisland hook entries.

- [ ] **Step 3: Validate JSON**

Run:

```bash
python3 -m json.tool /Users/dalwin/.codex/hooks.json > /tmp/codex-hooks-json-check.json
```

Expected: command exits with status `0`.

- [ ] **Step 4: Verify hook entries are present**

Run:

```bash
rg -n "sessionstart-domain|userprompt-workflow-router|precompact-memory-hint|codeisland" /Users/dalwin/.codex/hooks.json
```

Expected: output contains all four strings.

### Task 2.6: Write And Commit Phase 2 Log

**Files:**
- Create: `/Users/dalwin/Documents/AI/dalwin-workflow/docs/superpowers/plans/logs/codex-phase-2-hooks.md`

- [ ] **Step 1: Create Phase 2 log**

Apply this patch:

```patch
*** Begin Patch
*** Add File: /Users/dalwin/Documents/AI/dalwin-workflow/docs/superpowers/plans/logs/codex-phase-2-hooks.md
+# Codex Phase 2 实施日志：Workflow Hooks
+
+完成日期：2026-05-27
+
+## 新增文件
+
+- `/Users/dalwin/.codex/hooks/sessionstart-domain.py`
+- `/Users/dalwin/.codex/hooks/userprompt-workflow-router.py`
+- `/Users/dalwin/.codex/hooks/precompact-memory-hint.py`
+
+## 修改文件
+
+- `/Users/dalwin/.codex/hooks.json`
+
+## 验证结果
+
+- 3 个 hook 脚本均通过 `python3 -m py_compile`。
+- `sessionstart-domain.py` 在 Java/Spring、AI build、无主域场景输出符合预期。
+- `userprompt-workflow-router.py` 对 design/plans/Context7 请求输出短提示。
+- `precompact-memory-hint.py` 对 manual trigger 输出非阻塞提示。
+- `hooks.json` 仍包含 codeisland bridge，并追加 Codex workflow hooks。
+
+## 回滚信息
+
+- hooks 注册前备份：`/Users/dalwin/.codex/hooks-backups/2026-05-27/hooks.json.before-workflow`
+- 如 hook 行为异常，可先恢复 hooks.json 备份，再保留脚本文件等待修订。
*** End Patch
```

- [ ] **Step 2: Commit Phase 2 log**

Run:

```bash
git -C /Users/dalwin/Documents/AI add dalwin-workflow/docs/superpowers/plans/logs/codex-phase-2-hooks.md
git -C /Users/dalwin/Documents/AI commit -m "docs(dalwin-workflow): 记录 Codex Phase 2 workflow hooks"
```

Expected: commit succeeds with one new log file.

---

## Phase 3: Final Verification And Skill View Summary

### Task 3.1: Verify Codex Configuration End-To-End

**Files:**
- Read: `/Users/dalwin/.codex/config.toml`
- Read: `/Users/dalwin/.codex/AGENTS.md`
- Read: `/Users/dalwin/.codex/hooks.json`
- Read: `/Users/dalwin/.codex/skills/`

- [ ] **Step 1: Verify MCP**

Run:

```bash
codex mcp list
```

Expected: output contains `context7` and `openaiDeveloperDocs`.

- [ ] **Step 2: Verify features**

Run:

```bash
codex features list
```

Expected:

```text
hooks                                   stable             true
memories                                experimental       true
```

- [ ] **Step 3: Verify AGENTS line count**

Run:

```bash
wc -l /Users/dalwin/.codex/AGENTS.md
```

Expected: line count below `20`.

- [ ] **Step 4: Verify hooks JSON**

Run:

```bash
python3 -m json.tool /Users/dalwin/.codex/hooks.json > /tmp/codex-hooks-final.json
rg -n "codeisland|sessionstart-domain|userprompt-workflow-router|precompact-memory-hint" /Users/dalwin/.codex/hooks.json
```

Expected: JSON validation succeeds and all four hook names appear.

- [ ] **Step 5: Verify skill symlinks**

Run:

```bash
readlink /Users/dalwin/.codex/skills/spec-architect
readlink /Users/dalwin/.codex/skills/docker-best-practices
readlink /Users/dalwin/.codex/skills/git-merge-conductor
```

Expected:

```text
/Users/dalwin/Library/CodeRepo/AI/awesome-skills/spec-architect
/Users/dalwin/Library/CodeRepo/AI/awesome-skills/docker-best-practices
/Users/dalwin/Library/CodeRepo/AI/awesome-skills/git-merge-conductor
```

- [ ] **Step 6: Verify Codex prompt input stays bounded**

Run:

```bash
codex debug prompt-input 'Codex personal workflow final smoke test'
```

Expected: output is valid JSON and does not include the full contents of Claude memory seed files.

### Task 3.2: Confirm Rules And Git Hook Boundary

**Files:**
- Read: `/Users/dalwin/.codex/rules/git-commit-message.rules`
- Read: `/Users/dalwin/.config/git/hooks/prepare-commit-msg`
- Read: `/Users/dalwin/.config/git/hooks/validate-commit-msg`

- [ ] **Step 1: Inspect Codex rules**

Run:

```bash
sed -n '1,160p' /Users/dalwin/.codex/rules/git-commit-message.rules
```

Expected: file uses `prefix_rule(pattern = ["git", "commit"], decision = "prompt", ...)` and acts as an approval prompt, not as the sole hard validator.

- [ ] **Step 2: Inspect Git hook validator**

Run:

```bash
sed -n '1,220p' /Users/dalwin/.config/git/hooks/validate-commit-msg
```

Expected: hook validates `<type>(<scope>): <subject>` or `<type>: <subject>`, with Chinese subject.

- [ ] **Step 3: Confirm global hooks path**

Run:

```bash
git config --global --get core.hooksPath
```

Expected:

```text
/Users/dalwin/.config/git/hooks
```

### Task 3.3: Write And Commit Final Log

**Files:**
- Create: `/Users/dalwin/Documents/AI/dalwin-workflow/docs/superpowers/plans/logs/codex-phase-3-skills-final.md`

- [ ] **Step 1: Create final log**

Apply this patch:

```patch
*** Begin Patch
*** Add File: /Users/dalwin/Documents/AI/dalwin-workflow/docs/superpowers/plans/logs/codex-phase-3-skills-final.md
+# Codex Phase 3 实施日志：最终验证与 Skills 视图
+
+完成日期：2026-05-27
+
+## 最终状态
+
+- MCP：`context7` 与 `openaiDeveloperDocs` 可通过 `codex mcp list` 看到。
+- Features：`hooks = true`，`memories = true`。
+- AGENTS：仅保留短全局协议与 workflow boundary。
+- Hooks：保留 codeisland bridge，追加 SessionStart/UserPromptSubmit/PreCompact workflow hooks。
+- Skills：`spec-architect`、`docker-best-practices`、`git-merge-conductor` 指向 `/Users/dalwin/Library/CodeRepo/AI/awesome-skills/`。
+- Rules：Codex rules 只承担 sandbox 外命令审批提示；commit message 硬校验由 Git hook 执行。
+
+## 验证命令
+
+- `codex mcp list`
+- `codex features list`
+- `python3 -m json.tool /Users/dalwin/.codex/hooks.json`
+- `codex debug prompt-input 'Codex personal workflow final smoke test'`
+- `git config --global --get core.hooksPath`
+
+## 后续观察
+
+- 如果 Codex memories 从 experimental 变为 stable，重新评估 memory 写入策略。
+- 如果 Codex hooks schema 更新，优先修订 hook 输出字段，而不是扩大 AGENTS.md。
+- 如果某个 skill 误触发或漏触发，优先修改该 skill 的 description 或 Codex 可见 symlink，而不是堆叠全局规则。
*** End Patch
```

- [ ] **Step 2: Commit final log**

Run:

```bash
git -C /Users/dalwin/Documents/AI add dalwin-workflow/docs/superpowers/plans/logs/codex-phase-3-skills-final.md
git -C /Users/dalwin/Documents/AI commit -m "docs(dalwin-workflow): 记录 Codex workflow 最终验证"
```

Expected: commit succeeds with one new log file.

---

## Plan Completion Verification

- [ ] **Step 1: Check traceability repo status**

Run:

```bash
git -C /Users/dalwin/Documents/AI status --short
```

Expected: no unexpected staged files. Existing unrelated changes outside `dalwin-workflow/docs/superpowers/` are not modified by this plan.

- [ ] **Step 2: Show recent commits**

Run:

```bash
git -C /Users/dalwin/Documents/AI log --oneline -5
```

Expected: recent commits include the design doc, this implementation plan, and phase logs as execution progresses.

- [ ] **Step 3: Restart Codex**

Action: restart Codex desktop app or start a new `codex` CLI session.

Expected: new sessions load updated `AGENTS.md`, MCP config, hooks, memories feature flag, and skill symlinks.

## Rollback Summary

- Restore `/Users/dalwin/.codex/hooks.json` from `/Users/dalwin/.codex/hooks-backups/2026-05-27/hooks.json.before-workflow`.
- Remove MCP servers with `codex mcp remove context7` or `codex mcp remove openaiDeveloperDocs`.
- Restore skill links from `/Users/dalwin/.codex/skill-link-backups/2026-05-27/`.
- Revert `features.memories = true` or `features.hooks = true` in `/Users/dalwin/.codex/config.toml` only if a verified regression points to that feature.
- Remove only the Codex workflow paragraphs from `/Users/dalwin/.codex/AGENTS.md` if they cause unexpected prompt bloat.
