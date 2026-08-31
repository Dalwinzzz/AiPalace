# 溯源线索（community）

- **upstream**: https://github.com/obra/superpowers（skills/writing-plans）
- **credit**: Jesse Vincent（obra）
- **license**: MIT（Copyright (c) 2025 Jesse Vincent，见同目录 LICENSE）
- **来源性质**: superpowers 插件卸载后（见 [ADR-0018](../../../../adr/0018-卸载superpowers插件与ask-first软约束.md)），从其中个别挑取仍被 `skills/mine/spec-architect`（continue-to-coding.md，complex 分支）推荐使用的单个 skill，改以社区硬拷贝形式单独挂载，不再整体装插件。
- **已知局限（未随同挂载的依赖）**: 原文 Execution Handoff 一节要求执行阶段用 `superpowers:subagent-driven-development` 或 `superpowers:executing-plans` 二选一，Context 一节提到 `superpowers:using-git-worktrees`；本次仅挂载 `writing-plans` 本体（用于出计划），未挂载 `subagent-driven-development` / `executing-plans`，保持内容与上游逐字一致不做删改——这两处引用暂时指向未挂载的技能名，届时按名字就近手动 invoke 即可，不影响"出计划"这一核心用途。
- **快照方式**: 硬拷贝快照（SKILL.md + plan-document-reviewer-prompt.md + LICENSE），克隆于 2026-07-27（上游 commit `3dcbd5c`）
- **上游仓库本地路径**: `~/Library/CodeRepo/AI/superpowers`（已纳入 `tools/upstream_sync.py` 的 `superpowers` 映射，可随周期任务更新硬拷贝）
