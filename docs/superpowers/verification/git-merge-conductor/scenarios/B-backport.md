# Scenario B: Cross-Version Backport with Refactor

Maps to spec §9.1 scenario B.

## Setup

```bash
./setup-fixture.sh /tmp/merge-conductor-fixture
cd /tmp/merge-conductor-fixture
git checkout refactor/v2.0
```

Fixture state:
- `release/v1.0` has VIP_BONUS in `OrderService.calcDiscount`
- `refactor/v2.0` renamed `OrderService.calcDiscount` → `DiscountStrategy.apply`
- We backport VIP_BONUS into the refactored target

## Prompt

> 把 release/v1.0 上的 VIP_BONUS 功能回灌到 refactor/v2.0。注意目标分支重构了，calcDiscount 已经迁移到 DiscountStrategy.apply。

## Expected Behavior

- Stage 2: `mode: backport`, evidence shows `refactor_signals_in_target: true`
- Stage 5.5 (semantic mapping) RUNS and maps `OrderService.calcDiscount` → `DiscountStrategy.apply` with confidence high (rename trail follows cleanly)
- Stage 6: decision point shows mapped suggestion in `[3]` / `[4]`
- User picks `[3] source-first-then-target`
- Final commit preserves source SHA reference + uses `merge: 中文` message
- Working branch has VIP_BONUS code applied inside `DiscountStrategy.apply`

## Pass Criteria

```bash
TASK=$(ls .git/merge-conductor/ | head -1)
WORK_BRANCH="merge/$TASK"

# 1. Working branch contains VIP_BONUS inside DiscountStrategy.apply
git show "$WORK_BRANCH:src/strategy/DiscountStrategy.java" | grep -q VIP_BONUS || echo "FAIL: VIP_BONUS not in refactored location"

# 2. state.json shows semantic mapping
grep -q '"confidence"' ".git/merge-conductor/$TASK/state.json" || echo "FAIL: no semantic_mapping in state.json"

# 3. Commit message regex
git log "$WORK_BRANCH" -1 --pretty=%s | grep -E '^merge: ' || echo "FAIL: commit message format"

# 4. refactor/v2.0 unchanged
# (manual check)

# 5. Mode = backport
grep -q '"mode": "backport"' ".git/merge-conductor/$TASK/state.json" || echo "FAIL: mode not backport"
```

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

