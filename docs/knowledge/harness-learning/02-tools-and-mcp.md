# 02. Tools & MCP — 给 Agent 装上"手"

> **一句话**:Tools 是 Agent 对外部世界的"手",MCP 是一套让工具能被任何 LLM 客户端通用接入的"协议"。

---

## 核心问题

我们在 [01-agent-loop](./01-agent-loop.md) 里说过,Agent 能做多步任务是因为它能"调用工具"。但"工具"到底是什么?怎么让一个大模型知道"我可以调用这些工具"?怎么保证不同模型、不同工具之间能互相配合?

具体的痛点:

1. **如何定义一个工具?** 函数名、参数、返回值应该用什么格式告诉模型?
2. **工具和模型怎么解耦?** 换一个模型,工具不用重写。
3. **工具和进程怎么解耦?** 工具可能不在 Agent 进程里(可能在另一台服务器),怎么调用?
4. **工具怎么扩展?** 不改核心代码就能加新工具吗?
5. **工具怎么共享?** 我写的工具能让别人的 Agent 也用上吗?

Harness 在 Tools 这一块的所有设计,本质上都是在回答这五个问题。

---

## 通用概念

### 什么是"工具"?

**工具就是一个带签名的函数,模型可以通过 Tool Call 来调用它。**

一个工具由三部分组成:

1. **名字**(`read_file`)
2. **参数 schema**(`{"path": "string, required"}`)
3. **实现**(一段能执行的代码,或一个能发起网络调用的 stub)

对模型来说,它"看到"的只有前两部分(名字 + schema + 人类可读的描述)。模型决定调用时,它输出:

```json
{
  "name": "read_file",
  "arguments": {"path": "/workspace/data.csv"}
}
```

Harness 收到后,负责把这个调用**路由到真正的实现**并把结果塞回对话。

### 工具的三种来源

一个成熟的 Harness 通常会从三类来源组合出最终的工具列表:

| 来源 | 特点 | 示例 |
| --- | --- | --- |
| **Builtin(内置)** | 硬编码在 Harness 里,最快最可靠,覆盖通用需求 | `read_file`、`bash`、`ask_clarification` |
| **MCP**(Model Context Protocol) | 通过标准协议接入的外部工具服务,可以动态发现 | 数据库查询服务、企业知识库、Web 搜索 API |
| **Community / Plugin(社区)** | 以插件形式集成的第三方库 | Tavily 搜索、Jina 爬虫、Firecrawl |

一个好的 Harness 会让这三类工具**在调用方(模型)视角下完全一致** —— 模型不知道也不需要知道一个工具是 builtin 还是 MCP,只管按 schema 调用。

### MCP 是什么?

**MCP(Model Context Protocol)** 是 Anthropic 在 2024 年底提出的一个开放协议,目的是**让工具(和数据源)以统一的方式暴露给任何 LLM 客户端**。

你可以把它想象成"工具领域的 HTTP":

- 一个 **MCP Server** 声明"我提供这些工具、这些资源、这些 prompt 模板"
- 一个 **MCP Client**(比如 Claude Desktop、Cursor、DeerFlow)可以连接任何 MCP Server 并把它暴露的工具加入自己的工具列表
- 协议本身是基于 JSON-RPC 的,有 stdio 和 SSE 两种传输方式

**为什么这很重要?** 因为在 MCP 之前,每个 Agent 框架都有自己定义工具的方式。你给 LangChain 写的工具,不能直接在 Claude Desktop 里用。MCP 打破了这个隔阂。现在**写一次工具,就能被所有支持 MCP 的 Agent 调用** —— 就像写一个 REST API,任何支持 HTTP 的客户端都能调用一样。

### 延迟加载(Deferred Tools)

当工具数量很多时(一个生产级 Harness 可能有几十上百个工具),一次性把所有 schema 塞进 prompt 会有两个问题:

1. **Token 消耗大**:每一轮都要把几千 token 的工具清单传给模型
2. **模型选错概率高**:选项越多,模型越容易混淆

一个常见的优化是 **"延迟加载"**:

1. 一开始只给模型一个"元工具",比如 `tool_search("搜索能做 X 的工具")`
2. 模型先调这个元工具,Harness 返回"匹配的工具列表 + 它们的 schema"
3. 然后下一轮,模型才真正调用那些工具

这样做的代价是多一次工具调用,但在工具很多的场景下,省下的 token 和提升的准确率远大于开销。

---

## DeerFlow 的实现

DeerFlow 的工具系统严格按照上面说的"三个来源 + 统一注册入口"设计。

### 入口:`get_available_tools()`

- `backend/packages/harness/deerflow/tools/tools.py` — **核心注册函数 `get_available_tools()`**。这个函数根据运行时配置,从 builtin、MCP、community 三处收集工具,合并成一个列表交给 `make_lead_agent()`。在 `agent.py` 里你能看到 `tools=get_available_tools(model_name=..., groups=..., subagent_enabled=...)` 这样的调用。

### Builtin 工具

- `backend/packages/harness/deerflow/tools/builtins/` — 内置工具目录:
  - `task_tool.py` — **`task()` 工具**,用来委派子代理(这是 "super agent" 的关键)
  - `clarification_tool.py` — `ask_clarification()`,主动让 Agent 询问用户
  - `present_file_tool.py` — `present_file()`,向用户展示一个文件(图片、文档等)
  - `view_image_tool.py` — 让 Agent 能"看到"图片(配合视觉模型)
  - `invoke_acp_agent_tool.py` — 调用外部 ACP Agent(Codex、Claude Code 等)
  - `setup_agent_tool.py` — 在 bootstrap 模式下用来创建自定义 Agent
  - `tool_search.py` — **延迟加载的元工具**(对应前面讲的 Deferred Tools)

