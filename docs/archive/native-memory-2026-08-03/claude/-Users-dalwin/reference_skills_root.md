---
name: reference-skills-root
description: AI skills 主目录布局（~/Library/CodeRepo/AI/ 是唯一 SOT，含 awesome-skills、superpowers fork、skills 三仓）
metadata: 
  node_type: memory
  type: reference
  originSessionId: d30c5b2c-756f-4acb-a963-317dc8397219
---

`/Users/dalwin/Library/CodeRepo/AI/` 是 AI skills 的唯一 Source of Truth：

- `awesome-skills/` — 自创/精选 skills（如 docker-best-practices、spec-architect、git-merge-conductor）
- `superpowers/` — superpowers 仓库 fork
- `skills/` — 外部克隆（如 grill-me、grill-with-docs）

注册表与视图（双跳 symlink）：

- `/Users/dalwin/.agents/skills/{name}` → 软链 → SOT 下对应路径
- `/Users/dalwin/.claude/skills/{name}` → 软链 → `/Users/dalwin/.agents/skills/{name}`

相关：[[reference-cross-tool-memory]] 中说明 codex 与 claude 的跨工具协作约定。
