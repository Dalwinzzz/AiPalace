# context/howto —— 指令文件的按需子文档

存放被 `CLAUDE.md` / `AGENTS.md` 等 always-on 指令文件「索引指向、按需动态加载」的操作细则（how-to）。

主文件只留 when-to-use 触发 + 指针；具体 how-to 进本目录，模型实际要用时才 `Read`，不常驻上下文。维护约定见 [`instruction-file-maintenance.md`](instruction-file-maintenance.md)。

| 文件 | 被谁索引指向 | 内容 |
|------|-------------|------|
| [`context7-mcp.md`](context7-mcp.md) | `~/.claude/CLAUDE.md` · Documentation Lookups 段 | context7 调用流程 + 边界 |
| [`instruction-file-maintenance.md`](instruction-file-maintenance.md) | `~/.claude/CLAUDE.md` · 维护指令文件段 | CLAUDE.md/AGENTS.md 维护约定（本目录的元规则） |
| [`db-readonly-cli.md`](db-readonly-cli.md) | `~/.claude/CLAUDE.md` · 查数据库段 | dbq 只读查库通道：实例 / 用法 / 只读铁律 / 禁忌 |
