# State Schema

> Internal reference for `<repo>/.git/merge-conductor/<task>/state.json` —
> the machine-readable state persisted across the pipeline.

## Purpose

`state.json` is the single source of truth for pipeline state. It enables:

- Resume after interruption (terminal closed, pause via `[p]`)
- Recovery after git errors (roll back to backup tag, re-enter at known stage)
- Audit trail (who chose what at which decision point)
- Cleanup decisions (which sessions are finalized + when)

## Location

`<repo>/.git/merge-conductor/<task-name>/state.json`

The directory is inside `.git/` so it is **not tracked**, **not committed**, and **not in `git status` output**.

## Schema

```json
{
  "version": "2.0",
  "task_name": "promo-vip-backport",
  "mode": "backport-transplant",
  "pipeline": "transplant",
  "created_at": "2026-05-12T14:00:00+08:00",
  "paused_at": null,
  "finalized_at": null,
  "status": "in-progress",
  "iter": 1,
  "iterations": [
    {
      "iter": 1,
      "started_at": "2026-05-12T14:00:00+08:00",
      "trigger": "initial",
      "ended_at": null,
      "user_feedback": null
    }
  ],
  "source": {
    "type": "branch",
    "ref": "feature/promo-v2",
    "sha": "a1b2c3d",
    "merge_base_with_target": "x0y0z0w"
  },
  "target": {
    "branch": "develop",
    "head_sha": "x9y8z7w",
    "base_sha": "x9y8z7w"
  },
  "working_branch": {
    "name": "merge/promo-vip-backport",
    "worktree_path": "/Users/.../worktrees/promo-vip-backport",
    "use_worktree": true
  },
  "stage": 6,
  "stage_kind": "6t",
  "stage_history": [
    {
      "stage": 0,
      "kind": "0",
      "tag": null,
      "completed_at": "2026-05-12T14:01:00+08:00"
    },
    {
      "stage": 1,
      "kind": "1",
      "tag": null,
      "completed_at": "2026-05-12T14:02:00+08:00"
    },
    {
      "stage": 2,
      "kind": "2",
      "tag": null,
      "completed_at": "2026-05-12T14:04:00+08:00"
    },
    {
      "stage": 3,
      "kind": "3",
      "tag": "merge/promo-vip-backport/before-step-3",
      "completed_at": "2026-05-12T14:05:00+08:00"
    },
    {
      "stage": 4,
      "kind": "4t",
      "tag": "merge/promo-vip-backport/before-step-4",
      "completed_at": "2026-05-12T14:08:00+08:00"
    }
  ],
  "requirements": [],
  "global_out_of_scope": [],
  "grafts": [],
  "decisions": [
    {
      "id": 1,
      "file": "src/service/OrderService.java",
      "symbol": "calcDiscount",
      "class": "C",
      "d_subclass": null,
      "status": "resolved",
      "choice": 3,
      "free_text": null,
      "model_recommendation": 3,
      "semantic_mapping": {
        "mapped_to": "DiscountStrategy.apply",
        "mapped_to_file": "src/strategy/DiscountStrategy.java",
        "confidence": "high",
        "evidence": "renamed in commit f0e1d2c"
      },
      "resolved_at": "2026-05-12T14:15:00+08:00"
    },
    {
      "id": 2,
      "file": "src/controller/OrderController.java",
      "symbol": "create",
      "class": "C",
      "status": "skipped",
      "skip_reason": "deferred to end"
    }
  ],
  "audit": [
    {
      "unit_id": "G-01",
      "unit_kind": "graft",
      "result": "pass",
      "violations": [],
      "action": "applied",
      "audited_at": "2026-05-12T14:18:00+08:00"
    }
  ],
  "unresolved": [],
  "auto_resolved_summary": {
    "A_count": 14,
    "B_count": 22,
    "A_files": ["pom.xml", ".gitignore"],
    "demoted_A_in_backport_mode": ["build.gradle"]
  },
  "config": {
    "commit_granularity": "preserve-source-commits",
    "semantic_mapping_enabled": true,
    "locked_file_rules": {
      "take_target": ["*.lock", "package-lock.json", "yarn.lock"],
      "take_source": []
    },
    "verification": {
      "compile": true,
      "lint": true,
      "test": "scope",
      "suites": []
    }
  },
  "cleanup_policy": "default-7d"
}
```

## Field Reference

