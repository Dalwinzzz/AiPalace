# vault.md — 记忆 vault 规范

> 本文档是 AiPalace 记忆 vault（`vault/memory/`）的规范性说明，定义五层职责、frontmatter 硬标准、写入纪律与边界约定。  
> 最高准绳：[`PHILOSOPHY.md`](../../../PHILOSOPHY.md)（P1–P9）。  
> 决策依据：[ADR-0013](../../../adr/0013-吸收记忆宫殿方法论建Obsidian记忆层.md)（吸收记忆宫殿方法论）。

---

## 1. 定位

**vault** 是 AiPalace 管理的个人记忆层——关于**"我是谁"**（身份 / 全局约定 / 偏好）与**"事"**（项目知识 / 外部资料 / 飞轮沉淀）。其物理位置为 `AiPalace/vault/memory/`，同时作为 Obsidian 根（`vault/`）内的人类可读知识图谱，与工程机器（registry/skillctl/plugins）正交共存。

vault 是**内容资产**（见 [P7](../../../PHILOSOPHY.md#p7--内容统一源机制分治)）：内容工具无关，统一存放于本仓库；注入机制（SessionStart hook 按序读 `00-RULES/operating-rules.md` 与 `INDEX.md`）按工具分治，详见 [`product-assets/injection.md`](../product-assets/injection.md)。

> **与 context/memory 的关系**：`context/self/` 与 `context/memory/` 的内容已迁入 vault（ADR-0013）。现役 SOT 为 `vault/memory/`；旧位置文件已标注迁移指向（见 [`context.md`](context.md)、[`memory.md`](memory.md) 的过渡说明）。

---

## 2. 五层职责

```
vault/memory/
├── PROTOCOL.md        ← 唯一读写契约（受 P1–P9 统领）——任何 agent 读写 vault 的唯一入口
├── INDEX.md           ← always-on 注入：触发三门 + 条件决策树（SessionStart hook 入口）
├── 00-RULES/          ← 身份层：我是谁 / 全局工作约定 / 跨域铁律（最高法律）
├── 01-PROJECTS/       ← 项目/领域层：个人项目 + 企业项目 + 技术/工作流/参考域
├── 02-SOURCES/        ← 外部剪藏资料层：索引卡 + 外部文章/规范摘录
├── 03-MAPS/           ← 图层：流程图 / 架构 / 决策树索引（指向 creations 等）
├── 04-FEEDBACK/       ← 飞轮中枢：journal（今天发生了什么）/ candidates / DREAMS（审批留痕）
└── _template/         ← frontmatter 模板（`_template/note.md`）
```

### 00-RULES（身份层）

- 存放「我是谁」的核心：身份 / 技术栈偏好 / 工作方式 / 跨域铁律。
- **always-on 模型（ADR-0014 + ADR-0016）**：常驻两项——`identity.md`（精简身份卡，经 INDEX 指引读取）与 `operating-rules.md`（双工具共享操作规则，SessionStart hook 直注，M4 唯一豁免）；技术栈与操作规则组（`dev.md` / `flow.md` / `ops.md`）由 `INDEX.md` 决策树**按需拉、可叠加**（多组命中并集加载，如"多步 Java 修复"→ dev + flow）。
- 等价于原 `context/self/`（已迁移）；全局指令文件的工具无关共享规则已整合入 `operating-rules.md`（M4 完成，ADR-0016），native 侧（`~/.claude/CLAUDE.md`、`~/.codex/AGENTS.md`）为 `context/native/` 双 stub 的软链派生。
- **最高法律**：所有其余层内容在与 `00-RULES/` 矛盾时，以 `00-RULES/` 为准。

### 01-PROJECTS（项目/领域层）

- 容纳「项目」（career / enterprise 含 decisions + feedback 子目录）和「领域知识」（tech / workflow / reference）。
- 保留原 `context/memory/` 的五域结构：projects / enterprise / tech / workflow / reference。
- enterprise 条目须标注可见性边界（内部/仅本人）。

### 02-SOURCES（资料层）

- 仅收**外部**剪藏资料（文章/规范摘录/链接卡）；个人知识域（tech/workflow/reference）在 `01-PROJECTS/`，不在此层。

### 03-MAPS（图层）

- 存放流程图 / 架构图 / 决策树的**索引卡**；大文件指向 `creations/` 或 `docs/knowledge/`，不内联。

### 04-FEEDBACK（飞轮中枢）

- `journal/<YYYY-MM-DD>.md`：当天会话留痕、蒸馏候选捕获落点。
- `candidates.md`：待审批的蒸馏候选列表。
- `DREAMS.md`：已审批晋升条目的留痕档案。

---

## 3. PROTOCOL 为唯一入口

**任何 agent 读写 vault 前，必须先读 `vault/memory/PROTOCOL.md`**。该文件是三条最高指令（读 first / 写 back / 不越权）与「去哪找什么」表的唯一声明源。

`INDEX.md` 是 SessionStart 注入的**导航入口**（always-on 轻量注入），不是写入入口。写入遵循 PROTOCOL 指定的层，由 `/ai-palace` 编排落盘（`/wrap` 已于 ADR-0021 退役）。

---

## 4. frontmatter 硬标准

每条记忆 note 必须携带以下 frontmatter（模板见 `vault/memory/_template/note.md`）：

```yaml
---
title: <简短标题>
type: identity|preference|principle|decision|feedback|project|source|map|journal
scope: global | project:<域/子域> | source
status: active | draft | deprecated
confidence: high | medium | low
created: YYYY-MM-DD
updated: YYYY-MM-DD
last_confirmed: YYYY-MM-DD
source: []   # 来源会话/链接，可追溯
---
```

**硬约束（不可省略）**：

| 字段 | 约束 |
|------|------|
| `type` | 封闭枚举，不得自造新值（新值须先改本规范 + 写 ADR） |
| `scope` | `global`（00-RULES 层）/ `project:<域>` / `source` |
| `status` | 封闭枚举 |
| `confidence` | 封闭枚举 |
| `created` / `updated` | 绝对日期，不写相对时间（"上周"等）；见 [memory.md §9](memory.md) 禁止时间戳规则 |

**禁止**：在正文中注记"最后更新 DATE"、"YYYY-MM-DD 起"等变更日志式元信息——演进靠 `updated` 字段 + git 历史追溯，不靠正文时间戳。

---

## 5. 写入纪律

### 不越权改 00-RULES

**00-RULES/ 是最高法律**：任何 agent 或工具**不得直接编辑** `00-RULES/` 下的文件。唯一合法路径：

```
提议变更 → 捕获至 04-FEEDBACK/candidates.md → dalwin 审批 → /ai-palace promote → 写入 00-RULES/
```

使用 `/ai-palace` 捕获，由 dalwin 手动确认后再写入。

### 其余层可直接读写

- `04-FEEDBACK/journal/` 是**唯一无需审批的实时捕获落点**——不确定放哪的内容，先落 journal，由飞轮蒸馏归位。
- `01-PROJECTS/`、`02-SOURCES/`、`03-MAPS/` 可由 agent 按 PROTOCOL 指导直接写入（写后更新 `updated` 字段）。

### secrets 红线

secrets 绝不写入 vault 明文。格式：`$secret:NAME`（名称引用），实体经 Keychain / `.env`（gitignore）管理。

---

## 6. 与 context/rules 的边界

| 资产 | 位置 | 触发方式 | 内容性质 |
|------|------|---------|---------|
| **vault/memory/** | `vault/memory/` | SessionStart hook always-on | 「我是谁」+ 项目记忆（人格层） |
| **context/rules/** | `context/rules/` | path-scoped 硬触发（pom.xml/.java/.tsx 等） | 工程规范（Java Spring / 前端 Web 等程序记忆） |
| **context/howto/** | `context/howto/` | 指令文件指针按需 Read | 操作手册（怎么用某能力） |

判断原则：
- **「这是关于我自己、我的项目、全局工作约定吗？」** → 放 vault（`00-RULES/` 或 `01-PROJECTS/`）。
- **「这是工程代码规范（与语言/框架绑定）吗？」** → 放 `context/rules/`（path-scoped）。
- **「这是操作手册（某能力怎么用）吗？」** → 放 `context/howto/`（指针按需加载）。

---

## 7. 内容维护原则

1. **单一条目自洽**：每条 note 可独立注入，不依赖其他 note 的前置加载。
2. **只记当前态**：条目写当前有效事实，不留变更日志；旧态直接改写，演进靠 git 历史追溯。
3. **浅填优先**：允许层下只有少量文件；不为结构完整性造内容（体现浅填原则）。
4. **工具无关**：note 内容不含工具专有语法，确保跨工具复用（[P7](../../../PHILOSOPHY.md#p7--内容统一源机制分治)）。
5. **溯源标注**：`source` 字段填来源会话/链接，确保可追溯（[P8](../../../PHILOSOPHY.md#p8--决策留痕诚实标注)）。

---

## 8. 过渡态声明（P9）

> M4 全局指令整合已完成（ADR-0016）：共享规则单一源 `00-RULES/operating-rules.md` + native stub 软链派生，原双存已收敛。native memory（`~/.claude/projects/…/memory/`）存量条目仍按 [`memory.md`](memory.md) 既有策略渐进迁移，属正常运行态，非待决项。

---

*本规范依据 spec `2026-06-27-aipalace-obsidian记忆层-design.md`（M1–M7）成文，ADR-0013 为决策依据。*
