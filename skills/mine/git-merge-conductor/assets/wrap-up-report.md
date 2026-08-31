<!--
Template: wrap-up-report.md
Used by: SKILL.md Stage 8 (Wrap-up)
Output: rendered to terminal as final summary.
Placeholders use {{var_name}} (English); fixed text is Chinese (user-facing).
Required: present 4 cleanup options at the end.
-->

# ✅ 合并完成 — {{task_name}}

## 概要
- **形态**：{{mode}}
- **工作分支**：`merge/{{task_name}}`（HEAD = `{{final_sha}}`）
- **决策点**：{{resolved_count}} / {{total_count}} 已解决，{{skipped_count}} 跳过
- **自动处理**：A 类 {{A_count}} 处，B 类 {{B_count}} 处
{{#if semantic_mapping_used}}
- **语义映射**：{{mapping_count}} 处（详见 HTML 报告）
{{/if}}

## 决策亮点

{{top_5_decisions_summary}}

## 报告位置

- **全貌 HTML**（可浏览器打开，自包含、离线可用）：
  `{{repo_root}}/.git/merge-conductor/{{task_name}}/merge-report.html`
- **决策日志**（人读时间线）：
  `{{repo_root}}/.git/merge-conductor/{{task_name}}/decision-log.md`
- **机器状态**：
  `{{repo_root}}/.git/merge-conductor/{{task_name}}/state.json`

## 下一步建议

1. **复核工作分支与目标分支的差异**：
   ```bash
   git diff {{target_branch}}..merge/{{task_name}}
   ```
2. **在 JetBrains / VSCode 里打开工作分支做事后可视化检查**（事后视觉复核，确认合并质量）
3. **满意后合并回目标分支**：
   ```bash
   git checkout {{target_branch}}
   git merge merge/{{task_name}}
   ```
4. **推送 / 开 PR** 按你的团队规范自决（本 skill 不会自动 push 或开 PR）

## 清理建议（合并验证满意后）

本次合并产生的可清理资产：

- **工作分支**：`merge/{{task_name}}`
- **状态目录**：`.git/merge-conductor/{{task_name}}/`（含 HTML 报告 / state.json / decision-log）
- **backup tags**：`merge/{{task_name}}/before-step-*` 共 {{tag_count}} 个
- **final tag**：`merge/{{task_name}}/done`
{{#if use_worktree}}
- **worktree 目录**：`{{worktree_path}}`
{{/if}}

{{#if use_worktree}}
> 本次使用了独立 worktree（路径：`{{worktree_path}}`）。下方清理选项中
> 标 worktree 字样的子项决定是否同步清除 worktree 目录。
{{/if}}

请选择清理策略（回复数字）：

```
[1] 默认：backup tags 保留 7 天后自动清理
    下次运行本 skill 时检查并清理超过 7 天的合并状态目录与 before-step tags。
    final tag (done) 永久保留作为审计追溯。
    本次合并资产将在 {{cleanup_due_date}} 后被清理。
    {{#if use_worktree}}
    - worktree 同步清理（推荐）：到期时一并 `git worktree remove {{worktree_path}}`
    {{/if}}

[2] 按 commit 次数：保留最近 N 次合并的状态与 tags
    请指定 N（默认 5）。比 N 旧的合并会在下次启动时自动清理。
    {{#if use_worktree}}
    - worktree 路径保留（与 state 一同保留），超出 N 时一同清理
    {{/if}}

[3] 永久保留：什么都不清理，全部留档
    适合需要长期追溯合并历史的项目。注意 .git/ 目录可能膨胀。
    {{#if use_worktree}}
    - worktree 路径保留（不会自动 `git worktree remove`）
    {{/if}}

[4] 手动决定：现在告诉你清理命令，由你自己决定何时跑
    清理命令：
      git branch -D merge/{{task_name}}
      git tag -d $(git tag -l "merge/{{task_name}}/before-step-*")
      rm -rf .git/merge-conductor/{{task_name}}
    {{#if use_worktree}}
      git worktree remove {{worktree_path}}
    {{/if}}
    （建议至少保留 7 天再清理，以便事后复核）
```

请回复 `1` / `2` / `3` / `4` 选择清理策略。
