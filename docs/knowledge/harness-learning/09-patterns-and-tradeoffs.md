# 09. 设计模式与权衡 — Harness 工程的哲学

> **一句话**:前面八章是"组件",这一章是"原则"。读完这章,你应该能对任何一个 Agent Harness 做出"它是一个好设计还是坏设计"的判断。

---

## 这一章的读法

前面八章每一章讲一个组件(Agent Loop、Tools、Memory、Sandbox、Sub-agents、Middleware、Skills),每一章都有"DeerFlow 是怎么做的"。

这一章不一样。它**站在更高的视角**,把所有组件串起来,提炼出**反复出现的设计模式和权衡**。理解这些模式,你以后看到任何一个 Agent 框架(不管是不是 DeerFlow),都能迅速建立心智模型。

这一章里的每一条原则,都能从前面章节找到对应的实现例子。读的时候建议**双开**:左边放本章,右边放对应的实现章节对照。

---

## 原则一:分层边界 —— 单向依赖

### 是什么

DeerFlow 的代码被严格分成两层:

- **Harness 层**(`backend/packages/harness/deerflow/`)—— 通用的 Agent 运行时基础设施
- **App 层**(`backend/app/`)—— 基于 Harness 构建的具体应用(Web 服务、IM 集成)

**单向依赖的硬性规则**:`app` 可以 import `deerflow.*`,但 `deerflow.*` 永远不能 import `app.*`。

这条规则甚至有专门的测试(`test_harness_boundary.py`)来保证它不被违反。

### 为什么

单向依赖是"分层架构"的核心。违反它的代价:

- **循环依赖**:A 依赖 B,B 依赖 A,两边改一点就互相炸
- **不可复用**:Harness 里混入 Web 概念(session、cookie、HTTP 状态码),就没法在 CLI 或 Slack Bot 里用了
- **不可测试**:想单测 Harness 里的一个函数,得先启动整个 Web 服务
- **认知负担**:读 Harness 代码时不知道什么时候会突然跳到 Gateway 层

反过来,**遵守单向依赖**让 Harness 层可以独立发布、独立测试、独立演进。

### 怎么判断一个 Harness 有没有守住这条线

看三个迹象:

1. **Harness 层的代码里是否出现 HTTP 框架相关的 import**(FastAPI、Flask、Django)?有 → 污染了
2. **Harness 层的代码里是否依赖特定的数据库**(Redis、PostgreSQL 的具体客户端)?应该用抽象接口,具体实现在 App 层
3. **测试 Harness 层是否需要启动 Web 服务**?需要 → 没守住

### DeerFlow 的对应实现

- `backend/packages/harness/deerflow/` vs `backend/app/` 的目录分离
- `backend/tests/test_harness_boundary.py` — 自动化测试,扫描 import 关系,违反规则就测试失败
- `backend/CLAUDE.md` 明确写了这条规则

---

## 原则二:中间件组合,不是继承

### 是什么

把所有"横切关注点"(日志、错误处理、记忆、护栏、审计)做成独立的中间件,按顺序串成一条链。不要做成基类方法然后让子类覆写。

### 为什么

继承的组合爆炸问题:

假设你有 N 个可选功能(记忆、审计、压缩、...),用继承:
- `BaseAgent`
- `AgentWithMemory extends BaseAgent`
- `AgentWithAudit extends BaseAgent`
- `AgentWithMemoryAndAudit extends ??` ← 多继承 + diamond problem
- `AgentWithMemoryAndAuditButNoCompression extends ???`

用中间件组合:

```python
middlewares = [MemoryMiddleware(), AuditMiddleware(), ...]
# 要哪个加哪个,顺序可配,互不影响
```

中间件模式的本质是**把"决定功能组合"这件事从编译期推迟到运行期**。运行期可以根据配置、用户请求、环境变量动态组装,灵活性极大。

### 代价

- **顺序依赖隐式**:中间件的顺序是有语义的,但这层语义没有编译器检查。错了只能在运行时或代码审查时发现。DeerFlow 的解法是在 `agent.py` 里写大量注释解释顺序依赖,并用测试覆盖关键顺序。
- **Debug 链路长**:bug 可能跨越多个中间件,需要追踪请求经过了哪些中间件的哪些钩子。

### DeerFlow 的对应实现

