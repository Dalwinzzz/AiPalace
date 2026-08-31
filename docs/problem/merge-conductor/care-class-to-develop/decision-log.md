# merge-conductor decision log

- task: care-class-to-develop
- mode: backport / semantic transplant
- working_branch: merge/care-class-to-develop
- source: refactor/micro-core-dev@d5b40412fde74ae65e7f18b093c4c6daacd4c712
- target: develop@8e414953aca53ba00c9e2e3db466d15067fbc7a5

## timeline
- Stage 2：用户确认归并策略 OK
- Stage 3：基于 develop 创建工作分支 `merge/care-class-to-develop`
- Stage 4/5：按语义回并方式补齐课堂常量、课堂保存/详情/H5 展示、课堂导出逻辑
- Stage 5：保留 develop 现状中的杭州/南京等后续迭代逻辑，不回退到 refactor 实现
- Stage 7：完成代码暂存与提交，提交 SHA `58860138`
- Stage 8：`mvn -f skc-activity/pom.xml -DskipTests compile` 验证通过，工作分支状态干净，归并会话 finalized
- 续接任务：基于 `58860138` 继续补齐源分支遗漏的嘉善课堂教师从表与指导单位逻辑
- 续接归并：新增 `course_offline_teacher`、`course_offline_js` ORM；在 develop 现有活动保存、详情、列表、H5、预约详情链路中按 `projectName == JIASHAN` 接入
- 续接策略：指导单位筛选使用 SQL `exists`，避免在 PageHelper 分页查询前执行额外查询导致分页被提前消费
- 续接验证：`git diff --check` 通过；`mvn -f skc-activity/pom.xml -DskipTests compile` 编译通过
- 续接提交：完成代码暂存与提交，提交 SHA `4ac7b54b`
- Review 修正：人工修复后继续核对源分支三张表实体差异；确认 `course_offline_summary.content` 的 domain/example/mapper 链路当前分支已存在
- Review 修正：同步 `course_offline.course_type`、`course_offline.age`、`course_offline_appoint.age_month` 字段注释语义，去除课堂注释中的嘉善项目限定
- Review 修正：`normalizeCareClassTeacherName` 改为仅按 `courseType=CARE_CLASS` 使用 `teacherList` 维护课堂教师展示名，避免其他地区复用课堂模块时被项目名拦截
- Review 验证：`git diff --check` 通过；`mvn -nsu -f skc-activity/pom.xml -DskipTests compile` 编译通过
- Review 提交：完成代码暂存与提交，提交 SHA `4f98e9ec`
