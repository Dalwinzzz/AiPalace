# biz-workflow 业务工作流编排器 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建一个纯 Markdown 的 prompt-skill `biz-workflow`，作为业务侧日常「需求开发 / 运维排查」工作的 SOP 编排器，语义自动触发，在两个决策点暂停等用户拍板。

**Architecture:** Router(SKILL.md) + 2 个 workflow 剧本 + 6 个共享 reference 步骤。skill 本体建在 `dalwin-workflow/skills/biz-workflow/` 纳入 git，软链到 `~/.claude/skills/` 生效。编排器自身只管分诊/串流程/控决策点，专业活委托 sql-expert-dba（SQL）与 spec-architect（SDD），接口对齐委托 Apifox MCP。

**Tech Stack:** Markdown prompt-skill（无可执行代码）。验证靠：结构/frontmatter 合规 + 内容对照设计稿 + 触发场景演练。不适用 TDD/单元测试。

**Spec 来源：** `dalwin-workflow/docs/superpowers/specs/2026-06-09-biz-workflow-orchestrator-design.md`

---

## 关于"测试"的说明（重要）

本计划实现的是**纯文档 prompt-skill**，没有可运行代码，无法写 pytest 式单元测试。
每个任务的"验证"环节改造为适配 prompt-skill 的三类手段：

1. **结构校验**：文件存在、frontmatter 合法（`name`+`description`）、Markdown 可解析、内部链接锚点有效。
2. **内容对照**：用 `grep` 等确认关键约束/步骤/委托契约确实写进了文件（对照 spec）。
3. **触发演练**（最终验收任务）：在新会话用真实任务描述验证 skill 能被语义命中、分诊正确、决策点生效。

这是对 writing-plans 默认 TDD 范式的合理裁剪——TDD 针对代码，本 skill 是文档。

---

## 文件结构（决策锁定）

```
dalwin-workflow/skills/biz-workflow/          # ← git 纳管的 SOT
├── SKILL.md                       # Router：frontmatter + 分诊 + 决策点 + 状态可见性 + 委托索引
├── workflows/
│   ├── feature-dev.md             # 需求开发线 10 步剧本
│   └── ops-triage.md              # 运维排查线 10 步剧本（含早退分支）
└── references/
    ├── step-A-api-contract.md     # Apifox 接口契约对齐（3 时点，条件触发）
    ├── step-B-code-locate.md      # 代码定位套路
    ├── step-C-build-test.md       # 专属 Maven 构建自测
    ├── step-D-sql-delegate.md     # 委托 sql-expert-dba
    ├── step-E-commit.md           # git-commit-convention 提交
    └── step-F-triage-report.md    # 根因+影响面+修复建议产出物

~/.claude/skills/biz-workflow → dalwin-workflow/skills/biz-workflow  （软链，使其生效）
```

每个文件单一职责；SKILL.md 是唯一大脑且保持精简（索引式），细节下沉到 workflows/references 按需读取。

---

## Task 1：建目录骨架 + SKILL.md（Router 主体）

**Files:**
- Create: `dalwin-workflow/skills/biz-workflow/SKILL.md`

- [ ] **Step 1：创建目录骨架**

```bash
cd /Users/dalwin/Documents/AI/dalwin-workflow
mkdir -p skills/biz-workflow/workflows skills/biz-workflow/references
```

- [ ] **Step 2：写 SKILL.md（Router）**

写入 `skills/biz-workflow/SKILL.md`，完整内容如下：

````markdown
---
name: biz-workflow
description: >
  业务侧日常工作 SOP 编排器。当用户要做端到端的业务开发或运维排查任务时使用：
  开发需求 / 做这个功能 / 加个接口 / 改字段 / 实现这个原型；
  查工单 / 线上报错排查 / 定位这个 bug / 数据对不上 / 接口异常。
  本 skill 分诊到需求开发线或运维排查线，自动串联代码定位、构建自测、提交、
  接口契约同步等步骤，并在「方案/根因定调」「落库/提交前」两个决策点暂停等用户拍板。
  涉及 SQL 时委托 sql-expert-dba，需结构化设计时委托 spec-architect，
  接口契约用 Apifox。不要用于：纯 SQL 优化/报错（交 sql-expert-dba）、
  纯写 spec 不实现（交 spec-architect）、与业务开发/排查无关的一次性杂活。
