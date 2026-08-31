# 07. Middleware Pipeline — Harness 的"脊柱"

> **一句话**:Middleware 是 Agent Loop 每一步前后的"拦截器",让横切关注点(日志、错误处理、限流、注入)和核心业务逻辑完全解耦。理解了中间件,你就理解了 DeerFlow 的架构哲学。

---

## 核心问题

回到 Agent Loop 的基本形态:

```
调用模型 → 处理响应 → 执行工具 → 回到调用模型
```

现实中,**每一个箭头前后都需要做一堆"额外的事"**:

**调用模型之前**需要:
- 注入系统提示词
- 压缩长上下文
- 注入长期记忆事实
- 注入上传文件信息
- 修复悬空 tool call
- 检查 token 用量
- 注入图像数据(视觉模型)

**调用模型之后**需要:
- 记录 token 消耗
- 检测循环
- 转换异常为 ToolMessage
- 触发 title 生成(首轮后)
- 触发 memory 抽取(异步)

**执行工具之前**需要:
- 安全检查(护栏)
- 权限检查
- 审计记录
- 延迟工具过滤

**执行工具之后**需要:
- 错误包装
- 沙箱审计
- Clarification 截获

如果你把这些**全都写在核心 Agent Loop 里**,会得到一个两千行的大函数,谁也维护不了。

Middleware 模式的提出就是为了拆散这团乱麻。

---

## 通用概念

### 什么是中间件?

**中间件是一种可组合的、能在"主流程的某个节点前后插入逻辑"的组件。** 它的核心承诺是:

1. **每个中间件只关心一件事**(single responsibility)
2. **中间件之间通过"链"(pipeline)串联**
3. **中间件可以拦截、修改、阻断主流程**

写过 Web 框架(Express、Koa、FastAPI、Django)的人对这个概念会很熟悉。**Agent 框架的中间件就是把 Web 中间件的思想搬到 Agent Loop 上来**。

形象一点:

```
request → [M1] → [M2] → [M3] → 核心逻辑 → [M3] → [M2] → [M1] → response
            ↑       ↑       ↑                ↑       ↑       ↑
          前置    前置    前置             后置    后置    后置
```

每个中间件都有机会在核心逻辑前后执行代码。调用顺序像"洋葱"一样 —— 最外层的最先看到 request,最后看到 response。

### 横切关注点(Cross-Cutting Concerns)

Middleware 解决的问题在软件工程里有个专有名词:**横切关注点**。

横切关注点的特征是:

- **和业务逻辑正交**(日志、权限、错误处理都和"具体在做什么"无关)
- **在很多地方都要做**(几乎每个方法都要记日志、每个方法都可能抛异常)
- **需求会变**(今天要记到文件,明天要记到 Kafka,后天要加采样)

这些事情如果硬编码到业务逻辑里,会导致:

- 代码高度重复
- 修改要动很多地方
- 业务逻辑被淹没在"基础设施"代码里

Middleware(或它的近亲 Aspect-Oriented Programming)是解决横切关注点的经典方案。

### 中间件的三种"钩子"

在 LangChain 的中间件模型里,一个中间件可以实现多种钩子:

| 钩子 | 调用时机 | 典型用途 |
| --- | --- | --- |
| `before_agent` | 一次 Agent 运行开始前 | 初始化上下文、注入状态 |
| `before_model` | 每次调用模型前 | 修改消息、注入记忆、压缩历史 |
| `after_model` | 每次模型响应后 | 记录 token、检测循环、提取摘要 |
| `wrap_tool_call` | 包裹每次工具调用 | 异常处理、审计、权限检查 |
| `after_agent` | 一次 Agent 运行结束后 | 清理资源、触发后台任务 |

一个中间件可以只实现其中一种钩子,也可以实现多种。**实现哪种钩子,决定了它能在什么时机做什么事**。

### 顺序很重要

中间件的**顺序是有语义的**。举个例子:

```
认证中间件 → 速率限制中间件 → 业务逻辑
```

这个顺序是对的:**先认证,后限速,才能按用户身份统计限流**。

如果反过来:

```
速率限制中间件 → 认证中间件 → 业务逻辑
```

就错了:**还没认证怎么按用户限流?** 只能按 IP 限流,效果差很多。

DeerFlow 的中间件链在 `agent.py` 里有大量注释解释顺序依赖,非常值得精读。

---

## DeerFlow 的实现

DeerFlow 有**15 个中间件文件**(加上外部来源的 `SummarizationMiddleware` 就是 16 个)。它们分散在两个目录:

- `backend/packages/harness/deerflow/agents/middlewares/` — 大部分(15 个)
- `backend/packages/harness/deerflow/sandbox/middleware.py` — `SandboxMiddleware`
- `backend/packages/harness/deerflow/guardrails/middleware.py` — `GuardrailMiddleware`
- `langchain.agents.middleware.SummarizationMiddleware` — 外部依赖