- `backend/packages/harness/deerflow/agents/middlewares/` — 15 个独立中间件
- `backend/packages/harness/deerflow/agents/lead_agent/agent.py` 第 198-270 行 — `_build_middlewares()` 是中间件组合逻辑,注释解释了顺序
- [07-middleware](./07-middleware.md) 全章专门讲这个

---

## 原则三:Provider 抽象 —— 一个接口,多个实现

### 是什么

对一类"可替换的基础设施"定义抽象接口,提供多个具体实现,通过配置选择。典型场景:

- **Sandbox Provider**:Local / Docker / K8s / AIO Sandbox
- **Model Provider**:OpenAI / Anthropic / vLLM / Claude Code OAuth / Codex CLI
- **Memory Storage**:JSON 文件 / 数据库 / 向量库
- **Checkpointer**:内存 / SQLite / Postgres
- **MCP Client**:stdio / SSE 传输

### 为什么

基础设施会演化。今天用 Local Sandbox,明天上生产要切 K8s,后天某个新的超快沙箱技术出来想换过去。如果 Agent 代码直接调用了具体实现,切换就得改一大堆代码。

抽象接口让切换**只改一行配置**。

同时,多个 Provider 并存让**不同场景用不同实现**成为可能:开发用 Local,生产用 K8s,测试用 Mock,全都共存。

### 什么时候抽象是过度设计

不是所有东西都该做抽象。判断标准:

- ✅ **存在多个合理实现** → 做抽象(沙箱显然有多种实现)
- ✅ **未来会变** → 做抽象(模型 Provider 市场还在动)
- ❌ **只会有一种实现** → 不做抽象(比如"当前时间"这种东西)
- ❌ **抽象接口本身会因实现变化** → 抽象早了(过早抽象)

DeerFlow 的抽象都是在**已有多种实现**之后才提炼出来的,不是提前设计的。这是一种健康的节奏。

### DeerFlow 的对应实现

- `backend/packages/harness/deerflow/sandbox/sandbox_provider.py` — Sandbox Provider 接口
- `backend/packages/harness/deerflow/sandbox/local/` — 一个具体实现
- `backend/packages/harness/deerflow/models/` — 模型抽象,支持多种 Provider
- `backend/packages/harness/deerflow/reflection/` — 反射工具,用来"按字符串加载类",配合配置文件动态实例化 Provider(`resolve_variable`、`resolve_class`)

---

## 原则四:配置驱动装配

### 是什么

不把"Agent 长什么样"硬编码在 Python 代码里,而是放在 YAML / JSON 配置文件里。Harness 启动时读配置、装配组件。

### 为什么

Agent 的行为受**太多参数**影响:

- 用哪个模型?
- 用不用沙箱?哪个沙箱?
- 启用哪些中间件?
- 开不开子代理?并发上限几个?
- 开不开延迟工具加载?
- Summarization 什么时候触发?保留多少?
- 记忆是否启用?存哪里?
- Guardrail 用哪个 Provider?fail closed 还是 fail open?
- ……

如果全在代码里,每改一项都要改代码、重启服务、可能引入 bug。放在配置里,**改配置比改代码安全 10 倍**。

### 代价

- **配置膨胀**:DeerFlow 的 `config/` 目录有 20+ 个配置模块(`app_config`、`model_config`、`sandbox_config`、`memory_config`、...)。新人看会觉得复杂。
- **配置正确性难保证**:YAML 没有静态类型,写错字段要到运行时才发现。DeerFlow 的解法是用 Pydantic 做配置的 schema 验证。

### DeerFlow 的对应实现

- `backend/packages/harness/deerflow/config/` — 所有运行时配置模块(见文件清单,20+ 个)
- `config.yaml`(项目根)— 主配置文件
- `extensions_config.json` — MCP 和 Skills 的外部配置
- 运行时 `RunnableConfig` 带 `configurable` 字段,支持"每次请求级别"的动态配置(覆盖默认值)

---

## 原则五:Per-Thread 隔离

### 是什么

每一次对话(thread)都拥有**独立的资源空间**:

- 独立的工作目录(`.deer-flow/threads/{thread_id}/`)
- 独立的沙箱实例
- 独立的 ThreadState
- 独立的上传文件
- 独立的 token 计数
- 独立的审计日志

### 为什么

没有隔离会出一连串问题:

