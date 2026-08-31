---
name: git-merge-conductor
description: "Use when plain git cannot cleanly complete a complex merge, backport, or patch-apply task and the user explicitly invokes this skill."
---

# Git Merge Conductor

You orchestrate complex git merges end-to-end via a guarded multi-stage pipeline. Your job is to be a merge *strategist* who also executes the safe parts: classify conflicts, auto-resolve the trivial ones, and surface the hard ones to the user only at the final gate. You are not a better merge UI — the user can open JetBrains/VSCode later for visual review.

## Safety Invariants (Read First, Never Violate)

These hold for every invocation. Violating any of these breaks user trust irreversibly.

1. **The target branch is never modified.** All writes happen on a new working branch named `merge/<task-name>`. The user decides later (outside this skill) how to integrate the working branch back to target.
2. **Every stage takes a backup tag before doing destructive work.** Tag format: `merge/<task>/before-step-N`. The user can `git reset --hard <tag>` to recover from any stage.
3. **Runtime state lives in `<repo>/.git/merge-conductor/<task>/`.** This is inside `.git/` (never committed, never appears in `git status`). The user can `rm -rf` it at any time.
4. **No automatic push, no automatic PR.** The skill stops at a local working branch with a clean commit history. Push/PR is the user's call.
5. **The user can `[p]` pause or `[a]` abort at any decision point.** Pause saves state for later resume. Abort rolls back to a clean state.
6. **No change outside `requirements.yaml`.** 任何 graft / hunk 改动的文件不在
   `requirements.yaml::items[*].target_locations` 内即触发硬性 rollback。
   若用户希望纳入，必须先在 Stage 2 升级 `requirements.yaml` 加 item
   （回到 Stage 2 ★ Gate ★ 重审）。检测信号与后置见
   `references/negative-constraints.md#NC-05`.
7. **Stage transitions must persist before continuing.** Writing
   `state.json::stage = next` and appending to `state.json::stage_history`
   is a hard precondition for entering the next stage. If `state.json` write
   fails, halt the pipeline and report to the user — never proceed in memory only.
   Resume correctness depends on this: no stage may be skipped silently.

## Language Convention

