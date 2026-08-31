---
id: glossary-001
title: 覆盖索引 (Covering Index)
type: glossary
workflow: sql-query-optimizer
dialect: universal
tags: [index, performance, query-optimization]
problem_pattern: 查询需要回表获取额外字段时考虑覆盖索引
preconditions: 查询的 SELECT 字段较少且相对固定
conclusion: 当查询所需的所有列都包含在索引中时，数据库可直接从索引获取数据而无需回表，显著减少 IO
boundaries: 不适用于 SELECT * 或字段频繁变化的查询；索引列过多会增加写入开销
example: "CREATE INDEX idx_covering ON orders(user_id, status, created_at)"
anti_example: 在频繁更新的宽表上为每种查询都建覆盖索引
confidence: high
review_status: approved
last_reviewed_at: 2026-04-09
origin_skill: manual
capture_mode: explicit_user_requested
---

# 覆盖索引 (Covering Index)

## 定义

覆盖索引是指一个索引包含了查询所需的所有列，使得数据库引擎可以仅通过索引就完成查询，无需回表读取数据行。

## 适用场景

- 高频查询且 SELECT 字段固定
- 查询字段数量少（通常 3-5 个以内）
- 表数据量大，回表成本高

## 判断方法

- **MySQL**：EXPLAIN 输出中 Extra 列显示 `Using index` 表示使用了覆盖索引
- **PostgreSQL**：EXPLAIN 输出中显示 `Index Only Scan` 表示使用了覆盖索引

## MySQL vs PostgreSQL 差异

| 特性 | MySQL (InnoDB) | PostgreSQL |
|------|---------------|-----------|
| 实现方式 | 二级索引叶节点包含索引列值 | 索引 + `INCLUDE` 子句 (PG 11+) |
| 语法 | `CREATE INDEX idx ON t(a, b, c)` | `CREATE INDEX idx ON t(a) INCLUDE (b, c)` |
| Visibility Map | 不需要 | 需要 VM 足够新才能使用 Index Only Scan |