- **安全**:A 用户的 Agent 能看到 B 用户的文件
- **正确性**:两个对话的工具调用互相干扰
- **可恢复性**:一个会话崩了影响其他会话
- **可审计**:出问题不知道是谁干的

Per-thread 隔离是多租户 Agent 系统的最低门槛。哪怕你只有一个用户,多开两个 tab 同时跟 Agent 聊天,也需要隔离。

### 代价

- **资源开销**:每个 thread 都要分配独立资源,数量一多会占用大量磁盘 / 内存
- **清理逻辑**:什么时候销毁一个 thread?超时?用户主动清?LRU?需要明确策略
- **状态持久化**:独立状态必须持久化到某种存储,才能跨进程重启恢复

### DeerFlow 的对应实现

- `backend/packages/harness/deerflow/agents/middlewares/thread_data_middleware.py` — 为每个 thread 创建隔离目录
- `backend/packages/harness/deerflow/sandbox/middleware.py` — 为每个 thread 获取独立沙箱
- `backend/packages/harness/deerflow/agents/checkpointer/` — 每个 thread 有独立 checkpoint
- `backend/packages/harness/deerflow/agents/thread_state.py` — `ThreadState` 是 per-thread 的状态容器

---

## 原则六:懒初始化(Lazy Initialization)

### 是什么

**创建 Agent 对象时,不立刻初始化它依赖的所有资源**(沙箱、MCP 连接、模型实例等)。等这些资源真正被用到时才初始化。

### 为什么

Agent 的"创建"应该是几乎零成本的。因为:

- **高并发**:用户同时开一百个 thread,每个都要立刻创建一个 Agent。如果创建很慢,用户会卡住。
- **按需分配**:一个请求可能根本不用到沙箱,那就别启动沙箱
- **错误定位**:初始化失败发生在运行时而不是"对象构造时",异常堆栈更接近"出问题的那个请求"

### 代价

- **首次调用延迟**:第一次真正用到某资源时会有初始化延迟
- **错误延迟暴露**:配置错了可能要到运行时才发现
- **并发初始化**:如果多个请求同时触发初始化,要保证线程安全(DeerFlow 用锁解决)

### DeerFlow 的对应实现

- `backend/packages/harness/deerflow/agents/middlewares/tool_error_handling_middleware.py` 里 `build_lead_runtime_middlewares(lazy_init=True)` — `lazy_init=True` 是默认值
- `SandboxMiddleware(lazy_init=lazy_init)` — 沙箱中间件默认懒初始化
- MCP 工具列表的缓存(`mcp/cache.py`)也是一种懒 + 记忆化

---

## 原则七:可见优先 vs 后台优先

### 是什么

**和用户可见性相关的动作 > 后台动作**。具体到中间件顺序:

- TitleMiddleware(首轮生成标题,前端立即要显示)→ **优先**
- MemoryMiddleware(抽取长期记忆,异步处理即可)→ **次优**

在 `agent.py` 的注释里:

```
# TitleMiddleware generates title after first exchange
# MemoryMiddleware queues conversation for memory update (after TitleMiddleware)
```

### 为什么

**用户感知延迟**是 Agent 体验的核心。如果后台动作抢了前台动作的模型调用,用户会明显感到卡顿。

排序原则:**面向用户的动作必须先完成,面向后台的动作往后放**。

### 怎么应用

一个你在设计 Agent 系统时随时该问的问题:**"这个动作用户能不能看到?如果看不到,它就该能等。"**

能等的动作,就放到后面;不能等的动作,放前面。

### DeerFlow 的对应实现

- Title 在 Memory 之前 — `agent.py` 的中间件装配顺序
- Memory 的"抽取"是完全异步的(`memory/queue.py` + `memory/updater.py`),不阻塞用户请求
- Summarization 早于 Memory — 压缩能立刻让上下文变小,益处前置;记忆抽取后置

---

## 原则八:组合式 Agent(Super Agent)

### 是什么

让一个 Agent 能**把另一个 Agent 当工具调用**。主 Agent 的工具清单里有一个特殊工具 `task(description, ...)`,调用它会启动一个子代理,子代理独立执行后把结果返回。

### 为什么

单 Agent 的上下文窗口有上限。遇到复杂任务(读十篇论文、研究一个话题)时,单 Agent 会被"脏工作"污染。

把脏工作甩给子代理:

