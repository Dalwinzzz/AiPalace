# SQL Expert DBA v2 Design

## 1. Summary

SQL Expert DBA v2 upgrades the current SQL assistant from a mostly skill-driven plugin into a persistent, context-aware DBA helper. The main goal is to fix the v1 memory gap: the plugin had memory files and scripts, but no reliable runtime path that caused real SQL knowledge to be captured during normal use.

v2 keeps the existing five expert workflows:

- `sql-expert-router`
- `sql-query-optimizer`
- `sql-error-diagnostician`
- `sql-schema-reviewer`
- `sql-report-query-builder`

v2 adds three data capabilities:

- A portable, user-level global SQL memory for cross-project reusable knowledge.
- A project-level `./sql/` database context layer for local DDL, schema dumps, EXPLAIN output, slow SQL logs, and notes.
- A project-level `./sql/biz-rules/` rule base for business metrics, field semantics, report rules, and table relationships.

The plugin still does not connect to databases or execute SQL in v2.

## 2. Goals

- Make explicit memory capture reliable when the user says "记下来", "沉淀", "复盘", or similar phrases.
- Add guarded background memory capture through Codex Hook / Automation when enough context is available.
- Ensure automatic capture never writes directly to approved global memory.
- Move runtime memory away from plugin cache or plugin package directories.
- Let projects provide database context through `./sql/` files without requiring a live database connection.
- Let project-specific business SQL rules accumulate under `./sql/biz-rules/`.
- Keep project-specific rules faithful to real table names, field names, and business semantics.
- Ensure cross-project global memory is sanitized and abstracted.
- Preserve the v1 expert workflow structure while giving each workflow access to global memory, project context, and business rules.

## 3. Non-Goals

- Do not connect to online or local databases.
- Do not execute SQL.
- Do not add a full MCP server in v2.
- Do not rely on plugin installation cache as a durable knowledge store.
- Do not write project table names, field names, or private business semantics into global memory.
- Do not silently modify Git index during background capture.
- Do not turn memory scripts into SQL reasoning engines.

## 4. Architecture

v2 uses a layered data model.

### 4.1 Plugin Seed Memory

Location: plugin package `memory/`

Purpose:

- Ship stable, generic SQL rules, templates, and glossary entries.
- Act as seed knowledge for all users.
- Remain versioned with the plugin implementation.

This layer is not the runtime source of truth for new user knowledge.

### 4.2 User-Level Global SQL Memory

Location is resolved at runtime. No absolute user path is hardcoded.

Default resolution order:

1. `$SQL_EXPERT_DBA_MEMORY_DIR`
2. `$CODEX_HOME/memories/sql-expert-dba/`
3. `~/.codex/memories/sql-expert-dba/`

Purpose:

- Store cross-project reusable SQL knowledge.
- Store explicit captures as approved entries when validation passes.
- Store background captures as candidates only.

Global memory must be sanitized before write. It cannot retain concrete project table names, field names, tenant identifiers, private metric names, raw business data, or long conversation text.

Expected structure:

```text
sql-expert-dba/
  approved/
    rules/
    cases/
    templates/
    glossary/
  candidates/
    rules/
    cases/
    templates/
    glossary/
  index.json
  capture-log.jsonl
```

### 4.3 Project SQL Directory

Location: current workspace `./sql/`

Purpose:

- Provide project-local database context.
- Store DDL, schema dumps, EXPLAIN output, slow SQL logs, and notes.
- Store project-specific business SQL rules.

Default readable file types:

- `.sql`
- `.ddl`
- `.explain`
- `.log`
- `.txt`
- `.md`

The plugin ignores binary files, compressed files, images, unknown file extensions, and hidden directories except `./sql/.index/`.

### 4.4 Project SQL Index

Location: `./sql/.index/`

Purpose:

- Cache project SQL context so every workflow does not need to scan all files.
- Determine whether project context is sufficient for a workflow.
- Provide table, field, index, EXPLAIN, and slow SQL lookup.

Expected structure:

```text
sql/
  .index/
    file-digests.json
    context-index.json
    table-index.json
```

### 4.5 Project Business Rules

Location: `./sql/biz-rules/`

Purpose:

- Store project-specific metric definitions, field semantics, table relationships, report templates, exclusion rules, and reconciliation rules.
- Preserve real table names, field names, and business semantics because these rules only serve the current project.

Expected structure:

