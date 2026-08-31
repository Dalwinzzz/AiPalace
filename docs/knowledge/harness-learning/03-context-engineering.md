# 03. Context Engineering — 决定"给模型看什么"

> **一句话**:Context Engineering 是 Harness 最被低估、却最决定 Agent 质量上限的一环 —— 它管理"每一轮请求里,到底该把哪些内容塞给 LLM"。

---

## 核心问题

你可能听说过一种说法:**"Agent 表现好不好,90% 看 prompt"**。这句话更准确的说法应该是:**"Agent 表现好不好,90% 看每一轮进入模型的那段上下文是怎么构造的。"**

这个"构造"的过程就是 **Context Engineering(上下文工程)**。

具体的挑战:

1. **上下文窗口是有限的**。哪怕是 Claude 200k 或 GPT-4o 128k,对一个跑了几十轮的 Agent 来说也会爆。
2. **上下文不是越多越好**。塞太多不相关信息,模型的注意力会被稀释,甚至"迷失在长文本中间"(Lost in the Middle 现象)。
3. **上下文必须是"合法的"**。比如工具调用的消息必须和工具结果配对,否则模型会困惑。
4. **上下文要能容纳多模态**。视觉模型需要图片数据,文本模型不需要 —— 不能一刀切。
5. **上下文要能容纳外部状态**。用户新上传了文件?记忆里有相关事实?都要塞进去。

Context Engineering 就是一整套"决策 + 操作"的机制,在**每一次调用模型之前**,把上面这些问题一个个处理掉。

---

## 通用概念

### 上下文是由什么构成的?

一次 LLM 请求的上下文,通常包含这几类内容:

```
┌────────────────────────────────────────┐
│ System Prompt                          │  ← Harness 生成,每一轮都有
├────────────────────────────────────────┤
│ 工具 Schema 清单                       │  ← Harness 生成,每一轮都有
├────────────────────────────────────────┤
│ 历史消息                               │  ← 随对话增长
│  - 用户输入                            │
│  - 模型回复                            │
│  - Tool Call (模型发起)                │
│  - Tool Result (Harness 返回)          │
│  - ...                                 │
├────────────────────────────────────────┤
│ 当前轮次的新输入                       │  ← 本轮的新消息
└────────────────────────────────────────┘
```

Context Engineering 要对**每一层**做决策:

- **System Prompt**:基础模板 + 动态变量(技能、记忆、环境)怎么拼?
- **工具 Schema**:全部给?还是只给相关的?(参考延迟加载)
- **历史消息**:全部保留?还是压缩?还是截断?
- **新输入**:有附件吗?有图片吗?有上传文件吗?

### 几个关键操作

#### 1. System Prompt 模板化

把 System Prompt 分成**静态模板 + 动态变量**。比如:

```
你是 DeerFlow,一个帮助用户完成任务的 Agent。

今天是 {{date}}。
工作目录:{{workdir}}。

你记得的事实:
{{memory_facts}}

可用技能:
{{skill_list}}

...
```

这种模式的好处:修改模板不影响变量注入,单元测试容易。

#### 2. Summarization(上下文压缩)

当历史消息累积到一定长度时,**用模型本身(通常是便宜的模型)把前面的对话压缩成一段摘要**,然后用这段摘要替换原始消息。这样上下文长度可控,但关键信息不丢失。

触发条件可以是:
- 总 token 数超过阈值
- 消息数超过阈值
- 距离上次压缩已经过去 N 轮

保留策略也可以微调:
- 保留最近 M 条消息不压缩(因为它们和"正在做的事"最相关)
- 保留所有 tool call 结果不压缩(因为它们是"事实")
- 只压缩用户和 AI 的自然语言部分

#### 3. Dangling Tool Call 修复

这是一个很多人没意识到的坑。

考虑这种情况:
- 模型发起了一个 `tool_call`(id = "abc")
- 工具执行失败,或被中间件截获,没有产生 `tool_result`
- 下一轮,消息列表里只有一个"悬空的 tool_call",没有对应的 result

