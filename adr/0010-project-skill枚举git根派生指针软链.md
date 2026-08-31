# ADR-0010：project skill 挂载枚举 git 根派生指针软链

- 状态：已接受
- 日期：2026-06-26
- 决策人：dalwin
- 关联：落实用户「公司级 project skill 在每个子项目内可直接使用 / 自动触发」需求；延续 [P2 声明式派生](../PHILOSOPHY.md#p2--声明式管理工具派生限内容资产)、[P6 零破坏演进](../PHILOSOPHY.md#p6--零破坏演进)；同批登记 community/blader/humanizer 与 community/op7418/humanizer-zh（zh 版只取 star 最高主流版，不引 fork）

## 背景

`skillctl mount <proj>` 原仅在 registry `projects:` 声明的**单一项目根**（umbrella）下建 `<umbrella>/.claude/skills/<skill>` 软链。但 Claude Code 官方 skill 发现规则（[docs](https://code.claude.com/docs/en/skills)）是：

> Project skills load from `.claude/skills/` in your starting directory and **in every parent directory up to the repository root**.

即子目录启动只向上遍历**到 git 仓库根为止，绝不再往上**。

实测病灶：`projects.zhijin = ~/Library/IdeaProject/ZhiJin` 是个 **IDEA 伞形目录**，其下 `SunkidCloud/skcservers/skcactivity` 等业务模块**各自是独立 git 仓**。会话在 `skcactivity` 启动，向上遍历到 `skcactivity`（其 git 根）即停，够不到上方 4 级的 `ZhiJin/.claude/skills`——于是 umbrella 挂的 project skill 在子项目里**完全不可见**，`/` 菜单与自动触发都拿不到。

调研的其他路径均被否决：提升到 user 级会污染所有项目 `/` 菜单 + 吃预算（[P4](../PHILOSOPHY.md#p4--分级控预算tier)）；做成 plugin 经 settings 开启**更不向上遍历**（[issue #46107](https://github.com/anthropics/claude-code/issues/46107) 实证 plugin 发现连父目录都不遍历）；`--add-dir` 是启动参数、非声明式。

## 决策

**`mount` / `unmount` 在 umbrella 之外，枚举 umbrella 下的每个 git 仓根，逐根派生同一套受管指针软链。**

1. **新增 `git_roots(base, max_depth=6)`**：从 base 向下遍历，凡含 `.git`（目录或文件，后者覆盖 submodule/worktree）的目录即记为 git 根；剪枝噪声目录（`.git` / `.claude` / `.codex` / `node_modules` / `.venv` / `venv` / `target` / `build` / `dist` / `.gradle` / `.idea` / `__pycache__` / `out`）与 `max_depth` 双重兜底成本；**不在找到的根处剪枝**，以便捕获嵌套的独立仓（伞内可能 repo-in-repo）。base 不存在 → 返回 `[]`。剪枝含 `.claude`/`.codex` 的关键作用：避免下沉到 `<repo>/.claude/worktrees/` 下的 superpowers 临时 worktree（临时、嵌在配置目录内、随用随清，不应获得持久 project skill 挂载）。
2. **指针软链 = 直接指向 AiPalace 真身**：每个 git 根的 `<root>/.claude/skills/<name>` 软链目标 = `skills/<class>/<source>/<skill>`（与 umbrella 挂载同 target，绝对路径落在 `SKILLS` 内）。**刻意不做「目录级指针」（`<root>/.claude/skills -> umbrella/.claude/skills`）**：后者 realpath 落在 umbrella 而非 `SKILLS`，会让 `is_managed()` 判否、prune/unmount 清不掉，破坏受管标记不变量（[P6](../PHILOSOPHY.md#p6--零破坏演进)）。逐 skill 指向 `SKILLS` 则完全复用既有 `is_managed` / 悬挂检测 / 保护跳过逻辑。
3. **umbrella 始终保留**（向后兼容 + 覆盖恰在 umbrella 根启动的会话）；`targets = dedup([umbrella] + git_roots(umbrella))`。
4. **受管边界不变**：逐根挂载仍只建/清「指向 `SKILLS` 内」的软链；对各 `.claude/skills` 下的**非受管手建物保护跳过**，`unmount` 只清受管软链，零误删。
5. **CLI**：`mount/unmount <proj>` 默认递归；加 `--no-recurse` 回退「仅 umbrella」旧行为；`--dry` 预览。
6. **doctor 不变**：project 挂载本就是 opt-in、不进 doctor 漂移检查（doctor 只校验全局 core/extra 挂载与 registry 完整性），本 ADR 不扩 doctor 职责，控制爆炸半径。

## 后果

**正面**：umbrella 下每个独立 git 仓启动的会话都能在自身 git 根命中 project skill，`/` 菜单可见 + 自动触发；单一真源不破（所有指针仍指向 AiPalace `SKILLS`）；声明式——只改 registry，`mount` 自动枚举派生；完全复用既有受管/保护/prune 机制，无新受管语义。

**取舍 / 待观察**：
- **枚举到 `max_depth` 内的全部 `.git` 根**：若伞内存在 submodule / vendored repo，会被一并挂载。指针软链无害且 `unmount` 可清，接受此取舍；如日后噪声过多，再加显式 ignore 列表（[P9](../PHILOSOPHY.md#p9--显式过渡态) 显式过渡态）。
- **`git_roots` 仅在 `mount/unmount` 时遍历**（非 sync/doctor 热路径），伞形目录大时一次遍历有成本，靠剪枝 + `max_depth` 兜底；如遇超大伞可调小 `max_depth`。
- **worktree 场景**（[issue #45956](https://github.com/anthropics/claude-code/issues/45956)）：**刻意不挂** `<repo>/.claude/worktrees/` 下的 superpowers 临时 worktree（剪 `.claude`）——它们临时、随清，挂了反成嵌套 `.claude/skills` 噪声。代价是 worktree 会话看不到 project skill；该场景的可见性留给 SessionStart hook 兜底，或在 worktree 内手动 `mount`（观察项，由本 ADR 记录）。
- **新增 git 仓后需重跑 `mount`**：枚举是 mount 时一次性快照，伞内新 clone 的仓不会自动获得软链，须再次 `skillctl mount <proj>`。
