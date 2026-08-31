# 溯源线索（community）

- **upstream**: https://github.com/obra/superpowers（skills/using-git-worktrees）
- **credit**: Jesse Vincent（obra）
- **license**: MIT（Copyright (c) 2025 Jesse Vincent，见同目录 LICENSE）
- **来源性质**: superpowers 插件卸载后（见 [ADR-0018](../../../../adr/0018-卸载superpowers插件与ask-first软约束.md)），从其中个别挑取仍被 `skills/mine/git-merge-conductor` 运行时依赖（Stage 3 委托建 worktree）的单个 skill，改以社区硬拷贝形式单独挂载，不再整体装插件。
- **快照方式**: 硬拷贝快照（SKILL.md + LICENSE），克隆于 2026-07-27（上游 commit `3dcbd5c`）
- **上游仓库本地路径**: `~/Library/CodeRepo/AI/superpowers`（已纳入 `tools/upstream_sync.py` 的 `superpowers` 映射，可随周期任务更新硬拷贝）
