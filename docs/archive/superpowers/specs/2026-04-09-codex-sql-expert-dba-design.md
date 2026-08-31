# SQL Expert DBA 插件设计

## 1. 背景

本次需求是为 Codex 设计并落地一个可长期复用的本地 SQL 专家插件，对标 web 端 GPT 应用中的 SQL Expert（QueryGPT）能力形态，但更贴近个人日常开发与 DBA 助手场景。

该插件的目标不是做数据库执行器，而是做一个稳定、可复用、可沉淀经验的分析型 SQL 助手，服务以下高频工作：

- SQL 查询优化与执行计划分析
- SQL 报错诊断与修复建议
- DDL / Schema / 索引设计评审
- 根据业务需求与现有表结构生成业务 SQL 或临时报表 SQL
- 在不打扰用户的前提下沉淀高价值、可复用的 SQL 经验

## 2. 目标与非目标

### 2.1 目标

v1 目标如下：

1. 以 Codex 本地插件形式提供一个 SQL 专家助手
2. 以多工作流方式支持 5 类核心任务：
   - 总入口分诊
   - 查询优化
   - 报错诊断
   - Schema / DDL 评审
   - 业务 SQL 生成
3. 优先覆盖跨方言通用能力，并重点兼容 MySQL / PostgreSQL
4. 默认问题解决优先，学习/复盘作为显式可选模式
5. 设计一个插件内部 `memory/` 知识层，支持自动评估与结构化沉淀
6. 在仓库内开发，在用户级目录安装，形成个人长期可用工具

### 2.2 非目标

以下内容明确不属于 v1：

- 直接连接数据库
- 执行 SQL 或变更数据库对象
- 提供 MCP server
- 提供专用 App 或 UI 面板
- 自动沉淀原始长对话
- 无边界地自动学习所有会话内容

## 3. 总体定位

### 3.1 产品定位

该插件定位为“分析型 DBA 助手”，而不是“数据库连接工具”。

它负责：

- 理解 SQL、DDL、报错、执行计划、业务统计需求
- 基于结构化分析给出建议或生成结果
- 以 workflow 为单位稳定输出
- 在后台评估哪些经验值得沉淀

它不负责：

- 查询真实数据库元数据
- 验证 SQL 是否实际可跑
- 在用户未授权情况下生成危险写操作 SQL

### 3.2 全局原则

所有 workflow 都必须遵守以下原则：

- 区分 `已确认` 与 `推断`
- 输入不足时先指出缺口，不伪造确定性
- 默认问题解决优先，不默认展开教学
- 仅当用户明确要求学习/复盘时，才输出知识化解释
- 默认只生成只读 SQL
- `memory/` 只沉淀结构化结论，不沉淀原始长对话

## 4. 插件架构

### 4.1 结构分层

插件采用以下 5 层结构：

1. `plugin manifest`
2. `skills`
3. `scripts`
4. `memory`
5. `assets`

分层职责如下：

- `plugin manifest`：插件元信息、展示信息、默认入口提示
- `skills`：5 个专家 workflow 与共享规则
- `scripts`：memory 检索、沉淀、索引维护
- `memory`：结构化知识资产
- `assets`：图标与基础展示素材

### 4.2 v1 插件目录

仓库内开发目录固定为：

- `plugins/sql-expert-dba/`

建议目录结构如下：

```text
plugins/sql-expert-dba/
├── .codex-plugin/
│   └── plugin.json
├── skills/
│   ├── sql-expert-router/
│   │   └── SKILL.md
│   ├── sql-query-optimizer/
│   │   └── SKILL.md
│   ├── sql-error-diagnostician/
│   │   └── SKILL.md
│   ├── sql-schema-reviewer/
│   │   └── SKILL.md
│   ├── sql-report-query-builder/
│   │   └── SKILL.md
│   └── _shared/
│       ├── output-contract.md
│       ├── missing-input-checklists.md
│       ├── memory-policy.md
│       └── dialect-guidelines.md
├── scripts/
│   ├── memory_search.py
│   ├── memory_capture.py
│   └── memory_index.py
├── memory/
│   ├── README.md
│   ├── index.json
│   ├── glossary/
│   ├── rules/
│   ├── cases/
│   ├── candidates/
│   └── templates/
└── assets/
    ├── icon.png
    └── logo.png
```

