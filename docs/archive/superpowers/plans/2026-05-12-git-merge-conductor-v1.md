# Git Merge Conductor v1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the `git-merge-conductor` skill from [docs/superpowers/specs/2026-05-11-git-merge-conductor-design.md](../specs/2026-05-11-git-merge-conductor-design.md): an end-to-end git merge orchestrator skill that drives a strict 8-stage pipeline (entry probe → input normalization → mode inference + strategy report gate → working branch → source-side application → conflict classification → semantic mapping → decision point loop → commit → wrap-up) with A/B/C/D conflict classification, mode-aware tuning, semantic mapping for cross-version backports, terminal markdown + self-contained HTML mirror, and 5 verification scenarios.

**Architecture:** Pure prompt-driven, zero-external-dependency skill. Single `SKILL.md` (English, ~800-1200 lines) holds the 8-stage orchestration. `references/` (6 English files) holds machine-facing rule sets and schemas. `templates/` (4 Chinese files) holds user-facing markdown templates. Runtime state lives in the consumer repo at `<repo>/.git/merge-conductor/<task-name>/`. No scripts in v1 (planned for v2 per spec §11.1).

**Tech Stack:** Markdown only. No code dependencies. Verification uses Bash + git CLI against a toy fixture repo.

**Spec reference:** The design spec is the canonical content source. Tasks below say "copy spec §X verbatim" rather than duplicating ~1000 lines. The spec is committed to git at `89226dd` and won't drift.

**Language convention reminder (spec §13):**

| Content | Language |
|---|---|
| `SKILL.md` body | English |
| `references/*.md` (rules, schemas, prompts) | English |
| `templates/*.md` (user-facing fixed text) | Chinese |
| Template placeholders (`{{var_name}}`) | English |
| skill-generated commit message | `merge: 中文说明` |
| HTML report visible text | Chinese (`<html lang="zh-CN">`) |

**Commit convention for THIS plan's tasks:** Use `feat(git-merge-conductor): ...` (we're building the skill itself, not running it). The `merge:` prefix is reserved for the skill's runtime output.

---

## Scope Check

Single skill, single workflow. No subsystem decomposition needed. Spec confirms this is one cohesive 8-stage pipeline.

## File Structure

```
skills/git-merge-conductor/
├── SKILL.md                              # English, ~800-1200 lines
├── references/
│   ├── mode-inference.md                 # English, decision tree
│   ├── conflict-classification.md        # English, A/B/C/D rules
│   ├── semantic-mapping.md               # English, Stage 5.5 search
│   ├── html-report-template.md           # English skeleton + Chinese visible text
│   ├── state-schema.md                   # English, state.json schema
│   └── recovery-protocol.md              # English, recovery scenarios
└── templates/
    ├── strategy-report.md                # Chinese
    ├── decision-point.md                 # Chinese (5 candidate options)
    ├── commit-message.md                 # Chinese (`merge:` prefix)
    └── wrap-up-report.md                 # Chinese (4 cleanup options)

docs/superpowers/verification/git-merge-conductor/
├── README.md                             # how to run verification
├── setup-fixture.sh                      # build toy repo
└── scenarios/
    ├── A-forward-integrate.md            # scenario steps + expected outputs
    ├── B-backport.md
    ├── C-patch-apply.md
    ├── D-interrupt-resume.md
    └── E-guard.md
```

Verification fixtures live outside the skill package to keep the skill clean for distribution.

---

## Task 1: Scaffold Skill Directory

**Files:**
- Create: `skills/git-merge-conductor/`
- Create: `skills/git-merge-conductor/references/`
- Create: `skills/git-merge-conductor/templates/`
- Create: `skills/git-merge-conductor/SKILL.md` (empty placeholder)
- Create: empty placeholders for 6 references + 4 templates

- [ ] **Step 1: Verify the skills directory exists and check current layout**

Run:
```bash
ls /Users/dalwin/Documents/AI/skills/
```
Expected: shows existing `spec-architect/` directory (the only existing skill).

- [ ] **Step 2: Create skill directory tree**

Run:
```bash
mkdir -p /Users/dalwin/Documents/AI/skills/git-merge-conductor/references
mkdir -p /Users/dalwin/Documents/AI/skills/git-merge-conductor/templates
```

- [ ] **Step 3: Create empty placeholders for all 11 files**

Run:
```bash
cd /Users/dalwin/Documents/AI/skills/git-merge-conductor
touch SKILL.md
touch references/mode-inference.md
touch references/conflict-classification.md
touch references/semantic-mapping.md
touch references/html-report-template.md
touch references/state-schema.md
touch references/recovery-protocol.md
touch templates/strategy-report.md
touch templates/decision-point.md
touch templates/commit-message.md
touch templates/wrap-up-report.md
```

- [ ] **Step 4: Verify scaffold**

Run:
```bash
find /Users/dalwin/Documents/AI/skills/git-merge-conductor -type f | sort
```
Expected: 11 .md files listed in the structure above.

- [ ] **Step 5: Commit scaffold**

```bash
cd /Users/dalwin/Documents/AI
git add skills/git-merge-conductor/
git commit -m "feat(git-merge-conductor): scaffold skill directory tree"
```

---

## Task 2: Write SKILL.md (English, main orchestration)

**Files:**
- Modify: `skills/git-merge-conductor/SKILL.md`

**Content source:** Compose from spec §1 (overview), §4 (architecture + 8-stage pipeline), §5 (Stage 0-8 contracts), §13 (language convention). The SKILL.md is the runtime entry — it tells the model how to execute the workflow.

- [ ] **Step 1: Write SKILL.md frontmatter**

Frontmatter exact content (copy spec §1.2 description verbatim into `description:`):

```yaml
---
name: git-merge-conductor
description: >
  Use when you need to merge / backport / forward-integrate code across branches
  in scenarios git cannot 3-way merge cleanly: cross-version backport (deployed
  or refactored branch → develop), forward-integrate upstream hotfix into a
  feature branch and merge feat back, cherry-pick set across diverged code,
  patch/diff application to a moved target, etc. Drives the full flow end-to-end:
  branch reconnaissance → mode inference → strategy report → working branch
  creation → automatic trivial conflict resolution → method-level conflict
  report (terminal markdown + self-contained HTML mirror) → user single-point
  decisions → commit. Triggers on phrases like "把 X 合并到 dev", "backport",
  "归并到主线", "feature 合 dev 同时带上 dev 的 hotfix", "跨版本合并", "patch
  应用". Do NOT use for fast-forward merges or single-commit cherry-picks where
  plain git handles it cleanly.
---
```

- [ ] **Step 2: Write SKILL.md body sections**

Body structure (sections in order, English):

