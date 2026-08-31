---
name: palace-kb
description: 用户 Notion「Palace」个人知识库的结构、新增知识姿势、以及踩过的两个坑
metadata: 
  node_type: memory
  type: reference
  originSessionId: 34872e23-33ba-4208-8e16-5bf79eca95f4
---

Notion「Palace」个人知识库（截至 2026-05-29；ID 可能变，用前先 notion-search/fetch 核对）：

- 根页面 Palace `32f0c9cd-20f4-8157-9392-e83a1be7fdd5` → 数据中心 → **唯一数据库「全局知识引擎」** `e17645585c0445d0b8e448d79d563c3b`，data source = `collection://f140e35b-c54b-44df-93d8-f7d76b8bac5a`。
- `学习/工作/生活` 三个分支页**只是该库的视图入口，不单独存数据**。所有知识都是「全局知识引擎」里的页面(行)。
- **新增知识 = 在该 data source 下建页**，属性：`领域`(学习/工作/生活)、`内容类型`(知识卡片/笔记/会议纪要/项目文档/日报周报/复盘/资料索引/方法论)、`来源类型`(网页/书籍/课程/会议/项目/对话/自写)、`阶段`(收集/处理中/沉淀中/已输出/归档)、`名称`(title)。
- 命名约定：**「技术名｜主题」**。专题 = 1 个「专题入口」(资料索引) + N 张知识卡片(笔记)，入口页用目录链接各卡片（如 Git 专题、Golang 专题）。

**两个踩过的坑（重要）**：
1. ⚠️ `标签`(多选)**新增选项**只能改 schema，`update-data-source` 的 `ALTER COLUMN SET MULTI_SELECT(...)` 是**全量替换**（漏列即删旧标签），且会被 Claude Code auto-mode 安全分类器**直接拦截**。安全路径：**让用户在 Notion UI 标签单元格手动新建选项**，再用 `update_properties` 给页面设该标签（设“已存在”的选项值不会被拦截，已验证可行）。`Golang` 标签已于 2026-05-29 由用户在 UI 新建。
2. ⚠️ `update-page` 的 `replace_content`/`insert_content`，`new_str`/`content` **必须用真实换行符**；写成 `\n` 转义会被当字面 “n”，导致整页内容塌成残块。（而 `create-pages` 的 `content` 在 JSON 串里用 `\n` 反而 OK。）大段中文正文最稳的做法：建空骨架页后用 `replace_content` 真实换行注入。
- 建/改页前先读 MCP 资源 `notion://docs/enhanced-markdown-spec`：表格用 XML `<table>`(非 pipe)、callout/toggle 用专用标签。
