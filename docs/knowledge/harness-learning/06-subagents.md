# 06. Sub-agents — 让 Agent 调用 Agent

> **一句话**:Sub-agent 是"Agent 的 Agent" —— 主 Agent 把一个子任务甩给另一个 Agent 独立完成,从而突破单 Agent 的上下文限制,并行处理复杂问题。

---

## 核心问题

假设你给 Agent 一个任务:**"研究一下最近三个月国内 AI 大模型赛道的融资情况,写一份三千字的分析报告。"**

一个单 Agent 会这样做:

1. 搜索"最近三个月 AI 大模型融资"(调用搜索工具)
2. 得到几十条结果
3. 一个一个打开读(每次调用 fetch 工具)
4. 把信息累积在上下文里
5. 基于累积的信息写报告

问题来了:

- **第 3 步会把上下文撑爆**。读十个网页,每个几千 token,上下文窗口很快就满了。
- **第 4 步之后,"有用的"信息和"没用的网页内容"混在一起**,模型注意力被稀释。
- **不能并行**。单 Agent 只能一个个读网页,慢。
- **任务结构不清晰**。Agent 自己在"搜索 / 筛选 / 阅读 / 总结 / 写作"之间来回切换,容易丢上下文。

Sub-agent 机制的提出就是为了解决这些:

> **把"读十个网页"这种子任务丢给一个独立的 Agent 去做,让它独占一个上下文,返回一个精简的总结。主 Agent 只看到总结,不看原始网页。**

这样:

- ✅ 主 Agent 的上下文很干净
- ✅ 十个子代理可以并行读网页
- ✅ 子代理完成后自动销毁,资源自动释放
- ✅ 主 Agent 的角色变清晰:只做"规划 + 整合",不做"脏活"

---

## 通用概念

### "Super Agent":Agent 的 Agent

一个能调用其他 Agent 的 Agent,有时被称为 **"Super Agent"** 或 **"Lead Agent"**。它的区别在于:

- 普通 Agent 的工具是"函数"(`read_file`、`search_web`)
- Super Agent 的工具清单里**包含一个特殊工具**,比如 `task(description, tools, ...)`,这个工具的"实现"是**启动另一个 Agent**

从模型的视角看,`task()` 和 `read_file()` 没有本质区别 —— 它就是调用一个工具,工具返回一段文本。但这段文本是**另一个 Agent 在独立上下文里工作了一段时间后的产出**。

### 和"多步提示链"的区别

有一种看起来相似的技术叫 **多步提示链**(prompt chaining):

```
Step 1: LLM("用户想做什么? 分解任务")
Step 2: LLM("执行任务 1")
Step 3: LLM("执行任务 2")
Step 4: LLM("汇总结果")
```

区别在于**调度权**:

- **提示链**:调度逻辑是**硬编码**的(Python 代码里写死了"先分解、再执行、最后汇总")。模型只负责每一步的生成。
- **Sub-agent**:调度逻辑是**模型决定**的。主 Agent 自己决定"什么时候要开子代理、开几个、每个做什么"。

所以 Sub-agent 的灵活性远大于提示链,但也更难控制 —— 你得处理好并发、超时、资源限制。

### 子代理的三个关键参数

当主 Agent 调用 `task()` 时,它至少要指定:

1. **描述**:你希望子代理做什么?("阅读 https://xxx 这篇文章并总结 AI 融资信息")
2. **可用工具**:给子代理哪些工具?(通常是主 Agent 工具的子集,不会给 `task` 这个工具,避免无限递归)
3. **期望输出**:你希望它返回什么格式?(JSON?纯文本?Markdown?)

子代理拿到这些,独立运行一个完整的 Agent Loop,直到产出最终答案,然后把答案作为"工具结果"返回给主 Agent。

### 并发控制

Sub-agent 系统必须考虑并发,否则会出事:

1. **并发上限**:不能无限开子代理,否则会把 LLM API 打挂(速率限制)或者把钱包烧光
2. **超时**:子代理卡住怎么办?必须有超时机制
3. **取消**:用户取消主任务时,所有子代理也要一起取消
4. **资源隔离**:子代理的沙箱应该是独立的还是共享的?

DeerFlow 的默认是:**最多 3 个并发子代理 + 15 分钟超时 + 共享主 Agent 的沙箱**。

### 递归深度限制

如果子代理也能开子代理,那就是递归。理论上没问题,实际上危险 —— 可能无限套娃。所以一般会限制**最大递归深度**(例如 3 层)。超过深度的子代理调用会被拒绝。

DeerFlow 的设计上,子代理的工具清单里通常不包含 `task` 工具,这就在结构上避免了递归。

---

## DeerFlow 的实现

### `task()` 工具

- `backend/packages/harness/deerflow/tools/builtins/task_tool.py` — **`task` 工具的实现**。这是主 Agent 看到的"启动子代理"的接口。调用它会触发子代理执行器。

### Executor(执行器)

- `backend/packages/harness/deerflow/subagents/executor.py` — **`SubagentExecutor`**。管理后台线程池,负责真正"跑"一个子代理的全流程:
  - 根据请求选一个子代理类型(从 registry)
  - 创建一个独立的 Agent 实例
  - 在后台线程执行
  - 捕获结果 / 超时 / 异常
  - 把结果作为 tool result 返回

### Registry(注册表)

- `backend/packages/harness/deerflow/subagents/registry.py` — **子代理注册表**。维护一个 `{name: agent_factory}` 的映射。主 Agent 通过 `task(type="bash", ...)` 指定类型,Executor 从 registry 里取出对应的工厂函数。
- `backend/packages/harness/deerflow/subagents/config.py` — 子代理配置

### 内置子代理

