# 04. Memory — 让 Agent 拥有"短期"和"长期"记忆

> **一句话**:短期记忆让 Agent "记得这次对话",长期记忆让它"跨会话地记得你"。前者靠状态对象,后者靠异步抽取 + Prompt 注入。

---

## 核心问题

一个朴素的问题:**LLM 本身有没有记忆?**

答案是:**没有**。每次 API 调用对 LLM 来说都是独立的,它"看到"的全部信息就是这次请求里给它的消息列表。上一次请求里你告诉它"我叫 Alice",下一次请求如果不再把这条消息传进去,它就不知道。

但一个好的 Agent 应该:

1. **记得这次对话里发生的所有事** —— 三分钟前你说了什么、它调用过什么工具
2. **记得你是谁、你喜欢什么** —— 哪怕是三天前、三个月前跟它说的
3. **不要在每次请求里重新问你一遍**
4. **但也别把一切都记下来,那会爆上下文 / 侵犯隐私**

这些都得 Harness 来做。

---

## 通用概念

### 短期记忆 vs 长期记忆

这是一个关键区分:

| 类型 | 持续时间 | 存储在哪 | 典型内容 |
| --- | --- | --- | --- |
| **短期记忆**(Working Memory) | 当前会话内 | Agent 的 `State` 对象(内存 / 检查点) | 所有消息、tool call、当前 todo |
| **长期记忆**(Long-term Memory) | 跨会话,持久化 | 数据库 / 文件系统 / 向量库 | 用户偏好、事实(user: Alice)、重要决策 |

短期记忆的本质就是**对话历史本身**。只要这次对话没结束,Agent 的 State 里就保留着所有消息,下一轮请求会带上它们。当对话太长时,Context Engineering(上一章)负责压缩或截断。

长期记忆就复杂了 —— 它需要一个"写入策略"和一个"读取策略"。

### 长期记忆的两个核心问题

1. **写:什么时候、怎么决定"这条信息值得记下来"?**
2. **读:下次对话开始时,怎么决定"这次要用到哪些记忆"?**

#### 写入策略

主流有三种:

- **用户主动写入**:用户说"记住我住在北京",Agent 调用一个 `save_memory` 工具。简单但完全依赖用户主动性。
- **LLM 自动抽取**:对话结束后(或达到某个点),后台用一个 LLM 扫一遍对话,抽出"值得记下来的事实"并存进库。DeerFlow 走的就是这条路。
- **向量化全量存储**:每一条消息都向量化存进向量库,查询时按相似度检索。覆盖全但噪声大、成本高。

LLM 自动抽取的关键点:

- **异步进行**:不能阻塞用户的下一次请求
- **结构化输出**:抽取出的"事实"应该有一致格式(比如 `{"category": "user_preference", "fact": "lives in Beijing", "confidence": 0.9}`)
- **去重 / 更新**:已存在的事实不要重复存;有冲突的新事实(比如用户搬家了)要覆盖旧的

#### 读取策略

对应的读取策略:

- **检索式**:查询向量库,按相似度找回 top-k
- **全量注入**:把所有事实塞进 System Prompt(只有当事实数量很小时可行)
- **分类注入**:按"类别 + confidence"选一部分塞进去
- **混合**:静态常用的(用户姓名、工作目录)直接注入,临时相关的通过检索

对初学者来说,理解"**长期记忆本质上就是在 System Prompt 里多塞几行事实**"就够了。所有复杂的 embedding、向量检索、rerank 都是围绕"这几行该塞什么"展开的优化。

### 记忆和隐私

一个经常被忽略的点:**记忆是有隐私含义的**。如果你的 Agent 自动记下了"用户说自己 HIV 阳性"并且跨会话使用,这是严重的隐私事件。

一个成熟的 Harness 应该:

- 让用户能**查看**记忆里存了什么
- 让用户能**删除**特定记忆
- 对敏感类别(健康、金钱、政治)**默认不抽取**
- 有**审计日志**,记录每次读取 / 写入

DeerFlow 没有把隐私做成一等公民(开源社区版本),但结构上是可扩展的。

---

## DeerFlow 的实现

DeerFlow 的记忆系统是**"短期靠 ThreadState,长期靠异步抽取 + Prompt 注入"**的组合。

### 短期记忆:ThreadState

- `backend/packages/harness/deerflow/agents/thread_state.py` — **`ThreadState` Schema**。定义了一次会话的所有状态字段,包括消息历史、todos、沙箱句柄等。这是 LangGraph 图的 state 对象。

每当 Agent 跑一轮,LangGraph 会把更新后的 `ThreadState` 持久化(通过 checkpointer),下一次用户发消息时从 checkpoint 恢复 —— 这就是"短期记忆"的全部实现。

- `backend/packages/harness/deerflow/agents/checkpointer/` — LangGraph checkpoint 适配(支持内存、SQLite、Postgres 等多种后端)
- `backend/packages/harness/deerflow/config/checkpointer_config.py` — checkpointer 的配置

### 长期记忆:自动抽取事实

这是 DeerFlow 记忆系统的核心,分成**抽取、存储、注入**三个环节。

