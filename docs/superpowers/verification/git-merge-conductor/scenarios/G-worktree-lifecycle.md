# Scenario G — worktree lifecycle (create → abort → cleanup)

## Goal

Verify worktree integration end-to-end:
- Complex mode (e.g., backport-transplant) triggers worktree at Stage 3
- Worktree created via superpowers:using-git-worktrees, path written to state.json
- Mid-pipeline `[a]` abort cleanly removes worktree + branch + state dir
- Main repo working tree unchanged before/after

## Setup

```bash
cd /tmp && rm -rf gmc-fixture-G gmc-fixture-G-worktrees
bash /Users/dalwin/Documents/AI/docs/superpowers/verification/git-merge-conductor/setup-fixture.sh
cp -r /tmp/gmc-fixture-F /tmp/gmc-fixture-G    # cp not mv: preserve F for other scenarios
cd /tmp/gmc-fixture-G

# Make a local change in main repo so we can verify it's preserved
echo "// MAIN-LOCAL-MARKER" >> src/main/java/com/example/course/CourseOffline.java
```

## Run

Start Claude Code in `/tmp/gmc-fixture-G`. Invoke scenario F's instructions
(backport-transplant of the `care-class` feature).

When the pipeline reaches Stage 6t and shows a banner like
`[Stage 6t · Autonomous Apply Loop · ...]`, send the abort command:

> `[a]`

## Expected behavior

### After Stage 3
- Worktree created at some path (e.g., `/tmp/gmc-fixture-G-worktrees/care-class-transplant`)
- `state.json::working_branch.worktree_path` populated
- `state.json::working_branch.use_worktree == true`
- Main repo's `src/main/java/com/example/course/CourseOffline.java` STILL has the `MAIN-LOCAL-MARKER` line (worktree changes don't affect main repo's working tree)
- Banner clearly indicates work is happening in worktree (e.g., banner shows the working branch name and/or worktree path)

### On abort

- Model confirms in 中文: 「确认 abort 会删除 worktree、merge/<task> 分支、所有备份 tag、会话目录。确认？」
- User says 「确认」
- Model executes (per `references/recovery-protocol.md` v2 Abort with worktree):
  ```bash
  git worktree remove --force <worktree_path>
  git branch -D merge/<task>
  for tag in $(git tag -l "merge/<task>/*"); do git tag -d "$tag"; done
  rm -rf .git/merge-conductor/<task>/
  ```
- Model echoes 「abort 完成。worktree、分支、会话目录已清理。主仓回到 abort 前状态。」

### Verification commands

```bash
# Worktree gone
git -C /tmp/gmc-fixture-G worktree list
# Expected: only main repo listed

# Worktree directory gone from disk
test -d /tmp/gmc-fixture-G-worktrees/care-class-transplant && echo "FAIL: worktree dir still exists" || echo "worktree dir removed"

# Branch gone
git -C /tmp/gmc-fixture-G branch | grep "merge/care-class-transplant" && echo "FAIL: branch still exists" || echo "branch deleted"

# Backup tags gone
git -C /tmp/gmc-fixture-G tag -l "merge/care-class-transplant/*" | wc -l
# Expected: 0

# State dir gone
ls /tmp/gmc-fixture-G/.git/merge-conductor/care-class-transplant 2>/dev/null && echo "FAIL: state dir still exists" || echo "state dir cleared"

# Main repo preserved
grep "MAIN-LOCAL-MARKER" /tmp/gmc-fixture-G/src/main/java/com/example/course/CourseOffline.java
# Expected: marker still present
```

## Pass criteria

- [ ] Worktree created at Stage 3 (not main repo)
- [ ] `state.json::working_branch.use_worktree == true`
- [ ] `state.json::working_branch.worktree_path` populated with absolute path
- [ ] Main repo working tree unchanged during pipeline (MAIN-LOCAL-MARKER intact)
- [ ] Abort confirmation prompt in 中文 enumerating worktree + branch + tags + state dir
- [ ] Abort cleans worktree directory, branch, backup tags, state dir
- [ ] Main repo state preserved after abort (MAIN-LOCAL-MARKER still present)
