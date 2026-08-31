驿站活动统计接口性能优化(mapper `course/CourseOfflineDao.xml`,`selectStationYearGrade` / `selectStationGrade`)。首次修复分支 refactor/micro-core-dev,commit `ab3ff3e3`(2026-07-08,已 push)。

**根因**:`getStationYearGrade/{id}` 是单驿站查询,但原 SQL 内层派生表对全库所有 dept 做完整聚合,最后才 JOIN station 用 `s.id` 过滤丢弃;且 cot/grade/people 三个相关子查询逐行全表扫 `course_offline_appoint`。EXPLAIN 表现:5 个 `DEPENDENT SUBQUERY` 全 type=ALL。

**本次优化(不改表结构)**:① 年度版内层下推 `co.dept_id = (SELECT dept_id FROM station WHERE id=#{vo.id})`,单驿站不再全量聚合;② 三个相关子查询合并为按 `course_id` 分组的 `agg` 派生表一次 LEFT JOIN;③ 列表版 `selectStationGrade` 同样合并(列表不能下推单 dept)。dev-mysql 实测改写前后统计逐行一致。

**根治待补(需 DDL,本次因"不改表结构"未做)**:`course_offline_appoint` 目前**只有主键 + idx_userId,无 course_id 索引**——统计子查询全靠 course_id 过滤,是最大瓶颈。建议 `ADD INDEX idx_course_state(course_id, state)`;`course_offline` 只有主键,建议 `(dept_id, state)`。若接口仍慢,先补这两个索引。

**字段归属易错点(踩过)**:
- `activity_image / activity_video / activity_word`(点滴记录 activit 判定)在 **`course_offline_record`(cor)**,不在 `course_offline`——那个 `LEFT JOIN course_offline_record` 是必需的,别当无用 JOIN 删掉(cor.course_id 唯一,一对一不膨胀)。
- `is_will / synthesize_score` 在 **`course_offline_evaluate`(coe)**,不在 course_offline_appoint。

相关:[[skcactivity-build]] [[third-party-integration-package]]
