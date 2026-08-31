---
id: rule-001
title: 隐式类型转换导致索引失效
type: rule
workflow: sql-query-optimizer
dialect: mysql
tags: [index, type-conversion, performance, anti-pattern]
problem_pattern: WHERE 条件中字段类型与比较值类型不一致
preconditions: 索引字段为字符串类型（VARCHAR/CHAR），WHERE 条件传入数值型参数
conclusion: MySQL 会对索引字段做隐式类型转换（字符串→数字），导致无法使用索引，退化为全表扫描
boundaries: 仅影响"字符串字段比较数字"场景；数字字段比较字符串时 MySQL 会转换值而非字段，索引仍可用
example: "错误: WHERE phone = 13800000000\n正确: WHERE phone = '13800000000'"
anti_example: INT 字段与字符串比较时不受此影响（MySQL 会转换字符串侧）
confidence: high
review_status: approved
last_reviewed_at: 2026-04-09
origin_skill: sql-query-optimizer
capture_mode: auto_background
---

# 隐式类型转换导致索引失效

## 问题描述

当 WHERE 条件中，VARCHAR/CHAR 类型的索引字段与数值型参数比较时，MySQL 会将字段值逐行转换为数字再比较，导致索引无法命中。

这是一个高频且非直觉的性能陷阱，尤其在手机号、身份证号、订单号等"看起来像数字的字符串字段"上容易出现。

## 分析

MySQL 的类型转换规则：
1. 字符串 vs 数字比较时，MySQL 将字符串转为数字
2. 转换发生在字段侧时，索引失效（等价于对字段加了函数）
3. 转换发生在值侧时，索引正常

## 解决方案

确保 WHERE 条件中的参数类型与字段类型一致：

```sql
-- 错误：索引失效
SELECT * FROM users WHERE phone = 13800000000;

-- 正确：索引正常
SELECT * FROM users WHERE phone = '13800000000';
```

在应用层检查 ORM/框架传参类型，避免框架自动将字符串参数转为数字。

## PostgreSQL 差异

PostgreSQL 在类型不匹配时通常直接报错而非隐式转换，因此此问题主要影响 MySQL。

PostgreSQL 中若确需跨类型比较，需显式 CAST：
```sql
WHERE phone = CAST(13800000000 AS TEXT)
```
