# Mode Inference

> Internal reference used by SKILL.md Stage 2 to infer merge mode from the
> normalized task spec produced in Stage 1.

## Purpose

Given a merge task spec, output the inferred mode with confidence + alternatives + evidence.

## Input

Yaml from Stage 1 (see SKILL.md Stage 1). Key fields consumed:

- `sources[].type` (branch | patch | diff)
- `sources[].ref`, `sources[].commits` (optional range)
- `target.branch`, `target.base_commit`
- `intent.description`, `intent.keywords`

## Output Schema

```yaml
mode: backport
confidence: high | medium | low
alternatives:                    # only when confidence != high
  - mode: cherry-pick-set
    reason: "explicit commit range provided by user"
evidence:
  merge_base_age_days: 35
  source_commit_count: 8
  patch_files_present: false
  target_diverged_commits_since_merge_base: 142
  keyword_signals: ["回灌", "backport"]
  refactor_signals_in_target: true
  source_is_active: true         # true if source has commits in last 7 days
```

## Decision Tree

Evaluate rules in order. First match wins. If none match, fall through to step 7.

1. If `sources` contains any `.patch` or `.diff` file → **`patch-apply`**
2. Elif `intent.description` contains "rebase onto" OR "feature 长期落后" OR "重构后的 main" → **`rebase-onto`**
3. Elif `intent.description` matches the pattern "先把 X 的 fix 带进 Y 再 merge 回" (or paraphrases: "把 dev 的 hotfix 集成进 feature", "把主线 bug fix 融入需求") → **`forward-integrate`**
4. Elif `evidence.keyword_signals` ∩ {"回灌", "backport", "跨版本"} ≠ ∅ OR `evidence.merge_base_age_days` > 30 OR `evidence.refactor_signals_in_target` == true → **`backport`** (then run sub-classifier below to pick `backport-cherry` vs `backport-transplant`)
5. Elif user provided explicit `commits` range OR `evidence.source_commit_count` ≤ 5 → **`cherry-pick-set`**
6. Elif `evidence.source_is_active == true` AND no commit range → **`full-merge`**
7. Else → low confidence; default to `cherry-pick-set` with alternatives `[full-merge, backport]`

## Backport mode — sub-classification

When the high-level decision is `backport`, run this sub-classifier to pick the
pipeline:

### `backport-cherry` (conflict-pipeline)

Conditions (ALL must hold):
- `merge_base_age_days < T_AGE` (default T_AGE = 30 days)
- Source's affected files have NO target-side rename/move/refactor signal
  within the same files since merge-base
- All source commits are independently cherry-pickable (no commits depend on
  intermediate commits not being included)

`backport-cherry` runs the standard conflict-pipeline (Stage 4c/5c/6c).

### `backport-transplant` (transplant-pipeline)

Triggered when ANY of:
- `merge_base_age_days >= T_AGE`
- ≥ N (default N = 3) target-side rename/move/refactor signals within
  affected files since merge-base (signals detected by:
  `git log --all --diff-filter=R --find-renames=70% -- <file>` count)
- User explicitly requests "语义回并" or "transplant" in Stage 2 dialogue

`backport-transplant` runs the transplant-pipeline (Stage 4t/5t/6t).

### Edge: ambiguous boundary

If conditions land at the boundary (e.g., merge_base_age == T_AGE-5 with 2
refactor signals), present user with choice in Stage 2 Gate. Default
recommendation: transplant (safer — handles refactor properly even if
cherry would have worked).

## Refactor Signal Detection

For each file modified on the source side (from `git diff <merge-base>...<source> --stat`):

- Run `git log --follow --diff-filter=R -- <file>` on the target branch, restricted to commits since the merge-base
- If ≥1 rename detected → set `evidence.refactor_signals_in_target = true`

If signals are detected, also collect the rename pairs (old_path → new_path) to feed Stage 5.5 (semantic mapping).

## Confidence Scoring

- **high**: ≥ 2 distinct strong signals point to the same mode AND no contradicting signals
  - Example: `patch_files_present == true` (rule 1) → `patch-apply`, no contradiction → high
  - Example: `keyword_signals == ["backport"]` AND `merge_base_age_days == 60` AND `refactor_signals_in_target == true` → `backport` → high
- **medium**: 1 strong signal + no contradicting signals
- **low**: contradicting signals OR weak signals only → list 1-2 alternatives in the strategy report

## Edge Cases

- If `target` was not specified and the current branch is not a likely target (e.g., it's a feature branch), prompt the user before inferring. Don't guess silently.
- If multiple `sources` are provided (multi-source merge), v1 does NOT support this — return an error and instruct the user to run the skill multiple times in series.
- If `source` and `target` are the same branch, return an error.