| Field | Type | Notes |
|---|---|---|
| `version` | string | Schema version. v1 = `"1.0"`, v2 = `"2.0"`. Sessions never migrate; the field is used to refuse cross-version reuse. |
| `task_name` | string | Slugified task name; used in working_branch + state path |
| `mode` | enum | One of: full-merge, cherry-pick-set, patch-apply, backport-cherry, backport-transplant, semantic-transplant, rebase-onto, forward-integrate |
| `pipeline` | enum | `conflict` \| `transplant`. Set by Stage 2 mode inference. Drives Stage 4-6 fork. |
| `created_at` | ISO-8601 | When skill was first invoked for this task |
| `paused_at` | ISO-8601 \| null | Set when user `[p]`-paused; null otherwise |
| `finalized_at` | ISO-8601 \| null | Set when Stage 8 completes |
| `status` | enum | `in-progress` \| `paused` \| `pre-verified` \| `awaiting-user` \| `finalized` \| `aborted` \| `error`. Lifecycle: Stage 0-6 set `in-progress`; Stage 7 commit transitions to `pre-verified`; Stage 7.5 Phase 2 awaiting user input uses `awaiting-user`; Phase 2「完成」transitions to `finalized`. |
| `iter` | int | Phase 2 iteration counter. Initial = 1; bumps +1 each time Phase 2 user feedback loops back to Stage 4-6. |
| `iterations[]` | array | Per-iteration record: `{iter, started_at, trigger, ended_at, user_feedback}`. `trigger` ∈ {`initial`, `user-feedback`, `phase1-fix`}. |
| `source.type` | enum | `branch` \| `patch` \| `diff` |
| `source.ref` | string | Branch ref or file path |
| `source.sha` | string | Source branch HEAD at start (used for force-push detection on resume) |
| `source.merge_base_with_target` | string | Captured at start |
| `target.head_sha` | string | Target branch HEAD at start (immutable check at resume) |
| `target.base_sha` | string | What the working branch was built on (may differ from head_sha if user picked an older base) |
| `working_branch.name` | string | Always `merge/<task_name>` |
| `working_branch.worktree_path` | string \| null | Absolute path to the worktree when complex mode (`null` = 主仓 checkout) |
| `working_branch.use_worktree` | bool | True for complex modes (backport-transplant / semantic-transplant / rebase-onto / forward-integrate) or when user explicitly opted in |
| `stage` | int | Current stage as integer (0/1/2/3/4/5/6/7/8). Matches most recent entry in stage_history when in-progress. |
| `stage_kind` | string | Sub-stage label: `"0"` / `"1"` / `"2"` / `"3"` / `"4c"` / `"4t"` / `"5c"` / `"5t"` / `"6c"` / `"6t"` / `"6.5"` / `"7"` / `"7.5"` / `"8"`. Required for v2 to distinguish conflict vs transplant forks. |
| `stage_history[]` | array | Per-stage record: `{stage, kind, tag, completed_at}`. v2 requires a complete 11-entry history (0/1/2/3/4(c-or-t)/5(c-or-t)/6(c-or-t)/6.5/7/7.5/8). Gaps are a Safety Invariant 7 violation. |
| `requirements[]` | array | Stage 2 produced 需求清单 entries; full schema in `assets/requirements.yaml`. Each item: `{id, title, scope_tag, target_locations[], acceptance[], out_of_scope[], status, evidence{}, ambiguous}`. |
| `global_out_of_scope[]` | array<string> | Global negative-constraint lines applicable to all items (per `assets/requirements.yaml`). |
| `grafts[]` | array | Only populated when `pipeline == transplant`. Full schema in `assets/grafting-plan.yaml`. |
| `decisions[]` | array | Only populated when `pipeline == conflict`. One entry per C/D class hunk; see Decision Entry below. |
| `audit[]` | array | Stage 6.5 self-audit records: `{unit_id, unit_kind, result, violations[], action, audited_at}`. `unit_kind` ∈ {`graft`, `hunk`}; `result` ∈ {`pass`, `fail`}; `action` ∈ {`applied`, `rolled-back`}. |
| `unresolved[]` | array | Conflict-pipeline hunks Stage 6c could not auto-decide; also mirrored to `.git/merge-conductor/<task>/unresolved.md`. Each entry: `{id, file, symbol, taken: "target-fallback", note}`. Surfaced in Stage 7.5 Phase 2 report as ❓ items. |
| `auto_resolved_summary` | object | Counts + sample files for A/B class (conflict-pipeline) |
| `config.commit_granularity` | enum | `preserve-source-commits` \| `single-merge` \| `squash` \| `themed-regroup` |
| `config.semantic_mapping_enabled` | bool | True if semantic mapping ran for this session (applies to transplant-pipeline always; conflict-pipeline conditional) |
| `config.locked_file_rules.take_target` | array<glob> | Files forced to take target |
| `config.locked_file_rules.take_source` | array<glob> | Files forced to take source |
| `config.verification.compile` | bool | Stage 7.5 Phase 1 — run language-native compile/typecheck. Default `true`. |
| `config.verification.lint` | bool | Stage 7.5 Phase 1 — run linter. Default `true`. |
| `config.verification.test` | enum | `scope` \| `full` \| `off` \| `suites`. Default `scope` (only tests touching files in `requirements.yaml`). When `suites`, populates `config.verification.suites[]`. |
| `config.verification.suites` | array<string> | Test suite names; used only when `config.verification.test == "suites"`. |
| `cleanup_policy` | enum | `default-7d` \| `last-N` (with `cleanup_last_n` field) \| `permanent` \| `manual` |

