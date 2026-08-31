# ADR-0019：mine skill 轻量化（本地 harness 迭代第一步）

- 状态：已接受
- 日期：2026-08-03
- 决策人：dalwin
- 关联：承接 [ADR-0018](0018-卸载superpowers插件与ask-first软约束.md)（卸载 superpowers）；本轮为「本地 harness 配置迭代」的第一步

## 背景

`skills/mine/` 下 5 个自建 skill 均诞生于 2025 下半年（Codex GPT-5.1 / Claude Opus 4.5 时期）。当时的模型在流程自觉性上尚需外部约束，因此这批 skill 里写了大量**防合理化脚手架**：TDD 的"借口 vs 现实"对照表、RCA 的红旗清单、verify 的"声明↔证据"矩阵、spec 模板逐字段的"正确示例 / 错误示例"、质量检查清单等。

一年后模型能力已迭代，这类"提醒模型该系统拆解 / 该先验证再宣称完成"的内容已被模型自身内化，继续常驻只是 token 开销与阅读噪音。dalwin 判断：**保留领域知识与本地事实，砍掉方法论复述**。

同时，`spec-architect` 的模板走到了另一个极端——578 + 329 行的两份逐字段模板把 spec 的每个字段都规约死了，反而压制模型按任务实际形态发挥。

## 决策

**原则：留下"不查就会做错"的，砍掉"模型自己就会"的。**

判据三条：① 本地环境事实（命令、路径、命名规范）→ 留；② 领域判据与安全不变式（审查维度、冲突分类、不动目标分支）→ 留；③ 通用方法论复述与防合理化话术 → 砍。

### 1. biz-workflow → `tier: parked`（下线）

自身 description 已标注"已被 ownerpowers 取代，验证期保留为对照"，验证期实际早已结束，`references/` 与 ownerpowers 高度重复。摘出全局与项目挂载，仓内留档（P6 可逆）。

### 2. ownerpowers：7 文件 → 4 文件

- `disciplines/{tdd,rca,verify}.md`（125 行）→ `disciplines.md`（约 45 行）：三条铁律各压成一句话，**保留** Maven 本地 `settings.xml` + 独立仓库路径 + JDK8 切换的实际命令、切片 vs 单元测试的取舍、Spring/Go 常见根因入口、多组件先在边界打日志的定位法。砍掉 RED→GREEN→REFACTOR 分步教学、合理化对照表、红旗清单、声明↔证据矩阵。
- `policies/{worktree,subagent}.md` → `policies.md`：**保留**分支命名硬规范（含"冒号被 git ref 拒绝、须用连字符"这条实测结论）与 subagent 三类触发 + opus/effort 配置，压缩其余。
- SKILL.md 删除已失效的「superpowers ask-first 兜底」条目，路由表去掉对已删文件的引用。

### 3. spec-architect：12 文件 → 3 文件（重点）

- `templates/{claude-code,codex}.md`（907 行）→ `templates/spec.md`（约 130 行）：**从"每个字段怎么写"改为"一份好 spec 需要哪些部分、每部分要回答什么问题、怎么算写好了"**，附一份可裁剪的骨架与两工具差异说明。删掉三套完整 markdown 骨架、逐字段正确/错误示例、质量检查清单。
- `references/{tool-detection,codex-workflow,claude-code-workflow,mid-recon-interaction,anti-patterns,continue-to-coding,auto-commit}.md` 全部折叠进 SKILL.md：每份文件里真正非显然的规则（AGENTS.md/CLAUDE.md 不能单独判定工具、歧义当场问、commit 后不停下来等"继续"、auto-commit 不跳钩不 amend）各压成一到数行。SKILL.md 133 → 约 95 行。
- 保留 `references/mermaid-style-guide.md`——渲染失败规避是实测得来的外部事实，非方法论。

### 4. commit-review：清引用 + 瘦论证

删除全部 superpowers 引用（`requesting-code-review` / `subagent-driven-development` / `dispatching-parallel-agents` 已随插件卸载不存在，报告模板里的"审查依据"也一并改），压缩"为什么强制走子代理"的论证段。**13 条审查维度准绳完整保留**——那是领域判据，不是方法论。

### 5. git-merge-conductor：只削仪式，不动逻辑

这是本轮唯一**基本保留**的 skill：它的价值在可恢复状态机与冲突领域判据，不是流程说教。仅三处削减——放松"stage_history 必须正好 11 条，任何缺口都是 bug"的记账式表述（改为"不得静默跳阶段"，resume 语义不变）、Stage Banner 去掉"non-negotiable"话术保留格式与用途、5 条 Quick Sanity Checks 压到 2 条（只留模型无法自行推断的：目标分支未被改动、实际 stage 与心智模型一致）。全部 `references/` 契约文件未动。

## 顺带修复：spec-architect / commit-review 从未入库（P1 违反）

本轮发现全局 `~/.config/git/ignore` 里的 `**/spec-architect/` 与 `**/docs/commit-review/`（本意屏蔽各业务项目中 AI 生成的 spec / 审查报告产物）**误伤了本仓的 skill 源目录**——`skills/mine/spec-architect/` 12 个文件从来没进过 git 历史。已在仓库级 `.gitignore` 加反排除规则（仓库级优先于全局；因排除的是目录，须同时反排除目录本身与其内容）。

## 后果

**正面**：三个被改的 skill（ownerpowers / spec-architect / commit-review）合计 2573 → 1309 行（-49%）；剔掉两侧未变的 `mermaid-style-guide.md`（280 行）后是 2293 → 1029 行（-55%）。另有 biz-workflow 314 行整体退出挂载。砍掉的全是模型已内化的方法论复述；spec 模板从"填空题"变成"结构清单"，给模型留出按任务实际形态发挥的空间；superpowers 引用彻底清零；一个从未入库的 skill 回到版本控制。

**取舍 / 待观察**：
- 砍掉防合理化脚手架后，若实际使用中出现"跳过 test-first / 未验证就宣称完成"的回退，说明该约束仍有承载价值，届时按需补回**最小**形式，而非整块恢复旧文（本 ADR 不预设结论）。
- `biz-workflow` 为 parked 而非删除，若三个月内未被显式 invoke，下一轮可考虑真正移除。
- superpowers 插件本轮已用 `claude plugin uninstall` 真正卸载（ADR-0018 当时误判"无 uninstall 子命令"，只做了 disable；`installed_plugins.json` 条目现已清除，`~/.claude/plugins/cache/` 下的版本目录属 CLI 自管缓存，未手动干预）。