---

# biz-workflow · 业务工作流编排器

我是业务侧日常工作的 **SOP 编排器（orchestrator）**，不是执行器。
我负责：分诊、串流程、控决策点、报告进度。专业活我委托给专家：
SQL → `sql-expert-dba`；需求/根因结构化设计 → `spec-architect`；接口契约 → Apifox MCP。

## 第一步：分诊

判断这是哪条线，二选一：

| 输入信号 | 判定 | 加载剧本 |
|----------|------|----------|
| 需求原型 / PRD / "加个功能" / "改成…" / 接口字段变更 | **需求开发线** | 读 `workflows/feature-dev.md` |
| 工单 / 报错堆栈 / 异常日志 / "线上…出问题" / "查为什么…" / 数据对不上 | **运维排查线** | 读 `workflows/ops-triage.md` |
| 模糊 / 两可 | **不猜** | 问用户一句："这是开发需求还是排查问题？" |

分诊只做粗判断；选定后读对应 workflow，按其剧本推进。

## 两个决策点（全局硬约束，任何剧本都必须遵守）

- **★决策点①（方案 / 根因定调）**：自主走完"理解 + 定位"后**必须停**，摊出
  "打算怎么改 / 根因是什么"，等用户拍板。**未经确认不得改代码 / 调 DB**。
  - **归属动态绑定**：若本任务委托了 spec-architect，其 Confirm 即视为①，**不重复问**；
    若未委托（简单任务直接定位），①由我自己把控。
- **★决策点②（落库 / 提交前）**：自测通过后**必须停**，摊出"改了哪些文件 + diff 概要 +
  提交计划"，等用户拍板。**未经确认不得提交 / 写库 / 改文档**。

## 不可逆操作护栏（兜底，额外确认）

除上述两个常规卡点外，凡遇 **删数据 / 改生产配置 / 执行非只读 SQL / push 到远端**
等不可逆操作，**无论在哪一步，一律额外停下显式确认**。

## 状态可见性

每进入一个步骤，先用一行告知用户："现在在 [步骤] · [做什么]"，
让用户随时知道进度、随时可打断。

## 委托速查

| 场景 | 委托对象 | 方式 |
|------|----------|------|
| 涉及 DB（SQL 评审/优化/查数/DDL） | `sql-expert-dba:sql-expert-router` | 显式 invoke，见 `references/step-D-sql-delegate.md` |
| Medium+ 任务需结构化设计/拆解 | `spec-architect` | 显式 invoke，**契约见 `references/step-F-triage-report.md` 邻接的委托说明**与 workflow 内联说明 |
| 接口契约对齐 | Apifox MCP `mcp__apifox-new-mcp__*` | 见 `references/step-A-api-contract.md` |

## 公共步骤（references，按需读取）

- `references/step-A-api-contract.md` — 接口契约对齐（Apifox，条件触发）
- `references/step-B-code-locate.md` — 代码定位套路
- `references/step-C-build-test.md` — 专属 Maven 构建自测
- `references/step-D-sql-delegate.md` — 委托 sql-expert-dba
- `references/step-E-commit.md` — git-commit-convention 提交
- `references/step-F-triage-report.md` — 排查产出物（根因+影响面+修复建议）
````

- [ ] **Step 3：结构校验**

Run:
```bash
cd /Users/dalwin/Documents/AI/dalwin-workflow
test -f skills/biz-workflow/SKILL.md && echo "FILE OK"
head -1 skills/biz-workflow/SKILL.md | grep -q '^---$' && echo "FRONTMATTER START OK"
grep -q '^name: biz-workflow$' skills/biz-workflow/SKILL.md && echo "NAME OK"
grep -q '决策点①' skills/biz-workflow/SKILL.md && grep -q '决策点②' skills/biz-workflow/SKILL.md && echo "DECISION POINTS OK"
grep -q '不可逆操作' skills/biz-workflow/SKILL.md && echo "GUARDRAIL OK"
```
Expected: 全部打印 OK。

