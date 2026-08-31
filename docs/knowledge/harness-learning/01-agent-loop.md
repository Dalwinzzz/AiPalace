# 01. Agent Loop — 智能体的"心跳"

> **一句话**:Agent Loop 是一个 `推理 → 动作 → 观察 → 再推理` 的循环,把"单次问答的 LLM"升级成"多步任务的 Agent"。

---

## 核心问题

裸 LLM 的调用模式是:

```
你 → (输入一段话) → LLM → (输出一段话) → 你
```

一来一回,结束。但真实任务不是这样的。比如"帮我找出本季度销售最差的三个产品,然后写一封道歉邮件给区域经理":

1. 先得**读销售数据文件**(LLM 自己做不到)
2. 然后**分析数据**(LLM 能做,但需要看到数据)
3. 再**写邮件**(LLM 能做,但需要知道经理是谁 → 读通讯录)
4. 最后**发送邮件**(LLM 做不到,需要工具)

这四步里,第 1、4 步 LLM 完全做不到,第 2、3 步 LLM 能做但需要前面的输出作为输入。所以必须有一个机制:

1. 让 LLM 说"我下一步想调用哪个工具"
2. Harness 执行工具并把结果告诉 LLM
3. LLM 根据结果决定再下一步做什么
4. 一直循环,直到任务完成

这个机制就是 **Agent Loop**。

---

## 通用概念

### ReAct 范式

Agent Loop 最主流的形式来自 2022 年的 ReAct 论文(**Re**ason + **Act**)。它的核心思想是:**让 LLM 交替地输出"思考"和"动作",让思考指导动作,让动作的结果反过来校正思考。**

一个 ReAct 轮次长这样:

```
Thought: 我需要先看看销售数据的结构。
Action: read_file("sales_q4.csv")
Observation: [文件内容:产品A 销售额 12000,产品B 销售额 50000,...]
Thought: 现在我可以按销售额排序找到最差的三个。
Action: run_python("df.sort_values('sales').head(3)")
Observation: [产品C, 产品E, 产品H]
Thought: 接下来查一下这三个产品对应哪个区域经理。
...
```

每一轮 LLM 都拿到"目前为止发生的所有事情"(包括自己之前的 Thought、Action、Observation),然后决定下一步。直到它觉得"任务完成了",输出一个最终答案。

### 现代实现:Tool Calling

ReAct 论文里,"Action" 是通过让模型输出一个特殊格式的字符串(比如 `Action: read_file("...")`),然后外部代码用正则匹配来识别。这很脆弱 —— 模型偶尔会打错括号。

所以现代 LLM 提供商(OpenAI、Anthropic、Google、DeepSeek)都提供了**原生 Tool Calling API**:

- 你在请求里声明"这些是我能提供的工具,它们的名字、参数 schema 是什么"
- 模型如果想调用工具,就输出一个结构化的 JSON(而不是自由文本)
- API 保证这个 JSON 是合法的、参数符合 schema

这种方式比字符串匹配稳定得多,所以 2024 年以后的 Agent 几乎都基于 Tool Calling 实现 Agent Loop。

### 循环是谁驱动的?

一个关键的问题:**谁来负责"执行这个循环"**?有两种典型做法:

| 方式 | 谁驱动循环 | 代表 |
| --- | --- | --- |
| **命令式循环** | 你自己写一个 `while` 循环,每一轮调 LLM、执行工具、拼接消息 | 很多教学示例,LangChain 的 `AgentExecutor` |
| **状态机驱动** | 把"当前是什么状态"、"下一步走哪条边"抽象成一个图,由一个 Runtime 负责推进 | **LangGraph**(DeerFlow 用的),AutoGen |

状态机方式有几个好处:

1. **可持久化**:状态可以序列化到数据库,宕机了能恢复
2. **可观测**:每一步的状态转换都能被追踪、可视化
3. **可中断**:外部可以发信号"暂停"、"重来"、"改变方向"
4. **可组合**:多个图可以嵌套(一个节点本身是一个子图)

代价是:你得先理解状态机这个抽象,初学曲线稍陡。

### 系统提示词(System Prompt)的角色

Agent Loop 能跑起来,系统提示词至关重要。它告诉模型:

- **你是谁**("你是一个帮助用户完成任务的 Agent")
- **你有什么工具**(通常由 Harness 自动生成工具清单拼进去)
- **你应该怎么思考**("一步一步推理,不确定时调用 `ask_clarification`")
- **你不该做什么**("不要删除用户的文件,除非他明确要求")
- **环境信息**(当前时间、工作目录、已有的技能、记忆事实等)

系统提示词本质上是 Agent 的"操作手册" —— 同一个 LLM 装不同的系统提示词,行为可以完全不同。DeerFlow 的系统提示词用的是**模板 + 变量注入**的方式,运行时动态拼装。

---

## DeerFlow 的实现

DeerFlow 的 Agent Loop 本质上是**在 LangGraph 上搭的一个状态机**。核心入口是 `make_lead_agent(config)`:

### 关键文件

