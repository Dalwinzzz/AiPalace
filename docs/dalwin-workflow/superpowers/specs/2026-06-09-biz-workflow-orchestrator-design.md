# biz-workflow 业务工作流编排器 · 设计 Spec

> 日期：2026-06-09
> 状态：设计定稿（待实现）
> 类型：纯 Skill（语义自动触发），业务侧日常工作 SOP 编排器
> 关联资产：`sql-expert-dba`（SQL 委托）、`spec-architect`（SDD 委托）、Apifox MCP（接口契约）、`context/java-spring.md`（Maven 规范）、`git-commit-convention`

---

## 1. 目标与定位

把「公司日常业务侧需求开发 / 运维排查问题」中**真实重复、流程化**的工作 SOP 化，
沉淀为一个可语义触发的 Skill。日常处理任务时无需手工拆步骤，由 Skill 按既定流程
自动 push，只在**真正需要人脑判断的决策点**停下等用户拍板。

**核心定位：编排器（orchestrator），不是执行器。**
- 自己负责：分诊、串流程、控决策点、状态可见性。
- 专业活外包：SQL → 委托 `sql-expert-dba`；需求/根因结构化设计 → 委托 `spec-architect`；
  接口契约 → 委托 Apifox MCP。

**设计哲学**：尊重 Claude Code 原生设计——纯 Skill，靠 `description` 语义命中触发，
不做 slash command 显式入口（与 Codex 侧 `/命令` 习惯区分；在 Claude 中不显式指定）。

---

## 2. 形态与部署

| 项 | 结论 |
|----|------|
| 形态 | 纯 Skill，语义自动触发（不做 slash command） |
| 位置 | `~/.claude/skills/biz-workflow/`（与现有 skill 同级） |
| 触发 | 由 `SKILL.md` 的 `description` 语义命中；命门见 §7 |

**部署前置（由用户手动完成，本设计不擅自改全局 settings）：**
- 将 `spec-architect` 配置为 **name-only（禁止自动触发）**。
- biz-workflow 内部对 spec-architect 是**显式 invoke**，显式调用不受 name-only 限制，
  委托链照常工作。

---

## 3. 文件结构

与 `sql-expert-dba` 同构（Router + workflows + 共享 references）：

```
biz-workflow/
├── SKILL.md                       # ★Router：分诊 + 流程总控 + 决策点定义（唯一大脑）
├── workflows/
│   ├── feature-dev.md             # 需求开发线 workflow（剧本）
│   └── ops-triage.md              # 运维排查线 workflow（剧本）
└── references/                    # 两条线共享的公共步骤（可独立演化的积木）
    ├── step-A-api-contract.md     # 接口契约对齐（Apifox，条件触发）
    ├── step-B-code-locate.md      # 代码定位套路
    ├── step-C-build-test.md       # 专属 Maven 构建自测
    ├── step-D-sql-delegate.md     # 委托 sql-expert-dba（条件触发）
    ├── step-E-commit.md           # git-commit-convention 提交
    └── step-F-triage-report.md    # 根因+影响面+修复建议产出物
```

**职责边界：**
- `SKILL.md`：唯一大脑。分诊 → 选 workflow → 按剧本推进 → 决策点暂停。
- `workflows/*.md`：剧本。定义本条线步骤顺序、条件触发位置、决策点位置。
- `references/step-*.md`：可复用积木。每步的具体操作规范（命令、套路、产出格式），
  被两条 workflow 按需读取。

---

## 4. Router（SKILL.md）总控逻辑

### 4.1 分诊（进来第一步）

| 输入信号 | 判定 | 走向 |
|----------|------|------|
| 需求原型 / PRD / "加个功能" / "改成…" / 接口字段变更 | 需求开发线 | `workflows/feature-dev.md` |
| 工单 / 报错堆栈 / 异常日志 / "线上…出问题" / "查为什么…" / 数据对不上 | 运维排查线 | `workflows/ops-triage.md` |
| 模糊 / 两可 | **不猜，问一句** | 让用户一句话点明"开发还是排查" |

分诊只做二选一粗判断；细节决策交给 workflow。

### 4.2 两个决策点（全局硬约束，任何 workflow 必须遵守）

- **★决策点①（方案 / 根因定调）**：自主走完"理解 + 定位"后**必须停**，摊出
  "打算怎么改 / 根因是什么"等用户拍板。**未经确认不得改代码 / 调 DB**。
  - **归属动态绑定（依据见 §6' 决策点①去重）**：若该任务委托了 spec-architect，则其
    Confirm 承担①，biz-workflow 不重复问；若未委托，则由 biz-workflow 自管。
- **★决策点②（落库 / 提交前）**：自测通过后**必须停**，摊出"改了哪些文件 +
  diff 概要 + 提交计划"等用户拍板。**未经确认不得提交 / 写库 / 改文档**。

### 4.3 不可逆操作护栏（兜底，额外确认）

除上述两个常规卡点外，凡遇 **删数据 / 改生产配置 / 执行非只读 SQL / push 到远端**
等不可逆操作，**无论在哪一步一律额外停下显式确认**。防止流程中某个意外动作越权。

