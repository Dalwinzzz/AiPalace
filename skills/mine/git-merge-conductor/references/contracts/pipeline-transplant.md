# Stage Contracts — Transplant Pipeline (Stage 4t / 5t / 6t)

Each section below is the canonical 五字段 contract for the stage. SKILL.md
points at these anchors and the model reads on demand. Maintain anchors:
`#stage-<N>` (or `#stage-<N><c|t>` for forked stages).

---

## Stage 4t — Build Grafting Plan (Transplant Pipeline) {#stage-4t}

**Goal**
Translate `requirements.yaml` into a "per-item × per-target-location" grafting
matrix. Each entry pairs a source-side implementation with the target-side
landing spot and the strategy for grafting. After this stage, Stage 5t/6t
have a concrete unit of work per row.

**Inputs**
- `requirements.yaml` (all items)
- Source branch HEAD / range
- `references/semantic-mapping.md` (rename / grep / similar-signature heuristics)
- Target branch HEAD diff history (for refactor detection)

**Decisions you own**
- For each item × target_location: which source commits / hunks supply the implementation
- Mapping confidence (high / medium / low) per target_location, with evidence chain
- `graft_strategy` from {replace, merge-into, add-new, guarded-overlay}
  - `replace`: target counterpart is a stub
  - `merge-into`: target has its own implementation that needs the source logic merged in
  - `add-new`: target has nothing at this location
  - `guarded-overlay`: source logic guarded by `guard_condition` (e.g., scope_tag-derived)
- `guard_condition` (when strategy == guarded-overlay)

**Hard constraints**
- Tag `merge/<task>/before-step-4` first.
- Every graft must point back to a `requirements.yaml::items[i].id` — no orphan grafts.
- If a target_location confidence is `low`, do NOT set strategy = `replace`.
- Mapping evidence MUST be written down (the grafting plan is reviewed by user implicitly via Phase 2).

**Outputs**
- `.git/merge-conductor/<task>/grafting-plan.yaml` (one entry per graft)
- `state.json::grafts[]` mirrored
- `state.json::stage_history[4]` appended (kind: "4t")
- `state.json::stage = 5`
- Stage banner: `[Stage 4t · Build Grafting Plan · iter <i> · tag: merge/<task>/before-step-4]`

## Stage 5t — Per-Item Draft (Transplant Pipeline) {#stage-5t}

**Goal**
For each graft, produce a concrete unified-diff draft (does NOT apply to disk)
plus a context summary + confidence self-assessment + soft out_of_scope check.
Drafts are the artifacts Stage 6t will autonomously apply.

**Inputs**
- `grafting-plan.yaml`
- Source-side hunks (`git show -W <sha> -- <file>`)
- Target-side current content
- `requirements.yaml::items[i].out_of_scope`

**Decisions you own**
- Diff content for each graft (the actual edit to apply)
- Confidence (combines `target_location.confidence` from Stage 4t + how cleanly the draft sits in target context)
- Soft out_of_scope match (this is a draft-time pre-filter; Stage 6.5 is the authoritative audit)

**Hard constraints**
- Drafts go to `.git/merge-conductor/<task>/drafts/G-<id>.diff` — never to the working tree directly.
- Each draft must include the context summary in 中文 (so audit / report can show it).
- If a draft contains changes to files outside `requirements.yaml::items[i].target_locations`,
  fail the draft now (set draft_status: rejected, reason: "files outside target_locations").

**Outputs**
- `.git/merge-conductor/<task>/drafts/G-<id>.diff` for each graft
- `.git/merge-conductor/<task>/drafts/G-<id>.md` (context summary, rendered from `assets/draft.md`)
- `grafting-plan.yaml::plan[i].draft_status` updated to drafted | rejected
- `state.json::stage_history[5]` appended (kind: "5t")
- `state.json::stage = 6`
- Stage banner: `[Stage 5t · Per-Item Draft · iter <i> · tag: none]`

## Stage 6t — Autonomous Apply Loop (Transplant Pipeline) {#stage-6t}

**Goal**
For each drafted graft, autonomously apply it (no user mid-loop) using the
strategy + confidence determined earlier. Immediately invoke Stage 6.5
self-audit; pass → mark `applied`, fail → rollback + mark `partial`/`pending`
and surface in Stage 7.5 Phase 2.

**Inputs**
- Drafts from Stage 5t
- `grafting-plan.yaml`
- `references/negative-constraints.md` (for Stage 6.5 invocation)
- Strategy safety order: `add-new` < `merge-into` < `guarded-overlay` < `replace`

**Decisions you own**
- Apply order (typically by safety: safest first; or by graft_id sequence — your judgment)
- Whether to immediately apply a low-confidence graft (yes, but mark ⚠ for Phase 2)
  vs defer entirely (only if `draft_status: rejected` already)

**Hard constraints**
- Tag `merge/<task>/before-step-6` once before the loop.
- After EACH graft apply, run Stage 6.5 self-audit. Fail → `git reset --hard`
  the just-applied content for that graft, mark `partial`, continue.
- Drafts with `draft_status: rejected` from Stage 5t do NOT apply; carry forward to Phase 2.

**Outputs**
- Applied grafts on working tree (where audit passed)
- `grafting-plan.yaml::plan[i].draft_status` updated to applied | rejected
- `state.json::grafts[i].status` per item
- `state.json::stage_history[6]` appended (kind: "6t")
- `state.json::stage = 6.5` (per-unit immediately) then back to 6t until queue empty
- Stage banner: `[Stage 6t · Autonomous Apply Loop · iter <i> · tag: merge/<task>/before-step-6]`
