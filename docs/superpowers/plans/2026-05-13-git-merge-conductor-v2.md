# Git Merge Conductor v2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the `git-merge-conductor` v2 iteration from [docs/superpowers/specs/2026-05-13-git-merge-conductor-v2-design.md](../specs/2026-05-13-git-merge-conductor-v2-design.md): split v1's 8-stage conflict-pipeline into mode-aware dual pipelines (conflict + transplant), add Stage 2 `requirements.yaml` extraction, Stage 6.5 negative-constraint self-audit, Stage 7.5 verification loop (auto-fix + user final gate), worktree delegation for complex modes, single-line stage banners, and the M1 main-file → decision-oriented + contracts下沉 restructuring.

**Architecture:** Iterative refactor of an existing skill. SKILL.md goes from ~378 lines to ~200-220 lines (主薄化); per-stage details move to 5 new `references/contracts/*.md` files. New artifacts: `requirements.yaml`, `grafting-plan.yaml`, `draft.md`, `audit-report.md`, `verification-report.md`, `negative-constraints.md`. v1 `state.json` schema bumps to version 2.0 with new fields. Smoke scenarios A–E continue to pass; 4 new scenarios F/G/H/I cover transplant-pipeline, worktree lifecycle, Phase-1 self-fix limit, and Phase-2 multi-iter loop.

**Tech Stack:** Markdown + YAML only. No code dependencies. Verification uses Bash + git CLI against a toy fixture repo + the new care-class-to-develop fixture. Worktree work delegates to `superpowers:using-git-worktrees` skill (already installed).

**Spec reference:** Design spec is the canonical content source. Tasks say "per spec §X.Y" rather than duplicating long sections. Spec is committed at `9403d63` and will not drift.

**Language convention reminder (carried from v1):**

| Content | Language |
|---|---|
| `SKILL.md` body | English |
| `references/*.md` (rules, schemas, prompts) | English |
| `references/contracts/*.md` (五字段契约) | English |
| `templates/*.md`, `templates/*.yaml` user-facing fixed text | Chinese |
| Template placeholders (`{{var_name}}`) | English |
| skill-generated commit message | `merge: 中文说明` |
| HTML report visible text | Chinese (`<html lang="zh-CN">`) |

**Commit convention for THIS plan's tasks:**
- `feat(git-merge-conductor): v2 ...` — new files (contracts, requirements.yaml, etc.)
- `refactor(git-merge-conductor): v2 ...` — SKILL.md 主薄化 + 现有 reference 改写
- `docs(git-merge-conductor): v2 ...` — SMOKE-TEST scenarios新增
- `test(git-merge-conductor): v2 ...` — fixture 新增 / smoke runs

**Scope Check:** Single skill, single iteration. No subsystem decomposition needed — the dual pipeline split is internal to one skill.

---

## File Structure (v2 target)

```
skills/git-merge-conductor/
├── SKILL.md                                # English, 主薄化 200-220 lines
├── references/
│   ├── mode-inference.md                   # 改: 加 backport-cherry vs backport-transplant 阈值
│   ├── conflict-classification.md          # 改: C/D 自动决策启发式
│   ├── semantic-mapping.md                 # 改: 输出对齐 grafting-plan
│   ├── html-report-template.md             # 改: 加 Phase 2 兜底报表 section
│   ├── state-schema.md                     # 改: v2 字段
│   ├── recovery-protocol.md                # 改: worktree + iteration recovery
│   ├── negative-constraints.md             # 新: NC-01~05 + 领域示例附录
│   └── contracts/
│       ├── setup-stages.md                 # 新: Stage 0/1/2/3
│       ├── pipeline-conflict.md            # 新: Stage 4c/5c/6c
│       ├── pipeline-transplant.md          # 新: Stage 4t/5t/6t
│       ├── audit-and-verify.md             # 新: Stage 6.5 / 7 / 7.5
│       └── wrap-up.md                      # 新: Stage 8
└── templates/
    ├── strategy-report.md                  # 改: 加 requirements.yaml 渲染锚点
    ├── requirements.yaml                   # 新: Stage 2 需求清单 schema
    ├── grafting-plan.yaml                  # 新: Stage 4t 嫁接矩阵
    ├── draft.md                            # 新: Stage 5t per-item draft
    ├── audit-report.md                     # 新: Stage 6.5 self-audit
    ├── verification-report.md              # 新: Stage 7.5 Phase 2 兜底
    ├── commit-message.md                   # 改: 加 iteration + rolled-back
    ├── wrap-up-report.md                   # 改: 加 worktree 清理
    └── decision-point.md                   # 删: autonomous 不再需要

docs/superpowers/verification/git-merge-conductor/
├── SMOKE-TEST.md                           # 改: 加 F/G/H/I 注册项
├── setup-fixture.sh                        # 改: 加 care-class-to-develop fixture
└── scenarios/
    ├── A-forward-integrate.md              # 保留 (smoke 必过)
    ├── B-backport.md                       # 改: 拆分 backport-cherry vs backport-transplant
    ├── C-patch-apply.md                    # 保留
    ├── D-interrupt-resume.md               # 改: 加 worktree resume 子场景
    ├── E-guard.md                          # 保留
    ├── F-backport-transplant.md            # 新: care-class fixture 全链路
    ├── G-worktree-lifecycle.md             # 新: 创建 → abort → 清理
    ├── H-phase1-loop-limit.md              # 新: 注入 compile error → 3 次失败
    └── I-phase2-multi-iter.md              # 新: 用户反馈 loop → finalize
```

---

# Phase 1 — 基础设施

**Goal of phase:** State schema + Safety Invariant 第 6 条 + single-line stage banner + stage_history 完整性硬约束 + worktree integration instruction. After this phase, v1 smoke scenarios A/C/E still pass; state.json carries `version: "2.0"` and full stage_history.

## Task 1: Update `references/state-schema.md` with v2 fields

**Files:**
- Modify: `/Users/dalwin/Documents/AI/skills/git-merge-conductor/references/state-schema.md`

- [ ] **Step 1: Read current state-schema.md to understand v1 structure**

Run: `cat /Users/dalwin/Documents/AI/skills/git-merge-conductor/references/state-schema.md`
Expected: shows v1 schema with `task_name`, `mode`, `source`, `target`, `working_branch`, `stage`, `stage_history`, `decisions`, `auto_resolved_summary`, `config`, `cleanup_policy`.

- [ ] **Step 2: Add v2 top-level fields**

Append to the existing schema definition block (or modify in place) per spec §11.6:
```yaml
version: "2.0"                           # NEW. v1 sessions = "1.0", v2 sessions = "2.0", no migration
stage_kind: <stage编号子分类>             # NEW. e.g. "0", "1", "2", "3", "4c"/"4t", "5c"/"5t", "6c"/"6t", "6.5", "7", "7.5", "8"
pipeline: conflict | transplant          # NEW. 由 Stage 2 mode-inference 确定后写入
iter: 1                                  # NEW. Phase 2 循环计数器；初始 1，每轮 Phase 2 回 Stage 4-6 时 +1
iterations:                              # NEW. 历史循环记录
  - iter: 1
    started_at: <ISO>
    trigger: initial | user-feedback | phase1-fix
    ended_at: <ISO>
    user_feedback: <自由文本，trigger != initial 时>
```

- [ ] **Step 3: Update `working_branch` to include worktree fields**

Replace v1's `working_branch` (a string) with object form per spec §10.3:
```yaml
working_branch:
  name: merge/<task>
  worktree_path: <absolute path | null>   # null = 主仓 checkout
  use_worktree: true | false
```

- [ ] **Step 4: Add `requirements` array stub**

Add (full schema lives in `templates/requirements.yaml`; this is just the inline schema reference):
```yaml
requirements: []                          # NEW. Array of {id, title, scope_tag, target_locations[], acceptance[], out_of_scope[], status, evidence{}, ambiguous}, per templates/requirements.yaml
global_out_of_scope: []                   # NEW. Per templates/requirements.yaml
```

- [ ] **Step 5: Add `grafts` array stub (for transplant-pipeline)**

Add (full schema lives in `templates/grafting-plan.yaml`):
```yaml
grafts: []                                # NEW. Only populated for pipeline == transplant; schema per templates/grafting-plan.yaml
```

- [ ] **Step 6: Add `verification` config sub-object under `config`**

Modify the existing `config` block to include (per spec §9.1):
```yaml
config:
  commit_granularity: single-merge | per-source-commit | squash
  semantic_mapping_enabled: true | false
  locked_file_rules:
    take_target: []
    take_source: []
  verification:                           # NEW.
    compile: true                         # default true
    lint: true                            # default true
    test: scope | full | off | suites      # default "scope"; "suites" is followed by suites: [<name>]
    suites: []                            # only when test == "suites"
```

- [ ] **Step 7: Update `stage_history` entry shape**

Replace v1's `{stage, tag, completed_at}` with v2 form per spec §11.6:
```yaml
stage_history:
  - stage: 0
    kind: "0"
    tag: null                             # Stage 0/1/2 don't tag; Stage 3 onwards have merge/<task>/before-step-N
    completed_at: <ISO>
```
Note: `stage` is integer (0, 1, 2, 3, 4, 5, 6, 7, 8) and `kind` is string covering sub-stages including "4c"/"4t"/"5c"/"5t"/"6c"/"6t"/"6.5"/"7.5".

- [ ] **Step 8: Add `audit` array (filled by Stage 6.5)**

Append:
```yaml
audit:                                    # NEW. Stage 6.5 records
  - unit_id: G-01 | hunk-N                # graft id for transplant; hunk id for conflict
  - unit_kind: graft | hunk
  - result: pass | fail
  - violations: [<NC-id or out_of_scope匹配项>]
  - action: applied | rolled-back
  - audited_at: <ISO>
```

- [ ] **Step 9: Add `unresolved` array (Stage 6c output)**

Append:
```yaml
unresolved: []                            # NEW. Conflict-pipeline hunks 无法自动决策时落此；同时写 .git/merge-conductor/<task>/unresolved.md
```

- [ ] **Step 10: Commit**

```bash
cd /Users/dalwin/Documents/AI
git add skills/git-merge-conductor/references/state-schema.md
git commit -m "$(cat <<'EOF'
refactor(git-merge-conductor): v2 state schema (version 2.0)

Add v2 fields: version, stage_kind, pipeline, iter, iterations[],
working_branch.worktree_path, requirements[], grafts[], audit[],
unresolved[], config.verification. stage_history kind 字段扩展支持
4c/4t/5c/5t/6c/6t/6.5/7.5 子分类。v1 → v2 不做自动迁移；version
字段区分。

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

## Task 2: Add Safety Invariant 第 6 条 + stage_history 完整性硬约束 to SKILL.md

**Files:**
- Modify: `/Users/dalwin/Documents/AI/skills/git-merge-conductor/SKILL.md` (Safety Invariants section)

- [ ] **Step 1: Read current Safety Invariants section**

Run: `grep -n "Safety Invariants" /Users/dalwin/Documents/AI/skills/git-merge-conductor/SKILL.md`
Expected: shows the section starts around line 23.

- [ ] **Step 2: Add Safety Invariant 6 after the existing 5**

Use the Edit tool to find the closing line of the current Safety Invariants list (currently item 5 about `[p]` pause / `[a]` abort) and append item 6 + item 7 per spec §8.5 and §11.2:

```markdown
6. **No change outside `requirements.yaml`.** 任何 graft / hunk 改动的文件不在
   `requirements.yaml::items[*].target_locations` 内即触发硬性 rollback。
   若用户希望纳入，必须先在 Stage 2 升级 `requirements.yaml` 加 item
   （回到 Stage 2 ★ Gate ★ 重审）。检测信号与后置见
   `references/negative-constraints.md#NC-05`.
7. **Stage transitions must persist before continuing.** Writing
   `state.json::stage = next` and appending to `state.json::stage_history`
   is a hard precondition for entering the next stage. If `state.json` write
   fails, halt the pipeline and report to the user — never proceed in memory only.
   The final `stage_history` must contain 11 entries (0/1/2/3/4(c-or-t)/5(c-or-t)/6(c-or-t)/6.5/7/7.5/8);
   any gap is a bug, not an optimization.
```

- [ ] **Step 3: Verify insertion**

Run: `grep -A 2 "^6\." /Users/dalwin/Documents/AI/skills/git-merge-conductor/SKILL.md`
Expected: shows the new item 6 about requirements.yaml hard rollback.

- [ ] **Step 4: Commit**

```bash
cd /Users/dalwin/Documents/AI
git add skills/git-merge-conductor/SKILL.md
git commit -m "$(cat <<'EOF'
refactor(git-merge-conductor): v2 Safety Invariants 6 + 7

#6 hard-rollback any change outside requirements.yaml (NC-05 升级);
#7 stage_history 必须 11 条完整，state.json 写入失败即终止流程，
解决 v1 实践中 stage_history 3→7 直跳的根因 (care-class metadata).

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

## Task 3: Add single-line stage banner instructions to SKILL.md

**Files:**
- Modify: `/Users/dalwin/Documents/AI/skills/git-merge-conductor/SKILL.md`

- [ ] **Step 1: Locate "Pipeline Overview" section**

Run: `grep -n "Pipeline Overview" /Users/dalwin/Documents/AI/skills/git-merge-conductor/SKILL.md`
Expected: line ~43.

- [ ] **Step 2: Insert a new sub-section "Stage Banner" after Pipeline Overview**

Insert after the pipeline overview block, before "Between every stage, write state.json":

```markdown
### Stage Banner (mandatory)

On entering every Stage N, emit a single-line Chinese banner before any other output:

```
[Stage <N> · <Stage Name (English)> · iter <i> · tag: merge/<task>/before-step-<N>]
```

`<i>` is the Phase 2 iteration counter (`state.json::iter`). Stages with no `before-step` tag (0/1/2) use `tag: none`. This banner is non-negotiable — it is the user's only inline visibility into where the pipeline is.

You must also append to `state.json::stage_history` and bump `state.json::stage` before producing the banner. Banner-without-state-write or state-write-without-banner is a violation of Safety Invariant 7.
```

- [ ] **Step 3: Commit**

```bash
cd /Users/dalwin/Documents/AI
git add skills/git-merge-conductor/SKILL.md
git commit -m "$(cat <<'EOF'
refactor(git-merge-conductor): v2 single-line stage banner

每个 stage 入口强制单行 banner 输出 + state.json 同步写入，
解决 v1 模型 "忘了在哪 stage" 失配 (care-class metadata).

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

## Task 4: Add Quick Sanity Check stage-self-check to SKILL.md

**Files:**
- Modify: `/Users/dalwin/Documents/AI/skills/git-merge-conductor/SKILL.md` (Quick Sanity Checks section, currently end of file)

- [ ] **Step 1: Locate "Quick Sanity Checks" section**

Run: `grep -n "Quick Sanity Checks" /Users/dalwin/Documents/AI/skills/git-merge-conductor/SKILL.md`
Expected: line ~370.

- [ ] **Step 2: Append stage-self-check item**

Add to the end of the bulleted list per spec §11.4:

```markdown
- Before any user-facing output: am I at the stage I think I'm at?
  Read `state.json::stage` and compare against my mental model.
  Mismatch → stop and reconcile, do not continue.
```

- [ ] **Step 3: Commit**

```bash
cd /Users/dalwin/Documents/AI
git add skills/git-merge-conductor/SKILL.md
git commit -m "$(cat <<'EOF'
refactor(git-merge-conductor): v2 stage-self-check sanity rule

Stage-self-check added to Quick Sanity Checks; pairs with Safety
Invariant 7 to detect/repair stage drift.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

## Task 5: Add Stage 3 worktree delegation instruction to SKILL.md

**Files:**
- Modify: `/Users/dalwin/Documents/AI/skills/git-merge-conductor/SKILL.md` (Stage 3 section)

- [ ] **Step 1: Locate Stage 3 section**

Run: `grep -n "^## Stage 3" /Users/dalwin/Documents/AI/skills/git-merge-conductor/SKILL.md`
Expected: line ~160.

- [ ] **Step 2: Prepend a worktree-decision block at top of Stage 3 body**

Insert after the `## Stage 3 — Working Branch Setup` header, before the existing `After Stage 2 approval, execute:` block, per spec §10:

```markdown
**Worktree decision (run FIRST)**: read `state.json::pipeline` (set in Stage 2). If mode is one of `backport-transplant`, `semantic-transplant`, `rebase-onto`, `forward-integrate`, OR the user explicitly enabled `use_worktree: true` in Stage 2, delegate worktree creation to the `superpowers:using-git-worktrees` skill. Write `state.json::working_branch.worktree_path` with the returned path and `use_worktree: true`. All subsequent `git` invocations in Stage 4-7 must run with cwd set to this worktree path. State files in `.git/merge-conductor/<task>/` remain in the main repo (metadata 主仓化, per spec §10.2).

Otherwise (simple modes — `full-merge`, `cherry-pick-set`, `patch-apply`, `backport-cherry`): proceed with main-repo `git checkout -b merge/<task>` as before; set `use_worktree: false` and `worktree_path: null`.

If worktree creation fails, fall back to main-repo checkout and warn the user: 「worktree 创建失败，已降级到主仓模式，建议 stage 完成后立刻 review」.
```

- [ ] **Step 3: Commit**