- `backend/packages/harness/deerflow/subagents/builtins/` — **内置子代理目录**:
  - `general-purpose` 子代理(一个"全能型"子代理,拥有完整工具集)
  - `bash` 子代理(专门执行 shell 命令的子代理)
  - 可能还有其他,以源码为准

这些内置子代理都是用 `make_lead_agent()` 的一个变体创建的,但使用的是**子代理中间件链**(在 `tool_error_handling_middleware.py` 里你能看到 `build_subagent_runtime_middlewares()`)。子代理的中间件链是主 Agent 的**子集** —— 比如没有 `TitleMiddleware`、`ClarificationMiddleware` 这些"面向用户"的中间件。

### 并发限制

- `backend/packages/harness/deerflow/agents/middlewares/subagent_limit_middleware.py` — **`SubagentLimitMiddleware`**。在主 Agent 的中间件链里,**拦截那些超出并发上限的 `task` 调用**,直接把多余的调用转换成错误 ToolMessage,避免真的起太多子代理。

在 `agent.py` 的 `_build_middlewares()` 里:

```python
if subagent_enabled:
    max_concurrent_subagents = config.get("configurable", {}).get("max_concurrent_subagents", 3)
    middlewares.append(SubagentLimitMiddleware(max_concurrent=max_concurrent_subagents))
```

默认并发数是 3,可由运行时配置覆盖。

### 自定义 Agent

- `backend/packages/harness/deerflow/tools/builtins/setup_agent_tool.py` — 支持在 bootstrap 模式下通过工具调用创建自定义 Agent
- `backend/packages/harness/deerflow/config/agents_config.py` — 自定义 Agent 的配置加载(`load_agent_config`)
- 在 `agent.py` 里:`make_lead_agent()` 支持 `agent_name` 参数,可以为每个自定义 Agent 加载独立的 model / tools / skills 配置

这让 DeerFlow 的子代理机制不仅能用于"临时任务委派",还能作为"可发布的 Agent 单元" —— 用户可以定义自己的子代理,给它们专门的 prompt 和工具集。

---

## 设计权衡

### 为什么子代理独立进程(线程)而不是独立 LangGraph 节点?

一个替代方案是把子代理做成主 LangGraph 图里的一个子图节点,共享上下文。DeerFlow 选择"独立执行器 + 独立 Agent 实例"的原因:

1. **真正独立的上下文**:子代理有自己的 messages、自己的状态,主 Agent 看不到它的工作过程
2. **真正的并发**:用线程池可以跑多个子代理,用子图节点做不到这么自然
3. **故障隔离**:一个子代理崩了不影响其他子代理或主 Agent

代价是:每个子代理启动需要一次"加载模型、构建中间件链"的开销。但这对一个几分钟级别的任务来说可以忽略。

### 为什么默认上限是 3 个并发?

3 是一个经验值,兼顾:

- **成本**:并发越高,LLM 调用费用越高
- **速率限制**:API 厂商对并发有上限(通常是 RPM / TPM),跑太多容易被限流
- **协调成本**:并发越多,主 Agent 越难合理分工
- **用户感知**:3 个并发的进度展示还能看懂,20 个就乱了

这个数字在 `SubagentLimitMiddleware` 里可以调,但默认是 3。

### 为什么子代理共享沙箱而不是独立沙箱?

DeerFlow 默认让子代理**共享主 Agent 的沙箱**。好处:

- **文件可见性**:主 Agent 写的文件,子代理能直接读;反之亦然
- **成本低**:不用为每个子代理起新沙箱

代价:
- **并发文件冲突**:需要文件操作锁(见 [05-sandbox](./05-sandbox.md))
- **错误传播**:子代理在沙箱里搞坏的东西,主 Agent 也会看到

对于"任务分解式"的多代理协作,共享沙箱是合理的 —— 毕竟它们在**协作完成同一个任务**,共享工作区是自然的。如果需要强隔离(比如"跑不受信代码"),应该用独立沙箱。

### 子代理的中间件链为什么不同?

在 `tool_error_handling_middleware.py` 里,`build_lead_runtime_middlewares()` 和 `build_subagent_runtime_middlewares()` 是两个不同的函数。区别:

- **主 Agent**:`include_uploads=True, include_dangling_tool_call_patch=True`
- **子代理**:通常是 `include_uploads=False, include_dangling_tool_call_patch=False`

理由:
- 子代理不直接面对用户,没必要处理 uploads
- 子代理的对话历史是主 Agent 直接提供的,不会有"悬空 tool call"的遗留问题

这种**按角色定制中间件链**的做法体现了中间件模式的灵活性。

### 为什么没有让子代理也能开子代理?

理论上可以,但实际代价高:

- **递归爆炸**:一层一层开下去,很容易就开出几百个 Agent
- **Debug 困难**:三层以上的嵌套,出问题几乎无法追溯
- **成本失控**:每一层都是独立的 LLM 调用,累加起来很吓人

DeerFlow 的设计是"结构上不支持"(子代理工具清单里没有 `task`),而不是"显式拒绝"。这是一种更稳妥的做法 —— **设计空间里不能做的事,最好让它根本做不出来,而不是靠运行时检查**。

---

## 延伸阅读

- 下一章:[07. Middleware](./07-middleware.md) —— `SubagentLimitMiddleware` 是怎么接入到 Agent Loop 的
- 相关章节:[05. Sandbox](./05-sandbox.md) —— 子代理共享沙箱的文件锁问题
- 相关章节:[02. Tools & MCP](./02-tools-and-mcp.md) —— `task` 工具在工具系统里的位置
- 外部:AutoGen / CrewAI 的多 Agent 协作模式 —— 另一种"Agent 协作"的思路(编排驱动而非 Agent 驱动)