### Decision Entry

| Field | Type | Notes |
|---|---|---|
| `id` | int | Sequential 1..N |
| `file` | string | Relative path |
| `symbol` | string | Method/function/class name |
| `class` | enum | `C` \| `D` |
| `d_subclass` | enum \| null | D.1 / D.2 / ... when class == D; null when class == C |
| `status` | enum | `pending` \| `resolved` \| `skipped` |
| `choice` | int \| null | 1-5; null when not resolved |
| `free_text` | string \| null | Raw user input when choice == 5; null otherwise |
| `model_recommendation` | int | The option the model recommended (1-5) |
| `semantic_mapping` | object \| null | Populated only when Stage 5.5 ran for this decision |
| `resolved_at` | ISO-8601 \| null | When user resolved the decision |
| `skip_reason` | string | Only when status == skipped |

## Validation Rules

On every write to `state.json`:

1. `version` MUST be `"2.0"` for v2 sessions. v1 sessions (`"1.0"`) are read-only and never migrated.
2. `stage` MUST match the highest stage in `stage_history[].stage` for in-progress sessions.
3. `stage_kind` MUST match the most recent `stage_history[*].kind` and MUST be consistent with `pipeline` (e.g. `stage_kind: "4t"` requires `pipeline: "transplant"`).
4. `working_branch.name` MUST exist as a valid git branch. When `working_branch.use_worktree == true`, `working_branch.worktree_path` MUST be a valid worktree directory (`git worktree list` includes it).
5. All non-null tags listed in `stage_history` MUST exist (`git rev-parse <tag>` succeeds).
6. If `status == finalized`, `finalized_at` MUST be set and `stage_history` MUST contain 11 entries spanning stages 0–8 (Safety Invariant 7).
7. If `status == paused`, `paused_at` MUST be set. v2 allows pause at any decision-bearing stage (Stage 4-6, 6.5, 7.5 Phase 2).

## Sibling Files

All paths are under `<repo>/.git/merge-conductor/<task>/`.

| File | Purpose |
|---|---|
| `state.json` | This file (machine state) |
| `decision-log.md` | Human-readable timeline |
| `strategy.md` | Stage 2 strategy report (markdown) |
| `requirements.yaml` | Stage 2 需求清单 (v2; full schema in `assets/requirements.yaml`) |
| `grafting-plan.yaml` | Stage 4t per-graft 嫁接矩阵 (v2, transplant-pipeline only) |
| `drafts/G-XX.diff` | Stage 5t per-item draft diffs (v2, transplant-pipeline only) |
| `audit/<unit-id>.md` | Stage 6.5 self-audit reports (v2) |
| `merge-report.html` | Full-view mirror (HTML, may include `<script>`) |
| `merge-report.js` | Optional sibling JS file when HTML exceeds 200KB |
| `verification-report.md` | Stage 7.5 Phase 2 兜底差异表 (v2) |
| `unresolved.md` | Stage 6c hunks fallen through to default-take-target (v2, conflict-pipeline) |
| `patches/` | Copies of input `.patch` / `.diff` files for archival |

## Resume Validation

On invocation, if a `state.json` exists with `status: in-progress` or `paused`:

1. Read state.json
2. Refuse to resume if `version != "2.0"` — surface the version mismatch to the user; v1 sessions are not auto-migrated.
3. Verify `working_branch.name` exists: `git rev-parse --verify <working_branch.name>`
4. If `working_branch.use_worktree == true`, verify `working_branch.worktree_path` is registered: `git worktree list --porcelain | grep <worktree_path>`. Missing worktree → offer rebuild / fallback to main-repo checkout / abort (per `references/recovery-protocol.md`).
5. Verify `source.sha` is still reachable: `git rev-list --max-count=1 <source.sha>`
6. Verify the most recent non-null stage_history tag exists
7. If all pass → prompt user about resume
8. If any fail → diagnostic dump and refuse to resume (instruct user to inspect manually)
