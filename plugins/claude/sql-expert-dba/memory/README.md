# SQL Expert DBA — Memory 系统

## 定位

`memory/` 是 SQL Expert DBA 插件内部约定的数据层，由插件内的 skills / scripts 显式读写与维护。它不是 Codex 插件系统原生自动识别的 memory 能力。

## 硬约束

- 只沉淀结构化结论
- 不沉淀原始长对话
- 不沉淀未经验证的猜测
- 不沉淀无法去敏的业务细节
- 不沉淀纯一次性临时查询上下文

## 目录职责

| 目录 | 职责 | review_status |
|------|------|---------------|
| `glossary/` | 术语、指标口径、跨方言基础概念 | approved |
| `rules/` | 稳定规则类知识 | approved |
| `cases/` | 高价值案例卡片 | approved |
| `candidates/` | 待治理候选知识 | candidate |
| `templates/` | 高复用分析与报表模板 | approved |

## 索引

`index.json` 是供脚本检索的轻量索引文件，由 `memory_index.py` 维护。

## 命名规则

记忆文件命名格式：`{type}-{id}-{short-slug}.md`

示例：`rule-001-implicit-type-conversion.md`

## 单条记忆格式

每条记忆采用 Markdown + YAML front matter 形式，包含以下字段：

```yaml
---
id: rule-001                              # 唯一标识
title: 隐式类型转换导致索引失效            # 标题
type: rule                                 # rule | case | template | glossary
workflow: sql-query-optimizer              # 来源 workflow
dialect: mysql                             # mysql | postgresql | universal
tags: [index, type-conversion, performance] # 标签列表
problem_pattern: WHERE 条件中字段与值类型不一致  # 问题模式描述
preconditions: 字段为 VARCHAR 类型，WHERE 条件传入数字  # 前置条件
conclusion: 隐式类型转换会导致索引失效，应确保类型一致  # 结论
boundaries: 仅影响索引使用，不影响查询正确性          # 边界
example: "WHERE phone = 13800000000 → WHERE phone = '13800000000'"  # 正例
anti_example: 在确定类型一致时不需要额外转换                         # 反例
confidence: high                           # high | medium | low
review_status: approved                    # candidate | approved
last_reviewed_at: 2026-04-09              # 最后审核时间
origin_skill: sql-query-optimizer          # 来源 skill
capture_mode: explicit_user_requested      # auto_background | explicit_user_requested
---
```

## 记忆正文结构

YAML front matter 之后的 Markdown 正文建议包含：

1. **问题描述** — 什么场景下会遇到这个问题
2. **分析** — 为什么会这样
3. **解决方案** — 推荐做法
4. **方言差异**（如适用）— MySQL vs PostgreSQL 的行为差异