```text
sql/
  biz-rules/
    table-index.json
    module-index.json
    order/
      daily-statistics.md
      refund-reconciliation.md
    user/
      active-user-definition.md
    uncategorized/
```

## 5. Memory Lifecycle

v2 has three separate capture paths.

### 5.1 Explicit Global Memory Capture

Triggered when the user explicitly asks to preserve knowledge. Trigger phrases include:

- "记下来"
- "沉淀"
- "复盘"
- "保存这个经验"
- "这个值得沉淀"

Process:

1. Collect the current SQL problem, conclusion, workflow type, dialect, evidence, and boundaries.
2. Decide whether the result is global SQL knowledge or project-specific business knowledge.
3. If global, sanitize and abstract project-specific details.
4. Run duplicate detection.
5. Write to user-level global `approved/` by default.
6. Downgrade to `candidates/` if evidence is weak, boundaries are unclear, sanitization fails, or duplicates conflict.
7. Update global memory index.

Explicit capture may write approved global memory because the user intentionally requested persistence.

### 5.2 Background Global Memory Capture

Triggered through Codex Hook / Automation when available.

The background runner must first detect whether enough context is available. Minimum required context:

- User input containing SQL, DDL, EXPLAIN, an error message, or a business SQL requirement.
- Final assistant conclusion.
- Workflow type.
- Timestamp or source event metadata.

Rules:

- If context is insufficient, skip capture.
- Skipping must not create a memory entry.
- Background capture writes only to user-level global `candidates/`.
- Background capture never writes to global `approved/`.
- Background capture must sanitize and abstract project-specific details before writing global memory.
- Background capture must not silently modify Git index.

This section applies to global memory only. Project business rule capture has its own stricter project-context requirements in Section 5.3.

### 5.3 Project Business Rule Capture

Triggered after business SQL generation, complex report SQL, reconciliation SQL, schema review, or explicit user request when the result contains reusable project business knowledge.

Examples:

- Metric definition: "paid order count uses `orders.paid_at` and `orders.status = 'paid'`."
- Field semantics: "`orders.pay_amount` means actual paid amount."
- Table relationship: "`orders.user_id` references `users.id`."
- Report template: daily GMV, order count, and paying user count.
- Exclusion rule: cancelled orders and test channels are excluded by default.

Rules:

- Write to `./sql/biz-rules/`.
- Preserve real project table names, field names, and business wording.
- Update `table-index.json` and `module-index.json`.
- Do not write project-specific business rules into global memory unless the user explicitly requests export and the rule is sanitized first.
- Automatic project rule capture is allowed only when Hook / Automation context includes current workspace, business module, related tables, final rule conclusion, and source workflow.
- If any required project rule context is missing, skip project rule capture.
- Automatic project rule capture may update `./sql/biz-rules/` and its indexes, but must not silently untrack files from Git.

## 6. Project SQL Context Indexing

The project context helper reads only `./sql/`.

Suggested directory layout:

```text
sql/
  ddl/
    schema.sql
    tables/
  explain/
    slow-query-001.explain
  slow-logs/
    mysql-slow.log
  notes/
    schema-notes.md
  .index/
    context-index.json
    table-index.json
    file-digests.json
  biz-rules/
    table-index.json
    module-index.json
```

### 6.1 `file-digests.json`

Stores:

- Relative path.
- Modification time.
- Size.
- Hash.

Used to determine whether indexes are stale.

### 6.2 `context-index.json`

Stores:

- Indexed file list.
- Inferred dialect.
- DDL coverage summary.
- EXPLAIN file list.
- Slow SQL file list.
- Notes file list.
- Last indexed timestamp.
- Index version.

### 6.3 `table-index.json`

Stores:

- Table names.
- Columns.
- Primary keys.
- Index definitions.
- Foreign keys or inferred relationships.
- Source files.
- Related EXPLAIN files.
- Related slow SQL files.

### 6.4 Index Build Rules

- Workflow start checks `./sql/.index/`.
- If index files are missing or file digests changed, rebuild the index.
- If the environment cannot write `./sql/.index/`, perform a temporary scan without persisting the index.
- If `./sql/` does not exist, project context is disabled for that task.
- If `./sql/` is large, use the index first and only load relevant source snippets.

## 7. Project Business Rules

Business rules use Markdown with YAML front matter.

Example:

```yaml
---
id: biz-rule-xxxx
title: paid order daily statistics
module: order
tables: [orders, order_items, users]
fields: [orders.paid_at, orders.status, orders.pay_amount]
rule_type: metric_definition
source_workflow: sql-report-query-builder
capture_mode: explicit_user_requested
confidence: high
review_status: approved
last_reviewed_at: "2026-05-08"
---
```

Supported `rule_type` values:

- `metric_definition`
- `field_semantics`
- `table_relationship`
- `report_template`
- `exclusion_rule`
- `reconciliation_rule`

### 7.1 Organization

- Rule body files are stored by business module.
- Unknown modules go to `uncategorized/`.
- `table-index.json` maps tables to rule files.
- `module-index.json` maps modules to rule files.

### 7.2 Deduplication And Conflicts

- Same `module + rule_type + tables + normalized title` indicates a likely duplicate.
- Same field semantics for the same table field should merge into the existing rule when compatible.
- Conflicting metric definitions must not overwrite existing rules.
- Conflicts should be recorded or surfaced for user confirmation.

### 7.3 Git Policy

`./sql/biz-rules/` does not need to be tracked by Git.

After writing a business rule:

1. Check the current workspace `.gitignore`.
2. If missing, add:

```gitignore
/sql/biz-rules/
```

3. Check whether `sql/biz-rules` is tracked by Git.
4. If it is tracked, `git rm --cached -r sql/biz-rules` may be used to untrack it while keeping files in the working tree.
5. Untracking is a Git index change and must require explicit user authorization or an explicit governance command.
6. Background capture must not silently run `git rm --cached`.

## 8. Runtime Components

Scripts perform storage, indexing, search, deduplication, and governance. They do not replace model reasoning.

### 8.1 Existing Scripts To Update

`memory_search.py`

- Search plugin seed memory and user-level global memory.
- Default to approved entries.
- Support candidates only when explicitly requested.

`memory_capture.py`

- Write user-level global memory by default.
- Support `capture_mode` values:
  - `explicit_user_requested`
  - `auto_hook`
  - `auto_automation`
- Explicit capture can write approved entries.
- Auto capture is forced to candidate.

`memory_index.py`

- Build and validate user-level global memory indexes.
- Validate plugin seed memory indexes.

### 8.2 New Scripts

`paths.py`

- Resolve plugin directory.
- Resolve user-level memory directory.
- Resolve current project `./sql/`.
- Resolve current project `./sql/biz-rules/`.
- Avoid hardcoded user paths.

`project_context_index.py`

- Scan supported files under `./sql/`.
- Extract table names, columns, indexes, keys, inferred relationships, EXPLAIN features, and slow SQL features.
- Maintain `file-digests.json`, `context-index.json`, and `table-index.json`.

`project_context_search.py`

- Retrieve relevant project context by table, field, workflow, or keyword.
- Prefer indexes and load source snippets only when needed.

`biz_rules_capture.py`

- Write project business rules.
- Maintain front matter.
- Update `table-index.json` and `module-index.json`.
- Detect duplicates and conflicts.

`biz_rules_search.py`

- Search rules by module, table, field, rule type, or keyword.

`biz_rules_git_guard.py`

- Maintain `.gitignore`.
- Detect whether `sql/biz-rules` is tracked.
- Only untrack with explicit authorization or explicit governance command.

`auto_memory_runner.py`

- Act as the Hook / Automation entrypoint.
- Read Codex-provided recent context when available.
- Check context sufficiency.
- Skip when context is insufficient.
- Write only user-level global candidates during automatic global memory capture.
- Trigger project business rule capture only when project rule context is complete.

## 9. Workflow Integration

### 9.1 `sql-expert-router`

- Search user-level approved memory at the start of SQL tasks.
- Detect whether current workspace has `./sql/`.
- Build or validate `./sql/.index/` when useful.
- Identify related tables, fields, and modules.
- Decide whether `biz-rules` should be loaded.

### 9.2 `sql-query-optimizer`

- Use project `table-index.json` for related DDL, indexes, slow SQL, and EXPLAIN files.
- Distinguish facts from user input and facts from project context.
- Allow explicit global memory capture for reusable optimization lessons.
- Allow background capture only into global candidates.

### 9.3 `sql-error-diagnostician`

- Search project context when errors mention tables, fields, constraints, indexes, or SQLSTATE/error codes.
- Capture stable error patterns into global memory when sanitized.
- Keep project-specific constraint meanings in project rules or project notes, not global memory.

### 9.4 `sql-schema-reviewer`