```bash
cd /Users/dalwin/Documents/AI
git add skills/git-merge-conductor/SKILL.md
git commit -m "$(cat <<'EOF'
feat(git-merge-conductor): v2 Stage 3 worktree delegation

复杂 mode (backport-transplant/semantic-transplant/rebase-onto/
forward-integrate) 委托给 superpowers:using-git-worktrees；
失败降级主仓 checkout + warn 用户。

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

## Task 6: Phase 1 smoke gate — re-run scenario A (forward-integrate)

**Files:**
- Read: `/Users/dalwin/Documents/AI/docs/superpowers/verification/git-merge-conductor/scenarios/A-forward-integrate.md`
- Read: `/Users/dalwin/Documents/AI/docs/superpowers/verification/git-merge-conductor/setup-fixture.sh`

This is a manual verification step. The point: after Phase 1's changes, scenario A's automated portion still completes; state.json now contains v2 fields.

- [ ] **Step 1: Recreate the fixture repo**

Run:
```bash
cd /tmp
rm -rf gmc-fixture
bash /Users/dalwin/Documents/AI/docs/superpowers/verification/git-merge-conductor/setup-fixture.sh
```
Expected: `/tmp/gmc-fixture/` initialized with branches per fixture setup.

- [ ] **Step 2: Run scenario A manually with Claude Code in the fixture repo**

Start a fresh Claude Code session in `/tmp/gmc-fixture/` and request:
> 「把 feature/A 上的功能正向合并到 develop，按 git-merge-conductor 走」

Follow the prompts. Expected behavior in Phase 1 of v2:
- Stage banner appears as single-line `[Stage 0 · Entry Probe · iter 1 · tag: none]` etc.
- state.json after Stage 3 contains: `version: "2.0"`, `working_branch.worktree_path: null` (forward-integrate triggers worktree per v2 §10.1 — wait, forward-integrate IS in the complex list — confirm Phase 1 covers this), `stage_history` has 4 entries (0/1/2/3) and grows as expected.

- [ ] **Step 3: Inspect final state.json**

After the scenario finishes:
```bash
cat /tmp/gmc-fixture/.git/merge-conductor/scenario-a/state.json | jq '.version, .stage_history | length, .working_branch'
```
Expected: `"2.0"`, `11`, `{name, worktree_path, use_worktree: true}` (forward-integrate runs in worktree).

- [ ] **Step 4: Add Phase 1 gate notes to SMOKE-TEST.md**

Append to `/Users/dalwin/Documents/AI/docs/superpowers/verification/git-merge-conductor/SMOKE-TEST.md`:

```markdown
## v2 Phase 1 gate (2026-05-13)
- [ ] Scenario A re-run: state.json `version == "2.0"`, `stage_history.length == 11`, banner emitted at every stage.
- [ ] No regression on scenario C (patch-apply): still passes; no state schema breakage.
- [ ] No regression on scenario E (guard): guards still fire.
```

- [ ] **Step 5: Commit smoke notes**

```bash
cd /Users/dalwin/Documents/AI
git add docs/superpowers/verification/git-merge-conductor/SMOKE-TEST.md
git commit -m "$(cat <<'EOF'
test(git-merge-conductor): v2 Phase 1 smoke gate notes

Phase 1 完成基础设施改动后，重跑 A/C/E 三个 v1 场景验证不回归。

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

# Phase 2 — 主薄化 + Contracts

**Goal of phase:** SKILL.md slim down to ~200-220 lines pointing at new `references/contracts/`. Five contract files house the per-Stage 五字段模板. Reading Order table rewired.

## Task 7: Scaffold `references/contracts/` directory + 5 empty contract files

**Files:**
- Create: `/Users/dalwin/Documents/AI/skills/git-merge-conductor/references/contracts/setup-stages.md`
- Create: `/Users/dalwin/Documents/AI/skills/git-merge-conductor/references/contracts/pipeline-conflict.md`
- Create: `/Users/dalwin/Documents/AI/skills/git-merge-conductor/references/contracts/pipeline-transplant.md`
- Create: `/Users/dalwin/Documents/AI/skills/git-merge-conductor/references/contracts/audit-and-verify.md`
- Create: `/Users/dalwin/Documents/AI/skills/git-merge-conductor/references/contracts/wrap-up.md`

- [ ] **Step 1: Create directory**

Run: `mkdir -p /Users/dalwin/Documents/AI/skills/git-merge-conductor/references/contracts`

- [ ] **Step 2: Create 5 placeholder files with header**

For each of the 5 files, write this header (substitute `<phase>` per file):

```markdown
# Stage Contracts — <phase>

Each section below is the canonical 五字段 contract for the stage. SKILL.md
points at these anchors and the model reads on demand. Maintain anchors:
`#stage-<N>` (or `#stage-<N><c|t>` for forked stages).

---
```

Phases:
- `setup-stages.md` → "Setup (Stage 0 / 1 / 2 / 3)"
- `pipeline-conflict.md` → "Conflict Pipeline (Stage 4c / 5c / 6c)"
- `pipeline-transplant.md` → "Transplant Pipeline (Stage 4t / 5t / 6t)"
- `audit-and-verify.md` → "Audit & Verify (Stage 6.5 / 7 / 7.5)"
- `wrap-up.md` → "Wrap-up (Stage 8)"

- [ ] **Step 3: Commit scaffolding**

```bash
cd /Users/dalwin/Documents/AI
git add skills/git-merge-conductor/references/contracts/
git commit -m "$(cat <<'EOF'
feat(git-merge-conductor): v2 scaffold references/contracts/

5 文件骨架：setup-stages, pipeline-conflict, pipeline-transplant,
audit-and-verify, wrap-up. 每个 stage 用 anchor #stage-N 索引。

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

## Task 8: Write `references/contracts/setup-stages.md` (Stage 0/1/2/3)

**Files:**
- Modify: `/Users/dalwin/Documents/AI/skills/git-merge-conductor/references/contracts/setup-stages.md`

- [ ] **Step 1: Add Stage 0 contract**

Append to file:

