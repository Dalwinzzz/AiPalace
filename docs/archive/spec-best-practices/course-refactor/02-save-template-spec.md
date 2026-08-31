# Phase 1 Save Template 重构 Spec

## 1. 阶段目标

本阶段重构活动主档写链路，把 `CourseOfflineService` 中最肥的写流程迁入 `CourseOfflineSaveTemplate`，但不同时把 appoint、summary、workflow 一起卷进来。

核心目标：

- 让 `save`、`updateOfflineState` 等主写方法从实现层退回到兼容入口层。
- 把项目差异和课型差异从 `CourseOfflineService` 中抽到策略层。
- 用共享 `CourseOfflineGateway` 收口第一阶段 Save 所需的主档写入与少量扩展写入。

## 2. 全局强制约束

1. controller 层所有接口的入参、出参与原先保持一致，重构完成后必须做回归校验。
2. 编码前必须重新扫描 `CourseOfflineService`、相关保存 DTO、扩展表与 Mapper，确认本 spec 仍然准确；如果代码现实变化，应以完成“Save 主链瘦身 + 差异策略收口”为核心目标调整方案。
3. 所有新增或重构的方法必须补一句话 JavaDoc；方法内部需增加适量行级注释，说明通用校验、项目差异、课型差异、后置副作用和兼容处理点。

## 3. 本阶段范围

### 迁入 `CourseOfflineSaveTemplate` 的方法

- `save(SaveCourseOfflineVO vo, String projectName)`
- `save(SaveCourseOfflineVO vo)`
- `updateOfflineState(Integer courseId, Long deptId, String projectName)`
- `deleteOffline(Integer courseId, Long deptId)`
- `alterPosterImg(SaveCourseOfflineVO courseOfflineDTO)`
- `editSignTime(EditSignTimeDeadlineDto dto)`
- `getSignTimeDeadline()`

### 本阶段明确不迁

- appoint 相关主流程
- summary 相关保存
- workflow 主流程
- statistics/export/sync

## 4. 目标类

### 新增类

- `service/courseoffline/template/CourseOfflineSaveTemplate`
- `service/courseoffline/support/CourseOfflineSaveContext`
- `service/courseoffline/support/CourseOfflineSaveScene`
- `service/courseoffline/strategy/coursetype/CourseTypeSaveStrategy`
- `service/courseoffline/strategy/project/ProjectSaveStrategy`

### 复用类

- `service/courseoffline/gateway/CourseOfflineGateway`
- `service/courseoffline/strategy/CourseOfflineStrategyRouter`

### 改造类

- `CourseOfflineService`

## 5. 模板结构

### 公开方法

- `saveCourse(SaveCourseOfflineVO vo, String projectName)`
- `updateCourseState(Integer courseId, Long deptId, String projectName)`
- `deleteCourse(Integer courseId, Long deptId)`
- `updatePoster(SaveCourseOfflineVO vo)`
- `updateSignDeadline(EditSignTimeDeadlineDto dto)`
- `querySignDeadline()`

### 两条流程骨架

#### 骨架 A：主档写流程

适用于：

- `saveCourse`
- `updateCourseState`
- `deleteCourse`

步骤：

1. `initOperatorContext()`
2. `initSaveContext(scene, rawParam, operatorContext)`
3. `normalizeInput(context)`
4. `validateBaseRules(context)`
5. `loadCurrentState(context)`
6. `resolveStrategies(context)`
7. `applyBusinessRules(context)`
8. `persist(context)`
9. `afterPersist(context)`

#### 骨架 B：轻量字段/配置写流程

适用于：

- `updatePoster`
- `updateSignDeadline`

步骤：

1. `initOperatorContext()`
2. `initSaveContext(scene, rawParam, operatorContext)`
3. `validateTargetExists(context)`
4. `applyLightweightRules(context)`
5. `persist(context)`
6. `afterPersist(context)`

## 6. 第一阶段策略化边界

### 第一批必须策略化

#### `ProjectSaveStrategy`

必须承接：

- 新增活动的初始 `state / audit / courseCheck`
- 编辑保存后的审核状态回退或重置
- 下架后的项目审核状态回退
- 创建/编辑/状态切换后的项目特有后置动作
- 南京礼包扩展写入
- 晋江/嘉善审核记录回写

建议实现：

- `DefaultProjectSaveStrategy`
- `JinjiangProjectSaveStrategy`
- `JiashanProjectSaveStrategy`
- `NanjingProjectSaveStrategy`

#### `CourseTypeSaveStrategy`

必须承接：

- 当前课型是否属于活动主链路
- `ageList` 是否参与保存语义
- `ageString` 是否需要生成
- 课型特有字段归一化

建议实现：

- `ActivityCourseTypeSaveStrategy`
- `DefaultCourseTypeSaveStrategy`

