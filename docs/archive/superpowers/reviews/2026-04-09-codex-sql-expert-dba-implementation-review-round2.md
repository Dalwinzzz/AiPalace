# SQL Expert DBA Implementation Review — Round 2

## Review Scope

- Target implementation: `plugins/sql-expert-dba`
- Target spec: `docs/superpowers/specs/2026-04-09-sql-expert-dba-design.md`
- Reviewed commit range: `770c14b..e39572f`
- Review goal:
  - verify whether the revised implementation now strictly follows the approved design
  - confirm that the previous high-priority review findings were actually closed
  - identify any remaining mismatches before the plugin can be considered spec-aligned

## Current Assessment

This revision is **substantially better** than the previous one.

The earlier major issues around:

- manifest structure
- Chinese duplicate detection
- indexed memory search
- missing test coverage

have been addressed to a meaningful degree.

However, this version is still **not yet strictly spec-complete**. The remaining issues are smaller than before, but they are still real spec mismatches and should be fixed before declaring the implementation fully aligned.

## Findings

### 1. `defaultPrompt` no longer matches the approved spec

**Severity:** Important  
**Files:**
- `plugins/sql-expert-dba/.codex-plugin/plugin.json`
- `docs/superpowers/specs/2026-04-09-sql-expert-dba-design.md`

**What is wrong**

The spec explicitly defines **three** starter prompts as the default entry set for the plugin:

1. optimize SQL
2. explain SQL errors
3. generate reporting/business SQL from requirements + schema

The current implementation now provides only a **single** `interface.defaultPrompt` value.

**Why it matters**

This is not a runtime blocker, but it is still a direct deviation from the approved product definition. The design intentionally used three prompts to expose the three highest-frequency entry paths.

Reducing this to one prompt weakens the expected plugin UX and means the implementation is still not a strict drop of the approved design.

**Required fix**

Restore the full three-prompt entry set in the manifest, using the schema-supported field shape.

## 2. Explicit memory capture behavior drifted away from the final approved design

**Severity:** Important  
**Files:**
- `plugins/sql-expert-dba/skills/_shared/memory-policy.md`
- `docs/superpowers/specs/2026-04-09-sql-expert-dba-design.md`

**What is wrong**

The final approved design changed explicit memory capture behavior to:

- default background evaluation still happens automatically
- when the user explicitly asks to preserve the result, the plugin **shows** the structured capture result
- explicit mode is about surfacing the capture result, not reintroducing a mandatory confirmation gate

The current shared memory policy says:

1. show the structured result
2. ask for user confirmation
3. only write after confirmation

That is a reversion from the final agreed design.

**Why it matters**

This reintroduces exactly the interaction friction that was intentionally removed during the design stage.

If ClaudeCode follows the shared policy literally, the runtime behavior will drift from the approved workflow model even though the memory scripts themselves are stronger now.

**Required fix**

Update the shared memory policy so it matches the final approved design:

- background capture remains automatic
- explicit mode surfaces the structured result
- explicit mode does not automatically imply a hard user-confirm-before-write gate

## 3. `memory_index.py --validate` does not validate the newly indexed search fields

**Severity:** Important  
**Files:**
- `plugins/sql-expert-dba/scripts/memory_index.py`

**What is wrong**

The index now correctly includes:

- `problem_pattern`
- `conclusion`

and `memory_search.py` now depends on them for pattern search.

However, `validate()` still only compares:

- `id`
- `title`
- `type`
- `workflow`
- `dialect`

It does **not** validate the consistency of:

- `problem_pattern`
- `conclusion`
- `tags`
- `review_status`

**Why it matters**

The implementation now depends on the index for more than identity metadata. But the validator still behaves as if the index only stores lightweight descriptors.

That means `index.json` can drift in search-relevant fields while `--validate` still reports:

```json
"consistent": true
```

This weakens the design goal of a reliable, governable, and internally consistent memory system.

**Evidence**

During review, manually corrupting an indexed `conclusion` value still allowed:

```bash
python3 plugins/sql-expert-dba/scripts/memory_index.py --memory-dir ... --validate
```

to report a clean consistency result.

**Required fix**

Expand validation coverage to include all fields that are now operationally meaningful for search and governance, especially:

- `problem_pattern`
- `conclusion`
- `tags`
- `review_status`

## 4. `__pycache__` artifacts are committed into the plugin source tree

**Severity:** Minor  
**Files:**
- `plugins/sql-expert-dba/scripts/__pycache__/...`

**What is wrong**

Compiled Python bytecode files are currently tracked in the plugin source tree.

**Why it matters**

This does not break functionality, but it pollutes the implementation artifact, increases repository noise, and makes the plugin less portable and less clean as a maintained source package.

**Required fix**

- remove tracked `__pycache__` files
- add appropriate ignore rules so they do not reappear in future iterations

## Assumptions

- This review is based on the revised implementation in commit range `770c14b..e39572f`.
- The previously reported high-priority issues around manifest structure, Chinese duplicate detection, indexed search coverage, and automated test coverage have been materially improved.
- The memory subsystem tests currently pass locally:

```bash
python3 plugins/sql-expert-dba/scripts/test_memory.py
```

- The memory index currently validates cleanly for the shipped sample data:

```bash
python3 plugins/sql-expert-dba/scripts/memory_index.py --memory-dir plugins/sql-expert-dba/memory --validate
```

- The Chinese search regression from the prior review is now fixed for the current sample memory:

```bash
python3 plugins/sql-expert-dba/scripts/memory_search.py --memory-dir plugins/sql-expert-dba/memory --pattern 全表扫描
```

- The primary remaining gaps are now **spec fidelity gaps**, not foundational architectural failures.

## Recommended Next Iteration

ClaudeCode should treat the next iteration as a **spec-tightening pass**, not a redesign pass.

Recommended order:

1. restore the full 3 starter prompts in the plugin manifest
2. align explicit memory capture wording and behavior with the final approved design
3. strengthen `memory_index.py --validate` so it covers all search-relevant indexed fields
4. remove committed `__pycache__` artifacts and add ignore rules

## Bottom Line

This revision is close, but it is **not yet a strict spec-complete implementation**.

The remaining issues are now concentrated and fixable. After the next iteration, the plugin should be re-reviewed with a narrow focus on:

- manifest prompt fidelity
- explicit memory lifecycle behavior
- full memory index validation coverage
- source tree cleanliness