### 4.3 v1 明确不创建的内容

以下结构不进入本次实现：

- `.mcp.json`
- `.app.json`
- `hooks/`
- 数据库连接配置
- SQL 执行脚本
- 自动化截图集

## 5. 五类专家工作流

### 5.1 `sql-expert-router`

职责：

- 判断当前问题属于哪类 workflow
- 判断是否需要串联多个 workflow
- 指出关键缺失输入

不负责深度分析，只负责分诊与编排。

输出应至少包含：

- `primary_workflow`
- `secondary_workflow`（如有）
- `missing_inputs`
- `recommended_next_step`

### 5.2 `sql-query-optimizer`

职责：

- 分析现有 SQL
- 给出 SQL 改写建议
- 给出索引建议
- 解读 EXPLAIN / 执行计划
- 指出 MySQL / PostgreSQL 性能差异风险

建议输入：

- SQL 原文
- 方言
- 表结构 / 索引定义
- EXPLAIN / 执行计划
- 数据量级
- 优化目标

没有 EXPLAIN / 索引信息时，只能输出保守的静态分析结论。

### 5.3 `sql-error-diagnostician`

职责：

- 分析 SQL 报错
- 解释错误类型
- 给出根因排序
- 给出修复路径
- 指出跨方言兼容性风险

建议输入：

- 报错全文或错误码
- 触发 SQL
- 方言
- 相关 DDL

没有报错全文或 SQL 时，不允许给出伪确定性的根因。

### 5.4 `sql-schema-reviewer`

职责：

- 评审表结构设计
- 提出索引与约束建议
- 指出高优先级结构风险
- 解释规范化与性能之间的取舍

建议输入：

- DDL
- 业务目标
- 主要查询场景
- 数据规模

没有业务场景时，只能给出保守的通用评审结论。

### 5.5 `sql-report-query-builder`

职责：

- 根据业务需求与现有 DDL 生成业务 SQL
- 处理复杂、临时性、报表型统计 SQL 场景
- 在必要时串联优化 workflow 继续调优

典型场景：

- 临时报表查询
- 复杂业务统计 SQL
- 对账与排查 SQL
- 根据业务口径生成汇总 SQL

建议输入：

- 业务需求描述
- 指标定义
- 粒度
- 时间范围
- 去重规则
- DDL / 表关系
- 方言

关键口径不明确时，必须先反问；只有需求澄清后才输出最终 SQL。

## 6. 工作流之间的协同关系

支持以下固定串联链路：

1. `sql-report-query-builder -> sql-query-optimizer`
2. `sql-error-diagnostician -> sql-query-optimizer`
3. `sql-schema-reviewer -> sql-report-query-builder`
4. `sql-schema-reviewer -> sql-query-optimizer`

协同原则：

- `router` 决定是否串联
- 每个 workflow 只对自己的阶段负责
- 不允许单个 skill 包揽全部职责

## 7. 统一输入输出契约

所有 workflow 统一采用以下输出骨架：

1. `任务判断`
2. `已确认`
3. `待确认 / 推断`
4. `主输出`
5. `验证建议`
6. `可选学习补充`

这套契约的目标是：

- 统一用户体验
- 降低 prompt 输出风格漂移
- 把“事实”和“推断”显式拆开
- 保持问题解决优先的输出重心

## 8. Memory 设计

### 8.1 定位

`memory/` 是插件内部约定的数据层，不是 Codex 插件系统原生自动识别的 memory 能力。

它必须由插件内的 skills / scripts 显式读写与维护。

### 8.2 硬约束

`memory/` 必须遵守以下硬约束：