1. **Role & Boundaries** — copy from spec §1.3 (capability table) + §1.4 (non-goals) + §1.5 (constraints/risks). State role: end-to-end executor; safety invariants: target branch never touched, state in `.git/merge-conductor/<task>/`, backup tags every stage.
2. **Invocation & Entry Probe (Stage 0)** — copy spec §5.1 Stage 0 commands + guard table. Include the 4 guard scenarios (not in repo / dirty work tree / same-name branch / submodule or LFS).
3. **Input Normalization (Stage 1)** — copy spec §5.1 input spec yaml block. Three input types (branch ref / .patch+.diff / task description) merged into one spec.
4. **Mode Inference + Strategy Report (Stage 2)** — describe gate behavior; reference `references/mode-inference.md` for the decision tree; require strategy report generation per `templates/strategy-report.md`; describe acceptable user responses (approve / correct mode / freeform adjust → re-emit report).
5. **Working Branch Setup (Stage 3)** — commands: `git checkout -b merge/<task> <base>`; tag `before-step-3`; write `state.json` and `decision-log.md` skeleton.
6. **Source-side Application (Stage 4)** — copy spec §5.3 table of mode → command chain. Use `--no-commit` everywhere. Collect unmerged files via `git diff --name-only --diff-filter=U`.
7. **Conflict Classification (Stage 5)** — reference `references/conflict-classification.md` for A/B/C/D rules. Apply A class actions (silent take target; demoted to log-then-take-target in backport mode). Collect C/D into decision queue.
8. **Semantic Mapping (Stage 5.5)** — conditional: only for backport / rebase-onto / when `refactor_signals_in_target: true`. Reference `references/semantic-mapping.md` for search strategy. Attach mapping evidence to decision point metadata.
9. **Decision Point Loop (Stage 6)** — render each decision per `templates/decision-point.md` (5 candidate options). Sync to `merge-report.html`. Accept user input: 1-5, freeform, or `[s]`/`[p]`/`[a]`. For freeform: echo "我理解为..." for second confirmation.
10. **Commit (Stage 7)** — per-mode commit granularity table (copy spec §5.5). Commit message format `merge: 中文说明` per `templates/commit-message.md`.
11. **Wrap-up (Stage 8)** — terminal summary per `templates/wrap-up-report.md`. Present 4 cleanup options to user.
12. **Failure / Pause / Abort / Recovery** — reference `references/recovery-protocol.md`. Reiterate invariants.
13. **Language Convention** — terminal text in Chinese; internal model prompts in English; commits prefixed `merge:` with Chinese description.

Use this skeleton:

```markdown
---
<frontmatter from Step 1>
---

# Git Merge Conductor

You orchestrate complex git merges end-to-end via a strict 8-stage pipeline.

## Role & Safety Invariants

- ...
- The target branch is NEVER touched. All writes happen on `merge/<task-name>`.
- ...

## Stage 0 — Entry Probe & Guards

On invocation, immediately run (parallel, read-only):
```bash
git rev-parse --is-inside-work-tree
git status --porcelain
git branch --show-current
git branch -a --sort=-committerdate | head -30
```

Then echo a 中文 status briefing to the user.

### Guards

| Condition | Action |
|---|---|
| Not in a git repo | 报错，请用户 cd 到 repo |
| Dirty work tree | 询问「先 stash / 先 commit / 取消」 |
| `merge/<task>` already exists | 询问「恢复未完成会话 / 删除后重建 / 取消」 |
| Submodule or LFS detected | 中止，提示预处理（v1 不支持） |

## Stage 1 — Input Normalization

<copy spec §5.1 yaml schema verbatim>

Show the spec to the user in 中文 markdown for quick-check. Not a gate.

## Stage 2 — Mode Inference + Strategy Report (★ Gate ★)

Read `references/mode-inference.md` for the decision tree. Render the strategy report
using `templates/strategy-report.md`. Write to `.git/merge-conductor/<task>/strategy.md`
and echo to terminal.

User responses:
- 「策略 OK」 → proceed to Stage 3
- Correction → re-emit report
- Freeform adjust → echo 「我理解为...」, get confirmation, then re-emit changed sections

## Stage 3 — Working Branch Setup

```bash
git checkout -b merge/<task> <base-commit>
git tag merge/<task>/before-step-3
```

Write `state.json` (per `references/state-schema.md`) and seed `decision-log.md`.

## Stage 4 — Source-side Application

<copy spec §5.3 mode→command table>

Always use `--no-commit`. After execution, collect unmerged files:
```bash
git diff --name-only --diff-filter=U
```

Tag `before-step-4`.

## Stage 5 — Conflict Classification

For each unmerged hunk, classify per `references/conflict-classification.md` (A/B/C/D).

- A class: apply silently (in `backport` mode, write to decision-log instead).
- B class: already auto-merged by git; record count only.
- C/D class: append to decision queue.

Tag `before-step-5`.

## Stage 5.5 — Semantic Mapping (conditional)

Trigger only if mode ∈ {backport, rebase-onto} OR `refactor_signals_in_target == true`.

For each C/D decision point, run searches per `references/semantic-mapping.md`. Attach
mapping evidence to decision metadata.

## Stage 6 — Decision Point Loop (★ Interactive ★)

For each decision in the queue:

1. Render decision point per `templates/decision-point.md` (5 candidate options).
2. Append corresponding `<article>` to `merge-report.html`.
3. Wait for user input: `1`-`5`, freeform, or `[s]`/`[p]`/`[a]`.
4. If `5` (freeform): echo 「我理解为...」 and get second confirmation.
5. Apply selected change to working branch.
6. Update `state.json`, `decision-log.md`, and HTML report `<article>` state.

Tag `before-step-6` (once before loop starts).

## Stage 7 — Finalization & Commit

Commit per mode default (or user override from Stage 2):

<copy spec §5.5 commit granularity table>

Commit message format (per `templates/commit-message.md`):

```
merge: <中文说明本 commit 做了哪些事情>

源: <source_ref>@<sha>
mode: <inferred-mode>
决策摘要:
- ...
A 类自动处理: N 处
```

Tag `merge/<task>/done`.

## Stage 8 — Wrap-up

Render terminal summary per `templates/wrap-up-report.md`. Present 4 cleanup options:
- [1] Default 7-day retention
- [2] Last-N retention (specify N)
- [3] Permanent retention
- [4] Manual (echo commands, user decides)

Persist user's choice in `state.json::cleanup_policy`.

## Failure / Pause / Abort / Resume

Reference `references/recovery-protocol.md` for all recovery scenarios.

Invariants:
- Target branch never modified.
- `.git/merge-conductor/<task>/` is safe to delete at any time.
- All backup tags exist; `git reset --hard merge/<task>/before-step-N` always works.

## Language Convention

- User-visible terminal output: 中文
- Internal prompts / rules / schemas (this file + references/): English
- Commit message: `merge: 中文说明`
- HTML report visible text: 中文 (`<html lang="zh-CN">`)
```

Use this skeleton; expand each section with content from the spec sections referenced. The final SKILL.md should be 800-1200 lines.

- [ ] **Step 3: Verify SKILL.md structure**

Run:
```bash
grep "^## " /Users/dalwin/Documents/AI/skills/git-merge-conductor/SKILL.md
```
Expected output: all stage headings present (Stage 0 through Stage 8 + supporting sections).

Run:
```bash
head -25 /Users/dalwin/Documents/AI/skills/git-merge-conductor/SKILL.md
```
Expected: frontmatter with `name: git-merge-conductor` and `description: ...` block.

- [ ] **Step 4: Verify language**

The body must be English (except quoted Chinese examples in tables). Spot-check:
```bash
grep -c "## Stage" /Users/dalwin/Documents/AI/skills/git-merge-conductor/SKILL.md
```
Expected: ≥ 9 (Stages 0-8).

- [ ] **Step 5: Commit**

```bash
cd /Users/dalwin/Documents/AI
git add skills/git-merge-conductor/SKILL.md
git commit -m "feat(git-merge-conductor): write SKILL.md 8-stage orchestration"
```

---

## Task 3: Write references/mode-inference.md

**Files:**
- Modify: `skills/git-merge-conductor/references/mode-inference.md`

**Content source:** Spec §6.1 verbatim (English). 

- [ ] **Step 1: Open spec §6.1**

Run:
```bash
grep -n "^### 6.1" /Users/dalwin/Documents/AI/docs/superpowers/specs/2026-05-11-git-merge-conductor-design.md
```
Note the line number range for §6.1.

- [ ] **Step 2: Write mode-inference.md content**

The file content is the full body of spec §6.1 (English). Structure:

