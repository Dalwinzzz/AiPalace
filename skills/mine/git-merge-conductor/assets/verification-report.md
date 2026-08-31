# 合并验证报告 — {{task}}

## 自动化校验（Phase 1）

- **compile**: {{compile_status}} {{ if iter > 1: "(iter {{compile_pass_iter}})"}}
- **lint**: {{lint_status}}
- **test**: {{test_status}}{{ if scope: " (scope: {{tested_modules}})"}}{{ if off: " (skipped per config)"}}

{{ if any_phase1_fail: "
### Phase 1 自修复轮次

| iter | trigger | fix_unit | result |
|---|---|---|---|
{{phase1_iter_table}}
" }}

## 需求清单兑现

| REQ | 标题 | scope_tag | status | evidence | 备注 |
|---|---|---|---|---|---|
{{requirements_status_table}}

## Self-Audit 拦截项（共 {{intercept_count}} 处）

{{ if intercept_count == 0: "无" }}
{{ if intercept_count > 0: "
{{intercept_list_per_unit}}
" }}

## 范围外尝试（NC-05 拦截，共 {{nc05_count}} 处）

{{ if nc05_count == 0: "无" }}
{{ if nc05_count > 0: "
{{nc05_list}}
" }}

## 未决项（Conflict-pipeline unresolved + Transplant low-confidence ⚠）

{{ if no_pending: "无" }}
{{ if pending_count > 0: "
{{pending_list}}
" }}

---

## 你的决定

请在终端回复其一：

- **`完成`** — 进入 Stage 8 收尾
- **`REQ-X 没做对`** + 说明 — 回 Stage 4-6 针对 REQ-X 重做
- **`REQ-X 不该做`** — 升级 `requirements.yaml` 移除 + rollback 相关改动
- **`还多 Z`**（路径或描述）— 找到引入项 → rollback
- 任意自由文本 — 我会解析意图并回显「我理解为: ...」让你二次确认
