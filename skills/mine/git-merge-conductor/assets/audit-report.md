# Self-audit {{unit_id}}

**unit**: {{unit_id}} ({{unit_kind}}) → {{req_id_or_hunk_loc}} {{symbol_or_path}}

**结论**: {{pass_or_fail}}{{ if fail: "（{{violation_summary}}）"}}

**检测项**:
- Per-item out_of_scope: {{result}}{{ if hit: "命中「{{matched_constraint}}」"}}
- Global out_of_scope: {{result}}{{ if hit: "命中「{{matched_constraint}}」"}}
- NC-01 项目守卫套通用代码: {{result}}{{ if hit: "命中: {{evidence}}"}}
- NC-02 回退已演进逻辑: {{result}}{{ if hit: "命中: {{evidence}}"}}
- NC-03 源专属目录结构: {{result}}{{ if hit: "命中: {{evidence}}"}}
- NC-04 注释项目限定: {{result}}{{ if hit: "命中: {{evidence}}"}}
- NC-05 范围外变更: {{result}}{{ if hit: "命中: {{evidence}}"}}

**后续动作**: {{action}}
{{ if rolled-back: "rollback {{unit_id}}；req {{req_id}} 标 {{new_status}}；写入 Phase 2 报表 ⚠ 项" }}
{{ if applied: "保留改动；req {{req_id}} 维持 {{status}}" }}

**audited_at**: {{iso_timestamp}}