```markdown
# Mode Inference

> Internal reference used by SKILL.md Stage 2 to infer merge mode from the
> normalized task spec produced in Stage 1.

## Purpose

Given a merge task spec, output the inferred mode with confidence + alternatives + evidence.

## Input

Yaml from Stage 1 (see SKILL.md Stage 1).

## Output Schema

```yaml
mode: backport
confidence: high | medium | low
alternatives:  # only when confidence != high
  - mode: cherry-pick-set
    reason: "explicit commit range provided by user"
evidence:
  merge_base_age_days: 35
  source_commit_count: 8
  patch_files_present: false
  target_diverged_commits_since_merge_base: 142
  keyword_signals: ["回灌", "backport"]
  refactor_signals_in_target: true
```

## Decision Tree

1. If sources contain any .patch or .diff files → `patch-apply`
2. Elif description contains "rebase onto" OR "feature 长期落后" OR "重构后的 main" → `rebase-onto`
3. Elif description matches "先把 X 的 fix 带进 Y 再 merge 回" pattern → `forward-integrate`
4. Elif user provided explicit commit range OR source_commit_count ≤ 5 → `cherry-pick-set`
5. Elif merge_base_age_days > 30 OR keyword in {"回灌", "backport", "跨版本"} OR target has refactor signals → `backport`
6. Elif source is active branch (committed in last 7d) AND no commit range → `full-merge`
7. Else → low confidence, default to `cherry-pick-set` with alternatives [full-merge, backport]

## Refactor Signal Detection

For each file modified on source side:
- Run `git log --follow --diff-filter=R -- <file>` on target since merge-base
- If ≥1 rename detected → set `refactor_signals_in_target: true`

## Confidence Scoring

- **high**: ≥ 2 strong signals point to same mode AND no contradicting signals
- **medium**: 1 strong signal + no contradicting signals
- **low**: contradicting signals OR weak signals only → list alternatives in strategy report
```

- [ ] **Step 3: Verify file**

Run:
```bash
grep "^## " /Users/dalwin/Documents/AI/skills/git-merge-conductor/references/mode-inference.md
```
Expected: headings include `Purpose`, `Input`, `Output Schema`, `Decision Tree`, `Refactor Signal Detection`, `Confidence Scoring`.

- [ ] **Step 4: Commit**

```bash
cd /Users/dalwin/Documents/AI
git add skills/git-merge-conductor/references/mode-inference.md
git commit -m "feat(git-merge-conductor): add mode-inference reference"
```

---

## Task 4: Write references/conflict-classification.md

**Files:**
- Modify: `skills/git-merge-conductor/references/conflict-classification.md`

**Content source:** Spec §6.2 verbatim (English). This is the biggest reference — A/B/C/D rules with detailed sub-cases.

- [ ] **Step 1: Write conflict-classification.md content**

Copy the complete spec §6.2 content into the file. Structure must include:

```markdown
# Conflict Classification

> Internal reference for SKILL.md Stage 5. Classifies each unmerged hunk as
> A/B/C/D class with action.

## Purpose
## Input / Output
## A Class — Silent Take Target
  ### A.1 Pure whitespace / EOL
  ### A.2 Pure comment-only changes
  ### A.3 Import / using statement reorder
  ### A.4 Code formatting (no semantic change)
  ### A.5 Pure local variable rename
## B Class — Silent Take Source
  ### B.1 / B.2
## C Class — Require Human Decision
  ### C.1 Same method body, both sides logic change
  ### C.2 Same expression / constant value
  ### C.3 Incompatible signature change
## D Class — Flag + Require Human Decision
  ### D.1 Symbol removed by one side, modified by other
  ### D.2 Both sides modified imports
  ### D.3 Rename tracking ambiguity
  ### D.4 Binary file conflict
  ### D.5 Hunk in file with detected refactoring
  ### D.6 Patch context mismatch (patch-apply only)
## Mode-Aware Tuning
## Locked File Rules
```

Each A.x / C.x / D.x sub-section must include:
- **Detection**: how the model identifies this case
- **Action**: what to do (and in backport mode, the demoted action for A class)
- **Examples** (optional, for ambiguous cases)

The spec already has these fully written. Copy verbatim.

- [ ] **Step 2: Verify all 5 A-class + 3 C-class + 6 D-class sub-rules present**

Run:
```bash
grep -E "^### [ABCD]\." /Users/dalwin/Documents/AI/skills/git-merge-conductor/references/conflict-classification.md | wc -l
```
Expected: 16 (A.1-5, B.1-2, C.1-3, D.1-6) = 16.

- [ ] **Step 3: Verify mode-aware tuning section exists**

Run:
```bash
grep "^## Mode-Aware" /Users/dalwin/Documents/AI/skills/git-merge-conductor/references/conflict-classification.md
```
Expected: exactly one match.

- [ ] **Step 4: Verify backport demotion is documented**

Run:
```bash
grep -i "log-then-take-target\|demoted" /Users/dalwin/Documents/AI/skills/git-merge-conductor/references/conflict-classification.md
```
Expected: at least one match in A class section.

- [ ] **Step 5: Commit**

```bash
cd /Users/dalwin/Documents/AI
git add skills/git-merge-conductor/references/conflict-classification.md
git commit -m "feat(git-merge-conductor): add A/B/C/D conflict classification rules"
```

---

## Task 5: Write references/semantic-mapping.md

**Files:**
- Modify: `skills/git-merge-conductor/references/semantic-mapping.md`

**Content source:** Spec §6.3 verbatim (English).

- [ ] **Step 1: Write semantic-mapping.md content**

Content structure:

```markdown
# Semantic Mapping (Stage 5.5)

> Internal reference for SKILL.md Stage 5.5. Triggered only in backport /
> rebase-onto / cross-version modes.

## Trigger
Only in `backport`, `rebase-onto`, or any mode with `refactor_signals_in_target: true`.
Run for each C/D class hunk in Stage 5.5.

## Goal
For each conflict hunk, search the target branch for "the refactored counterpart"
of source-side modified symbols.

## Search Strategy

### 1. Extract source-side modified symbols (per hunk)
- methods/functions: name + signature
- classes/types: name + key members
- constants: name + value

### 2. For each symbol, run candidate searches (in order)
- **Direct grep** on target HEAD: `git grep -n "<symbol_name>" -- '*.{ext}'`
- **Rename trail**: `git log --all --follow --diff-filter=R -- <original_file>`
- **Cross-file rename**: `git log --all --diff-filter=R --find-renames=70%`
- **Similar-signature heuristic**: search target for methods with same param types/return type, within neighboring files (proximity by directory)

### 3. Score mapping confidence
- **high**: direct grep hit + signature unchanged + same calling context
- **medium**: rename trail follows + signature similar but changed
- **low**: similar-signature heuristic match only OR multiple candidates

### 4. Attach mapping evidence to decision point metadata

## Output Schema (per decision point)

<copy spec §6.3 yaml schema verbatim>

## Low-Confidence Handling

When confidence = low, still present the mapping in decision point but mark with
`⚠ 映射置信度低，请人工校验`. Do NOT auto-apply.
```

- [ ] **Step 2: Verify file structure**

Run:
```bash
grep "^## \|^### " /Users/dalwin/Documents/AI/skills/git-merge-conductor/references/semantic-mapping.md
```
Expected: includes `Trigger`, `Goal`, `Search Strategy` with 4 sub-sections, `Output Schema`, `Low-Confidence Handling`.

- [ ] **Step 3: Commit**

```bash
cd /Users/dalwin/Documents/AI
git add skills/git-merge-conductor/references/semantic-mapping.md
git commit -m "feat(git-merge-conductor): add semantic-mapping reference"
```

---

## Task 6: Write references/html-report-template.md

**Files:**
- Modify: `skills/git-merge-conductor/references/html-report-template.md`

