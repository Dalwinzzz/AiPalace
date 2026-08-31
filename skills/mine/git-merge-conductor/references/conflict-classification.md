# Conflict Classification

> Internal reference for SKILL.md Stage 5. Classifies each unmerged hunk into
> A/B/C/D class and dictates the action to take.

## Purpose

Given an unmerged hunk (source side / target side / merge-base), produce:

- `classification`: A | B | C | D
- `reason`: a short English string for the decision log
- `action`: applied automatically (A class, except in backport mode) or queued for user decision (C/D class)

## Input

For each unmerged hunk:

```yaml
file: src/service/OrderService.java
hunk_range_target: [45, 55]
source_text: <raw source side text>
target_text: <raw target side text>
base_text: <merge-base text, if available>
mode: backport | cherry-pick-set | forward-integrate | full-merge | patch-apply | rebase-onto
locked_file_rules: {take_target: [...], take_source: [...]}
task_keywords: ["VIP", "promo", ...]
```

## Locked File Rules — Apply First

If the file matches any `locked_file_rules.take_target` glob → action = take target, classification = A (forced), reason = "locked rule".

If the file matches `locked_file_rules.take_source` glob → action = take source, classification = B (forced), reason = "locked rule".

Otherwise, proceed to A/B/C/D classification below.

## A Class — Silent Take Target

Applied silently in `full-merge` / `forward-integrate` / `cherry-pick-set` / `patch-apply` / `rebase-onto` modes.

**Demoted to `log-then-take-target`** in `backport` mode: same action, but record the hunk + reason in `decision-log.md` and surface counts in the next strategy summary (do not hide silently).

### A.1 — Pure whitespace / EOL diff

