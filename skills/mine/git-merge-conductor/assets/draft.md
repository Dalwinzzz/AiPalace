# Draft G-{{graft_id}} — REQ-{{req_id}}

> 草案，未应用到工作树。位置：`.git/merge-conductor/{{task}}/drafts/G-{{graft_id}}.diff`

## 上下文摘要

**需求**：{{req_title}}
**scope_tag**：{{scope_tag}}
**source**：{{source_ref}}@{{source_sha}}::{{source_symbol}}
**target**：{{target_file}}::{{target_symbol}}
**策略**：{{graft_strategy}}{{ if guarded-overlay: "（守卫: {{guard_condition}}）"}}

## 改动说明（中文）

{{model_writes_one_paragraph_中文_explaining_what_changes_and_why}}

## 置信度

- target_location mapping: {{high|medium|low}}
- target 端代码 fit: {{high|medium|low}}
- 综合: {{high|medium|low}}

## out_of_scope 初筛

- 本草案改动的文件：{{list_of_files}}
- 与 requirements.yaml::items[i].target_locations 比对：{{match|mismatch}}
- per-item out_of_scope 命中检查：{{none|hit_list}}
- global_out_of_scope 命中检查：{{none|hit_list}}

> 这是 draft-time 一次轻筛，Stage 6.5 是 authoritative audit。

## Proposed unified diff

参见 `.git/merge-conductor/{{task}}/drafts/G-{{graft_id}}.diff`。
