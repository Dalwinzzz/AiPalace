# Phase 1 Query Template 重构 Spec

## 1. 阶段目标

本阶段只重构活动域 Query 主读模型，不进入统计、工作流、总结、预约域。

核心目标：

- 在不破坏 `@DataScope` 注入机制的前提下，把 Query 逻辑从 `CourseOfflineService` 中拆出到 `CourseOfflineQueryTemplate`。
- 让 `CourseOfflineService` 中对应查询方法收缩为兼容入口。
- 用 `CourseOfflineGateway` 收口第一阶段真正触达的主档查询。

## 2. 全局强制约束

1. controller 层所有接口的入参、出参与原先保持一致，重构完成后必须做回归校验。
2. 开始编码前必须重新扫描 `CourseOfflineService`、相关 DTO/VO、相关 XML，确认本 spec 与当前代码现实一致；若不一致，应围绕“Query 主读模型瘦身 + DataScope 兼容”重新调整实现。
3. 所有新增或重构的方法必须补一句话 JavaDoc；方法内部需增加适量行级注释，解释权限注入、场景分发、视图增强和兼容处理点。

## 3. 第一阶段范围

### 迁入 `CourseOfflineQueryTemplate` 的方法

- `getList(QueryCourseOfflineListVO vo)`
- `getCourseOfflineTotal(QueryCourseOfflineListVO vo)`
- `getDetail(Integer courserId)`
- `getDetailById(Integer courserId)`
- `getH5CourseOfflineList(QueryH5CourseOfflineListDTO dto)`
- `getHotList()`
- `getNurseryHotList(Long deptId)`

### 本阶段明确不迁

- `selectStationYearGrade`
- `selectStationGrade`
- `getCourseDetail`
- `selectStatistics`
- `selectSubStatisticsList`
- `getNurturingActivity`
- `batchGetEvaluationForm`
- `getNurturActivRecodeAll`
- `getWorkFlowList`

## 4. 目标类

### 新增类

- `service/courseoffline/template/CourseOfflineQueryTemplate`
- `service/courseoffline/gateway/CourseOfflineGateway`
- `service/courseoffline/support/CourseOfflineQueryContext`
- `service/courseoffline/support/CourseOfflineOperatorContext`
- `service/courseoffline/support/CourseOfflineQueryScene`
- `service/courseoffline/strategy/coursetype/CourseTypeQueryStrategy`
- `service/courseoffline/strategy/project/ProjectQueryStrategy`
- `service/courseoffline/strategy/CourseOfflineStrategyRouter`
- `dto/courseoffline/CourseOfflineDetailQuery` 或等价最小查询载体

### 改造类

- `CourseOfflineService`

## 5. `@DataScope` 处理方案

### 要做什么

- 把需要数据权限注入的公开查询方法标在 `CourseOfflineQueryTemplate` 上。
- 保证模板公开方法的首参是可承接 `params.dataScope` 的对象。
- 已有 `BaseEntity` 查询对象优先复用：
  - `QueryCourseOfflineListVO`
- 对 `getDetail(Integer courserId)` 补一个最小查询载体：
  - `CourseOfflineDetailQuery extends BaseEntity`
  - 只保留 `courseId`

### 不要做什么

- 不要继续维持 `@DataScope` + 基础类型首参 + 手动 `new BaseEntity()` 的结构。
- 不要把 `@DataScope` 写在私有方法或模板内部自调用的方法上。
- 不要大面积改造现有 XML 参数对象。

## 6. `CourseOfflineQueryTemplate` 公开方法

- `@DataScope(deptAlias = "c") queryAdminList(QueryCourseOfflineListVO vo)`
- `@DataScope(deptAlias = "c") queryAdminTotal(QueryCourseOfflineListVO vo)`
- `@DataScope(deptAlias = "c") queryAdminDetail(CourseOfflineDetailQuery query)`
- `queryDetailById(Integer courseId)`
- `queryH5List(QueryH5CourseOfflineListDTO dto)`
- `queryHotList()`
- `queryNurseryHotList(Long deptId)`

## 7. `CourseOfflineQueryTemplate` 私有步骤

### 统一私有步骤