**Content source:** Spec §6.4 verbatim (English skeleton + Chinese visible text in HTML template).

- [ ] **Step 1: Write html-report-template.md content**

Content structure:

```markdown
# HTML Report Template

> Internal reference for the self-contained HTML mirror written alongside
> terminal interactions.

## Purpose
Define the structure of `merge-report.html`.

## Constraints
- Self-contained: inline CSS + inline JS (or sibling `.js` if size > 200KB)
- Allow vanilla JS for: section folding, decision-point jump links, syntax highlighting, real-time selection state styling
- No external resources (CDN, fonts, images)
- Offline-openable, printable
- Append-mode writes: each new decision point appended as a new `<article>`; status updates rewrite in-place

## Skeleton

<copy spec §6.4 full HTML skeleton verbatim, including style block, header, nav.toc, sections, article example, script block>

## Write Semantics
- Stage 2 → write skeleton + strategy section
- Stage 5 → append auto-resolved summary
- Stage 6 → append each decision article as pending, rewrite class to resolved/skipped on user choice
- Stage 8 → finalize footer status

## JS Constraints
- Vanilla JS only (no jQuery, no framework)
- Inline `<script>` block, ≤ 100 lines
- Or sibling `merge-report.js` if HTML > 200KB
- Allowed features: smooth scroll, keyboard shortcuts (j/k for decision jump), TOC count updates, collapsible long diffs (auto-collapse if > 80 lines)
```

- [ ] **Step 2: Verify HTML skeleton present**

Run:
```bash
grep -c "article id=" /Users/dalwin/Documents/AI/skills/git-merge-conductor/references/html-report-template.md
```
Expected: ≥ 1 (the example decision article).

Run:
```bash
grep "lang=\"zh-CN\"" /Users/dalwin/Documents/AI/skills/git-merge-conductor/references/html-report-template.md
```
Expected: ≥ 1 match.

- [ ] **Step 3: Commit**

```bash
cd /Users/dalwin/Documents/AI
git add skills/git-merge-conductor/references/html-report-template.md
git commit -m "feat(git-merge-conductor): add HTML report template"
```

---

## Task 7: Write references/state-schema.md

**Files:**
- Modify: `skills/git-merge-conductor/references/state-schema.md`

**Content source:** Spec §6.5 verbatim (English JSON schema).

- [ ] **Step 1: Write state-schema.md content**

```markdown
# State Schema

> Internal reference for `.git/merge-conductor/<task>/state.json`.

## Purpose
Machine-readable state persisted across the 8-stage pipeline; consumed by
recovery / resume flows.

## Location
`<repo>/.git/merge-conductor/<task-name>/state.json`

## Schema

<copy spec §6.5 JSON schema verbatim, including version, task_name, mode,
created_at, paused_at, finalized_at, status, source, target, working_branch,
stage, stage_history, decisions, auto_resolved_summary, config, cleanup_policy>

## Validation Rules

- `stage` must match the most recent entry in `stage_history`
- `working_branch` must exist in git (validated on resume)
- `source.sha` and `target.head_sha` must still exist (otherwise force-push detected, refuse to resume)

## Sibling Files

| File | Purpose |
|---|---|
| `state.json` | machine state (this file) |
| `decision-log.md` | human-readable timeline |
| `strategy.md` | Stage 2 strategy report |
| `merge-report.html` | full-view mirror |
| `merge-report.js` | (optional, when split) |
| `patches/` | copies of input .patch / .diff files |
```

- [ ] **Step 2: Verify JSON schema present**

Run:
```bash
grep -E '"version"|"task_name"|"mode"|"status"|"decisions"' /Users/dalwin/Documents/AI/skills/git-merge-conductor/references/state-schema.md | wc -l
```
Expected: ≥ 5.

- [ ] **Step 3: Commit**

```bash
cd /Users/dalwin/Documents/AI
git add skills/git-merge-conductor/references/state-schema.md
git commit -m "feat(git-merge-conductor): add state.json schema reference"
```

---

## Task 8: Write references/recovery-protocol.md

**Files:**
- Modify: `skills/git-merge-conductor/references/recovery-protocol.md`

**Content source:** Spec §6.6 verbatim (English).

- [ ] **Step 1: Write recovery-protocol.md content**

