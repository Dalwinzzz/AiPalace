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
cp -r /tmp/gmc-fixture-F /tmp/gmc-fixture-I    # cp not mv: preserve F for other scenarios
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
