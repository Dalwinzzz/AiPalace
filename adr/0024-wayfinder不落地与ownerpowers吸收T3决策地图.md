# ADR-0024：wayfinder 不接入公司 tracker，其设计吸收进 ownerpowers T3

- 状态：已接受
- 日期：2026-08-04
- 决策人：dalwin
- 关联：承接 [ADR-0023](0023-mattpocock族skill同步与wayfinder引入.md)（引入 wayfinder 时记的"待观察：tracker 是否具备"）；在 [ADR-0019](0019-mine-skill轻量化第一轮.md) 的轻量化基线上做加法

## 背景

ADR-0023 引入 `wayfinder` 时留了一条待观察：它要真正发挥作用，依赖仓库有支持**子工单 + 原生 blocking 关系**的 issue tracker，而主力业务仓是否具备未验证。

公司远端为 GitLab Enterprise Edition v16.11.10-ee。

## 决策

### 1. 不把 wayfinder 接到公司 GitLab

三条理由，按分量：

**组织层（决定性）**：公司 GitLab 是共享 tracker。一张 `wayfinder:map` 加数十个 AI 生成的决策工单对同事全部可见，混入项目正常 issue 流；建起来容易，撤下来麻烦。个人 harness 的规划产物不应成为公司资产。

**授权层**：`-ee` 是发行版后缀，不代表授权等级。wayfinder 视为 essential 的 `blocks` / `is blocked by` 关系是 **Premium/Ultimate 专属**，Free 只有 `relates to`；子工单方面 Task 作 issue 子项 Free 可用，Epic 需 Premium。若公司为 Free 授权，前沿可视化直接不存在，wayfinder 退化为一堆平铺 issue。

**形态层**：日常公司工作以 T0/T1 直做与排查为主，wayfinder 的"planning 不 doing、一次会话一单"用在这些上是拖累；真正够大的需求已有 `spec-architect` + 仓内 `docs/` 承载。

`wayfinder` 保持 `tier: extra` 在库，供个人项目（有远端 tracker 的个人仓）按需使用，不在公司项目启用。

### 2. ownerpowers 新增 T3 决策地图档

wayfinder 的价值与 tracker 无关——tracker 只是持久化载体。ownerpowers 作为单任务引擎，T2 隐含假设"一次 grilling + 一份 spec + 一轮实现"装得下；**装不下时没有任何机制**：状态存哪、下次从哪续、还有哪些决策未定，全靠人脑记。这是真实缺口，与 ADR-0022 归档时丢弃的那批"实现进度 / TODO"同源。

新增 **T3 决策地图**，剧本 `workflows/decision-map.md`。升档判据要求**两条同时成立**：一次会话装不下（≥3 次会话）**且**有多个相互依赖的未定决策。只满足前者是"活多"，走 T2 分多次执行。

吸收的设计：

- **决策条目 ≠ 实现切片**；T3 只定不做，"想直接动手"识别为已到地图边界该降档的信号
- **迷雾区**，判据是"现在能不能把问题**说精确**"而非"能不能答"——与 [P9 显式过渡态](../PHILOSOPHY.md#p9--显式过渡态)同源
- **范围外单列且永不毕业**，与"已定决策"分开：后者记走过的路，划边界不是路上的一步
- **地图是索引不是仓库**：决策正文只活在自己的文件里，`MAP.md` 只留一行摘要 + 链接。这条是 T3 省上下文的全部来源——每次会话只加载「地图 + 一个决策文件」
- **一次会话只解一个条目**
- **条目四型**（grilling / research / prototype / task），标注 HITL 与否

未吸收：以名字而非编号称呼工单、assignee 作并发 claim——单人无并发，不适用。

落盘 `docs/decision-map/<需求名>/`，**默认不 `git add`**，同 spec 落盘规则。

### 3. 新增外派禁区（全档通用）

`policies.md` 原本只写了三种**该**派 subagent 的场景，没有一条写**什么绝不能派**。ownerpowers 的全部纪律建立在决策点①②"摊开等拍板"上，而"派个 subagent 把方案定了"能无声绕过它。

补 🚧 外派禁区：subagent 只查事实、跑执行、收证据，**不替用户拍板**。决策点①②要摊的内容、`grilling` 的每一问、T3 的 HITL 条目、触发不可逆护栏的动作，一律回主线由用户本人回答。判据："subagent 带回来的应该是'我查到什么'，不是'我决定了什么'。"

这条与 T3 无关，独立生效——是本轮价值最高、成本最低的一处。

## 后果

**正面**：ownerpowers 补上跨会话大需求的档位；外派禁区堵上一个能绕过全部决策点门控的漏洞。

**预算**：`ownerpowers` 391 → 529 行。但 `SKILL.md` 仅 65 → 69 行（+4），增量集中在按需读取的 `decision-map.md`（118 行，只在判为 T3 时加载）。ADR-0019 轻量化的成果不受影响——那一轮砍的正是"无论用不用都常驻"的部分。

**取舍 / 待观察**：

- T3 是四档里唯一**尚未实跑验证**的档位。升档判据（两条同时成立）刻意收紧，宁可漏判走 T2 也不误判空转。跑过一次真实需求后再校准。
- 决策地图落在仓内 `docs/decision-map/` 且默认不追踪，会在 `git status` 里表现为未跟踪文件。若确认长期使用，可考虑比照 `spec-architect` 在全局 gitignore 加一条——**属用户个人 git 配置，不由本仓代改**。
- `wayfinder` 与 T3 现在是同一套思想的两个实现（tracker 版 / 文件版）。若日后个人项目实跑 wayfinder 后发现某些设计 T3 没吸收到，回补到 `decision-map.md`，不反向去改 community 真身。
