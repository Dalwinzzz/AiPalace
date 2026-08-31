# Stage Contracts — Wrap-up (Stage 8)

Each section below is the canonical 五字段 contract for the stage. SKILL.md
points at these anchors and the model reads on demand. Maintain anchors:
`#stage-<N>` (or `#stage-<N><c|t>` for forked stages).

---

## Stage 8 — Wrap-up + Cleanup Options {#stage-8}

**Goal**
Summarize the merge outcome for the user, present cleanup options
(including the new worktree decision), and archive the report.

**Inputs**
- All session metadata (`state.json`, `decision-log.md`, audit reports, drafts)
- `assets/wrap-up-report.md`

**Decisions you own**
- Report content selection (top-N most impactful decisions to highlight)
- Cleanup-policy default for the task

**Hard constraints**
- Status MUST be `finalized` (set by Stage 7.5 Phase 2 完成 path).
- Final HTML report `<header><dl>` status field must show `finalized`.
- Worktree cleanup choice must be presented for any session where
  `state.json::working_branch.use_worktree == true`.

**Outputs**
- Terminal 中文 wrap-up report
- HTML report finalized (archive-ready)
- `state.json::cleanup_policy` persisted
- `state.json::stage_history[8]` appended (kind: "8")
- Stage banner: `[Stage 8 · Wrap-up · iter <final> · tag: merge/<task>/done]`
