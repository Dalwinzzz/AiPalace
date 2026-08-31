# ADR-0017：project tier skill 支持多项目归属（逗号分隔多值）

- 状态：已接受
- 日期：2026-07-13
- 决策人：dalwin
- 关联：扩展 ADR-0006（引入 project tier）；延续 [ADR-0010](0010-project-skill枚举git根派生指针软链.md) / [ADR-0015](0015-project-skill双发现路径派生补齐Codex侧.md)（project skill 双发现路径 mount）、[P2 声明式管理](../PHILOSOPHY.md#p2--声明式管理工具派生限内容资产)、[P4 分级控预算](../PHILOSOPHY.md#p4--分级控预算tier)

## 背景

智金公司下不止一个业务项目：`zhijin`（`~/Library/IdeaProject/ZhiJin`，SunkidCloud/SaaS/托育等，公司伞级）+ 新增 `zhijin_etl`（`~/Library/IdeaProject/WaveFlow`，ETL）。通用研发工作流 skill（`ownerpowers` / `biz-workflow` / `spec-architect` / `commit-review` / `liquibase-dual-db-writer`）在两个项目里都要用。

原 schema `project:` 为**单值**——一个 project tier skill 只能属一个项目（`load_registry` 正则单值捕获、`_link_project_skills` 精确 `==` 过滤）。同一 skill 无法同时属 `zhijin` 与 `zhijin_etl`，只能：① 复制成两条登记（违背单一登记）；或 ② 降回 `core`（进全局、泄给所有无关项目，违背 project tier「移出全局」本意，P4）。

## 决策

**project tier 的 `project:` 字段支持多值——逗号分隔（无空格），一个 skill 可同时属多个项目；`mount <项目>` 时凡 `<项目>` 在该 skill 的项目列表中即派生。**

1. `load_registry`：项目捕获字符集 `[A-Za-z0-9_-]` → `[A-Za-z0-9_,-]`（容逗号）；解析结果 `project` 统一存 **list**（单值→单元素 list，无值→空 list）。
2. `_link_project_skills`：过滤条件 `i["project"] != proj` → `proj not in i["project"]`（成员判断）。
3. `doctor`：project skill 的**每个**项目 key 都须在 `projects:` 声明，逐个校验；有一个未声明即报错。
4. `stats`：项目段显示逗号连接的多项目。
5. registry 书写约束：多值逗号分隔、**无空格**（`project: zhijin,zhijin_etl`）——解析器为正则（非 PyYAML），字符集不含空格。

## 后果

**正面**：一个 skill 声明一次即可跨多项目 opt-in mount，无需复制登记；**单值书写完全向后兼容**（解析为单元素 list，既有 mount/doctor/stats 行为不变，`tests/test_skillctl.py` 32 项含 2 项多项目新测全绿）；仍是声明式（registry → `mount` 派生），project tier「移出全局、按项目 opt-in」语义不破。

**取舍 / 待观察**：
- 逗号分隔靠正则解析、**须无空格**——已在 registry 注释与本 ADR 显式约束；doctor 不校验空格，写错会导致逗号后的项目漏解析（属书写纪律，非工具兜底）。
- 一个 skill 属多项目 = 每个项目各派生一份指针软链，`mount`/`unmount` 各自独立；某项目 unmount 不影响其它项目的软链。
- 跨项目共享的 skill 内容须真正项目无关；若某 skill 只适用部分项目（如 `liquibase-dual-db-writer` 若 ETL 项目不用 Kingbase），从其 project 列表移除即按需收窄。