- Compare submitted DDL against existing `./sql/` schema context when present.
- Capture cross-project modeling rules into global memory.
- Capture project field semantics and table relationships into `biz-rules`.

### 9.5 `sql-report-query-builder`

- Before generating SQL, search:
  - Project SQL `table-index.json`
  - `biz-rules/table-index.json`
  - `biz-rules/module-index.json`
- Reuse existing metric definitions and business rules.
- If rules conflict, stop before final SQL generation and ask the user to resolve the conflict.
- After generating or refining business SQL, evaluate whether new project rules should be captured.
- Export reusable report patterns to global memory only after sanitization.

## 10. Output Contract Changes

The v1 six-section output structure remains the default:

1. Task judgment.
2. Confirmed facts.
3. Unknowns and assumptions.
4. Main output.
5. Verification suggestions.
6. Optional learning notes.

v2 adds optional sections when relevant:

- `使用的项目上下文`
- `命中的业务规则`
- `沉淀结果`

These sections should be concise. They should not turn normal SQL answers into long audit logs.

## 11. Safety And Privacy

- Project context and `biz-rules` preserve real project semantics because they are project-local.
- Global memory must be sanitized and abstracted.
- Automatic capture is candidate-only.
- Approved global memory requires explicit user intent or later promotion.
- Context insufficiency causes skip, not speculative capture.
- Git index changes require explicit authorization.
- No SQL execution is introduced.

## 12. Testing Plan

Path resolution:

- `$SQL_EXPERT_DBA_MEMORY_DIR` overrides all defaults.
- `$CODEX_HOME/memories/sql-expert-dba/` is used when `CODEX_HOME` exists.
- `~/.codex/memories/sql-expert-dba/` is used as fallback.
- No tests depend on a specific username.

Global memory:

- Explicit capture writes approved when evidence, boundaries, deduplication, and sanitization pass.
- Explicit capture downgrades to candidate when boundaries are unclear.
- Auto capture always writes candidate.
- Auto capture skips when required context fields are missing.
- Global memory rejects unsanitized project table names and field names.
- Chinese duplicate detection works for similar problem patterns.

Project context:

- Supported file types are indexed.
- Unsupported file types are ignored.
- Digest changes trigger reindexing.
- Table, field, index, EXPLAIN, and slow SQL features are extracted.
- Large `./sql/` directories use indexes and relevant snippets.

Business rules:

- `biz_rules_capture.py` writes module-based Markdown rules.
- `table-index.json` maps tables to rules.
- `module-index.json` maps modules to rules.
- Duplicate rules are detected.
- Conflicting metric rules are not overwritten.
- Chinese titles and business terms are handled correctly.

Git guard:

- Missing `/sql/biz-rules/` ignore rule is added to `.gitignore`.
- Tracked `sql/biz-rules` is detected.
- `git rm --cached -r sql/biz-rules` is not executed in background mode.
- Untracking requires explicit authorization or explicit governance command.

Workflow integration:

- Query optimization uses project indexes when table names match.
- Business SQL generation reuses existing `biz-rules`.
- Conflicting business rules stop final SQL generation.
- Outputs identify project context and business rule sources when used.

## 13. Acceptance Criteria

- A user can explicitly say "记下来" and get a persisted structured memory entry.
- The global memory path is portable and contains no hardcoded absolute user path.
- Background capture skips safely when context is insufficient.
- Background capture writes only user-level global candidates when context is sufficient.
- Plugin seed memory remains readable as built-in knowledge.
- `./sql/` can be indexed into `./sql/.index/`.
- Project SQL tasks can use indexed DDL, indexes, EXPLAIN, and slow SQL context.
- Business SQL generation can read and reuse `./sql/biz-rules/`.
- New project business rules can be written and indexed by module and table.
- `./sql/biz-rules/` is ignored by Git.
- Already tracked `sql/biz-rules` can be untracked only through explicit authorization.
- Existing v1 workflows continue to work when no `./sql/` directory exists.

## 14. Implementation Order Recommendation

1. Add portable path resolution.
2. Refactor global memory search, capture, and indexing around user-level memory.
3. Add explicit capture behavior and tests.
4. Add auto memory runner with context sufficiency checks and candidate-only writes.
5. Add project context indexing and search.
6. Add `biz-rules` capture, search, indexes, and Git guard.
7. Update skill documents and output contracts.
8. Add integration tests and Chinese-language regression cases.
