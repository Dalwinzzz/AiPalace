# Spec: SYZH V2.0.4 杭州科学育儿活动链路改造（Codex 执行版）

## 0. 元信息
- 目标工具: Codex
- 变更类型: 存量模块改造 + 新业务分支接入 + 统计口径调整
- 创建时间: 2026-03-26
- PRD 基线: `2026-03-26-syzh-v2.0.4-prd.md`
- 仓库/模块: `skc-activity`
- 扫描级别: 重度

## 1. 业务目标与范围

### 1.1 业务目标
在不新增主业务表的前提下，基于 `course_offline` 完成杭州项目的 6 类改造：养育照护活动时间冲突限制、养育照护活动总结内容必填治理、营养厨房接入、质量评分、科学育儿数据分析口径调整、`course_field` 多 `configType` 查询。

### 1.2 范围内
- `course_type=4` 营养厨房接入现有活动 CRUD、详情、预约、统计链路
- 杭州项目下，养育照护活动预约增加“同时间段只能预约一场”活动冲突校验
- 杭州项目下，活动总结保存/回显按 `course_type` 区分普通活动与营养厨房
- 杭州项目下，养育照护活动监管列表新增质量评分展示、可修改标识、录入接口
- 杭州项目下，科学育儿数据分析保留原 `train*` 字段兼容，同时新增营养厨房统计承载属性
- 杭州项目下，`course_field` 列表接口支持多 `configType` 查询
- 杭州项目相关查询里，`course_type` 业务语义筛选改为精确匹配，避免 `course_type=4` 串入普通活动

### 1.3 范围外
- 不新增营养厨房独立主表
- 不新增营养厨房独立接口组
- 不改 `/courseOffline/add/field` 的单 `configType` 维护模式
- 不新增质量评分历史表
- 不修改前端菜单与页面代码
- 不重构 `judgeIsLimitAppoint(String idCard)` 的调用顺序
- 不在本次实现中额外做“营养厨房跳过现有爽约限制”的链路重构

### 1.4 已锁定的实现默认值
- 杭州项目判定统一使用 `Constants.PROJECT_NAME_HANGZHOU.equals(projectName)`
- 质量评分新增录入接口，路径固定为 `POST /courseOffline/qualityScore/save`
- 科学育儿数据分析继续保留 `StatisticsDataVO.trainCourseNum/trainSignNum/trainAvgScore` 供既有调用兼容
- `StatisticsDataVO` 新增复合属性 `nutritionKitchenStatistics`，类型为新增 VO `NutritionKitchenStatisticsVO`
- 杭州页面接口读取 `nutritionKitchenStatistics`
- 质量评分列表新增布尔字段 `canEditQualityScore`
- `judgeIsLimitAppoint` 现有调用保持不动，杭州新增课型校验抽成独立方法维护

## 2. 勘察结论摘要
- 杭州活动后台列表入口在 `CourseOfflineController#getCourseOfflineList`
- App 预约主链在 `CourseOfflineService#appoint`
- 动态表单配置读取在 `CourseOfflineService#getFieldList`
- 活动总结读写在 `CourseOfflineService#getSummary/saveSummary`
- 科学育儿统计在 `CourseOfflineService#selectStatistics/selectSubStatisticsList`
- 当前高风险点是 `course_type >=`、普通活动专属分支、统计仍用 `co.type = 2`

## 3. 实现设计

### 3.1 主模型与枚举
- 在 `ActivityConstants.CourseOfflineType` 中新增 `NUTRITION_KITCHEN = 4`，并补齐 `CLASSROOM = 3`
- `CourseOffline` 增加：
  - `qualityScore`
  - `qualityScoreUserId`

### 3.2 杭州项目开关
- 所有本次新增行为统一以 `Constants.PROJECT_NAME_HANGZHOU.equals(projectName)` 为前置条件

### 3.3 营养厨房接入
- `course_type=4`
- 动态表单读取 `configType=3`
- 复用普通活动保存、详情、预约、统计主链
- 不接入本次新增的时间冲突限制与质量评分

### 3.4 预约链路
- 保留 `judgeIsLimitAppoint(dto.getIdCard())` 原调用位置
- 在加载活动后新增 `validateHangzhouCourseTypeRules(courseOffline, dto)`
- 普通活动执行杭州时间冲突校验
- 营养厨房不执行本次时间冲突校验
- 同课程重复预约防重扩展到 `course_type in (1,4)`

### 3.5 活动总结
- 普通活动：四项内容 `bingUpShare`、`healthPropagate`、`parentChildInteraction`、`bringUpExpand` 全部必填
- 营养厨房：使用 `course_offline_summary.content`，长度限制 1000

### 3.6 质量评分
- 新增接口 `POST /courseOffline/qualityScore/save`
- 仅杭州项目、仅监管账号、仅 `course_type=1`
- 仅保存：
  - `quality_score`
  - `quality_score_user_id`
- 列表返回：
  - `qualityScore`
  - `canEditQualityScore`

### 3.7 科学育儿统计
- `StatisticsDataVO` 保留 `trainCourseNum/trainSignNum/trainAvgScore`
- 新增 `nutritionKitchenStatistics`
- 杭州项目厨房统计通过新属性返回
- 导出时把新属性平铺为“营养厨房”列

### 3.8 动态表单多 configType
- `field/list` 保留单 `configType`
- 新增 `configTypes`
- 多值查询走 `IN`
- 保存接口不变

## 4. 实施顺序
1. 落地 spec 文档
2. 补齐枚举、主表字段、DTO/VO
3. 改 `course_field` 多 `configType`
4. 改营养厨房主链复用与杭州精确查询
5. 改杭州预约课型校验
6. 改活动总结分流
7. 增加质量评分接口与列表返回
8. 改杭州科学育儿统计与导出
9. 编译验证与联调

## 5. 验证要点
- 杭州普通活动时间重叠预约被拦截
- 杭州营养厨房不触发本次时间冲突校验
- 普通活动与营养厨房列表互不串数
- 活动总结按课型分流校验
- 质量评分仅首录用户可修改
- 科学育儿统计页面与导出一致返回营养厨房数据
- 非杭州项目行为不变

## 6. 维护记录

### 2026-03-27
- 按 `b9edfd03 feat(course): implement SYZH V2.0.4 for nutrition kitchen integration and quality scoring` 的改动范围补充维护性注释：
  - 为本次新增或调整的方法补充 JavaDoc
  - 为杭州课型校验、质量评分权限回填、多 `configType` 查询、营养厨房统计组装等关键调用点补充行级注释
- 对 `CourseOfflineDao.xml` 的 `selectStatisticsForHangzhou` 进行维护性重构：
  - 将与 `selectStatistics` 共用的知识发布统计、养育照护活动统计、扩展业务统计提取为 `<sql>` 片段
  - 通过 `<include>` + `<property>` 方式仅替换杭州营养厨房统计条件和字段别名
  - 严格要求重构前后统计逻辑一致，杭州口径仅在扩展业务统计条件上由原实现的厨房条件承接，不改变其余统计规则
