# 合并策略报告 — care-class-to-develop

## 形态推断
- 推断结果：**backport / semantic transplant**
- 置信度：高
- 依据：
  - 源分支 `refactor/micro-core-dev` 与目标分支 `develop` 目录架构明显不同，不能直接 cherry-pick 落地
  - 红框 commit 集合聚焦养育照护活动课堂需求，存在插件化实现，需要映射回 develop 主链路
  - 用户已明确要求复杂 conflict 先保留 develop，再将源分支同名方法逻辑合并为结果

## 分支双侧
- **源**：`refactor/micro-core-dev`（HEAD = `d5b40412fde74ae65e7f18b093c4c6daacd4c712`，merge-base = `8ea045f5ac028b9a6731c2573211f3e471d6db89`）
- **目标**：`develop`（HEAD = `8e414953aca53ba00c9e2e3db466d15067fbc7a5`）
- **工作分支**：`merge/care-class-to-develop`（基于 `8e414953aca53ba00c9e2e3db466d15067fbc7a5`）

## 执行约束
- develop 已具备的同逻辑实现直接保留 develop
- 复杂冲突先保留 develop，再把源分支课堂需求逻辑语义回并到 develop 同名方法
- 插件包业务逻辑归并到主线时必须增加项目判断前置条件，避免影响非嘉善项目

## 当前归并重点
1. 课堂常量与表单配置类型补齐
2. 课堂保存/详情/H5 列表中的年龄与主讲老师逻辑回并
3. 嘉善课堂列表导出使用独立导出视图，补齐课堂状态/课堂类型列头
4. 课堂预约链路补齐重复预约防重、详情年龄回显、预约导出列控制

## 备注
- 本次采用语义回并，不做机械式 git cherry-pick
- docs 与 refactor 专属插件结构不直接迁入 develop
