# ADR-0015：project skill 双发现路径派生，补齐 Codex 侧项目级挂载

- 状态：已接受
- 日期：2026-07-02
- 决策人：dalwin
- 关联：扩展 [ADR-0010](0010-project-skill枚举git根派生指针软链.md)（枚举 git 根派生，仅覆盖 `.claude/skills`）；延续 [P5 实证选型](../PHILOSOPHY.md#p5--实证选型不照搬)、[P6 零破坏演进](../PHILOSOPHY.md#p6--零破坏演进)、[P7 内容统一源机制分治](../PHILOSOPHY.md#p7--内容统一源机制分治)

## 背景

实测病灶（2026-07-02，Codex 会话 `rollout-2026-07-02T10-52-18-*.jsonl`，nursery 业务任务）：会话注入的 `<skills_instructions>` skill roots 仅含 `~/.codex/skills`、`~/.codex/skills/.system` 与插件缓存目录，registry 中 `tier: project, project: zhijin` 的 4 个 skill（`ownerpowers` / `biz-workflow` / `spec-architect` / `zhijin/liquibase-dual-db-writer`）**完全不在列表中**，隐式触发无从谈起——biz-workflow「决策点①定调后须停等拍板」纪律因此未生效。

根因是**发现路径零重叠**，属设计缺口而非执行漂移：

- **Claude Code**（[官方 docs](https://code.claude.com/docs/en/skills)）：项目级只扫 `.claude/skills/`（cwd 逐级向上至 git 仓根 + 子目录按需），**不扫 `.agents/skills`**。
- **Codex**（[官方 docs](https://developers.openai.com/codex/skills)）：项目级只扫 `.agents/skills`（cwd 逐级向上至 git 仓根），另有用户级 `~/.agents/skills`、admin 级 `/etc/codex/skills`、全局 `$CODEX_HOME/skills`（即 `~/.codex/skills`，本机已实测生效——core/extra 全局挂载正常出现在 skill roots）；扫描时跟随 symlink。
- **本机版本证实**：codex-cli 0.142.5 二进制 strings 含 `.agents` + `skills` 路径段拼接（`.agentsskills`），确认该版本已支持 `.agents/skills` 发现。

ADR-0010 的 `mount`/`unmount` 只派生 `<git根>/.claude/skills/`，Codex 侧项目级结构性照不到。全局 tier（core/extra）双工具均已打通（`~/.claude/skills` + `~/.codex/skills`），缺口仅在 project tier。

## 决策

**`mount` / `unmount` 在每个目标（umbrella + 各 git 仓根）同时派生/清理两个发现目录：`.claude/skills/`（Claude Code）与 `.agents/skills/`（Codex）。**

1. **新增 `PROJECT_SKILL_DIRS = (".claude/skills", ".agents/skills")`**：mount/unmount 对每个 target 逐目录执行既有 `_link_project_skills` / 受管清理逻辑，软链目标同为 AiPalace 真身（`skills/<class>/<source>/<skill>`），完全复用 `is_managed` / 悬挂检测 / 非受管保护跳过。
2. **不会重复触发**：两工具各只扫自己的目录（实证见背景），双路径派生互不可见，无菜单/注入重复。
3. **`GIT_ROOT_SKIP` 增 `.agents`**：与 `.claude`/`.codex` 同理，git 根枚举不下沉配置目录。
4. **不启用 `~/.agents/skills` 用户级路径解决本问题**：它是全局作用域，project tier 的本意就是「移出全局、按项目 opt-in」（P4）；用用户级路径会把公司 skill 泄给所有项目会话。flat_mirror（`~/.agents/skills`）仍维持注释占位，供日后 core 默认加载层使用，与本决策正交。
5. **doctor 职责不变**（同 ADR-0010 第 6 条）：project 挂载 opt-in、不进 doctor 漂移检查。

## 后果

**正面**：project skill 在两工具的项目级会话中对称可见——Claude 经 `.claude/skills`、Codex 经 `.agents/skills`，均在各自 git 根命中；单一真源不破（指针仍指向 AiPalace）；声明式不变（registry → mount 派生）；机制分治（P7）——同一内容、两工具各自的发现机制各挂各的。

**取舍 / 待观察**：
- **公司仓根多出未跟踪的 `.agents/` 目录**：与既有 `.claude/skills` 软链同性质（untracked、不入库）；如团队仓有严格目录规约，可按仓加 `.git/info/exclude`。
- **Codex 对 project skill 无 ask-first 之外的注入兜底**：本 ADR 只解决「可发现」，隐式触发质量取决于各 SKILL.md 的 description 触发语；vault INDEX 决策树文本仍为语义提示层（ADR-0007），两层互补。
- **`.agents/skills` 为 agentskills.io 开放标准目录，Claude Code 日后若原生支持**，可能出现双目录同名 skill 并存；届时实测去重行为后再决定是否收敛为单目录（P5，留待观察）。
- **新增 git 仓后需重跑 `mount`**（继承 ADR-0010 既有取舍）。
