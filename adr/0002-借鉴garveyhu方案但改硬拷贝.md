# ADR-0002：借鉴 garveyhu skill-management 方法论，但落地形态改用硬拷贝

> ⚠️ **被 [ADR-0005](0005-实测修正symlink可见性并回归symlink派生.md) 推翻/修正（2026-06-17）。**
> 本 ADR 据 #14836 判定"symlink 进 `~/.claude/skills` 不出现在 `/` 斜杠菜单"——经 2026-06-17 本地实测，
> 这是**错误结论**：软链 skill 在 `/` 斜杠菜单正常显示，#14836 仅影响 `/skills` **管理命令**。因此"改硬拷贝"
> 的决策已被 ADR-0005 推翻、派生形态回归 symlink。**本文保留不删改，作为实证演进的真实记录
> （P8 决策留痕 / P9 显式过渡态）。**

- 状态：~~已接受~~ → **被 ADR-0005 推翻/修正**
- 日期：2026-06-16
- 决策人：dalwin
- 关联：[ADR-0001](0001-AiPalace为个人AI-harness唯一SOT.md)；被 [ADR-0005](0005-实测修正symlink可见性并回归symlink派生.md) supersede

## 背景

同事 garveyhu 开源的 `skill-management`（`method/skill-management/SKILL.md`）提出一套
优雅的 skill 规模化管理法：**来源→分类→skill 三级** + 单一 `registry.yaml` + `tier`
控 token + `skillctl.py`（sync/doctor）把派生物自动化，「只改 registry 跑 sync」防腐化。

其 `sync` 的派生形态是 **symlink**：把 skill 真身目录软链进各 agent 的 skill 目录
（Claude Code 填 `~/.claude/skills`）。

## 问题：Claude Code 对 ~/.claude/skills/ 下 symlink 的已知缺陷

评估时核对官方文档与 anthropics/claude-code issue 后确认：Claude Code 在 skill
**发现/校验阶段**的目录扫描不跟随 symlink（缺 `find -L` 等价逻辑），导致软链进
`~/.claude/skills/` 的 skill：

- ✅ **能被模型自动触发/加载**（执行阶段直接读文件，会跟随软链）；
- ❌ **不出现在 `/skills` 列表与 `/` 斜杠菜单**（发现阶段看不到）。

证据：
- [issue #14836](https://github.com/anthropics/claude-code/issues/14836)（2025-12-20 开，**至今 open**）：
  软链 skill 跑 `/skills` 显示 `No skills found`，原文明确 *"even though the skill is
  correctly loaded and usable by the model"*。根因即扫描未跟随软链
  （`find -L` 能列出、`find` 不能）。
- [issue #37590](https://github.com/anthropics/claude-code/issues/37590)：请求 `.claude/skills/`
  支持 symlink（对标已支持软链的 `.claude/rules/`），被 **closed as duplicate**，无修复计划。

附带约束：Claude Code 还有 `skillListingBudgetFraction` /
`SLASH_COMMAND_TOOL_CHAR_BUDGET` 预算上限，skill 数量大时描述会被降级为 name-only。

## 决策

**保留 garveyhu 方法论内核**（三级结构 + registry + tier + sync/doctor + 防腐化工作流），
**只把 `sync` 的派生形态从 symlink 换成硬拷贝（`shutil.copytree`）**。代价是 skill 改动后
需重跑 sync、占额外磁盘；换来的是 `/` 斜杠菜单对所有挂载 skill 完整可见，不赌 issue 何时修。

配套对 `skillctl.py` 的三处改造（见 `tools/skillctl.py` 头注释）：
1. **硬拷贝**替代 symlink；
2. 支持 source 内带子路径的 key（如 `garveyhu/style-vault`），适配三级保真目录；
3. **受管标记 `.aipalace-managed`**：prune 只回收本工具写入的拷贝，
   遇到用户手建的软链/真实 skill 一律保护跳过，**零误删**保护现有 `~/.claude/skills` 体系。

双 mount：`mounts` 同时写 `~/.claude/skills` 与 `~/.codex/skills`
（Codex 自 2025-12 起原生支持 skill 自动发现，目录 `~/.codex/skills`/`~/.agents/skills`），
一次 sync 同步两个工具 —— 这正是该方法论"多 agent 统一源"的最大价值。

## 后果

- 正面：`/` 菜单完整可见；双工具一次同步；prune 零误删。
- 负面：skill 源码改动后须重跑 sync 才生效（symlink 本可即时生效）；拷贝占磁盘
  （当前 community 备份约 25M，可接受）。
- 备注：本轮（2026-06-16）只搭骨架、未执行 sync。`sync --dry` 已验证可正确定位 49 个
  skill 真身、且对现有非受管软链全部保护跳过。
