# 方言指南

本文件定义 SQL Expert DBA 插件在处理不同 SQL 方言时的规则和参考。

## 默认方言策略

1. 用户未指定方言时，**先询问而非猜测**
2. 如果 SQL 中存在明确的方言特征，可推断并标注 `[推断]`
3. 无法判断时，优先输出标准 ANSI SQL

### 方言推断信号

| 信号 | 推断方言 |
|------|---------|
| `LIMIT` + `OFFSET`（无 `FETCH`）| MySQL `[推断]` |
| `IFNULL()` | MySQL `[推断]` |
| `AUTO_INCREMENT` | MySQL `[推断]` |
| `ENGINE=InnoDB` | MySQL `已确认` |
| `ILIKE` | PostgreSQL `[推断]` |
| `SERIAL` / `BIGSERIAL` | PostgreSQL `[推断]` |
| `RETURNING` | PostgreSQL `[推断]` |
| `::` 类型转换 | PostgreSQL `[推断]` |
| `NOW()` | 两者皆有，无法判断 |

## MySQL vs PostgreSQL 核心差异速查

### 数据类型

| 用途 | MySQL | PostgreSQL | 注意事项 |
|------|-------|-----------|---------|
| 自增主键 | `BIGINT AUTO_INCREMENT` | `BIGINT GENERATED ALWAYS AS IDENTITY` | PG 不推荐 `SERIAL`（新项目） |
| 时间戳 | `DATETIME` / `TIMESTAMP` | `TIMESTAMP` / `TIMESTAMPTZ` | MySQL TIMESTAMP 有 2038 年问题 |
| 布尔 | `TINYINT(1)` | `BOOLEAN` | MySQL 无原生布尔 |
| JSON | `JSON`（实际存 TEXT） | `JSON` / `JSONB` | PG JSONB 支持索引，MySQL JSON 不支持 |
| 枚举 | `ENUM('a','b')` | `CREATE TYPE ... AS ENUM` | PG 枚举是独立类型 |
| 文本 | `VARCHAR` / `TEXT` | `VARCHAR` / `TEXT` | PG TEXT 无性能差异，MySQL TEXT 有限制 |

### 函数差异

| 用途 | MySQL | PostgreSQL |
|------|-------|-----------|
| 空值替换 | `IFNULL(a, b)` | `COALESCE(a, b)` |
| 日期格式化 | `DATE_FORMAT(d, '%Y-%m-%d')` | `TO_CHAR(d, 'YYYY-MM-DD')` |
| 字符串拼接 | `CONCAT(a, b)` | `a \|\| b` 或 `CONCAT(a, b)` |
| 条件聚合 | `IF(cond, val, null)` | `CASE WHEN cond THEN val END` |
| 分页 | `LIMIT n OFFSET m` | `LIMIT n OFFSET m` 或 `FETCH FIRST n ROWS` |
| 当前时间 | `NOW()` | `NOW()` / `CURRENT_TIMESTAMP` |
| 随机数 | `RAND()` | `RANDOM()` |
| 正则匹配 | `REGEXP` | `~` / `~*` |

### 索引差异

| 特性 | MySQL (InnoDB) | PostgreSQL |
|------|---------------|-----------|
| 覆盖索引 | 支持（聚簇索引 + 二级索引） | 支持（INCLUDE 子句，PG 11+） |
| 部分索引 | 不支持 | `CREATE INDEX ... WHERE ...` |
| 表达式索引 | 不支持（5.7），支持（8.0+） | 完全支持 |
| GIN 索引 | 不支持 | 支持（全文、JSON、数组） |
| 哈希索引 | 不推荐（8.0 前不可靠） | 支持 |
| 索引并发创建 | `ALTER TABLE ... ALGORITHM=INPLACE` | `CREATE INDEX CONCURRENTLY` |

### EXPLAIN 输出差异

| 维度 | MySQL | PostgreSQL |
|------|-------|-----------|
| 基本命令 | `EXPLAIN SELECT ...` | `EXPLAIN SELECT ...` |
| 实际执行 | `EXPLAIN ANALYZE` (8.0.18+) | `EXPLAIN ANALYZE` |
| 关键指标 | type, key, rows, Extra | Node type, cost, actual time, rows |
| 全表扫描标志 | `type: ALL` | `Seq Scan` |
| 索引扫描标志 | `type: ref/range/index` | `Index Scan` / `Index Only Scan` |
| 排序标志 | `Extra: Using filesort` | `Sort` 节点 |
| 临时表标志 | `Extra: Using temporary` | `HashAggregate` / `Sort` + `Materialize` |

### 锁与并发

| 特性 | MySQL (InnoDB) | PostgreSQL |
|------|---------------|-----------|
| 默认隔离级别 | REPEATABLE READ | READ COMMITTED |
| 间隙锁 | 有（Gap Lock） | 无 |
| MVCC 实现 | undo log | 多版本元组 |
| 死锁检测 | 自动（innodb_deadlock_detect） | 自动（deadlock_timeout） |
| 锁等待超时 | `innodb_lock_wait_timeout` | `lock_timeout` |
| DDL 锁 | 大部分 DDL 锁表 | 部分 DDL 可并发（CONCURRENTLY） |

## 跨方言风险标注规则

当分析结果中包含方言特定的语法或行为时，必须按以下规则标注：

1. **方言特定语法**：标注 `⚠️ 此写法仅适用于 {dialect}`
2. **行为差异**：标注 `⚠️ MySQL 与 PostgreSQL 在此行为不同：{具体差异}`
3. **隐式转换差异**：标注 `⚠️ 隐式类型转换规则因方言而异`
4. **函数不兼容**：标注 `⚠️ 此函数为 {dialect} 专有，跨方言替代方案：{替代}`

## ANSI SQL 优先原则

在以下情况下优先输出标准 ANSI SQL：

1. 用户未指定方言
2. SQL 可用标准语法等价表达
3. 跨方言兼容性是用户的显式需求

ANSI SQL 优先 **不适用于** 性能优化建议 — 优化建议必须基于特定方言的执行引擎特性。