- **User-facing terminal output** (progress, prompts, reports): Chinese
- **Internal prompts, rules, schemas** (this file + references/): English
- **Templates** (assets/*.md): Chinese fixed text + English placeholders (`{{var_name}}`)
- **Commit messages**: `merge: <中文说明>` (see Stage 7)
- **HTML report visible text**: Chinese (`<html lang="zh-CN">`)

## Pipeline Overview

```
Stage 0   — Entry probe & guards (read-only)
Stage 1   — Input normalization
Stage 2   — Mode inference + requirements ★ USER GATE ★
Stage 3   — Working setup (worktree-delegated for complex modes)
Stage 4-6 — Mode-aware fork:
            conflict-pipeline   (4c → 5c → 6c)   autonomous
            transplant-pipeline (4t → 5t → 6t)   autonomous
Stage 6.5 — Per-unit negative-constraint self-audit
Stage 7   — Finalization & commit (status: pre-verified)
Stage 7.5 — Verification loop (Phase 1 auto-fix N≤3, Phase 2 ★ FINAL GATE ★)
Stage 8   — Wrap-up + cleanup options
```

### Stage Banner

On entering every Stage N, emit one banner before any other output — it is the
user's only inline visibility into pipeline state, and their cue to interrupt:

```
[Stage <N> · <Stage Name (English)> · iter <i> · tag: merge/<task>/before-step-<N>]
```

`<i>` = `state.json::iter` (Phase 2 loop counter). Stages with no `before-step` tag (0/1/2) use `tag: none`.

Persist state (`stage_history` append + `stage` bump) BEFORE the banner. State schema: `references/state-schema.md`.

## Stage Contracts

## Stage 0 — Entry Probe & Guards

**职责**：read-only 仓库环境检查；submodule/LFS/dirty 状态 → 询问或中止；
检测旧会话给出 resume/discard/show-only 选择。

**详细契约**：`references/contracts/setup-stages.md#stage-0`

## Stage 1 — Input Normalization

**职责**：三种输入形态（branch refs / patch-diff / 任务描述）归一化为
task spec；提取关键字、enumerate source commits、archive patch files。

**详细契约**：`references/contracts/setup-stages.md#stage-1`

## Stage 2 — Mode Inference, Strategy & Requirement Extraction ★ GATE ★

**职责**：判断 mode + 选 pipeline (conflict / transplant) + 提取
`requirements.yaml`（含 `scope_tag` + `out_of_scope` 每项）+ 产出策略报告。
后续所有写操作以此为基础。

**Hard gate**：用户未明确「策略 OK」前禁止任何写操作。

**详细契约**：`references/contracts/setup-stages.md#stage-2`
**决策依据**：`references/mode-inference.md`
**清单模板**：`assets/requirements.yaml`

## Stage 3 — Working Setup

**职责**：复杂 mode 委托 `using-git-worktrees` 创建 worktree（project-tier skill，见 [ADR-0018](../../../adr/0018-卸载superpowers插件与ask-first软约束.md)）；
简单 mode 主仓 checkout `merge/<task>`。.git/merge-conductor 数据仍在主仓
(metadata 主仓化)。

**详细契约**：`references/contracts/setup-stages.md#stage-3`

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
**模板**：`assets/grafting-plan.yaml`, `assets/draft.md`

Stage 6.5 (Negative-Constraint Self-Audit) is invoked per-unit at the end of each 6c hunk decision / 6t graft apply, not as a separate batch stage.

## Stage 6.5 — Negative-Constraint Self-Audit

**职责**：per-unit 即时 audit；命中 NC 规则或 `out_of_scope` → rollback +
标 partial/unresolved 进 Phase 2 报表。NC-05 (改动越界 `target_locations`)
对应 Safety Invariant 6 硬性 rollback。

**详细契约**：`references/contracts/audit-and-verify.md#stage-65`
**规则库**：`references/negative-constraints.md`
**模板**：`assets/audit-report.md`

## Stage 7 — Finalization & Commit

**职责**：按 `commit_granularity` 提交；commit message 含 iter 信息 +
rolled-back 项 + audit 摘要。tag `merge/<task>/done`。状态置 `pre-verified`，
NOT `finalized` (要等 Phase 2 通过)。

**详细契约**：`references/contracts/audit-and-verify.md#stage-7`
**模板**：`assets/commit-message.md`

## Stage 7.5 — Verification Loop

**Phase 1 (自动化)**：compile/lint/scope-test，失败 model 自修复 loop (N≤3)
后投降把错误带给用户。
**Phase 2 (用户兜底 ★ FINAL GATE ★)**：渲染需求清单 vs 已合并差异表 +
audit 拦截项；用户「完成 / REQ-X 没做对 / REQ-X 不该做 / 还多 Z」决定。
Phase 2 是 Stage 2 之外唯一 mid-pipeline 中断点。

**详细契约**：`references/contracts/audit-and-verify.md#stage-75`
**模板**：`assets/verification-report.md`

## Stage 8 — Wrap-up + Cleanup

**职责**：终端 + HTML 终态报告；4 个 cleanup 选项 + worktree 清理子选项；
status = finalized 持久化。

**详细契约**：`references/contracts/wrap-up.md#stage-8`
**模板**：`assets/wrap-up-report.md`

## Runtime Recovery

## Failure / Pause / Abort / Resume

See `references/recovery-protocol.md` for the full scenario matrix. Key guarantees:

- **Every stage has a `before-step-N` tag** — `git reset --hard <tag>` always recovers.
- **`state.json` is the source of truth** for resume. Scan `.git/merge-conductor/*/state.json` on invocation; for `status: in-progress | paused` prompt 「检测到未完成会话 (task=X, paused at stage=Y)，要恢复 / 丢弃重来 / 仅查看状态？」
- **Force-push detection**: verify `source.sha` reachable via `git rev-list` on resume; refuse if not.
- **Abort is destructive**: `[a]` triggers `git branch -D merge/<task>` + `rm -rf .git/merge-conductor/<task>`. Confirm in 中文 first.

## When NOT to Use This Skill

Decline + echo plain git for: fast-forward merge (`git merge --ff-only`),
single clean cherry-pick (`git cherry-pick <sha>`), or PR-style merge with
green CI. Tell the user 「这个场景用原生 git 命令就够了，不需要走 conductor」.

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

## Quick Sanity Checks

Two checks the pipeline cannot infer on its own — verify them, and stop and
report the inconsistency rather than proceeding if either fails:

- **Target branch unchanged** before any `git checkout -b`:
  `git rev-parse <target>` still matches the value captured in Stage 2.
- **Actual stage matches your mental model** before any user-facing output:
  read `state.json::stage`; a mismatch means state was lost or a stage was
  skipped — reconcile before continuing.
