# ADR-0023：mattpocock 族 skill 同步、归桶与 wayfinder 引入

- 状态：已接受
- 日期：2026-08-03
- 决策人：dalwin
- 关联：延续 [ADR-0019](0019-mine-skill轻量化第一轮.md) 的 skill 轮次迭代；受 [P3](../PHILOSOPHY.md#p3--来源优先归属分层) / [P4](../PHILOSOPHY.md#p4--分级控预算tier) 约束

## 背景

`grilling` 系列引自 `mattpocock/skills`，上次同步在 2026-07-24。本轮对齐上游 `2ab9580` 发现三件事：

1. **`grilling` 已过期**。上游改写了核心段——把"能查的事实自己查"与"决策必须逐条问人"分开，并加了"未确认前不得动手"。本地还缺 `agents/openai.yaml`。
2. **`grill-with-docs` 依赖断裂**。它已瘦成两行委派（`/grilling` + `/domain-modeling`），而 `domain-modeling` 本地从未安装；同时本地仍留着上游已迁走的 `ADR-FORMAT.md` / `CONTEXT-FORMAT.md`（现归 `domain-modeling`）。
3. **上游新增 `wayfinder`**，本地未装。

`grilling`、`grill-me`、`grill-with-docs` 三个同源 skill 平铺在 `skills/community/github-skills/` 顶层，而同目录下其他上游都已按来源分桶（`anthropic-official/` `third-party/` `misc/`），溯源分层被弱化。

## 决策

### 1. 新建 `mattpocock/` 子桶，8 个同源 skill 全部归入

`skills/community/github-skills/mattpocock/`，桶级一份 `_SOURCE.md` 取代原来三份 skill 级副本。registry key 由 `github-skills/<skill>` 改为 `mattpocock/<skill>`；**挂载点目录名取 key 的 basename，故派生软链名不变**，双工具侧零破坏。

`_SOURCE.md` 记录上游同步基线 commit 与**族内依赖图**——这一族互相委派，单独更新任一个都会断链，必须整族同步。

### 2. 装齐 wayfinder 依赖链，5 个新 skill 全部 `tier: extra`

`wayfinder` 依赖 `/grilling`、`/domain-modeling`、`/research`、`/prototype`，另需 `/setup-matt-pocock-skills` 给仓库配 issue tracker（未配则退化到本地 markdown tracker）。只装 `wayfinder` 等于装一个跑不起来的入口，故整链装齐。

全局挂载 14 → 19。**代价是 always-on skill 描述预算增加 5 条**，与本轮先前的预算收缩方向相反，属有意接受：这 5 个里 `wayfinder` / `grill-me` / `grill-with-docs` / `setup-matt-pocock-skills` 都带 `disable-model-invocation: true`，只进斜杠菜单、不参与模型自动触发。

### 3. 同步即整族对齐上游，不做本地改写

8 个 skill 与上游逐字一致（含 `agents/openai.yaml`）。本地不改写的理由：这一族靠彼此的 `/skill-name` 委派协作，任何本地分叉都会在下次同步时产生难以判读的三方冲突。要定制则新建 mine skill 包一层，不改 community 真身。

## 后果

**正面**：`grill-with-docs` 从断链状态恢复可用；`grilling` 拿到"事实自查 / 决策必问 / 未确认不动手"这三条实质改进；`wayfinder` 补上一个此前没有的能力档位——超出单次 session 容量的大工作，用 issue tracker 上的决策工单地图承载，一次只解一单。溯源分层与同目录其他上游拉齐，`_SOURCE.md` 从三份重复收敛为一份带依赖图的桶级文档。

**验收**：`skillctl doctor` 36 skill 全绿无漂移；双工具挂载点无悬挂软链；`skill-security-audit` 扫 26 个文件 CLEAN。

**取舍 / 待观察**：

- `wayfinder` 与既有的 `spec-architect`（ADR-0019 刚精简）、`superpowers/writing-plans` 在"把大工作拆开"这件事上有重叠，但切法不同：wayfinder 产出的是**决策**工单、且强制"planning 不 doing"，spec-architect 产出的是可执行 spec。三者是否需要收敛，等 wayfinder 实跑过再判，现在不预先裁剪。
- `wayfinder` 要真正发挥作用依赖仓库有 issue tracker 且支持子 issue + 原生 blocking 关系。主力业务仓是否具备尚未验证；不具备时它退化为本地 markdown tracker，价值打折。
- 上游这一族仍在快速迭代（`in-progress/` 下有 `batch-grill-me` 等未定型件）。同步节奏定为**按需拉取、整族对齐**，不追 in-progress。
