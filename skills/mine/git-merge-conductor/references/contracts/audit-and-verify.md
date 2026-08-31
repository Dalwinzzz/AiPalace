# Stage Contracts — Audit & Verify (Stage 6.5 / 7 / 7.5)

Each section below is the canonical 五字段 contract for the stage. SKILL.md
points at these anchors and the model reads on demand. Maintain anchors:
`#stage-<N>` (or `#stage-<N><c|t>` for forked stages).

---

## Stage 6.5 — Negative-Constraint Self-Audit {#stage-65}

**Goal**
After each unit of work (graft applied in 6t, or hunk decided in 6c),
verify it doesn't violate any negative constraint. This is the single most
important defense against scope creep — care-class scope creep happened
because v1 lacked this stage.

**Inputs**
- The just-applied unit (graft or hunk)
- `requirements.yaml::items[i].out_of_scope` (per-item)
- `requirements.yaml::global_out_of_scope`
- `references/negative-constraints.md` (NC-01~NC-05 + appendix)
- Stage 6c/6t output state

**Decisions you own**
- Which NC rules to evaluate (typically all; some are file-type-specific)
- For "soft" violations (e.g., a `projectName ==` that the user might still want):
  whether the scope_tag justifies the exception (read `requirements.yaml::items[i].scope_tag`)

**Hard constraints**
- Pass / fail is binary. Soft warnings still go in `audit-report.md` but
  don't trigger rollback.
- Any hit on NC-05 (change outside target_locations) is a HARD fail — Safety Invariant 6.
- Rollback uses `git reset --hard merge/<task>/before-step-6` then re-applies
  prior siblings in order; for granular rollback (single graft) use
  `git revert --no-commit <staged change>` if possible, else full reset + replay.
- Audit report MUST be written before returning control to 6c/6t.

### NC Iteration Sub-protocol

For each unit invocation of Stage 6.5:

1. Load `requirements.yaml::items[unit.req_id].out_of_scope` (per-item constraints).
2. Load `requirements.yaml::global_out_of_scope`.
3. Read `references/negative-constraints.md` (load NC-01~NC-05 + appendix).
4. For each NC rule:
   - Evaluate `检测信号` against the just-applied unit
   - If hit, record violation with rule ID + evidence
5. Independent check: NC-05 hard-fail — if `unit.files_touched` contains any
   file not in any `requirements.yaml::items[*].target_locations`, immediately
   rollback regardless of other checks. This is Safety Invariant 6.
6. Render `audit-report.md` from `assets/audit-report.md` to
   `.git/merge-conductor/<task>/audit/<unit_id>.md`.
7. If any violation: rollback per the Hard constraints section above.

The model SHOULD use the appendix领域示例 as inspiration when deciding whether
to flag ⚠ warnings (not full violations) for human review. Appendix items do
not auto-rollback.

**Outputs**
- `.git/merge-conductor/<task>/audit/<unit-id>.md` (rendered from
  `assets/audit-report.md`)
- `state.json::audit[]` appended
- For fail: rollback executed, unit status set to `partial` (transplant) or
  `unresolved` (conflict)
- For pass: unit status `applied`; continue to next unit in 6c/6t
- `state.json::stage_history[6.5]` appended (kind: "6.5") on first invocation per iter
  (subsequent same-iter invocations bump `state.json::audit[]` length only)
- Stage banner emitted ONLY on first invocation per iter: `[Stage 6.5 · Self-Audit · iter <i> · tag: none]`

## Stage 7 — Finalization & Commit {#stage-7}

**Goal**
Commit the working branch state per `state.json::config.commit_granularity`.
This is the last write before Phase 1 verification.

**Inputs**
- Working tree (all applied units staged in 6c/6t via `git add`)
- `state.json::config.commit_granularity`
- `assets/commit-message.md`

**Decisions you own**
- Per-mode commit shape (single merge / per-source-commit / squash)
- Rewriting auto-generated commits (from `git am` / `git rebase`) with
  the structured `merge:` prefix message

**Hard constraints**
- Use heredoc `git commit -m "$(cat <<'EOF' ... EOF)"` to preserve formatting.
- Commit message must include: 中文 subject, source ref + sha, mode,
  decision summary, A class auto-handled count, iteration number, rolled-back items.
