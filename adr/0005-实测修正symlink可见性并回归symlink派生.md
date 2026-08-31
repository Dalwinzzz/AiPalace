# ADR-0005：实测修正 symlink 可见性结论，skill 派生形态回归 symlink

- 状态：已接受
- 日期：2026-06-17
- 决策人：dalwin
- 关联：**Supersedes [ADR-0002](0002-借鉴garveyhu方案但改硬拷贝.md) 的硬拷贝决策**；延续 [ADR-0001](0001-AiPalace为个人AI-harness唯一SOT.md)

## 背景

[ADR-0002](0002-借鉴garveyhu方案但改硬拷贝.md) 基于 [issue #14836](https://github.com/anthropics/claude-code/issues/14836)，
判定"symlink 进 `~/.claude/skills` 的 skill 能被模型自动触发，但**不出现在 `/skills` 列表与 `/` 斜杠菜单**"，
据此把 `skillctl sync` 的派生形态从 symlink 改为**硬拷贝（`shutil.copytree`）**。代价是：skill 改动后须重跑
sync、占额外磁盘、真身与拷贝可能漂移、prune 逻辑复杂化。

## 新证据（2026-06-17 本地实测）

1. `~/.claude/skills` 下当前 13 个条目**全部是 symlink**（指向 `~/.agents/skills`、`dalwin-workflow/skills`、
   `CodeRepo/AI/awesome-skills|skills` 各源）。
2. 其中 6 个——`docker-best-practices`、`docx`、`find-skills`、`gemini-svg-creator`、`git-merge-conductor`、
   `grill-me`——**确认出现在 `/` 斜杠菜单**（用户截图证据）。菜单里另有 `executing-plans`、
   `finishing-a-development-branch`、`frontend-design`、`goal` 等，经核对是**插件**提供的 skill（不在
   `~/.claude/skills`），已排除干扰。
3. `gh` 复核：**#14836 仍 OPEN**（更新于 2026-06-03），但其标题精确为
   *"`/skills` command doesn't find skills in symlinked directories"*——只针对 **`/skills` 管理命令**；
   [#37590](https://github.com/anthropics/claude-code/issues/37590) 仍 closed-as-duplicate。

## 根因

ADR-0002 把**两条不同的发现路径**混为一谈：

| 路径 | 用途 | 对软链 skill 的实测表现 |
|------|------|------|
| **`/` 斜杠菜单**（slash 自动补全） | 显式调用 skill | ✅ **正常显示** |
| **`/skills` 管理命令** | 列出/管理已装 skill | ❌ #14836 所述缺陷在此；即便失效也**不妨碍用 `/` 调用** |

因此 ADR-0002"为让 `/` 可见而改硬拷贝"的**核心前提不成立**——软链 skill 本就能在 `/` 斜杠菜单可见。

> 待补实证：`/skills` 管理命令对软链 skill 是否真的列不出，留一次实测确认（不影响本决策）。

## 决策

1. **skill 派生挂载形态回归 symlink**（garveyhu 原版精神）。中圈+外圈由 `registry.yaml` 声明派生
   （`skillctl` 软链回仓库真身），内圈手动显式 symlink；三圈挂载统一为 symlink，`/` 斜杠菜单均可见。
2. **区分两层、互不混淆**：
   - **仓库内 SOT 存储层**：`community/`、`enterprise/` 的硬拷贝是**备份快照，保留不动**（溯源 + 防上游漂移）。
   - **sync 派生挂载层**：从 `copytree` **改回 symlink**（指回仓库真身）。
3. 对应设计哲学总纲 **P2 修订为"全圈 symlink 挂载"**；ADR-0002 标注被本 ADR supersede、正文保留。

## 后果

- **正面**：省掉硬拷贝全部代价（改后重 sync、占磁盘、源码漂移、prune 复杂）；symlink 即时生效；
  双 mount（Claude + Codex）同样可做；总纲 P2 内圈"symlink vs `/` 可见"的冲突直接消解。
- **负面**：依赖 symlink 的下游工具（备份/分发）需注意是否跟随软链；`/skills` 管理命令对软链的已知缺陷
  继续存在（但不影响核心用法）。
- **决策方式**：本 ADR 不删改 ADR-0002，采 **append-only supersede**——保留走过的弯路作为实证演进的真实记录
  （践行 P8 决策留痕 / P9 显式过渡态）。

## 待落盘改动（随治理 spec 定稿统一执行，本轮不改代码）

1. `tools/skillctl.py`：`sync` 从 `shutil.copytree` 改回 `os.symlink`，保留双 mount + `.aipalace-managed`
   prune 保护 + 三级路径前缀（`garveyhu/xxx`）支持。
2. `registry.yaml` 头注释：删除/修正"为规避 symlink bug 改硬拷贝"的表述。
3. `README.md`：三层加载策略、`sync` 安全保证等处的硬拷贝叙述改为 symlink。
4. **待细化决策点**（另行拍板）：圈层（内/中/外）↔ tier（core/extra/parked）映射；内圈手动 symlink 与
   registry 声明派生的边界；`/skills` 命令对软链行为的实测确认。
