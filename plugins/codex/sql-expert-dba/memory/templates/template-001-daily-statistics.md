---
id: template-001
title: 日统计报表基础模板
type: template
workflow: sql-report-query-builder
dialect: universal
tags: [report, statistics, template, daily, aggregation]
problem_pattern: 需要按日期维度统计某业务指标的汇总数据
preconditions: 存在业务主表，包含时间字段和可聚合的度量字段
conclusion: 提供一个通用的日统计报表 SQL 模板，包含日期筛选、分组聚合、排序和空值处理
boundaries: 仅适用于单表或简单关联的日粒度统计；多表复杂关联需按业务定制
example: 日订单量统计、日活跃用户统计、日交易金额统计
anti_example: 实时数据流统计、跨时区复杂日期处理
confidence: high
review_status: approved
last_reviewed_at: 2026-04-09
origin_skill: sql-report-query-builder
capture_mode: explicit_user_requested
---

# 日统计报表基础模板

## 模板 SQL

```sql
-- 日统计报表基础模板
-- 使用前替换：{table}, {date_column}, {metric_column}, {start_date}, {end_date}
SELECT
    DATE({date_column})                    AS stat_date,
    COUNT(*)                               AS total_count,
    COUNT(DISTINCT {metric_column})        AS distinct_count,
    SUM({metric_column})                   AS total_sum,
    AVG({metric_column})                   AS avg_value,
    MIN({metric_column})                   AS min_value,
    MAX({metric_column})                   AS max_value
FROM {table}
WHERE {date_column} >= '{start_date}'
  AND {date_column} <  '{end_date}'
GROUP BY DATE({date_column})
ORDER BY stat_date ASC;
```

## 使用说明

1. **时间范围**：使用左闭右开区间 `[start, end)`，避免边界问题
2. **DATE() 函数**：将 DATETIME/TIMESTAMP 截断为日期，确保按天分组
3. **聚合函数**：按需保留，删除不需要的指标列
4. **NULL 处理**：如 metric_column 可能为 NULL，考虑使用 `COALESCE`

## 常见扩展

### 补齐无数据的日期

```sql
-- 使用日期序列表（或生成序列）LEFT JOIN 业务数据
-- PostgreSQL
SELECT d.dt AS stat_date, COALESCE(t.cnt, 0) AS total_count
FROM generate_series('{start_date}'::date, '{end_date}'::date - 1, '1 day') AS d(dt)
LEFT JOIN (
    SELECT DATE(created_at) AS dt, COUNT(*) AS cnt
    FROM orders
    WHERE created_at >= '{start_date}' AND created_at < '{end_date}'
    GROUP BY DATE(created_at)
) t ON d.dt = t.dt
ORDER BY d.dt;
```

### 同比/环比

```sql
-- 日环比（与前一天比较）
SELECT
    stat_date,
    total_count,
    LAG(total_count, 1) OVER (ORDER BY stat_date) AS prev_day_count,
    ROUND(
        (total_count - LAG(total_count, 1) OVER (ORDER BY stat_date)) * 100.0
        / NULLIF(LAG(total_count, 1) OVER (ORDER BY stat_date), 0),
        2
    ) AS day_over_day_pct
FROM daily_stats
ORDER BY stat_date;
```

## 方言注意事项

| 特性 | MySQL | PostgreSQL |
|------|-------|-----------|
| 日期截断 | `DATE(col)` | `DATE(col)` 或 `col::date` |
| 日期序列生成 | 需要辅助表或递归 CTE | `generate_series()` |
| 窗口函数 | 8.0+ 支持 | 完全支持 |