- [ ] **Step 4：Commit**

```bash
cd /Users/dalwin/Documents/AI/dalwin-workflow
git add skills/biz-workflow/SKILL.md
git commit -m "feat(biz-workflow): 新增 Router SKILL.md 与目录骨架"
```

---

## Task 2：需求开发线剧本 workflows/feature-dev.md

**Files:**
- Create: `dalwin-workflow/skills/biz-workflow/workflows/feature-dev.md`

- [ ] **Step 1：写 feature-dev.md**

写入完整内容：

````markdown
# 需求开发线 · feature-dev

> 由 SKILL.md 分诊为"需求开发"后读取。按下列步骤推进，遵守 SKILL.md 的两个决策点与护栏。

## 步骤序列

```
1. 分析需求原型               理解要做什么、影响哪些接口/表
   [Medium+ 或用户要求] → 委托 spec-architect（见下方「SDD 委托契约」）产出 spec
2. [改接口?] → step-A         先拉 Apifox 契约当靶子（改接口才执行）
3. step-B 代码定位            Controller→Service→Mapper/SQL 定位改动点
                              （若已走 spec，B 退化为"按 spec 核对定位"）
4. ★决策点①                  摊出实现方案 → 等用户拍板
                              （若走了 spec-architect，①由其 Confirm 承担，不重复问）
   ───────── 以下需经①放行 ─────────
5. 实现改动                   按确认方案改代码
6. [涉及DB?] → step-D         委托 sql-expert-dba 评审/优化
7. step-C 构建自测            专属 Maven 命令编译+跑测
8. ★决策点②                  摊出 diff 概要 + 提交计划 → 等用户拍板
   ───────── 以下需经②放行 ─────────
9. [改接口?] → step-A         提交前核对实现与契约一致
10. step-E 提交               git-commit-convention 生成 message 并提交
```

## 复杂度判定与 SDD 委托

沿用 spec-architect 自身的复杂度判定：

| 复杂度 | 是否委托 spec-architect | 决策点①归属 |
|--------|------------------------|------------|
| Small（加字段/改校验/调查询条件） | 可跳过，直接 step-B | 我自己把控 |
| Medium / Complex（跨模块/多表/迁移/架构变更） | **委托，走 SDD** | spec-architect Confirm 承担 |
| 用户显式说"先写 spec / 先规划" | **强制委托** | 同上 |

## SDD 委托契约（invoke spec-architect 时必须声明）

spec-architect 自身会在产出 spec 后**强制进入编码**（其硬约束#3 + Step 7）。
为不与本编排器的决策点冲突，invoke 时**必须包含**：

1. 任务上下文；
2. **"仅交付 spec，触发 spec-architect 的 B 分支（显式停止），不要 continue-to-coding，
   产出 spec 后交还控制权给 biz-workflow"**；
3. 交还后我把 spec 当"已确认方案输入"，继续 step-B（核对）→ 决策点①（已由其 Confirm
   承担则跳过）→ D/C → 决策点② → E → A。

## 条件触发说明

- **step-A**：仅当改动涉及 Controller 接口/字段变更才执行（前置拉契约 + 提交前核对，两个时点）。
- **step-D**：仅当改动涉及 DB 才执行。
- 不涉及接口 → 整段跳过 A；不涉及 DB → 跳过 D。
````

- [ ] **Step 2：结构与内容校验**

Run:
```bash
cd /Users/dalwin/Documents/AI/dalwin-workflow
F=skills/biz-workflow/workflows/feature-dev.md
test -f $F && echo "FILE OK"
grep -q '决策点①' $F && grep -q '决策点②' $F && echo "DECISION POINTS OK"
grep -q 'B 分支' $F && grep -q 'continue-to-coding' $F && echo "SDD CONTRACT OK"
grep -q 'step-A' $F && grep -q 'step-E' $F && echo "STEPS REF OK"
```
Expected: 全部 OK。

- [ ] **Step 3：Commit**