此外,沙箱提供的文件/命令工具在另一个位置:
- `backend/packages/harness/deerflow/sandbox/tools.py` — 沙箱工具,包括 `bash`、`ls`、`read`、`write`、`str_replace` 等。这些工具需要先有沙箱才能用,所以由 `SandboxMiddleware` 管理生命周期。

### MCP 集成

- `backend/packages/harness/deerflow/mcp/client.py` — **MCP 客户端**,负责与外部 MCP Server 建立连接(支持 stdio 和 SSE 两种传输方式)
- `backend/packages/harness/deerflow/mcp/tools.py` — 把 MCP Server 声明的工具"翻译"成 LangChain 工具的适配层
- `backend/packages/harness/deerflow/mcp/cache.py` — 工具缓存。MCP Server 的工具清单不变时,避免每次请求都重新发现
- `backend/packages/harness/deerflow/mcp/oauth.py` — OAuth 认证支持,用于需要用户授权的 MCP Server

MCP Server 的配置不在代码里,而在项目根目录的 `extensions_config.json`(或 `extensions_config.example.json` 看示例)—— 这保证了"加新 MCP 工具不用改代码"。

### Community 工具

- `backend/packages/harness/deerflow/community/` — 社区/第三方工具集成:
  - `tavily/` — Tavily 搜索 API
  - `jina_ai/` — Jina AI 爬虫
  - `firecrawl/` — Firecrawl 网页抓取
  - `exa/` — Exa 搜索
  - `ddg_search/` — DuckDuckGo 搜索
  - `image_search/` — 图像搜索
  - `infoquest/` — InfoQuest(字节的搜索 / 爬虫工具集)
  - `aio_sandbox/` — AIO Sandbox 集成

这些工具每个都是一个独立的模块,可以单独 import、单独禁用。

### 延迟加载相关

- `backend/packages/harness/deerflow/tools/builtins/tool_search.py` — `tool_search` 元工具的实现
- `backend/packages/harness/deerflow/config/tool_search_config.py` — 配置开关
- `backend/packages/harness/deerflow/agents/middlewares/deferred_tool_filter_middleware.py` — 一个中间件,当延迟加载启用时,**从模型能看到的工具 schema 里把延迟工具隐藏掉**(只保留 `tool_search`)

---

## 设计权衡

### 为什么要把工具分成三层?

一个扁平的工具注册表也能工作,但 DeerFlow 的三层设计有几个好处:

1. **生命周期不同**:Builtin 工具随进程启动,MCP 工具是动态连接,community 工具按需 import。混在一起管理会很乱。
2. **可靠性不同**:Builtin 最可靠(直接函数调用),MCP 可能断连,community 可能失败。错误处理策略不同。
3. **权限边界不同**:Builtin 工具是"可信的",community 工具可能有风险(比如 `bash` 和 "一个第三方 HTTP 调用" 显然风险级别不一样),需要不同的护栏策略。

### 为什么要有 `ask_clarification` 这种"反向工具"?

大多数工具是"Agent 对外界说话"。而 `ask_clarification` 是**"Agent 对用户说话"**。这是一个容易被新手忽略但极其重要的设计:

> **好的 Agent 会在不确定时主动问用户,而不是硬猜。**

但如果你不给它一个"问用户"的工具,它就只能硬猜 —— 因为在工具调用范式里,"产生文本给用户看"和"调用工具"是两种不同的动作。`ask_clarification` 把"问用户"显式地变成一个"工具",让 Agent 能在思考链里主动选择它。

DeerFlow 还有一个专门的 `ClarificationMiddleware`(始终是中间件链的最后一个),用来截获这个工具的调用并把它转化成对用户的提问。

### 为什么要有 `task_tool`(子代理工具)?

见 [06-subagents](./06-subagents.md)。简单说:**让 Agent 能递归调用自己**,把复杂任务拆给子代理去做,从而突破单 Agent 的上下文窗口限制。

### MCP vs 自定义插件机制,DeerFlow 为什么两个都支持?

理论上只用 MCP 就够了,但实际上:

1. **MCP 还在早期**,有些能力(比如高性能并发工具)还没覆盖
2. **现有社区工具**大多数是 Python 库,包装成 MCP Server 有成本
3. **Community 模块**可以用 Python 原生性能,不走 JSON-RPC 的开销

所以 DeerFlow 的策略是**"MCP 优先,community 补充"**:新工具尽量用 MCP,性能敏感或生态不完备的场景用 community 模块。

---

## 延伸阅读

- 下一章:[03. Context Engineering](./03-context-engineering.md) —— 工具 schema 怎么塞进 prompt,又怎么在上下文紧张时压缩
- 相关章节:[06. Sub-agents](./06-subagents.md) —— `task_tool` 的详细讨论
- 相关章节:[05. Sandbox](./05-sandbox.md) —— 沙箱工具(`bash`、文件 IO)的专门管理
- 外部:[Model Context Protocol 官方文档](https://modelcontextprotocol.io/)
- 外部:OpenAI Function Calling 文档(如果你想理解 Tool Calling 的底层 API)
