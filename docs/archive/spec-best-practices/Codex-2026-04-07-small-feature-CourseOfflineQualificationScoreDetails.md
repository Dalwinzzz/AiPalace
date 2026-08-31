# SYZH 质量评分明细化改造 Spec

## Summary
本次迭代在历史质量评分实现基础上，把“只存总分”升级为“主表总分 + 从表小项明细快照”。  
主表 `course_offline` 继续保留 `quality_score`、`quality_score_user_id`，用于列表展示、权限判断和总分口径；新增从表 `course_offline_quality_score_detail` 保存每个小项的分值。  
继续复用现有 `POST /courseOffline/qualityScore/save`，请求 DTO 新增 `Map<Integer, Integer> details`；同时新增一个质量评分详情读取接口，用于评分弹窗回显。  
本次交付物明确包含两个文档产物：
- `skc-activity/docs/syzh/2026-04-07-syzh-v2.0.4-quality-score-detail-codex-spec.md`
- `skc-activity/docs/syzh/2026-04-07-syzh-v2.0.4-quality-score-detail-ddl.sql`

## 关键改动

### 1. 数据模型与 ORM
- 新增表 `course_offline_quality_score_detail`，字段只保留：
  - `id`
  - `course_id`
  - `item_index`
  - `item_score`
- 不加物理外键约束，沿用项目现有风格，`course_id` 仅作为业务外键使用。
- 增加唯一索引 `uk_course_item(course_id, item_index)`，避免同一活动同一小项重复落库。
- 增加普通索引 `idx_course_id(course_id)`，支撑按活动查询和删除。
- ORM 层按现有项目规范完整新增：
  - `CourseOfflineQualityScoreDetail`
  - `CourseOfflineQualityScoreDetailExample`
  - `CourseOfflineQualityScoreDetailMapper`
  - `CourseOfflineQualityScoreDetailMapper.xml`

### 2. 保存接口改造
- 继续使用 `POST /courseOffline/qualityScore/save`。
- `CourseOfflineQualityScoreDTO` 扩展为：
  - `courseId`
  - `qualityScore`
  - `Map<Integer, Integer> details`
- 请求示例：
```json
{
  "courseId": 123,
  "qualityScore": 86,
  "details": {
    "1": 3,
    "2": 4,
    "3": 5
  }
}
```
- 保存规则明确如下：
  - 现有权限规则完全不变：
    - 仅市级、区级监管账号可评分
    - 仅养育照护活动支持质量评分
    - 首次评分后，仅 `quality_score_user_id` 对应用户可修改
  - 当 `details` 非空时：
    - 服务端按 `item_index` 升序处理
    - `details` 的 value 求和作为最终总分
    - 主表 `quality_score` 以服务端求和结果为准
    - 入参 `qualityScore` 仅做兼容保留，不作为最终可信来源
    - 事务内先删旧明细，再插入新明细
  - 当 `details` 为空时：
    - 若该活动从未有明细，兼容旧逻辑，仅更新主表总分
    - 若该活动已存在明细，直接拒绝保存并返回明确错误，避免主从不一致
- 明细校验约束：
  - `details` 的 key、value 都不能为空
  - key 必须为正整数
  - value 必须为非负整数
  - 最终总分必须在 `0-100`
- 事务要求：
  - 主表更新、旧明细删除、新明细插入必须同事务提交或回滚

### 3. 详情回显接口
- 当前仓库没有质量评分详情读取接口，不能只加从表不补读链路。
- 新增接口：
  - `GET /courseOffline/qualityScore/detail/{courseId}`
- 返回 VO 建议字段：
  - `courseId`
  - `qualityScore`
  - `LinkedHashMap<Integer, Integer> details`
  - `canEditQualityScore`
- 读取规则：
  - 使用活动数据权限查询，保持与现有质量评分权限口径一致
  - 同权限范围内监管账号可查看详情，不要求必须是首录用户
  - `canEditQualityScore` 继续沿用当前规则：
    - 未评分时可编辑
    - 已评分时仅 `quality_score_user_id == 当前用户` 可编辑
  - 明细按 `item_index` 升序组装为有序 Map，保证回显稳定