```markdown
# Recovery Protocol

> Internal reference for SKILL.md failure / pause / abort / resume handling.

## Recovery Scenarios

<copy spec §6.6 scenario table verbatim, all 7 rows: session interrupted, git
command failure, [p] pause, [a] abort, model error, force-pushed source,
existing same-name branch>

## Resume Flow

1. Read `state.json`
2. Reconstruct in-memory context (mode, decisions list, current decision queue position)
3. Verify git state matches expected:
   - Working branch exists
   - Last `before-step-N` tag exists
   - `source.sha` resolvable
4. If verification fails → fall back to "manual intervention required" with diagnostic info dump
5. Else → resume from `stage` field

## Cleanup Runs

On every skill invocation: scan `.git/merge-conductor/*/` for `status: finalized`
with `finalized_at > 7d ago` → delete according to `cleanup_policy`.

Cleanup policies:
- `default-7d`: delete state dir + backup tags after 7 days
- `last-N`: keep most recent N finalized merges
- `permanent`: never auto-clean
- `manual`: never auto-clean, print cleanup commands at wrap-up
```

- [ ] **Step 2: Verify scenarios table present**

Run:
```bash
grep "Session interrupted\|Git command failure\|Force-pushed" /Users/dalwin/Documents/AI/skills/git-merge-conductor/references/recovery-protocol.md | wc -l
```
Expected: ≥ 3 (key scenarios present).

- [ ] **Step 3: Commit**

```bash
cd /Users/dalwin/Documents/AI
git add skills/git-merge-conductor/references/recovery-protocol.md
git commit -m "feat(git-merge-conductor): add recovery protocol reference"
```

---

## Task 9: Write templates/strategy-report.md

**Files:**
- Modify: `skills/git-merge-conductor/templates/strategy-report.md`

**Content source:** Spec §5.2 template body (Chinese visible text + English placeholders).

- [ ] **Step 1: Write strategy-report.md content**

The file starts with an English usage comment header, then the Chinese template body:

```markdown
<!--
Template: strategy-report.md
Used by: SKILL.md Stage 2 (Mode Inference + Strategy Report gate)
Output: rendered to terminal + written to .git/merge-conductor/{task}/strategy.md
Placeholders use {{var_name}} (English); fixed text is Chinese (user-facing).
-->

# 合并策略报告 — {{task_name}}

## 形态推断
- 推断结果：**{{mode}}**
- 依据：
  - {{signal_1}}
  - {{signal_2}}
- 不确定度：{{confidence}}（低/中/高）{{alternatives_if_low_confidence}}

## 分支双侧
- 源：{{source_ref}}（HEAD={{source_sha}}，与 target 的 merge-base={{merge_base_sha}}）
- 目标：{{target_ref}}（HEAD={{target_head_sha}}）
- 工作分支：merge/{{task_name}}（基于 {{base_sha}}）

## 影响范围分类
| 文件 | 源侧 +/- | 目标侧 +/- | 相关性 |
|---|---|---|---|
{{impact_table_rows}}

## 预估冲突分布
- A 类（自动 take target）：~{{A_estimate}} 处
- B 类（自动 take source）：~{{B_estimate}} 处
- C 类（需人决断）：~{{C_estimate}} 处
- D 类（标注后人决）：~{{D_estimate}} 处

## 计划执行命令链
{{command_chain_numbered}}

## 你需要确认 / 可调整
- [ ] mode 推断对吗？
- [ ] 工作分支名 / 基准 commit OK 吗？
- [ ] 是否允许"语义辅助映射"（Stage 5.5）？默认开启
- [ ] commit 粒度偏好：保留源 commits / squash 单 commit / 按主题重组
- [ ] 锁定 take target 或 take source 的特定文件？（如"lock 文件统一 take target"）

请回复「策略 OK」或具体调整意见。
```

- [ ] **Step 2: Verify Chinese sections present**

Run:
```bash
grep "形态推断\|分支双侧\|影响范围分类\|预估冲突分布\|计划执行命令链\|你需要确认" /Users/dalwin/Documents/AI/skills/git-merge-conductor/templates/strategy-report.md | wc -l
```
Expected: 6.

- [ ] **Step 3: Commit**

```bash
cd /Users/dalwin/Documents/AI
git add skills/git-merge-conductor/templates/strategy-report.md
git commit -m "feat(git-merge-conductor): add strategy-report template"
```

---

## Task 10: Write templates/decision-point.md

**Files:**
- Modify: `skills/git-merge-conductor/templates/decision-point.md`

**Content source:** Spec §5.4 template body (Chinese, 5 candidate options).

- [ ] **Step 1: Write decision-point.md content**

```markdown
<!--
Template: decision-point.md
Used by: SKILL.md Stage 6 (Decision Point Loop)
Output: rendered to terminal + appended as <article> to merge-report.html
Placeholders use {{var_name}} (English); fixed text is Chinese (user-facing).
Optional sections: "▼ 语义映射依据" only when Stage 5.5 ran for this hunk.
-->

─────────────────────────────────────────────
决策点 [{{idx}} / {{total}}]：{{file_path}}::{{symbol_name}}
分类：{{class}} 类（{{class_reason}}）

▼ 源侧改动（{{source_ref}} @ {{source_sha}}）
{{source_diff_hunk}}

▼ 目标侧改动（{{target_ref}} @ {{target_sha}}）
{{target_diff_hunk}}

▼ 模型分析
- 源侧意图：{{source_intent}}
- 目标侧意图：{{target_intent}}
- 冲突点：{{conflict_summary}}
- 是否相互独立：{{independence_assessment}}
- 语义映射：{{semantic_mapping_summary_or_none}}

{{#if has_semantic_mapping}}
▼ 语义映射依据
- 源侧改动 `{{source_symbol}}`
- 目标侧已被重构：方法迁移到 `{{mapped_to}}`（commit {{rename_commit_sha}}）
- 映射置信度：{{mapping_confidence}}（{{mapping_evidence}}）
- 候选方案 [3]/[4] 已基于映射重写到 `{{mapped_to}}` 位置
{{/if}}

▼ 候选方案
[1] take source：仅保留源侧改动
[2] take target：仅保留目标侧改动
[3] source-first-then-target：先保留源侧，后合并目标
[4] target-first-then-source：先保留目标侧，后合并源侧
[5] 自由输入：用一句话描述你的合并意图，模型解析后回显「我理解为...」请你二次确认

▼ 模型建议：[{{recommended_option}}]
依据：{{recommendation_reason}}

回复 1/2/3/4/5（5 为自由文本）
其它指令：[s] 跳过本点暂存到末尾  [p] 暂停退出（下次可恢复）  [a] 中止整个合并
─────────────────────────────────────────────
```

- [ ] **Step 2: Verify all 5 candidate options present**

Run:
```bash
grep -E "^\[1\]|^\[2\]|^\[3\]|^\[4\]|^\[5\]" /Users/dalwin/Documents/AI/skills/git-merge-conductor/templates/decision-point.md | wc -l
```
Expected: 5.

- [ ] **Step 3: Verify exit commands present**

Run:
```bash
grep "\[s\].*跳过\|\[p\].*暂停\|\[a\].*中止" /Users/dalwin/Documents/AI/skills/git-merge-conductor/templates/decision-point.md
```
Expected: at least one match showing all three exit commands.

- [ ] **Step 4: Commit**

```bash
cd /Users/dalwin/Documents/AI
git add skills/git-merge-conductor/templates/decision-point.md
git commit -m "feat(git-merge-conductor): add decision-point template with 5 candidate options"
```

---

## Task 11: Write templates/commit-message.md

**Files:**
- Modify: `skills/git-merge-conductor/templates/commit-message.md`

**Content source:** Spec §5.5 (`merge:` prefix + Chinese fields).

- [ ] **Step 1: Write commit-message.md content**

```markdown
<!--
Template: commit-message.md
Used by: SKILL.md Stage 7 (Finalization & Commit)
Output: passed as -m argument to git commit (multi-line via heredoc)
Placeholders use {{var_name}} (English); fixed text is Chinese (user-facing).
Required prefix: `merge:` (per user rule 5).
-->

merge: {{summary_chinese}}

源: {{source_ref}}@{{source_sha}}
mode: {{inferred_mode}}
决策摘要:
{{#each decisions}}
- [{{file_path}}::{{symbol_name}} #{{idx}}] {{choice_label}}：{{decision_brief_chinese}}
{{/each}}
A 类自动处理: {{A_count}} 处（详见 .git/merge-conductor/{{task_name}}/decision-log.md）
```

For multi-commit modes (cherry-pick-set / backport): each commit gets its own
rendering of this template, with `{{summary_chinese}}` rewritten from the source
commit's subject line.

- [ ] **Step 2: Verify `merge:` prefix and Chinese fields**

Run:
```bash
head -1 /Users/dalwin/Documents/AI/skills/git-merge-conductor/templates/commit-message.md
grep "^merge:\|^源:\|^mode:\|^决策摘要:\|^A 类自动处理:" /Users/dalwin/Documents/AI/skills/git-merge-conductor/templates/commit-message.md | wc -l
```
Expected: ≥ 5.

- [ ] **Step 3: Commit**

```bash
cd /Users/dalwin/Documents/AI
git add skills/git-merge-conductor/templates/commit-message.md
git commit -m "feat(git-merge-conductor): add commit-message template with merge: prefix"
```

---

## Task 12: Write templates/wrap-up-report.md

**Files:**
- Modify: `skills/git-merge-conductor/templates/wrap-up-report.md`

**Content source:** Spec §5.6 (Chinese, 4 cleanup options).

- [ ] **Step 1: Write wrap-up-report.md content**

```markdown
<!--
Template: wrap-up-report.md
Used by: SKILL.md Stage 8 (Wrap-up)
Output: rendered to terminal as final summary.
Placeholders use {{var_name}} (English); fixed text is Chinese (user-facing).
Required: present 4 cleanup options (per spec §5.6).
-->

# 合并完成 — {{task_name}}

## 概要
- 形态：{{mode}}
- 工作分支：merge/{{task_name}}（HEAD = {{final_sha}}）
- 决策点：{{resolved_count}}/{{total_count}} 已解决，{{skipped_count}} 跳过
- 自动处理：A 类 {{A_count}} 处，B 类 {{B_count}} 处

## 决策亮点
{{top_5_decisions_summary}}

## 报告位置
- 全貌 HTML（可浏览器打开）：`{{repo_root}}/.git/merge-conductor/{{task_name}}/merge-report.html`
- 决策日志（人读）：`{{repo_root}}/.git/merge-conductor/{{task_name}}/decision-log.md`
- 机器状态：`{{repo_root}}/.git/merge-conductor/{{task_name}}/state.json`

## 下一步建议
1. 复核：`git diff {{target_branch}}..merge/{{task_name}}`
2. 在 JetBrains / VSCode 里打开工作分支做事后可视化检查
3. 满意后合并：`git checkout {{target_branch}} && git merge merge/{{task_name}}`
4. 推送 / 开 PR 按团队规范自决

## 清理建议（满意后）
本次合并产生的可清理资产：
- 工作分支：`merge/{{task_name}}`
- 状态目录：`.git/merge-conductor/{{task_name}}/`（含 HTML 报告 / state.json / decision-log）
- backup tags：`merge/{{task_name}}/before-step-*` 共 {{tag_count}} 个
- final tag：`merge/{{task_name}}/done`

请选择清理策略：
[1] 默认：backup tags 保留 7 天后自动清理（运行 skill 时检查并清理过期 tag）
[2] 按 commit 次数：保留最近 N 次合并的状态与 tags（请指定 N）
[3] 永久保留：什么都不清理，全部留档
[4] 手动决定：现在告诉你清理命令，由你自己决定何时跑

选 [1] 后，本次清理仅清理超过 7 天的旧合并；本次合并资产将在 {{cleanup_due_date}} 后被清理。
```

- [ ] **Step 2: Verify 4 cleanup options present**

Run:
```bash
grep -E "^\[1\] 默认|^\[2\] 按 commit|^\[3\] 永久保留|^\[4\] 手动决定" /Users/dalwin/Documents/AI/skills/git-merge-conductor/templates/wrap-up-report.md | wc -l
```
Expected: 4.

- [ ] **Step 3: Commit**

```bash
cd /Users/dalwin/Documents/AI
git add skills/git-merge-conductor/templates/wrap-up-report.md
git commit -m "feat(git-merge-conductor): add wrap-up-report template with 4 cleanup options"
```

---

## Task 13: Create Verification Fixture (Toy Repo Setup)

**Files:**
- Create: `docs/superpowers/verification/git-merge-conductor/README.md`
- Create: `docs/superpowers/verification/git-merge-conductor/setup-fixture.sh`

This task creates a reusable toy repo construction script for the 5 verification scenarios.

- [ ] **Step 1: Create verification directory**

```bash
mkdir -p /Users/dalwin/Documents/AI/docs/superpowers/verification/git-merge-conductor/scenarios
```

- [ ] **Step 2: Write setup-fixture.sh**

Create `/Users/dalwin/Documents/AI/docs/superpowers/verification/git-merge-conductor/setup-fixture.sh`:

```bash
#!/usr/bin/env bash
# setup-fixture.sh — build the toy repo used by all 5 verification scenarios.
# Per spec §14.1.
#
# Usage: ./setup-fixture.sh /tmp/merge-conductor-fixture
set -euo pipefail

DEST="${1:-/tmp/merge-conductor-fixture}"
rm -rf "$DEST"
mkdir -p "$DEST"
cd "$DEST"

git init -q -b main
git config user.email "fixture@local"
git config user.name "Fixture"

# Initial OrderService on main
mkdir -p src/service
cat > src/service/OrderService.java <<'JAVA'
package service;
import java.math.BigDecimal;
public class OrderService {
    private static final BigDecimal RATE = new BigDecimal("0.1");
    public BigDecimal calcDiscount(Order order) {
        BigDecimal base = order.getAmount().multiply(RATE);
        return base;
    }
}
JAVA
git add .
git commit -q -m "init: OrderService"

# Branch develop from main
git branch develop

# Branch release/v1.0 from main (deployed branch)
git branch release/v1.0

# On release/v1.0: add VIP_BONUS feature
git checkout -q release/v1.0
cat > src/service/OrderService.java <<'JAVA'
package service;
import java.math.BigDecimal;
public class OrderService {
    private static final BigDecimal RATE = new BigDecimal("0.1");
    private static final BigDecimal VIP_BONUS = new BigDecimal("100");
    public BigDecimal calcDiscount(Order order) {
        BigDecimal base = order.getAmount().multiply(RATE);
        if (order.isVip()) {
            base = base.add(VIP_BONUS);
        }
        return base;
    }
}
JAVA
git add .
git commit -q -m "feat: add VIP_BONUS to calcDiscount"

# On develop: add coupon discount
git checkout -q develop
cat > src/service/OrderService.java <<'JAVA'
package service;
import java.math.BigDecimal;
public class OrderService {
    private static final BigDecimal RATE = new BigDecimal("0.1");
    private CouponService couponService;
    public BigDecimal calcDiscount(Order order) {
        BigDecimal base = order.getAmount().multiply(RATE);
        Coupon c = couponService.find(order.getUserId());
        if (c != null) base = base.subtract(c.value);
        return base;
    }
}
JAVA
git add .
git commit -q -m "feat: apply coupon to calcDiscount"

# Branch refactor/v2.0 from develop, rename calcDiscount → DiscountStrategy.apply
git checkout -q -b refactor/v2.0 develop
mkdir -p src/strategy
cat > src/strategy/DiscountStrategy.java <<'JAVA'
package strategy;
import java.math.BigDecimal;
public class DiscountStrategy {
    private static final BigDecimal RATE = new BigDecimal("0.1");
    private CouponService couponService;
    public BigDecimal apply(Order order) {
        BigDecimal base = order.getAmount().multiply(RATE);
        Coupon c = couponService.find(order.getUserId());
        if (c != null) base = base.subtract(c.value);
        return base;
    }
}
JAVA
git rm -q src/service/OrderService.java
git add .
git commit -q -m "refactor: rename OrderService.calcDiscount → DiscountStrategy.apply"

# Branch feature/promo-v2 from develop (older base), add VIP_BONUS
git checkout -q -b feature/promo-v2 develop~0
cat > src/service/OrderService.java <<'JAVA'
package service;
import java.math.BigDecimal;
public class OrderService {
    private static final BigDecimal RATE = new BigDecimal("0.1");
    private static final BigDecimal VIP_BONUS = new BigDecimal("100");
    private CouponService couponService;
    public BigDecimal calcDiscount(Order order) {
        BigDecimal base = order.getAmount().multiply(RATE);
        if (order.isVip()) {
            base = base.add(VIP_BONUS);
        }
        Coupon c = couponService.find(order.getUserId());
        if (c != null) base = base.subtract(c.value);
        return base;
    }
}
JAVA
git add .
git commit -q -m "feat: VIP promo on feature branch"

# Back to develop
git checkout -q develop

echo "Fixture ready at $DEST"
echo "Branches: $(git -C "$DEST" branch | tr '\n' ' ')"
```

- [ ] **Step 3: Make script executable + smoke-test it**

```bash
chmod +x /Users/dalwin/Documents/AI/docs/superpowers/verification/git-merge-conductor/setup-fixture.sh
/Users/dalwin/Documents/AI/docs/superpowers/verification/git-merge-conductor/setup-fixture.sh /tmp/merge-conductor-fixture-smoke
cd /tmp/merge-conductor-fixture-smoke
git branch
```
Expected output: branches `main`, `develop`, `release/v1.0`, `refactor/v2.0`, `feature/promo-v2` all present.

- [ ] **Step 4: Write verification README**

Create `/Users/dalwin/Documents/AI/docs/superpowers/verification/git-merge-conductor/README.md`:

```markdown
# Git Merge Conductor Verification

How to verify the skill works against the 5 acceptance scenarios from
spec §9.1.

## Setup

```bash
./setup-fixture.sh /tmp/merge-conductor-fixture
cd /tmp/merge-conductor-fixture
```

## Scenarios

Each scenario lives in `scenarios/`:

| File | Scenario |
|---|---|
| `A-forward-integrate.md` | feature → dev with hotfix during development |
| `B-backport.md` | Cross-version backport with refactor |
| `C-patch-apply.md` | Pure patch-apply |
| `D-interrupt-resume.md` | Interrupt at Stage 6 and resume |
| `E-guard.md` | Stage 0 guard with dirty work tree |

Each scenario file documents:
- Setup steps (on top of the toy fixture)
- The user prompt to feed the skill
- Expected observable outputs (commit message regex, state.json shape, HTML elements)
- Pass / fail criteria
```

- [ ] **Step 5: Clean smoke-test fixture and commit**

```bash
rm -rf /tmp/merge-conductor-fixture-smoke
cd /Users/dalwin/Documents/AI
git add docs/superpowers/verification/git-merge-conductor/
git commit -m "feat(git-merge-conductor): add toy fixture setup script"
```

---

## Task 14: Document 5 Verification Scenarios

**Files:**
- Create: `docs/superpowers/verification/git-merge-conductor/scenarios/A-forward-integrate.md`
- Create: `docs/superpowers/verification/git-merge-conductor/scenarios/B-backport.md`
- Create: `docs/superpowers/verification/git-merge-conductor/scenarios/C-patch-apply.md`
- Create: `docs/superpowers/verification/git-merge-conductor/scenarios/D-interrupt-resume.md`
- Create: `docs/superpowers/verification/git-merge-conductor/scenarios/E-guard.md`

Each scenario doc follows the same shape: Setup → Prompt → Expected → Pass/Fail.

- [ ] **Step 1: Write scenario A — forward-integrate**

Create `scenarios/A-forward-integrate.md`:

```markdown
# Scenario A: Forward-Integrate (feature → dev + hotfix)

Maps to spec §9.1 scenario A.

## Setup

```bash
./setup-fixture.sh /tmp/merge-conductor-fixture
cd /tmp/merge-conductor-fixture
git checkout develop
```

Fixture state: `feature/promo-v2` has VIP_BONUS + coupon both; `develop` has only
coupon. We simulate that `feature/promo-v2` was branched before coupon landed,
so the merge should integrate coupon (from dev) into the feature's logic.

## Prompt

> 帮我把 feature/promo-v2 合并到 develop。feature 期间 develop 也修改了 calcDiscount
> 加入了优惠券逻辑，希望最终包含 VIP 加成 + 优惠券。

## Expected

- Stage 0 guard passes (clean work tree)
- Stage 2 strategy report: `mode: forward-integrate`, confidence high or medium
- Stage 6: 1+ C-class decision point on `OrderService.calcDiscount`
- Final commit: `merge: ...` (Chinese), includes both VIP_BONUS and coupon logic
- Working branch `merge/promo-v2-to-develop` exists
- `develop` branch HEAD unchanged
- `.git/merge-conductor/promo-v2-to-develop/state.json` exists with `status: finalized`

## Pass / Fail

Pass criteria (all must hold):
- [ ] `git log merge/promo-v2-to-develop -1 --pretty=%s` matches `^merge: `
- [ ] `git show merge/promo-v2-to-develop:src/service/OrderService.java` contains both `VIP_BONUS` and `couponService`
- [ ] `git rev-parse develop` unchanged from pre-merge value
- [ ] `merge-report.html` opens in browser; has `<article class="decision ... resolved">` for `calcDiscount`
```

- [ ] **Step 2: Write scenario B — backport**

Create `scenarios/B-backport.md`:

```markdown
# Scenario B: Cross-Version Backport with Refactor

Maps to spec §9.1 scenario B.

## Setup

```bash
./setup-fixture.sh /tmp/merge-conductor-fixture
cd /tmp/merge-conductor-fixture
git checkout refactor/v2.0
```

Fixture state: `release/v1.0` has VIP_BONUS in `OrderService.calcDiscount`.
`refactor/v2.0` renamed `OrderService.calcDiscount` → `DiscountStrategy.apply`.
We backport VIP_BONUS into the refactored target.

## Prompt

> 把 release/v1.0 上的 VIP_BONUS 功能回灌到 refactor/v2.0。注意目标分支重构了，
> calcDiscount 已经迁移到 DiscountStrategy.apply。

## Expected

- Stage 2 strategy report: `mode: backport`, `refactor_signals_in_target: true`
- Stage 5.5 (semantic mapping) runs: maps `OrderService.calcDiscount` → `DiscountStrategy.apply` with confidence high or medium
- Stage 6: decision point shows the mapped suggestion in candidate [3] / [4]
- Final commit message preserves source SHA reference + `merge: 中文`
- Working branch `merge/vip-bonus-backport` has VIP_BONUS code applied inside `DiscountStrategy.apply`

## Pass / Fail

- [ ] `git show merge/vip-bonus-backport:src/strategy/DiscountStrategy.java` contains `VIP_BONUS`
- [ ] state.json `decisions[*].semantic_mapping.confidence` is set for at least one decision
- [ ] Commit message regex `^merge: .+`
- [ ] `git rev-parse refactor/v2.0` unchanged
```

- [ ] **Step 3: Write scenario C — patch-apply**

Create `scenarios/C-patch-apply.md`:

```markdown
# Scenario C: Pure patch-apply

Maps to spec §9.1 scenario C.

## Setup

```bash
./setup-fixture.sh /tmp/merge-conductor-fixture
cd /tmp/merge-conductor-fixture
# Generate a patch from release/v1.0's VIP_BONUS commit
git format-patch release/v1.0~1..release/v1.0 -o /tmp/patches
ls /tmp/patches  # Expect: 0001-feat-add-VIP_BONUS....patch
git checkout develop
```

## Prompt

> 把这个 patch 应用到当前 develop 分支：/tmp/patches/0001-feat-add-VIP_BONUS-to-calcDiscount.patch

## Expected

- Stage 2 strategy report: `mode: patch-apply`
- Stage 4 uses `git am --3way` (or `git apply --3way`)
- Conflict expected on `calcDiscount` (develop already has coupon logic)
- Stage 6 decision point appears
- Final commit message `merge: ...`

## Pass / Fail

- [ ] state.json `mode == "patch-apply"`
- [ ] At least one C-class decision in `decisions[]`
- [ ] Working branch has merged code (VIP_BONUS + coupon)
- [ ] `merge-report.html` exists
```

- [ ] **Step 4: Write scenario D — interrupt and resume**

Create `scenarios/D-interrupt-resume.md`:

```markdown
# Scenario D: Interrupt at Stage 6 and Resume

Maps to spec §9.1 scenario D.

## Setup

Same as scenario A (forward-integrate setup). Begin the merge normally.

## Prompt (run 1)

> 帮我把 feature/promo-v2 合并到 develop。

When the skill reaches Stage 6 and presents the first decision point:

> [p]

The skill should pause gracefully.

## Prompt (run 2 — new session)

> 检查是否有未完成的合并会话。

## Expected

After [p] pause:
- state.json `status == "paused"`
- state.json `paused_at` is set
- state.json `stage == 6`
- decision-log.md has entry "用户暂停于决策点 N"

After resume prompt:
- Skill detects existing session and prompts: 「检测到未完成会话 (task=X, paused at stage=6)」
- User selects "恢复"; skill resumes from the next pending decision

## Pass / Fail

- [ ] After pause: `cat .git/merge-conductor/*/state.json | grep '"status": "paused"'` matches
- [ ] After resume: `state.json` `status` becomes `in-progress`, then `finalized`
- [ ] Final commit message `merge: ...`
- [ ] No data loss between pause and resume (decisions array contiguous)
```

