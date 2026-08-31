# Agent Harness 学习索引 — 以 DeerFlow 2.0 为案例

> 本目录是一份面向**初学者**的 Agent Harness(智能体脚手架)学习手册。
> 我们以字节跳动开源的 [`bytedance/deer-flow`](https://github.com/bytedance/deer-flow) 2.0 版本作为案例,
> 因为它在 README 中直接自称为 *"open-source super agent harness"*,
> 而其核心 Python 包的名字就叫 **`deerflow-harness`**,是学习 Harness 概念最直接的"标本"。

---

## 什么是 Agent Harness?(一句话版本)

**Harness(脚手架/挽具)= 包在大模型外面的那一整套基础设施:工具、记忆、沙箱、子代理、上下文、中间件……让一个只会"根据对话历史生成下一段文字"的 LLM,变成一个能"在真实世界里完成多步任务"的 Agent。**

如果你只用 `openai.chat.completions.create(...)` 调用一次大模型,那是**裸 LLM**。
在裸 LLM 外面加上"工具调用循环 + 记忆 + 沙箱 + 子代理 + 安全护栏 + 可观测"这一整圈组件,你得到的就是 **Agent Harness**。

可以打个类比:

| 裸 LLM | Agent Harness |
| --- | --- |
| 大脑(只会思考) | 大脑 + 身体 + 感官 + 记忆 + 工具箱 |
| 一问一答 | 多轮循环,边做边调整 |
| 无状态 | 有短期 + 长期记忆 |
| 无副作用 | 能读写文件、执行命令、调用 API |
| 无安全边界 | 有沙箱、权限、护栏 |

---

## 学习脑图(Mind Map)

```
Agent Harness
│
├── 00. 为什么需要 Harness?
│     └── 裸 LLM 的五大局限:无记忆、无工具、无状态、无隔离、无组合
│
├── 01. Agent Loop(智能体循环)
│     ├── ReAct 范式:Think → Act → Observe → Repeat
│     ├── Tool Calling(工具调用)
│     ├── 状态机:LangGraph 与 ThreadState
│     ├── 流式输出与可中断
│     └── 系统提示词(System Prompt)
│
├── 02. Tools & MCP(工具系统)
│     ├── Builtin Tools(内置工具)
│     ├── MCP 协议(Model Context Protocol)
│     ├── Community Tools(社区工具)
│     └── Deferred Tools(延迟加载工具)
│
├── 03. Context Engineering(上下文工程)
│     ├── System Prompt 模板化
│     ├── Summarization(上下文压缩)
│     ├── Dangling Tool Call 修复
│     ├── Uploads 注入
│     └── 视觉模型的图像注入
│
├── 04. Memory(记忆系统)
│     ├── 短期记忆:ThreadState
│     ├── 长期记忆:自动抽取的事实(Facts)
│     ├── 异步更新队列
│     └── 记忆注入到 System Prompt
│
├── 05. Sandbox(沙箱执行环境)
│     ├── 为什么需要沙箱?副作用隔离
│     ├── Sandbox 抽象接口
│     ├── Provider 模式:Local / Aio / Kubernetes
│     ├── 虚拟路径翻译(Virtual Path Translation)
│     └── 文件操作锁
│
├── 06. Sub-Agents(子代理 / 分层委派)
│     ├── 为什么需要子代理?任务分解
│     ├── task() 工具
│     ├── 并发上限与超时
│     └── Registry 与 Builtin 子代理
│
├── 07. Middleware Pipeline(中间件管道)
│     ├── 中间件模式:横切关注点(cross-cutting concerns)
│     ├── 15 个中间件一览表
│     ├── 顺序依赖关系
│     └── 静态 vs 动态中间件
│
├── 08. Skills(技能系统)
│     ├── 什么是 Skill?渐进披露(Progressive Disclosure)
│     ├── SKILL.md 约定
│     ├── 发现、加载、安装
│     └── 安全扫描
│
└── 09. 设计模式与权衡(综合)
      ├── 分层边界:deerflow.* 与 app.* 的单向依赖
      ├── 中间件组合 vs 单体逻辑
      ├── Provider 抽象
      ├── 配置驱动装配
      ├── Per-thread 隔离
      └── Lazy 初始化
```

---

## 推荐阅读路径

### 🌱 路径 A:零基础完整学习(推荐)

按编号顺序一章一章读,每章都独立自包含,预计每章 10-15 分钟。

```
00 → 01 → 07 → 02 → 03 → 04 → 05 → 06 → 08 → 09
         ↑
    先看中间件,
    后面 02/03 才能理解它们是怎么"接进去"的
```

### 🚀 路径 B:已经用过 LLM / 写过简单 Agent

直接从 01 开始,重点看 07(中间件)和 09(综合),这两章是 Harness 设计哲学的浓缩。

```
01 → 07 → 05 → 06 → 09
```

### 🎯 路径 C:只想了解某一个概念

跳到对应章节即可,每章独立阅读。

---

## 概念速查表

| 概念 | 文件 | 一句话说明 |
| --- | --- | --- |
| Harness(脚手架) | [00](./00-what-is-a-harness.md) | 包在 LLM 外面的基础设施总和 |
| Agent Loop(智能体循环) | [01](./01-agent-loop.md) | Think-Act-Observe 的反复执行 |
| Tool(工具) | [02](./02-tools-and-mcp.md) | Agent 对外部世界的"手" |
| MCP | [02](./02-tools-and-mcp.md) | Model Context Protocol,标准化工具接口 |
| Context Engineering | [03](./03-context-engineering.md) | 决定每一轮给 LLM 看什么 |
| Summarization | [03](./03-context-engineering.md) | 上下文接近上限时的压缩 |
| Short-term Memory | [04](./04-memory.md) | 单次会话内的状态(ThreadState) |
| Long-term Memory | [04](./04-memory.md) | 跨会话的事实(Facts)存储 |
| Sandbox(沙箱) | [05](./05-sandbox.md) | 隔离 Agent 的副作用 |
| Virtual Path | [05](./05-sandbox.md) | 虚拟路径到物理路径的翻译 |
| Sub-agent(子代理) | [06](./06-subagents.md) | 把任务拆给另一个 Agent 做 |
| Middleware(中间件) | [07](./07-middleware.md) | 横切关注点的组合模式 |
| Skill(技能) | [08](./08-skills.md) | 可插拔的工作流单元 |
| ReAct | [01](./01-agent-loop.md) | Reason + Act 的交替范式 |
| ThreadState | [01](./01-agent-loop.md), [04](./04-memory.md) | LangGraph 里的会话状态 Schema |
| Guardrail(护栏) | [07](./07-middleware.md) | 策略层的安全检查 |

---

## 名词表(Glossary)

- **Agent(智能体)** — 能根据目标自主选择下一步行动的 LLM 程序。与"聊天机器人"的区别是它会调用工具、会循环。
- **Harness(脚手架)** — 支持 Agent 运行的所有"非 LLM"基础设施。本文档的主题。
- **LLM(大语言模型)** — 比如 GPT-4、Claude、DeepSeek。是 Agent 的"大脑",但本身无状态、无工具。
- **Tool(工具)** — Agent 可以调用的函数,由 Harness 注册。例如 `read_file`、`bash`、`web_search`。
- **Tool Call(工具调用)** — 模型在生成文本时输出一个"请调用 X 工具、参数是 Y"的结构化消息,Harness 执行后把结果塞回对话。
- **ReAct** — "Reason + Act"范式的缩写:模型先推理、再行动、观察结果、再推理,循环直到任务完成。
- **Thread(线程 / 会话)** — 一次独立的对话上下文。DeerFlow 里每个 Thread 有自己的工作目录和沙箱。
- **ThreadState** — LangGraph 中会话状态的 Schema,保存 messages、todo、内部标志等。
- **Middleware(中间件)** — 在"模型调用前/后"、"工具调用前/后"插入的横切逻辑。例如日志、速率限制、错误处理。
- **Sandbox(沙箱)** — 一个受控的执行环境,隔离 Agent 对主机的副作用。Local、Docker、K8s 都是常见实现。
- **Sub-agent(子代理)** — 主 Agent 委派出去的一个独立 Agent 实例,通常用来处理子任务(例如"研究这个话题后给我一个总结")。
- **Skill(技能)** — 一个以 `SKILL.md` 为入口的工作流包,包含说明、步骤、工具清单。运行时按需加载。
- **MCP(Model Context Protocol)** — Anthropic 提出的一个标准,让工具/数据源以统一协议暴露给 LLM 客户端。
- **Context Window(上下文窗口)** — 一次请求能塞给 LLM 的最大 token 数,例如 128k。超过就得压缩或截断。
- **System Prompt(系统提示词)** — 放在对话最前面的、告诉模型"你是谁、应该怎么做"的指令。

---

## DeerFlow 源码地图(学习时对照查看)

所有核心 Harness 组件都在 `backend/packages/harness/deerflow/` 下:

```
deerflow/
├── agents/
│   ├── lead_agent/          主 Agent 的工厂与提示词 (make_lead_agent 在这里)
│   │   ├── agent.py         组装 model + tools + middleware + prompt
│   │   └── prompt.py        系统提示词模板
│   ├── middlewares/         15 个中间件(核心看点!)
│   ├── memory/              长期记忆:storage/queue/updater/prompt
│   ├── checkpointer/        LangGraph checkpoint 适配
│   └── thread_state.py      ThreadState Schema
│
├── sandbox/                 沙箱系统
│   ├── sandbox.py           抽象接口
│   ├── sandbox_provider.py  Provider 接口(Local/Aio/K8s 都实现它)
│   ├── middleware.py        SandboxMiddleware:生命周期管理
│   ├── tools.py             bash/ls/read/write/str_replace 工具
│   ├── security.py          路径与命令安全检查
│   ├── file_operation_lock.py  并发文件操作锁
│   └── local/               Local Provider(文件系统)
│
├── subagents/               子代理系统
│   ├── executor.py          后台线程池执行器
│   ├── registry.py          Agent 注册表
│   ├── config.py            配置
│   └── builtins/            内置子代理(general-purpose、bash 等)
│
├── tools/                   工具注册入口
│   ├── tools.py             get_available_tools() 工厂
│   ├── builtins/            内置工具(task_tool、present_file 等)
│   └── skill_manage_tool.py 技能管理工具
│
├── mcp/                     MCP 集成
│   ├── client.py            MCP 客户端
│   ├── tools.py             MCP → LangChain 工具适配
│   ├── cache.py             工具缓存
│   └── oauth.py             OAuth 认证
│
├── skills/                  技能系统
│   ├── manager.py           技能生命周期管理
│   ├── loader.py            加载 SKILL.md
│   ├── parser.py            解析 Frontmatter
│   ├── installer.py         安装/卸载
│   ├── security_scanner.py  安全扫描(恶意技能检测)
│   ├── validation.py        验证
│   └── types.py             类型定义
│
├── models/                  模型抽象(OpenAI/Anthropic/vLLM 等统一接口)
├── config/                  配置系统(20+ 个子配置模块)
├── guardrails/              护栏 / 策略层
├── runtime/                 Gateway 模式下的 Agent 运行时(进阶)
├── tracing/                 LangSmith / Langfuse 追踪
├── reflection/              反射(按字符串解析类)
├── community/               社区工具(Tavily、Jina、Firecrawl 等)
└── uploads/                 上传文件管理
```

> 💡 **小贴士**:读到各章节的"DeerFlow 实现"部分时,用上面这张地图对照查找路径,比直接 `grep` 快。

---

## 文档范围说明

本文档 **只覆盖 Harness 核心概念**,下列内容不在范围内(读者如果感兴趣可以另外去看 DeerFlow 的 README):

- Gateway REST API(`backend/app/gateway/`)
- Next.js 前端(`frontend/`)
- IM 平台集成(飞书 / Slack / Telegram)
- Docker / Kubernetes 部署细节
- LangGraph 内部实现细节(我们只用到它的"外部接口")

---

## 使用建议

1. **先读 [00-what-is-a-harness](./00-what-is-a-harness.md)**,建立整体概念。
2. 每章末尾都有 **"设计权衡"** 一节,这是学 Harness 最值钱的部分 —— 你会看到同一个问题的不同解法以及 DeerFlow 选择的理由。
3. "DeerFlow 的实现"一节只给**文件路径 + 一句话说明**。想深入的话,打开对应文件直接读源码(DeerFlow 代码质量很高,非常适合精读)。
4. 读完 [09-patterns-and-tradeoffs](./09-patterns-and-tradeoffs.md) 之后,你应该能自己画出一个 Harness 的架构图,并解释每个组件的作用。

---

## 关于本文档

- **基于版本**:DeerFlow 2.0(主干,截至 2026-04-10)
- **来源**:项目 README + `backend/CLAUDE.md` + DeepWiki 总结 + 源码直读
- **面向读者**:对 LLM Agent 不熟悉、想建立完整心智模型的工程师
- **非目标**:不是 DeerFlow 的用户手册;DeerFlow 只是我们的"教学标本"

祝学习顺利 🦌