1. `initOperatorContext()`
2. `initQueryContext(scene, rawParam, operatorContext)`
3. `normalizeQuery(context)`
4. `resolveStrategies(context)`
5. `beforeQuery(context)`
6. `doQuery(context)`
7. `afterQuery(context, rawResult)`
8. `returnResult(context, rawResult)`

### 可以保留的轻量私有增强方法

- `enrichTeacherInfo(...)`
- `enrichAgeInfo(...)`
- `enrichQualityScorePermission(...)`
- `enrichAuditInfo(...)`
- `enrichSummaryScore(...)`

### 不要做什么

- 不要做一个 `execute(Object, Scene)` 万能入口。
- 不要在模板内部直接注入 `CourseOfflineDao`、`CourseOfflineMapper`。
- 不要在模板里继续写 `projectName` 大段 if/else。

## 8. `CourseOfflineGateway` 在本阶段要收口的调用

### Query Core

- `queryAdminList(QueryCourseOfflineListVO vo)`
- `queryAdminTotal(QueryCourseOfflineListVO vo)`
- `queryAdminDetail(CourseOfflineDetailQuery query)`
- `queryDetailById(Integer courseId)`
- `queryH5List(QueryH5CourseOfflineListDTO dto)`
- `queryHotList()`
- `queryNurseryHotList(Long deptId)`
- `loadSummaryScoreMap(List<Integer> courseIds)` 可选

### 第一阶段优先收口的底层访问

- `courseOfflineDao.getCourseOfflineList`
- `courseOfflineDao.getCourseOfflineTotal`
- `courseOfflineDao.getById`
- `courseOfflineDao.getDetailById`
- `courseOfflineDao.getH5CourseOfflineList`
- `courseOfflineDao.getHotList`
- `courseOfflineDao.getNurseryHotList`
- `courseOfflineSummaryDao.getByNurseryId` 可选

### 本阶段不要收口

- `courseOfflineAppointService.*`
- `businessAuditRecordService`
- `businessAuditRecordDao`
- 统计域 DAO
- 总结域 Mapper

## 9. `CourseOfflineService` 方法瘦身目标

### `getList`

- 目标：`<= 3` 行有效业务代码
- 只做：空值保护 + 调 `queryTemplate.queryAdminList(vo)`

### `getCourseOfflineTotal`

- 目标：`<= 3` 行有效业务代码
- 只做：调 `queryTemplate.queryAdminTotal(vo)`

### `getDetail`

- 目标：`<= 8` 行有效业务代码
- 只做：构造 `CourseOfflineDetailQuery` + 调 `queryTemplate.queryAdminDetail(query)`

### `getDetailById`

- 目标：`<= 3` 行有效业务代码
- 只做：调 `queryTemplate.queryDetailById(courseId)`

### `getH5CourseOfflineList`

- 目标：`<= 3` 行有效业务代码
- 只做：调 `queryTemplate.queryH5List(dto)`

### `getHotList`

- 目标：`<= 2` 行有效业务代码
- 只做：调 `queryTemplate.queryHotList()`

### `getNurseryHotList`

- 目标：`<= 2` 行有效业务代码
- 只做：调 `queryTemplate.queryNurseryHotList(deptId)`

## 10. 第一阶段策略

### 第一批需要的策略

- `CourseTypeQueryStrategy`
- `ProjectQueryStrategy`
- `CourseOfflineStrategyRouter`

### 建议实现

- `ActivityCourseTypeQueryStrategy`
- `DefaultCourseTypeQueryStrategy`
- `DefaultProjectQueryStrategy`
- `HangzhouProjectQueryStrategy`
- `JiashanProjectQueryStrategy`
- `JinjiangProjectQueryStrategy`

### 第一阶段不要做什么

- 不要给每个课型都建空策略。
- 不要让项目策略直接拼 SQL。
- 不要让策略直接消费 `AjaxResult`、分页对象、XML 结果细节。

## 11. 验收标准

1. `getList / getCourseOfflineTotal / getDetail / getDetailById / getH5CourseOfflineList / getHotList / getNurseryHotList` 均已迁入模板。
2. `CourseOfflineService` 中对应方法明显瘦身。
3. `@DataScope` 仍能正确把权限 SQL 注入到 XML 消费的首参对象中。
4. 杭州 `strictCourseTypeMatch`、质量评分可编辑标识、嘉善 `summaryScore` 等现有行为保持一致。
5. controller 层入参与出参未变化。
