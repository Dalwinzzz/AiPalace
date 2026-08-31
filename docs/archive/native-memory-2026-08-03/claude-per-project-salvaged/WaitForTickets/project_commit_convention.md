WaitForTickets 仓库装了一个 PreToolUse:Bash 钩子，强制所有 git commit 信息符合格式：`<type>(<scope>): <subject>` 或 `<type>: <subject>`。冒号后必须恰好一个空格；type 必须是 feat/fix/docs/style/refactor/perf/test/chore/revert/build 之一；**subject 必须用中文**；scope 选填。违规直接 exit 1 拒绝提交。

**Why:** 2026-06-09 首次提交 v3 文档时英文 subject 被钩子拒绝，改中文 subject 后通过。这是仓库级硬约束，非个人偏好。

**How to apply:** 自己 commit 时用中文 subject + 合规 type。派发 subagent 做实现时，**必须在 subagent prompt 里写明这条 commit 规范**，否则 subagent 的 commit 会被钩子拒绝、卡住任务。示例：`feat(scheduler): 实现 ±250ms 精度调度器`。关联 [[project_v3_restart]]。
