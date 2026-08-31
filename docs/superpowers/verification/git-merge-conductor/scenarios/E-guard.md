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

## Expected Behavior

- Stage 0 detects dirty work tree
- Skill stops and prompts (中文): 「检测到未提交改动，要先 stash / 先 commit / 取消？」
- No working branch created
- No state.json written under `.git/merge-conductor/`
- No `before-step-N` tags created
- The dirty file remains exactly as the user left it (skill didn't touch it)

## Pass Criteria

```bash
# 1. No new branch starts with merge/
test -z "$(git branch --list 'merge/*')" || echo "FAIL: merge/* branch created"

# 2. State dir not created (or empty)
test ! -d ".git/merge-conductor" || test -z "$(ls .git/merge-conductor 2>/dev/null)" || echo "FAIL: state dir non-empty"

# 3. No backup tags
test -z "$(git tag -l 'merge/*')" || echo "FAIL: backup tag created"

# 4. Dirty file still dirty
git status --porcelain | grep -q "OrderService.java" || echo "FAIL: dirty file no longer detected (skill may have touched it)"
```

The skill's response should include the 3 options (stash/commit/取消) in Chinese.
