thread_id: 019e8803-ba74-7971-aa42-eb412d4148cb
updated_at: 2026-06-03T07:20:14+00:00
rollout_path: /Users/dalwin/.codex/sessions/2026/06/02/rollout-2026-06-02T19-06-46-019e8803-ba74-7971-aa42-eb412d4148cb.jsonl
cwd: /Users/dalwin/Library/IdeaProject/ZhiJin/gongshu/gsskservers

# 生产环境 course_offline 删除活动残留预约的 SQL 运维脚本生成

Rollout context: 用户要求结合前一轮对 `course_offline` 活动删除影响的代码勘查结论，生成可在 DBeaver 中执行的生产数据库运维 SQL；目标是修复已删除活动残留数据对移动端预约的影响。

## Task 1: 生成删除活动残留预约的生产修复 SQL

Outcome: success

Preference signals:
- 用户说“我将通过 dbeaver 连接工具去运维生产环境的数据库相关业务表数据” -> 后续应默认输出可直接在 DBeaver 执行的、分步骤的运维脚本，而不是只给抽象结论。
- 用户要求“根据业主需求结合代码勘查结论给出数据运维的 sql 脚本” -> 后续类似任务应把代码勘查结论落到具体 SQL，且要区分预检 SQL、执行 SQL、复核 SQL。
- 在前一轮已定位影响点后，用户继续追问脚本而不是再要解释 -> 表明用户此类场景更需要可执行脚本优先于长篇分析。

Key steps:
- 先确认 SQL Expert DBA 路由，归类为生产数据修复/业务 SQL 生成。
- 复用前一轮代码证据：移动端预约冲突校验在 `sunkidsh5server`，关键表是 `course_offline_appointment`；删除活动后残留的 `state = 1` 预约会继续参与冲突判断。
- 额外检查本仓 `./sql/` 上下文，发现只有 `sunkidsdistdrserver/docs/sql`，没有现成的项目级 SQL 索引/业务规则可直接复用，因此脚本按已确认代码事实降级生成。
- 输出了带注释的事务脚本：先按 `course_offline.id` 预检目标行，再查残留预约，再 `START TRANSACTION`、`SELECT ... FOR UPDATE`、`UPDATE course_offline_appointment ... SET state = 0, update_time = NOW()`，最后复核 `remaining_stale_appointment_count`。

Failures and how to do differently:
- 需要先锁定唯一 `course_offline.id`，不能按活动名称直接更新；脚本里明确把名称模糊匹配放在“仅用于查找候选 id”的预检步骤。
- `course_offline_sign` 不应作为修复对象；它不参与新活动预约的主门禁，只影响签到/评价/详情按钮态。
- 代码与实体注释存在状态语义不一致：实体注释写了 `2=未签到且活动删除`，但后台删除预约记录的实际代码是把 `course_offline_appointment.state` 置为 `0`；运维脚本应跟随代码实际行为而不是只看注释。

Reusable knowledge:
- 真实业务表名是 `course_offline_appointment`，不是口述中的 `course_offline_appoint`。
- 移动端预约冲突校验使用 `course_offline_appointment` 关联 `course_offline` 的时间段，但**没有**过滤 `course_offline.state`，所以删除态主表仍可能通过残留预约记录影响新预约。
- 后台删除链路把 `course_offline.state` 置为 `2`，并且只在特定时机级联处理预约状态；时机较晚时，残留 `state=1` 预约会继续影响冲突校验。
- 本仓没有独立的 SQL 索引/业务规则目录可直接用于此任务，主要还是依赖代码勘查结果生成脚本。

References:
- [1] `sunkidsh5server/src/main/java/com/iktapp/api/controller/CourseOfflineController.java:124-168` — 移动端预约入口 `makeAppointment()`；失败码映射包括 `APPOINTMENT_OTHER_LIMIT`、`COURSE_OFFLINE_NOTEXIST` 等。
- [2] `sunkidsh5server/src/main/java/com/iktapp/api/service/courseoffline/CourseOfflineServiceImpl.java:186-270` — 预约前校验：截止时间、人数上限、同时间段冲突、同课重复预约、年龄段匹配、仅 `courseOffline.getState() == COURSE_ON` 才可插入预约。
- [3] `sunkidsh5server/src/main/resources/mapper/CourseOfflineDao.xml:93-106` — `getOtherAppointment()` 只按 `a.state = 1` + 时间段 join `course_offline` 判断冲突，未过滤 `course_offline.state`。
- [4] `sunkidsdistdrserver/src/main/java/com/iktapp/api/controller/CourseOfflineController.java:253-260` — 管理端删除活动接口把状态设为 `COURSE_DELETE`。
- [5] `sunkidsdistdrserver/src/main/java/com/iktapp/api/service/courseoffline/CourseOfflineServiceImpl.java:410-462` — 删除活动实际只改主表状态；仅在“删除且当前时间早于签到开始时间”时才会把预约状态改为 0 并发消息。
- [6] `sunkidsh5server/src/main/java/com/iktapp/api/constants/BusinessConstants.java:165-175, 271-272` — `APPOINTMENT_OTHER_LIMIT=10114`，提示文案为“您已经在该活动时间范围内预约了其他活动，请预约其他时间范围的活动”；`APPOINT_ERROR=1029`。

## Task 2: 校对生产运维脚本的执行边界

Outcome: success

Preference signals:
- 用户强调要“通过 dbeaver 连接工具”运维生产库 -> 后续脚本要默认包含事务、预检、复核，且提示关闭 auto-commit 或手工 COMMIT/ROLLBACK。
- 用户场景是生产数据修复 -> 后续应明确区分“查找候选”“预检”“执行”“复核”四段，避免直接给危险的单句 UPDATE。

Key steps:
- 检查仓内 SQL 上下文，仅发现 `./sql` 目录但没有可直接复用的课程业务索引。
- 以 `course_offline.id` 为唯一定位键，避免按活动名称直接修改生产数据。
- 在脚本中显式保留 `SELECT ... FOR UPDATE` 与 `ROW_COUNT()` 复核，方便 DBeaver 中逐步执行。

Failures and how to do differently:
- 不要将“代码里可能的状态语义”误当成“数据库里必须这样改”；应以已确认的后台实际更新语句为准。
- 遇到含删除/回滚风险的生产脚本时，默认先写可回滚事务脚本，而不是单条 UPDATE。

Reusable knowledge:
- 如果目标是修复“已删除活动仍阻塞移动端预约”，优先修正 `course_offline_appointment.state` 的残留有效预约，而不是动 `course_offline_sign`。
- 复核标准应是：残留 `state=1` 且关联删除态主表的预约记录应归零，且同身份证再次预约重叠新活动不再命中 `10114`。

References:
- [1] `find . -maxdepth 3 -type d -name sql -o -path './sql/.index' -o -path './sql/biz-rules'` → 仅发现 `./sunkidsdistdrserver/docs/sql`。
- [2] `rg -n "course_offline_appointment|CREATE TABLE.*course_offline|course_offline_sign" . -g '*.sql' -g '*.xml'` → 发现相关表/SQL 主要分布在 `sunkidsh5server` 和 `sunkidsdistdrserver` 的 mapper/liquibase 中。
- [3] `sunkidsh5server/src/main/resources/mapper/CourseOfflineAppointmentMapper.xml`、`CourseOfflineMapper.xml` — 可用于判断表结构/状态字段和更新方式。
