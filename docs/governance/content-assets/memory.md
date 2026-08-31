# memory.md — 知识沉淀规范

> 本文档是 AiPalace 知识沉淀（memory）的规范性说明，定义"是什么"与"怎么遵循"。  
> 最高准绳：[`PHILOSOPHY.md`](../../../PHILOSOPHY.md)（P1–P9）。

> ⚠️ **过渡态说明（ADR-0013，2026-06-30）**：`context/memory/`（三级五域知识库）已迁移至 `vault/memory/01-PROJECTS/`，域结构（projects/enterprise/tech/workflow/reference）保持不变。当前 SOT 为 **`vault/memory/`**；SessionStart hook 注入路径已改为 `vault/memory/INDEX.md`（原 `context/memory/INDEX.md` 的决策树已并入其中）。本文档保留历史规范说明（三级结构、五域封闭集、触发三门等约定仍有效，在 vault 层沿用）供参考；新增条目请写入 `vault/memory/01-PROJECTS/`；详见 [`vault.md`](vault.md) 规范。

---

## 1. 定位

**memory** 是 AiPalace 管理的按需知识库——关于**"事"**的事实沉淀：项目进展、技术积累、工作流记录、参考资料、企业上下文。内容随沉淀增长，按需精细取用，而非一次性全量注入。