- Tag `merge/<task>/done` after commit(s); the tag is **moved** on subsequent iters
  (always points at the latest iter's commit).
- **Empty-iter handling**: If working tree has no staged changes (all units
  rolled back by 6.5 audit), use `git commit --allow-empty` to anchor the
  iteration in commit history. The commit message's `回滚摘要` block becomes
  the meaningful payload — Phase 2 will surface why this iter was a no-op.
  This avoids ambiguity between "no graft applied" and "iter never ran".

**Outputs**
- Commit(s) on `merge/<task>` branch (may be `--allow-empty` for full-rollback iters)
- Tag `merge/<task>/done` (moved on each iter; always points at latest iter's HEAD)
- `state.json::status = pre-verified` (NOT `finalized` until Phase 2 passes)
- `state.json::stage_history[7]` appended (kind: "7")
- `state.json::stage = 7.5`
- Stage banner: `[Stage 7 · Finalization · iter <i> · tag: merge/<task>/done]`

## Stage 7.5 — Verification Loop {#stage-75}

Two phases. Phase 1 is automated; Phase 2 is the user's final gate.

### Phase 1 — Automated Verification

**Goal**
Catch broken builds, type errors, lint failures, and scope-test regressions
before bothering the user. If anything fails, run a bounded self-fix loop.
If self-fix exhausts its budget, hand the error verbatim to Phase 2.

**Inputs**
- `state.json::config.verification` (compile, lint, test settings)
- Working tree state at `merge/<task>/done` tag
- Project files (pom.xml / package.json / go.mod / pyproject.toml etc.) for tool detection

**Decisions you own**
- Tool selection per language signal (Maven mvn compile / npm tsc / go build / ruff)
- Test scope when `test: scope` — which suites correspond to `requirements.yaml::items[*].target_locations`
- Fix strategy when a test fails — which graft / hunk likely caused it (map error → file → graft)

**Hard constraints**
- Self-fix iteration cap: N ≤ 3.
- Each fix iteration: tag `merge/<task>/before-fix-iter-<N>`, rollback the
  guilty unit, regenerate draft, re-audit (Stage 6.5), reapply.
- After 3 failed iters, surrender — pass full error text to Phase 2 verbatim.
- Append to `state.json::iterations[]` each iter with trigger: `phase1-fix`.

**Outputs**
- Phase 1 result (pass / fail-with-errors) into `state.json::verification.phase1`
- `state.json::stage_history[7.5]` appended (kind: "7.5") on first Phase 1 entry
- Stage banner: `[Stage 7.5 · Phase 1 Verification · iter <i> · tag: merge/<task>/before-fix-iter-<N>]`

### Phase 2 — User Final Gate

**Goal**
The user's only mid-pipeline interrupt after Stage 2. Present a single
report — automation results + requirements coverage + audit-intercepted
items — and let the user say "完成 / REQ-X 没做对 / REQ-X 不该做 / 还多 Z".

**Inputs**
- Phase 1 result
- `requirements.yaml::items[]` with current `status` and `evidence`
- `state.json::audit[]` (all intercepts)
- `state.json::unresolved[]` (conflict-pipeline only)
- `state.json::grafts[]` (transplant-pipeline only)

**Decisions you own**
- How to organize the report sections (template at `assets/verification-report.md`)
- How to parse user's free-form response into one of: 完成 / REQ-X 没做对 / REQ-X 不该做 / 还多 Z / 自由文本
- For free-form: echo back "我理解为: ..." in 中文 for confirmation before acting

**Hard constraints**
- This is the ONLY mid-pipeline interrupt point. Don't interrupt earlier.
- Report MUST be written to both terminal (中文) and `merge-report.html`.
- User says 「完成」 → mark `state.json::status = finalized`, proceed to Stage 8.
- Any other user response → bump `state.json::iter`, append to `iterations[]`
  with appropriate trigger, route back to 4-6 (transplant: 4t / conflict: 5c).
- NEVER auto-decide "完成" without explicit user confirmation.

**Outputs**
- Terminal markdown report + HTML report `<section id="verification">` updated
- For 完成 path: `state.json::status = finalized`, `state.json::finalized_at = now`
- For loop path: `state.json::iter += 1`, `state.json::stage = 4` (or 5),
  `iterations[]` appended with trigger and user_feedback
- Stage banner: `[Stage 7.5 · Phase 2 User Gate · iter <i> · tag: none]`
