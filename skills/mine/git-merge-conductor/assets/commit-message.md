<!--
Template: commit-message.md (v2)
Used by: SKILL.md Stage 7 (Finalization & Commit)
Output: passed as -m argument to git commit via heredoc
Placeholders use {{var_name}} (English); fixed text is Chinese (user-facing).
Required prefix: `merge:` (per user rule 5).

v2 changes:
- Adds `iter: N` field reflecting `state.json::iter`
- Adds optional 回滚摘要 block summarizing Stage 6.5 NC interceptions
- Adds optional 未决项 pointer to unresolved.md for follow-up iterations

For multi-commit modes (cherry-pick-set / backport / rebase-onto), each commit
gets its own rendering with {{summary_chinese}} rewritten from the source
commit's subject line.

For squash mode, render ONE commit message aggregating all decisions.
-->

merge: {{summary_chinese}}

源: {{source_ref}}@{{source_sha}}
mode: {{inferred_mode}} (pipeline: {{pipeline}})
iter: {{iter_number}}

决策摘要:
{{#each applied_units}}
- [{{path}}::{{symbol}} #{{idx}}] {{choice_label}}：{{decision_brief_chinese}}
{{/each}}

{{#if has_rolled_back}}
回滚摘要 (iter {{iter_number}} 中 Stage 6.5 拦截):
{{#each rolled_back_units}}
- [{{path}}::{{symbol}}] 命中 {{nc_or_constraint}}, 已 rollback
{{/each}}
{{/if}}

{{#if has_auto_resolved}}
A 类自动处理: {{A_count}} 处（详见 .git/merge-conductor/{{task_name}}/decision-log.md）
{{/if}}

{{#if semantic_mapping_used}}
语义映射: {{mapping_count}} 处映射依据已记入决策日志
{{/if}}

{{#if has_unresolved}}
未决项: {{unresolved_count}} 处（详见 .git/merge-conductor/{{task_name}}/unresolved.md，
将在下轮 Phase 2 由用户决议）
{{/if}}