```bash
cd /Users/dalwin/Documents/AI/dalwin-workflow
git add skills/biz-workflow/workflows/feature-dev.md
git commit -m "feat(biz-workflow): 新增需求开发线剧本 feature-dev"
```

---

## Task 3：运维排查线剧本 workflows/ops-triage.md

**Files:**
- Create: `dalwin-workflow/skills/biz-workflow/workflows/ops-triage.md`

- [ ] **Step 1：写 ops-triage.md**

写入完整内容：

````markdown
# 运维排查线 · ops-triage

> 由 SKILL.md 分诊为"运维排查"后读取。按下列步骤推进，遵守 SKILL.md 的两个决策点与护栏。
> 注意：排查类任务**不强制产生代码提交**——给完结论即可结束（早退分支）。

## 步骤序列

```
1. 分析工单/报错              判断是代码问题还是数据问题
   [根因需结构化设计] → 委托 spec-architect 产出修复 spec（契约同 feature-dev）
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

## 早退分支（排查线特性）

排查任务的**核心交付是 step-F 的结论**（根因 + 影响面 + 修复建议）。
若用户只需结论、不需要立即改代码：在决策点①摊出结论后**即可结束**，
产出物已落 `docs/problem/`，可追溯可复盘。**不强制走到提交。**

## 条件触发说明

- **step-D**：数据问题定位辅助 / 修复涉及 DB，两处都可能触发。
- **step-C / step-E**：仅当真要改代码修复才走；纯结论型排查不碰。
- **step-A**：仅当修复**动到了 Controller 接口**才在收尾回归同步 Apifox 文档。

## SDD 委托契约

与 feature-dev 相同：invoke spec-architect 时必须声明"仅交付 spec、触发 B 分支显式停止、
不要 continue-to-coding、产出后交还控制权"。详见 feature-dev.md 的「SDD 委托契约」。
````

- [ ] **Step 2：结构与内容校验**

Run:
```bash
cd /Users/dalwin/Documents/AI/dalwin-workflow
F=skills/biz-workflow/workflows/ops-triage.md
test -f $F && echo "FILE OK"
grep -q '早退分支' $F && echo "EARLY EXIT OK"
grep -q 'step-F' $F && grep -q 'docs/problem' $F && echo "REPORT OK"
grep -q 'Controller 接口' $F && echo "API REGRESS OK"
```
Expected: 全部 OK。

- [ ] **Step 3：Commit**

```bash
cd /Users/dalwin/Documents/AI/dalwin-workflow
git add skills/biz-workflow/workflows/ops-triage.md
git commit -m "feat(biz-workflow): 新增运维排查线剧本 ops-triage"
```

---

## Task 4：reference 步骤 A/B（接口契约 + 代码定位）

**Files:**
- Create: `dalwin-workflow/skills/biz-workflow/references/step-A-api-contract.md`
- Create: `dalwin-workflow/skills/biz-workflow/references/step-B-code-locate.md`

- [ ] **Step 1：写 step-A-api-contract.md**

````markdown
# step-A · 接口契约对齐（Apifox MCP，条件触发）

> **触发条件**：仅当改动涉及 Controller 接口 / 字段变更。不涉及接口则整段跳过。

## 三个时点

| 时点 | 线 | 动作 |
|------|----|----|
| 前置 | 需求线（进 step-B 前） | 从 Apifox 拉 OpenAPI / 字段 / 用例，当作实现靶子 |
| 提交前 | 需求线（进 step-E 前） | 核对实现与契约是否一致；不一致先对齐再提交 |
| 收尾 | 排查线（step-E 后） | 反向更新 Apifox 文档，防文档腐化 |

## 委托对象

Apifox MCP 工具族 `mcp__apifox-new-mcp__*`，常用：
- `listOpenApiEndpoints` / `getOpenApiDetails` / `getHttpEndpoint` — 拉契约与字段
- `listTestCases` / `getTestCase` — 拉用例
- `updateHttpEndpoint` / `createHttpEndpoint` — 收尾回写文档（属"改文档"，需经决策点②或额外确认）

## 注意

- 回写 Apifox 文档（update/create）属于对外产物变更，须在决策点②已确认或额外确认后再做。
- 若 Apifox MCP 当前不可用，提示用户手动核对，不阻塞主流程。
````

- [ ] **Step 2：写 step-B-code-locate.md**

````markdown
# step-B · 代码定位套路

## 需求线定位

自顶向下沿调用链定位改动点：

```
Controller（入口/参数/返回）
  → Service（业务逻辑/事务边界）
    → Mapper / XML / SQL（数据访问）