- 主 Agent 上下文干净
- 子代理可并行
- 主 Agent 角色变成"规划 + 整合",职责清晰

### 代价

- **并发控制**:必须限制并发数,否则 API 速率被打爆
- **递归深度**:必须防止无限递归
- **资源共享**:子代理共享主 Agent 的沙箱?文件锁要做好

### DeerFlow 的对应实现

- `backend/packages/harness/deerflow/subagents/` — 子代理执行器 / 注册表 / 内置
- `backend/packages/harness/deerflow/tools/builtins/task_tool.py` — `task` 工具(主 Agent 调用的入口)
- `backend/packages/harness/deerflow/agents/middlewares/subagent_limit_middleware.py` — 并发上限(默认 3)
- 子代理的中间件链是主 Agent 的子集(见 [06-subagents](./06-subagents.md))

---

## 原则九:渐进披露

### 是什么

不要一开始就把所有信息暴露给模型。让模型**先看到一个简洁的索引**,需要细节时**再通过工具调用加载**。

典型场景:

- **工具很多时**:Deferred Tools(延迟工具加载)— 只给模型看 `tool_search`,匹配到才加载具体工具
- **技能很多时**:只给模型看技能元数据列表,需要时才加载 `SKILL.md` 内容
- **文件很多时**:只给模型看"工作目录里有这些文件",需要时调 `read_file` 看具体内容
- **记忆很多时**:只注入"相关的"事实,不是全部

### 为什么

**Lost in the Middle**。模型对长 prompt 中间的内容关注度低。短 prompt 反而效果更好。

另外,**成本和延迟**。每一个 token 都是钱和时间。渐进披露让"花多少"和"用多少"成正比。

### 代价

- **多一次工具调用**:每次加载要走一个额外的工具调用回合,增加一次 LLM 调用的延迟和成本
- **模型判断负担**:模型需要先判断"我需要什么",这本身是需要上下文的能力

当内容数量很小(5 个工具以内)时,渐进披露反而是过度设计。它只在规模上去之后才值得。

### DeerFlow 的对应实现

- `backend/packages/harness/deerflow/tools/builtins/tool_search.py` — Deferred Tools 的元工具
- `backend/packages/harness/deerflow/agents/middlewares/deferred_tool_filter_middleware.py` — 从 schema 清单里隐藏延迟工具
- `backend/packages/harness/deerflow/skills/` — Skills 的"元数据列表 + 按需加载"两阶段
- `backend/packages/harness/deerflow/config/tool_search_config.py` — 配置开关(默认是否启用)

---

## 原则十:数据驱动扩展

### 是什么

新能力应该能**通过"加数据"**(加配置、加 MCP Server、加 `SKILL.md`)扩展,而不是"改代码"。

### 为什么

Agent 的能力需求是**长尾的**。每一个用户都有一点自己的特殊需求("按我公司模板写邮件"、"查询我们内部的那个系统"、"用我们团队的编码规范")。如果每一项都要改 Harness 源码,维护者会被淹没。

数据驱动让扩展**去中心化** —— 用户可以自己加,不打扰 Harness 维护者。

### 代价

- **安全问题**:用户加的数据可能是恶意的(恶意 Skill、恶意 MCP Server)。需要安全扫描 + 沙箱 + 审计
- **调试困难**:bug 可能在用户的配置里,而不是 Harness 代码里,排查要多一层

### DeerFlow 的对应实现

- `extensions_config.json` — MCP 服务器配置,加一个服务器不用改代码
- `skills/custom/` — 用户自定义 Skill 的目录
- `backend/packages/harness/deerflow/config/agents_config.py` — 自定义 Agent 配置(可以给每个 Agent 配不同的 model / tools / skills)
- `backend/packages/harness/deerflow/skills/security_scanner.py` — Skill 安全扫描器
- `backend/packages/harness/deerflow/guardrails/` — 可配置的护栏策略

---

## 十条原则的总表

