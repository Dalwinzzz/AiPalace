---
name: project-spec-location
description: spec 文件落到 docs/spec-architect/YYYY-MM/ 时遵循 .gitignore；仅用户明确要求才 git add -f
metadata: 
  node_type: memory
  type: project
  originSessionId: d30c5b2c-756f-4acb-a963-317dc8397219
---

## Spec 文件落地规则 (p2)

spec 文件落到 `docs/spec-architect/YYYY-MM/` 时**遵循 .gitignore**；仅当用户明确要求纳入 git 追踪才 `git add -f`。

**Why:** `.gitignore` 是项目的权威配置；不应擅自把被忽略文件纳入追踪。
**How to apply:** 落 spec 后用 `git check-ignore <path>` 确认；若被 ignore 则保留在 working tree 不 add；用户明确说 "把这个 spec 提交" 才 `git add -f`。
