thread_id: 019db450-50c4-7b03-86dd-98747e2aabe2
updated_at: 2026-07-03T09:06:40+00:00
rollout_path: /Users/dalwin/.codex/sessions/2026/04/22/rollout-2026-04-22T16-30-55-019db450-50c4-7b03-86dd-98747e2aabe2.jsonl
cwd: /Users/dalwin/.codex/worktrees/6308/skcnursery/skc-nursery
git_branch: release/eeds-20260416

# Production data repair for 鄂尔多斯 nursery total-capacity bug

Rollout context: The user asked for a review / repair-oriented SQL DBA analysis on the `skc-nursery` repo, focused on the 鄂尔多斯 production issue where a nursery’s profile total capacity showed 0. The work combined code review of a fix commit (`0a6ac6a3`) and a production-only read-only verification / repair SQL for Kingbase.

## Task 1: Review the class-capacity regression and produce a safe repair SQL

Outcome: partial

Preference signals:
- The user’s request was explicit about using the SQL DBA route and producing a repair-oriented answer, which suggests future similar DB investigations should default to code+data cross-checking and then emit a ready-to-execute repair SQL rather than only a narrative diagnosis.
- The environment rules / local database guidance were reinforced during the rollout: the agent treated the database as read-only, and when it needed to change data it generated SQL for manual execution instead of trying to write directly. That aligns with a future default of “query first, then hand off a guarded SQL patch.”

Key steps:
- Read the SQL expert router and report-query-builder skill docs, plus the local read-only DB CLI notes.
- Identified the relevant code fix in `0a6ac6a3` (`NurseryClassDisplaySupport.computeOrderedTypes`) and the associated regression report in `60b8ec1d`.
- Confirmed via production read-only `dbq` that the affected nursery is `skcity.nursery.id=111824` (`乌兰镇托育照护服务中心`) and that the live data still had `scope=0`, `class_types=3`, `class_num=0`, `class_scope=0`.
- Confirmed the formal class tables for `111824` actually sum to `type4=10班 / 200托位`, and the latest passing audit snapshot reflects `class_types=4, scope=200, class_num=10`.
- Ran a full mismatch scan and found 4 affected nurseries, but only `111824` had the complete evidence chain for this ticket; the others were left out of the repair scope.
- Built a Kingbase repair SQL using a CTE + `FULL JOIN` / `ROW_NUMBER()`-style latest-row selection pattern, with `FOR UPDATE` precheck and a guarded `UPDATE ... FROM fixed` to restore `class_types=4, class_num=10, class_scope=200, scope=200`.

Failures and how to do differently:
- The first production query attempted to select `record_class_num`, but the 鄂尔多斯 `nursery` table does not have that column. The agent recovered by checking `information_schema.columns` and then constrained the repair SQL to real columns only.
- One audit-info query also failed because the local entity fields did not match the production table (`class_scope` missing there). Future similar runs should inspect actual production columns before composing cross-table validation queries.
- The production tunnel initially errored with `Operation not permitted`; the agent then retried using the allowed `dbq` flow with escalation. For similar cases, start with `dbq --list` / instance confirmation, then use the sanctioned read-only path directly.

Reusable knowledge:
- For this repository, `NurseryClassDisplaySupport` drives both the nursery profile card and the main nursery summary through `buildFormalClassLimitSnapshot()`, so a stale snapshot bug can corrupt both display and persisted summary values.
- The code fix in `0a6ac6a3` is the right prevention layer: `computeOrderedTypes()` now keeps only effective class types and prevents old snapshot order from filtering out currently-valid class type 4 data.
- The production bug here was not just a display issue; `refreshNurseryClassSummary()` had already persisted the wrong derived values into `nursery`, so historical data required a one-time backfill even after code was fixed.
- The exact mismatch pattern for the target nursery was: `nursery.scope=0` while the class-scope table summed to `200` (`type4` only).

References:
- [1] Code fix commit: `0a6ac6a32` — `fix(nursery): 修复机构变更编班类型后画像总托位数被算成0`
- [2] Regression report commit: `60b8ec1d6` — `docs(nursery): 补充鄂尔多斯机构画像总托位数为0排查报告`
- [3] Production evidence for target nursery:
  - `skcity.nursery WHERE id = 111824` → `scope=0, class_types=3, class_num=0, class_scope=0`
  - `skcity.nursery_class_limit` / `skcity.nursery_class_scope_limit` → `type4=10 / 200`, others 0
  - latest passing audit rows: `1313` (`class_types=4, scope=200`) and `1310` (`class_types=3, scope=200`)
- [4] Derived repair result check for `111824` returned `fixed_class_types=4`, `fixed_class_num=10`, `fixed_class_scope=200`, `fixed_scope=200`
- [5] `dbq --list` confirmed the usable production instance name is `鄂尔多斯-正式`; all production verification was done through `/Users/dalwin/Library/ConfigFile/db/dbq` only
