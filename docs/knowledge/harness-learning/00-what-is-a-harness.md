# 00. 什么是 Agent Harness?为什么需要它?

> **一句话**:Harness 是包在 LLM 外面的那一整套基础设施,把一个"只会生成下一段文字"的大模型,变成一个能"在真实世界里完成复杂任务"的 Agent。

---

## 核心问题

想象一下,你只给一个刚从实验室里走出来的大语言模型(比如 GPT-4 或 Claude)一台电脑,让它帮你"写一份关于下季度销售的报告"。它大概率会这样:

1. 它能**写字** —— 输出一段文字。
2. 但它**不记得**你昨天跟它说过什么销售数据,因为每次请求都是独立的。
3. 它**看不到**你电脑上的 CSV 文件,因为它没有读文件的能力。
4. 它**执行不了** `python analyze.py`,因为它没有运行命令的手。
5. 它**不知道**现在是几月、外面有没有发生大事,因为它的知识截止到训练数据那一刻。
6. 如果你真的让它自己去跑命令,**没人拦得住它**误删了你的重要文件。
7. 如果它卡住了反复调一个坏掉的工具,**没人叫停它**,你会看着它把余额里的 token 烧完。

这些问题**每一个都不是大模型本身能解决的**。它们要在 LLM 之外解决。LLM 只管"生成下一个 token",其他一切 —— 记忆、感知、动作、安全、恢复 —— 都得靠外面的一层"壳"。

这层壳,就是 **Harness(脚手架 / 挽具)**。

---

## 通用概念

### "Harness" 这个词的由来

Harness 在英文里本意是"马具":你给马套上马具,它才能拉车干活;没有马具,马再强壮也只是匹野马。放到 AI 领域,大模型就是那匹"马",Harness 就是让它能被用来干活的那一整套装备。

更技术一点的说法:

> **Harness = 一个以 LLM 为核心决策器、但由大量非 LLM 代码组成的运行时系统,负责记忆、工具接入、执行隔离、错误恢复、可观测、扩展性等一切 LLM 本身不具备的能力。**

### 一个典型的 Harness 都包含什么?

基本上所有"严肃"的 Agent 框架都会包含下面这几块。它们之间的组合方式可能不同,但缺一块就算不上完整的 Harness:

| 模块 | 作用 | 如果缺了会怎样 |
| --- | --- | --- |
| **Agent Loop(智能体循环)** | 让模型能"边想边做":推理 → 调用工具 → 看结果 → 再推理 | 模型只能一问一答,做不了多步任务 |
| **Tools(工具系统)** | 让模型能调用外部函数:读文件、执行命令、访问 API | 模型只能"说",不能"做" |
| **Memory(记忆)** | 跨轮次、跨会话地保留信息 | 每次都从零开始,用户体验极差 |
| **Context Engineering(上下文工程)** | 管理每轮该给模型看哪些内容,避免爆上下文窗口 | 对话稍长就塞不下了,或钱包烧光 |
| **Sandbox(沙箱)** | 隔离模型的副作用,让它不能搞垮宿主环境 | 模型一个 `rm -rf /` 就把系统干掉了 |
| **Middleware(中间件)** | 横切关注点:日志、限流、审计、护栏 | 所有功能全揉在核心代码里,无法维护 |
| **Sub-agents(子代理)** | 把大任务拆给多个 Agent 并行处理 | 单 Agent 吃不下复杂任务,上下文爆炸 |
| **Skills(技能)** | 可插拔的工作流 / 能力包 | Agent 能力只能硬编码,无法扩展 |
| **Observability(可观测)** | 追踪、日志、成本统计 | 出问题无法 debug,账单无法审计 |

### Harness 和 "Agent 框架" 是同一个东西吗?

严格说不完全是,但实践中可以近似等同。区别在于语气:

- **"Agent 框架"** 强调"给开发者用的 API/SDK",重点是"你怎么用它来写 Agent"。典型代表:LangChain、LlamaIndex、AutoGen。
- **"Agent Harness"** 强调"把模型运行时需要的一切打包好",重点是"Agent 在运行时需要哪些设施"。典型代表:Claude Code、Cursor Agent、DeerFlow 2.0。

你可以这样理解:**Harness 是 Agent 框架站在"运行时基础设施"视角的重新命名**。它的兴起反映了社区共识的转变 —— 大家越来越意识到:

> **做一个好用的 Agent,难点不在"调用模型",而在模型之外的那些基础设施。**

这也是 Harness 这个词最近越来越火的原因。

### 为什么 Harness 比"单次调 API"难这么多?

一个常见的误解是:"Agent 不就是一个循环调 `chat.completions.create` 吗?"

表面看确实是,但你真去写一个:

```python
while True:
    response = model.generate(messages)
    if response.has_tool_call:
        result = execute_tool(response.tool_call)
        messages.append(result)
    else:
        return response.text
```

你会立刻遇到一连串问题:

1. **上下文怎么管?** 跑几轮后 `messages` 就爆了。
2. **工具出错了怎么办?** 异常抛出去,循环直接崩。
3. **模型疯了反复调同一个坏工具怎么办?** 你得检测死循环。
4. **要不要支持中断?** 用户可能想让它停下来。
5. **工具并发怎么办?** 一次 `response` 里可能有 5 个 tool call,串行跑慢,并行跑会撞车。
6. **跨会话的记忆怎么保存?** `messages` 是内存里的,关掉进程就没了。
7. **多个用户同时用,怎么隔离?** 不能让 A 用户的 Agent 看到 B 的文件。
8. **怎么加护栏,阻止它做危险操作?** 不能任由模型 `rm -rf`。
9. **怎么 debug?** 模型为什么做出这个决定,得能追溯。