- `backend/packages/harness/deerflow/agents/lead_agent/agent.py` — **核心**。`make_lead_agent(config)` 在这里。它读取运行时配置,创建模型、工具、中间件链、系统提示词,然后调用 LangChain 的 `create_agent()` 组装成一个 LangGraph 可执行对象。
- `backend/packages/harness/deerflow/agents/lead_agent/prompt.py` — 系统提示词模板和 `apply_prompt_template()` 函数。会注入 subagent 数量、可用 skill 列表、agent 名字等变量。
- `backend/packages/harness/deerflow/agents/thread_state.py` — `ThreadState` 数据类,定义一个会话所需的全部状态字段(messages、todo、sandbox 句柄等)。
- `backend/packages/harness/deerflow/agents/checkpointer/` — LangGraph checkpoint 适配,让状态可以持久化到数据库。

### 装配流程(读 `agent.py` 的顺序)

如果你打开 `agent.py`,建议按这个顺序读:

1. `make_lead_agent(config)`(底部)—— 入口函数
2. `_resolve_model_name(...)` —— 解析用户想用哪个模型(带 fallback)
3. `_build_middlewares(config, ...)` —— 组装中间件链(这是 Harness 的精华,单独在 [07-middleware](./07-middleware.md) 详细讲)
4. `create_agent(model=..., tools=..., middleware=..., system_prompt=..., state_schema=ThreadState)` —— 最后一步调用 LangChain,把所有东西装配成 LangGraph 图

这四步读完,你就理解 DeerFlow 的 Agent 是怎么"长出来"的。

### 循环由谁驱动?

DeerFlow 把循环交给 LangGraph —— 它不自己写 `while` 循环,而是用 `langchain.agents.create_agent()` 返回的一个图对象。这个图内部已经实现了:

- 调用模型 → 如果有工具调用 → 执行工具 → 拼消息 → 再调模型 → ...
- 中间件在每一步的前后插入(这就是 Middleware 能生效的原因)

所以 DeerFlow 的 "Agent Loop" **不是一段写在 `agent.py` 里的代码,而是 LangGraph 图的执行语义**。如果你想深入理解这个图长什么样,可以去读 `langchain/agents/create_agent.py` 的实现(不过这超出了本文档的范围)。

### ThreadState:一轮对话的"工作台"

每一个进行中的 Agent 会话,LangGraph 都会维护一个 `ThreadState` 对象,保存:

- `messages`:历史消息列表(用户、AI、tool call、tool result)
- todos:如果启用了 plan mode,这里有 Agent 自己列的 todo 清单
- 沙箱句柄、工作目录、已加载技能等其他运行时字段

每当模型输出一条新消息、每当工具返回结果,`ThreadState` 都会被更新;中间件可以在每个节点前后读写这个状态。可以把它理解成 Agent 的"工作台",上面摊着它当前能看到的所有东西。

---

## 设计权衡

### 为什么用 LangGraph 而不是自己写循环?

DeerFlow 选 LangGraph 的理由(推断自代码组织):

**优点**:
- 不用自己实现 checkpoint / 恢复 / 中断
- 内置流式输出语义(和前端配合的核心)
- 社区生态大,Middleware 模式天然契合
- 状态机的可观测性远好于命令式循环

**代价**:
- 多一层抽象,初学需要先理解 LangGraph 的概念
- 版本升级可能引入不兼容(LangGraph 还在快速迭代)
- 某些精细控制(比如超低延迟场景)反而不如手写循环灵活

### 为什么区分 "Lead Agent" 和 "Sub-agent"?

DeerFlow 的主 Agent 叫 `lead_agent`,还有专门的 `subagents/` 目录定义子代理。为什么不是统一一种 Agent?

因为**两者关心的事情不一样**:

- **Lead Agent** 直接面对用户,关心上下文、多模态、对话记忆、UI 交互(比如澄清问题、进度汇报)
- **Sub-agent** 是被主 Agent 调用的"工人",关心任务执行、并发、超时、独立上下文

所以它们的中间件链是不同的(在 `tool_error_handling_middleware.py` 里你能看到 `build_lead_runtime_middlewares()` 和 `build_subagent_runtime_middlewares()` 两套)。共享底层(沙箱、工具错误处理等)但独立顶层(澄清、标题生成不给子代理用)。

### System Prompt 放哪里?

DeerFlow 把系统提示词模板放在 `prompt.py`,用 Jinja 风格的变量注入。好处:

- 提示词本身是"数据",不是代码 —— 修改不需要重启服务(可以做热更新)
- 可以按语言、按用户角色、按运行模式切换不同模板

代价:模板的 bug 只有在运行时才暴露。所以 DeerFlow 在 `tests/` 里有针对 prompt 的单测。

---

## 延伸阅读

- 下一章:[02. Tools & MCP](./02-tools-and-mcp.md) —— 了解 Agent 的"手"是怎么装上去的
- 相关章节:[07. Middleware](./07-middleware.md) —— Agent Loop 中每一步前后能插入的"拦截器"
- 相关章节:[04. Memory](./04-memory.md) —— `ThreadState` 里的记忆字段是怎么被填充的
- 外部:[ReAct: Synergizing Reasoning and Acting in Language Models](https://arxiv.org/abs/2210.03629) —— Agent Loop 的理论起源
- 外部:LangGraph 官方文档 —— 如果你想深入理解状态机实现
