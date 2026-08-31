# Scenario D: Interrupt at Stage 6 and Resume

Maps to spec §9.1 scenario D.

## Setup

Same as Scenario A. Begin the merge normally.

## Prompt (Run 1)

> 帮我把 feature/promo-v2 合并到 develop。feature 期间 develop 也修改了 calcDiscount 加入了优惠券逻辑。

When the skill reaches Stage 6 and presents the first decision point:

> [p]

The skill should pause gracefully and print resume instructions in Chinese.

## Prompt (Run 2, fresh session)

> 检查是否有未完成的合并会话。

## Expected Behavior

After `[p]` pause:
- `state.json` `status: paused`
- `state.json` `paused_at` is set to a timestamp
- `state.json` `stage: 6`
- `decision-log.md` has entry "用户暂停于决策点 N"
- Skill prints (中文): 「会话已暂停。下次启动 skill 时检测到该 task 即可恢复。」

After resume prompt:
- Skill scans `.git/merge-conductor/*/state.json`, finds the paused session
- Prompts (中文): 「检测到未完成会话 (task=X, paused at stage=6)，要恢复 / 丢弃重来 / 仅查看状态？」
- User: "恢复"
- Skill rolls back to `before-step-6`, fast-forwards by replaying resolved decisions (if any), continues at the pending decision

## Pass Criteria

```bash
TASK=$(ls .git/merge-conductor/ | head -1)

# After [p] pause:
grep -q '"status": "paused"' ".git/merge-conductor/$TASK/state.json" || echo "FAIL: not paused"
grep -q '"paused_at":' ".git/merge-conductor/$TASK/state.json" || echo "FAIL: no paused_at"

# After full resume + completion:
grep -q '"status": "finalized"' ".git/merge-conductor/$TASK/state.json" || echo "FAIL: not finalized after resume"
git log "merge/$TASK" -1 --pretty=%s | grep -E '^merge: ' || echo "FAIL: commit message format"

# Decisions array contiguous (no gaps)
# (manual JSON inspection of decisions[].id should be 1..N sequential)
```

## v2 sub-scenario: worktree resume

This sub-scenario verifies `references/recovery-protocol.md` v2 Worktree
Recovery Scenarios (resume + 3-option missing-worktree dialogue).

### Setup

Same as scenario F (backport-transplant fixture). Reuse `/tmp/gmc-fixture-F`
or rebuild via `setup-fixture.sh`.

### Steps

1. Start a session per scenario F (backport-transplant of `care-class`).
2. When pipeline reaches Stage 5t (Plan & Graft), send `[p]` pause.
3. Verify worktree path persisted in `state.json::working_branch.worktree_path`
   and `state.json::working_branch.use_worktree == true`.
4. End the Claude Code session entirely.
5. Optionally remove the worktree directory manually to simulate a corrupt
   workspace:
   ```bash
   rm -rf /tmp/gmc-fixture-F-worktrees/care-class-transplant
   ```
6. Start a fresh Claude Code session in `/tmp/gmc-fixture-F` (main repo).
7. The pipeline should detect the existing `state.json` with
   `status: paused` and prompt for resume.
8. Skill detects the worktree is missing and prompts (中文):
   「检测到 worktree 缺失（{{worktree_path}}）。要重建 / 降级主仓 / 放弃？」
9. Test all three responses across separate runs (rebuild fixture between
   runs so each starts from the paused state):
   - "重建" → worktree re-created via `git worktree add`, pipeline continues
     from saved Stage 5t state
   - "降级" → `state.json::use_worktree` flipped to `false`,
     `worktree_path` set to `null`, main repo checkout used,
     banner indicates downgrade
   - "放弃" → abort flow (worktree path entry cleaned up if it still
     existed; otherwise just branch + tags + state dir removed)

### Pass criteria

- [ ] Pause persists `worktree_path` and `use_worktree == true`
- [ ] Resume detects missing worktree directory and surfaces 3-option prompt
- [ ] 重建 path: `git worktree list` shows the path again; pipeline continues
      at Stage 5t with `state.json::stage` unchanged
- [ ] 降级 path: `state.json::use_worktree` flipped to `false`,
      `worktree_path` cleared; subsequent stages run in main repo
- [ ] 放弃 path: clean abort per `references/recovery-protocol.md`
      v2 Abort with worktree section