这九个问题,每个都是 Harness 要解决的 —— 而且每个都需要精心设计,没有"一行代码搞定"的方案。这就是为什么"写一个玩具 Agent"只要两百行,而"写一个能上线的 Agent"需要几万行代码。

---

## DeerFlow 的实现(概览)

DeerFlow 2.0 是一个**教科书级**的 Harness 实现,因为:

1. 它的核心 Python 包的名字就叫 `deerflow-harness`(在 `backend/packages/harness/` 下),这在命名上就表明了它的定位。
2. 它的 README 自称 "super agent harness that orchestrates sub-agents, memory, and sandboxes"。
3. 它的架构严格遵循**两层分离**原则:
   - **Harness 层**(`backend/packages/harness/deerflow/`)—— 可独立发布的 Agent 基础设施
   - **App 层**(`backend/app/`)—— 基于 Harness 构建的 Web 服务
   规则:`app` 可以 import `deerflow`,但 `deerflow` 永远不能 import `app`。这种"单向依赖"是识别一个好 Harness 的标志。

### 关键入口文件

- `backend/packages/harness/deerflow/agents/lead_agent/agent.py` — **主 Agent 的工厂**:`make_lead_agent(config)` 在这里,它把所有 Harness 组件"装配"成一个可运行的 Agent。**读代码从这里开始。**
- `backend/packages/harness/deerflow/agents/lead_agent/prompt.py` — 系统提示词模板
- `backend/packages/harness/deerflow/agents/thread_state.py` — `ThreadState` Schema,定义一个会话的状态结构
- `backend/README.md` + `backend/CLAUDE.md` — 项目整体架构说明
- `README.md`(项目根目录) — DeerFlow 对自己的定义

### 整体架构(超简化版)

```
                 ┌────────────────────────────────────────┐
                 │            用户 / 前端                 │
                 └────────────────────┬───────────────────┘
                                      │
                 ┌────────────────────▼───────────────────┐
                 │    Gateway API (FastAPI, app.*)        │
                 └────────────────────┬───────────────────┘
                                      │
                 ┌────────────────────▼───────────────────┐
                 │       Harness 层 (deerflow.*)          │
                 │  ┌─────────────────────────────────┐   │
                 │  │  Lead Agent (LangGraph)         │   │
                 │  │  + 15 个 Middlewares            │   │
                 │  │  + Tools 注册表                 │   │
                 │  │  + System Prompt                │   │
                 │  └─────────────────────────────────┘   │
                 │  ┌─────────┬─────────┬─────────────┐   │
                 │  │ Memory  │ Sandbox │  Sub-agents │   │
                 │  ├─────────┼─────────┼─────────────┤   │
                 │  │ Skills  │  MCP    │ Guardrails  │   │
                 │  └─────────┴─────────┴─────────────┘   │
                 └────────────────────┬───────────────────┘
                                      │
                 ┌────────────────────▼───────────────────┐
                 │       LLM (OpenAI/Claude/DeepSeek/...) │
                 └────────────────────────────────────────┘
```

后面每一章我们会把这张图里的一个方块单独拎出来讲。

---

## 设计权衡

### 为什么非要分出一个"Harness 层"?直接把所有代码写在 Gateway 里不行吗?

**行,但不好**。分层的好处:

1. **可独立发布**:`deerflow-harness` 可以作为一个独立的 pip 包被其他项目引用,不用被 Gateway 绑死。
2. **可独立测试**:不启动 Web 服务就能单测 Agent 逻辑。
3. **替换前端容易**:想从 Web 换成 CLI 或 Slack Bot,只要写一个新的 `app` 层,Harness 不用动。
4. **更好的边界**:单向依赖约束逼着开发者把"Web 相关"的东西(HTTP、session、鉴权)留在 `app` 层,不污染 Harness。

代价是:多了一层抽象,文件数变多,初次阅读的心智负担稍大。但对于长期维护的项目,这几乎总是值得的。

### Harness 要不要做成"框架"(让用户继承)还是"库"(让用户调用)?

这是 Agent 领域的长期争论。DeerFlow 走的是"**库 + 约定**"路线:

- 核心逻辑通过**函数 + 配置**组装(`make_lead_agent(config)`),不是"继承 BaseAgent 再覆写几个方法"
- 扩展点通过**中间件 + Provider**抽象(你可以注入新的 Middleware 和 SandboxProvider,但不用继承 Agent 类)
- 配置通过 YAML + 环境变量(不用写 Python 代码就能改行为)

这种设计的好处是**组合优于继承**,坏处是约定多了以后学习曲线陡峭。

### "Super Agent" 是什么意思?

DeerFlow 在 README 里自称是 "super agent harness"。"super" 不是营销词,它指的是:

> **一个能调用其他 Agent 作为工具的 Agent。**

也就是说,DeerFlow 的主 Agent(Lead Agent)自己就有一个 `task()` 工具,可以把子任务丢给"子代理"(Sub-agent)去做。从主 Agent 的视角看,子代理只是"一个特殊的工具";从子代理的视角看,它也是一个完整的 Agent。这是一种"递归组合",大幅扩展了 Agent 能处理的任务复杂度。我们会在 [06-subagents](./06-subagents.md) 详细讨论。

---

## 延伸阅读

- 本系列下一章:[01. Agent Loop](./01-agent-loop.md) —— 理解 Agent 的"心脏"是怎么跳动的
- DeerFlow 官方 README:`/Users/dalwin/Library/CodeRepo/AI/deer-flow/README.md`
- Claude Code 的"Harness"介绍(如果你想看另一个 Harness 案例):Anthropic 官方博客关于 Claude Code 架构的文章
- 论文:ReAct: Synergizing Reasoning and Acting in Language Models (Yao et al., 2022) —— Agent Loop 的理论起源
