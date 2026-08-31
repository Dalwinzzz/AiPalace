# 记忆策略 — Codex 版工具差异分片

> **依据来源**：Codex 官方文档约定：脚本以裸名调用，路径由 `paths.py` 运行时解析；
> 全局 memory 落点 `CODEX_HOME/memories/sql-expert-dba/` 或 `~/.codex/memories/sql-expert-dba/`。
> 本分片仅记录 Codex harness 相关差异，公共策略规则见 [memory-policy.md](memory-policy.md)。

## Codex 版脚本调用约定

| 时机 | 调用方式 | 目的 |
|------|---------|------|
| workflow 开始前 | `memory_search.py --memory-dir <resolved>` | 查找相关已有记忆 |
| 主任务完成后（有写入时） | `memory_capture.py --memory-dir <resolved> --capture-mode explicit_user_requested ...` | 写入 candidate / approved |
| candidate 复审晋升 | `memory_promote.py --memory-dir <resolved> --id <memory-id>` | 将指定 candidate 晋升为 approved |
| 维护时 | `memory_index.py --memory-dir <resolved>` | 重建或校验索引一致性 |

脚本以裸名调用（由 PATH 或调用方解析），`--memory-dir` 由 `paths.py::resolve_user_memory_dir()` 在运行时决定，优先级：`SQL_EXPERT_DBA_MEMORY_DIR` > `CODEX_HOME/memories/sql-expert-dba` > `~/.codex/memories/sql-expert-dba`。

## Codex 版全局 memory 落点

- 默认：`~/.codex/memories/sql-expert-dba/`
- 覆盖：`$SQL_EXPERT_DBA_MEMORY_DIR`（绝对路径或 `~` 展开路径）
- 备用：`$CODEX_HOME/memories/sql-expert-dba/`（若设置了 CODEX_HOME）

该目录与插件源码物理分离，插件重装/升级不影响已沉淀记忆。