### 中间件清单(按功能分类)

| 中间件 | 文件 | 作用 |
| --- | --- | --- |
| **线程数据** | `thread_data_middleware.py` | 为当前 thread 创建隔离的数据目录,注入 `thread_id` |
| **上传** | `uploads_middleware.py` | 把用户上传的文件作为上下文的一部分注入 |
| **沙箱** | `sandbox/middleware.py` | 为当前 thread 获取 / 释放沙箱实例 |
| **悬空工具修复** | `dangling_tool_call_middleware.py` | 扫描历史,给未返回结果的 tool_call 补错误消息 |
| **LLM 错误处理** | `llm_error_handling_middleware.py` | 捕获 LLM 调用异常,转为可恢复状态 |
| **护栏** | `guardrails/middleware.py` | 策略层的安全检查(可插拔 provider) |
| **沙箱审计** | `sandbox_audit_middleware.py` | 审计沙箱操作,记录到审计日志 |
| **工具错误处理** | `tool_error_handling_middleware.py` | 把工具异常转换成 `ToolMessage(status="error")`,让循环能继续 |
| **摘要** | `langchain.agents.middleware.SummarizationMiddleware` | 上下文压缩(达到阈值时用轻量模型摘要) |
| **Todo 列表** | `todo_middleware.py` | 提供 `write_todos` 工具(plan mode 下启用) |
| **Token 统计** | `token_usage_middleware.py` | 精细统计每轮 token 消耗 |
| **标题生成** | `title_middleware.py` | 首轮后自动生成会话标题 |
| **记忆** | `memory_middleware.py` | 注入长期记忆到 System Prompt,异步触发抽取 |
| **图像注入** | `view_image_middleware.py` | 视觉模型专用,注入图像数据 |
| **延迟工具过滤** | `deferred_tool_filter_middleware.py` | 从 schema 列表里隐藏延迟加载的工具 |
| **子代理限制** | `subagent_limit_middleware.py` | 拦截超出并发上限的 `task` 调用 |
| **循环检测** | `loop_detection_middleware.py` | 检测并打破模型的重复工具调用循环 |
| **澄清** | `clarification_middleware.py` | 截获 `ask_clarification` 调用,转为对用户的提问 |

### 两套运行时中间件链

DeerFlow 区分了两类 Agent 的基础中间件链:

- `build_lead_runtime_middlewares()` — 主 Agent 的基础中间件链(在 `tool_error_handling_middleware.py` 里定义)
- `build_subagent_runtime_middlewares()` — 子代理的基础中间件链

两者的区别:

| 中间件 | 主 Agent | 子代理 |
| --- | --- | --- |
| ThreadData | ✅ | ✅ |
| Uploads | ✅ | ❌ |
| Sandbox | ✅ | ✅ |
| DanglingToolCall | ✅ | ❌ |
| LLMErrorHandling | ✅ | ✅ |
| Guardrail | ✅(可配置) | ✅(可配置) |
| SandboxAudit | ✅ | ✅ |
| ToolErrorHandling | ✅ | ✅ |

基础之上,主 Agent 额外拼接了另一批只属于"面对用户"的中间件(Title、Memory、Clarification 等)。这种分层让"给不同角色的 Agent 配不同中间件链"变得非常自然。

### 装配入口

- `backend/packages/harness/deerflow/agents/lead_agent/agent.py` — `_build_middlewares(config, ...)` 函数(第 208 行左右)是**主 Agent 中间件链的完整装配**。读这个函数最能理解 DeerFlow 的中间件组织逻辑。

装配顺序(简化版):

```python
# 1. 基础中间件(来自 build_lead_runtime_middlewares)
#    ThreadData → Uploads → Sandbox → DanglingToolCall → LLMErrorHandling
#    → Guardrail → SandboxAudit → ToolErrorHandling
middlewares = build_lead_runtime_middlewares(lazy_init=True)

# 2. Summarization(如果启用)
if enabled: middlewares.append(SummarizationMiddleware(...))

# 3. TodoList(如果 plan mode)
if is_plan_mode: middlewares.append(TodoMiddleware(...))

# 4. TokenUsage(如果启用)
if enabled: middlewares.append(TokenUsageMiddleware())

# 5. Title
middlewares.append(TitleMiddleware())

# 6. Memory(必须在 Title 之后)
middlewares.append(MemoryMiddleware(agent_name=agent_name))

# 7. ViewImage(只在视觉模型启用)
if model_supports_vision: middlewares.append(ViewImageMiddleware())

# 8. DeferredToolFilter(如果启用 tool_search)
if tool_search_enabled: middlewares.append(DeferredToolFilterMiddleware())

# 9. SubagentLimit(如果启用 subagent)
if subagent_enabled: middlewares.append(SubagentLimitMiddleware(...))

# 10. LoopDetection(始终)
middlewares.append(LoopDetectionMiddleware())

# 11. 自定义中间件(可选)
if custom: middlewares.extend(custom)

# 12. Clarification(始终最后)
middlewares.append(ClarificationMiddleware())
```