- [ ] **Step 5: Write scenario E — guard**

Create `scenarios/E-guard.md`:

```markdown
# Scenario E: Stage 0 Guard with Dirty Work Tree

Maps to spec §9.1 scenario E.

## Setup

```bash
./setup-fixture.sh /tmp/merge-conductor-fixture
cd /tmp/merge-conductor-fixture
git checkout develop
echo "uncommitted change" >> src/service/OrderService.java
```

Work tree is now dirty.

## Prompt

> 帮我把 feature/promo-v2 合并到 develop。

## Expected

- Stage 0 detects dirty work tree
- Skill stops and prompts (中文): 「检测到未提交改动，先 stash / 先 commit / 取消？」
- No working branch created
- No state.json written
- No `before-step-N` tags created

## Pass / Fail

- [ ] No new branch starts with `merge/`
- [ ] `.git/merge-conductor/` directory not created (or empty)
- [ ] Skill response includes the 3 options stash/commit/取消 in Chinese
- [ ] git status still shows the uncommitted modification (skill didn't touch it)
```

- [ ] **Step 6: Commit all 5 scenarios**

```bash
cd /Users/dalwin/Documents/AI
git add docs/superpowers/verification/git-merge-conductor/scenarios/
git commit -m "feat(git-merge-conductor): add 5 acceptance scenario specs"
```