- 不改造通用 `GET /courseOffline/detail/{courseId}`，避免影响已有课程详情链路。

### 4. 现有链路保持不变
- `/courseOffline/list` 继续只返回：
  - `qualityScore`
  - `canEditQualityScore`
- `fillQualityScorePermission(...)` 的权限判定逻辑保持不变。
- 营养厨房仍不支持质量评分。
- 历史老数据兼容策略：
  - 主表已有 `quality_score`、从表无记录时
  - 新详情接口返回 `qualityScore=主表值`
  - `details={}` 空 Map
  - 不尝试反推旧明细

## DDL 约束
DDL 文档按现有 `syzh` 风格输出 MySQL 版本，文件路径：
- `skc-activity/docs/syzh/2026-04-07-syzh-v2.0.4-quality-score-detail-ddl.sql`

推荐建表语句如下：
```sql
-- 善于在杭活动需求ddl：质量评分明细从表
CREATE TABLE `course_offline_quality_score_detail` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键',
  `course_id` int NOT NULL COMMENT '活动ID',
  `item_index` int NOT NULL COMMENT '质量评分小项索引',
  `item_score` int NOT NULL COMMENT '质量评分小项分值',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_course_item` (`course_id`, `item_index`),
  KEY `idx_course_id` (`course_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='活动质量评分明细';
```

DDL 约束说明：
- 不新增外键约束，避免影响现网表迁移与历史脏数据兼容。
- `item_index`、`item_score` 都使用 `int`，与现有主表质量分值口径保持一致。
- 若部署环境包含 Kingbase，DBA 按同等逻辑转换建表语句；代码层不依赖数据库方言特性。

## 实施顺序
1. 落盘 spec 文档和 DDL 文档。
2. 新增从表 domain / example / mapper / mapper xml。
3. 扩展 `CourseOfflineQualityScoreDTO.details`。
4. 改造 `CourseOfflineService.saveQualityScore(...)`，完成主表总分与从表明细事务写入。
5. 新增 `GET /courseOffline/qualityScore/detail/{courseId}` 控制器、服务方法和返回 VO。
6. 复用现有权限判定逻辑，统一详情回显中的 `canEditQualityScore`。
7. 编译验证与回归测试。

## Test Plan
1. 首次评分保存
- 传入 `details`
- 主表 `quality_score` 等于明细求和
- 从表按 `item_index` 全量落库
- `quality_score_user_id` 写入当前用户

2. 同一首录用户修改评分
- 旧明细被删除
- 新明细完整重建
- 主表总分同步更新
- 不产生重复 `(course_id, item_index)` 记录

3. 非首录用户修改
- 返回“仅首次评分用户可修改评分”
- 主表和从表都不变

4. 详情回显
- 新接口返回总分、升序 `details`、`canEditQualityScore`
- 非首录但有数据权限的用户可读、不可编辑

5. 历史老数据兼容
- 主表有总分、从表无记录时
- 新接口返回空 `details`
- 列表总分展示保持原样

6. 旧客户端兼容
- 不传 `details` 且该活动没有明细时，沿用旧总分保存逻辑
- 不传 `details` 且该活动已有明细时，明确拒绝，避免主从不一致

7. 业务回归
- `/courseOffline/list` 的 `qualityScore / canEditQualityScore` 不回退
- 营养厨房评分入口仍不可用
- 市级/区级监管账号限制不回退

## Assumptions
- 前端评分模板顺序由 `details` 的 key 表示，key 与评分表中的小项顺序一一对应。
- 本次不做历史评分明细迁移，也不从旧总分反推小项分值。
- 本次不新增“删除评分”接口；对外仍只有“保存/修改”和“读取详情”。
- 当前线程处于 Plan Mode，本轮输出的是可直接执行的最终实施 spec；实际落盘与编码按本 spec 执行。
