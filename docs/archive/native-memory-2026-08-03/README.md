# 双工具原生记忆归档 · 2026-08-03

ADR-0021 / ADR-0022 两轮记忆收敛前，Claude Code 与 Codex **原生自动记忆**的原始快照。归档在此是为了：这两套记忆是**机器本地的**（不进版本控制、换机即失），收敛时把内容蒸馏进 `vault/memory/` 后原处已删除，原始记录若不入仓就永久消失。

**这里是只读留档，不是活跃记忆。** 当前有效的跨工具/跨设备事实一律在 `vault/memory/`；本目录仅供回查"当时原文到底怎么写的"。

---

## 内容

| 目录 | 来源 | 快照时间 | 完整性 |
|------|------|---------|--------|
| `codex/` | `~/.codex/memories/` 全量 | 2026-08-03 首轮归档前 | ✅ 完整（`MEMORY.md` 646 行 + `memory_summary.md` + `raw_memories.md` + `rollout_summaries/` 17 份 + `skills/` + `extensions/`） |
| `claude/-Users-dalwin/` | Claude 全局 auto memory | 2026-08-03 首轮归档前 | ✅ 完整（18 条 + MEMORY.md） |
| `claude/-Users-dalwin-Library-CodeRepo/` | Claude auto memory（个人项目域） | 2026-08-03 首轮归档前 | ✅ 完整（4 条 + MEMORY.md） |
| `claude-per-project-salvaged/` | Claude 逐 repo auto memory | 2026-08-03 二轮归档前 | ⚠️ **部分**，见下 |

## ⚠️ `claude-per-project-salvaged/` 的完整性缺口

首轮备份只覆盖了 Codex 与 Claude 的两个全局域；二轮归档处理的 **10 个逐 repo memory 目录未被纳入那次备份就被删除了**。本目录是事后从会话的持久化工具输出中还原的，**只包含当时逐字读取过的条目**。

| 项目 | 原条目数 | 已还原 | 状态 |
|------|---------:|-------:|------|
| `skcnursery` | 12 | 12 | ✅ 全部逐字还原 |
| `skcactivity` | 8 | 8 | ✅ 全部逐字还原 |
| `skciotdevice` | 1 | 1 | ✅ |
| `kernel-framework` | 2 | 2 | ✅ |
| `awesome-skills`（两个域各 1） | 2 | 2 | ✅ |
| `skcmultimedia` | 0 | 0 | ✅ 本就为空 |
| `WaitForTickets` | 9 | 5 | ⚠️ 缺 4 |
| `MyRainmeterSkin` | 6 | 3 | ⚠️ 缺 3 |
| `skcinfant` | 3 | 1 | ⚠️ 缺 2 |
| **合计** | **43** | **34** | |

**原文已丢失、无法还原的 9 条**（仅存 MEMORY.md 索引里的一句话描述，正文不复存在）：

| 条目 | 索引描述（仅存这一句） |
|------|----------------------|
| `skcinfant/jianye-child-exam-v104-design.md`（564 行） | 儿童健康体检 v1.0.4 完整设计与实现进度（仅前 25 行曾被读取） |
| `skcinfant/jianye-infant-health-data-topology.md`（126 行） | 建邺儿童健康数据拓扑（仅前 60 行曾被读取） |
| `WaitForTickets/project_v3_restart.md` | 【历史】v3 Web 重启流程，撞 HttpOnly 墙后废弃，转 v4 Android |
| `WaitForTickets/project_websocket_abandoned.md` | v2 的服务端 Playwright + WS 远程认证已放弃 |
| `WaitForTickets/project_v2_checkpoint.md` | `v2-checkpoint` tag 指向 commit 740700a，保留重启前可运行的 v2 代码入口 |
| `WaitForTickets/project_phase5_integration.md` | 联调=全链路 UI + Mock 外部依赖，damai auth probe URL 侦查提前 |
| `MyRainmeterSkin/iteration-style.md` | 用户用红字批注截图给反馈，逐条批注回应 |
| `MyRainmeterSkin/direct-implementation.md` | 设计锁定后直接写代码，不要正式 plan 文档 |
| `MyRainmeterSkin/iteration-loop-86hud.md` | 6 轮 /loop 迭代，每小时一轮，前 5 轮本地 commit、第 6 轮 push；lua 解释器 + mock SKIN 验证 |

**缓解**：上述内容的**结论部分**已在二轮归档时蒸馏进 vault，未真正丢失知识——
`vault/memory/01-PROJECTS/enterprise/zhijin/skc-infant.md`、`projects/waitfortickets.md`、`projects/rainmeter-skin.md`。丢的是原始表述与被判定为"在途状态"的实现进度明细（分支进度、commit 号、TODO 清单），那些在各仓自己的 `docs/` 里另有更完整版本。

**教训**：删除机器本地记忆前，备份必须覆盖**本轮要动的全部目录**，不能只备份上一轮的范围。

---

## 各归档的原始位置

```
codex/                              ← ~/.codex/memories/
claude/-Users-dalwin/               ← ~/.claude/projects/-Users-dalwin/memory/
claude/-Users-dalwin-Library-CodeRepo/  ← ~/.claude/projects/-Users-dalwin-Library-CodeRepo/memory/
claude-per-project-salvaged/<项目>/ ← ~/.claude/projects/<对应 repo 路径编码>/memory/
```

## 相关决策

- [ADR-0021](../../../adr/0021-三套记忆收敛与wrap退役.md) — 三套记忆分工定案（方案 C：自动记忆当入口，vault 当归档）与首轮归档
- [ADR-0022](../../../adr/0022-vault维护宪法与二轮归档.md) — vault 维护宪法、二轮归档、INDEX 瘦身