### 第一阶段先留在模板内

- 开始/结束时间校验
- 报名截止时间校验
- 年龄段去重与存在性校验触发
- 活动存在性/删除态校验
- 所有权与编辑权限校验
- 活动进行前/进行中/结束后可编辑范围控制
- 报名人数不得低于已预约人数
- 轻量更新流程

### 第一阶段明确不要策略化

- `deleteOffline`
- `alterPosterImg`
- `editSignTime`
- `getSignTimeDeadline`
- 每一条基础校验拆成单独策略
- 按课型制造一堆空策略实现

## 7. `CourseOfflineGateway` 在本阶段要收口的调用

### Save Core

- `loadCourse(Integer courseId)`
- `insertCourse(CourseOffline courseOffline)`
- `updateCourse(CourseOffline courseOffline)`
- `countAppointByCourseId(Integer courseId, Integer state)`
- `softDeleteCourse(Integer courseId, String updateBy, Date updateTime)`
- `updatePoster(Integer courseId, String posterImg, Date updateTime)`

### Extension Support

- `loadSignTimeConfig(String projectName)`
- `upsertSignTimeConfig(String projectName, Integer signEndTime, Integer notAppointSignEndTime, LocalDateTime now)`
- `upsertNanjingGift(Integer courseId, Boolean hasGift)`

### 第一阶段优先收口的底层访问

- `courseOfflineMapper.selectByPrimaryKey`
- `courseOfflineMapper.insert`
- `courseOfflineMapper.updateByPrimaryKeySelective`
- `courseOfflineDao.countAppointByCourseId`
- `courseOfflineSignTimeConfMapper.selectByExample`
- `courseOfflineSignTimeConfMapper.insertSelective`
- `courseOfflineSignTimeConfMapper.updateByPrimaryKey`
- `courseOfflineNjMapper.countByExample`
- `courseOfflineNjMapper.selectByExample`
- `courseOfflineNjMapper.insert`
- `courseOfflineNjMapper.updateByPrimaryKey`

### 本阶段不要收口

- `businessAuditRecordService` 与 `businessAuditRecordDao` 到独立 workflow 网关
- 消息发送与异步通知到独立 integration 网关
- appoint 域 service/dao
- summary 域 mapper

## 8. `CourseOfflineService` 方法瘦身目标

### `save(SaveCourseOfflineVO vo, String projectName)`

- 目标：`<= 8` 行有效业务代码
- 只做：参数兼容 + 调 `saveTemplate.saveCourse(vo, projectName)`

### `save(SaveCourseOfflineVO vo)`

- 目标：`<= 3` 行有效业务代码
- 只做：调 `saveTemplate.saveCourse(vo, this.projectName)`

### `updateOfflineState`

- 目标：`<= 5` 行有效业务代码
- 只做：调 `saveTemplate.updateCourseState(courseId, deptId, projectName)`

### `deleteOffline`

- 目标：`<= 5` 行有效业务代码
- 只做：调 `saveTemplate.deleteCourse(courseId, deptId)`

### `alterPosterImg`

- 目标：`<= 3` 行有效业务代码
- 只做：调 `saveTemplate.updatePoster(vo)`

### `editSignTime`

- 目标：`<= 3` 行有效业务代码
- 只做：调 `saveTemplate.updateSignDeadline(dto)`

### `getSignTimeDeadline`

- 目标：`<= 3` 行有效业务代码
- 只做：调 `saveTemplate.querySignDeadline()`

## 9. 要做什么

- 把 `save` 中的新增/编辑主流程迁进模板。
- 把 `save` 中的项目差异迁进 `ProjectSaveStrategy`。
- 把 `isActivityCourseType` 相关保存差异迁进 `CourseTypeSaveStrategy`。
- 让 `CourseOfflineService` 只保留兼容入口职责。
- 用 `CourseOfflineGateway` 统一收口主档与扩展写入。

## 10. 不要做什么

- 不要保留两个 `save` 方法各自一套完整实现。
- 不要把项目差异继续留在 `CourseOfflineService` 里。
- 不要让 `CourseOfflineSaveTemplate` 直接注入一堆 Mapper。
- 不要为了“架构纯洁”把轻量更新流程也做成独立模板类。
- 不要把按项目存配置误判成按项目有业务差异。

## 11. 验收标准

1. `save / updateOfflineState / deleteOffline / alterPosterImg / editSignTime / getSignTimeDeadline` 已迁入 `CourseOfflineSaveTemplate`。
2. `CourseOfflineService` 中上述方法均明显瘦身。
3. 晋江/嘉善/南京现有项目差异行为保持不变。
4. 新增/编辑/上下架/删除/海报更新/签到期限配置查询与更新的 controller 接口入参与出参未变化。
5. 方法级 JavaDoc 和关键行级注释补齐。
