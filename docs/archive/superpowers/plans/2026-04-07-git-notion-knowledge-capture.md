# Git Notion 知识沉淀实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将本次 Git 本地仓库初始化实践沉淀到 Notion 的 `Palace -> 学习 -> 全局知识引擎` 体系中，形成 1 个 Git 专题入口和 1 张高质量实践知识卡片。

**Architecture:** 内容全部进入 `全局知识引擎` 数据源 `collection://f140e35b-c54b-44df-93d8-f7d76b8bac5a`。先创建 `Git｜专题入口`，再基于其 URL 创建 `Git｜本地仓库初始化实践与常用命令`，最后回填专题入口中的知识点目录，形成稳定双向导航。

**Tech Stack:** Notion MCP 工具、Notion 数据源 `全局知识引擎`、本地 spec 文档、Git 本地仓库

---

### Task 1: 校验目标位置与去重

**Files:**
- Reference: `docs/superpowers/specs/2026-04-07-git-notion-knowledge-capture-design.md`
- Query: `全局知识引擎` 数据源 `collection://f140e35b-c54b-44df-93d8-f7d76b8bac5a`

- [ ] **Step 1: 搜索是否已存在同名页面**

使用 Notion 搜索分别检查以下两个标题是否已存在：

```json
{
  "query": "Git｜专题入口",
  "query_type": "internal",
  "page_size": 10,
  "max_highlight_length": 0,
  "filters": {}
}
```

```json
{
  "query": "Git｜本地仓库初始化实践与常用命令",
  "query_type": "internal",
  "page_size": 10,
  "max_highlight_length": 0,
  "filters": {}
}
```

预期结果：
- 没有标题完全相同的现成记录
- 如果存在完全同名页面，不要继续创建重复页面，改为拉取现有页面并转入“更新模式”

- [ ] **Step 2: 再次确认目标数据源与字段值**

本次所有新记录都必须写入下面这个数据源，且字段值固定：

```text
data_source_url: collection://f140e35b-c54b-44df-93d8-f7d76b8bac5a
领域: 学习
标签: Git
阶段: 已输出
```

记录类型要求：

```text
Git｜专题入口 -> 内容类型: 资料索引, 来源类型: 自写
Git｜本地仓库初始化实践与常用命令 -> 内容类型: 知识卡片, 来源类型: 对话
```

- [ ] **Step 3: 如果搜索结果为空，则进入创建流程**

进入下一任务前，确认以下条件全部成立：

- 两个标题都不存在完全重复页面
- 目标数据源是 `collection://f140e35b-c54b-44df-93d8-f7d76b8bac5a`
- 本次不修改 `学习` 页面结构，不新建数据库

### Task 2: 创建 Git 专题入口

**Files:**
- Reference: `docs/superpowers/specs/2026-04-07-git-notion-knowledge-capture-design.md`
- Create in Notion: `Git｜专题入口`

- [ ] **Step 1: 用明确字段创建专题入口页面**

调用 `mcp__codex_apps__notion_notion_create_pages` 创建页面：

```json
{
  "parent": "collection://f140e35b-c54b-44df-93d8-f7d76b8bac5a",
  "pages": [
    {
      "properties": {
        "名称": "Git｜专题入口",
        "领域": "学习",
        "内容类型": "资料索引",
        "来源类型": "自写",
        "标签": ["Git"],
        "阶段": "已输出"
      },
      "content": "<callout icon=\"🧭\" color=\"gray_bg\">\n这个专题只保留我日常最常用、最容易忘、最值得快速回查的 Git 知识，不做大而全整理。\n</callout>\n\n## 你会在这里看到什么\n- 本地仓库初始化\n- 日常提交与查看状态\n- 常见回滚与撤销\n- 后续再补分支基础\n\n## 知识点目录\n\n## Git 日常最小命令集\n- 初始化仓库：`git init`\n- 查看状态：`git status`\n- 加入暂存区：`git add -A`\n- 创建提交：`git commit -m \"...\"`\n- 查看历史：`git log --oneline`\n- 回到某次提交：`git reset --hard <commit>`\n\n## 后续可扩展知识点\n- Git｜日常提交流程\n- Git｜撤销与回滚\n- Git｜分支基础"
    }
  ]
}
```

预期结果：
- 成功返回新页面的 `id` 和 `url`
- 页面已出现在 `全局知识引擎`

- [ ] **Step 2: 记录专题入口页面 URL**

把上一步返回的 URL 原样记录为：

```text
TOPIC_PAGE_URL = <create_pages 返回的 Git｜专题入口 url>
TOPIC_PAGE_ID = <create_pages 返回的 Git｜专题入口 id>
```

这两个值会在后续创建实践卡片和回填目录时直接使用。

- [ ] **Step 3: 立刻拉取专题入口页面做一次校验**

调用 `mcp__codex_apps__notion_fetch`：

```json
{
  "id": "TOPIC_PAGE_ID"
}
```

确认以下内容存在：
- 标题为 `Git｜专题入口`
- 字段中 `领域=学习`
- 正文包含 `## 知识点目录`
- 正文包含 `Git 日常最小命令集`

