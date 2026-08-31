# SQL Expert DBA Implementation Review

## Review Scope

- Target implementation: `plugins/sql-expert-dba`
- Target spec: `docs/superpowers/specs/2026-04-09-sql-expert-dba-design.md`
- Reviewed commit range: `30754a4..8dd3201`
- Reviewer focus:
  - strict alignment with the approved design/spec
  - plugin manifest validity
  - workflow boundary fidelity
  - memory lifecycle correctness
  - safety defaults
  - implementation readiness for actual Codex usage

## Executive Summary

This implementation is **not yet strictly aligned** with the approved design/spec and should **not** be treated as spec-complete.

The largest blocker is the plugin manifest shape: it does not match the current Codex plugin manifest structure used by the local plugin scaffolding reference or by installed first-party plugins. That means the plugin may fail to load correctly even before the SQL workflows are exercised.

The second major gap is the `memory/` subsystem. The design promised a searchable, governable, low-pollution structured memory layer. The current implementation ships the files and scripts, but several core guarantees are not actually upheld:

- memory search can miss valid entries
- duplicate detection is weak for Chinese text
- auto-promotion to `approved` is looser than the spec allows
- there are no automated tests around the most failure-prone scripts

Because the primary users of this plugin are Chinese developers, the current whitespace-based duplicate detection and pattern matching design is especially problematic and should be redesigned with Chinese text handling as a first-class requirement.

## Findings

### 1. Plugin manifest shape does not match the current Codex plugin schema

**Severity:** Critical  
**Files:**
- `plugins/sql-expert-dba/.codex-plugin/plugin.json`
- `.codex/skills/.system/plugin-creator/references/plugin-json-spec.md`

**What is wrong**

The plugin manifest was implemented with a flattened top-level structure:

- `displayName`
- `shortDescription`
- `longDescription`
- `developerName`
- `category`
- `starterPrompts`
- `skills` as an array of file paths
- `scripts` as an array of file paths

This does **not** match the current plugin manifest structure used by the local scaffold reference or installed plugins. The current expected shape is:

- top-level `description`
- top-level `skills` as a relative path like `./skills/`
- optional top-level `apps`, `mcpServers`, `hooks`
- `interface` object for:
  - `displayName`
  - `shortDescription`
  - `longDescription`
  - `developerName`
  - `category`
  - `capabilities`
  - `defaultPrompt`
  - branding metadata

**Why it matters**

This is not a cosmetic mismatch. It can prevent Codex from recognizing and loading the plugin correctly, which makes the rest of the implementation irrelevant until fixed.

**Evidence**

- Current implementation:
  - `plugins/sql-expert-dba/.codex-plugin/plugin.json`
- Local reference:
  - `.codex/skills/.system/plugin-creator/references/plugin-json-spec.md`
- Installed plugin examples:
  - `.codex/plugins/cache/openai-curated/github/.../.codex-plugin/plugin.json`
  - `.codex/plugins/cache/openai-curated/notion/.../.codex-plugin/plugin.json`

**Required fix**

Rewrite `plugin.json` to follow the actual schema used by Codex plugins:

- add top-level `description`
- move UI/display metadata into `interface`
- replace the skill array with `skills: "./skills/"`
- move starter prompts into `interface.defaultPrompt`
- only declare optional top-level fields that are actually supported

## 2. `memory_search.py` drops searchable fields when it uses `index.json`

**Severity:** Important  
**Files:**
- `plugins/sql-expert-dba/scripts/memory_search.py`
- `plugins/sql-expert-dba/memory/index.json`
- `plugins/sql-expert-dba/memory/rules/rule-001-implicit-type-conversion.md`

**What is wrong**

`memory_search.py` claims that `--pattern` searches across:

- `title`
- `problem_pattern`
- `conclusion`
- `tags`

However, the fast path uses `index.json`, and the index only stores:

- `id`
- `title`
- `type`
- `workflow`
- `dialect`
- `tags`
- `review_status`
- `file`

So when search runs through the index, it cannot see `problem_pattern` or `conclusion` at all.

**Why it matters**

This breaks one of the core promises of the design: the workflows are supposed to retrieve relevant memory efficiently and reliably. In practice, approved entries can become partially undiscoverable.

**Reproduction**

This command returned `[]` during review:

```bash
python3 plugins/sql-expert-dba/scripts/memory_search.py \
  --memory-dir plugins/sql-expert-dba/memory \
  --pattern 全表扫描
```

But the phrase appears in the `conclusion` of:

- `plugins/sql-expert-dba/memory/rules/rule-001-implicit-type-conversion.md`

**Required fix**

Choose one of these designs:

1. Expand `index.json` to include searchable fields such as:
   - `problem_pattern`
   - `conclusion`
   - optionally a normalized `search_text`
2. Or, if `--pattern` is used, bypass the index and scan files directly

If performance matters, prefer a normalized indexed search field rather than keeping the index minimal and incorrect.

## 3. `memory_capture.py` duplicate detection is effectively broken for Chinese text

**Severity:** Important  
**Files:**
- `plugins/sql-expert-dba/scripts/memory_capture.py`

**What is wrong**

Duplicate detection uses:

```python
target_words = set(problem_pattern.lower().split())
```

This assumes whitespace-separated tokens. That is a poor fit for Chinese text, where problem patterns are often written without spaces.

If the pattern becomes a single token, this guard disables duplicate detection entirely:

```python
if len(target_words) < 2:
    return False
```

**Why it matters**

This plugin is primarily intended for Chinese developers. In that environment, duplicate detection and memory pollution control must be Chinese-aware by design, not as an afterthought.

Right now, repeated Chinese entries can silently accumulate in `candidate` or `approved`, which directly undermines the spec’s memory governance goals.

**Reproduction**