---

## Task 15: Run Skill Through Scenario A (Smoke Test)

This task is the end-to-end smoke test. It exercises the freshly built skill
against scenario A and confirms the formal contract holds.

**Files:**
- No file changes; this task is verification only.

- [ ] **Step 1: Build the fixture**

```bash
/Users/dalwin/Documents/AI/docs/superpowers/verification/git-merge-conductor/setup-fixture.sh /tmp/merge-conductor-fixture
cd /tmp/merge-conductor-fixture
git checkout develop
```
Expected: clean dev branch with `OrderService.java` containing only coupon logic.

- [ ] **Step 2: Invoke the skill**

In a Claude Code (or Codex) session targeting `/tmp/merge-conductor-fixture`, paste:

> 帮我把 feature/promo-v2 合并到 develop。feature 期间 develop 也修改了 calcDiscount 加入了优惠券逻辑，希望最终包含 VIP 加成 + 优惠券。

The skill should:
1. Stage 0: confirm clean repo, list branches in 中文.
2. Stage 1: echo task spec yaml in 中文.
3. Stage 2: emit strategy report (中文); user confirms with 「策略 OK」.
4. Stage 3: create `merge/promo-v2-to-develop`.
5. Stages 4-5: apply source, classify A/B/C/D.
6. Stage 6: present at least one C-class decision on `calcDiscount`; user picks `3` (source-first-then-target).
7. Stage 7: commit with `merge: ...` in Chinese.
8. Stage 8: print wrap-up report with 4 cleanup options.