```

先找接口对应的 Controller 方法，再顺着 Service 调用链找到要改的逻辑点与数据访问点。

## 排查线定位

- **有报错堆栈**：从堆栈最顶层业务类逐层下钻，定位抛异常的真实位置（区分框架栈与业务栈）。
- **无堆栈、按现象**：从现象涉及的接口/功能入口反查，结合日志关键字搜索。

## 与 spec-architect 的关系

若本任务已委托 spec-architect，spec 内已含勘察定位结论，
step-B **退化为"按 spec 列出的文件/改动点核对"**，不重复勘察。

## 工具

- 优先用项目内搜索（Grep/Glob）按类名、方法名、SQL 片段、报错关键字定位。
- 大范围、不确定命中位置时，可派 Explore/general-purpose 子代理并行检索。
````

- [ ] **Step 3：校验**

Run:
```bash
cd /Users/dalwin/Documents/AI/dalwin-workflow
A=skills/biz-workflow/references/step-A-api-contract.md
B=skills/biz-workflow/references/step-B-code-locate.md
test -f $A && test -f $B && echo "FILES OK"
grep -q 'mcp__apifox-new-mcp__' $A && echo "APIFOX TOOL OK"
grep -q 'Controller' $B && grep -q 'spec' $B && echo "LOCATE OK"
```
Expected: 全部 OK。

- [ ] **Step 4：Commit**

```bash
cd /Users/dalwin/Documents/AI/dalwin-workflow
git add skills/biz-workflow/references/step-A-api-contract.md skills/biz-workflow/references/step-B-code-locate.md
git commit -m "feat(biz-workflow): 新增 step-A 接口契约与 step-B 代码定位"
```

---

## Task 5：reference 步骤 C/D（构建自测 + SQL 委托）

**Files:**
- Create: `dalwin-workflow/skills/biz-workflow/references/step-C-build-test.md`
- Create: `dalwin-workflow/skills/biz-workflow/references/step-D-sql-delegate.md`

- [ ] **Step 1：写 step-C-build-test.md**

> 注：以下 Maven 路径取自 `dalwin-workflow/context/java-spring.md`。

````markdown
# step-C · 专属 Maven 构建自测

> **触发条件**：有代码改动需要本地编译/自测时。

## 硬约束：绝不使用 `~/.m2`

本地 Maven 仓库**不在** `~/.m2`。执行任何 `mvn` 命令必须附加专属参数：

```bash
mvn -s /Users/dalwin/Library/ConfigFile/maven/saas/settings.xml \
    -Dmaven.repo.local=/Users/dalwin/Library/Repository <goal>
