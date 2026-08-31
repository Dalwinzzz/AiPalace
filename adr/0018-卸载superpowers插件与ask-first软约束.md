# ADR-0018：卸载 superpowers 插件与 ask-first 软约束

- 状态：已接受
- 日期：2026-07-27
- 决策人：dalwin
- 关联：**Supersedes** [ADR-0012](0012-superpowers-ask-first兜底与Codex挂载.md)（superpowers ask-first 兜底 + 挂入 Codex）

## 背景

ADR-0012 为 superpowers 建立了双工具兜底机制：Claude 侧靠插件级 SessionStart 强注入 `using-superpowers` + 全局指令文件里的 ask-first 软约束双保险，Codex 侧把 superpowers 仓库的 14 个 skill 软链进 `~/.codex/skills/` 并配同一条 ask-first 软约束兜底触发。

半年后回看，dalwin 判断：以当前模型能力，superpowers 那套"强制 invoke 流程 skill"的方法论已经偏重——无论是 `using-superpowers` 的强注入语气，还是 ask-first 的"先说明再征求同意"仪式，都在为一个模型自身已具备的判断力（何时该系统拆解、何时该先写计划、何时该先验证再收尾）加一层流程开销。dalwin 计划参照当前更新的开源社区工作流，对本地 harness 重新做一版设计，superpowers 不再是这版设计的基础组件。

## 决策

**双工具彻底卸载 superpowers，相关软约束一并移除**：

1. **Claude Code**：
   - `claude plugin disable superpowers@claude-plugins-official`
   - `claude plugin marketplace remove superpowers-marketplace`（移除 `obra/superpowers-marketplace` 来源，`~/.claude/plugins/marketplaces/` 与 `cache/` 下的 superpowers 残留已清理）
   - 走官方 CLI 操作，不手编 `installed_plugins.json` / `known_marketplaces.json`（与 [plugins.md](../docs/governance/product-assets/plugins.md) 既有原则一致）
2. **Codex**：删除 `~/.codex/skills/` 下 14 个 superpowers skill 软链（`brainstorming`、`systematic-debugging`、`test-driven-development`、`writing-plans`、`executing-plans` 等）与顶层 `~/.codex/superpowers` 软链。仅解除挂载，未删除源仓库 `~/Library/CodeRepo/AI/superpowers`（该仓库不属于 AiPalace SOT，是否留存/删除由用户后续另行决定）。
3. **AiPalace 文档**：
   - `vault/memory/00-RULES/operating-rules.md` 删除「superpowers 技能 — ask-first」整节
   - `context/native/claude-global.md` 删除"superpowers 注入"条目
   - `context/native/codex-global.md` 删除"superpowers 注入"条目

## 后果

**正面**：两工具都不再有 superpowers 相关的自动加载、强注入或软约束，为按开源社区最新工作流重做本地 harness 清空前置负担；卸载走官方 CLI，未产生手编状态文件的技术债。

**取舍 / 待观察**：
- superpowers 提供的流程方法论（系统化调试、TDD、写计划再执行、完成前验证）不再有专属 skill 兜底，需在后续新工作流设计中评估是否需要等价能力、以何种形式承载（新 skill？直接内化为默认行为？）——本 ADR 只记录"卸载"这一步，不预判后续设计。
- `~/Library/CodeRepo/AI/superpowers` 源仓库暂保留未删，若确认不再需要应由用户显式清理（非本仓库 SOT 范围，AiPalace 不代管）。
- ADR-0012 中"Codex 侧 superpowers skill 软链不受 skillctl 治理"的记录随本次卸载而失效，但按 P8 不删改旧 ADR，仅由本 ADR supersede。

## 后续更新（同日）：个别挑取重新挂载 2 个 skill

卸载后复查 `skills/mine/**`，发现两处**运行时真依赖**（非"蒸馏内化"式引用）尚未有替代实现：

- `git-merge-conductor` Stage 3（复杂 mode）委托建 worktree
- `spec-architect` continue-to-coding.md（complex 分支）推荐先出计划

按 skill-management 规范正规纳入，不再走整插件路径：

- 新增来源 `superpowers`（`skills/community/superpowers/`），硬拷贝 `using-git-worktrees`、`writing-plans` 两个 skill（含 `_SOURCE.md` 溯源、LICENSE），并把 `superpowers` 补进 `tools/upstream_sync.py` 的自动映射（此前是"仅追踪仓库、无映射"的挂起状态）。
- registry 登记为 `tier: project, project: zhijin,zhijin_etl`（与消费方 `spec-architect` 的项目归属对齐；`git-merge-conductor` 本身是 `tier: core` 全局技能，此依赖只在这两个项目内可用，其余项目沿用 Stage 3 已有的"worktree 创建失败则降级主仓 checkout 并告警"兜底，不阻断）。
- `writing-plans` 上游原文仍引用未挂载的 `superpowers:subagent-driven-development` / `superpowers:executing-plans`（用户决策：只挂最小依赖，不追全链路），内容保持逐字硬拷贝不改，仅在 `_SOURCE.md` 里记录此局限。
- `git-merge-conductor` 自身文档里的 `superpowers:using-git-worktrees` 引用改回不带插件前缀的 `using-git-worktrees`（现挂载名）。
- `skillctl doctor` 全绿（31 skill）、`mount zhijin` / `mount zhijin_etl` 已实际执行并落盘。
