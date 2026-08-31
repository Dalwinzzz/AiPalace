# Semantic Mapping (Stage 5.5)

> Internal reference for SKILL.md Stage 5.5. Triggered only when a refactored
> target is suspected and decisions exist that may be misaligned with the
> target's current layout.

## Trigger

Run Stage 5.5 only if any of:

- `mode == backport`
- `mode == rebase-onto`
- `evidence.refactor_signals_in_target == true` (from Stage 2 mode-inference)
- User explicitly enabled in Stage 2 config

For each C/D class decision in the queue, run the search strategy below and attach mapping metadata.

## Goal

For each conflict hunk on the source side, find "the refactored counterpart" of the source-side modified symbols in the target branch. Use this counterpart to:

1. Inform the user where on the target the change should land (file + symbol)
2. Pre-generate candidate options [3] (source-first) and [4] (target-first) rewritten on the target's location
3. Surface mapping evidence so the user can verify the model's interpretation

## Search Strategy

For each conflict hunk, extract the source-side modified symbols and run candidate searches.

### 1. Extract source-side modified symbols

For each hunk, identify:

- **Methods / functions**: name + signature (param list + return type if statically typed)
- **Classes / types**: name + key members
- **Top-level constants**: name + value
- **Imports**: added or removed deps

Use `git diff -W --function-context` to get function-level surrounding lines, then identify the changed symbol(s).

### 2. For each symbol, run candidate searches (in order; stop on first high-confidence match)

#### Search A — Direct grep on target HEAD

```bash
git grep -n "<symbol_name>" -- '*.{ext}'
```

If found and the location matches the source-side semantic (e.g., same call sites), high confidence.

#### Search B — Rename trail (same file)

```bash
git log --all --follow --diff-filter=R -- <original_file_path>
```

If git followed a rename, find the new path and re-run Search A on the new path.

#### Search C — Cross-file rename detection

```bash
git log --all --diff-filter=R --find-renames=70%
```

Search for files in the target that share ≥ 70% similarity with source-side modified files but exist at a different path.

#### Search D — Similar-signature heuristic (model judgment)

If A/B/C don't find a counterpart, use model reasoning:

- Look for methods in the target with the same param types and return type within neighboring files (proximity by directory)
- Inspect the source's caller chain: where was the source method called? Find the same caller in the target and inspect what it now calls — that downstream method is likely the counterpart.

### 3. Score mapping confidence

| Confidence | Criteria |
|---|---|
| **high** | Search A direct hit AND signature unchanged AND same calling context |
| **medium** | Search B/C rename trail follows; signature similar but changed; OR Search D produces a single unambiguous candidate |
| **low** | Search D yields multiple candidates OR no good match — present as low and warn the user |

### 4. Generate candidate options for the decision point

For high/medium confidence, pre-build the [3] and [4] candidate options rewritten on the target's location:

- **[3] source-first-then-target**: Take the source-side change semantics and apply them on the target's counterpart, then layer the target's own changes after
- **[4] target-first-then-source**: Inverse order

For low confidence, do NOT pre-build; instead surface the search results to the user and ask them to pick a counterpart or skip.

## Output Format (v2)

After running the search procedures, emit a `target_location` array on the
graft entry in `grafting-plan.yaml`:

```yaml
target_location:
  - file: <target_file>
    symbol: <target_symbol>            # may be null for add-new
    confidence: high | medium | low
    evidence:
      - "git grep '<symbol>' returned <N> hits in <file>"
      - "git log --diff-filter=R found rename: <old> → <new>"
      - "<your judgment summary in 1 line>"
```

For `confidence`:
- **high**: exact symbol match OR clean rename trail
- **medium**: signature/semantic match but renamed/moved with non-trivial drift
- **low**: heuristic match with weak evidence; Stage 4t MUST set
  `graft_strategy != replace` for low-confidence locations

Per-task `target_location` arrays go into `grafting-plan.yaml::plan[i]` rather
than `state.json::decisions[i].semantic_mapping` (the v1 field is deprecated
for transplant-pipeline).

## Low-Confidence Handling

When confidence is low:

- Still present the mapping in the decision point, but mark it with `⚠ 映射置信度低，请人工校验`
- Do NOT pre-build options [3]/[4]; just list the candidate target locations
- Encourage the user to use `[5] 自由输入` to describe the intended merge, OR `[s]` to skip and revisit later

## Cost Control

Stage 5.5 should not exceed ~30s of git operations per decision. If a search becomes pathological (e.g., very large repos), fall back to low confidence rather than timeout.