```

常用 goal：`compile`（编译）、`test`（跑测）、`-pl <module> -am`（指定模块）。

## 查找 / 解压依赖 jar

同样走专属仓库，**不用 `~/.m2`**：

- 查找：`find /Users/dalwin/Library/Repository -name "*.jar" ...`
- 解压：`jar tf|xf /Users/dalwin/Library/Repository/...`

## 自测策略

- 优先跑改动相关的最小测试集（按模块/测试类），不必全量。
- 编译失败或测试失败 → 回到实现步骤修复，不要带病提交。
````

- [ ] **Step 2：写 step-D-sql-delegate.md**

````markdown
# step-D · 委托 sql-expert-dba（条件触发）

> **触发条件**：改动涉及 DB —— SQL 评审、优化、查数、DDL。

## 委托方式

**显式 invoke** 已安装的 `sql-expert-dba:sql-expert-router`（总入口分诊），由其路由到子专家：
- SQL 报错 → sql-error-diagnostician
- 慢查询/执行计划/索引 → sql-query-optimizer
- 建表/DDL/Schema 评审 → sql-schema-reviewer
- 业务统计/报表 SQL → sql-report-query-builder

**不在 biz-workflow 内重写 SQL 能力**（DRY）。把任务上下文（涉及哪些表、什么操作、
是评审还是查数）交给 router，由它接管 SQL 专业流程，完成后返回结论。

## 两处可能触发

- **定位辅助**（排查线 step-2）：数据问题时委托查数/诊断，帮助定位根因。
- **改动评审**（两条线的实现后）：改了 SQL/DDL 时委托评审或优化。

## 护栏衔接

sql-expert-dba 产出的若是**非只读 SQL / DDL**，执行它属于不可逆操作，
须经决策点②或额外确认后再落库。
````

- [ ] **Step 3：校验**

Run:
```bash
cd /Users/dalwin/Documents/AI/dalwin-workflow
C=skills/biz-workflow/references/step-C-build-test.md
D=skills/biz-workflow/references/step-D-sql-delegate.md
test -f $C && test -f $D && echo "FILES OK"
grep -q 'maven.repo.local=/Users/dalwin/Library/Repository' $C && echo "MAVEN PATH OK"
grep -q '绝不使用' $C && echo "M2 GUARD OK"
grep -q 'sql-expert-router' $D && echo "DELEGATE OK"
```
Expected: 全部 OK。

- [ ] **Step 4：Commit**

```bash
cd /Users/dalwin/Documents/AI/dalwin-workflow
git add skills/biz-workflow/references/step-C-build-test.md skills/biz-workflow/references/step-D-sql-delegate.md
git commit -m "feat(biz-workflow): 新增 step-C 构建自测与 step-D SQL 委托"
```

---

## Task 6：reference 步骤 E/F（提交 + 排查产出物）

**Files:**
- Create: `dalwin-workflow/skills/biz-workflow/references/step-E-commit.md`
- Create: `dalwin-workflow/skills/biz-workflow/references/step-F-triage-report.md`

- [ ] **Step 1：写 step-E-commit.md**

> 注：commit 格式取自 `~/.claude/git-commit-convention.txt`。

````markdown
# step-E · git 提交（git-commit-convention）

> **触发条件**：有代码改动且已通过决策点②。

## 提交规范

格式：`<type>(<scope>): <subject>`（冒号后有空格，subject 用中文简短描述）。

type：feat / fix / docs / style / refactor / perf / test / chore / revert / build
scope（选填）：作用范围或目录名。

示例：
- `feat(order): 增加订单导出分页参数`
- `fix(auth): 修复登录空指针`

## 流程

1. 在决策点②已向用户摊出 diff 概要与提交计划并获确认。
2. `git add <相关文件>`（只 add 本次改动文件，不裹挟无关变更）。
3. `git commit -m "<规范 message>"`。
4. **不自动 push**——push 属不可逆操作，需用户额外确认后才执行。
5. pre-commit hook 报错时：向用户报告并停止，不加 `--no-verify` 跳钩。
````

- [ ] **Step 2：写 step-F-triage-report.md**

````markdown
# step-F · 排查产出物（根因 + 影响面 + 修复建议）

> **仅排查线**。这是排查任务的**核心交付**——很多排查到此即结束（早退分支）。

## 产出格式

```markdown
# [问题简述] 排查结论

## 根因
[定位到的真实原因，含代码位置 file:line / 数据现象]

## 影响面
[受影响的接口/功能/数据范围；是否影响线上；严重程度]

## 修复建议
[具体改法；若涉及 DB 列出 SQL 思路；风险与回滚要点]

