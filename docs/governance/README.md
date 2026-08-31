# AiPalace 规范区索引

> 本区是 AiPalace 治理规范的索引入口。所有规范细则均以 [`PHILOSOPHY.md`](../../PHILOSOPHY.md) 为最高准绳。

---

## 三层关系

```
PHILOSOPHY.md           ← 最高准绳（设计哲学总纲 P1–P9，极少改）
    │
docs/governance/        ← 治理规范层（各资产规范 + 机制规范，按需迭代）
    │
evolution.md            ← 演进流程层（操作 SOP、ADR 工作流、待决项汇总）
```

- **哲学层** 是九条不变原则，裁判所有规范冲突的最高准绳。
- **规范层** 是各类资产的纳入标准、命名规则与工作流约定，按需迭代。
- **流程层** 是操作 SOP、ADR 工作流与过渡态汇总，指导每次演进动作。

---

## 资产分类总览

### 内容资产（content-assets）— 统一源，工具无关

| 类别 | 定位 | 规范文档 |
|------|------|---------|
| **skills** | 能力资产；`registry.yaml` 单一源，`skillctl` symlink 派生到双工具 | [content-assets/skills.md](content-assets/skills.md) |
| **rules** | 硬配置域规约（路径/条件匹配后必须注入整篇）；无需 INDEX，path-scoped 匹配即触发 | [content-assets/rules.md](content-assets/rules.md) |
| **context** | 关于"我"的画像（身份/技术栈/工作方式/环境偏好）；原 `context/self/` 已迁 vault（见过渡说明） | [content-assets/context.md](content-assets/context.md) |
| **memory** | 关于"事"的知识库（三级五域，按需 pull）；原 `context/memory/` 已迁 vault（见过渡说明） | [content-assets/memory.md](content-assets/memory.md) |
| **vault** | 记忆 vault（`vault/memory/`）：五层结构 + PROTOCOL 契约 + frontmatter 标准；现役个人记忆 SOT | [content-assets/vault.md](content-assets/vault.md) |

### 产品资产（product-assets）— 与工具形态耦合，分治

| 类别 | 定位 | 规范文档 |
|------|------|---------|
| **injection** | 注入机制协同：SessionStart hook（双工具同逻辑）+ path-scoped 硬触发 + native memory 协同 | [product-assets/injection.md](product-assets/injection.md) |
| **plugins** | 插件布局（claude/codex marketplace + sql-expert-dba）；插件↔skill 边界 | [product-assets/plugins.md](product-assets/plugins.md) |
| **commands** | 斜杠命令（`commands/<name>.md` 软链派生到工具 commands 目录）；命令↔skill 边界 | [product-assets/commands.md](product-assets/commands.md) |

### 横切关注点

| 类别 | 定位 | 规范文档 |
|------|------|---------|
| **creations** | 创作性产物（与内容资产正交单列）的管理规则 | [creations.md](creations.md) |
| **evolution** | 演进流程 SOP：skill 工作流、ADR append-only 规则、上游同步、SOT 切换路径 | [evolution.md](evolution.md) |

---

## 文档跳转表

| # | 文档 | 状态 | 说明 |
|---|------|------|------|
| 1 | [content-assets/skills.md](content-assets/skills.md) | **就绪** | skill 三级结构、registry 规范、tier、doctor 校验项、纳入门槛 |
| 2 | [content-assets/rules.md](content-assets/rules.md) | **就绪** | 硬配置域规约、path-scoped 命名、工具实现分治 |
| 3 | [content-assets/context.md](content-assets/context.md) | **就绪** | context 分层结构、INDEX 格式、软注入规则 |
| 4 | [content-assets/memory.md](content-assets/memory.md) | **就绪** | memory 三级五域、INDEX 格式、触发三门、浅填原则 |
| 5 | [product-assets/injection.md](product-assets/injection.md) | **就绪** | SessionStart hook、path-scoped 实现、native memory 协同策略 |
| 6 | [product-assets/plugins.md](product-assets/plugins.md) | **就绪** | 插件布局、插件↔skill 边界判断规则 |
| 7 | [product-assets/commands.md](product-assets/commands.md) | **就绪** | 斜杠命令软链派生、命令↔skill 边界 |
| 8 | [creations.md](creations.md) | **就绪** | 创作性产物归档、命名、可见性管理 |
| 9 | [evolution.md](evolution.md) | **就绪** | 演进流程 SOP：skill 工作流 + ADR 规则 + 待决项汇总 |
| 10 | [../../PHILOSOPHY.md](../../PHILOSOPHY.md) | **就绪** | 设计哲学总纲（P1–P9） |
| 11 | [content-assets/vault.md](content-assets/vault.md) | **就绪** | 记忆 vault 规范：五层职责 + frontmatter 硬标准 + 写入纪律 + context/rules 边界（ADR-0013） |

---

## 使用指南

**新增任何资产前**，先读对应的 content-assets 规范（如新增 skill 先读 [skills.md](content-assets/skills.md)）。

**改演进流程前**，先读 [evolution.md](evolution.md)。

**遇到规范冲突**，以 [PHILOSOPHY.md](../../PHILOSOPHY.md) 为准，并在对应 ADR 中记录裁判依据。

> 参考：体系设计背景与决策依据见 [`docs/superpowers/specs/2026-06-18-aipalace治理与设计哲学-design.md`](../superpowers/specs/2026-06-18-aipalace治理与设计哲学-design.md)