| # | 原则 | 核心动作 | DeerFlow 体现 |
| --- | --- | --- | --- |
| 1 | **分层边界** | 单向依赖 | `deerflow.*` 不 import `app.*` |
| 2 | **中间件组合** | 拆散横切关注点 | 15 个中间件独立装配 |
| 3 | **Provider 抽象** | 接口 + 多实现 | Sandbox / Model / Memory Provider |
| 4 | **配置驱动** | YAML 而非 Python | `config/` 的 20+ 模块 |
| 5 | **Per-Thread 隔离** | 每会话独立资源 | 独立目录 / 沙箱 / 状态 |
| 6 | **懒初始化** | 按需分配 | `lazy_init=True` 默认 |
| 7 | **可见优先** | 前台动作先完成 | Title 在 Memory 之前 |
| 8 | **组合式 Agent** | Agent 能调 Agent | `task` 工具 + 子代理系统 |
| 9 | **渐进披露** | 按需加载细节 | Deferred Tools + Skills |
| 10 | **数据驱动扩展** | 加数据而非改代码 | MCP / Skills / Guardrails |

---

## 如何"用"这些原则

学完这十条原则,你可以拿它们来做三件事:

### 1. 评估别的 Agent 框架

下次你遇到一个新的 Agent 框架(LangChain、AutoGen、CrewAI、MetaGPT 等),用这十条原则做检查:

- 它的分层是否干净?
- 中间件是显式的还是隐式的?
- Provider 抽象有几层?
- 能不能用配置驱动扩展?
- Per-thread 隔离做得怎么样?
- ……

你会发现,成熟的框架大多数原则都在某种程度上实现了,不成熟的框架在几个地方存在明显短板。

### 2. 设计自己的 Agent 系统

如果你要自己写一个 Agent 系统,这十条原则就是你的"设计检查清单":

- 先画分层图(原则 1)
- 列出所有横切关注点,决定哪些做成中间件(原则 2)
- 找出所有可能有多实现的地方,抽象接口(原则 3)
- 把参数收敛到配置(原则 4)
- 设计隔离边界(原则 5)
- 确定启动开销(原则 6)
- 排出动作优先级(原则 7)
- 评估是否需要多 Agent 组合(原则 8)
- 评估扩展点的数量和类型(原则 9、10)

### 3. 读懂任何开源 Agent 框架

接下来你可以打开任何一个 Agent 框架的代码,按这个套路阅读:

1. 找**分层边界**:哪几个顶层目录?它们之间的依赖关系?
2. 找**中间件 / 拦截器**:循环的前后插入点在哪?
3. 找**Provider**:哪些概念有多种实现?
4. 找**配置入口**:运行时参数从哪里读?
5. 找**隔离单元**:每个会话 / 请求的状态容器是什么?

这五个问题能让你在半小时内从完全不懂到能画出架构草图。

---

## 最后的话

Agent Harness 这个领域还非常年轻 —— 2024 年底 MCP 才出现,2025 年 "agent harness" 这个词才开始流行,2026 年我们才看到 DeerFlow 这样把所有概念系统化的开源项目。

这意味着**现在入场正是时候**。这十条原则是目前社区共识的快照,但它们一定会演进。未来五年里:

- 会有新的"跨切关注点"被识别出来(今天我们谈 token,未来可能谈 attention cost)
- 会有新的 Provider 抽象涌现(比如"推理轨迹 Provider" — 把思考过程外化成可替换的模块)
- 会有新的组合方式(也许是 Agent 之间的事件总线,而不仅仅是 `task()` 调用)
- 会有新的安全模型(Prompt injection 的防御会变成一门独立学科)

但这些演进都**不会推翻前面的原则**,只会在它们之上叠加新的层次。分层、组合、抽象、配置 —— 这些是软件工程沉淀了几十年的通用道理,Agent 只是把它们应用到了新的领域。

读完这十章,你已经不再是 Agent 的"新手"。你可以打开 DeerFlow 的源码,从 `agent.py` 的 `make_lead_agent()` 入口开始,一路往下读,任何一个文件你都能说出**它解决了哪个原则下的哪个问题**。

祝你从这个"观念起点"出发,去写出属于自己的 Harness 🦌

---

## 延伸阅读

- 回到索引:[README](./README.md) — 使用概念速查表按需复习
- 外部:Anthropic 的 "Constitutional AI" 和 "Agentic Safety" 系列博客 —— 护栏层的深入讨论
- 外部:LangGraph 官方文档 —— 学习 DeerFlow 依赖的核心框架
- 外部:[MCP 官方文档](https://modelcontextprotocol.io/) —— 工具标准化协议的未来
- 外部:Claude Code 的架构文档 —— 另一个成熟 Harness 的参考
