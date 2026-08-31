# 记忆策略 — Claude 版工具差异分片

> **依据来源**：Claude Agent SDK 官方文档约定：脚本以 `${CLAUDE_PLUGIN_ROOT}/scripts/...` 全路径调用；
> 全局 memory 落点 `~/.claude/plugins/data/sql-expert-dba/memory/`（Claude 官方插件 data 区）。
> 本分片仅记录 Claude harness 相关差异，公共策略规则见 [memory-policy.md](memory-policy.md)。

## Claude 版脚本调用约定

| 时机 | 调用方式 | 目的 |
|------|---------|------|
| workflow 开始前 | `${CLAUDE_PLUGIN_ROOT}/scripts/memory_search.py --memory-dir <resolved>` | 查找相关已有记忆 |
| 主任务完成后（有写入时） | `${CLAUDE_PLUGIN_ROOT}/scripts/memory_capture.py --memory-dir <resolved> --capture-mode explicit_user_requested ...` | 写入 candidate / approved |
| candidate 复审晋升 | `${CLAUDE_PLUGIN_ROOT}/scripts/memory_promote.py --memory-dir <resolved> --id <memory-id>` | 将指定 candidate 晋升为 approved |
| 维护时 | `${CLAUDE_PLUGIN_ROOT}/scripts/memory_index.py --memory-dir <resolved>` | 重建或校验索引一致性 |

`--memory-dir` 由 `paths.py::resolve_user_memory_dir()` 在运行时决定，优先级：`SQL_EXPERT_DBA_MEMORY_DIR` > `~/.claude/plugins/data/sql-expert-dba/memory/`。

## Claude 版全局 memory 落点

- 默认：`~/.claude/plugins/data/sql-expert-dba/memory/`（Claude 官方插件 data 区）
- 覆盖：`$SQL_EXPERT_DBA_MEMORY_DIR`（绝对路径或 `~` 展开路径）

该目录与插件源码物理分离，插件重装/升级不影响已沉淀记忆。
