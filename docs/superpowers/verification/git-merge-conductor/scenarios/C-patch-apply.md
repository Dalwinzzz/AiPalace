# Scenario C: Pure patch-apply

Maps to spec §9.1 scenario C.

## Setup

```bash
./setup-fixture.sh /tmp/merge-conductor-fixture
cd /tmp/merge-conductor-fixture

# Generate a patch from release/v1.0's VIP_BONUS commit
mkdir -p /tmp/patches
rm -rf /tmp/patches/*
git format-patch release/v1.0~1..release/v1.0 -o /tmp/patches
ls /tmp/patches   # expect: 0001-feat-add-VIP_BONUS-to-calcDiscount.patch

git checkout develop
```

## Prompt

> 把这个 patch 应用到当前 develop 分支：/tmp/patches/0001-feat-add-VIP_BONUS-to-calcDiscount.patch

## Expected Behavior

- Stage 2: `mode: patch-apply`
- Stage 4 uses `git am --3way` (or `git apply --3way`)
- Conflict expected on `calcDiscount` (develop already has coupon logic)
- Stage 6 decision point appears
- User picks `[3]`
- Final commit message: `merge: <中文>`

## Pass Criteria

```bash
TASK=$(ls .git/merge-conductor/ | head -1)
WORK_BRANCH="merge/$TASK"

# 1. Mode = patch-apply
grep -q '"mode": "patch-apply"' ".git/merge-conductor/$TASK/state.json" || echo "FAIL: mode not patch-apply"

# 2. At least one C-class decision
grep -q '"class": "C"' ".git/merge-conductor/$TASK/state.json" || echo "FAIL: no C-class decision"

# 3. Working branch has merged code (VIP_BONUS + coupon)
git show "$WORK_BRANCH:src/service/OrderService.java" | grep -q VIP_BONUS || echo "FAIL: VIP_BONUS missing"
git show "$WORK_BRANCH:src/service/OrderService.java" | grep -q coupon || echo "FAIL: coupon missing"

# 4. HTML report exists
test -f ".git/merge-conductor/$TASK/merge-report.html" || echo "FAIL: HTML report missing"

# 5. Patch file archived
test -f ".git/merge-conductor/$TASK/patches/0001-feat-add-VIP_BONUS-to-calcDiscount.patch" || echo "FAIL: patch not archived"
```