- 只沉淀结构化结论
- 不沉淀原始长对话
- 不沉淀未经验证的猜测
- 不沉淀无法去敏的业务细节
- 不沉淀纯一次性临时查询上下文

### 8.3 目录职责

- `glossary/`：术语、指标口径、跨方言基础概念
- `rules/`：稳定规则类知识
- `cases/`：高价值案例卡片
- `candidates/`：待治理候选知识
- `templates/`：高复用分析与报表模板
- `index.json`：供脚本检索的轻量索引

### 8.4 单条记忆字段

每条记忆建议采用 `Markdown + YAML front matter` 形式，最少包含：

- `id`
- `title`
- `type`
- `workflow`
- `dialect`
- `tags`
- `problem_pattern`
- `preconditions`
- `conclusion`
- `boundaries`
- `example`
- `anti_example`
- `confidence`
- `review_status`
- `last_reviewed_at`
- `origin_skill`
- `capture_mode`

其中：

- `type`：`rule` / `case` / `template` / `glossary`
- `review_status`：`candidate` / `approved`
- `capture_mode`：`auto_background` / `explicit_user_requested`

## 9. Memory 生命周期

### 9.1 默认后台模式

每次专家 workflow 完成主任务后，后台自动执行一次记忆评估。

该流程默认不打断用户、不强制显式确认。

后台评估结果仅有三种：

1. 丢弃
2. 静默写入 `candidate`
3. 静默写入 `approved`

### 9.2 显式沉淀模式

当用户明确提出：

- “这个值得沉淀”
- “帮我复盘”
- “记下来”

插件再将沉淀过程显式展示给用户，并输出结构化沉淀结果。

### 9.3 评估流程

后台评估固定执行以下步骤：

1. 完成当前主任务
2. 执行价值评估
3. 执行结构化归一
4. 执行去敏
5. 执行去重
6. 写入 `candidate` 或 `approved`
7. 更新 `memory/index.json`

### 9.4 沉淀判定标准

只有同时满足以下硬门槛，才允许进入 memory：

- 可复用
- 有证据
- 有边界
- 可结构化
- 可去敏

在满足硬门槛的基础上，以下信号可提升沉淀优先级：

- 高频问题
- 非直觉陷阱
- 跨方言差异
- 报表统计口径模板
- 明显节省未来排查时间的经验

### 9.5 正式入库约束

默认只消费 `approved` 记忆。

后台自动直接写入 `approved` 只适用于：

- 高通用性规则
- 稳定错误模式
- 高复用模板
- 边界清晰的跨方言规则
- 通用索引/优化规则

其他内容即使有价值，也优先写入 `candidate`。

## 10. Scripts 职责

### 10.1 `memory_search.py`

负责按以下维度检索现有 memory：

- workflow
- dialect
- tags
- problem pattern

### 10.2 `memory_capture.py`

负责执行记忆沉淀相关逻辑：

- 价值判断
- 字段归一
- 去敏
- 去重
- 分流写入 `candidate` / `approved`

### 10.3 `memory_index.py`

负责：

- 构建 `memory/index.json`
- 增量更新索引
- 保证 memory 检索效率与一致性

## 11. Manifest 设计

### 11.1 基础定义

建议 manifest 使用以下产品定义：

- `name`: `sql-expert-dba`
- `displayName`: `SQL Expert DBA`
- `shortDescription`: `SQL 优化、报错定位、DDL 评审与业务 SQL 生成助手`
- `longDescription`: `面向 MySQL/PostgreSQL 与通用 SQL 场景的分析型 DBA 助手，支持查询优化、报错诊断、Schema 评审、业务报表 SQL 生成，并带有结构化经验沉淀能力。`
- `developerName`: `dalwin`
- `category`: `Programming`

### 11.2 默认 starter prompts

starter prompts 固定保留 3 条：

1. `优化这条 SQL，并指出性能瓶颈和索引建议`
2. `解释这段 SQL 报错，并给出最可能的修复方案`
3. `根据业务需求和表结构生成统计 SQL，再帮我检查口径`

### 11.3 关键词

建议关键词包括：

