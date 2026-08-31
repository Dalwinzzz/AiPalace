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