- **Detection**: `git diff --ignore-all-space --ignore-blank-lines` on the source vs target hunk text produces empty diff
- **Action**: take target side (write target_text to the file's hunk range)
- **Reason**: "whitespace only"

### A.2 — Pure comment-only changes

- **Detection**: All added/removed lines match comment syntax for the file's language:
  - Java/JS/TS/Go/Rust/C/C++: lines start with `//` or are wrapped in `/* ... */`
  - Python/Shell/Ruby: lines start with `#`
  - SQL: lines start with `--`
  - HTML/XML: lines wrapped in `<!-- -->`
- **Exclusion**: lines containing code followed by inline comment do NOT count as "pure comment"
- **Action**: take target side
- **Reason**: "comment only"

### A.3 — Import / using statement reorder

- **Detection**: All added/removed lines are import statements; the set of imported deps is identical, only ordering changed
- **Language patterns**:
  - Java: `^import\s+.+;$`
  - Python: `^(import |from )`
  - JS/TS: `^import\s+.+\s+from\s+`
  - C#: `^using\s+`
  - Go: lines inside `import (...)` block
  - Rust: `^use\s+`
- **Action**: take target side (respect target's import ordering)
- **Reason**: "import reorder, deps unchanged"

### A.4 — Code formatting (no semantic change)

- **Detection**: After `git diff --ignore-all-space --ignore-blank-lines`, the remaining diff is only punctuation/brace position changes (semicolons, braces, indent, intra-line whitespace)
- **Action**: take target side
- **Reason**: "formatting only"

### A.5 — Pure local variable rename

- **Detection** (heuristic, model judgment required):
  - Rename confined to a single method body
  - No signature change
  - No method/class name change
  - No impact beyond the hunk
- **Action**: take target side
- **Reason**: "local rename only"
- **Note**: If uncertain → escalate to C class. Model should err on the side of human review.

## B Class — Silent Take Source (auto-merged by git)

These do NOT typically produce unmerged state in standard git 3-way merge; included for statistics completeness.

### B.1 — Source modified, target untouched at same hunk

- Counted but no action needed (git auto-took source).

### B.2 — Source added new symbol (class/method/file) that doesn't exist in target

- Counted but no action needed.

Surface counts in the strategy summary and decision-log only.

## C Class — Require Human Decision

Collected into the decision queue. No auto-apply.

### C.1 — Same method body, both sides logic change

- **Detection**: Source and target both modified hunks that overlap within the same method (identified by `git diff -W` function context)
- **Action**: queue as C; show terminal decision point with 5 candidate options
- **Reason**: "both sides modified method body"

### C.2 — Same expression / constant value, both sides change

- **Detection**: Same line(s) modified on both sides with different content (excluding whitespace/comment differences)
- **Action**: queue as C
- **Reason**: "expression / constant changed by both sides"

### C.3 — Incompatible signature change

- **Detection**: Method/function/type signature modified on both sides differently (param list / return type / annotations / decorators)
- **Action**: queue as C with `flags: [signature_conflict]`
- **Reason**: "signature conflict"

## D Class — Flag + Require Human Decision

Same as C, but flagged with `[需注意]` in the decision point UI.

### D.1 — Symbol removed by one side, modified/depended on by other

- **Detection**: One side deletes a symbol that the other side modifies or depends on; detect via `git log --diff-filter=D` for deletes, then cross-check usages
- **Flag**: `[需注意：单侧删除]`

### D.2 — Both sides modified imports with different deps

- **Detection**: Both sides added/removed different dependencies in import block (set symmetric difference is non-empty)
- **Flag**: `[需注意：依赖差异]`

### D.3 — Rename tracking ambiguity

- **Detection**: `git diff -M --find-renames` similarity score is borderline (50-70%); git can't decisively call it a rename
- **Flag**: `[需注意：rename 追踪不确定]` + show both possible rename pairs in the decision point

### D.4 — Binary file conflict

- **Detection**: File is binary (per `.gitattributes` or git's heuristic)
- **Flag**: `[需注意：二进制]`
- **Note**: Only options `[1] take source` / `[2] take target` are available; options `[3]/[4]/[5]` are disabled (no text merge possible)

### D.5 — Hunk in file with detected refactoring

- **Detection**: File appears in `evidence.refactor_signals_in_target` set from mode-inference
- **Flag**: `[需注意：目标侧有重构]` + trigger Stage 5.5 semantic mapping for this hunk

### D.6 — (patch-apply only) Patch context mismatch

- **Detection**: Patch context lines are off by > 5 lines from the target file (drift)
- **Flag**: `[需注意：patch 上下文偏差]` + show context drift in the decision point

## Mode-Aware Tuning

| Mode | A class behavior | Stage 5.5 trigger |
|---|---|---|
| `full-merge` | silent take target | only if `refactor_signals_in_target == true` |
| `cherry-pick-set` | silent take target | only if `refactor_signals_in_target == true` |
| `forward-integrate` | silent take target | only if `refactor_signals_in_target == true` |
| `patch-apply` | silent take target | only if `refactor_signals_in_target == true` |
| `backport` | **demoted to log-then-take-target** | mandatory |
| `rebase-onto` | silent take target | mandatory |

## Output

For each hunk, write a classification record to `decision-log.md` (one line per hunk for A/B; one block per hunk for C/D). For C/D, also append to the decision queue used in Stage 6.

## C/D Class Autonomous Heuristics (v2 — Stage 6c)

v1 surfaced every C/D class hunk to the user via an interactive 5-option
decision prompt. v2 removes that interactive flow: Stage 6c now runs an
autonomous heuristic ladder per hunk, surfacing only the unresolved residue
to Phase 2.

### Heuristic Ladder (apply in order; first match wins)

1. **locked_file_rules or global_out_of_scope match**
   - If `state.json::config.locked_file_rules.take_target` includes this file → take target.
   - If `take_source` includes this file → take source.
   - If a `global_out_of_scope` constraint matches the hunk's introduced code → take target.

2. **Both sides additive (no overlapping logic)**
   - If both source and target hunks are purely additive (no overlapping line ranges, no共同 modified lines), and neither side deletes the other's lines → take both (concatenate source-first then target).

3. **One side is whitespace-only / comment-only**
   - If one side's hunk modifications are entirely whitespace, blank lines, or comments → take the OTHER side.

4. **Source-side older**
   - Run `git log --follow -1 --format=%cI <target_file>` (target side's most recent commit time on this file).
   - If source merge-base of this hunk is older than target's most recent change → take target (target has had more time to evolve).

5. **Fallback: mark `unresolved`**
   - Code keeps target version (safest).
   - Append source hunk preserved to `.git/merge-conductor/<task>/unresolved.md`.
   - Record `state.json::unresolved[]` entry.

### After Each Heuristic Application

- Record `state.json::decisions[i].resolution = "rule-N"` (where N is the rung number).
- Record `state.json::decisions[i].taken = "source" | "target" | "both" | "target-fallback"`.
- Immediately invoke Stage 6.5 self-audit on the resolved hunk.

### unresolved.md Format

`.git/merge-conductor/<task>/unresolved.md` accumulates:

```markdown
## Unresolved hunk h-{{nn}}

**File**: {{file}}
**Symbol**: {{symbol_or_line_range}}
**Decision**: target taken as fallback; source preserved below.

### Source side (preserved)

```diff
{{source_hunk}}
```

### Target side (taken)

```diff
{{target_hunk}}
```

Surface in Phase 2 for user adjudication: keep target / take source / merge / free-form.
```