### Task 3: 创建实践知识卡片

**Files:**
- Reference: `docs/superpowers/specs/2026-04-07-git-notion-knowledge-capture-design.md`
- Create in Notion: `Git｜本地仓库初始化实践与常用命令`

- [ ] **Step 1: 使用专题入口 URL 创建实践卡片**

调用 `mcp__codex_apps__notion_notion_create_pages`：

```json
{
  "parent": "collection://f140e35b-c54b-44df-93d8-f7d76b8bac5a",
  "pages": [
    {
      "properties": {
        "名称": "Git｜本地仓库初始化实践与常用命令",
        "领域": "学习",
        "内容类型": "知识卡片",
        "来源类型": "对话",
        "标签": ["Git"],
        "阶段": "已输出"
      },
      "content": "<callout icon=\"✅\" color=\"green_bg\">\n如果只是把本地目录当成版本管理容器，标准流程是：`git init` -> 写 `.gitignore` -> `git add .` -> `git commit`。\n</callout>\n\n## 场景背景\n这次目标是把 `/Users/dalwin/Documents/AI` 作为本地 Git 仓库使用，只做版本回溯，不连接远程仓库。\n\n执行 `git add .` 后出现了 `embedded git repository` 警告，原因是目录里已有多个子目录自带 `.git/`，外层仓库会把它们当成嵌套仓库而不是普通文件内容。\n\n## 正常初始化流程\n1. `git init`\n2. 新建 `.gitignore`\n3. `git add .`\n4. `git commit -m \"initial commit\"`\n5. `git status`\n\n## 本次特殊问题：embedded git repository\n处理思路不是硬提交，而是先处理子目录里的内部 `.git` 元数据，再重新暂存。\n\n### 处理步骤\n1. 找出哪些子目录带有 `.git`\n2. 决定这些目录要不要继续保留独立仓库身份\n3. 如果外层仓库要完整纳入它们，就先移走内部 `.git`\n4. `git reset`\n5. `git add .`\n6. `git commit`\n\n## 命令速查\n- `git init`：初始化仓库。第一次建立本地版本管理时用。\n- `git status`：查看工作区和暂存区状态。每次修改前后都可用。\n- `git add .`：把当前目录改动加入暂存区。准备提交时用。\n- `git reset`：清空暂存区但保留文件改动。加错内容时用。\n- `git commit -m \"...\"`：创建一个版本快照。形成可回溯节点时用。\n- `git log --oneline`：查看简洁历史。找最近提交或回退点时用。\n\n## 可直接复用的命令块\n```bash\ngit init\nprintf \".DS_Store\\n**/.DS_Store\\n\" > .gitignore\ngit add .\ngit commit -m \"initial commit\"\ngit status\n```\n\n## 避坑提醒\n- 看到 `embedded git repository` 时，不要直接忽略后提交。\n- 外层仓库如果要完整管理子目录内容，就不能保留子目录里的 `.git/`。\n- `git reset --hard <commit>` 会丢失未提交修改，使用前必须确认。\n- `.DS_Store` 这类系统垃圾文件应在一开始就忽略。\n\n## 关联页面\n- [Git｜专题入口](TOPIC_PAGE_URL)\n\n## 记忆锚点\n`先 init，后 ignore，再 add/commit；遇嵌套，先处理内部 .git。`"
    }
  ]
}
```

执行要求：
- 先把正文中的 `TOPIC_PAGE_URL` 替换为 Task 2 返回的真实专题页 URL
- 替换后再发起创建请求

- [ ] **Step 2: 记录实践卡片 URL**

把创建结果记录为：

```text
PRACTICE_PAGE_URL = <create_pages 返回的实践卡片 url>
PRACTICE_PAGE_ID = <create_pages 返回的实践卡片 id>
```

- [ ] **Step 3: 拉取实践卡片并校验核心结构**

调用 `mcp__codex_apps__notion_fetch`：

```json
{
  "id": "PRACTICE_PAGE_ID"
}
```

确认以下内容存在：
- 标题为 `Git｜本地仓库初始化实践与常用命令`
- 正文首屏为核心结论型 `callout`
- 正文包含代码块
- 正文包含 `避坑提醒`
- 正文包含指向专题页的链接

### Task 4: 回填专题入口中的知识点目录

**Files:**
- Update in Notion: `Git｜专题入口`

- [ ] **Step 1: 在专题入口的“知识点目录”下插入实践卡片链接**

调用 `mcp__codex_apps__notion_notion_update_page`：

```json
{
  "page_id": "TOPIC_PAGE_ID",
  "command": "update_content",
  "content_updates": [
    {
      "old_str": "## 知识点目录",
      "new_str": "## 知识点目录\n- [Git｜本地仓库初始化实践与常用命令](PRACTICE_PAGE_URL)"
    }
  ],
  "properties": {}
}
```

执行要求：
- 先把 `PRACTICE_PAGE_URL` 替换为 Task 3 返回的真实实践卡片 URL
- `old_str` 必须与页面现有内容完全一致

- [ ] **Step 2: 再次拉取专题入口，确认目录链接已生效**

调用 `mcp__codex_apps__notion_fetch`：

```json
{
  "id": "TOPIC_PAGE_ID"
}
```

确认以下结果：
- `知识点目录` 下已有实践卡片链接
- 链接文案与卡片标题一致
- 页面仍保持轻量导航页，不变成长教程

### Task 5: 做最终检索与阅读体验校验

**Files:**
- Validate in Notion: `Git｜专题入口`
- Validate in Notion: `Git｜本地仓库初始化实践与常用命令`

- [ ] **Step 1: 用 `Git` 关键词做一次检索校验**

调用 `mcp__codex_apps__notion_search`：

```json
{
  "query": "Git",
  "query_type": "internal",
  "page_size": 10,
  "max_highlight_length": 120,
  "filters": {}
}
```

确认两条新记录都能被搜到。

- [ ] **Step 2: 做结构化阅读检查**

人工检查两条页面是否符合以下标准：

- `Git｜专题入口` 是目录页，不是教程正文
- `Git｜专题入口` 包含专题说明、目录、最小命令集
- `Git｜本地仓库初始化实践与常用命令` 包含核心结论、流程、命令速查、代码块、避坑提醒、记忆锚点
- 两页都没有扩展到远程仓库或多人协作主题

- [ ] **Step 3: 如果检查通过，则输出完成说明**

完成说明必须包含：

```text
1. Git 专题入口页面 URL
2. Git 实践卡片页面 URL
3. 已写入全局知识引擎
4. 已符合“学习”分支检索与阅读要求
```

## Self-Review

### Spec coverage

- `专题入口` 创建：覆盖
- `实践卡片` 创建：覆盖
- `全局知识引擎` 字段约束：覆盖
- `目录链接与返回关系`：覆盖
- `结构化内容与记忆导向`：覆盖
- `最终校验`：覆盖

### Placeholder scan

- 计划中没有 `TBD`、`TODO`、`类似 Task N` 之类的占位语句
- 唯一需要动态替换的只有 `TOPIC_PAGE_URL` 与 `PRACTICE_PAGE_URL`，它们都来自前序真实创建结果，不是开放性占位

### Type consistency

- 数据源统一为 `collection://f140e35b-c54b-44df-93d8-f7d76b8bac5a`
- 标题、内容类型、来源类型、标签、领域在所有任务中保持一致
- 先创建专题页，再创建实践页，再回填目录，顺序一致且依赖明确