这时候把消息发给模型,大多数 LLM 会报错或者行为异常 —— 因为 Tool Calling 协议要求 call 和 result 必须配对。

**Dangling Tool Call 修复**就是在把消息送去模型之前,扫一遍历史,给所有悬空的 tool_call 补一个"错误 ToolMessage"(内容类似"此工具调用未返回结果")。

#### 4. Uploads 注入

用户上传了一个文件,Agent 该怎么"看到"它?有几种做法:

- **路径注入**:只把"文件路径"加入系统提示词,让 Agent 自己去读(省 token)
- **内容注入**:把文件内容直接塞进 prompt(贵,但 Agent 立刻能用)
- **引用注入**:给 Agent 一个"文件列表 + ID",Agent 调 `read_file(id)` 来获取内容(最灵活)

DeerFlow 默认走的是**引用 + 路径**的混合模式,由 `UploadsMiddleware` 负责。

#### 5. 视觉模型的图像注入

如果你用的是支持视觉的模型(GPT-4o、Claude 3.5、Gemini 2.5),你需要在 prompt 里插入**图像数据**(base64 或 URL)。但如果你用的是纯文本模型,插入图像会报错。

**视觉注入中间件**的逻辑很简单:**判断当前模型是否支持 vision,只有支持时才注入图像;不支持时,把图片转成"请参考这张图片:<描述>"的文本**。这个判断需要读模型配置,所以它得是 per-request 的。

---

## DeerFlow 的实现

DeerFlow 的 Context Engineering 是**分散在多个中间件 + 一个统一的系统提示词模板**里实现的。

### System Prompt

- `backend/packages/harness/deerflow/agents/lead_agent/prompt.py` — **主系统提示词模板**。你能在这里看到 DeerFlow 是怎么把"agent name、可用技能、subagent 限制、当前日期"等变量注入提示词的。`apply_prompt_template(...)` 是入口函数。

### Summarization

DeerFlow 没有自己实现 Summarization,而是复用了 LangChain 官方提供的:

- `langchain.agents.middleware.SummarizationMiddleware` — 来自 `langchain.agents.middleware`(外部依赖),由 DeerFlow 在 `agent.py` 里调用 `_create_summarization_middleware()` 来创建和配置
- `backend/packages/harness/deerflow/config/summarization_config.py` — DeerFlow 自己的配置文件,定义了 trigger(何时触发)、keep(保留多少不压缩)、summary_prompt(压缩时用的提示词)等

在 `agent.py` 的 `_create_summarization_middleware()` 函数里你能看到**专门用一个轻量模型跑压缩**的逻辑 —— 因为 Summarization 不需要最强的模型,用便宜模型既省钱又够用。

### Dangling Tool Call 修复

- `backend/packages/harness/deerflow/agents/middlewares/dangling_tool_call_middleware.py` — 在模型看到历史消息之前扫一遍,给悬空的 tool_call 补上错误 `ToolMessage`。注释明确说 "patches missing ToolMessages before model sees the history"。

### Uploads 注入

- `backend/packages/harness/deerflow/agents/middlewares/uploads_middleware.py` — 把用户上传的文件作为上下文的一部分注入给 Agent
- `backend/packages/harness/deerflow/uploads/` — 上传文件的元数据管理

这个中间件在 `tool_error_handling_middleware.py` 的 `_build_runtime_middlewares()` 里被**特意插在位置 1**(即 `ThreadDataMiddleware` 之后,`SandboxMiddleware` 之前),因为它需要 `thread_id` 才知道该加载哪个会话的上传文件。

### 视觉模型的图像注入

- `backend/packages/harness/deerflow/agents/middlewares/view_image_middleware.py` — 视觉模型图像注入中间件
- 在 `agent.py` 里:`if model_config.supports_vision: middlewares.append(ViewImageMiddleware())` —— 只在模型支持视觉时才加入中间件链
- 对应的用户工具:`backend/packages/harness/deerflow/tools/builtins/view_image_tool.py` —— 让 Agent 能主动"看"一张图片