## 验证方式
[如何确认修复有效]
```

## 落盘

写入 `docs/problem/`（沿用现有目录习惯），文件名体现问题主题，便于追溯与复盘。
若该目录在当前工作仓库不存在，按用户实际项目结构落到对应的问题记录目录，
或先询问落盘位置。

## 与决策点的关系

产出结论后进入**决策点①**：摊出根因与修复方案等用户拍板。
用户若只需结论 → 结束；若需修复 → 继续步骤 5+。
````

- [ ] **Step 3：校验**

Run:
```bash
cd /Users/dalwin/Documents/AI/dalwin-workflow
E=skills/biz-workflow/references/step-E-commit.md
F=skills/biz-workflow/references/step-F-triage-report.md
test -f $E && test -f $F && echo "FILES OK"
grep -q '不自动 push' $E && echo "NO PUSH OK"
grep -q '<type>(<scope>): <subject>' $E && echo "COMMIT FMT OK"
grep -q '根因' $F && grep -q '影响面' $F && grep -q '修复建议' $F && echo "REPORT FMT OK"
```
Expected: 全部 OK。

- [ ] **Step 4：Commit**

```bash
cd /Users/dalwin/Documents/AI/dalwin-workflow
git add skills/biz-workflow/references/step-E-commit.md skills/biz-workflow/references/step-F-triage-report.md
git commit -m "feat(biz-workflow): 新增 step-E 提交与 step-F 排查产出物"
```

---

## Task 7：软链生效 + 整体结构校验

**Files:**
- Create（软链）: `~/.claude/skills/biz-workflow` → 仓库内 `skills/biz-workflow`
- Modify: `dalwin-workflow/archived_skills/README.md`（登记本软链，沿用现有登记习惯）
- Modify: `dalwin-workflow/README.md`（在目录说明中加一行 skills/）

- [ ] **Step 1：建软链使 skill 生效**

```bash
ln -s /Users/dalwin/Documents/AI/dalwin-workflow/skills/biz-workflow /Users/dalwin/.claude/skills/biz-workflow
```

- [ ] **Step 2：验证软链与整体结构**

Run:
```bash
ls -l /Users/dalwin/.claude/skills/biz-workflow | grep -q 'dalwin-workflow/skills/biz-workflow' && echo "SYMLINK OK"
test -f /Users/dalwin/.claude/skills/biz-workflow/SKILL.md && echo "SKILL VIA LINK OK"
# 9 个文件齐全
cd /Users/dalwin/Documents/AI/dalwin-workflow
N=$(find skills/biz-workflow -name '*.md' | wc -l | tr -d ' ')
echo "MD FILES = $N (expect 9)"
```
Expected: `SYMLINK OK` / `SKILL VIA LINK OK` / `MD FILES = 9`。

- [ ] **Step 3：frontmatter 合法性检查（所有 SKILL.md 必须能被解析）**

Run:
```bash
cd /Users/dalwin/Documents/AI/dalwin-workflow
# SKILL.md 必须以 --- 开头、含 name 与 description
awk 'NR==1{if($0!="---"){print "BAD: no frontmatter"; exit 1}} /^name:/{n=1} /^description:/{d=1} END{if(n&&d) print "FRONTMATTER OK"; else {print "BAD frontmatter"; exit 1}}' skills/biz-workflow/SKILL.md
```
Expected: `FRONTMATTER OK`。

- [ ] **Step 4：登记软链到 archived_skills/README.md**

在 `archived_skills/README.md` 末尾追加一节（archived_skills 是仓库内软链登记习惯地，复用之）：

```markdown

## 现役自建 skill 软链（非 archive，仅登记）

| Skill | 源码 SOT（本仓库） | 生效软链命令 |
|---|---|---|
| biz-workflow | `dalwin-workflow/skills/biz-workflow` | `ln -s /Users/dalwin/Documents/AI/dalwin-workflow/skills/biz-workflow ~/.claude/skills/biz-workflow` |

