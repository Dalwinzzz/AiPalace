# 个人全局上下文层设计 spec — 2026-06-01

> 范围：解决"工作域级规则无法跨项目自动注入"的痛点。新增一个按工作域、按需注入的个人全局上下文层（`~/.agents/context` 作为共享入口，实体在 dalwin-workflow 仓做版本控制），用 Claude **原生** path-scoped rules 实现。
>
> 决策：方案 1（原生 path-scoped rules）+ 工具中性 SOT 命名 `context` + 仅建议层。Codex 侧本次只留接口说明，不实现。

---

## 1. 背景与根因

### 1.1 现象（docs/problem 两张截图）

- **截图1（`memory没起效.png`）**：Claude 准备执行 `jar xf /Users/dalwin/.m2/repository/...`，用了默认 `.m2`，违反"绝不能用 `~/.m2`"。
- **截图2（`memory没起效问题1.png`）**：用户原话"这条记忆存在于全局用户记忆里但没有同步到本项目"——Maven 规则在某项目反复交代过，换项目后没注入。

### 1.2 根因（已查证官方文档）

官方机制：**auto memory 以 git 仓库根目录为 key**，仅同 repo 的子目录/worktree 共享；不在 git 仓库时回退 cwd（来源：code.claude.com/docs/en/memory）。

而"工作域"是**跨 repo 的语义概念**。两者错位导致：

1. `maven-config.md` 被手工复制进 **4 个** memory 目录（`-Users-dalwin` + `skciotdevice` + `skcmultimedia` + `skcnursery`），内容还不一致（一份标 `type: project`、一份标 `type: reference`）→ 每进一个新 java repo 就漏（截图2）。
2. 兜底塞进 63 行全局 `CLAUDE.md` 的 Maven 段虽每会话加载，但**埋在长文件里被稀释**（官方：文件越长 adherence 越低），且对 Go/Notion/AI 会话**过宽** → 截图1 仍失败。

**一句话**：native memory 按 git-root 隔离，工作域规则要么被复制 N 份，要么被抬到全局过宽。需要一个"按工作域、按需注入、单一源、跨工具"的新层。

## 2. 官方依据（Claude Code v2.1.159）

| 机制 | 官方表述 | 本设计用法 |
|---|---|---|
| `~/.claude/rules/*.md` 用户级规则 | "Personal rules in `~/.claude/rules/` apply to every project on your machine" | 对每个项目可用 → 不受 git-root 隔离 |
| path-scoped rules（`paths:` frontmatter） | "only apply when Claude is working with files matching the specified patterns…trigger when Claude reads files matching the pattern, not on every tool use" | 用 java 文件信号限定域内注入，不污染非 java 会话 |
| rules 支持 symlink | "The `.claude/rules/` directory supports symlinks…resolved and loaded normally, circular symlinks are detected" | SOT 单源 + symlink 视图 |
| InstructionsLoaded hook | "log exactly which instruction files are loaded, when…and why" | 验证 path-scoped rule 是否在读 pom.xml 时触发 |

## 3. 架构：SOT + 双视图（与现有 skills 架构同构）

```
~/Documents/AI/dalwin-workflow/context/        # ① 实体 SOT（git 版本控制，追溯演化）
  └── java-spring.md                            #    frontmatter paths + Maven 规则
        ▲ symlink
~/.agents/context/                              # ② 跨工具共享入口（工具中性，"个人全局上下文"）
  └── java-spring.md  ──▶  ①
        ▲ symlink
~/.claude/rules/                                # ③ Claude 加载视图（官方约定目录名）
  └── java-spring.md  ──▶  ②
```

与 skills 的 `CodeRepo(实体) → .agents/skills → .claude/skills` **完全同构**，统一心智。命名 `context`（非 `rules`）体现"具有强烈个人属性的全局上下文"，跨工具共享、复用、按需注入。

## 4. 首个域文件：`java-spring.md`

域名对齐 `sessionstart-domain.py` 的域 key（`java/spring`）。当前装 Maven 规则；未来同域全局规则（编码/构建约定等）往这一个文件加（"每工作域一个 `<域>.md`"）。

