# rules.md — 硬配置域规约规范

> 本文档是 AiPalace 硬配置域规约（rules）的规范性说明，定义"是什么"与"怎么遵循"。  
> 最高准绳：[`PHILOSOPHY.md`](../../../PHILOSOPHY.md)（P1–P9）。

---

## 1. 定位

**rules** 是 AiPalace 管理的硬配置域规约——每条 rule 针对特定路径或技术域，一旦触发条件匹配，**必须整篇注入**当前上下文，不可跳过或部分注入。

rules 是**内容资产**（见 [P7](../../../PHILOSOPHY.md#p7--内容统一源机制分治)）：规约内容工具无关，统一存放于本仓库；注入机制（Claude rules glob / Codex 目录树 AGENTS.md）按工具分治，规范详见 [`product-assets/injection.md`](../product-assets/injection.md)。

---

## 2. rules vs context：边界

rules 与 context 同为内容资产，但**注入哲学完全不同**：

| 维度 | rules（硬配置） | context（软选） |
|------|----------------|----------------|
| **本质** | 域规约：路径/条件匹配即强制注入 | 个人画像：关于"我"的偏好与背景 |
| **触发方式** | path-scoped 硬触发，无需 INDEX | `context/INDEX.md` 约束，模型自选 |
| **注入方式** | **硬注**：条件命中后整篇必须注入 | **软注**：模型据任务自行判断是否展开 |
| **内容性质** | 针对特定技术域的规范、约束、最佳实践 | 身份偏好、技术栈习惯、工作方式、环境配置 |
| **INDEX** | **无需 INDEX**（path-scoped 匹配本身即 when） | 需要 `context/INDEX.md`（决策树约束 when→what） |

> 判断原则：**"这是对某个技术域的规范约束吗？"** → 是，放 rules；**"这是关于我自己的背景偏好吗？"** → 是，放 context。

---

## 3. 触发机制

**rules 无需 INDEX**：path-scoped 匹配本身就是触发条件。

> **实测语义（ADR-0020，2026-08-03）**：触发条件是**读取工作目录树内匹配 `paths` 的文件**，
> 不是 cwd 落在该项目。三组对照实验：Java 项目根启动但不读文件 → 不注入；同一 cwd 读一个
> `.java` → 注入（`load_reason: path_glob_match`）；在别处启动、读**工作区之外**的 `.java`
> → 同样不注入（glob 相对工作目录树匹配）。写 rule 的 `paths` 时按"会打开哪些文件"设计，
> 不是按"在哪个目录启动"设计。

每条 rule 通过 glob 模式或目录范围声明其**生效域**：

```
# 示例（Claude rules 格式）
---
paths:
  - "**/*.java"
  - "**/src/main/java/**"
---
<rule 内容>
```

路径命中即注入，无需任何手动激活步骤（体现 [P2](../../../PHILOSOPHY.md#p2--声明式管理工具派生限内容资产)）。

---

## 4. 内容统一源

rules 内容统一存放于本仓库，工具无关（体现 [P7](../../../PHILOSOPHY.md#p7--内容统一源机制分治)）：

```
rules/
├─ java-spring.md     ← Java Spring 技术域规约
├─ frontend-web.md    ← 前端 Web 技术域规约
└─ ...
```

规约文件本身不含工具专有语法，只包含域规约正文。工具侧的注入配置（paths glob 声明、AGENTS.md 引用）在 `product-assets/injection.md` 中分治管理。

---

## 5. 注入机制分治

rules 的注入机制按工具分治，**不在本文档中规范，详见 [`product-assets/injection.md`](../product-assets/injection.md)**。

概述：

| 工具 | 机制 | 触发方式 |
|------|------|---------|
| **Claude Code** | `~/.claude/rules/<域>.md`，文件头声明 `paths:` glob | glob 命中即注入整篇 |
| **Codex** | 目录树 `AGENTS.md` 中引用规约内容 | 目录范围命中即注入 |

两工具的注入实现不同，但统一源（rules 内容）只维护一份（体现 [P7](../../../PHILOSOPHY.md#p7--内容统一源机制分治)）。

---

## 6. 现有 rules

当前已纳入的硬配置域规约：

| rule | 技术域 | 生效路径（示例） |
|------|--------|----------------|
| `java-spring` | Java Spring 框架 | `**/*.java`、`**/src/main/java/**` |
| `frontend-web` | 前端 Web 开发 | `**/*.tsx`、`**/*.ts`、`**/src/**` |

---

## 7. 纳入新 rule 的要求

新增 rule 须满足：

1. **有明确的技术域边界**：rule 必须对应具体的路径集合或技术域，不得是通用性建议。
2. **内容工具无关**：规约正文不含工具专有语法，确保可跨工具复用。
3. **路径声明清晰**：需在 `product-assets/injection.md` 中同步声明各工具的 paths glob 或目录范围。
4. **整篇可注入**：规约内容应完整自洽，命中时整篇注入后即可直接生效，无需额外上下文。

---

## 8. 溯源与演进

- rules 内容变更须通过 git 追溯（体现 [P8](../../../PHILOSOPHY.md#p8--决策留痕诚实标注)）。
- 影响注入机制的变更（如调整 paths glob 范围）须在 `product-assets/injection.md` 同步更新。
- 已知不一致或过渡状态须显式标注（体现 [P9](../../../PHILOSOPHY.md#p9--显式过渡态)）。

---

*本规范依据 spec §6a（`2026-06-18-aipalace治理与设计哲学-design.md`）成文。*