### 顺序依赖的注释

`agent.py` 第 198-207 行有一段非常有价值的注释,解释了为什么中间件顺序是这样:

```python
# ThreadDataMiddleware must be before SandboxMiddleware to ensure thread_id is available
# UploadsMiddleware should be after ThreadDataMiddleware to access thread_id
# DanglingToolCallMiddleware patches missing ToolMessages before model sees the history
# SummarizationMiddleware should be early to reduce context before other processing
# TodoListMiddleware should be before ClarificationMiddleware to allow todo management
# TitleMiddleware generates title after first exchange
# MemoryMiddleware queues conversation for memory update (after TitleMiddleware)
# ViewImageMiddleware should be before ClarificationMiddleware to inject image details before LLM
# ToolErrorHandlingMiddleware should be before ClarificationMiddleware to convert tool exceptions to ToolMessages
# ClarificationMiddleware should be last to intercept clarification requests after model calls
```

**这段注释值得逐行细读** —— 它把 DeerFlow 团队在设计中间件顺序时考虑的所有依赖关系说清楚了。

---

## 设计权衡

### 为什么用中间件模式,不是继承?

一个替代方案是:**定义一个 `BaseAgent` 类,子类覆写不同方法来加功能**。比如 `LeadAgent(BaseAgent)`、`SubAgent(BaseAgent)`、`LeadAgentWithMemory(LeadAgent)`。

这种方式的问题:

1. **组合爆炸**:想要"带记忆但不带 title 生成"的 Agent?得再继承一次。有 N 个开关,就会有 2^N 种组合。
2. **修改影响面大**:改基类影响所有子类,容易引入回归。
3. **多继承混乱**:Python 的 MRO 在深层继承时几乎没人能预测对。

中间件模式的好处:

1. **线性组合**:要什么中间件加什么,不要的就不加。数量再多也是线性管理。
2. **运行时配置**:可以根据 `config` 决定装配什么中间件,不需要预先定义类。
3. **测试友好**:每个中间件单独测,链路测试通过组合覆盖。

### 为什么默认用"懒初始化"(lazy_init=True)?

在 `build_lead_runtime_middlewares(lazy_init=True)` 里,`lazy_init=True` 是默认值。含义是:

**中间件对象在创建时,不立刻初始化它们依赖的资源(比如沙箱),而是等到真正运行时才初始化。**

好处:

- **启动快**:创建 Agent 对象本身几乎是零开销的(只是组装中间件列表)
- **按需分配**:用不到的资源不会被占用(比如如果本次请求不涉及沙箱操作,沙箱就不会被创建)
- **错误定位**:初始化失败会发生在运行时而不是组装时,更容易定位到具体请求

代价是:第一次真正用到资源时会有一次初始化延迟。但对 Agent 这种"请求级别"的工作量来说可以接受。

### 为什么 ClarificationMiddleware 必须是最后一个?

因为它的作用是**截获 `ask_clarification` 的工具调用并转为对用户的提问**。如果它不是最后一个,那么:

- `ToolErrorHandlingMiddleware` 可能把 `ask_clarification` 的"特殊调用"当成异常处理了
- `LoopDetectionMiddleware` 可能把连续的澄清请求当成循环
- `TokenUsageMiddleware` 可能漏记澄清带来的 token

放在最后,保证其他中间件已经完成它们的工作,澄清是"最后一步"的干预。

### 为什么某些中间件不在基础链里,而是在 `_build_middlewares` 里加?

看 `_build_middlewares` 的装配逻辑,你会发现一些中间件(Title、Memory、Clarification)不在 `build_lead_runtime_middlewares()` 里,而是在 `_build_middlewares` 里单独加。原因:

- **基础链**:适用于**所有运行模式**(主 Agent 和子代理都有)
- **`_build_middlewares` 额外添加的**:只适用于**主 Agent 的典型场景**(面对用户、有对话、需要标题和记忆)

这种分层让"复用基础、定制顶层"成为可能。

---

## 延伸阅读

- 下一章:[08. Skills](./08-skills.md) —— 技能是另一种"可插拔扩展",和中间件互补
- 相关章节:[01. Agent Loop](./01-agent-loop.md) —— 中间件运行在 Agent Loop 的每个节点上
- 相关章节:[03. Context Engineering](./03-context-engineering.md) —— Context Engineering 的实现 90% 在中间件里
- 相关章节:[05. Sandbox](./05-sandbox.md) —— `SandboxMiddleware` 的生命周期管理
- 外部:Express.js 的中间件文档 —— Web 框架中间件的经典参考
- 外部:FastAPI 的中间件 / Dependency Injection 模型 —— Python 生态里最接近的参考