### 4.4 状态可见性

每进入一个步骤，Router 用一行告知"现在在 X 步、要做什么"（参照 sql-expert-dba 的
阶段提示），让用户随时知道进度、随时可打断。

---

## 5. 两条 Workflow 剧本

### 5.1 需求开发线（`workflows/feature-dev.md`）

```
1. 分析需求原型               理解要做什么、影响哪些接口/表
   [Medium+ 或用户要求] → 委托 spec-architect（见 §6）产出 spec
2. [改接口?] → step-A         先拉 Apifox 契约当靶子（改接口才执行）
3. step-B 代码定位            Controller→Service→Mapper/SQL 定位改动点
                              （若已走 spec，B 退化为"按 spec 核对定位"）
4. ★决策点①                  摊出实现方案 → 等用户拍板
                              （若走了 spec-architect，①由其 Confirm 承担）
   ───────── 以下需经①放行 ─────────
5. 实现改动                   按确认方案改代码
6. [涉及DB?] → step-D         委托 sql-expert-dba 评审/优化
7. step-C 构建自测            专属 Maven 命令编译+跑测
8. ★决策点②                  摊出 diff 概要 + 提交计划 → 等用户拍板
   ───────── 以下需经②放行 ─────────
9. [改接口?] → step-A         提交前核对实现与契约一致
10. step-E 提交               git-commit-convention 生成 message 并提交
```

### 5.2 运维排查线（`workflows/ops-triage.md`）

```
1. 分析工单/报错              判断是代码问题还是数据问题
   [根因需结构化设计] → 委托 spec-architect 产出修复 spec（见 §6）
2. step-B 代码定位            按报错堆栈反查 / 按现象定位
   [数据问题?] → step-D       委托 sql-expert-dba 查数/诊断（辅助定位根因）
3. step-F 产出结论            根因 + 影响面 + 修复建议 → 落 docs/problem
4. ★决策点①                  摊出根因与修复方案 → 等用户拍板
   ┌─ 只需结论、不改代码 → 到此结束（产出物已落盘）【早退分支】
   └─ 需修复 ↓ ───── 以下需经①放行 ─────
5. 实现修复                   按确认方案改代码
6. [涉及DB?] → step-D         委托 sql-expert-dba（修复涉及 DB）
7. step-C 构建自测            专属 Maven 命令验证修复
8. ★决策点②                  摊出 diff + 提交计划 → 等用户拍板
   ───────── 以下需经②放行 ─────────
9. step-E 提交               git-commit-convention 提交修复
10. [改了Controller接口?] → step-A  回归同步更新 Apifox 文档
```

### 5.3 两条线关键差异

- **A 接口契约位置**：需求线 = 前置（靶子）+ 提交前（校验）；排查线 = 仅收尾（回归同步）。
  两条线均「**改接口才触发**」，不涉及接口则整段跳过 A。
- **F 产出物**：仅排查线有，且是其**核心交付**。很多排查任务到步骤 3/4 给完结论即结束。
- **C/E 在排查线**：条件触发——只有真要改代码修复才走；纯结论型排查不碰。
- **D**：两条线都可能出现两次（定位辅助 / 改动评审），按需触发。
- **早退分支**：排查类任务不强制产生代码提交；给完结论（已落盘）即可结束。

---

## 6. 公共步骤规范（references）

### 6.1 step-A 接口契约对齐（Apifox MCP，条件触发）

- **触发**：仅当改动涉及 Controller 接口 / 字段变更。
- **三个时点**：
  - 需求线前置——拉 OpenAPI/字段/用例当实现靶子；
  - 需求线提交前——核对实现与契约一致；
  - 排查线收尾——反向更新 Apifox 文档（防文档腐化）。
- **委托对象**：Apifox MCP（`mcp__apifox-new-mcp__*`）。

### 6.2 step-B 代码定位

- 需求线：按 Controller→Service→Mapper/SQL 自顶向下定位改动点。
- 排查线：按报错堆栈反查 / 按现象定位。
- 若该任务已走 spec-architect，spec 内已含勘察定位结论，B 退化为"按 spec 核对"。

### 6.3 step-C 专属 Maven 构建自测

- **必须**使用 `context/java-spring.md` 定义的专属命令，**绝不用 `~/.m2`**：
  ```
  mvn -s /Users/dalwin/Library/ConfigFile/maven/saas/settings.xml \
      -Dmaven.repo.local=/Users/dalwin/Library/Repository <goal>
  ```
- 查找/解压依赖 jar 同样走 `/Users/dalwin/Library/Repository`，不用 `~/.m2`。

### 6.4 step-D 委托 sql-expert-dba（条件触发）

- **触发**：改动涉及 DB（SQL 评审、优化、查数、DDL）。
- **委托方式**：显式 invoke `sql-expert-dba:sql-expert-router`（总入口分诊），
  由其路由到具体子专家。不在 biz-workflow 内重写 SQL 能力（DRY）。

