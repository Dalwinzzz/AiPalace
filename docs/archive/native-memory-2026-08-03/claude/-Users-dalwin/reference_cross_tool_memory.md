---
name: reference-cross-tool-memory
description: 跨工具事实唯一源——codex memory 与 claude memory 的物理位置 + 对账要求
metadata: 
  node_type: memory
  type: reference
  originSessionId: d30c5b2c-756f-4acb-a963-317dc8397219
---

跨工具事实唯一源：

- Codex memory：`/Users/dalwin/.codex/memories/MEMORY.md` + `memory_summary.md` + `raw_memories.md`
- Claude memory：`/Users/dalwin/.claude/projects/-Users-dalwin/memory/`

两侧定期对账；如发现 codex 中已有的稳定事实但 claude 未沉淀（或反之），主动建议补全。

相关：[[reference-skills-root]] 中说明 skills 也走类似 SOT + symlink 跨工具共享模式。
