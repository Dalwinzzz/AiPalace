# Recovery Protocol

> Internal reference for SKILL.md failure / pause / abort / resume handling.

## Core Principle

The pipeline is designed so that every stage is recoverable. Backup tags are
the unit of rollback; `state.json` is the source of truth for what was done
and what's pending.

The target branch is never touched, so the worst-case failure mode is "throw
away the working branch and start over" — the user's main branches are always
safe.

## Recovery Scenarios

| Scenario | Detection | Action |
|---|---|---|
| **Session interrupted** (terminal closed, model timed out, network glitch) | On next skill invocation, find `state.json` with `status: in-progress` and no recent file activity | Prompt (中文): 「检测到未完成会话 (task=X, paused at stage=Y)，要恢复 / 丢弃重来 / 仅查看状态？」 |
| **Git command failure mid-stage** | Non-zero exit code from a git operation | Roll back to most recent `before-step-N` tag (silently, no user prompt), then report the error to user (中文) and ask: 重试 / 调整策略后重试 / 中止 |
| **User typed `[p]` in Stage 6** | Inline command at a decision prompt | Save state with `status: paused`, `paused_at: now`, write summary to decision-log, exit cleanly with a message in 中文 explaining how to resume |
| **User typed `[a]` in Stage 6** | Inline command at a decision prompt | Confirm in 中文: 「将丢弃工作分支和状态目录，确定？」→ on yes: `git checkout <target> && git branch -D merge/<task> && rm -rf .git/merge-conductor/<task>`, also delete `merge/<task>/before-step-*` tags |
| **Model encounters unrecoverable error** | Internal exception or contradiction (e.g., state.json validation fails mid-write) | Save state with `status: error` + diagnostic info, print recovery instructions to user (中文), do NOT auto-rollback (preserves evidence for inspection) |
| **Force-pushed source branch during process** | On resume, `source.sha` no longer reachable via `git rev-list` | Refuse to resume; tell the user (中文): 「源分支历史已变更（可能被 force-push）。无法安全恢复。请丢弃当前工作分支并重新启动」 |
| **Existing same-name working branch at Stage 0** | Stage 0 guard finds `merge/<task>` exists | Prompt (中文): 「检测到同名 merge/<task> 分支，要恢复未完成会话 / 删除后重建 / 取消？」 |
| **Existing `.git/merge-conductor/<task>/` but no working branch** | State dir exists but branch doesn't (someone deleted it manually) | Prompt (中文): 「检测到孤立状态目录，工作分支不存在。要清理状态目录 / 取消？」 |

## Resume Flow

When user chooses "恢复" after detection:

1. Read `state.json` — load mode, decisions[], config, current stage
2. Reconstruct in-memory context:
   - Mode + config (from `state.json::config`)
   - Decision queue (filter `decisions[]` to `pending` + `skipped`)
   - Current decision index (next `pending` after the most recently resolved)
3. Verify git state matches expected:
   - `git rev-parse --verify <working_branch>` succeeds
   - `git tag` shows the expected `before-step-N` tags
   - `git rev-list --max-count=1 <source.sha>` succeeds (source still exists)
   - `git rev-parse <target.head_sha>` succeeds (target branch SHA still resolvable; note: target may have advanced past `head_sha`, that's OK — the working branch is based on `base_sha` regardless)
4. If verification fails → fall back to "manual intervention required" with diagnostic info dump. Do NOT attempt automatic repair.
5. If all verifications pass → set `status: in-progress`, clear `paused_at`, append "resumed at <now>" to decision-log, jump to the appropriate stage.

## Resume Entry Points by Stage

| Saved stage | Entry point |
|---|---|
| Stage 0-2 (before Stage 3 setup) | Restart from Stage 0 (no working branch exists yet) |
| Stage 3 mid | Roll back to `before-step-3`, restart Stage 3 |
| Stage 4 mid | Roll back to `before-step-4`, restart Stage 4 |
| Stage 5 mid (auto-resolving) | Roll back to `before-step-5`, restart Stage 5 |
| Stage 5.5 mid | Roll back to `before-step-5`, restart Stage 5 (which re-runs Stage 5.5 if applicable) |
| Stage 6 mid (paused at decision N) | Roll back to `before-step-6`, restart Stage 6, fast-forward by re-applying decisions[0..N-1] from state.json (their `choice` was saved), continue at decision N |
| Stage 7 mid | Roll back to `before-step-6`, restart Stage 7 |
| Stage 8 | Restart Stage 8 (idempotent — just re-render wrap-up) |

## Cleanup Runs

On every skill invocation, before doing anything else:

1. Scan `<repo>/.git/merge-conductor/*/state.json` for sessions with `status: finalized`
2. For each, check `cleanup_policy` and `finalized_at`:
   - `default-7d`: if `finalized_at > 7 days ago` → delete state dir + delete `merge/<task>/before-step-*` tags (keep `done` tag for traceability)
   - `last-N` (with `cleanup_last_n: 5`): sort by `finalized_at`, keep most recent 5, clean older
   - `permanent`: never clean
   - `manual`: never auto-clean

3. Report cleanup results to user (中文): 「已清理 N 个超期的合并状态目录」 (or skip if no cleanup happened)

Run cleanup BEFORE prompting about resume, so stale finalized sessions don't clutter the resume list.

## Diagnostic Info Dump

When refusing to resume due to verification failure, print:

- Path to `state.json`
- Stored `working_branch`, `source.sha`, `target.head_sha`
- Result of each verification check (pass/fail with git output)
- Suggested manual recovery commands

This gives the user enough info to recover manually or escalate.

## Abort Cleanup Order

When `[a]` is confirmed:

1. `git checkout <target_branch>` (move HEAD away from working branch)
2. `git branch -D merge/<task>` (delete working branch)
3. `for tag in $(git tag -l "merge/<task>/*"); do git tag -d $tag; done` (delete all backup tags)
4. `rm -rf <repo>/.git/merge-conductor/<task>/` (clear state dir)
5. Report to user (中文): 「已丢弃工作分支和状态目录。目标分支未被改动」

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
   - On "放弃": abort flow (same as `[a]`, see v2 Abort with worktree below)

### Abort with worktree

When `[a]` is confirmed and `state.json::working_branch.use_worktree == true`:

```bash
# inside main repo
git worktree remove --force <worktree_path>
git branch -D merge/<task>
for tag in $(git tag -l "merge/<task>/*"); do git tag -d "$tag"; done
rm -rf <repo>/.git/merge-conductor/<task>/
```

Confirm in 中文 before executing: 「确认 abort 会删除 worktree、merge/<task> 分支、
所有备份 tag、会话目录。确认？」

After cleanup, report to user (中文): 「abort 完成。worktree、分支、会话目录已清理。
主仓回到 abort 前状态。」

## v2 — Iteration Recovery Scenarios

### Resume mid-iter

1. Read `state.json::iter` and `state.json::iterations[<iter>]`.
2. If `iterations[<iter>].ended_at` is null:
   - Last iter was interrupted. Read `state.json::stage` for where to resume.
   - Verify the corresponding `merge/<task>/before-iter-<iter>` tag exists.
   - Resume from that stage.
3. If `iterations[<iter>].ended_at` is set:
   - That iter is fully closed. Next iter starts from `state.json::iter + 1`.

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