#### 抽取(Updater)

- `backend/packages/harness/deerflow/agents/memory/updater.py` — **记忆更新器**。在对话达到某个触发点时,启动一个后台任务,调用 LLM 扫一遍最近的消息,抽取出值得记录的事实。
- `backend/packages/harness/deerflow/agents/memory/prompt.py` — 抽取时用的提示词模板(告诉 LLM "请从这段对话里抽取出用户的偏好和事实")

#### 队列(Queue)

- `backend/packages/harness/deerflow/agents/memory/queue.py` — **异步更新队列**。抽取动作不阻塞用户请求,而是把"需要更新记忆"的信号放到队列里,由后台 worker 处理。

#### 存储(Storage)

- `backend/packages/harness/deerflow/agents/memory/storage.py` — **事实持久化**。DeerFlow 把记忆存成 JSON 文件(或数据库),支持 **mtime-based 缓存失效**(根据文件修改时间判断是否需要重新加载)

#### 注入(MemoryMiddleware)

- `backend/packages/harness/deerflow/agents/middlewares/memory_middleware.py` — **记忆注入中间件**。在每一轮调用模型之前,从存储里读出最相关的事实,插入到 System Prompt。

在 `agent.py` 的 `_build_middlewares()` 里你会看到:

```python
middlewares.append(MemoryMiddleware(agent_name=agent_name))
```

注意 `agent_name` 参数 —— 这说明**每个 Agent 可以有自己独立的记忆空间**。主 Agent 和子代理不会混淆记忆。

### 配置

- `backend/packages/harness/deerflow/config/memory_config.py` — 记忆系统的配置:开关、抽取触发条件、存储路径等

---

## 设计权衡

### 为什么抽取要异步?

如果抽取是同步的 —— 每一轮对话结束后立刻调一次 LLM 抽取记忆 —— 会发生两个问题:

1. **用户请求被阻塞**。用户发消息 → Agent 回复 → 抽取(+几秒)→ 才能接受下一次消息。
2. **短对话的抽取是浪费**。用户发一句"你好",完全没必要抽取记忆。

异步化解决这两个问题。代价是:记忆更新有延迟 —— 如果用户在短时间内发送两次消息,第二次可能看不到第一次的抽取结果。但对大多数场景这没关系。

### 为什么 Memory 不用向量库,而用 JSON 文件?

这是 DeerFlow 最反直觉的选择之一。主流 Agent 框架(MemGPT、LangMem、Zep)大多用向量库做长期记忆。DeerFlow 却用 JSON 文件。理由:

1. **事实数量通常不大**。一个用户的长期事实可能就几十到几百条,完全可以全量加载进 prompt,不需要检索。
2. **可解释性强**。JSON 文件可以直接打开看,用户也能理解"Agent 记住了我什么"。
3. **部署简单**。不需要额外运行向量数据库。
4. **`mtime` 足够用**。文件的修改时间就是现成的版本号,不需要复杂的缓存失效逻辑。

代价是:**规模上去后(成千上万条事实)会扛不住**。对那种场景,DeerFlow 预留了"storage 模块可替换"的扩展点 —— 你可以写一个基于向量库的 `storage.py` 替换掉默认的 JSON 实现。

### 为什么 Memory Middleware 放在 TitleMiddleware 之后?

在 `agent.py` 的注释里你能看到:

```python
# MemoryMiddleware queues conversation for memory update (after TitleMiddleware)
```

理由:`TitleMiddleware` 是在首轮对话后生成标题,这个动作是"同步"的(需要立即返回一个标题给前端)。如果 `MemoryMiddleware` 放在它前面,记忆抽取任务可能会抢占 TitleMiddleware 的模型调用资源。放在后面保证"用户可见的动作"优先完成,"后台动作"随后发起。

这种**"可见优先级 > 后台优先级"**的排序思路是 Harness 工程的常见权衡。

### 为什么每个 Agent 有独立的记忆?

DeerFlow 的主 Agent 和子代理是**独立记忆空间**的。好处:

1. **隔离**:子代理处理的是一个狭窄任务,没必要看到主 Agent 的全部历史事实
2. **聚焦**:子代理的记忆可以针对其任务领域(比如一个"翻译子代理"记的是术语表,一个"搜索子代理"记的是用户偏好的信息源)
3. **安全**:敏感记忆可以只给主 Agent,不向子代理暴露

代价是:跨 Agent 共享的事实要重复存储。DeerFlow 的取舍是**隔离优先**。

---

## 延伸阅读

- 下一章:[05. Sandbox](./05-sandbox.md) —— 让 Agent 的动作有"隔离的执行环境"
- 相关章节:[03. Context Engineering](./03-context-engineering.md) —— 记忆注入也是 Context Engineering 的一部分
- 相关章节:[01. Agent Loop](./01-agent-loop.md) —— `ThreadState` 在 Agent Loop 中的角色
- 外部:[MemGPT: Towards LLMs as Operating Systems](https://arxiv.org/abs/2310.08560) —— 一个影响力很大的长期记忆论文
- 外部:LangMem 项目 —— 另一个长期记忆的实现思路