- [ ] **Step 3: Verify formal contract**

After skill completes, run from `/tmp/merge-conductor-fixture`:

```bash
# 1. Working branch exists
git rev-parse --verify merge/promo-v2-to-develop

# 2. Commit message format
git log merge/promo-v2-to-develop -1 --pretty=%s | grep -E '^merge: '

# 3. Target branch unchanged
git rev-parse develop  # should equal the SHA before merge

# 4. State files exist
ls .git/merge-conductor/*/state.json
ls .git/merge-conductor/*/merge-report.html
ls .git/merge-conductor/*/decision-log.md
ls .git/merge-conductor/*/strategy.md

# 5. Backup tags exist
git tag | grep 'merge/promo-v2-to-develop/before-step'
git tag | grep 'merge/promo-v2-to-develop/done'

# 6. Final code has both VIP_BONUS and couponService
git show merge/promo-v2-to-develop:src/service/OrderService.java | grep -E 'VIP_BONUS|couponService'

# 7. HTML opens (visual inspection)
open .git/merge-conductor/*/merge-report.html  # macOS; or: xdg-open on Linux
```
Expected: all greps return matches; tag list non-empty; HTML opens with strategy + decisions sections visible.

- [ ] **Step 4: If any contract fails, iterate**

If a contract fails:
- Inspect `.git/merge-conductor/*/decision-log.md` to see where the skill diverged.
- Identify which Stage / reference / template needs adjustment.
- Edit the corresponding file in `skills/git-merge-conductor/`.
- Reset the fixture (`rm -rf /tmp/merge-conductor-fixture`) and re-run from Step 1.
- Commit the fix:
  ```bash
  cd /Users/dalwin/Documents/AI
  git add skills/git-merge-conductor/<changed-file>
  git commit -m "fix(git-merge-conductor): <one-line fix description>"
  ```

- [ ] **Step 5: Document the smoke-test pass**

After contract passes, write a brief verification note:

```bash
cat > /Users/dalwin/Documents/AI/docs/superpowers/verification/git-merge-conductor/SMOKE-TEST.md <<EOF
# Smoke Test Result — Scenario A

Date: $(date -u +%Y-%m-%d)
Skill version: v1
Fixture: /tmp/merge-conductor-fixture

## Result
PASS — all 7 contract checks satisfied.

## Notes
<paste any noteworthy observations from the run>
EOF

cd /Users/dalwin/Documents/AI
git add docs/superpowers/verification/git-merge-conductor/SMOKE-TEST.md
git commit -m "feat(git-merge-conductor): record scenario A smoke-test pass"
```

---

## Task 16: Final Wrap-up

**Files:**
- Modify: skill itself if any tuning is needed after scenarios A-E full run

- [ ] **Step 1: Run scenarios B-E**

Repeat the smoke-test pattern from Task 15 for scenarios B, C, D, E.
For each:
1. Reset fixture.
2. Invoke skill with scenario's prompt.
3. Verify pass criteria from the scenario doc.
4. If fail → fix skill → re-run.

- [ ] **Step 2: Update SMOKE-TEST.md with all 5 scenario results**

```bash
cd /Users/dalwin/Documents/AI
# Edit docs/superpowers/verification/git-merge-conductor/SMOKE-TEST.md to add B/C/D/E results
git add docs/superpowers/verification/git-merge-conductor/SMOKE-TEST.md
git commit -m "feat(git-merge-conductor): all 5 acceptance scenarios pass"
```

- [ ] **Step 3: Final repository state check**

```bash
cd /Users/dalwin/Documents/AI
find skills/git-merge-conductor -type f | sort
find docs/superpowers/verification/git-merge-conductor -type f | sort
```
Expected: 11 files under `skills/git-merge-conductor/`; 7+ files under verification dir (README + setup-fixture.sh + 5 scenarios + SMOKE-TEST.md).

- [ ] **Step 4: Tag v1 release**

```bash
cd /Users/dalwin/Documents/AI
git tag git-merge-conductor-v1
git log --oneline -20  # Sanity check: ~16 commits with feat(git-merge-conductor) prefix
```

---

## Plan Self-Review

**1. Spec coverage:** Skim spec §1-§14:
- §1 overview → Task 2 frontmatter
- §4 architecture → Task 2 SKILL.md body
- §5 stage contracts → Task 2 SKILL.md body
- §6.1-6.6 references → Tasks 3-8
- §7 templates → Tasks 9-12
- §8 failure/recovery → Task 8 (recovery-protocol) + Task 2 (SKILL.md)
- §9 acceptance → Tasks 13-16 (fixture + scenarios + smoke tests)
- §10 boundaries → Task 2 (SKILL.md non-goals section)
- §11 evolution → Out of scope (v2)
- §12 file structure → Task 1 scaffold
- §13 language convention → Implicit in each task's language requirement + Task 2 final section
- §14 testing → Tasks 13-16

All covered.

**2. Placeholder scan:** No TBDs, no "see Task X for code" without code, no "add appropriate error handling" without specifics. Every step has an exact command or exact content reference.

**3. Type consistency:**
- Skill name `git-merge-conductor` — consistent throughout
- Working branch pattern `merge/<task-name>` — consistent
- State path `.git/merge-conductor/<task>/` — consistent
- Commit prefix `merge:` (skill output) vs `feat(git-merge-conductor):` (plan tasks) — distinct, no collision
- Template placeholders use `{{var_name}}` (English) — consistent
- 5 candidate options indexed 1-5 — consistent across decision-point template and SKILL.md Stage 6

Plan complete.
