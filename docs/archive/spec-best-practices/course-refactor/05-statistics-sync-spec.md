# Phase 4 Statistics & Sync 重构 Spec

## 1. 阶段目标

本阶段重构统计、导出、同步类查询，解决活动域最后一批跨项目、跨口径、跨导出模型的耦合问题。

## 2. 全局强制约束

1. controller 层所有接口的入参、出参与原先保持一致，重构完成后必须做回归校验。
2. 编码前必须重新扫描统计、导出、同步相关 service/dao/xml，确认本 spec 仍然准确；如不一致，应以“统计口径收口 + 导出/同步边界清晰”为核心目标调整方案。
3. 所有新增或重构的方法必须补一句话 JavaDoc；方法内部需增加适量行级注释，说明统计场景选择、项目口径差异、导出映射与同步边界。

## 3. 本阶段范围

- `selectStatistics`
- `selectSubStatisticsList`
- `getNurturingActivity`
- `selectStationGrade`
- `selectStationYearGrade`
- `getCourseDetail`
- 与上述查询直接关联的导出、同步、补充组装逻辑

## 4. 目标类

- `template/CourseOfflineStatisticsTemplate`
- `support/CourseOfflineStatisticsContext`
- `support/CourseOfflineStatisticsScene`
- `strategy/project/ProjectStatisticsStrategy`
- `gateway/CourseOfflineStatisticsGateway`
- `template/CourseOfflineSyncTemplate`
- `support/CourseOfflineSyncContext`
- `support/CourseOfflineSyncScene`
- `gateway/CourseOfflineSyncGateway`

## 4.1 代码现实修正

1. 本阶段先收口统计与评分查询，不额外抽 `CourseTypeStatisticsStrategy`。当前差异主要集中在项目口径，不在课型口径。
2. 同步与外部集成链路继续留在后续阶段，本轮不把 `citysync/remote` 相关调用一并迁入统计模板。
3. `selectCourseGrade` 一并纳入 `CourseOfflineStatisticsTemplate`，用于统一承接分数配置回退与 JSON 字段解析。
4. `selectStationYearGrade / selectStationGrade / getCourseDetail` 也纳入本阶段，作为活动统计与评分查询的一部分同步收口。
5. 同步侧按代码现实落地为 `CourseOfflineSyncTemplate + CourseOfflineSyncGateway`，当前不引入项目策略；现有代码中尚未形成稳定的项目分叉，先用模板收口外部平台同步与轻量查询流程。

## 5. 要做什么

- 把统计场景、项目口径、导出字段组装从大 service 中拆开。
- 让杭州、嘉善等项目统计差异不再继续堆在 `CourseOfflineService`。
- 把统计查询与导出平铺映射放到模板步骤和项目策略里。
- 保持 controller 层接口签名不变的前提下，把 `@DataScope` 从 `CourseOfflineService` 下沉到 `CourseOfflineStatisticsTemplate` 的公开查询方法。
- 把 `getSwipeCourse / syncStationCourse2asola / getListByDeptId / getNeedCreate / getDistrictCourseOfflineCount` 从 `CourseOfflineService` 中迁入 `CourseOfflineSyncTemplate`，并通过 `CourseOfflineSyncGateway` 收口 Redis、上传日志和 DAO 调用。

## 6. 不要做什么

- 不要提前把同步与外部集成全抽成新平台。
- 不要把统计模板做成新一轮大 if/else。
- 不要把第一阶段 QueryTemplate 硬扩成统计模板。
- 不要为了“体系完整”提前引入空的 `CourseTypeStatisticsStrategy`。
- 不要把站点评分、科学育儿统计、养育活动评分三组查询继续散落在 `CourseOfflineService`。
- 不要在本轮 sync 重构中改 controller 层签名、HTTP 报文结构或 Asola 上传日志表结构。

## 7. 阶段依赖

- 依赖 Query 读模型骨架、Summary/Workflow 读模型边界稳定。

## 8. 验收标准

1. 统计主流程已从 `CourseOfflineService` 中明显收口。
2. 项目统计差异通过策略管理。
3. controller、导出、同步的入参与出参保持兼容。
4. 统计结果与导出结果口径一致。
5. `@DataScope` 在 `CourseOfflineStatisticsTemplate` 上仍可正常生效，并在 XML 层正确注入 `params.dataScope`。
6. `CourseOfflineService` 中原有 sync 入口已瘦身为模板转调，Asola token 获取、上传日志记录与轻量查询逻辑已迁入 `CourseOfflineSyncTemplate / Gateway`。
