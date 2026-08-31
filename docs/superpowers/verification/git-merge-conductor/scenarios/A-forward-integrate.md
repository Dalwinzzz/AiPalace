# Scenario A: Forward-Integrate (feature → dev + hotfix during development)

Maps to spec §9.1 scenario A.

## Setup

```bash
./setup-fixture.sh /tmp/merge-conductor-fixture
cd /tmp/merge-conductor-fixture
git checkout develop
```

Fixture state recap:
- `feature/promo-v2` has VIP_BONUS but no coupon (branched before coupon landed in develop)
- `develop` has only coupon
- Final merge target should integrate both VIP_BONUS (from feature) and coupon (from dev)

## Prompt to Feed the Skill

> 帮我把 feature/promo-v2 合并到 develop。feature 期间 develop 也修改了 calcDiscount 加入了优惠券逻辑，希望最终包含 VIP 加成 + 优惠券。

## Expected Behavior

- Stage 0 guard passes (clean work tree)
- Stage 2 strategy report: `mode: forward-integrate`, confidence medium or high
- Stage 6: at least one C-class decision point on `OrderService.calcDiscount`
- User picks `[3] source-first-then-target` at the decision point
- Final commit uses `merge: <中文说明>` format
- Working branch `merge/promo-v2-to-develop` exists (or similar task name)
- `develop` HEAD unchanged from pre-merge SHA
- `.git/merge-conductor/<task>/state.json` shows `status: finalized`

## Pass Criteria

After skill completes, run these checks. ALL must pass:

```bash
TASK=$(ls .git/merge-conductor/ | head -1)
WORK_BRANCH="merge/$TASK"

# 1. Working branch exists
git rev-parse --verify "$WORK_BRANCH" || echo "FAIL: working branch missing"

# 2. Commit message format
git log "$WORK_BRANCH" -1 --pretty=%s | grep -E '^merge: ' || echo "FAIL: commit message format"

# 3. Target branch unchanged (capture SHA before running scenario)
# (manual check: compare git rev-parse develop now vs pre-merge)

# 4. State files exist
test -f ".git/merge-conductor/$TASK/state.json" || echo "FAIL: state.json missing"
test -f ".git/merge-conductor/$TASK/merge-report.html" || echo "FAIL: HTML report missing"
test -f ".git/merge-conductor/$TASK/decision-log.md" || echo "FAIL: decision log missing"
test -f ".git/merge-conductor/$TASK/strategy.md" || echo "FAIL: strategy report missing"

# 5. Backup tags exist
git tag -l "$WORK_BRANCH/before-step-*" | wc -l   # expect ≥ 4
git tag -l "$WORK_BRANCH/done" | grep -q done || echo "FAIL: done tag missing"

# 6. Final code has both VIP_BONUS and couponService
git show "$WORK_BRANCH:src/service/OrderService.java" | grep -q VIP_BONUS || echo "FAIL: missing VIP_BONUS"
git show "$WORK_BRANCH:src/service/OrderService.java" | grep -q couponService || echo "FAIL: missing couponService"

# 7. HTML opens (manual visual inspection)
open ".git/merge-conductor/$TASK/merge-report.html"   # macOS
```

Pass = no FAIL output + HTML visually inspected.