### Token Usage 统计

- `backend/packages/harness/deerflow/agents/middlewares/token_usage_middleware.py` — 精细统计每一轮的 token 消耗,便于成本审计和触发告警
- `backend/packages/harness/deerflow/config/token_usage_config.py` — 配置开关

这和 Context Engineering 有什么关系?因为**"省 token"是 Context Engineering 的一个核心动机**。你得先知道花了多少,才能决定哪里值得压缩。

### Title 自动生成

- `backend/packages/harness/deerflow/agents/middlewares/title_middleware.py` — 在第一轮对话结束后,自动生成一个会话标题(用更小的模型)

这个中间件本质上是**一次额外的 LLM 调用**,把它放在中间件里管理,而不是 Gateway 层 —— 体现了 "把所有与对话内容相关的智能处理都收敛到 Harness 里"的设计思路。

---

## 设计权衡

### 为什么 Context Engineering 散在多个中间件里?

一个替代方案是:**写一个巨大的 `ContextManager` 类**,里面统一处理所有上下文构造。为什么 DeerFlow 不这么做?

因为上下文构造的不同步骤**依赖条件不同**:

- Uploads 注入只在"有上传"时有意义
- 视觉注入只在"模型支持视觉"时有意义
- Summarization 只在"开启压缩"时有意义
- Dangling tool call 修复只在"有悬空 call"时有意义

把它们拆成独立中间件,每个都有自己的启用开关和顺序,**组合比继承灵活,调试也更容易**。想禁用某一项?把对应中间件从链里移除即可,其他不受影响。

### 为什么 Summarization 要用"更小的模型"?

Summarization 本质上是一个"语言任务",不需要最强的推理能力。**用 GPT-4 做 Summarization 和用 GPT-4o-mini 做效果差别不大,但成本可能差 10 倍以上**。所以 DeerFlow 在 `_create_summarization_middleware()` 里明确注释 "Use a lightweight model for summarization to save costs"。

这是一个小细节,但反映了 **Harness 工程思维**:每一个 LLM 调用都要考虑"最便宜的模型能不能做",而不是"一招鲜吃遍天"。

### 为什么 Title 生成也做成中间件?

替代方案是在 Gateway 里写一个 endpoint,用户主动触发 "generate title"。DeerFlow 选择做成中间件,好处是:

- **自动**,不需要用户或前端主动触发
- **上下文现成**,中间件拿到的就是对话历史,不用再传一次
- **可以用更强的 prompt**,因为不暴露给前端,改起来方便

代价是:每次会话都会多一次 LLM 调用(虽然是小模型)。DeerFlow 认为这个代价可以接受。

### 静态工具 Schema vs 延迟加载

一个扁平的 Context Engineering 会**每一轮都把所有工具 schema 塞进 prompt**。当工具超过 20 个以后,这会显著变慢、变贵。

DeerFlow 的**延迟加载**方案(`DeferredToolFilterMiddleware` + `tool_search` 工具)避开了这个问题:

- 平时只给模型看核心的几个工具 + 一个 `tool_search`
- 需要用某类工具时,模型先调 `tool_search("我需要做 X")`
- 返回匹配的工具 schema,模型下一轮才真正调用

代价是多一次工具调用,但当工具数量 > 20 时,这个取舍几乎总是划算的。

---

## 延伸阅读

- 下一章:[04. Memory](./04-memory.md) —— 长期记忆怎么注入到 System Prompt(这也是 Context Engineering 的一部分)
- 相关章节:[07. Middleware](./07-middleware.md) —— 上面提到的所有 Middleware 的完整清单和顺序
- 相关章节:[02. Tools & MCP](./02-tools-and-mcp.md) —— 工具 Schema 和延迟加载的更多细节
- 外部:[Lost in the Middle: How Language Models Use Long Contexts](https://arxiv.org/abs/2307.03172) —— 为什么"上下文不是越多越好"的经典论文