- `sql`
- `mysql`
- `postgresql`
- `query-optimization`
- `schema-review`
- `reporting-sql`
- `dba`

## 12. 安装与维护策略

### 12.1 开发与安装位置

- 仓库内开发真源：`/Users/dalwin/Documents/AI/plugins/sql-expert-dba`
- 用户级安装目录：`~/plugins/sql-expert-dba`
- 用户级 marketplace：`~/.agents/plugins/marketplace.json`

### 12.2 安装原则

采用“仓库开发 + 用户安装”模式：

- 仓库目录是唯一开发真源
- 用户目录是安装产物
- 不并行维护仓库级 marketplace 作为第二真源

### 12.3 marketplace 策略

用户级 marketplace entry 应包含：

- `name: sql-expert-dba`
- `source.path: ./plugins/sql-expert-dba`
- `policy.installation: AVAILABLE`
- `policy.authentication: ON_INSTALL`
- `category: Programming`

## 13. 安全边界

### 13.1 SQL 生成安全策略

默认只生成只读 SQL，包括：

- `SELECT`
- `WITH / CTE`
- 只读分析查询

以下写操作 SQL 只有在用户显式要求时才允许生成：

- `INSERT`
- `UPDATE`
- `DELETE`
- `ALTER`
- `DROP`
- 其他 DDL / DML

### 13.2 高风险误用防护

插件必须避免以下风险：

- 把推断当成已确认事实
- 把业务口径猜测伪装成最终答案
- 把 MySQL 写法误当作 PostgreSQL 可用写法
- 把 schema 问题误判成 SQL 改写问题
- 把一次性上下文沉淀进正式 memory
- 在未授权前生成危险写 SQL

## 14. 验收标准

v1 至少需要覆盖以下验收场景：

1. 查询优化场景  
   输入 SQL + DDL + 索引 + EXPLAIN，能输出优化建议、改写 SQL 与验证方案

2. 静态优化场景  
   只有 SQL 时，能输出保守建议，并明确哪些只是推断

3. 报错定位场景  
   输入报错全文 + SQL，能输出根因排序与修复路径

4. DDL 评审场景  
   输入 DDL + 业务目标，能输出结构风险、索引建议与边界说明

5. 业务 SQL 生成场景  
   输入需求 + DDL，能先澄清口径，再生成只读 SQL

6. 串联 workflow 场景  
   router 能正确调度“生成 SQL 再优化”等复合任务

7. memory 沉淀场景  
   高价值案例能自动完成评估，并正确进入 `candidate` 或 `approved`

8. memory 防污染场景  
   一次性、不可去敏、口径不清的案例不能进入正式记忆库

### 14.1 通过标准

满足以下条件视为 v1 设计达标：

- 5 个 workflow 边界清晰
- router 能正确分诊
- 各 workflow 有明确缺失信息检查逻辑
- 默认只读 SQL 边界成立
- 业务 SQL 在口径不清时会主动追问
- 输出能稳定区分 `已确认` / `推断`
- memory 自动评估存在且可治理
- starter prompts 覆盖三大高频入口

## 15. 后续实施顺序

建议实施顺序如下：

1. 搭建插件目录与 `plugin.json`
2. 搭建 5 个 skill 骨架与共享规则文件
3. 搭建 `memory/` 目录、模板与索引结构
4. 实现 `memory_search.py`、`memory_capture.py`、`memory_index.py`
5. 完善 5 个 workflow 的 prompt 与输入输出契约
6. 本地安装插件并做 workflow 验收
7. 根据试用结果再决定是否进入下一阶段扩展

## 16. 结论

本次方案确定将 SQL Expert DBA 插件设计为一个分析型、多 workflow、可沉淀经验的本地 Codex 插件。

其核心价值不在于“会回答 SQL 问题”，而在于：

- 以稳定 workflow 提供专业能力
- 以结构化 `memory/` 积累长期可复用经验
- 以保守安全边界避免误导与误用
- 为后续扩展数据库只读分析能力保留清晰接口
