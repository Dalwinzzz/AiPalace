---
name: aipalace-upstream-sync
description: Run or inspect the recurring AiPalace upstream skill sync when the task mentions heartbeat runs, codex定时任务, upstream_sync.py, repo-local logs, or reporting which hard-copy files changed or were intentionally skipped.
argument-hint: "[--commit|--skip-pull]"
disable-model-invocation: true
allowed-tools:
  - Read
  - Grep
  - Bash
---

# AiPalace Upstream Sync

## When to use

Use this skill when the task is about the recurring GitHub-to-AiPalace skill sync workflow in `/Users/dalwin/Library/CodeRepo/AI`, especially if the user mentions:

- `upstream_sync.py`
- heartbeat / scheduled sync payloads
- `codex定时任务`
- repo-local logs under `AiPalace/logs/`
- reporting which files changed or were kept
- `skill-management` exclusion / intentional skip

Do not use this skill for generic git mirroring, other repos, or any workflow that is not driven by `AiPalace/tools/upstream_sync.py`.

## Inputs / context to gather

1. Confirm the cwd is `/Users/dalwin/Library/CodeRepo/AI` or that the task explicitly targets `AiPalace`.
2. Read:
   - `AiPalace/tools/upstream_sync.py`
   - `AiPalace/registry.yaml`
   - `AiPalace/tools/skillctl.py`
3. Check whether the user wants:
   - execution with commit: `--commit`
   - dry-ish verification: `--skip-pull`
   - result reporting only from existing logs
4. Check repo-local logs if they already exist:
   - `AiPalace/logs/aipalace-upstream-sync.log`
   - `AiPalace/logs/aipalace-upstream-sync.err.log`
5. Check whether the task touches the durable local exception:
   - `skills/community/garveyhu/method/skill-management`
   - confirm it is still protected by the script's exclusion list instead of being overwritten

## Procedure

1. Verify this is the mapped hard-copy workflow, not an all-files sync.
   - Preserve the boundary: only source-mapped skill hard-copies should be updated.
   - Preserve the local exception: `skills/community/garveyhu/method/skill-management` should stay excluded from upstream overwrite unless the user explicitly changes that rule.
2. Decide the execution mode from the request.
   - Heartbeat / scheduled execution usually means:
     - `python3 AiPalace/tools/upstream_sync.py --commit`
   - Log-path / script verification usually means:
     - `python3 AiPalace/tools/upstream_sync.py --skip-pull`
3. Before running, inspect the script output contract so the final report matches it.
   - Reuse these four headings:
     - `上游同步结果`
     - `硬拷贝同步结果`
     - `保留不动`
     - `策略`
4. Run from `/Users/dalwin/Library/CodeRepo/AI`.
5. After execution, inspect:
   - changed upstream repos
   - changed hard-copy files
   - any `kept:` local-only files
   - any intentional skips from the exclusion list
   - commit id if `--commit` was used
   - repo-local log creation/update
6. Report results in a file-level, human-readable way.
   - Include what changed, what was preserved, and which strategy produced that result.

## Efficiency plan

- Start with `AiPalace/tools/upstream_sync.py`; it is the single entrypoint and usually answers most routing questions.
- If the task is only about reporting, prefer reading repo-local logs before rerunning the job.
- Cache one key branch fact early: `langchain` may fall back to remote default branch `master` because `origin/main` is absent.
- Cache one key boundary fact early: `skill-management` is a durable local exception and should appear as skipped/preserved, not overwritten.
- Stop exploring once you can answer:
  - what command should run,
  - where logs are,
  - what changed,
  - what was intentionally preserved or skipped.

## Pitfalls and fixes

- Symptom: trying to treat this as generic repo mirroring.
  - Fix: keep the scope to mapped AiPalace hard-copy skill directories only.
- Symptom: assuming logs live in `/private/tmp`.
  - Fix: use repo-local logs under `AiPalace/logs/`.
- Symptom: assuming every upstream uses `origin/main`.
  - Fix: check remote default branch fallback; `langchain` may use `master`.
- Symptom: reporting only “done” without detail.
  - Fix: include file-level changes, preserved files, and the strategy used.
- Symptom: `skill-management` disappears from AiPalace after a sync.
  - Fix: check the script exclusion list first; this path is expected to be intentionally skipped from awesome-skills overwrite.
- Symptom: a fetch failure looks like a script bug.
  - Fix: separate environment/network git failures from sync-logic failures before changing code.

## Verification checklist

- `AiPalace/tools/upstream_sync.py` is still the workflow entrypoint.
- Repo-local logs exist or are intentionally created under `AiPalace/logs/`.
- Output/report covers `上游同步结果` / `硬拷贝同步结果` / `保留不动` / `策略`.
- Any commit created for scheduled execution preserves the `(codex定时任务)` suffix expectation.
- Any durable exception such as `skills/community/garveyhu/method/skill-management` is still reported as skipped/preserved rather than overwritten.
- The final report names concrete changed files or explicitly says there were no mapped hard-copy updates.

## Minimal examples

- Execute a heartbeat-style run:
  - `python3 AiPalace/tools/upstream_sync.py --commit`
- Verify logging path without pulling:
  - `python3 AiPalace/tools/upstream_sync.py --skip-pull`
