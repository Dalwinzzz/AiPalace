# Git Merge Conductor — Smoke Test Results

Fixture: `setup-fixture.sh /tmp/merge-conductor-fixture`
Skill version: committed at `739172a` (SKILL.md), patch fix applied after Scenario A

## Summary

| Scenario | Status | Date | Notes |
|---|---|---|---|
| A — forward-integrate | ✅ PASS | 2026-05-12 | All 7 pass criteria met |
| B — backport | ✅ PASS | 2026-05-12 | Model used semantic judgment to override rule 4 (bug fixed in mode-inference.md) |
| C — patch-apply | ✅ PASS | 2026-05-12 | patch-apply mode inferred, git am path exercised |
| D — interrupt-resume | ✅ PASS | 2026-05-12 | state.json paused→finalized, no duplicate decisions |
| E — guard | ✅ PASS | 2026-05-12 | Dirty worktree blocked correctly, user prompted |

## Scenario A — Forward-integrate Detail

**Model**: claude-sonnet-4-6  
**Session type**: Fresh Claude Code session at `/tmp/merge-conductor-fixture`  
**Prompt**: 帮我把 feature/promo-v2 合并到 develop。feature 期间 develop 也修改了 calcDiscount 加入了优惠券逻辑，希望最终包含 VIP 加成 + 优惠券。  
**Decision at Stage 6**: option 3 (source-first-then-target)

| # | Check | Result |
|---|---|---|
| 1 | Working branch `merge/promo-v2-to-develop` exists | ✅ |
| 2 | Commit message starts with `merge:` | ✅ `merge: 将 feature/promo-v2 前向集成到 develop，同时保留 VIP 加成与优惠券逻辑` |
| 3 | develop HEAD SHA unchanged (4467c1e) | ✅ |
| 4 | All state files present (state.json / merge-report.html / decision-log.md / strategy.md) | ✅ (strategy.md written during execution) |
| 5 | Backup tags ≥ 4 (before-step-3/4/5/6) + done tag | ✅ |
| 6 | Final code contains both VIP_BONUS and couponService | ✅ |
| 7 | state.json status: finalized | ✅ |

**Bug found and fixed**: Stage 2 did not `mkdir -p` the state dir before writing `strategy.md`; Stage 3 did not explicitly confirm `strategy.md` exists. Applied fix in SKILL.md after this run.

## How to Run a Scenario

```bash
# 1. Build fixture
cd /Users/dalwin/Documents/AI/docs/superpowers/verification/git-merge-conductor
./setup-fixture.sh /tmp/merge-conductor-fixture

# 2. Record target SHA (verify it's unchanged after the run)
cd /tmp/merge-conductor-fixture
git checkout develop
git rev-parse develop

# 3. Open fresh Claude Code session
cd /tmp/merge-conductor-fixture
claude

# 4. Paste the scenario prompt from scenarios/<X>.md
# 5. Run pass-criteria bash checks from the same scenario file
```

## v2 Scenario Catalog

| ID | Name | Purpose | Pipeline |
|---|---|---|---|
| A | forward-integrate | feature + target hotfix integration | conflict |
| B.1 | backport-cherry | cherry-pick path (close merge-base) | conflict |
| B.2 | backport-transplant | see scenario F | transplant |
| C | patch-apply | git am patch | conflict |
| D | interrupt-resume | pause/resume + v2 worktree resume | conflict |
| E | guard | Stage 0 guards (submodule/LFS/dirty) | n/a |
| F | backport-transplant care-class | NC-01 intercept + 2-iter finalize | transplant |
| G | worktree lifecycle | create / abort / cleanup | transplant |
| H | Phase 1 self-fix limit | N=3 cap; surrender to Phase 2 | transplant |
| I | Phase 2 multi-iter | 3-iter user feedback loop | transplant |

Pipeline-coverage gate before declaring v2 ready:
- [ ] All 10 entries above run cleanly (or with documented expected behavior per scenario doc).
- [ ] No regressions in A/B.1/C/D.v1/E (v1 base scenarios pass under v2).
- [ ] Smoke gates Phase 1-8 all checked.

## v2 Final Acceptance Gate (2026-05-13)

- [ ] All Phase 1-8 partial gates checked above
- [ ] All 10 v2 catalog scenarios pass per their docs
- [ ] SKILL.md line count: 200-220 ± 10
- [ ] references/contracts/ has 5 files, all with anchors per Reading Order
- [ ] No references to deleted templates/decision-point.md
- [ ] negative-constraints.md NC-01~05 present + 领域附录
- [ ] requirements.yaml, grafting-plan.yaml, draft.md, audit-report.md,
      verification-report.md templates present and valid YAML/markdown
- [ ] state.json::version == "2.0" in all new sessions
- [ ] No `<<<<<<<` markers ever in code post-6c
- [ ] Worktree delegation works for all 4 complex modes
