# Git Merge Conductor Verification

How to verify the skill works against the 5 acceptance scenarios from
spec §9.1 (`docs/superpowers/specs/2026-05-11-git-merge-conductor-design.md`).

## Setup

```bash
./setup-fixture.sh /tmp/merge-conductor-fixture
cd /tmp/merge-conductor-fixture
```

The fixture builds a toy java repo with 5 branches:

- `main` — baseline
- `develop` — has coupon-discount logic
- `release/v1.0` — deployed branch with VIP_BONUS feature
- `refactor/v2.0` — has `DiscountStrategy.apply` (renamed from `OrderService.calcDiscount`)
- `feature/promo-v2` — feature branch with VIP_BONUS, branched before coupon landed in develop

## Scenarios

Each scenario lives in `scenarios/`:

| File | Spec scenario | Tests |
|---|---|---|
| `A-forward-integrate.md` | §9.1.A | feature → dev with hotfix during development |
| `B-backport.md` | §9.1.B | Cross-version backport with refactor |
| `C-patch-apply.md` | §9.1.C | Pure patch-apply |
| `D-interrupt-resume.md` | §9.1.D | Interrupt at Stage 6 and resume |
| `E-guard.md` | §9.1.E | Stage 0 guard with dirty work tree |

Each scenario doc documents:
- Setup steps (on top of the toy fixture)
- The user prompt to feed the skill
- Expected observable outputs
- Pass / fail criteria (executable checks)

## Running a Scenario

1. Reset the fixture: `./setup-fixture.sh /tmp/merge-conductor-fixture`
2. Apply scenario-specific setup steps from the scenario doc
3. Open a fresh Claude Code (or Codex) session pointed at `/tmp/merge-conductor-fixture`
4. Paste the scenario's user prompt
5. Let the skill run end-to-end (answer decision points as suggested)
6. Run the pass-criteria commands from the scenario doc

## Tracking Results

After running all 5 scenarios, write the outcome to `SMOKE-TEST.md` in this directory (created by Task 16 of the implementation plan).