Using a temporary memory directory, two entries with the exact same Chinese `problem_pattern` were both captured successfully:

- `统计口径不一致导致重复计数`
- `统计口径不一致导致重复计数`

No duplicate was detected.

**Required fix**

Redesign duplicate detection for Chinese-first usage. Good options include:

- normalized CJK-aware tokenization
- character bigrams or trigrams
- normalized substring similarity
- edit-distance / fuzzy matching over normalized fields
- combining structured keys:
  - `workflow`
  - `dialect`
  - `problem_pattern`
  - `conclusion`

At minimum, avoid using whitespace tokenization as the primary dedupe strategy for Chinese text.

## 4. Auto-promotion to `approved` is looser than the spec allows

**Severity:** Important  
**Files:**
- `plugins/sql-expert-dba/scripts/memory_capture.py`
- `docs/superpowers/specs/2026-04-09-sql-expert-dba-design.md`

**What is wrong**

The current implementation promotes an entry directly to `approved` whenever:

- `confidence == "high"`
- and `type in ("rule", "template", "glossary")`

That is much broader than the spec.

The spec only allows direct auto-approval for a constrained subset of memory:

- high-universality rules
- stable error patterns
- high-reuse templates
- clear cross-dialect rules
- general optimization rules

Everything else should default to `candidate`.

**Why it matters**

The current implementation effectively treats “high confidence” as “safe for formal memory,” which is not the same thing. Business-specific or under-validated content can be promoted too early.

That weakens the memory governance model that was central to the design.

**Required fix**

Encode the actual approval policy from the spec, not just confidence + type.

For example:

- add an explicit classification or promotion reason
- only auto-approve when the captured entry matches one of the allowed categories
- otherwise route to `candidate`

## 5. The memory subsystem has no automated tests

**Severity:** Important  
**Files:**
- `plugins/sql-expert-dba/scripts/memory_capture.py`
- `plugins/sql-expert-dba/scripts/memory_search.py`
- `plugins/sql-expert-dba/scripts/memory_index.py`

**What is wrong**

There are no tests for the three scripts that define the behavior of the structured memory system.

**Why it matters**

This subsystem is doing non-trivial work:

- front matter parsing
- indexing
- search behavior
- duplicate detection
- status routing
- approved/candidate governance

The review already surfaced reproducible bugs in search and dedupe. Without tests, those regressions will keep recurring.

**Required fix**

Add automated tests for at least:

- index rebuild vs validate consistency
- pattern search through the index
- pattern search through the scan fallback
- Chinese duplicate detection behavior
- approved vs candidate routing policy
- malformed or incomplete front matter handling

## Conclusion

This implementation is **not yet compliant enough** to be considered a strict spec-grounded delivery.

The plugin currently has the right high-level file layout and the right conceptual direction, but two design-critical areas are still not actually reliable:

1. **Plugin loading contract**  
   The manifest shape must be corrected first, otherwise the plugin may not be usable in Codex at all.

2. **Memory governance contract**  
   The current implementation does not yet fully satisfy the design goals of:
   - discoverability
   - deduplication
   - safe routing into `candidate` vs `approved`
   - low-noise memory accumulation for Chinese-language usage

## Recommended Next Iteration Order

1. Fix the manifest so the plugin follows the real Codex plugin schema
2. Fix indexed search so memory retrieval is complete and predictable
3. Redesign duplicate detection for Chinese-first usage
4. Tighten `approved` routing to match the spec exactly
5. Add automated tests around the memory subsystem
6. Only then treat the plugin as a stable spec-aligned implementation

## Notes for ClaudeCode

Please treat Chinese developer usage as a first-class requirement in the next iteration.

Specifically:

- do not rely on whitespace tokenization for duplicate detection
- do not assume English keyword search behavior
- prefer normalized CJK-aware matching strategies
- make search and dedupe robust for Chinese business terminology, metric names, and problem patterns

This is not a localization detail. It affects the correctness of the plugin’s core memory system.

## Appendix A — Review Cleanup Diff

The following diff is **not part of the implementation findings**. It is included only as reference for the temporary review artifact that was created and then removed during this review process.

### A.1 Exact diff for `memory/index.json`

```diff
diff --git a/plugins/sql-expert-dba/memory/index.json b/plugins/sql-expert-dba/memory/index.json
index 81fd019..50da114 100644
--- a/plugins/sql-expert-dba/memory/index.json
+++ b/plugins/sql-expert-dba/memory/index.json
@@ -45,7 +45,17 @@
       ],
       "review_status": "approved",
       "file": "templates/template-001-daily-statistics.md"
+    },
+    {
+      "id": "case-b42e4a",
+      "title": "test",
+      "type": "case",
+      "workflow": "sql-schema-reviewer",
+      "dialect": "universal",
+      "tags": [],
+      "review_status": "candidate",
+      "file": "candidates/case-b42e4a-test.md"
     }
   ],
-  "last_updated": "2026-04-09T01:21:37.524574+00:00"
+  "last_updated": "2026-04-09T07:58:36.228089+00:00"
 }
```

### A.2 Reference diff for the transient candidate file deletion

This file was a temporary review-generated candidate and was removed immediately. Because it was untracked and then deleted, Git does not retain a normal historical patch for it. The snippet below is a **reference deletion diff** for ClaudeCode, not a Git-extracted canonical patch.

```diff
diff --git a/plugins/sql-expert-dba/memory/candidates/case-b42e4a-test.md b/plugins/sql-expert-dba/memory/candidates/case-b42e4a-test.md
deleted file mode 100644
--- a/plugins/sql-expert-dba/memory/candidates/case-b42e4a-test.md
+++ /dev/null
@@ -1,0 +0,0 @@
- [temporary review-generated candidate memory entry removed]
```