### 6.5 step-E git 提交

- 按 `git-commit-convention`（`<type>(<scope>): <subject>`）生成 commit message。
- 提交前已在决策点②向用户确认；不自动 push（push 属不可逆护栏，需额外确认）。

### 6.6 step-F 排查产出物

- 格式：**根因 + 影响面 + 修复建议**。
- 落盘：`docs/problem/`（沿用现有目录习惯，可追溯/可复盘）。

---

## 6'. spec-architect 委托契约（SDD 集成）

> 关键集成点。spec-architect **自身是会跑完整流程的编排器**（硬约束#3 + Step 7
> 会 auto-commit spec 后**强制进入编码**），若不约束会与 biz-workflow 的决策点护栏冲突。

### 何时委托

| 复杂度（沿用 spec-architect 自身判定） | 是否委托 | 决策点①归属 |
|------|----------|------|
| Small（加字段/改校验/调查询条件） | 可跳过，直接 step-B | biz-workflow 自管 |
| Medium / Complex（跨模块/多表/迁移/架构变更） | **委托，走 SDD** | spec-architect Confirm 承担 |
| 用户显式说"先写 spec / 先规划" | **强制委托** | 同上 |

排查线同理：简单报错直接 step-B；根因涉及多模块/需结构化修复方案时委托。

### 委托契约（invoke 指令必须包含）

1. 任务上下文；
2. **"仅交付 spec，触发 spec-architect 的 B 分支（显式停止），不要 continue-to-coding，
   产出后交还控制权"**——精准命中 `continue-to-coding.md` 的 B 分支，干净止于
   spec + auto-commit，**不越权抢占后续编码**；
3. 产出 spec 后交还 biz-workflow。

### 职责分工

- **spec-architect 负责**：勘察真实代码、复杂度判定、自身 Confirm、生成 spec、
  auto-commit spec（其 Step 6.5）。
- **交还后 biz-workflow 负责**：把 spec 当"已确认方案输入"，继续 step-B（核对）→
  决策点①（若走 spec 则由其 Confirm 已承担，不重复）→ D/C → 决策点② → E → A。

### 决策点①去重（§4.2 动态归属的依据）

spec-architect 的 Confirm 与 biz-workflow 决策点①语义重叠（都在动代码前确认方案）。
**规则**：走了 spec-architect → 其 Confirm 即视为①，交还后不重复问；
未走 spec-architect（简单任务直接 step-B）→ ①由 biz-workflow 自管。

---

## 7. description 触发策略（纯 Skill 的命门）

`description` 要做到：**端到端业务开发/排查任务能命中，但不抢纯 SQL / 纯 spec 场景**。

- **命中**："做这个需求"、"开发这个功能"、"改个接口"、"查这个工单"、
  "线上报错排查"、"这个 bug 定位一下"——即端到端的业务开发/排查任务。
- **让位**：
  - 纯 SQL 优化/报错 → `sql-expert-dba`（biz-workflow 内部需要时再委托）；
  - 纯"只写个 spec" → `spec-architect`（用户 name-only 显式调用）。
- **不冲突说明**：spec-architect 改 name-only 后，"需要 spec 的自动场景"正好由
  biz-workflow 接管并内部显式委托，显式 invoke 不受 name-only 限制。

---

## 8. 设计决策汇总

| # | 决策项 | 结论 |
|---|--------|------|
| 1 | 形态 | 纯 Skill，语义自动触发（不做 slash command） |
| 2 | 位置 | `~/.claude/skills/biz-workflow/` |
| 3 | 结构 | Router(SKILL.md) + 2 workflows + 6 共享 references |
| 4 | 分诊 | 需求线 / 排查线二选一；模糊则问，不猜 |
| 5 | 自动化档位 | 均衡：2 个决策点（方案/根因定调、落库/提交前） |
| 6 | 护栏 | 不可逆操作（删数据/改生产配置/非只读SQL/push）一律额外确认 |
| 7 | 步骤序列 | 需求线 10 步 / 排查线 10 步（排查线支持"给结论即结束"早退） |
| 8 | A 接口契约 | 需求线前置+提交前校验；排查线收尾回归；均"改接口才触发" |
| 9 | D SQL | 委托 sql-expert-dba（显式 invoke），定位/评审按需触发 |
| 10 | SDD/spec | Medium+ 委托 spec-architect，指令含"止于 spec、触发 B 分支、交还控制权" |
| 11 | 决策点①归属 | 动态：走 spec-architect 则由其 Confirm 承担，否则 biz-workflow 自管 |
| 12 | 部署前置 | spec-architect 改 name-only 由用户做；biz-workflow 内部显式 invoke 不受限 |

---

## 9. 后续（实现阶段）

- 进入 `writing-plans` skill 产出实现计划。
- 实现产物：上述 9 个文件（SKILL.md + 2 workflows + 6 references）。
- 实现后：用户手动将 spec-architect 配为 name-only。
- 演进策略：先落一版，使用过程中按真实需求迭代调整（用户明确表态）。