memory 是**内容资产**（见 [P7](../../../PHILOSOPHY.md#p7--内容统一源机制分治)）：内容工具无关，统一存放于本仓库；注入机制（SessionStart hook + cwd 触发）按工具分治，详见 [`product-assets/injection.md`](../product-assets/injection.md)（见 [P2](../../../PHILOSOPHY.md#p2--声明式管理工具派生限内容资产)）。

---

## 2. memory vs context：边界

memory 与 context 同为内容资产，均通过 INDEX 触发，但**内容域完全不同**：

| 维度 | memory（关于"事"） | context（关于"我"） |
|------|------------------|-------------------|
| **本质** | 知识库：项目、技术、工作流、参考 | 个人画像：身份、偏好、工作方式 |
| **内容性质** | 随沉淀增长，精细到条目级别 | 偏稳定，几乎任何任务都可参考 |
| **注入方式** | 渐进 pull：三门触发，精细到条目 | 软注：模型自选是否展开 what |
| **组织方式** | 三级：域（L1）→ 主题（L2）→ 条目（L3） | 维度拆分：identity / tech-stack 等 |
| **L1 封闭性** | **封闭集 5 域**（不可随意新增域） | 维度开放（可按需新增维度） |

> 判断原则：**"这是关于某个项目/技术/工作流的事实记录吗？"** → 是，放 memory；**"这是关于我自己的背景偏好吗？"** → 是，放 context。

---

## 3. 三级结构与五域封闭集

memory 采用**三级组织**：**域（L1）→ 主题（L2）→ 条目（L3）**。

### L1 域封闭集（不可增删，扩域走"先改规范"）

```
memory/
├─ projects/        个人项目（非企业）
├─ tech/            技术深度积累
├─ workflow/        工作流与方法
├─ reference/       参考资料与速查
└─ enterprise/      企业/公司项目
    └─ <公司名>/
       └─ <项目或模块>.md
```

**五域定义：**

| 域 | 含义 | L2 示例 | L3 示例 |
|----|------|---------|---------|
| `projects` | 个人（非企业）项目的进展、决策、积累 | `career/`、`side-projects/` | `go-transition.md` |
| `tech` | 技术深度：语言特性、框架原理、踩坑记录 | `go/`、`java/`、`ai/` | `generics.md`、`jvm-gc.md` |
| `workflow` | 工作流与方法：AI 使用、效率工具、流程 | `ai-workflow.md`、`gtd.md` | — |
| `reference` | 参考资料与速查：词汇表、外部规范摘录 | `glossary.md`、`links.md` | — |
| `enterprise` | 企业/公司项目：二级=公司名，三级=项目或模块 | `zhijin/`、`<其他公司>/` | `syzh.md`、`iam.md` |

**企业域特殊规则（体现 [P3](../../../PHILOSOPHY.md#p3--来源优先的归属分层判别方式按资产分化)）：**
- L2 必须是公司名（不可跳级直接放条目）。
- L3 是具体项目或模块（可继续嵌套，但不强制）。
- enterprise 内容含有可见性边界，务必在条目文件中标注公开级别（内部/仅本人）。

### L2/L3 开放

L2（主题）和 L3（条目）**开放**，随沉淀按需增长，无需预先规划（体现浅填原则）。

---

## 4. 浅填原则

三级结构是**精细化注入预留的框架**，不强制在初始阶段填满：

- 允许某个域下只有 1-2 个文件，甚至暂时为空目录。
- 优先保证已有知识的准确性，而非追求结构完整性。
- 随沉淀积累，自然向下展开 L2/L3；不要为填结构而造内容。

---

## 5. `memory/INDEX.md` 格式规范

`memory/INDEX.md` 是 memory 体系的**声明源**（体现 [P2](../../../PHILOSOPHY.md#p2--声明式管理工具派生限内容资产)），与 `context/INDEX.md` 同构——均为多级决策树，约束 `when → what`。

```markdown
# memory/INDEX.md — 知识库导航

always-on：本文件注入后，模型按以下决策树决定 pull 哪些条目。

## 何时看哪个 memory

### projects — 个人项目
- 涉及职业转型/学习路径 → [projects/career/go-transition.md](projects/career/go-transition.md)
- ...

### tech — 技术积累
- 涉及 Go 语言 → [tech/go/](tech/go/)（查索引后按需取条目）
- 涉及 Java/JVM → [tech/java/](tech/java/)
- ...

### workflow — 工作流
- 涉及 AI 工具使用/提示工程 → [workflow/ai-workflow.md](workflow/ai-workflow.md)
- ...

### reference — 参考
- 术语/缩写查询 → [reference/glossary.md](reference/glossary.md)
- ...

### enterprise — 企业项目
- 涉及知进公司 → [enterprise/zhijin/](enterprise/zhijin/)（不全量注入，细到具体项目条目）
- ...
```

**约束：**

1. `when` 条件在域间正交，域内按主题细分。
2. `enterprise` 域**禁止全量注入**——必须细到具体公司/项目条目，防止企业内部信息混入无关任务。
3. `what` 路径相对于 `memory/` 目录，使用 markdown 链接。
4. INDEX 本身不含实质性知识——知识在各条目文件中，INDEX 只做导航。
5. 每次新增/删除条目，须同步更新 INDEX 的对应节点。

---

## 6. 触发：三门并集

memory 的触发采用**三门并集（OR，最大化召回）**，任一门命中即触发对应条目加载：

| 门 | 触发方式 | 说明 |
|----|---------|------|
| **门 a：cwd 打分** | 复用 `compute_confidence()`，按工作目录路径打分 | 在 AiPalace 仓库工作 → 触发 `projects/`；在企业项目目录 → 触发 `enterprise/<公司>/` |
| **门 b：模型语义判断** | 模型读取 INDEX 全树，语义判断当前任务相关的条目 | 任务描述提到某技术词 → 触发 `tech/` 对应条目 |
| **门 c：任务描述×索引匹配** | 任务描述与 INDEX 叶节点的 when 条件主动匹配 | 任务含"词汇表"/"术语" → 触发 `reference/glossary.md` |

三门并集的意义：单一触发方式容易漏召回；三门同时工作，最大化"该取的知识被取到"的概率。

---

## 7. 注入粒度

**MVP 策略（当前）：** always 注入整棵 `memory/INDEX.md`（代价低，INDEX 本身不含实质内容）；具体条目按触发三门按需 Read。

**演进项（树大后启用）：** hook 按 cwd 裁剪子树注入（如：在企业项目目录时只注入 `enterprise/<公司>/` 分支），减少 INDEX 注入体积。此演进项须在实际达到阈值后，由 ADR 决策后落地（体现 [P8](../../../PHILOSOPHY.md#p8--决策留痕诚实标注)）。

> `context/INDEX` 与 `memory/INDEX` 均 always-on，落地时可合并为**一个注入块**省一次开销（实现细节见 [`product-assets/injection.md`](../product-assets/injection.md)）。

---

## 8. 沉淀来源

memory 条目通过两条路径沉淀：

1. **`/ai-palace` 主动沉淀**：会话收尾时把本轮新增知识点提炼后写入对应条目（`/wrap` 已于 ADR-0021 退役）。
2. **从双工具 native memory 凝练提取**：Claude Code / Codex 各自有原生 memory 机制；本仓库 memory 可从这些 native 沉淀中**再凝练提取**精华条目。**native memory 不弃用，只增强**——native 是仓库 memory 的上游提炼源之一，两者互补。

沉淀原则：
- 提炼后落入对应域/主题/条目，严格按三级结构存放。
- 单条条目保持自洽，可独立注入而不依赖其他条目。
- 过时内容及时标注或删除，保持知识库准确性（体现 [P9](../../../PHILOSOPHY.md#p9--显式过渡态)）。

---

## 9. 纳入新条目的要求

新增 memory 条目须满足：

1. **属于"关于事"的知识范畴**：项目/技术/工作流/参考，而非个人偏好（后者放 context）。
2. **落位于五域之一**：不得在 L1 域外新建顶级目录。
3. **INDEX 同步更新**：新条目必须在 `memory/INDEX.md` 的对应节点中添加 when→what 条目。
4. **enterprise 条目标注可见性**：公司内部信息必须在文件头注明可见性边界（内部/仅本人）。
5. **工具无关**：条目内容不含工具专有语法，确保跨工具复用（体现 [P7](../../../PHILOSOPHY.md#p7--内容统一源机制分治)）。
6. **只记当前态，不留时间戳/changelog**（体现 [P9](../../../PHILOSOPHY.md#p9--显式过渡态)）：条目写**当前有效**的事实/方案/设计，不是变更日志。
   - **禁止**注记类日期：`最后更新：<date>`、`（YYYY-MM-DD 起）`、`X 改名为 Y（date）`、`提炼来源：N session（date）`、`验证：<date>` 等"何时写的/何时改的/何时沉淀的"元信息。
   - 内容被推翻时**直接改写为新当前态**，旧态不留在条目里；**演进留痕靠 git 历史**追溯，不靠条目内日期注记。
   - **例外**：作为**事实本身一部分**的日期可保留（如截止日 / 发布日 / 版本时间线 / 合同到期）；这类日期写**绝对日期**，不写"上周 / 三天前"等相对表述。
   - 同一原则适用于 `context/` 下其它内容资产（rules / identity 等），不止 memory。

---

## 10. 扩域规则

**L1 域封闭**（体现 [P3](../../../PHILOSOPHY.md#p3--来源优先的归属分层判别方式按资产分化)）：不得随意在 `memory/` 根目录新增第六个域。如有合理需求，须先：

1. 在 `docs/governance/content-assets/memory.md`（本文件）修改五域定义并说明理由。
2. 更新 `memory/INDEX.md` 决策树结构。
3. 写 ADR 记录扩域决策（背景/动机/取舍）。
4. 再建立新域目录。

---

## 11. 溯源与演进

- memory 内容变更须通过 git 追溯（体现 [P8](../../../PHILOSOPHY.md#p8--决策留痕诚实标注)）。
- 影响注入粒度或触发机制的变更须在 `product-assets/injection.md` 同步更新，并写 ADR。
- 已知不一致或过渡状态须显式标注（体现 [P9](../../../PHILOSOPHY.md#p9--显式过渡态)）。

---

*本规范依据 spec §6c（`2026-06-18-aipalace治理与设计哲学-design.md`）成文。*
