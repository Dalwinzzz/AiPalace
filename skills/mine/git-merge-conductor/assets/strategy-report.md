<!--
Template: strategy-report.md
Used by: SKILL.md Stage 2 (Mode Inference + Strategy Report — user gate)
Output: rendered to terminal AND written to .git/merge-conductor/{{task_name}}/strategy.md
Placeholders use {{var_name}} (English); fixed text is Chinese (user-facing).
-->

# 合并策略报告 — {{task_name}}

## 形态推断
- 推断结果：**{{mode}}**
- 置信度：{{confidence}}（低 / 中 / 高）
- 依据：
  - {{signal_1}}
  - {{signal_2}}
  - {{signal_3}}
{{#if alternatives}}
- 备选形态（置信度非高时）：
  - {{alternative_mode_1}}：{{alternative_reason_1}}
  - {{alternative_mode_2}}：{{alternative_reason_2}}
{{/if}}

## 分支双侧
- **源**：`{{source_ref}}`（HEAD = `{{source_sha}}`，与 target 的 merge-base = `{{merge_base_sha}}`）
- **目标**：`{{target_ref}}`（HEAD = `{{target_head_sha}}`）
- **工作分支**：`merge/{{task_name}}`（基于 `{{base_sha}}`）

## 影响范围分类

| 文件 | 源侧 +/- | 目标侧 +/- | 相关性 |
|---|---|---|---|
{{impact_table_rows}}

> 相关性说明：**核心** = 与本次需求直接相关；**边缘** = 顺带变动；**可能误命中** = 与任务关键词无明显关联，请关注

## 预估冲突分布

- **A 类**（自动 take target / backport 模式下汇报）：约 {{A_estimate}} 处
- **B 类**（git 已自动 take source）：约 {{B_estimate}} 处
- **C 类**（需你逐个决断）：约 {{C_estimate}} 处
- **D 类**（标注后需你决断）：约 {{D_estimate}} 处

> 实际数字会在 Stage 5 完成分类后给出。预估只是先让你心里有数。

## 计划执行命令链

```bash
{{command_chain}}
```

{{#if semantic_mapping_enabled}}
## 语义辅助映射

由于检测到目标分支存在重构信号 / 当前为 backport 模式，Stage 5.5 将主动搜索源侧修改符号在目标分支的对应位置（重命名 / 搬家 / 重构后的 counterpart），并在决策点附上"映射依据 + 建议合并方案"。
{{/if}}

## 你需要确认 / 可调整

- [ ] **mode 推断对吗**？若需纠正，回复："mode 应该是 {新mode}"
- [ ] **工作分支名 / 基准 commit** OK 吗？若需调整，回复："基于 {commit} 而不是 HEAD"
- [ ] **是否允许"语义辅助映射"**（Stage 5.5）？默认 {{semantic_mapping_default}}
- [ ] **commit 粒度偏好**：保留源 commits（默认）/ squash 单 commit / 模型按主题重组
- [ ] **锁定特定文件 take 哪一侧**？例如："*.lock 文件统一 take target"

## 需求清单（requirements.yaml 同源）

| ID | 标题 | scope_tag | target_locations | acceptance | out_of_scope | ambiguous |
|---|---|---|---|---|---|---|
{{requirement_table_rows}}

> Stage 2 Gate 前请人工核对此清单——尤其 `ambiguous: true` 条目和 `out_of_scope`
> 是否齐全。后续 Stage 6.5 自审与 Stage 7.5 Phase 2 兜底报表都以本清单为基线。

## 下一步

确认无误请回复**「策略 OK」**；有调整意见直接描述，我会重新发送修改后的策略。

只有你明确确认后，才会开始建工作分支与执行 git 操作。