```markdown
---
paths:
  - "**/pom.xml"
  - "**/*.java"
  - "**/mvnw"
---

# Java / Maven 本地配置（个人全局上下文）

本地 Maven 仓库**不在**默认 `~/.m2`，**绝不能用 `~/.m2`** 查找或解压依赖 jar。

- 本地 Maven 仓库：`/Users/dalwin/Library/Repository`
- settings.xml：`/Users/dalwin/Library/ConfigFile/maven/saas/settings.xml`

**执行任何 `mvn` 命令时必须附加：**
\`\`\`
mvn -s /Users/dalwin/Library/ConfigFile/maven/saas/settings.xml -Dmaven.repo.local=/Users/dalwin/Library/Repository <goal>
\`\`\`

**查找 / 解压 Maven 依赖 jar 时：**
- 查找：`find /Users/dalwin/Library/Repository -name "*.jar" ...`，不要 `find ~/.m2 ...`
- 解压：`jar tf|xf /Users/dalwin/Library/Repository/...`，不要 `~/.m2/...`
```

> `paths` 用 `**/` 前缀，匹配任意深度的 java 信号文件，兼容相对/绝对匹配语义（实现后用 InstructionsLoaded 实测确认）。

## 5. 配套清理（落实"每条规则只持久化一处"）

| 重复源 | 处理 | 时机 |
|---|---|---|
| 全局 `CLAUDE.md` 第 11–25 行 `## Maven 本地配置（全局）` | 删除，迁入 `java-spring.md` | 与建链路同批 |
| 4 份 `maven-config.md`（home + 3 java 项目 memory） | 删除项目级 3 份；home 那份保留或删（评估） | 机制验证生效**后** |

## 6. 边界与 fallback（仅建议层，已选）

| 边界 | 说明 | fallback |
|---|---|---|
| 冷启动缺口 | path-scoped 是"读到匹配文件才注入"；会话初未读 java 文件时不注入 | 真实 java 任务几乎必先读 pom.xml/源码（截图1 正是已在反编译 class），触发足够及时 |
| 多级 symlink 加载 | 两跳 symlink 能否被 rules 正常解析 | 实测；若不行改各视图单跳直指实体 |
| paths 匹配语义 | 用户级 rule 的 paths 相对项目根 vs 绝对路径 | InstructionsLoaded 实测；`**/` 前缀两者都兼容 |
| 不保证 100% | 仅建议层 | 若抽出后仍偶发失效，再上 `PreToolUse` 硬钩子（改写/拦截含 `~/.m2` 的 mvn/jar/find） |

## 7. Codex 接口说明（本次不实现）

实体 SOT（`dalwin-workflow/context/`）与共享入口（`~/.agents/context/`）均**工具中性**。Codex 后续可从 `~/.agents/context/` 做 symlink 或在 `~/.codex/AGENTS.md` 用 `@import` 接同一份源。本次只留此接口，由用户后续以 Codex 原语实现。

## 8. 实施步骤

1. 建 `dalwin-workflow/context/` + 写 `java-spring.md`（实体，§4 内容）。
2. 建 `~/.agents/context/` + symlink `java-spring.md` → 实体。
3. 建 `~/.claude/rules/` + symlink `java-spring.md` → `~/.agents/context/java-spring.md`。
4. 全局 `CLAUDE.md` 删除 `## Maven 本地配置（全局）` 节。
5. **验证**：临时挂 InstructionsLoaded hook 记录加载；新会话进 java 项目读 `pom.xml`，确认 `java-spring` rule 注入；进 dalwin-workflow（非 java）确认不注入。
6. 验证通过后清理重复 `maven-config.md`（§5）。
7. 两张截图文件名加 `-已修复待验证` 标识。
8. spec + 实施记录 commit 到 dalwin-workflow。

## 9. 验证标准

- `/memory` 在 java 项目会话中列出 `~/.claude/rules/java-spring.md`（经 symlink）。
- InstructionsLoaded 日志显示读 `pom.xml`/`.java` 时加载 `java-spring`，非 java 项目不加载。
- 全局 `CLAUDE.md` 不再含 Maven 段，行数下降。
- 重复 `maven-config.md` 清理后，java 项目仍能拿到 Maven 规则。

## 10. 交付物

1. `dalwin-workflow/context/java-spring.md` + 两层 symlink 视图。
2. 全局 `CLAUDE.md` 瘦身。
3. 验证记录（InstructionsLoaded / `/memory` 截图或日志）。
4. 重复 memory 清理。
5. 两张截图改名。
6. 本 spec + 实施日志 commit。

## 11. 复审条件

- Claude Code 改变用户级 rules 的加载/匹配语义。
- path-scoped rules 触发时机变化（如支持 SessionStart 即时注入）。
- 新增第二个域上下文（届时验证多域 path glob 不互相误触）。
