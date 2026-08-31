# ADR-0006：同步 garveyhu skill-management 新版——四层 tier + 扁平镜像 + project 挂载

- 状态：已接受
- 日期：2026-06-25
- 决策人：dalwin
- 关联：延续 [ADR-0002](0002-借鉴garveyhu方案但改硬拷贝.md)（借鉴 garveyhu 方法论）、[ADR-0005](0005-实测修正symlink可见性并回归symlink派生.md)（symlink 派生）

## 背景

garveyhu 的 `skill-management` 方法论（`method/skill-management/SKILL.md`）更新了一版，相对本仓库当前实现新增：

1. **`tier: project`（四层加载）**：在 `core/extra/parked` 之间加一层，把"只在某工作目录才用得到"的 skill **移出全局挂载点**（`sync` 从全局 prune），按 `projects:` 段声明 `<项目名>: "<绝对路径>"`，默认只"声明 + 移出"、不挂载；要用时 `skillctl mount <项目>` 软链进该目录的 `.claude/skills/`，`unmount` 撤销。
2. **扁平镜像 `<root>/skills/`**：把 `tier=core` 的 skill 软链**拍平成一层**（不带来源/分类/tier 层级），供"会扫描整个目录的通用 agent"使用，相当于"默认加载层"。
3. 配套 `skillctl mount/unmount` 子命令、stats 显示项目级 skill。

用户要求：先验证这一版 project 级挂载能否在 Claude Code 正常工作，可行则同步本仓库方案。

## 实测（P5 实证，2026-06-25，Claude Code v2.1.179）

在 AiPalace（git 根）建 `.claude/skills/projtest-wiki-creator` 软链（指向 parked 的 garveyhu `wiki-creator` 真身，确认该 skill 当前不在 user 级挂载），新 session 实证：

| 观察点 | 结果 |
|--------|------|
| `/skills` 管理命令 | ✅ 显示，标 **`project · ~130 tok · ✓ on`**（project 级加载铁证） |
| `/` 斜杠菜单 | ✅ 可见——但以 **`SKILL.md` 的 `name` 字段**（`wiki-creator`）显示/搜索，**不是挂载目录名**（`projtest-wiki-creator`） |
| 模型自动触发 | ✅ 可用（动态注入到 session 可用 skill 列表） |

**结论：project 级 symlink skill 可被 Claude Code 正常发现加载。**

附带发现：
- v2.1.179 的 project 级 `/skills` **对软链可见**——优于 ADR-0005 当时 user 级 `/skills` 受 [#14836](https://github.com/anthropics/claude-code/issues/14836) 影响的情况（可能已修，或 project 级扫描跟随软链）。
- **斜杠菜单用 `SKILL.md` 的 `name` 字段显示，而非挂载目录名**——这是同步时必须记入规范的实现细节。

官方文档佐证：project skills 从「cwd 及其所有父目录直到 repository root」的 `.claude/skills` 自动加载（git 共享），子目录工作时按需发现 nested（monorepo）。garveyhu「路径须指向 git 根」是保守约束（保证任何 cwd 都能加载），合理。

## 决策

同步 garveyhu 新版，**机制就绪、本轮不碰现役挂载**（实际写 `~/.agents`、`~/.claude` 等现役配置留 SOT 切换 final-spec，与 P1–P3 边界一致）：

1. **四层 tier**：`core / extra / project / parked`。`tier: project` 的 skill 从全局挂载点 prune 移出，按 `project:` 字段归属项目。
2. **扁平镜像（core 拍平）**：`core` skill 软链拍平成一层（**不包 core 目录层**，与现役 `~/.agents/skills` 形态一致）作"默认加载层"。落点路径**配置化**（registry 声明），实际指向 + 现役对账留 SOT 切换。
3. **project 挂载**：registry 加 `projects:` 段；`skillctl mount <项目>` / `unmount <项目>` 软链进 `<项目>/.claude/skills/`（真身仍在来源目录，单一事实源不破）；默认 `sync` 不自动挂（opt-in）。
4. **挂载名 = `SKILL.md` 的 `name`**：实测斜杠菜单用 `name` 显示，故 project skill 的挂载名须等于其 `name`（避免目录名与 name 不一致导致 `/` 菜单搜不到，本次实测即因 `projtest-` 前缀暴露）。

## 取舍

- **不同步** garveyhu 的"白名单 `.gitignore` 专门机制"——AiPalace 已有 `.gitignore` + `community/` 硬拷贝备份层（ADR-0003），来源天然隔离。
- **扁平镜像 vs Codex 挂载点对账**：现役 `~/.agents/skills` 是扁平层（Codex 从此发现），`~/.codex/skills` 基本空，registry 写的 `~/.codex/skills` 与现状不符——这个对账留 SOT 切换处理，本轮只让 skillctl 具备生成扁平镜像的能力（路径配置化 + dry 预览）。
- 本轮 skillctl 的扁平镜像/mount 能力均以 `tmp` 测试覆盖，不向真实现役挂载落盘。

## 后果

- 正面：四层 tier 控制更精细（project 移出全局省 token、按需 opt-in）；扁平镜像给通用 agent 一个"默认加载层"；与 garveyhu 上游对齐、便于复刻分享（可分享方法论）。
- 待办（留 SOT 切换 / 后续）：扁平镜像与 Codex 挂载点的现役路径对账；实际挂载落盘。

## 待落盘（交 P4 plan + subagent 执行）

1. `registry.yaml`：加 `projects:` 段 + 可选 `flat_mirror` 路径声明；支持 `tier: project` + skill 的 `project:` 字段。
2. `tools/skillctl.py`：`load_registry` 解析新字段；`sync` 把 `tier:project` 移出全局 + 生成扁平镜像（core 平铺）；新增 `mount/unmount <项目>`；`stats` 显示 project 级 + 扁平镜像；维持现有 symlink/is_managed/doctor/--fix 不破坏；补 pytest（tmp 隔离）。
3. `docs/governance/content-assets/skills.md`：tier 表加 **project** 第四层 + 扁平镜像「默认加载层」+ project 挂载机制 + **「挂载名 = `SKILL.md` name」** 实测细节。