```markdown
## Stage 0 — Entry Probe & Guards {#stage-0}

**Goal**
You need to verify the repository is in a sane starting state before any
write attempt. Catch impossible-to-recover conditions early. The output of
this stage is a go/no-go decision — if you proceed past Stage 0 with a
broken precondition, every subsequent stage's safety guarantees are voided.

**Inputs**
- Current working directory (must be inside a git repo)
- `git status --porcelain`, `git branch -a`, `.gitmodules` presence, LFS markers
- Existing `.git/merge-conductor/*/state.json` files (for resume detection)

**Decisions you own**
- Whether the repo is invocable at all (not a git repo → hard fail)
- Whether to stash / commit / cancel on dirty work tree (ask user)
- How to handle a same-named existing `merge/<task>` branch (resume / rebuild / cancel)
- How to handle stale or paused sessions in `.git/merge-conductor/` (resume / discard / show-only)

**Hard constraints**
- No write operation allowed in this stage. Read-only checks only.
- Submodules / LFS presence → abort immediately with 中文 error message.
- Never auto-resume a session without user confirmation.
- A v1 session (`state.json::version: "1.0"`) cannot be resumed by v2 — instruct user to abort + restart.

**Outputs**
- Terminal 中文 status briefing
- Stage banner: `[Stage 0 · Entry Probe · iter 1 · tag: none]`
- `state.json::stage_history[0]` appended (kind: "0", tag: null, completed_at)
- `state.json::stage = 1` (after passing)
```

- [ ] **Step 2: Add Stage 1 contract**

Append:

```markdown
## Stage 1 — Input Normalization {#stage-1}

**Goal**
Three different input shapes (branch refs, patch/diff files, freeform task
description) collapse into one normalized task spec that Stage 2 can reason
about. Get this normalization wrong and Stage 2's mode inference makes
decisions on bad data.

**Inputs**
- User's raw invocation arguments (branch names, file paths, or 中文 task description)
- `git log <merge-base>..<source>`, `git diff <merge-base>...<source> --stat`
- Parsed `.patch` / `.diff` files

**Decisions you own**
- task_name (slug from description if not provided; ask user if ambiguous)
- Which source ref(s) to use (could be multiple)
- Which target ref to use (default: current branch)
- Whether to copy patch files into `.git/merge-conductor/<task>/patches/` for archival
- Keyword extraction for relevance judgment (model judgment)

**Hard constraints**
- Do not proceed with empty task_name.
- Echo normalized spec back to user in 中文 before continuing (not a gate, but a sanity check).

**Outputs**
- Normalized task spec (in-memory YAML, see SKILL.md Stage 1 for shape)
- Stage banner: `[Stage 1 · Input Normalization · iter 1 · tag: none]`
- `state.json::stage_history[1]` appended
- `state.json::stage = 2`
```

- [ ] **Step 3: Add Stage 2 contract**

Append:

```markdown
## Stage 2 — Mode Inference, Strategy & Requirement Extraction ★ GATE ★ {#stage-2}

**Goal**
This is the single most important decision in the pipeline. You decide which
mode applies, which pipeline (conflict / transplant) the work runs through,
and you extract the structured requirements list that becomes the
"constitution" for every later stage. Stages 6.5 / 7.5 Phase 2 both depend on
`requirements.yaml` — get it wrong here and the rest of the pipeline either
permits scope creep or rejects valid work.

**Inputs**
- Stage 1 task spec (normalized)
- `references/mode-inference.md` (decision tree + `backport-cherry` vs
  `backport-transplant` thresholds)
- User's natural language intent + clarifications during the gate dialogue

**Decisions you own**
- Choose mode; if confidence < high, present alternatives to user
- Whether to upgrade `backport` to `backport-transplant` (merge_base_age + refactor signals)
- Whether to enable worktree (default yes for complex modes, override allowed)
- Granularity of requirement items (per-feature, per-method, per-file —
  use your judgment based on task complexity; each item must have crisp
  acceptance criteria)
- `scope_tag` text for each item (free-form, e.g., "嘉善养育照护专属",
  "通用课堂功能", "tbd-待用户确认")
- `out_of_scope` per item + `global_out_of_scope` for the task
- `locked_file_rules` (which files unconditionally take target / take source)
- `commit_granularity`, `verification` config

**Hard constraints**
- No write operation until user explicitly says 「策略 OK」 in Chinese (the gate).
- `requirements.yaml` must enumerate the user's intent exhaustively. Any
  item you generated by inference (not direct user statement) must carry
  `ambiguous: true` and force user confirmation in the same gate.
- You may not proceed to Stage 3 with any `ambiguous: true` item unresolved.
- The mode you pick is the mode that runs — do not silently switch later.

**Outputs**
- `.git/merge-conductor/<task>/strategy.md` (rendered from `templates/strategy-report.md`)
- `.git/merge-conductor/<task>/requirements.yaml` (rendered from `templates/requirements.yaml`)
- `state.json::config` populated: mode, pipeline, commit_granularity, verification, locked rules, use_worktree
- `state.json::requirements` mirrored from requirements.yaml
- `state.json::stage_history[2]` appended
- `state.json::stage = 3`
- Stage banner: `[Stage 2 · Mode Inference + Requirement Extraction · iter 1 · tag: none]`
```

- [ ] **Step 4: Add Stage 3 contract**

Append:

```markdown
## Stage 3 — Working Setup {#stage-3}

**Goal**
Materialize the working branch (and worktree, if applicable). After this
stage, the pipeline has a clean isolated workspace to operate on, with
metadata seeded in `.git/merge-conductor/<task>/`.

**Inputs**
- `state.json::config` from Stage 2 (mode, pipeline, use_worktree)
- Target ref + base commit
- `templates/strategy-report.md`, `templates/requirements.yaml`,
  `references/html-report-template.md`

**Decisions you own**
- Worktree path (delegated to `superpowers:using-git-worktrees`)
- Initial seeding of `state.json`, `decision-log.md`, `merge-report.html`,
  `requirements.yaml`, `strategy.md`

**Hard constraints**
- Always tag `merge/<task>/before-step-3` on the main repo before creating
  the working branch / worktree.
- All state metadata stays in `<main-repo>/.git/merge-conductor/<task>/`,
  even when code work happens in a worktree (metadata 主仓化).
- If worktree creation fails for a complex mode, fall back to main-repo
  checkout AND warn the user. Do not silently retry without telling the user.

**Outputs**
- Working branch `merge/<task>` (in worktree or main repo)
- Tag `merge/<task>/before-step-3`
- `state.json::working_branch` populated with name + worktree_path + use_worktree
- `state.json::stage_history[3]` appended
- `state.json::stage = 4`
- Stage banner: `[Stage 3 · Working Setup · iter 1 · tag: merge/<task>/before-step-3]`
```

- [ ] **Step 5: Commit setup-stages.md**

```bash
cd /Users/dalwin/Documents/AI
git add skills/git-merge-conductor/references/contracts/setup-stages.md
git commit -m "$(cat <<'EOF'
feat(git-merge-conductor): v2 setup-stages contract

Stage 0/1/2/3 五字段契约：Goal / Inputs / Decisions you own /
Hard constraints / Outputs. SKILL.md 后续 link 到这里的 anchors.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

## Task 9: Write `references/contracts/pipeline-conflict.md` (Stage 4c/5c/6c)

**Files:**
- Modify: `/Users/dalwin/Documents/AI/skills/git-merge-conductor/references/contracts/pipeline-conflict.md`

- [ ] **Step 1: Add Stage 4c contract**

Append:

```markdown
## Stage 4c — Source-side Application (Conflict Pipeline) {#stage-4c}

**Goal**
Apply the source-side change to the working branch using the mode-specific
git command chain. After this stage, git has either auto-merged cleanly,
or you have unmerged files to classify.

**Inputs**
- `state.json::config.mode` (full-merge | cherry-pick-set | patch-apply |
  backport-cherry | rebase-onto | forward-integrate)
- Source refs / patch files
- Tag `merge/<task>/before-step-4` (you create this first)

**Decisions you own**
- Which command chain to use for the inferred mode (see table in SKILL.md)
- Whether to invoke `--no-commit` flags (always yes where supported — commit
  happens at Stage 7)
- For `forward-integrate`: first phase on source feature branch
  (`git merge <target>`), second phase on working branch

**Hard constraints**
- Tag `merge/<task>/before-step-4` before any merge / cherry-pick / am.
- If the command fails non-recoverably (e.g., empty cherry-pick range),
  stop and instruct user how to recover via the tag. Do not silently retry.

**Outputs**
- Working tree with merged content + possibly conflict markers
- List of unmerged files (`git diff --name-only --diff-filter=U`)
- `state.json::stage_history[4]` appended (kind: "4c")
- `state.json::stage = 5`
- Stage banner: `[Stage 4c · Source-side Application · iter <i> · tag: merge/<task>/before-step-4]`
```

- [ ] **Step 2: Add Stage 5c contract**

Append:

```markdown
## Stage 5c — Conflict Classification + Auto-resolve (Conflict Pipeline) {#stage-5c}

**Goal**
Classify each conflict hunk as A/B/C/D and auto-resolve A class. Build the
queue of C/D class items that Stage 6c will process autonomously.

**Inputs**
- Unmerged files from Stage 4c
- `references/conflict-classification.md` (A/B/C/D rules, mode-aware adjustments)
- `state.json::config.locked_file_rules` (user-specified overrides)

**Decisions you own**
- For each hunk, which class fits (A/B/C/D)
- For A class: use `git checkout --theirs` (whole file) or hunk-level rewrite
  (your judgment, based on hunk size and surrounding context)
- For backport-cherry mode: demote A class to "log-then-take-target"
  (not silent)

**Hard constraints**
- Apply `locked_file_rules` FIRST — they override classification.
- B class (git already auto-merged) requires no action; just count.
- Tag `merge/<task>/before-step-5` once before any auto-resolution.
- Every A class application MUST append to `decision-log.md`.

**Outputs**
- C/D class decision queue (in `state.json::decisions[]`)
- `state.json::auto_resolved_summary` populated (A/B counts, A files,
  demoted-A list for backport)
- `state.json::stage_history[5]` appended (kind: "5c")
- `state.json::stage = 6`
- HTML report `<section id="auto-resolved">` appended
- Stage banner: `[Stage 5c · Conflict Classification · iter <i> · tag: merge/<task>/before-step-5]`
```

- [ ] **Step 3: Add Stage 6c contract**

Append:

```markdown
## Stage 6c — Autonomous C/D Decision Loop (Conflict Pipeline) {#stage-6c}

**Goal**
For each C/D class hunk in the decision queue, autonomously pick a resolution
(no user mid-loop interruption) using the heuristic ladder. Hunks that the
ladder cannot decide get marked `unresolved` (NOT left as `<<<<<<<` markers
in code) and surface in Stage 7.5 Phase 2 for user adjudication.

**Inputs**
- Decision queue from Stage 5c
- `references/conflict-classification.md` (C/D autonomous heuristics section)
- `state.json::config.locked_file_rules`
- `requirements.yaml::global_out_of_scope`

**Decisions you own**
- Which heuristic ladder rung matches each hunk (in priority order):
  1. locked_file_rules / global_out_of_scope match → apply rule
  2. Both sides additive (no overlapping logic) → take both (concatenate)
  3. One side is whitespace-only / comment-only → take the other
  4. Source side older than target's most recent change to this location → take target
  5. Otherwise → mark `unresolved`, take target as code fallback

**Hard constraints**
- NEVER leave `<<<<<<< HEAD ... =======  ... >>>>>>>` markers in code.
  Marker would break Stage 7.5 Phase 1 compile check and cascade errors.
- For "unresolved" hunks: code keeps target version (safest fallback);
  the source hunk is preserved in `.git/merge-conductor/<task>/unresolved.md`
  for Phase 2 user review.
- After each hunk decision, immediately invoke Stage 6.5 self-audit. Do
  NOT batch-audit at end.
- Tag `merge/<task>/before-step-6` once before the loop starts.

**Outputs**
- Resolved hunks staged via `git add`
- `state.json::decisions[]` updated with `resolution`, `taken`, `audited_at`
- `state.json::unresolved[]` populated for hunks falling to rung 5
- `.git/merge-conductor/<task>/unresolved.md` written
- `state.json::stage_history[6]` appended (kind: "6c")
- `state.json::stage = 6.5` (then immediately into 6.5 audit per-unit, then back to 6c for next hunk)
- Stage banner: `[Stage 6c · Autonomous Decision Loop · iter <i> · tag: merge/<task>/before-step-6]`
```

- [ ] **Step 4: Commit pipeline-conflict.md**

```bash
cd /Users/dalwin/Documents/AI
git add skills/git-merge-conductor/references/contracts/pipeline-conflict.md
git commit -m "$(cat <<'EOF'
feat(git-merge-conductor): v2 pipeline-conflict contract

Stage 4c/5c/6c 五字段契约。6c 改 autonomous，per-hunk 启发式 ladder
+ unresolved 落 audit 不留 conflict marker。

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

## Task 10: Write `references/contracts/pipeline-transplant.md` (Stage 4t/5t/6t)

**Files:**
- Modify: `/Users/dalwin/Documents/AI/skills/git-merge-conductor/references/contracts/pipeline-transplant.md`

- [ ] **Step 1: Add Stage 4t contract**

Append:

```markdown
## Stage 4t — Build Grafting Plan (Transplant Pipeline) {#stage-4t}

**Goal**
Translate `requirements.yaml` into a "per-item × per-target-location" grafting
matrix. Each entry pairs a source-side implementation with the target-side
landing spot and the strategy for grafting. After this stage, Stage 5t/6t
have a concrete unit of work per row.

**Inputs**
- `requirements.yaml` (all items)
- Source branch HEAD / range
- `references/semantic-mapping.md` (rename / grep / similar-signature heuristics)
- Target branch HEAD diff history (for refactor detection)

**Decisions you own**
- For each item × target_location: which source commits / hunks supply the implementation
- Mapping confidence (high / medium / low) per target_location, with evidence chain
- `graft_strategy` from {replace, merge-into, add-new, guarded-overlay}
  - `replace`: target counterpart is a stub
  - `merge-into`: target has its own implementation that needs the source logic merged in
  - `add-new`: target has nothing at this location
  - `guarded-overlay`: source logic guarded by `guard_condition` (e.g., scope_tag-derived)
- `guard_condition` (when strategy == guarded-overlay)

**Hard constraints**
- Tag `merge/<task>/before-step-4` first.
- Every graft must point back to a `requirements.yaml::items[i].id` — no orphan grafts.
- If a target_location confidence is `low`, do NOT set strategy = `replace`.
- Mapping evidence MUST be written down (the grafting plan is reviewed by user implicitly via Phase 2).

**Outputs**
- `.git/merge-conductor/<task>/grafting-plan.yaml` (one entry per graft)
- `state.json::grafts[]` mirrored
- `state.json::stage_history[4]` appended (kind: "4t")
- `state.json::stage = 5`
- Stage banner: `[Stage 4t · Build Grafting Plan · iter <i> · tag: merge/<task>/before-step-4]`
```

- [ ] **Step 2: Add Stage 5t contract**

Append:

```markdown
## Stage 5t — Per-Item Draft (Transplant Pipeline) {#stage-5t}

**Goal**
For each graft, produce a concrete unified-diff draft (does NOT apply to disk)
plus a context summary + confidence self-assessment + soft out_of_scope check.
Drafts are the artifacts Stage 6t will autonomously apply.

**Inputs**
- `grafting-plan.yaml`
- Source-side hunks (`git show -W <sha> -- <file>`)
- Target-side current content
- `requirements.yaml::items[i].out_of_scope`

**Decisions you own**
- Diff content for each graft (the actual edit to apply)
- Confidence (combines `target_location.confidence` from Stage 4t + how cleanly the draft sits in target context)
- Soft out_of_scope match (this is a draft-time pre-filter; Stage 6.5 is the authoritative audit)

**Hard constraints**
- Drafts go to `.git/merge-conductor/<task>/drafts/G-<id>.diff` — never to the working tree directly.
- Each draft must include the context summary in 中文 (so audit / report can show it).
- If a draft contains changes to files outside `requirements.yaml::items[i].target_locations`,
  fail the draft now (set draft_status: rejected, reason: "files outside target_locations").

**Outputs**
- `.git/merge-conductor/<task>/drafts/G-<id>.diff` for each graft
- `.git/merge-conductor/<task>/drafts/G-<id>.md` (context summary, rendered from `templates/draft.md`)
- `grafting-plan.yaml::plan[i].draft_status` updated to drafted | rejected
- `state.json::stage_history[5]` appended (kind: "5t")
- `state.json::stage = 6`
- Stage banner: `[Stage 5t · Per-Item Draft · iter <i> · tag: none]`
```

- [ ] **Step 3: Add Stage 6t contract**

Append:

```markdown
## Stage 6t — Autonomous Apply Loop (Transplant Pipeline) {#stage-6t}

**Goal**
For each drafted graft, autonomously apply it (no user mid-loop) using the
strategy + confidence determined earlier. Immediately invoke Stage 6.5
self-audit; pass → mark `applied`, fail → rollback + mark `partial`/`pending`
and surface in Stage 7.5 Phase 2.

**Inputs**
- Drafts from Stage 5t
- `grafting-plan.yaml`
- `references/negative-constraints.md` (for Stage 6.5 invocation)
- Strategy safety order: `add-new` < `merge-into` < `guarded-overlay` < `replace`

**Decisions you own**
- Apply order (typically by safety: safest first; or by graft_id sequence — your judgment)
- Whether to immediately apply a low-confidence graft (yes, but mark ⚠ for Phase 2)
  vs defer entirely (only if `draft_status: rejected` already)

**Hard constraints**
- Tag `merge/<task>/before-step-6` once before the loop.
- After EACH graft apply, run Stage 6.5 self-audit. Fail → `git reset --hard`
  the just-applied content for that graft, mark `partial`, continue.
- Drafts with `draft_status: rejected` from Stage 5t do NOT apply; carry forward to Phase 2.

**Outputs**
- Applied grafts on working tree (where audit passed)
- `grafting-plan.yaml::plan[i].draft_status` updated to applied | rejected
- `state.json::grafts[i].status` per item
- `state.json::stage_history[6]` appended (kind: "6t")
- `state.json::stage = 6.5` (per-unit immediately) then back to 6t until queue empty
- Stage banner: `[Stage 6t · Autonomous Apply Loop · iter <i> · tag: merge/<task>/before-step-6]`
```

- [ ] **Step 4: Commit pipeline-transplant.md**

```bash
cd /Users/dalwin/Documents/AI
git add skills/git-merge-conductor/references/contracts/pipeline-transplant.md
git commit -m "$(cat <<'EOF'
feat(git-merge-conductor): v2 pipeline-transplant contract

Stage 4t/5t/6t 五字段契约。autonomous apply + per-graft 即时
Stage 6.5 audit + rollback on fail，对应 care-class 失配主因。

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

## Task 11: Write `references/contracts/audit-and-verify.md` (Stage 6.5 / 7 / 7.5)

**Files:**
- Modify: `/Users/dalwin/Documents/AI/skills/git-merge-conductor/references/contracts/audit-and-verify.md`

- [ ] **Step 1: Add Stage 6.5 contract**

Append:

```markdown
## Stage 6.5 — Negative-Constraint Self-Audit {#stage-65}

**Goal**
After each unit of work (graft applied in 6t, or hunk decided in 6c),
verify it doesn't violate any negative constraint. This is the single most
important defense against scope creep — care-class scope creep happened
because v1 lacked this stage.

**Inputs**
- The just-applied unit (graft or hunk)
- `requirements.yaml::items[i].out_of_scope` (per-item)
- `requirements.yaml::global_out_of_scope`
- `references/negative-constraints.md` (NC-01~NC-05 + appendix)
- Stage 6c/6t output state

**Decisions you own**
- Which NC rules to evaluate (typically all; some are file-type-specific)
- For "soft" violations (e.g., a `projectName ==` that the user might still want):
  whether the scope_tag justifies the exception (read `requirements.yaml::items[i].scope_tag`)

**Hard constraints**
- Pass / fail is binary. Soft warnings still go in `audit-report.md` but
  don't trigger rollback.
- Any hit on NC-05 (change outside target_locations) is a HARD fail — Safety Invariant 6.
- Rollback uses `git reset --hard merge/<task>/before-step-6` then re-applies
  prior siblings in order; for granular rollback (single graft) use
  `git revert --no-commit <staged change>` if possible, else full reset + replay.
- Audit report MUST be written before returning control to 6c/6t.

**Outputs**
- `.git/merge-conductor/<task>/audit/<unit-id>.md` (rendered from
  `templates/audit-report.md`)
- `state.json::audit[]` appended
- For fail: rollback executed, unit status set to `partial` (transplant) or
  `unresolved` (conflict)
- For pass: unit status `applied`; continue to next unit in 6c/6t
- `state.json::stage_history[6.5]` appended (kind: "6.5") on first invocation per iter
  (subsequent same-iter invocations bump `state.json::audit[]` length only)
- Stage banner emitted ONLY on first invocation per iter: `[Stage 6.5 · Self-Audit · iter <i> · tag: none]`
```

- [ ] **Step 2: Add Stage 7 contract**

Append:

```markdown
## Stage 7 — Finalization & Commit {#stage-7}

**Goal**
Commit the working branch state per `state.json::config.commit_granularity`.
This is the last write before Phase 1 verification.

**Inputs**
- Working tree (all applied units staged in 6c/6t via `git add`)
- `state.json::config.commit_granularity`
- `templates/commit-message.md`

**Decisions you own**
- Per-mode commit shape (single merge / per-source-commit / squash)
- Rewriting auto-generated commits (from `git am` / `git rebase`) with
  the structured `merge:` prefix message

**Hard constraints**
- Use heredoc `git commit -m "$(cat <<'EOF' ... EOF)"` to preserve formatting.
- Commit message must include: 中文 subject, source ref + sha, mode,
  decision summary, A class auto-handled count, iteration number, rolled-back items.
- Tag `merge/<task>/done` after commit(s).

**Outputs**
- Commit(s) on `merge/<task>` branch
- Tag `merge/<task>/done`
- `state.json::status = pre-verified` (NOT `finalized` until Phase 2 passes)
- `state.json::stage_history[7]` appended (kind: "7")
- `state.json::stage = 7.5`
- Stage banner: `[Stage 7 · Finalization · iter <i> · tag: merge/<task>/done]`
```

- [ ] **Step 3: Add Stage 7.5 contract**

Append:

```markdown
## Stage 7.5 — Verification Loop {#stage-75}

Two phases. Phase 1 is automated; Phase 2 is the user's final gate.

### Phase 1 — Automated Verification

**Goal**
Catch broken builds, type errors, lint failures, and scope-test regressions
before bothering the user. If anything fails, run a bounded self-fix loop.
If self-fix exhausts its budget, hand the error verbatim to Phase 2.

**Inputs**
- `state.json::config.verification` (compile, lint, test settings)
- Working tree state at `merge/<task>/done` tag
- Project files (pom.xml / package.json / go.mod / pyproject.toml etc.) for tool detection

**Decisions you own**
- Tool selection per language signal (Maven mvn compile / npm tsc / go build / ruff)
- Test scope when `test: scope` — which suites correspond to `requirements.yaml::items[*].target_locations`
- Fix strategy when a test fails — which graft / hunk likely caused it (map error → file → graft)

**Hard constraints**
- Self-fix iteration cap: N ≤ 3.
- Each fix iteration: tag `merge/<task>/before-fix-iter-<N>`, rollback the
  guilty unit, regenerate draft, re-audit (Stage 6.5), reapply.
- After 3 failed iters, surrender — pass full error text to Phase 2 verbatim.
- Append to `state.json::iterations[]` each iter with trigger: `phase1-fix`.

**Outputs**
- Phase 1 result (pass / fail-with-errors) into `state.json::verification.phase1`
- `state.json::stage_history[7.5]` appended (kind: "7.5") on first Phase 1 entry
- Stage banner: `[Stage 7.5 · Phase 1 Verification · iter <i> · tag: merge/<task>/before-fix-iter-<N>]`

### Phase 2 — User Final Gate

**Goal**
The user's only mid-pipeline interrupt after Stage 2. Present a single
report — automation results + requirements coverage + audit-intercepted
items — and let the user say "完成 / REQ-X 没做对 / REQ-X 不该做 / 还多 Z".

**Inputs**
- Phase 1 result
- `requirements.yaml::items[]` with current `status` and `evidence`
- `state.json::audit[]` (all intercepts)
- `state.json::unresolved[]` (conflict-pipeline only)
- `state.json::grafts[]` (transplant-pipeline only)

**Decisions you own**
- How to organize the report sections (template at `templates/verification-report.md`)
- How to parse user's free-form response into one of: 完成 / REQ-X 没做对 / REQ-X 不该做 / 还多 Z / 自由文本
- For free-form: echo back "我理解为: ..." in 中文 for confirmation before acting

**Hard constraints**
- This is the ONLY mid-pipeline interrupt point. Don't interrupt earlier.
- Report MUST be written to both terminal (中文) and `merge-report.html`.
- User says 「完成」 → mark `state.json::status = finalized`, proceed to Stage 8.
- Any other user response → bump `state.json::iter`, append to `iterations[]`
  with appropriate trigger, route back to 4-6 (transplant: 4t / conflict: 5c).
- NEVER auto-decide "完成" without explicit user confirmation.

**Outputs**
- Terminal markdown report + HTML report `<section id="verification">` updated
- For 完成 path: `state.json::status = finalized`, `state.json::finalized_at = now`
- For loop path: `state.json::iter += 1`, `state.json::stage = 4` (or 5),
  `iterations[]` appended with trigger and user_feedback
- Stage banner: `[Stage 7.5 · Phase 2 User Gate · iter <i> · tag: none]`
```

- [ ] **Step 4: Commit audit-and-verify.md**

```bash
cd /Users/dalwin/Documents/AI
git add skills/git-merge-conductor/references/contracts/audit-and-verify.md
git commit -m "$(cat <<'EOF'
feat(git-merge-conductor): v2 audit-and-verify contract

Stage 6.5 self-audit + Stage 7 commit + Stage 7.5 双 Phase 校验循环。
Phase 1 N=3 自修复上限；Phase 2 唯一 final gate。

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

## Task 12: Write `references/contracts/wrap-up.md` (Stage 8)

**Files:**
- Modify: `/Users/dalwin/Documents/AI/skills/git-merge-conductor/references/contracts/wrap-up.md`

- [ ] **Step 1: Add Stage 8 contract**

Append:

```markdown
## Stage 8 — Wrap-up + Cleanup Options {#stage-8}

**Goal**
Summarize the merge outcome for the user, present cleanup options
(including the new worktree decision), and archive the report.

**Inputs**
- All session metadata (`state.json`, `decision-log.md`, audit reports, drafts)
- `templates/wrap-up-report.md`

**Decisions you own**
- Report content selection (top-N most impactful decisions to highlight)
- Cleanup-policy default for the task

**Hard constraints**
- Status MUST be `finalized` (set by Stage 7.5 Phase 2 完成 path).
- Final HTML report `<header><dl>` status field must show `finalized`.
- Worktree cleanup choice must be presented for any session where
  `state.json::working_branch.use_worktree == true`.

**Outputs**
- Terminal 中文 wrap-up report
- HTML report finalized (archive-ready)
- `state.json::cleanup_policy` persisted
- `state.json::stage_history[8]` appended (kind: "8")
- Stage banner: `[Stage 8 · Wrap-up · iter <final> · tag: merge/<task>/done]`
```

- [ ] **Step 2: Commit wrap-up.md**

```bash
cd /Users/dalwin/Documents/AI
git add skills/git-merge-conductor/references/contracts/wrap-up.md
git commit -m "$(cat <<'EOF'
feat(git-merge-conductor): v2 wrap-up contract

Stage 8 五字段契约 + worktree cleanup option 提示。

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

## Task 13: Rewrite `SKILL.md` 主薄化 — replace Stage sections with薄壳 + Reading Order

**Files:**
- Modify: `/Users/dalwin/Documents/AI/skills/git-merge-conductor/SKILL.md`

This is a large but mechanical refactor. SKILL.md becomes a skeleton pointing to contracts.

- [ ] **Step 1: Read full current SKILL.md**

Run: `wc -l /Users/dalwin/Documents/AI/skills/git-merge-conductor/SKILL.md`
Expected: ~378 lines (post Phase 1 changes).

- [ ] **Step 2: Replace Stage 0 section body (keep header, Safety Invariant references already updated in Phase 1)**

Use the Edit tool. Find the entire Stage 0 body (between `## Stage 0` and `## Stage 1`) and replace with:

```markdown
## Stage 0 — Entry Probe & Guards

**职责**：read-only 仓库环境检查；submodule/LFS/dirty 状态 → 询问或中止；
检测旧会话给出 resume/discard/show-only 选择。

**详细契约**：`references/contracts/setup-stages.md#stage-0`
```

- [ ] **Step 3: Replace Stage 1 section body**

Replace Stage 1 body with:

```markdown
## Stage 1 — Input Normalization

**职责**：三种输入形态（branch refs / patch-diff / 任务描述）归一化为
task spec；提取关键字、enumerate source commits、archive patch files。

**详细契约**：`references/contracts/setup-stages.md#stage-1`
```

- [ ] **Step 4: Replace Stage 2 section body**

Replace Stage 2 body with:

```markdown
## Stage 2 — Mode Inference, Strategy & Requirement Extraction ★ GATE ★

**职责**：判断 mode + 选 pipeline (conflict / transplant) + 提取
`requirements.yaml`（含 `scope_tag` + `out_of_scope` 每项）+ 产出策略报告。
后续所有写操作以此为基础。

**Hard gate**：用户未明确「策略 OK」前禁止任何写操作。

**详细契约**：`references/contracts/setup-stages.md#stage-2`
**决策依据**：`references/mode-inference.md`
**清单模板**：`templates/requirements.yaml`
```

- [ ] **Step 5: Replace Stage 3 section body**

Replace Stage 3 body with:

```markdown
## Stage 3 — Working Setup

**职责**：复杂 mode 委托 `superpowers:using-git-worktrees` 创建 worktree；
简单 mode 主仓 checkout `merge/<task>`。.git/merge-conductor 数据仍在主仓
(metadata 主仓化)。

**详细契约**：`references/contracts/setup-stages.md#stage-3`
```

- [ ] **Step 6: Replace Stage 4 / 5 / 5.5 / 6 with fork pointer block**

The old Stage 4 / 5 / 5.5 / 6 sections collapse into a single "Stage 4-6 (mode-aware fork)" pointer block:

```markdown
## Stage 4-6 — Mode-aware Fork

By `state.json::pipeline`:

### conflict-pipeline (full-merge | cherry-pick-set | patch-apply | backport-cherry | rebase-onto | forward-integrate)

- **Stage 4c** source-side apply (mode-specific git command chain)
- **Stage 5c** A/B/C/D classification + A class auto-resolve
- **Stage 6c** autonomous C/D decision via heuristic ladder; unresolved → audit, not marker

**详细契约**：`references/contracts/pipeline-conflict.md`
**决策依据**：`references/conflict-classification.md`

### transplant-pipeline (backport-transplant | semantic-transplant)

- **Stage 4t** build grafting plan (requirement × target location matrix)
- **Stage 5t** per-item draft (semantic mapping → suggested diff, off-tree)
- **Stage 6t** autonomous apply + per-graft immediate Stage 6.5 audit

**详细契约**：`references/contracts/pipeline-transplant.md`
**决策依据**：`references/semantic-mapping.md`
**模板**：`templates/grafting-plan.yaml`, `templates/draft.md`

Stage 6.5 (Negative-Constraint Self-Audit) is invoked per-unit at the end of each 6c hunk decision / 6t graft apply, not as a separate batch stage.
```

- [ ] **Step 7: Replace Stage 7 / 7.5 / 8 with pointer blocks**

```markdown
## Stage 6.5 — Negative-Constraint Self-Audit

**职责**：per-unit 即时 audit；命中 NC 规则或 `out_of_scope` → rollback +
标 partial/unresolved 进 Phase 2 报表。NC-05 (改动越界 `target_locations`)
对应 Safety Invariant 6 硬性 rollback。

**详细契约**：`references/contracts/audit-and-verify.md#stage-65`
**规则库**：`references/negative-constraints.md`
**模板**：`templates/audit-report.md`

## Stage 7 — Finalization & Commit

**职责**：按 `commit_granularity` 提交；commit message 含 iter 信息 +
rolled-back 项 + audit 摘要。tag `merge/<task>/done`。状态置 `pre-verified`，
NOT `finalized` (要等 Phase 2 通过)。

**详细契约**：`references/contracts/audit-and-verify.md#stage-7`
**模板**：`templates/commit-message.md`

## Stage 7.5 — Verification Loop

**Phase 1 (自动化)**：compile/lint/scope-test，失败 model 自修复 loop (N≤3)
后投降把错误带给用户。
**Phase 2 (用户兜底 ★ FINAL GATE ★)**：渲染需求清单 vs 已合并差异表 +
audit 拦截项；用户「完成 / REQ-X 没做对 / REQ-X 不该做 / 还多 Z」决定。
Phase 2 是 Stage 2 之外唯一 mid-pipeline 中断点。

**详细契约**：`references/contracts/audit-and-verify.md#stage-75`
**模板**：`templates/verification-report.md`

## Stage 8 — Wrap-up + Cleanup

**职责**：终端 + HTML 终态报告；4 个 cleanup 选项 + worktree 清理子选项；
status = finalized 持久化。

**详细契约**：`references/contracts/wrap-up.md#stage-8`
**模板**：`templates/wrap-up-report.md`
```

- [ ] **Step 8: Update "Reading order for references" table**

Find the existing Reading order table near the end of SKILL.md and replace with:

```markdown
## Reading Order for References

Read on demand per stage:

| Stage | Required Reference Read |
|---|---|
| Stage 0 / 1 | `references/contracts/setup-stages.md#stage-0`, `#stage-1` |
| Stage 2 | `references/contracts/setup-stages.md#stage-2`, `references/mode-inference.md` |
| Stage 3 | `references/contracts/setup-stages.md#stage-3`, `references/state-schema.md` |
| Stage 4-6 (conflict) | `references/contracts/pipeline-conflict.md`, `references/conflict-classification.md` |
| Stage 4-6 (transplant) | `references/contracts/pipeline-transplant.md`, `references/semantic-mapping.md` |
| Stage 6.5 | `references/contracts/audit-and-verify.md#stage-65`, `references/negative-constraints.md` |
| Stage 7 | `references/contracts/audit-and-verify.md#stage-7` |
| Stage 7.5 | `references/contracts/audit-and-verify.md#stage-75`, `references/html-report-template.md` |
| Stage 8 | `references/contracts/wrap-up.md` |
| Recovery / Pause / Abort | `references/recovery-protocol.md` |

Templates are read just-in-time when about to render output.
```

- [ ] **Step 9: Verify SKILL.md length is ~200-220 lines**

Run: `wc -l /Users/dalwin/Documents/AI/skills/git-merge-conductor/SKILL.md`
Expected: ~200-220 lines (the spec target). If significantly larger, prune verbose sections; if much smaller (<150), check that all stage pointer blocks are present.

- [ ] **Step 10: Commit**

```bash
cd /Users/dalwin/Documents/AI
git add skills/git-merge-conductor/SKILL.md
git commit -m "$(cat <<'EOF'
refactor(git-merge-conductor): v2 SKILL.md 主薄化

每 Stage 收缩到 3-4 行职责 + 「详细契约」link，详细内容下沉到
references/contracts/。Reading Order 重新映射。整体规模从 ~378 行
降到 ~200-220 行。

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

## Task 14: Phase 2 smoke gate — re-run scenarios A, C, E

**Files:**
- Modify: `/Users/dalwin/Documents/AI/docs/superpowers/verification/git-merge-conductor/SMOKE-TEST.md`

- [ ] **Step 1: Run scenario A in a fresh fixture**

```bash
cd /tmp && rm -rf gmc-fixture
bash /Users/dalwin/Documents/AI/docs/superpowers/verification/git-merge-conductor/setup-fixture.sh
```

Then start Claude Code session in `/tmp/gmc-fixture/` and run scenario A.

Expected: skill correctly resolves contract files (no broken links), all stages emit banners, state.json has `version: "2.0"` and `stage_history` 完整.

- [ ] **Step 2: Run scenario C (patch-apply)**

Same as Step 1 but for scenario C. Expected: patch-apply mode still works, no transplant-pipeline accidentally invoked.

- [ ] **Step 3: Run scenario E (guard)**

Verify Stage 0 guards (submodule / LFS / dirty tree) still fire correctly.

- [ ] **Step 4: Append Phase 2 gate to SMOKE-TEST.md**

Append:

```markdown
## v2 Phase 2 gate (2026-05-13)
- [ ] Scenario A re-run with 主薄化 SKILL.md: all stages emit banner, contracts resolve correctly.
- [ ] Scenario C re-run: patch-apply mode unchanged.
- [ ] Scenario E re-run: guards fire as v1.
- [ ] SKILL.md line count between 200-220.
```

- [ ] **Step 5: Commit**

```bash
cd /Users/dalwin/Documents/AI
git add docs/superpowers/verification/git-merge-conductor/SMOKE-TEST.md
git commit -m "$(cat <<'EOF'
test(git-merge-conductor): v2 Phase 2 smoke gate notes

Phase 2 主薄化 + contracts 完成后 A/C/E 不回归验证。

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

# Phase 3 — Stage 2 需求清单

**Goal of phase:** `templates/requirements.yaml` schema 落地；`strategy-report.md` 加渲染锚点；Stage 2 提取流程契约就位。

## Task 15: Create `templates/requirements.yaml`

**Files:**
- Create: `/Users/dalwin/Documents/AI/skills/git-merge-conductor/templates/requirements.yaml`

- [ ] **Step 1: Write the schema template**

Content (verbatim from spec §5.1):

```yaml
# requirements.yaml — Stage 2 产物，作为 Stage 6.5 / 7.5 Phase 2 的对照宪法
#
# 渲染规则：
# - 中文 fixed text 保持；占位符用 {{var_name}} (English)
# - items 数组按用户需求逐项展开；每项必填 acceptance + out_of_scope
# - 模糊条目（模型推断非用户直说）必须 ambiguous: true，Stage 2 Gate 必须澄清

task: {{task_name}}
extracted_at: {{iso_timestamp}}

items:
  - id: REQ-{{nn}}
    title: {{中文一句话}}
    scope_tag: {{free_text}}            # 自由文本，由 Stage 2 model 按 task 起；
                                        # 例："嘉善养育照护专属" / "通用课堂功能" / "tbd-待用户确认"
    target_locations:                   # 改动位置（可为空，由 Stage 4t/5c 推断填充）
      - file: {{relative_path}}
        symbol: {{class_or_method}}     # 可选
    acceptance:                         # 完成判据；Phase 2 用户兜底报表用
      - {{中文一行}}
      - {{中文一行}}
    out_of_scope:                       # per-item 负向约束（喂给 Stage 6.5）
      - {{中文一行}}
    status: pending                     # pending | partial | completed | abandoned
                                        # Stage 6 / 6.5 / 7 / 7.5 维护
    evidence:                           # 完成证据
      commits: []
      files_touched: []
    ambiguous: false                    # 模糊条目必须 true，需用户确认才能进 Stage 3

global_out_of_scope:                    # 全局负向约束（适用所有 item）
  - {{自动从 references/negative-constraints.md 通用条目注入}}
  - {{用户在 Stage 2 自定义补充，可选}}
```

- [ ] **Step 2: Commit**

```bash
cd /Users/dalwin/Documents/AI
git add skills/git-merge-conductor/templates/requirements.yaml
git commit -m "$(cat <<'EOF'
feat(git-merge-conductor): v2 requirements.yaml schema template

Stage 2 强制产物，含 scope_tag 自由文本 / per-item out_of_scope /
ambiguous 标记 / status 生命周期。Stage 6.5 + 7.5 Phase 2 对照基线。

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

## Task 16: Update `templates/strategy-report.md` 加 requirements 渲染锚点

**Files:**
- Modify: `/Users/dalwin/Documents/AI/skills/git-merge-conductor/templates/strategy-report.md`

- [ ] **Step 1: Read existing strategy-report.md**

Run: `cat /Users/dalwin/Documents/AI/skills/git-merge-conductor/templates/strategy-report.md`

- [ ] **Step 2: Add a "需求清单" section at the end**

Append (or insert before the final remarks block):

```markdown
## 需求清单（requirements.yaml 同源）

| ID | 标题 | scope_tag | target_locations | acceptance | out_of_scope | ambiguous |
|---|---|---|---|---|---|---|
{{requirement_table_rows}}

> Stage 2 Gate 前请人工核对此清单——尤其 `ambiguous: true` 条目和 `out_of_scope`
> 是否齐全。后续 Stage 6.5 自审与 Stage 7.5 Phase 2 兜底报表都以本清单为基线。
```

- [ ] **Step 3: Commit**

```bash
cd /Users/dalwin/Documents/AI
git add skills/git-merge-conductor/templates/strategy-report.md
git commit -m "$(cat <<'EOF'
refactor(git-merge-conductor): v2 strategy-report 加 requirements 锚点

Strategy 报告末尾渲染需求清单表，方便 Gate 阶段人工核对。

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

## Task 17: Update `references/contracts/setup-stages.md#stage-2` 补充 ambiguous handling 细节

**Files:**
- Modify: `/Users/dalwin/Documents/AI/skills/git-merge-conductor/references/contracts/setup-stages.md`

- [ ] **Step 1: Add an "Ambiguous Item Handling" sub-section under Stage 2**

Append within the Stage 2 anchor block, before its `**Outputs**` field:

```markdown

### Ambiguous Item Handling (Stage 2 sub-protocol)

An item is `ambiguous: true` when:
- You inferred it from context (not direct user statement), OR
- The acceptance criteria you wrote could be interpreted multiple ways, OR
- target_locations is empty AND you cannot determine where it lands

For each ambiguous item, during the Gate dialogue:
1. Show the item to the user in 中文 with the reason flagged
2. Ask: "REQ-X 是 ___ 吗？" with concrete clarification options
3. On user response, set `ambiguous: false`, update title/acceptance/scope_tag accordingly
4. If user says "skip" → set `status: abandoned` (not pending), item stays in requirements.yaml for record-keeping but does not block Stage 3

You may not exit Stage 2 with any `ambiguous: true` item unresolved.
```

- [ ] **Step 2: Commit**

```bash
cd /Users/dalwin/Documents/AI
git add skills/git-merge-conductor/references/contracts/setup-stages.md
git commit -m "$(cat <<'EOF'
refactor(git-merge-conductor): v2 stage-2 ambiguous handling sub-protocol

Ambiguous item 强制澄清流程：标志 → 中文询问 → 用户响应 → 状态
转换；不允许带 ambiguous=true 进 Stage 3。

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

## Task 18: Phase 3 smoke gate — scenario A re-run validating requirements.yaml output

**Files:**
- Modify: `/Users/dalwin/Documents/AI/docs/superpowers/verification/git-merge-conductor/SMOKE-TEST.md`

- [ ] **Step 1: Re-run scenario A in fresh fixture**

Same setup as Phase 1 Step 1.

When scenario A reaches Stage 2 Gate, verify the model produces both `strategy.md` AND `requirements.yaml` in `.git/merge-conductor/<task>/`.

- [ ] **Step 2: Inspect requirements.yaml**

After Gate:
```bash
cat /tmp/gmc-fixture/.git/merge-conductor/scenario-a/requirements.yaml
```
Expected: valid YAML with `task`, `items`, `global_out_of_scope`; at least 1 item with all required fields.

- [ ] **Step 3: Verify state.json mirrors requirements**

```bash
cat /tmp/gmc-fixture/.git/merge-conductor/scenario-a/state.json | jq '.requirements | length'
```
Expected: > 0.

- [ ] **Step 4: Append Phase 3 gate to SMOKE-TEST.md**

```markdown
## v2 Phase 3 gate (2026-05-13)
- [ ] Scenario A produces requirements.yaml at Stage 2
- [ ] requirements.yaml valid YAML, has items with scope_tag + out_of_scope + acceptance
- [ ] state.json::requirements mirrors items array
- [ ] No ambiguous: true items left after Gate
```

- [ ] **Step 5: Commit**

```bash
cd /Users/dalwin/Documents/AI
git add docs/superpowers/verification/git-merge-conductor/SMOKE-TEST.md
git commit -m "$(cat <<'EOF'
test(git-merge-conductor): v2 Phase 3 smoke gate notes

Stage 2 需求清单产物验证。

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

# Phase 4 — transplant-pipeline

**Goal of phase:** mode-inference 拆分 `backport-cherry` / `backport-transplant`；`templates/grafting-plan.yaml` + `templates/draft.md` 落地；`semantic-mapping.md` 输出对齐；新增 scenario F fixture (care-class) 全链路通过。

## Task 19: Update `references/mode-inference.md` — add backport 拆分阈值

**Files:**
- Modify: `/Users/dalwin/Documents/AI/skills/git-merge-conductor/references/mode-inference.md`

- [ ] **Step 1: Read existing mode-inference.md**

Run: `cat /Users/dalwin/Documents/AI/skills/git-merge-conductor/references/mode-inference.md`
Note the current `backport` branch in the decision tree.

- [ ] **Step 2: Replace the existing `backport` decision with split**

Find the section defining `mode: backport` and replace with:

```markdown
## Backport mode — sub-classification

When the high-level decision is `backport`, run this sub-classifier to pick the
pipeline:

### `backport-cherry` (conflict-pipeline)

Conditions (ALL must hold):
- `merge_base_age_days < T_AGE` (default T_AGE = 30 days)
- Source's affected files have NO target-side rename/move/refactor signal
  within the same files since merge-base
- All source commits are independently cherry-pickable (no commits depend on
  intermediate commits not being included)

`backport-cherry` runs the standard conflict-pipeline (Stage 4c/5c/6c).

### `backport-transplant` (transplant-pipeline)

Triggered when ANY of:
- `merge_base_age_days >= T_AGE`
- ≥ N (default N = 3) target-side rename/move/refactor signals within
  affected files since merge-base (signals detected by:
  `git log --all --diff-filter=R --find-renames=70% -- <file>` count)
- User explicitly requests "语义回并" or "transplant" in Stage 2 dialogue

`backport-transplant` runs the transplant-pipeline (Stage 4t/5t/6t).

### Edge: ambiguous boundary

If conditions land at the boundary (e.g., merge_base_age == T_AGE-5 with 2
refactor signals), present user with choice in Stage 2 Gate. Default
recommendation: transplant (safer — handles refactor properly even if
cherry would have worked).
```

- [ ] **Step 3: Verify decision tree consistency**

Search the file for any other place mentioning `backport` to ensure all references are updated:
```bash
grep -n "backport" /Users/dalwin/Documents/AI/skills/git-merge-conductor/references/mode-inference.md
```

- [ ] **Step 4: Commit**

```bash
cd /Users/dalwin/Documents/AI
git add skills/git-merge-conductor/references/mode-inference.md
git commit -m "$(cat <<'EOF'
refactor(git-merge-conductor): v2 mode-inference 拆 backport

backport-cherry (conflict-pipeline) vs backport-transplant (transplant-
pipeline) 判定：merge_base_age + refactor signal 双阈值。Care-class
那种场景按此规则会被识别为 backport-transplant。

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

## Task 20: Create `templates/grafting-plan.yaml`

**Files:**
- Create: `/Users/dalwin/Documents/AI/skills/git-merge-conductor/templates/grafting-plan.yaml`

- [ ] **Step 1: Write the schema**

```yaml
# grafting-plan.yaml — Stage 4t 产物，per-item × per-target-location 嫁接矩阵
#
# 渲染规则：
# - 每个 graft 必须 req_id 指回 requirements.yaml::items[i].id
# - target_location 可多个；confidence 三档（high / medium / low）+ evidence 必填
# - graft_strategy 四类（按安全度）：add-new < merge-into < guarded-overlay < replace
# - draft_status 生命周期：pending → drafted → applied | rejected

task: {{task_name}}
extracted_at: {{iso_timestamp}}

plan:
  - graft_id: G-{{nn}}
    req_id: REQ-{{nn}}                    # 指回 requirements.yaml
    source_evidence:
      - sha: {{commit_sha}}
        file: {{source_file_path}}
        symbol: {{class_or_method}}
        hunk: |
          {{git_show_W_block}}
    target_location:
      - file: {{target_file_path}}
        symbol: {{target_counterpart}}    # 可为空（add-new 时）
        confidence: high | medium | low
        evidence:                         # 映射依据（grep 结果、rename trail、判断要点）
          - {{evidence_line}}
    graft_strategy: replace | merge-into | add-new | guarded-overlay
    guard_condition: {{e.g., projectName == "JIASHAN"}}   # 仅 guarded-overlay 必填
    draft_status: pending                  # pending → drafted → applied | rejected
    rejection_reason: ""                   # draft_status == rejected 时填写
```

- [ ] **Step 2: Commit**

```bash
cd /Users/dalwin/Documents/AI
git add skills/git-merge-conductor/templates/grafting-plan.yaml
git commit -m "$(cat <<'EOF'
feat(git-merge-conductor): v2 grafting-plan.yaml schema template

Stage 4t 嫁接矩阵 schema：req_id 回指 / source_evidence /
target_location confidence / graft_strategy 四类。

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

## Task 21: Create `templates/draft.md`

**Files:**
- Create: `/Users/dalwin/Documents/AI/skills/git-merge-conductor/templates/draft.md`

- [ ] **Step 1: Write the per-graft draft context template**

```markdown
# Draft G-{{graft_id}} — REQ-{{req_id}}

> 草案，未应用到工作树。位置：`.git/merge-conductor/{{task}}/drafts/G-{{graft_id}}.diff`

## 上下文摘要

**需求**：{{req_title}}
**scope_tag**：{{scope_tag}}
**source**：{{source_ref}}@{{source_sha}}::{{source_symbol}}
**target**：{{target_file}}::{{target_symbol}}
**策略**：{{graft_strategy}}{{ if guarded-overlay: "（守卫: {{guard_condition}}）"}}

## 改动说明（中文）

{{model_writes_one_paragraph_中文_explaining_what_changes_and_why}}

## 置信度

- target_location mapping: {{high|medium|low}}
- target 端代码 fit: {{high|medium|low}}
- 综合: {{high|medium|low}}

## out_of_scope 初筛

- 本草案改动的文件：{{list_of_files}}
- 与 requirements.yaml::items[i].target_locations 比对：{{match|mismatch}}
- per-item out_of_scope 命中检查：{{none|hit_list}}
- global_out_of_scope 命中检查：{{none|hit_list}}

> 这是 draft-time 一次轻筛，Stage 6.5 是 authoritative audit。

## Proposed unified diff

参见 `.git/merge-conductor/{{task}}/drafts/G-{{graft_id}}.diff`。
```

- [ ] **Step 2: Commit**

```bash
cd /Users/dalwin/Documents/AI
git add skills/git-merge-conductor/templates/draft.md
git commit -m "$(cat <<'EOF'
feat(git-merge-conductor): v2 draft.md per-graft context template

每个 graft 的草案上下文 + 置信度 + out_of_scope 初筛 + diff 路径。

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

## Task 22: Update `references/semantic-mapping.md` 输出对齐 grafting-plan

**Files:**
- Modify: `/Users/dalwin/Documents/AI/skills/git-merge-conductor/references/semantic-mapping.md`

- [ ] **Step 1: Read existing semantic-mapping.md**

Run: `cat /Users/dalwin/Documents/AI/skills/git-merge-conductor/references/semantic-mapping.md`

- [ ] **Step 2: Update the output format section**

Replace the existing output format (which targets `state.json::decisions[i].semantic_mapping`) with the v2 format targeting `grafting-plan.yaml::plan[i].target_location`:

```markdown
## Output Format (v2)

After running the search procedures, emit a `target_location` array on the
graft entry in `grafting-plan.yaml`:

```yaml
target_location:
  - file: <target_file>
    symbol: <target_symbol>            # may be null for add-new
    confidence: high | medium | low
    evidence:
      - "git grep '<symbol>' returned <N> hits in <file>"
      - "git log --diff-filter=R found rename: <old> → <new>"
      - "<your judgment summary in 1 line>"
```

For `confidence`:
- **high**: exact symbol match OR clean rename trail
- **medium**: signature/semantic match but renamed/moved with non-trivial drift
- **low**: heuristic match with weak evidence; Stage 4t MUST set
  `graft_strategy != replace` for low-confidence locations

Per-task `target_location` arrays go into `grafting-plan.yaml::plan[i]` rather
than `state.json::decisions[i].semantic_mapping` (the v1 field is deprecated
for transplant-pipeline).
```

- [ ] **Step 3: Commit**

```bash
cd /Users/dalwin/Documents/AI
git add skills/git-merge-conductor/references/semantic-mapping.md
git commit -m "$(cat <<'EOF'
refactor(git-merge-conductor): v2 semantic-mapping output 对齐 grafting-plan

输出格式从 state.json::decisions[i].semantic_mapping 改为
grafting-plan.yaml::plan[i].target_location；confidence 三档与
graft_strategy 的安全度联动。

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

## Task 23: Create scenario F (care-class-to-develop) fixture + scenario doc

**Files:**
- Modify: `/Users/dalwin/Documents/AI/docs/superpowers/verification/git-merge-conductor/setup-fixture.sh`
- Create: `/Users/dalwin/Documents/AI/docs/superpowers/verification/git-merge-conductor/scenarios/F-backport-transplant.md`

- [ ] **Step 1: Read existing setup-fixture.sh**

Run: `cat /Users/dalwin/Documents/AI/docs/superpowers/verification/git-merge-conductor/setup-fixture.sh`
Note how A/B/C/D/E fixtures are built so we can follow the pattern.

- [ ] **Step 2: Append a care-class fixture section to setup-fixture.sh**

Append after the last existing fixture block:

```bash

# --- Scenario F: backport-transplant (care-class-to-develop) ---
# Simulates a target branch that has refactored since the source branch diverged.
# Source has 5 requirements; target has its own evolved logic on the same files.

mkdir -p /tmp/gmc-fixture-F
cd /tmp/gmc-fixture-F
git init -q
git checkout -b base

# Initial common base — minimal Java-like file structure
mkdir -p src/main/java/com/example/course
cat > src/main/java/com/example/course/CourseOffline.java <<'JAVA'
package com.example.course;

public class CourseOffline {
    public String getDisplayName() {
        return "default";
    }
}
JAVA

cat > pom.xml <<'XML'
<project>
  <modelVersion>4.0.0</modelVersion>
  <groupId>com.example</groupId>
  <artifactId>care-class</artifactId>
  <version>1.0</version>
  <packaging>jar</packaging>
  <build>
    <finalName>care-class</finalName>
    <plugins>
      <plugin>
        <groupId>org.apache.maven.plugins</groupId>
        <artifactId>maven-compiler-plugin</artifactId>
        <version>3.8.1</version>
        <configuration><source>1.8</source><target>1.8</target></configuration>
      </plugin>
    </plugins>
  </build>
</project>
XML
git add . && git commit -q -m "base: minimal CourseOffline + pom"

# Target branch (develop) — has evolved with project-aware logic but DIFFERENT shape than source
git checkout -b develop
cat > src/main/java/com/example/course/CourseOffline.java <<'JAVA'
package com.example.course;

import java.util.List;

public class CourseOffline {
    private List<Teacher> teacherList;

    public String getDisplayName() {
        if (teacherList != null && !teacherList.isEmpty()) {
            return teacherList.get(0).getName();
        }
        return "default";
    }

    public String getRegionalName(String project) {
        // Hangzhou & Nanjing iteration added in develop after merge-base
        if ("HANGZHOU".equals(project)) return "杭州-" + getDisplayName();
        if ("NANJING".equals(project)) return "南京-" + getDisplayName();
        return getDisplayName();
    }
}
JAVA
cat > src/main/java/com/example/course/Teacher.java <<'JAVA'
package com.example.course;
public class Teacher {
    private String name;
    public String getName() { return name; }
    public void setName(String n) { this.name = n; }
}
JAVA
git add . && git commit -q -m "develop: evolve to teacherList + regional name (HZ/NJ)"

# Source branch (refactor/micro-core-dev) — diverged with care-class plugin structure
git checkout base
git checkout -b refactor/micro-core-dev
mkdir -p plugins/care-class/src/main/java/com/example/care
cat > plugins/care-class/src/main/java/com/example/care/CareClassUtil.java <<'JAVA'
package com.example.care;
// Source's care-class-specific implementation, plugin-isolated
public class CareClassUtil {
    public static String normalizeCareClassTeacherName(String project, String raw) {
        // Source's logic uses projectName guard — this is what care-class round-3 had to FIX
        if ("JIASHAN".equals(project)) {
            return raw.replace("老师", "");
        }
        return raw;
    }
}
JAVA
# Source also has CourseOffline override
cat > src/main/java/com/example/course/CourseOffline.java <<'JAVA'
package com.example.course;
// Source's diverged CourseOffline — does NOT have teacherList; uses raw string
public class CourseOffline {
    private String careClassTeacher;

    public String getDisplayName() {
        if (careClassTeacher != null) {
            // direct call into plugin
            return com.example.care.CareClassUtil.normalizeCareClassTeacherName("JIASHAN", careClassTeacher);
        }
        return "default";
    }
}
JAVA
git add . && git commit -q -m "refactor/micro-core-dev: plugin-style CareClassUtil + CourseOffline override"

echo "Scenario F fixture ready at /tmp/gmc-fixture-F. Source: refactor/micro-core-dev. Target: develop."
```

Make it executable:
```bash
chmod +x /Users/dalwin/Documents/AI/docs/superpowers/verification/git-merge-conductor/setup-fixture.sh
```

- [ ] **Step 3: Write scenario F doc**

Create `/Users/dalwin/Documents/AI/docs/superpowers/verification/git-merge-conductor/scenarios/F-backport-transplant.md`:

```markdown
# Scenario F — backport-transplant (care-class-to-develop)

## Goal

Verify the end-to-end transplant-pipeline:
- Stage 2 identifies `backport-transplant` (not `backport-cherry`)
- requirements.yaml extracted with `scope_tag` per item
- Stage 4t builds grafting plan; Stage 5t drafts; Stage 6t auto-applies
- Stage 6.5 NC-01 INTERCEPTS the `projectName == "JIASHAN"` guard on
  `normalizeCareClassTeacherName` because scope_tag = "通用课堂功能"
- Stage 7.5 Phase 2 surfaces the intercepted item; user provides feedback
- Loop back to Stage 4t; second iter resolves; user says "完成"
- Finalize

## Setup

```bash
cd /tmp && rm -rf gmc-fixture-F
bash /Users/dalwin/Documents/AI/docs/superpowers/verification/git-merge-conductor/setup-fixture.sh
cd /tmp/gmc-fixture-F
```

## Run

Start Claude Code in `/tmp/gmc-fixture-F`. Invoke:

> 「把 refactor/micro-core-dev 上的 care-class 功能合并到 develop，
> 主要是把 normalizeCareClassTeacherName 这个方法的展示逻辑回并进来。
> 注意 develop 已经有了 teacherList 的实现，不要回退。」

## Expected pipeline behavior

### Stage 0-2

- Stage 0 emits banner, no guards trip
- Stage 1 normalizes: source=refactor/micro-core-dev, target=develop
- Stage 2 mode inference: should detect `backport-transplant` (refactor signals in
  CourseOffline + plugin structure delta)
- Stage 2 Gate: model proposes requirements.yaml with at least 1 item like:
  ```yaml
  - id: REQ-01
    title: 课堂教师展示名回并
    scope_tag: 通用课堂功能
    target_locations:
      - file: src/main/java/com/example/course/CourseOffline.java
        symbol: getDisplayName
    out_of_scope:
      - 不引入 projectName == "JIASHAN" 守卫（develop 主线通用）
      - 不删除 teacherList 实现
  ```
  User confirms "策略 OK".

### Stage 3

- Worktree created via `superpowers:using-git-worktrees` (backport-transplant
  triggers worktree).
- Banner: `[Stage 3 · Working Setup · iter 1 · tag: merge/care-class-transplant/before-step-3]`

### Stage 4t / 5t / 6t

- 4t builds grafting plan with 1 graft, `graft_strategy: merge-into`
  (CareClassUtil source → CourseOffline.getDisplayName target)
- 5t produces a draft; the draft may include the `projectName == "JIASHAN"`
  guard (out_of_scope soft-filter SHOULD catch this; if not, Stage 6.5 will)
- 6t applies → Stage 6.5 invokes → NC-01 hits → rollback
- 6t loop ends with REQ-01 status = partial

### Stage 7

- Commit produced even though REQ-01 partial (Stage 7 commits whatever is staged)
- Tag merge/care-class-transplant/done; status = pre-verified

### Stage 7.5 Phase 1

- compile passes (no syntax error from rollback)
- lint passes
- scope-test: passes

### Stage 7.5 Phase 2

- Report shows REQ-01: ⚠ partial, evidence: rollback (NC-01)
- User says: 「REQ-01 没做对——去掉项目守卫，只用 teacherList 路径」
- iter += 1, loop back to Stage 4t

### Iter 2

- 4t re-drafts with strategy = merge-into, no projectName guard
- 6t applies; Stage 6.5 passes
- Stage 7 commits iter 2
- Phase 1 passes
- Phase 2 user says "完成"

### Stage 8

- Wrap-up shows iterations[].length == 2
- state.json::status = finalized
- worktree cleanup option presented

## Inspection commands

```bash
# After scenario completes:
cat .git/merge-conductor/care-class-transplant/state.json | jq '.status, .iterations | length, .audit | length'
# Expected: "finalized", 2, ≥1

cat .git/merge-conductor/care-class-transplant/audit/*.md
# Should show the NC-01 intercept from iter 1

cat .git/merge-conductor/care-class-transplant/grafting-plan.yaml | head -30
# Should show G-01 with merge-into strategy
```

## Pass criteria

- [ ] Mode = backport-transplant (not backport-cherry)
- [ ] Worktree created at Stage 3
- [ ] NC-01 fires on iter 1 (projectName guard intercepted)
- [ ] User feedback parsed correctly in Phase 2; iter 2 triggered
- [ ] Final status = finalized after iter 2
- [ ] stage_history complete (11 entries × 2 iters = audit array shows 2 attempts on REQ-01)
```

- [ ] **Step 4: Commit fixture + scenario**

```bash
cd /Users/dalwin/Documents/AI
git add docs/superpowers/verification/git-merge-conductor/setup-fixture.sh
git add docs/superpowers/verification/git-merge-conductor/scenarios/F-backport-transplant.md
git commit -m "$(cat <<'EOF'
test(git-merge-conductor): v2 scenario F (backport-transplant care-class)

Fixture 模拟 care-class-to-develop 关键情形：source 用 projectName
守卫 + target 已迭代到 teacherList。期望流程：NC-01 在 iter 1 拦截，
user feedback 触发 iter 2 后 finalize。

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

## Task 24: Phase 4 smoke gate — scenario F dry-run (without negative-constraints.md yet)

**Files:**
- Modify: `/Users/dalwin/Documents/AI/docs/superpowers/verification/git-merge-conductor/SMOKE-TEST.md`

Note: At this point Phase 5 (negative-constraints.md) is NOT done yet. We dry-run F to validate the transplant-pipeline mechanics; NC-01 interception will fail (expected — that's why Phase 5 follows).

- [ ] **Step 1: Run scenario F**

```bash
cd /tmp && rm -rf gmc-fixture-F
bash /Users/dalwin/Documents/AI/docs/superpowers/verification/git-merge-conductor/setup-fixture.sh
cd /tmp/gmc-fixture-F
```

Then run in Claude Code per scenario F doc.

- [ ] **Step 2: Verify Phase 4 partial pass**

Expected at this point:
- Mode = backport-transplant (Task 19's split fires correctly)
- requirements.yaml produced (Phase 3 works)
- grafting-plan.yaml produced (Task 20)
- Drafts produced (Task 21)
- Stage 6t applies grafts (autonomous)
- Stage 6.5 NOT yet hooked to NC-01 (Phase 5 will add) — so NO interception
- Phase 1 may PASS spuriously (no audit fail to rollback)
- Phase 2 may auto-pass with finalized = true

This is expected partial behavior. The real F gate happens after Phase 5.

- [ ] **Step 3: Append Phase 4 partial gate notes**

```markdown
## v2 Phase 4 gate (2026-05-13, partial — full F gate after Phase 5)
- [ ] Mode = backport-transplant correctly selected
- [ ] requirements.yaml + grafting-plan.yaml + drafts produced
- [ ] Worktree created (Stage 3 delegates to superpowers:using-git-worktrees)
- [ ] Stage 6t autonomous apply executes
- [ ] (Pending Phase 5): NC-01 interception
- [ ] No regression on A/C/E
```

- [ ] **Step 4: Commit**

```bash
cd /Users/dalwin/Documents/AI
git add docs/superpowers/verification/git-merge-conductor/SMOKE-TEST.md
git commit -m "$(cat <<'EOF'
test(git-merge-conductor): v2 Phase 4 partial smoke gate

transplant-pipeline 机制走通；NC-01 interception 待 Phase 5。

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

# Phase 5 — Stage 6.5 + 反向约束

**Goal of phase:** `references/negative-constraints.md` 落地 NC-01~05 + 领域示例附录；`templates/audit-report.md` 落地；Stage 6.5 在 6t/6c 中即时调用；scenario F 完整通过（NC-01 拦截 → iter 2 finalize）。

## Task 25: Create `references/negative-constraints.md`

**Files:**
- Create: `/Users/dalwin/Documents/AI/skills/git-merge-conductor/references/negative-constraints.md`

- [ ] **Step 1: Write NC-01 ~ NC-05 (verbatim from spec §8.4)**

```markdown
# Negative Constraints

每条规则结构：[ID] 名称 / 失败原因 / 检测信号 / 后置动作。

Stage 6.5 self-audit iterates these rules against every applied unit
(graft in 6t, hunk in 6c) and emits an `audit-report.md` entry per unit.
A fail triggers rollback per Stage 6.5 contract.

---

## NC-01 项目守卫不要套通用代码

- **失败原因**：通用方法被 `projectName == X` / `tenantId == X` / 类似 enum 比较守卫包裹，其他地区/项目复用同模块时被拦截。Care-class round 3 教训：`normalizeCareClassTeacherName` 套 `projectName==JIASHAN` 拦截了其他地区。
- **检测信号**：
  1. 当前 graft 引入的代码中 grep 命中 `projectName ==` / `tenantId ==` / 类似 enum 比较模式
  2. 对应 `requirements.yaml::items[i].scope_tag` 不含项目专属语义（自由文本但常见词如"嘉善专属"、"项目X限定"等）
- **后置动作**：把守卫降级到业务维度（如 courseType / channel / userRole），或完全移除。如果用户在 Stage 2 明确说该方法是项目专属，scope_tag 应包含项目语义，本 NC 不应该触发。

---

## NC-02 不回退目标已演进的逻辑

- **失败原因**：源分支是早期分叉，target 已有迭代；机械 `replace` 覆盖 target 进展。Care-class 教训：target 的 HZ/NJ regional logic 不可被 source 的 plugin-style 覆盖。
- **检测信号**：
  1. `grafting-plan.yaml::plan[i].target_location.evidence` 显示 target 端有比 merge-base 更新的同名方法 commit
  2. `graft_strategy == replace`
- **后置动作**：strategy 改为 `merge-into` 或 `guarded-overlay`，保留 target 已加入的代码路径。

---

## NC-03 源专属目录结构不带入目标

- **失败原因**：源分支的插件化 / 重构 / 独立 starter 形态污染 target 主线架构。Care-class 教训：refactor/micro-core-dev 的 plugins/ 目录不应整体迁入 develop。
- **检测信号**：
  1. graft 改动包含 target 中不存在的顶级目录（如 `plugins/`、新 `pom.xml` 模块、独立 starter）
  2. 或 graft 修改了顶层构建文件添加新模块
- **后置动作**：转写为 target 已有模块内的等效改动。如果必须新增模块，必须先回 Stage 2 升级 `requirements.yaml` 加 item 并请用户确认。

---

## NC-04 注释里的项目语义限定要解耦

- **失败原因**：源注释带项目限定，迁到 target 后语义错位。Care-class 教训：源注释「嘉善养育照护」搬到 target 后变成限定，但实际代码已经通用化。
- **检测信号**：
  1. 源 hunk 注释 / Javadoc / docstring 含 task 的 scope_tag 中出现的项目专属词
  2. target 同位置注释 / Javadoc 不含该词
- **后置动作**：移除项目限定词，保留业务语义。例如 `// 嘉善养育照护课堂教师` → `// 课堂教师展示名`。

---

## NC-05 不引入 requirements.yaml 外的变更

- **失败原因**：模型"顺手清理"把范围外改动混进合并，导致 PR 散乱 + scope creep。
- **检测信号**：
  1. graft.files_touched 中存在不属于任一 `requirements.yaml::items[*].target_locations` 的文件
- **后置动作**：rollback；若用户在 Phase 2 确认要纳入，必须先回 Stage 2 升级 `requirements.yaml` 加 item（重审 Gate）。
- **特别说明**：此规则在 `SKILL.md` Safety Invariants 第 6 条对应一行硬约束（hard rollback，不可由 NC 配置 disable）。本文件保留检测细节供模型在 self-audit 时引用。

---

## 附录 — 领域示例（参考，非硬规则）

以下示例从 care-class-to-develop 真实实践提炼，作为模型在判断时的参考案例。
不是 NC 编号规则，但在做 self-audit 时可以作为同类问题的识别锚。

### 例 1: PageHelper 分页前不要插入额外查询

- **背景**：Java/MyBatis 项目使用 PageHelper 时，`PageHelper.startPage()` 必须紧跟分页查询调用。
- **错误模式**：在 startPage 之前/之间插入其他查询调用 → 分页 limit 被前一个查询消费，分页失效。
- **care-class round 2 教训**：续接归并时差点把指导单位 filter 写成额外查询，幸而改为 SQL `exists` 内联。
- **应对**：如果 graft 引入了与分页查询同方法的额外 query 调用，self-audit 应该 flag 这条作为人工确认项（不强制 rollback，但报告中标注 ⚠）。

### 例 2: ORM 实体新增字段时的全链路核对

- **背景**：新增表/字段后，domain/example/mapper/service/controller/view 一条链路都要更新。
- **错误模式**：只改 domain，漏掉 mapper.xml 或 example builder。
- **应对**：如果 graft 改动了某 ORM 实体的字段定义，self-audit 应该建议核对同名 mapper.xml + Example.java；缺一则 status 标 partial。

(后续可在此附录持续累积领域示例，但 NC-01~NC-05 是结构性约束，不需要扩展枚举。)
```

- [ ] **Step 2: Commit**

```bash
cd /Users/dalwin/Documents/AI
git add skills/git-merge-conductor/references/negative-constraints.md
git commit -m "$(cat <<'EOF'
feat(git-merge-conductor): v2 negative-constraints.md (NC-01~05 + 领域附录)

5 条通用 NC 规则 (项目守卫/不回退/源结构/注释解耦/范围外变更) 从
care-class 实践提炼；领域示例附录 (PageHelper 分页/ORM 全链路) 作
为参考案例。NC-05 与 Safety Invariant 6 联动。

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

## Task 26: Create `templates/audit-report.md`

**Files:**
- Create: `/Users/dalwin/Documents/AI/skills/git-merge-conductor/templates/audit-report.md`

- [ ] **Step 1: Write the template**

```markdown
# Self-audit {{unit_id}}

**unit**: {{unit_id}} ({{unit_kind}}) → {{req_id_or_hunk_loc}} {{symbol_or_path}}

**结论**: {{pass_or_fail}}{{ if fail: "（{{violation_summary}}）"}}

**检测项**:
- Per-item out_of_scope: {{result}}{{ if hit: "命中「{{matched_constraint}}」"}}
- Global out_of_scope: {{result}}{{ if hit: "命中「{{matched_constraint}}」"}}
- NC-01 项目守卫套通用代码: {{result}}{{ if hit: "命中: {{evidence}}"}}
- NC-02 回退已演进逻辑: {{result}}{{ if hit: "命中: {{evidence}}"}}
- NC-03 源专属目录结构: {{result}}{{ if hit: "命中: {{evidence}}"}}
- NC-04 注释项目限定: {{result}}{{ if hit: "命中: {{evidence}}"}}
- NC-05 范围外变更: {{result}}{{ if hit: "命中: {{evidence}}"}}

**后续动作**: {{action}}
{{ if rolled-back: "rollback {{unit_id}}；req {{req_id}} 标 {{new_status}}；写入 Phase 2 报表 ⚠ 项" }}
{{ if applied: "保留改动；req {{req_id}} 维持 {{status}}" }}

**audited_at**: {{iso_timestamp}}
```

- [ ] **Step 2: Commit**

```bash
cd /Users/dalwin/Documents/AI
git add skills/git-merge-conductor/templates/audit-report.md
git commit -m "$(cat <<'EOF'
feat(git-merge-conductor): v2 audit-report.md template

Stage 6.5 self-audit 输出模板。检测三层 + 5 个 NC + 后续动作。

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

## Task 27: Update `references/contracts/audit-and-verify.md#stage-65` 补充 NC 调用细节

**Files:**
- Modify: `/Users/dalwin/Documents/AI/skills/git-merge-conductor/references/contracts/audit-and-verify.md`

- [ ] **Step 1: Add NC iteration sub-protocol to Stage 6.5 anchor**

Append within the Stage 6.5 section, before its `**Outputs**` field:

```markdown

### NC Iteration Sub-protocol

For each unit invocation of Stage 6.5:

1. Load `requirements.yaml::items[unit.req_id].out_of_scope` (per-item constraints).
2. Load `requirements.yaml::global_out_of_scope`.
3. Read `references/negative-constraints.md` (load NC-01~NC-05 + appendix).
4. For each NC rule:
   - Evaluate `检测信号` against the just-applied unit
   - If hit, record violation with rule ID + evidence
5. Independent check: NC-05 hard-fail — if `unit.files_touched` contains any
   file not in any `requirements.yaml::items[*].target_locations`, immediately
   rollback regardless of other checks. This is Safety Invariant 6.
6. Render `audit-report.md` from `templates/audit-report.md` to
   `.git/merge-conductor/<task>/audit/<unit_id>.md`.
7. If any violation: rollback per the Hard constraints section above.

The model SHOULD use the appendix领域示例 as inspiration when deciding whether
to flag ⚠ warnings (not full violations) for human review. Appendix items do
not auto-rollback.
```

- [ ] **Step 2: Commit**

```bash
cd /Users/dalwin/Documents/AI
git add skills/git-merge-conductor/references/contracts/audit-and-verify.md
git commit -m "$(cat <<'EOF'
refactor(git-merge-conductor): v2 stage-65 NC iteration sub-protocol

Stage 6.5 显式 7 步检查流程：load constraints → 评估每条 NC →
NC-05 hard-fail → 渲染 audit-report → 必要时 rollback。

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

## Task 28: Phase 5 smoke gate — scenario F full pass

**Files:**
- Modify: `/Users/dalwin/Documents/AI/docs/superpowers/verification/git-merge-conductor/SMOKE-TEST.md`

- [ ] **Step 1: Re-run scenario F**

```bash
cd /tmp && rm -rf gmc-fixture-F
bash /Users/dalwin/Documents/AI/docs/superpowers/verification/git-merge-conductor/setup-fixture.sh
cd /tmp/gmc-fixture-F
```

Then run scenario F in Claude Code per the scenario doc.

- [ ] **Step 2: Verify NC-01 interception**

Expected during iter 1:
- Stage 6t applies graft G-01 (which DOES include `projectName == "JIASHAN"`)
- Stage 6.5 invokes; loads negative-constraints.md
- NC-01 fires (graft has `projectName ==` + scope_tag = "通用课堂功能")
- audit-report.md written with `pass_or_fail: fail`
- graft rolled back; REQ-01 status = partial

```bash
cat /tmp/gmc-fixture-F/.git/merge-conductor/care-class-transplant/audit/G-01.md
# Expected: 结论 fail; NC-01 命中
```

- [ ] **Step 3: Verify Phase 2 surfaces the intercept and accepts user feedback**

The Phase 2 report should show:
- REQ-01: ⚠ partial
- Audit intercepts: G-01 / NC-01

User responds: 「REQ-01 没做对——去掉项目守卫，只用 teacherList 路径」.

Expected: iter increments to 2, loop back to Stage 4t.

- [ ] **Step 4: Verify iter 2 finalizes**

After iter 2, expected:
- New draft without projectName guard
- Stage 6.5 passes
- Stage 7.5 Phase 1 + Phase 2 pass
- `state.json::status: finalized`, `iterations | length == 2`

- [ ] **Step 5: Append Phase 5 gate to SMOKE-TEST.md**

```markdown
## v2 Phase 5 gate (2026-05-13)
- [ ] Scenario F iter 1: NC-01 fires, G-01 rolled back, REQ-01 partial
- [ ] Phase 2 surfaces NC-01 intercept correctly
- [ ] User feedback parsed; iter 2 triggered
- [ ] Iter 2 succeeds; status: finalized
- [ ] state.json::iterations.length == 2
- [ ] audit-report.md per unit written
- [ ] No regression on A/C/E
```

- [ ] **Step 6: Commit**

```bash
cd /Users/dalwin/Documents/AI
git add docs/superpowers/verification/git-merge-conductor/SMOKE-TEST.md
git commit -m "$(cat <<'EOF'
test(git-merge-conductor): v2 Phase 5 smoke gate (scenario F full pass)

Stage 6.5 + NC-01 完整链路验证；scenario F 2-iter finalize 通过。

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

# Phase 6 — Stage 7.5 校验循环

**Goal of phase:** `templates/verification-report.md` 落地；项目类型自动检测落地；Phase 1 修复 loop N=3 实现；Phase 2 用户反馈解析；scenario H/I 通过。

## Task 29: Create `templates/verification-report.md`

**Files:**
- Create: `/Users/dalwin/Documents/AI/skills/git-merge-conductor/templates/verification-report.md`

- [ ] **Step 1: Write the template**

```markdown
# 合并验证报告 — {{task}}

## 自动化校验（Phase 1）

- **compile**: {{compile_status}} {{ if iter > 1: "(iter {{compile_pass_iter}})"}}
- **lint**: {{lint_status}}
- **test**: {{test_status}}{{ if scope: " (scope: {{tested_modules}})"}}{{ if off: " (skipped per config)"}}

{{ if any_phase1_fail: "
### Phase 1 自修复轮次

| iter | trigger | fix_unit | result |
|---|---|---|---|
{{phase1_iter_table}}
" }}

## 需求清单兑现

| REQ | 标题 | scope_tag | status | evidence | 备注 |
|---|---|---|---|---|---|
{{requirements_status_table}}

## Self-Audit 拦截项（共 {{intercept_count}} 处）

{{ if intercept_count == 0: "无" }}
{{ if intercept_count > 0: "
{{intercept_list_per_unit}}
" }}

## 范围外尝试（NC-05 拦截，共 {{nc05_count}} 处）

{{ if nc05_count == 0: "无" }}
{{ if nc05_count > 0: "
{{nc05_list}}
" }}

## 未决项（Conflict-pipeline unresolved + Transplant low-confidence ⚠）

{{ if no_pending: "无" }}
{{ if pending_count > 0: "
{{pending_list}}
" }}

---

## 你的决定

请在终端回复其一：

- **`完成`** — 进入 Stage 8 收尾
- **`REQ-X 没做对`** + 说明 — 回 Stage 4-6 针对 REQ-X 重做
- **`REQ-X 不该做`** — 升级 `requirements.yaml` 移除 + rollback 相关改动
- **`还多 Z`**（路径或描述）— 找到引入项 → rollback
- 任意自由文本 — 我会解析意图并回显「我理解为: ...」让你二次确认
```

- [ ] **Step 2: Commit**

```bash
cd /Users/dalwin/Documents/AI
git add skills/git-merge-conductor/templates/verification-report.md
git commit -m "$(cat <<'EOF'
feat(git-merge-conductor): v2 verification-report.md template

Stage 7.5 Phase 2 兜底报表 (终端 + HTML 共用)。自动化校验 +
需求兑现 + audit 拦截 + 未决项 + 4 种用户决定形态。

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

## Task 30: Update `references/html-report-template.md` 加 Phase 2 section

**Files:**
- Modify: `/Users/dalwin/Documents/AI/skills/git-merge-conductor/references/html-report-template.md`

- [ ] **Step 1: Read existing html-report-template.md**

Run: `cat /Users/dalwin/Documents/AI/skills/git-merge-conductor/references/html-report-template.md`

- [ ] **Step 2: Append a `<section id="verification">` skeleton**

```markdown

## Verification Section (Stage 7.5 Phase 2)

Append this section to the HTML report when Phase 2 runs:

```html
<section id="verification">
  <h2>验证报告 — iter {{iter}}</h2>
  
  <h3>自动化校验</h3>
  <ul class="check-list">
    <li class="{{compile_class}}"><span class="label">compile</span>: {{compile_status}}</li>
    <li class="{{lint_class}}"><span class="label">lint</span>: {{lint_status}}</li>
    <li class="{{test_class}}"><span class="label">test</span>: {{test_status}}</li>
  </ul>

  <h3>需求清单兑现</h3>
  <table class="reqs">
    <thead><tr><th>REQ</th><th>标题</th><th>scope_tag</th><th>status</th><th>evidence</th><th>备注</th></tr></thead>
    <tbody>
      {{requirements_table_rows}}
    </tbody>
  </table>

  <h3>Self-Audit 拦截项</h3>
  {{audit_intercept_blocks_or_empty}}

  <h3>范围外尝试 (NC-05)</h3>
  {{nc05_blocks_or_empty}}

  <h3>未决项</h3>
  {{pending_blocks_or_empty}}

  <h3>用户决定</h3>
  <p class="user-decision">{{user_response}}{{ if echo: " — 我理解为: {{model_interpretation}}"}}</p>
</section>
```

Add minimal CSS to the existing `<style>` block:
```css
.check-list .pass { color: #1a7f37; }
.check-list .fail { color: #d1242f; }
.check-list .skip { color: #8b949e; }
.reqs tr.completed { background: #dafbe1; }
.reqs tr.partial { background: #fff8c5; }
.reqs tr.pending { background: #ffebe9; }
.reqs tr.abandoned { background: #d0d7de; }
```
```

- [ ] **Step 3: Commit**

```bash
cd /Users/dalwin/Documents/AI
git add skills/git-merge-conductor/references/html-report-template.md
git commit -m "$(cat <<'EOF'
refactor(git-merge-conductor): v2 html-report 加 Phase 2 section

verification section HTML 骨架 + 状态颜色样式。

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

## Task 31: Create scenario H — Phase 1 self-fix loop limit

**Files:**
- Create: `/Users/dalwin/Documents/AI/docs/superpowers/verification/git-merge-conductor/scenarios/H-phase1-loop-limit.md`

- [ ] **Step 1: Write scenario H doc**

```markdown
# Scenario H — Phase 1 self-fix loop limit (N=3)

## Goal

Verify Phase 1's bounded self-fix behavior:
- Inject a deliberate compile error via a graft
- Stage 7.5 Phase 1 detects compile fail
- Model attempts fix iter 1 → still fails
- Iter 2 → still fails
- Iter 3 → still fails
- After iter 3, model surrenders and passes error to Phase 2 verbatim
- `state.json::iterations[]` shows 3 entries with `trigger: phase1-fix`
- User decides in Phase 2

## Setup

Reuse the F fixture but inject a compile-breaking source.

```bash
cd /tmp && rm -rf gmc-fixture-H
cp -r /tmp/gmc-fixture-F /tmp/gmc-fixture-H
cd /tmp/gmc-fixture-H
git checkout refactor/micro-core-dev

# Inject syntax error in CareClassUtil
cat > plugins/care-class/src/main/java/com/example/care/CareClassUtil.java <<'JAVA'
package com.example.care;
public class CareClassUtil {
    public static String normalizeCareClassTeacherName(String project, String raw)
        // intentionally missing return type + braces — compile will fail
        if ("JIASHAN".equals(project)) {
            return raw.replace("老师", "");
        }
        return raw;
    }
}
JAVA
git add . && git commit -q -m "intentional: introduce syntax error in CareClassUtil"
```

## Run

Start Claude Code in `/tmp/gmc-fixture-H` and invoke same as scenario F.

## Expected pipeline behavior

Stages 0-7 proceed similarly to F. The graft applies (Stage 6t), Stage 6.5
passes (NC checks don't catch syntax errors). Stage 7 commits.

### Stage 7.5 Phase 1

- iter 1: `mvn compile` → BUILD FAILURE; model attempts fix:
  - rollback graft G-01
  - regenerate draft (may produce same or different syntax)
  - reapply
  - re-run compile → still FAIL
- iter 2: similar attempt → still FAIL
- iter 3: similar attempt → still FAIL
- After iter 3, model surrenders; phase1.result = "fail-with-errors";
  errors[] populated with compile output verbatim

### Stage 7.5 Phase 2

- Report includes "Phase 1 自修复轮次" table with 3 iter rows, all failed
- Report shows the compile error text in a fenced block

User responds (e.g.): "REQ-01 没做对——syntax error 是源端的，先回滚 REQ-01 让我手工修源端"

iter += 1 (now iter 4 overall), but `trigger: user-feedback` (not phase1-fix).
The loop budget for phase1-fix iters resets in the next Phase 2 round.

## Inspection commands

```bash
cat .git/merge-conductor/<task>/state.json | jq '.iterations | map({iter, trigger, ended_at})'
# Expected: at least 3 entries with trigger == "phase1-fix" in iter 1's life,
# plus initial entry. Total length ≥ 4 after user feedback.
```

## Pass criteria

- [ ] Phase 1 iter cap N=3 enforced (no iter 4 of phase1-fix)
- [ ] All 3 iter attempts logged in iterations[] with trigger: phase1-fix
- [ ] Phase 2 report shows the compile error
- [ ] User feedback in Phase 2 triggers a new outer iter (not phase1-fix)
```

- [ ] **Step 2: Commit**

```bash
cd /Users/dalwin/Documents/AI
git add docs/superpowers/verification/git-merge-conductor/scenarios/H-phase1-loop-limit.md
git commit -m "$(cat <<'EOF'
test(git-merge-conductor): v2 scenario H (Phase 1 fix loop limit)

注入 compile syntax error，验证 Phase 1 自修复 N=3 后投降把
错误带给 Phase 2 用户。

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

## Task 32: Create scenario I — Phase 2 multi-iter loop

**Files:**
- Create: `/Users/dalwin/Documents/AI/docs/superpowers/verification/git-merge-conductor/scenarios/I-phase2-multi-iter.md`

- [ ] **Step 1: Write scenario I doc**

```markdown
# Scenario I — Phase 2 multi-iter user feedback loop

## Goal

Verify Phase 2's loop-back semantics across multiple iters:
- iter 1: 自动化 pass, but user says "REQ-X 没做对"
- iter 2: re-do REQ-X, automation pass, but user says "还多 Y"
- iter 3: rollback Y, automation pass, user says "完成"
- state.json::iterations[] has 3 entries with proper triggers
- stage_history shows the iter-decorated re-entries to Stage 4-6

## Setup

Reuse scenario F fixture (the NC-01 path), but pretend the FIRST user feedback
doesn't fully address the issue. We script the user's responses:

```bash
cd /tmp && rm -rf gmc-fixture-I
bash /Users/dalwin/Documents/AI/docs/superpowers/verification/git-merge-conductor/setup-fixture.sh
mv /tmp/gmc-fixture-F /tmp/gmc-fixture-I
cd /tmp/gmc-fixture-I
```

## Run + user response script

Start Claude Code in `/tmp/gmc-fixture-I` and invoke scenario F.

### iter 1
- Stage 6.5 fires NC-01 (same as F).
- Phase 1 may pass (rollback left clean compile).
- Phase 2 report shown.
- User responds: `REQ-01 没做对——重做但是用 setter 注入项目名` (悄悄重新引入 projectName via setter — model should still flag this in iter 2)

### iter 2
- Stage 4t re-drafts using setter pattern (still introduces project-aware behavior)
- Stage 6.5 fires NC-01 again (setter chained with projectName check)
- Phase 1 passes
- Phase 2 report shown
- User responds: `还多 setProject 这个方法` (asks to remove the new setter)

### iter 3
- Model rollbacks the setter addition
- Re-drafts using only teacherList path
- Stage 6.5 passes
- Phase 1 passes
- Phase 2 report shown
- User responds: `完成`

### Wrap up
- state.json::iterations[] length == 3
- iterations[].triggers: [initial, user-feedback ("REQ-01 没做对"), user-feedback ("还多 setProject")]
- audit array shows NC-01 hits in iter 1 + iter 2

## Inspection commands

```bash
cat .git/merge-conductor/<task>/state.json | jq '.iterations | length, .iterations | map(.trigger)'
# Expected: 3, ["initial", "user-feedback", "user-feedback"]

cat .git/merge-conductor/<task>/state.json | jq '.audit | length'
# Expected: ≥ 3 (1 per iter × at least 1 unit)

cat .git/merge-conductor/<task>/state.json | jq '.status'
# Expected: "finalized"
```

## Pass criteria

- [ ] Phase 2 correctly parses 3 different user response types
- [ ] iterations[] grows to 3 with correct triggers
- [ ] Each iter writes its own stage_history entries with kind suffix
- [ ] Final status: finalized
- [ ] Worktree preserved through all iters (single creation in Stage 3, never re-created)
```

- [ ] **Step 2: Commit**

```bash
cd /Users/dalwin/Documents/AI
git add docs/superpowers/verification/git-merge-conductor/scenarios/I-phase2-multi-iter.md
git commit -m "$(cat <<'EOF'
test(git-merge-conductor): v2 scenario I (Phase 2 multi-iter loop)

验证 3 轮 Phase 2 反馈完整链路：NC-01 拦截 → 第二轮再次拦截 →
第三轮 finalize。iterations[] 完整记录。

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

## Task 33: Phase 6 smoke gate — scenarios H + I

**Files:**
- Modify: `/Users/dalwin/Documents/AI/docs/superpowers/verification/git-merge-conductor/SMOKE-TEST.md`

- [ ] **Step 1: Run scenario H**

Follow scenario H doc. Verify pass criteria.

- [ ] **Step 2: Run scenario I**

Follow scenario I doc. Verify pass criteria.

- [ ] **Step 3: Append Phase 6 gate**

```markdown
## v2 Phase 6 gate (2026-05-13)
- [ ] Scenario H: Phase 1 self-fix N=3 cap enforced; errors passed to Phase 2 verbatim
- [ ] Scenario I: 3-iter Phase 2 loop completes; iterations[] has 3 entries
- [ ] verification-report.md renders correctly (终端 + HTML)
- [ ] No regression on F (re-run F: still finalizes in 2 iters)
- [ ] No regression on A/C/E
```

- [ ] **Step 4: Commit**

```bash
cd /Users/dalwin/Documents/AI
git add docs/superpowers/verification/git-merge-conductor/SMOKE-TEST.md
git commit -m "$(cat <<'EOF'
test(git-merge-conductor): v2 Phase 6 smoke gate (H + I)

Phase 1 N=3 自修复上限 + Phase 2 多轮 loop 完整验证。

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

# Phase 7 — conflict-pipeline autonomous

**Goal of phase:** `references/conflict-classification.md` 加 C/D 自动决策启发式；`pipeline-conflict.md` 已有契约;`unresolved.md` 格式;不再留 conflict marker；scenario B 升级支持 backport-cherry / backport-transplant 双子场景.

## Task 34: Add C/D autonomous heuristics to `references/conflict-classification.md`

**Files:**
- Modify: `/Users/dalwin/Documents/AI/skills/git-merge-conductor/references/conflict-classification.md`

- [ ] **Step 1: Read existing conflict-classification.md**

Run: `cat /Users/dalwin/Documents/AI/skills/git-merge-conductor/references/conflict-classification.md`

- [ ] **Step 2: Append a new section "C/D Autonomous Heuristics"**

Append at the end (after existing A/B/C/D class definitions):

```markdown

## C/D Class Autonomous Heuristics (v2 — Stage 6c)

v1 surfaced every C/D class hunk to the user via the 5-option decision-point
template. v2 changes this: Stage 6c runs an autonomous heuristic ladder per
hunk, surfacing only the unresolved residue to Phase 2.

### Heuristic Ladder (apply in order; first match wins)

1. **locked_file_rules or global_out_of_scope match**
   - If `state.json::config.locked_file_rules.take_target` includes this file → take target.
   - If `take_source` includes this file → take source.
   - If a `global_out_of_scope` constraint matches the hunk's introduced code → take target.

2. **Both sides additive (no overlapping logic)**
   - If both source and target hunks are purely additive (no overlapping line ranges, no共同 modified lines), and neither side deletes the other's lines → take both (concatenate source-first then target).

3. **One side is whitespace-only / comment-only**
   - If one side's hunk modifications are entirely whitespace, blank lines, or comments → take the OTHER side.

4. **Source-side older**
   - Run `git log --follow -1 --format=%cI <target_file>` (target side's most recent commit time on this file).
   - If source merge-base of this hunk is older than target's most recent change → take target (target has had more time to evolve).

5. **Fallback: mark `unresolved`**
   - Code keeps target version (safest).
   - Append source hunk preserved to `.git/merge-conductor/<task>/unresolved.md`.
   - Record `state.json::unresolved[]` entry.

### After Each Heuristic Application

- Record `state.json::decisions[i].resolution = "rule-N"` (where N is the rung number).
- Record `state.json::decisions[i].taken = "source" | "target" | "both" | "target-fallback"`.
- Immediately invoke Stage 6.5 self-audit on the resolved hunk.

### unresolved.md Format

`.git/merge-conductor/<task>/unresolved.md` accumulates:

```markdown
## Unresolved hunk h-{{nn}}

**File**: {{file}}
**Symbol**: {{symbol_or_line_range}}
**Decision**: target taken as fallback; source preserved below.

### Source side (preserved)

```diff
{{source_hunk}}
```

### Target side (taken)

```diff
{{target_hunk}}
```

Surface in Phase 2 for user adjudication: keep target / take source / merge / free-form.
```
```

- [ ] **Step 3: Commit**

```bash
cd /Users/dalwin/Documents/AI
git add skills/git-merge-conductor/references/conflict-classification.md
git commit -m "$(cat <<'EOF'
refactor(git-merge-conductor): v2 C/D 自动决策启发式 ladder + unresolved.md

5 rung ladder + 不留 conflict marker；source side 落 unresolved.md
等 Phase 2 用户决议。

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

## Task 35: Update scenario B to split into B-cherry and B-transplant

**Files:**
- Modify: `/Users/dalwin/Documents/AI/docs/superpowers/verification/git-merge-conductor/scenarios/B-backport.md`

- [ ] **Step 1: Read existing scenario B**

Run: `cat /Users/dalwin/Documents/AI/docs/superpowers/verification/git-merge-conductor/scenarios/B-backport.md`

- [ ] **Step 2: Add a "v2 sub-scenarios" section to scenario B**

Append to the file:

```markdown

## v2 sub-scenarios

In v2, backport splits into `backport-cherry` (conflict-pipeline) and
`backport-transplant` (transplant-pipeline). This scenario covers the
cherry-path; the transplant path is exercised by scenario F.

### B.1 backport-cherry path

For this scenario, the fixture is built such that `merge_base_age_days < 30` AND no rename signals.
Expected mode inference: `backport-cherry`.
Pipeline: conflict-pipeline (4c/5c/6c).
Stage 6c autonomous: C/D hunks resolved via heuristic ladder; no unresolved.
Phase 1 passes; Phase 2 user "完成"; finalize.

### B.2 backport-transplant path

See scenario F. Same backport flag but with a fixture that hits the
transplant threshold (refactor signals or aged merge-base).

## Pass criteria (v2)

- [ ] Original scenario B steps still pass
- [ ] Mode inference correctly selects `backport-cherry` (not `backport-transplant`)
- [ ] Stage 6c heuristic ladder resolves all hunks autonomously
- [ ] No code left with `<<<<<<<` markers
- [ ] If any hunk hits rung 5 fallback, unresolved.md created and surfaced in Phase 2
```

- [ ] **Step 3: Commit**

```bash
cd /Users/dalwin/Documents/AI
git add docs/superpowers/verification/git-merge-conductor/scenarios/B-backport.md
git commit -m "$(cat <<'EOF'
docs(git-merge-conductor): v2 scenario B 加 cherry/transplant 拆分

scenario B 现在专测 backport-cherry path；transplant path 由 F 覆盖。

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

## Task 36: Phase 7 smoke gate — scenarios A, B, C, E (no user mid-loop interrupts)

**Files:**
- Modify: `/Users/dalwin/Documents/AI/docs/superpowers/verification/git-merge-conductor/SMOKE-TEST.md`

- [ ] **Step 1: Re-run A, B (cherry path), C, E**

Verify all conflict-pipeline scenarios run autonomously through 6c (no
5-option decision-point prompts at Stage 6c).

- [ ] **Step 2: Verify no conflict markers left**

For each scenario after Stage 6c completes:
```bash
grep -rn "<<<<<<< " /tmp/gmc-fixture-<X>/  || echo "no markers found"
```
Expected: "no markers found" for all scenarios.

- [ ] **Step 3: Append Phase 7 gate**

```markdown
## v2 Phase 7 gate (2026-05-13)
- [ ] Scenario A: conflict-pipeline runs autonomously through 6c; no user mid-loop interrupts
- [ ] Scenario B (cherry): mode correctly = backport-cherry; autonomous
- [ ] Scenario C: patch-apply unchanged
- [ ] Scenario E: guards unchanged
- [ ] No `<<<<<<<` markers in working tree post-6c for any scenario
- [ ] unresolved.md created where rung-5 fallback hits
- [ ] No regression on F/H/I
```

- [ ] **Step 4: Commit**

```bash
cd /Users/dalwin/Documents/AI
git add docs/superpowers/verification/git-merge-conductor/SMOKE-TEST.md
git commit -m "$(cat <<'EOF'
test(git-merge-conductor): v2 Phase 7 smoke gate (autonomous 6c)

conflict-pipeline autonomous 改造完成；A/B-cherry/C/E 无中断通过。

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

# Phase 8 — 收尾

**Goal of phase:** 删 `templates/decision-point.md`、`commit-message.md` 加 iteration 字段、`wrap-up-report.md` 加 worktree 清理选项、`recovery-protocol.md` 加 worktree + iter recovery、scenario G + 全部 A-I 综合回归.

## Task 37: Delete `templates/decision-point.md`

**Files:**
- Delete: `/Users/dalwin/Documents/AI/skills/git-merge-conductor/templates/decision-point.md`

- [ ] **Step 1: Remove file**

```bash
rm /Users/dalwin/Documents/AI/skills/git-merge-conductor/templates/decision-point.md
```

- [ ] **Step 2: Search for any remaining references**

```bash
grep -rn "decision-point" /Users/dalwin/Documents/AI/skills/git-merge-conductor/ 2>/dev/null || echo "no references"
```
Expected: no references (or only this scan).

If any remain, edit those files to remove or replace the reference.

- [ ] **Step 3: Commit**

```bash
cd /Users/dalwin/Documents/AI
git add -A skills/git-merge-conductor/templates/
git commit -m "$(cat <<'EOF'
refactor(git-merge-conductor): v2 删除 templates/decision-point.md

autonomous pipeline (6c + 6t) 不再需要逐项 5 选项中断；用户决策
集中在 Stage 7.5 Phase 2 兜底报表。

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

## Task 38: Update `templates/commit-message.md` 加 iteration + rolled-back 字段

**Files:**
- Modify: `/Users/dalwin/Documents/AI/skills/git-merge-conductor/templates/commit-message.md`

- [ ] **Step 1: Read existing template**

Run: `cat /Users/dalwin/Documents/AI/skills/git-merge-conductor/templates/commit-message.md`

- [ ] **Step 2: Replace with v2 structure**

Write the file content as:

```markdown
# Commit message template (v2)

Structure for `merge: <中文说明>` commit messages produced by Stage 7.

```
merge: {{中文 subject 一句话}}

源: {{source_ref}}@{{source_sha}}
mode: {{inferred_mode}} (pipeline: {{pipeline}})
iter: {{iter_number}}

决策摘要:
{{ for each applied unit }}
- [{{path}}::{{symbol}} #{{idx}}] {{choice_label}}：{{decision_brief_中文}}
{{ end }}

{{ if has_rolled_back }}
回滚摘要 (iter {{iter}} 中 Stage 6.5 拦截):
{{ for each rolled-back unit }}
- [{{path}}::{{symbol}}] 命中 {{nc_or_constraint}}, 已 rollback
{{ end }}
{{ end }}

{{ if has_auto_resolved }}
A 类自动处理: {{n}} 处（详见 .git/merge-conductor/{{task}}/decision-log.md）
{{ end }}

{{ if has_unresolved }}
未决项: {{n}} 处（详见 .git/merge-conductor/{{task}}/unresolved.md，
将在下轮 Phase 2 由用户决议）
{{ end }}
```

Use heredoc to commit:
```bash
git commit -m "$(cat <<'EOF'
<rendered template content>
EOF
)"
```
```

- [ ] **Step 3: Commit**

```bash
cd /Users/dalwin/Documents/AI
git add skills/git-merge-conductor/templates/commit-message.md
git commit -m "$(cat <<'EOF'
refactor(git-merge-conductor): v2 commit-message 加 iter + rolled-back + unresolved

每次 Stage 7 commit message 携带 iter 号 + Stage 6.5 拦截摘要 +
unresolved 项指针，方便事后追溯多轮迭代。

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

## Task 39: Update `templates/wrap-up-report.md` 加 worktree cleanup

**Files:**
- Modify: `/Users/dalwin/Documents/AI/skills/git-merge-conductor/templates/wrap-up-report.md`

- [ ] **Step 1: Read existing wrap-up-report.md**

Run: `cat /Users/dalwin/Documents/AI/skills/git-merge-conductor/templates/wrap-up-report.md`

- [ ] **Step 2: Add a worktree-cleanup section in the cleanup-options part**

Find the existing cleanup options block (4 options). For each option, append a worktree-handling sub-line per spec §10.5:

```markdown
1. **默认 7 天保留** — 备份 tag + state 目录在下次 skill 调用时若超过 7 天自动清理
   {{ if use_worktree }}
   - worktree 同步清理（推荐）
   {{ end }}
2. **保留最近 N 个** — 保留最近 N 个 finalized 会话（询问 N）
   {{ if use_worktree }}
   - worktree 路径保留（与 state 一同保留）
   {{ end }}
3. **永久保留** — 不自动清理
   {{ if use_worktree }}
   - worktree 路径保留
   {{ end }}
4. **手动** — 打印精确清理命令，由你执行
   {{ if use_worktree }}
   - 包含 `git worktree remove {{worktree_path}}` 命令
   {{ end }}
```

Also add a summary line above the cleanup options:

```markdown
{{ if use_worktree }}
> 本次使用了独立 worktree（路径：`{{worktree_path}}`）。下方清理选项中
> 标 worktree 字样的子项决定是否同步清除 worktree 目录。
{{ end }}
```

- [ ] **Step 3: Commit**

```bash
cd /Users/dalwin/Documents/AI
git add skills/git-merge-conductor/templates/wrap-up-report.md
git commit -m "$(cat <<'EOF'
refactor(git-merge-conductor): v2 wrap-up 加 worktree 清理子选项

4 个 cleanup 选项每个 condition on use_worktree 加 worktree 处理
子项；推荐与 state 同步清理。

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

## Task 40: Update `references/recovery-protocol.md` 加 worktree + iter recovery

**Files:**
- Modify: `/Users/dalwin/Documents/AI/skills/git-merge-conductor/references/recovery-protocol.md`

- [ ] **Step 1: Read existing recovery-protocol.md**

Run: `cat /Users/dalwin/Documents/AI/skills/git-merge-conductor/references/recovery-protocol.md`

- [ ] **Step 2: Append worktree + iter recovery scenarios**

Append:

```markdown

## v2 — Worktree Recovery Scenarios

### Resume from `paused` with worktree

1. Read `state.json::working_branch.worktree_path`.
2. Check path exists with `test -d <path>`.
3. If exists:
   - Verify `git worktree list` includes the path
   - Verify the worktree's HEAD matches `merge/<task>` and tag `before-step-N` is reachable
   - Resume normally from `state.json::stage`
4. If path missing or worktree corrupt:
   - Prompt user (中文): 「检测到 worktree 缺失（{{worktree_path}}）。
     要重建 / 降级主仓 / 放弃会话？」
   - On "重建": `git worktree add <path> merge/<task>` + reset to `before-step-<stage>` tag
   - On "降级": set `worktree_path: null`, `use_worktree: false`, checkout `merge/<task>` in main repo
   - On "放弃": abort flow (same as `[a]`)

### Abort with worktree

```bash
# inside main repo
git worktree remove --force <worktree_path>
git branch -D merge/<task>
rm -rf .git/merge-conductor/<task>/
```

Confirm in 中文 before executing.

## v2 — Iteration Recovery Scenarios

### Resume mid-iter

1. Read `state.json::iter` and `state.json::iterations[<iter>]`.
2. If `iterations[<iter>].ended_at` is null:
   - Last iter was interrupted. Read `state.json::stage` for where to resume.
   - Verify the corresponding `merge/<task>/before-iter-<iter>` tag exists.
   - Resume from that stage.

### Phase 1 fix loop interrupt

If interrupted during Phase 1 self-fix:
1. Read `state.json::iterations` for `trigger: phase1-fix` entries within current iter.
2. If 3 phase1-fix entries already exist → next attempt is the surrender path; go directly to Phase 2.
3. If < 3 → continue from last phase1-fix entry's state.

### Phase 2 awaiting user response

If interrupted while waiting for Phase 2 user response:
1. `state.json::status` should be `paused` or `awaiting-user`.
2. On resume, re-render the Phase 2 report (verbatim from `merge-report.html` Phase 2 section, or regenerated from current state).
3. Wait for user response normally.
```

- [ ] **Step 3: Commit**

```bash
cd /Users/dalwin/Documents/AI
git add skills/git-merge-conductor/references/recovery-protocol.md
git commit -m "$(cat <<'EOF'
refactor(git-merge-conductor): v2 recovery-protocol 加 worktree + iter 恢复

新增场景：worktree 缺失/损坏的重建/降级/放弃；多 iter 中断的
phase1-fix 重入；Phase 2 等待用户响应时的中断恢复。

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

## Task 41: Create scenario G — worktree lifecycle (create → abort → cleanup)

**Files:**
- Create: `/Users/dalwin/Documents/AI/docs/superpowers/verification/git-merge-conductor/scenarios/G-worktree-lifecycle.md`

- [ ] **Step 1: Write scenario G doc**

```markdown
# Scenario G — worktree lifecycle (create → abort → cleanup)

## Goal

Verify worktree integration end-to-end:
- Complex mode (e.g., backport-transplant) triggers worktree at Stage 3
- Worktree created via superpowers:using-git-worktrees, path written to state.json
- Mid-pipeline `[a]` abort cleanly removes worktree + branch + state dir
- Main repo working tree unchanged before/after

## Setup

```bash
cd /tmp && rm -rf gmc-fixture-G
bash /Users/dalwin/Documents/AI/docs/superpowers/verification/git-merge-conductor/setup-fixture.sh
mv /tmp/gmc-fixture-F /tmp/gmc-fixture-G
cd /tmp/gmc-fixture-G

# Make a local change in main repo so we can verify it's preserved
echo "// MAIN-LOCAL-MARKER" >> src/main/java/com/example/course/CourseOffline.java
```

## Run

Start Claude Code in `/tmp/gmc-fixture-G`. Invoke scenario F's instructions.

When the pipeline reaches Stage 6t and shows a banner like
`[Stage 6t · Autonomous Apply Loop · ...]`, send the abort command:
> `[a]`

## Expected behavior

### After Stage 3
- Worktree created at some path (e.g., `/tmp/gmc-fixture-G-worktrees/care-class-transplant`)
- `state.json::working_branch.worktree_path` populated
- Main repo's `src/main/java/com/example/course/CourseOffline.java` STILL has the `MAIN-LOCAL-MARKER` line (worktree changes don't affect main repo's working tree)
- Banner clearly indicates work is happening in worktree (e.g., banner shows the working branch name)

### On abort

- Model confirms in 中文: 「确认 abort 会删除 worktree、merge/<task> 分支、所有会话元数据。确认？」
- User says 「确认」
- Model executes:
  ```bash
  git worktree remove --force <path>
  git branch -D merge/<task>
  rm -rf .git/merge-conductor/<task>/
  ```
- Model echoes 「abort 完成。worktree、分支、会话目录已清理。主仓回到 abort 前状态。」

### Verification commands

```bash
# Worktree gone
git worktree list
# Expected: only main repo listed

# Branch gone
git branch | grep "merge/care-class-transplant" || echo "branch deleted"

# State dir gone
ls .git/merge-conductor/ 2>/dev/null || echo "state dir empty"

# Main repo preserved
grep "MAIN-LOCAL-MARKER" src/main/java/com/example/course/CourseOffline.java
# Expected: marker still present
```

## Pass criteria

- [ ] Worktree created at Stage 3 (not main repo)
- [ ] Main repo working tree unchanged during pipeline
- [ ] Abort confirmation prompt in 中文
- [ ] Abort cleans worktree + branch + state dir
- [ ] Main repo state preserved after abort
```

- [ ] **Step 2: Commit**

```bash
cd /Users/dalwin/Documents/AI
git add docs/superpowers/verification/git-merge-conductor/scenarios/G-worktree-lifecycle.md
git commit -m "$(cat <<'EOF'
test(git-merge-conductor): v2 scenario G (worktree lifecycle)

验证复杂 mode 创建 worktree + 中途 abort 清理 + 主仓不受影响。

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

## Task 42: Update D scenario (interrupt-resume) 加 worktree resume 子场景

**Files:**
- Modify: `/Users/dalwin/Documents/AI/docs/superpowers/verification/git-merge-conductor/scenarios/D-interrupt-resume.md`

- [ ] **Step 1: Read existing scenario D**

Run: `cat /Users/dalwin/Documents/AI/docs/superpowers/verification/git-merge-conductor/scenarios/D-interrupt-resume.md`

- [ ] **Step 2: Append a v2 sub-scenario**

```markdown

## v2 sub-scenario: worktree resume

This sub-scenario verifies `references/recovery-protocol.md#worktree-recovery-scenarios`.

### Setup

Same as scenario F (backport-transplant fixture).

### Steps

1. Start a session per scenario F.
2. When pipeline reaches Stage 5t, send `[p]` pause.
3. Verify worktree path persisted in `state.json::working_branch.worktree_path`.
4. End the Claude Code session entirely.
5. Optionally remove the worktree directory manually:
   ```bash
   rm -rf /tmp/gmc-fixture-F-worktrees/care-class-transplant
   ```
6. Start a fresh Claude Code session in `/tmp/gmc-fixture-F` (main repo).
7. The pipeline should detect the existing `state.json` with `status: paused`
   and prompt for resume.
8. Skill detects the worktree is missing and prompts:
   「检测到 worktree 缺失。要重建 / 降级主仓 / 放弃？」
9. Test all three responses:
   - "重建" → worktree re-created, pipeline continues from saved stage
   - "降级" → main repo checkout used, banner indicates downgrade
   - "放弃" → abort flow

### Pass criteria

- [ ] Pause persists worktree_path
- [ ] Resume detects missing worktree
- [ ] 重建 path: pipeline continues to Stage 5t state
- [ ] 降级 path: state.json::use_worktree flipped to false
- [ ] 放弃 path: clean abort
```

- [ ] **Step 3: Commit**

```bash
cd /Users/dalwin/Documents/AI
git add docs/superpowers/verification/git-merge-conductor/scenarios/D-interrupt-resume.md
git commit -m "$(cat <<'EOF'
docs(git-merge-conductor): v2 scenario D 加 worktree resume 子场景

测试 worktree 缺失时的 3 种 resume 路径（重建/降级/放弃）。

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

## Task 43: Update `SMOKE-TEST.md` 加 v2 完整场景注册 + final gate

**Files:**
- Modify: `/Users/dalwin/Documents/AI/docs/superpowers/verification/git-merge-conductor/SMOKE-TEST.md`

- [ ] **Step 1: Read existing SMOKE-TEST.md**

Run: `cat /Users/dalwin/Documents/AI/docs/superpowers/verification/git-merge-conductor/SMOKE-TEST.md`

- [ ] **Step 2: Add a v2 scenarios index at the top of the document (or append a new "v2 catalog" section)**

Append (or insert near the top, before the v1 scenarios list):

```markdown

## v2 Scenario Catalog

| ID | Name | Purpose | Pipeline |
|---|---|---|---|
| A | forward-integrate | feature + target hotfix integration | conflict |
| B.1 | backport-cherry | cherry-pick path (close merge-base) | conflict |
| B.2 | backport-transplant | see scenario F | transplant |
| C | patch-apply | git am patch | conflict |
| D | interrupt-resume | pause/resume + v2 worktree resume | conflict |
| E | guard | Stage 0 guards (submodule/LFS/dirty) | n/a |
| F | backport-transplant care-class | NC-01 intercept + 2-iter finalize | transplant |
| G | worktree lifecycle | create / abort / cleanup | transplant |
| H | Phase 1 self-fix limit | N=3 cap; surrender to Phase 2 | transplant |
| I | Phase 2 multi-iter | 3-iter user feedback loop | transplant |

Pipeline-coverage gate before declaring v2 ready:
- [ ] All 10 entries above run cleanly (or with documented expected behavior per scenario doc).
- [ ] No regressions in A/B.1/C/D.v1/E (v1 base scenarios pass under v2).
- [ ] Smoke gates Phase 1-8 all checked.
```

- [ ] **Step 3: Add final v2 acceptance gate**

Append:

```markdown
## v2 Final Acceptance Gate (2026-05-13)

- [ ] All Phase 1-8 partial gates checked above
- [ ] All 10 v2 catalog scenarios pass per their docs
- [ ] SKILL.md line count: 200-220 ± 10
- [ ] references/contracts/ has 5 files, all with anchors per Reading Order
- [ ] No references to deleted templates/decision-point.md
- [ ] negative-constraints.md NC-01~05 present + 领域附录
- [ ] requirements.yaml, grafting-plan.yaml, draft.md, audit-report.md,
      verification-report.md templates present and valid YAML/markdown
- [ ] state.json::version == "2.0" in all new sessions
- [ ] No `<<<<<<<` markers ever in code post-6c
- [ ] Worktree delegation works for all 4 complex modes
```

- [ ] **Step 4: Commit**

```bash
cd /Users/dalwin/Documents/AI
git add docs/superpowers/verification/git-merge-conductor/SMOKE-TEST.md
git commit -m "$(cat <<'EOF'
test(git-merge-conductor): v2 final acceptance gate + scenario catalog

完整 10 个 v2 场景注册表 + Phase 1-8 gate 汇总 + 验收 checklist。

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

## Task 44: Phase 8 smoke gate — full A-I regression

**Files:**
- Modify: `/Users/dalwin/Documents/AI/docs/superpowers/verification/git-merge-conductor/SMOKE-TEST.md`

- [ ] **Step 1: Sequential re-run of all 10 scenarios**

Run each scenario from a fresh fixture rebuild. Check off the v2 final acceptance gate items as you go.

- [ ] **Step 2: Inspect for any straggler issues**

```bash
# Find any TODO/TBD/FIXME left in the skill or docs:
grep -rn "TBD\|TODO\|FIXME" /Users/dalwin/Documents/AI/skills/git-merge-conductor/ /Users/dalwin/Documents/AI/docs/superpowers/verification/git-merge-conductor/
# Expected: only comments in user-facing template placeholders, not implementation gaps
```

- [ ] **Step 3: Final commit if anything needed fixing in step 2**

If you found any leftover issue:
```bash
cd /Users/dalwin/Documents/AI
git add <fixed files>
git commit -m "$(cat <<'EOF'
fix(git-merge-conductor): v2 final regression sweep cleanup

[describe the small fix]

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

- [ ] **Step 4: Append final v2 acceptance gate close-out to SMOKE-TEST.md**

```markdown

## v2 Acceptance Complete ✓ (2026-05-13)

All Phase 1-8 gates passed. All 10 scenarios passed. SKILL.md 200-220 lines. v2 ready.

Sign-off: jpdalwin (czw) — see `docs/superpowers/specs/2026-05-13-git-merge-conductor-v2-design.md`.
```

- [ ] **Step 5: Commit final close-out**

```bash
cd /Users/dalwin/Documents/AI
git add docs/superpowers/verification/git-merge-conductor/SMOKE-TEST.md
git commit -m "$(cat <<'EOF'
test(git-merge-conductor): v2 acceptance complete

Phase 1-8 + 10 场景全绿；v2 ready for production use.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

## Self-Review Notes (post-plan)

**Spec coverage check:**

- Spec §1 4 决策点 → Task 11 (Stage 7.5 Phase 1+2) + Task 5 (worktree) + Task 25 (NC-05 SI) + Task 13 (五字段下沉) ✓
- Spec §2 方案 B 双轨制 → Task 19 (split mode) + Task 9-10 (contracts) ✓
- Spec §3 Pipeline 总览 → Task 13 SKILL.md 重写 ✓
- Spec §4 SKILL.md 主薄 → Task 13 ✓
- Spec §5 requirements.yaml → Task 15 + Task 17 ✓
- Spec §6 transplant-pipeline → Task 10 + Task 20 + Task 21 + Task 22 ✓
- Spec §7 conflict-pipeline autonomous → Task 9 + Task 34 ✓
- Spec §8 Stage 6.5 + NC → Task 11 + Task 25 + Task 26 + Task 27 ✓
- Spec §9 Stage 7.5 → Task 11 + Task 29 + Task 30 ✓
- Spec §10 worktree → Task 5 + Task 40 ✓
- Spec §11 Stage 可见性 → Task 2 + Task 3 + Task 4 ✓
- Spec §12 文件清单 → covered across all tasks; Task 37 explicit deletion ✓
- Spec §13 兼容性 + 验证 + 实施分阶段 → all 8 phases covered ✓
- Spec §14 风险 → spec-level, not implementation; n/a
- Spec §15 v1 关系总结 → spec-level, n/a

**Placeholder scan:** Plan contains TBD-like text only where templates explicitly use `{{var}}` placeholders — those are intentional template syntax, not plan gaps.

**Type consistency:** `requirements.yaml` schema (Task 15) matches references in Task 17, Task 21, Task 25, Task 27, Task 29. `grafting-plan.yaml` schema (Task 20) matches Task 10, Task 22, Task 25. `state.json` v2 fields (Task 1) reused consistently throughout.

**Phase ordering rationale (per user's choice):** Phase 4 (transplant-pipeline mechanics) before Phase 7 (conflict-pipeline autonomous) so care-class main complaint is resolved early; Phase 5 (NC) directly after transplant gives the audit teeth; Phase 6 (Stage 7.5) closes the verification loop before conflict-pipeline gets autonomous treatment.

---

> Plan complete. 44 tasks across 8 phases. Use the executing-plans or
> subagent-driven-development skill to walk through.
