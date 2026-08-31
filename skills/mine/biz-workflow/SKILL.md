---
name: biz-workflow
description: >
  （⚠️ 已被 ownerpowers 取代，验证期保留为对照；公司项目新任务优先走 ownerpowers，
  本 skill 仅在用户显式 invoke 时使用。）
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
| Medium+ 任务需结构化设计/拆解 | `spec-architect` | 显式 invoke，契约见 workflow 内联的「SDD 委托契约」 |
| 接口契约对齐 | Apifox MCP `mcp__apifox-new-mcp__*` | 见 `references/step-A-api-contract.md` |

## 公共步骤（references，按需读取）

- `references/step-A-api-contract.md` — 接口契约对齐（Apifox，条件触发）
- `references/step-B-code-locate.md` — 代码定位套路
- `references/step-C-build-test.md` — 专属 Maven 构建自测
- `references/step-D-sql-delegate.md` — 委托 sql-expert-dba
- `references/step-E-commit.md` — git-commit-convention 提交
- `references/step-F-triage-report.md` — 排查产出物（根因+影响面+修复建议）
