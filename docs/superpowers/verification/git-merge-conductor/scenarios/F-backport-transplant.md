# Scenario F — backport-transplant (care-class-to-develop)

## Goal

Verify the end-to-end transplant-pipeline:
- Stage 2 identifies `backport-transplant` (not `backport-cherry`)
- requirements.yaml extracted with `scope_tag` per item
- Stage 4t builds grafting plan; Stage 5t drafts; Stage 6t auto-applies
- Stage 6.5 NC-01 INTERCEPTS the `projectName == "JIASHAN"` guard on
  `normalizeCareClassTeacherName` because scope_tag = "通用课堂功能"
- Stage 7.5 Phase 2 surfaces the intercepted item; user provides feedback
- Loop back to Stage 4t; second iter resolves; user says "完成"
- Finalize

## Setup

```bash
cd /tmp && rm -rf gmc-fixture-F
bash /Users/dalwin/Documents/AI/docs/superpowers/verification/git-merge-conductor/setup-fixture.sh
cd /tmp/gmc-fixture-F
```

## Run

Start Claude Code in `/tmp/gmc-fixture-F`. Invoke:

> 「把 refactor/micro-core-dev 上的 care-class 功能合并到 develop，
> 主要是把 normalizeCareClassTeacherName 这个方法的展示逻辑回并进来。
> 注意 develop 已经有了 teacherList 的实现，不要回退。」

## Expected pipeline behavior

### Stage 0-2

- Stage 0 emits banner, no guards trip
- Stage 1 normalizes: source=refactor/micro-core-dev, target=develop
- Stage 2 mode inference: should detect `backport-transplant` (refactor signals in
  CourseOffline + plugin structure delta)
- Stage 2 Gate: model proposes requirements.yaml with at least 1 item like:
  ```yaml
  - id: REQ-01
    title: 课堂教师展示名回并
    scope_tag: 通用课堂功能
    target_locations:
      - file: src/main/java/com/example/course/CourseOffline.java
        symbol: getDisplayName
    out_of_scope:
      - 不引入 projectName == "JIASHAN" 守卫（develop 主线通用）
      - 不删除 teacherList 实现
  ```
  User confirms "策略 OK".

### Stage 3

- Worktree created via `superpowers:using-git-worktrees` (backport-transplant
  triggers worktree).
- Banner: `[Stage 3 · Working Setup · iter 1 · tag: merge/care-class-transplant/before-step-3]`

### Stage 4t / 5t / 6t

- 4t builds grafting plan with 1 graft, `graft_strategy: merge-into`
  (CareClassUtil source → CourseOffline.getDisplayName target)
- 5t produces a draft; the draft may include the `projectName == "JIASHAN"`
  guard (out_of_scope soft-filter SHOULD catch this; if not, Stage 6.5 will)
- 6t applies → Stage 6.5 invokes → NC-01 hits → rollback
- 6t loop ends with REQ-01 status = partial

### Stage 7

- Commit produced even though REQ-01 partial (Stage 7 commits whatever is staged)
- Tag merge/care-class-transplant/done; status = pre-verified

### Stage 7.5 Phase 1

- compile passes (no syntax error from rollback)
- lint passes
- scope-test: passes

### Stage 7.5 Phase 2

- Report shows REQ-01: ⚠ partial, evidence: rollback (NC-01)
- User says: 「REQ-01 没做对——去掉项目守卫，只用 teacherList 路径」
- iter += 1, loop back to Stage 4t

### Iter 2

- 4t re-drafts with strategy = merge-into, no projectName guard
- 6t applies; Stage 6.5 passes
- Stage 7 commits iter 2
- Phase 1 passes
- Phase 2 user says "完成"

### Stage 8

- Wrap-up shows iterations[].length == 2
- state.json::status = finalized
- worktree cleanup option presented

## Inspection commands

```bash
# After scenario completes:
cat .git/merge-conductor/care-class-transplant/state.json | jq '.status, .iterations | length, .audit | length'
# Expected: "finalized", 2, ≥1

cat .git/merge-conductor/care-class-transplant/audit/*.md
# Should show the NC-01 intercept from iter 1

cat .git/merge-conductor/care-class-transplant/grafting-plan.yaml | head -30
# Should show G-01 with merge-into strategy
```

## Pass criteria

- [ ] Mode = backport-transplant (not backport-cherry)
- [ ] Worktree created at Stage 3
- [ ] NC-01 fires on iter 1 (projectName guard intercepted)
- [ ] User feedback parsed correctly in Phase 2; iter 2 triggered
- [ ] Final status = finalized after iter 2
- [ ] stage_history complete (11 entries × 2 iters = audit array shows 2 attempts on REQ-01)
