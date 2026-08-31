# Stage Contracts — Conflict Pipeline (Stage 4c / 5c / 6c)

Each section below is the canonical 五字段 contract for the stage. SKILL.md
points at these anchors and the model reads on demand. Maintain anchors:
`#stage-<N>` (or `#stage-<N><c|t>` for forked stages).

---

## Stage 4c — Source-side Application (Conflict Pipeline) {#stage-4c}

**Goal**
Apply the source-side change to the working branch using the mode-specific
git command chain. After this stage, git has either auto-merged cleanly,
or you have unmerged files to classify.

**Inputs**
- `state.json::config.mode` (full-merge | cherry-pick-set | patch-apply |
  backport-cherry | rebase-onto | forward-integrate)
- Source refs / patch files
- Tag `merge/<task>/before-step-4` (you create this first)

**Decisions you own**
- Which command chain to use for the inferred mode (see table in SKILL.md)
- Whether to invoke `--no-commit` flags (always yes where supported — commit
  happens at Stage 7)
- For `forward-integrate`: first phase on source feature branch
  (`git merge <target>`), second phase on working branch

**Hard constraints**
- Tag `merge/<task>/before-step-4` before any merge / cherry-pick / am.
- If the command fails non-recoverably (e.g., empty cherry-pick range),
  stop and instruct user how to recover via the tag. Do not silently retry.

**Outputs**
- Working tree with merged content + possibly conflict markers
- List of unmerged files (`git diff --name-only --diff-filter=U`)
- `state.json::stage_history[4]` appended (kind: "4c")
- `state.json::stage = 5`
- Stage banner: `[Stage 4c · Source-side Application · iter <i> · tag: merge/<task>/before-step-4]`

## Stage 5c — Conflict Classification + Auto-resolve (Conflict Pipeline) {#stage-5c}

**Goal**
Classify each conflict hunk as A/B/C/D and auto-resolve A class. Build the
queue of C/D class items that Stage 6c will process autonomously.

**Inputs**
- Unmerged files from Stage 4c
- `references/conflict-classification.md` (A/B/C/D rules, mode-aware adjustments)
- `state.json::config.locked_file_rules` (user-specified overrides)

**Decisions you own**
- For each hunk, which class fits (A/B/C/D)
- For A class: use `git checkout --theirs` (whole file) or hunk-level rewrite
  (your judgment, based on hunk size and surrounding context)
- For backport-cherry mode: demote A class to "log-then-take-target"
  (not silent)

**Hard constraints**
- Apply `locked_file_rules` FIRST — they override classification.
- B class (git already auto-merged) requires no action; just count.
- Tag `merge/<task>/before-step-5` once before any auto-resolution.
- Every A class application MUST append to `decision-log.md`.

**Outputs**
- C/D class decision queue (in `state.json::decisions[]`)
- `state.json::auto_resolved_summary` populated (A/B counts, A files,
  demoted-A list for backport)
- `state.json::stage_history[5]` appended (kind: "5c")
- `state.json::stage = 6`
- HTML report `<section id="auto-resolved">` appended
- Stage banner: `[Stage 5c · Conflict Classification · iter <i> · tag: merge/<task>/before-step-5]`

## Stage 6c — Autonomous C/D Decision Loop (Conflict Pipeline) {#stage-6c}

**Goal**
For each C/D class hunk in the decision queue, autonomously pick a resolution
(no user mid-loop interruption) using the heuristic ladder. Hunks that the
ladder cannot decide get marked `unresolved` (NOT left as `<<<<<<<` markers
in code) and surface in Stage 7.5 Phase 2 for user adjudication.

**Inputs**
- Decision queue from Stage 5c
- `references/conflict-classification.md` (C/D autonomous heuristics section)
- `state.json::config.locked_file_rules`
- `requirements.yaml::global_out_of_scope`

**Decisions you own**
- Which heuristic ladder rung matches each hunk (in priority order):
  1. locked_file_rules / global_out_of_scope match → apply rule
  2. Both sides additive (no overlapping logic) → take both (concatenate)
  3. One side is whitespace-only / comment-only → take the other
  4. Source side older than target's most recent change to this location → take target
  5. Otherwise → mark `unresolved`, take target as code fallback

**Hard constraints**
- NEVER leave `<<<<<<< HEAD ... =======  ... >>>>>>>` markers in code.
  Marker would break Stage 7.5 Phase 1 compile check and cascade errors.
- For "unresolved" hunks: code keeps target version (safest fallback);
  the source hunk is preserved in `.git/merge-conductor/<task>/unresolved.md`
  for Phase 2 user review.
- After each hunk decision, immediately invoke Stage 6.5 self-audit. Do
  NOT batch-audit at end.
- Tag `merge/<task>/before-step-6` once before the loop starts.

**Outputs**
- Resolved hunks staged via `git add`
- `state.json::decisions[]` updated with `resolution`, `taken`, `audited_at`
- `state.json::unresolved[]` populated for hunks falling to rung 5
- `.git/merge-conductor/<task>/unresolved.md` written
- `state.json::stage_history[6]` appended (kind: "6c")
- `state.json::stage = 6.5` (then immediately into 6.5 audit per-unit, then back to 6c for next hunk)
- Stage banner: `[Stage 6c · Autonomous Decision Loop · iter <i> · tag: merge/<task>/before-step-6]`
