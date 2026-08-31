# context.md — 个人上下文规范

> 本文档是 AiPalace 个人上下文（context）的规范性说明，定义"是什么"与"怎么遵循"。  
> 最高准绳：[`PHILOSOPHY.md`](../../../PHILOSOPHY.md)（P1–P9）。

> ⚠️ **过渡态说明（ADR-0013，2026-06-30）**：`context/self/`（身份/技术栈/工作方式画像）已迁移至 `vault/memory/00-RULES/`；`context/memory/`（五域知识库）已迁移至 `vault/memory/01-PROJECTS/`。当前 SOT 为 **`vault/memory/`**，SessionStart hook 注入路径已改为 `vault/memory/INDEX.md`。本文档保留历史规范说明（第 3–8 章描述的 `context/self/` 与 `context/memory/` 结构供参考），新内容请维护至 vault；详见 [`vault.md`](vault.md) 规范。

---

## 1. 定位

**context** 是 AiPalace 管理的可选个人上下文——关于**"我"**的画像：身份、技术栈偏好、工作方式、环境偏好。内容偏稳定，几乎任何任务都可能参考一眼。

context 是**内容资产**（见 [P7](../../../PHILOSOPHY.md#p7--内容统一源机制分治)）：其内容工具无关，统一存放于本仓库；注入机制（SessionStart hook）按工具分治，详见 [`product-assets/injection.md`](../product-assets/injection.md)（见 [P2](../../../PHILOSOPHY.md#p2--声明式管理工具派生限内容资产)）。

---

## 2. context vs memory：边界

context 与 memory 同为内容资产，均通过 INDEX 触发，但**内容域完全不同**：

| 维度 | context（关于"我"） | memory（关于"事"） |
|------|--------------------|------------------|
| **本质** | 个人画像：身份、偏好、工作方式 | 知识库：项目、技术、工作流、参考资料 |
| **内容性质** | 偏稳定，几乎任何任务都可能参考 | 随沉淀增长，按需精细取用 |
| **注入方式** | 软注：模型据任务自选是否展开 what | 渐进 pull：按触发三门决定取哪个条目 |
| **INDEX** | `context/INDEX.md`（决策树 when→what） | `memory/INDEX.md`（同构决策树 when→what） |
| **内容归类** | 维度拆分：identity / tech-stack / workflow-style / env-preference | 域→主题→条目：projects / tech / workflow / reference / enterprise |

> 判断原则：**"这是关于我自己的背景偏好吗？"** → 是，放 context；**"这是关于某个项目/技术/工作流的事实记录吗？"** → 是，放 memory。

---

## 3. 目录结构

```
context/
├─ INDEX.md             ← always-on 注入：决策树，约束 when → what
├─ identity.md          ← 身份：角色、目标、人称偏好
├─ tech-stack.md        ← 技术栈：语言/框架偏好、工具链
├─ workflow-style.md    ← 工作方式：节奏、习惯、协作偏好
└─ env-preference.md    ← 环境偏好：系统、编辑器、终端配置
```

- `INDEX.md`：always-on 注入（轻），是模型导航 context 的唯一入口。
- `<what>.md`：按"我"的维度拆分，模型按 INDEX 的 when 条件自选加载，**不强制全量注入**。

> 维度列表开放，可随个人画像的演进新增 `<what>.md`；变更须同步更新 `INDEX.md` 的决策树。

---

## 4. `context/INDEX.md` 格式规范

`context/INDEX.md` 是 context 体系的**声明源**（体现 [P2](../../../PHILOSOPHY.md#p2--声明式管理工具派生限内容资产)）。格式：多级决策树，每个叶节点给出 `when`（何时相关）与 `what`（指向哪个 md）。

```markdown
# context/INDEX.md — 个人上下文导航

always-on：本文件注入后，模型按以下决策树自选展开。

## 何时看哪个 context

- **任何任务** → 可参考 [identity.md](identity.md)
- **涉及代码/技术选型** → 参考 [tech-stack.md](tech-stack.md)
- **涉及任务拆解/工作节奏** → 参考 [workflow-style.md](workflow-style.md)
- **涉及环境配置/工具链** → 参考 [env-preference.md](env-preference.md)
```

**约束：**

1. `when` 条件尽量正交，不同条目覆盖不同维度的判断。
2. `what` 路径相对于 `context/` 目录，使用 markdown 链接。
3. INDEX 本身不含实质性内容——内容在各 `<what>.md` 中，INDEX 只做导航。
4. 每次新增/删除 `<what>.md`，INDEX 必须同步更新。

---

## 5. 注入哲学（软注）

context 采用**软注（soft injection）**——不强制加载所有维度：

- `INDEX.md` always-on 注入（SESSION start 时注入，代价低）。
- 模型据当前任务的 `when` 条件**自行判断**是否 Read 对应的 `<what>.md`。
- **不要求每次任务都展开全部 context**；如果任务与某维度无关，可以跳过。

软注的意义：避免 token 浪费，同时保持"我的画像随时可及"的可用性（体现 [P4](../../../PHILOSOPHY.md#p4--分级控预算tier) 精神）。

注入机制的实现细节（SessionStart hook 配置、双工具同逻辑、与 memory/INDEX 的合并注入优化）下沉至 [`product-assets/injection.md`](../product-assets/injection.md)，本文档不重复。

---

## 6. 内容维护原则

1. **维度拆分，按需填写**：新维度随个人画像演进按需增加；不强制填满所有文件（体现浅填精神）。
2. **稳定优先**：context 内容偏稳定；频繁变化的事实（如项目进展）属 memory，不放 context。
3. **工具无关**：各 `<what>.md` 不含工具专有语法，确保跨工具复用（体现 [P7](../../../PHILOSOPHY.md#p7--内容统一源机制分治)）。
4. **来源标注**：context 内容均为本人自建（class = mine），无需 `_SOURCE.md`，但可在文件末尾注明"最后更新"日期。

---

## 7. 纳入新 context 维度的要求

新增 `<what>.md` 须满足：

1. **属于"关于我"的画像范畴**：身份/偏好/习惯/环境，而非事实记录（后者放 memory）。
2. **有清晰的维度边界**：与现有维度不重叠，有独立的 `when` 触发场景。
3. **INDEX 同步更新**：新文件必须在 `INDEX.md` 的决策树中添加对应的 when→what 条目。
4. **工具无关**：文件内容不含工具专有语法。

---

## 8. 溯源与演进

- context 内容变更须通过 git 追溯（体现 [P8](../../../PHILOSOPHY.md#p8--决策留痕诚实标注)）。
- 影响注入机制的变更须在 `product-assets/injection.md` 同步更新。
- 已知不一致或过渡状态须显式标注（体现 [P9](../../../PHILOSOPHY.md#p9--显式过渡态)）。

---

## 9. `context/howto/` —— 指令文件的按需子文档

`context/howto/` 存放被 `CLAUDE.md` / `AGENTS.md` 等 always-on 指令文件「索引指向、按需动态加载」的操作细则（how-to）。与 `self/`（关于我）、`memory/`（关于事）并列，同属 context 层的**渐进披露**内容，但**触发入口不同**——由**指令文件中的指针**触发 `Read`，而非 `context/INDEX` 决策树。

- **边界**：howto/ 是"操作手册"（某能力**怎么用**），既非"关于我"的画像（self/），也非事实记录（memory/）。
- **维护约定**：[`context/howto/instruction-file-maintenance.md`](../../../context/howto/instruction-file-maintenance.md) —— 指令文件主体只留 when + 约束 + 指针，how-to 细节移入本目录（[ADR-0009](../../../adr/0009-指令文件渐进披露与howto子文档.md)）。
- 现有条目见 [`context/howto/README.md`](../../../context/howto/README.md)。

---

*本规范依据 spec §6/§6b（`2026-06-18-aipalace治理与设计哲学-design.md`）成文；§9 howto/ 由 ADR-0009 补充。*
