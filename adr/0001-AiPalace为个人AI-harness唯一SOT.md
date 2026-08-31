# ADR-0001：AiPalace 作为个人本地 AI harness 实践的唯一 SOT

- 状态：已接受
- 日期：2026-06-16
- 决策人：dalwin

## 背景

个人本地 AI 工作流（Claude Code + Codex 双工具）的资产此前散落多处，互相用软链拼接：

| 资产 | 旧位置 |
|------|--------|
| 自建 skill 源码 + context + 演化 docs | `~/Documents/AI/dalwin-workflow/`（已是 git repo，无 remote，事实上的 SOT） |
| 我 clone 的开源 skill 安装版 | `~/Library/CodeRepo/AI/awesome-skills/` |
| 同事自创开源上游 | `~/Library/CodeRepo/AI/garveyhu/awesome-skills/` |
| 官方 skills 仓 | `~/Library/CodeRepo/AI/skills/` |
| 跨工具共享视图 | `~/.agents/skills/`（软链中转） |
| Claude/Codex 加载视图 | `~/.claude/skills/`、`~/.codex/skills/`（软链） |

问题：① 没有一个能 `git clone` 即得全貌的总仓；② "我选装了什么 / 备份了什么 / 自建了什么"
三件事混在软链拓扑里，难以一眼追溯；③ dalwin-workflow 只覆盖自建 skill 与 context，
不含开源 skill 的备份，不是完整的 harness 实践快照。

## 决策

新建 `~/Library/CodeRepo/AI/AiPalace` 作为**个人本地 AI harness 实践的唯一 SOT**，
**收编** dalwin-workflow：其 `skills/ context/ docs/ archived_skills/` 全部整理进 AiPalace
对应目录。dalwin-workflow 旧仓**本轮保留不动**（不搬空、不改其指向的 hook / path-scoped
rules / 软链），降级为「历史快照 + 待迁移源」，迁移在后续迭代分步完成。

AiPalace 用 **来源→分类→skill** 三级组织 skills，用 `registry.yaml` 单一事实源 + `tier`
分级 + `skillctl.py`（sync/doctor）派生工具，借鉴 garveyhu 的 skill-management 方法论。

## 本轮范围（2026-06-16，loop 任务）

**只建仓 + 硬拷贝备份 + 搭管理骨架**，明确**不**做以下事：
- 不执行 `skillctl sync`（不向 ~/.claude、~/.codex 写任何东西）；
- 不删除/改动任何现有软链、hook、path-scoped rules；
- 不搬空 dalwin-workflow。

链路改指向 AiPalace、SOT 正式切换等，留给醒后亲自推进（见 `NEXT-STEPS.md`）。

## 后果

- 正面：一个仓库即个人 harness 全貌，可 git 追溯；选装/备份/自建三态由 registry 显式表达。
- 待解：**两个 SOT 暂时并存**（dalwin-workflow 与 AiPalace）。这是已知的过渡态，
  必须在后续迭代中收敛为一个，否则 /wrap 沉淀、hook 注入会指向旧仓造成漂移。
  收敛方案见 NEXT-STEPS 待决策项。
