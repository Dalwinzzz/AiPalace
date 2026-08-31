# context/rules/ — 硬配置域规约

## 是什么

**rules** 是 path-scoped 的硬配置域规约：只要匹配到 `paths:` frontmatter 所指定的文件路径，agent harness 就**必须**自动注入对应规约，无需人工选择、不得跳过。

这与其他内容资产的性质截然不同（记忆层已于 ADR-0013 迁入 `vault/memory/`）：

| 类型 | 位置 | 触发方式 | 强制性 |
|------|------|----------|--------|
| **rules** | `context/rules/` | path-scoped 自动注入 | **必注** |
| **操作规则** | `vault/memory/00-RULES/operating-rules.md` | SessionStart hook 直注 | **必注**（always-on） |
| **自我画像** | `vault/memory/00-RULES/`（其余） | INDEX 决策树命中 | 按需 |
| **项目/技术知识** | `vault/memory/01-PROJECTS/` | INDEX 决策树命中 | 按需 |
| **how-to 细则** | `context/howto/` | 被 operating-rules 指针引用，用时再读 | 懒加载 |

> **边界**：rules 只放「命中路径就必须遵守的硬约束」（构建命令、版本约束、编码禁忌）。
> 方法论、背景知识、按需参考的细则**不进 rules**——分别归 skill、`vault/memory/`、`context/howto/`。

## 当前 rules 一览

| 文件 | 说明 | 触发 paths |
|------|------|------------|
| `java-spring.md` | Java / Maven 本地配置（仓库路径、settings.xml、JDK 版本约束）+ 写 SQL 前的指针 | `**/pom.xml`、`**/*.java`、`**/mvnw` |
| `frontend-web.md` | Web 前端美学基因（设计系统流程、UI 规范） | `**/*.tsx`、`**/*.jsx`、`**/*.vue`、`**/*.svelte`、`**/*.astro`、`**/tailwind.config.*` |

> `frontend-web.md` 的 paths 已于 2026-07-31 收窄：移出 `*.css`/`*.scss`/`*.sass`/`*.less`/`*.html`
> ——改一行样式细节不需要注入整套美学方法论，只在动组件/页面/tailwind 配置时才触发。

## 出站指针（本层唯一允许的外链形式）

rules 正文保持"硬约束"本色，需要展开的细则一律用**单行指针**引出，不复制内容：

| 位于 | 指向 | 何时读 |
|------|------|--------|
| `java-spring.md` 文末 | `vault/memory/01-PROJECTS/tech/sql-performance.md` | 要写/改 mapper XML 或业务查询 SQL 时 |

## 规范参考

完整内容资产治理规范见：[docs/governance/content-assets/rules.md](../../docs/governance/content-assets/rules.md)