> 可选：若要让 codex 也发现，另建 `ln -s <SOT> ~/.agents/skills/biz-workflow`。
```

- [ ] **Step 5：更新仓库 README.md 目录说明**

在 `README.md` 的"## 目录"列表中，`archived_skills` 条目下方加一行：

```markdown
- `skills/` — 自建现役 skill 的源码 SOT（如 `biz-workflow`），经软链注入 `~/.claude/skills/` 生效
```

- [ ] **Step 6：Commit**

```bash
cd /Users/dalwin/Documents/AI/dalwin-workflow
git add archived_skills/README.md README.md
git commit -m "docs(biz-workflow): 登记软链并更新仓库目录说明"
```

---

## Task 8：触发与流程演练（最终验收）

> 这是替代 TDD 的端到端验收。无代码可断言，故用真实场景演练验证 skill 行为正确。
> 此任务由用户在**新会话**执行（当前会话已加载大量上下文，不能客观验证语义触发）。

**Files:** 无（验收任务）

- [ ] **Step 1：触发命中验证（需求线）**

在新 Claude Code 会话输入类似："帮我给订单列表接口加个分页参数"。
**预期**：biz-workflow 被语义命中并启动，分诊为"需求开发线"，
报告进入流程，在改代码前停在决策点①。
**不预期**：直接开始改代码而不分诊/不停决策点。

- [ ] **Step 2：触发命中验证（排查线）**

新会话输入类似："线上这个订单查询接口报 NPE，帮我排查下"。
**预期**：分诊为"运维排查线"，先定位→产出 step-F 结论→停在决策点①，
且允许"只要结论"的早退。

- [ ] **Step 3：边界不抢活验证**

新会话输入纯 SQL 场景："帮我优化这条慢 SQL `SELECT ...`"。
**预期**：命中 `sql-expert-dba` 而非 biz-workflow（biz-workflow 的 description 已声明让位）。
若 biz-workflow 误抢 → 记录并回到 Task 1 收紧 description。

- [ ] **Step 4：决策点护栏验证**

在一个真实小需求上跑完整流程，确认：
- 决策点①、②确实暂停等待用户；
- 出现不可逆操作（如 push、非只读 SQL）时额外确认；
- 委托 spec-architect 时它止于 spec 未擅自编码（若触发了 Medium+ 路径）。

- [ ] **Step 5：记录演练结果**

把演练中发现的偏差（触发不准 / 决策点失效 / 委托越权等）记录到
`docs/problem/` 或直接迭代修正对应文件。skill 类改动遵循"先落一版、用中迭代"。

---

## Self-Review（计划自检）

**Spec 覆盖核对**（逐节对照 `2026-06-09-biz-workflow-orchestrator-design.md`）：

- §2 形态/部署（纯 Skill + 软链 + spec-architect name-only 前置）→ Task 1（frontmatter）、Task 7（软链）、Task 8 备注 ✔
- §3 文件结构（9 文件）→ Task 1–6 逐一创建，Task 7 校验 9 文件 ✔
- §4 Router（分诊/决策点/护栏/状态可见性）→ Task 1 SKILL.md 全覆盖 ✔
- §5.1 需求线 10 步 → Task 2 ✔
- §5.2 排查线 10 步 + 早退 → Task 3 ✔
- §5.3 两线差异（A 位置/F 核心/C-E 条件/D 两次）→ Task 2/3 条件触发说明 + Task 4–6 reference ✔
- §6.1–6.6 六个 reference → Task 4/5/6 ✔
- §6' spec-architect 委托契约（止于 spec/B 分支/交还/①去重）→ Task 2 SDD 委托契约 + Task 3 引用 ✔
- §7 description 触发策略（命中+让位）→ Task 1 frontmatter description + Task 8 Step 3 边界验证 ✔
- §8 决策汇总 → 全计划贯彻 ✔

**Placeholder 扫描**：无 TBD/TODO；每个文件给出完整 Markdown 内容；每个校验给出具体命令与预期 ✔

**一致性核对**：
- 文件名 step-A..F 在 SKILL.md「公共步骤」、两个 workflow、各 reference 文件名间一致 ✔
- 委托对象名 `sql-expert-dba:sql-expert-router`、`spec-architect`、`mcp__apifox-new-mcp__*` 前后一致 ✔
- Maven 路径与 commit 格式分别取自 `context/java-spring.md` 与 `git-commit-convention.txt`，未杜撰 ✔
- 决策点①归属规则在 SKILL.md 与 feature-dev.md 表述一致（走 spec 由其承担，否则自管）✔

**已知裁剪**：TDD→prompt-skill 三类验证（结构/内容/演练），已在计划顶部「关于测试的说明」声明理由。
