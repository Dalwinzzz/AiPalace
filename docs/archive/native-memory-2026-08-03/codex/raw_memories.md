# Raw Memories

Merged stage-1 raw memories (stable ascending thread-id order):

## Thread `019db450-50c4-7b03-86dd-98747e2aabe2`
updated_at: 2026-07-03T09:06:40+00:00
cwd: /Users/dalwin/.codex/worktrees/6308/skcnursery/skc-nursery
rollout_path: /Users/dalwin/.codex/sessions/2026/04/22/rollout-2026-04-22T16-30-55-019db450-50c4-7b03-86dd-98747e2aabe2.jsonl
rollout_summary_file: 2026-04-22T08-30-55-fz3A-eeds_nursery_class_capacity_repair_sql.md

---
description: Production read-only verification for 鄂尔多斯 nursery total-capacity=0 bug; confirmed code fix in NurseryClassDisplaySupport and generated guarded Kingbase backfill SQL for nursery id 111824.
task: 鄂尔多斯 nursery 总托位数为0 的生产核验与修复SQL生成
task_group: skc-nursery / nursery capacity / Kingbase read-only repair
 task_outcome: partial
cwd: /Users/dalwin/.codex/worktrees/6308/skcnursery/skc-nursery
keywords: skc-nursery, Kingbase, dbq, 鄂尔多斯-正式, NurseryClassDisplaySupport, computeOrderedTypes, refreshNurseryClassSummary, nursery_class_limit, nursery_class_scope_limit, nursery_audit_info, work_flow_service_info, read-only SQL, mismatch scan
---

### Task 1: 鄂尔多斯总托位数为0排查与修复SQL

task: review commit 0a6ac6a3 and 60b8ec1d; verify production nursery capacity mismatch; generate safe Kingbase repair SQL for skcity.nursery id 111824
task_group: production DB investigation / data repair SQL
task_outcome: partial

Preference signals:
- when the user wants a DBA-style review / repair, they expect code review + live data verification + a ready-to-execute repair SQL, not just a diagnosis.
- when the environment is read-only, the workflow should stay read-only for verification and only emit a handoff SQL patch for manual execution.

Reusable knowledge:
- `NurseryClassDisplaySupport.buildFormalClassLimitSnapshot()` feeds both profile display and main nursery summary; stale snapshot ordering can corrupt persisted `nursery.scope` as well as read-time display.
- `0a6ac6a32` fixes the prevention layer by making `computeOrderedTypes()` keep only effective class types and not treat snapshot order as a whitelist.
- For nursery `111824`, production evidence showed `nursery.scope=0` while the formal class tables summed to `type4=10班 / 200托位`, and the latest passing audit row was `class_types=4, scope=200`.
- The production `nursery` table in `skcity` does not contain `record_class_num`; repair SQL must target only actual columns: `scope`, `class_types`, `class_num`, `class_scope`, `update_time`.

Failures and how to do differently:
- An initial production query tried to select a non-existent `record_class_num` column; future similar queries should check `information_schema.columns` first.
- A query against `nursery_audit_info` also hit schema mismatch because the production table has fewer columns than the local entity model; production column inspection should happen before building validation SQL.
- There are 4 total mismatch nurseries in the full scan, but only `111824` had enough evidence for this ticket; do not batch-repair the others without separate root-cause confirmation.

References:
- `0a6ac6a32e40341547bc5cc5405febdae5bd8735`
- `60b8ec1d6` (`docs/problem/20260703-鄂尔多斯机构画像总托位数为0.md`)
- `dbq 鄂尔多斯-正式`
- Target row: `skcity.nursery id=111824`
- Verified derived result for 111824: `fixed_class_types=4`, `fixed_class_num=10`, `fixed_class_scope=200`, `fixed_scope=200`
- Repair SQL pattern used: `WITH ... FULL JOIN ... UPDATE skcity.nursery ... WHERE n.id=111824 AND f.fixed_class_types='4' AND f.fixed_class_num=10 AND f.fixed_class_scope='200' AND f.fixed_scope=200`

## Thread `019db8fd-2366-75d0-a90f-48999e97e7e9`
updated_at: 2026-07-22T08:37:32+00:00
cwd: /Users/dalwin/.codex/worktrees/36a8/skcactivity
rollout_path: /Users/dalwin/.codex/sessions/2026/04/23/rollout-2026-04-23T14-18-10-019db8fd-2366-75d0-a90f-48999e97e7e9.jsonl
rollout_summary_file: 2026-04-23T06-18-10-4g2d-develop_worktree_courseoffline_copy_age_detail_analysis.md

description: 创建 develop 基准 bugfix worktree，并结合 release/syzh260110 代码、生产库和操作日志定位复制活动 63761 年龄显示异常；结论是后端保存与详情查询正确，旧值来自前端复制状态/海报组装，服务端 alterPosterImg 缺少一致性校验
 task: create develop-based bugfix worktree and diagnose courseOffline copied-activity age display mismatch
 task_group: skcactivity/courseOffline production debugging
 task_outcome: success
 cwd: /Users/dalwin/.codex/worktrees/36a8/skcactivity
 keywords: git-worktree, origin/develop, release/syzh260110, courseOffline, ageString, ageList, alterPosterImg, getById, dbq, sys_oper_log, PostgreSQL
---

### Task 1: 创建 develop 基准 bugfix worktree

task: create isolated bugfix worktree from latest origin/develop
task_group: git workflow
 task_outcome: success

Preference signals:
- 用户说“先以develop分支的最新代码commit情况为基准检出一个专用于bug修复任务的worktree” -> 类似任务先 `git fetch origin develop`，确认远端 commit 后再建隔离 worktree。

Reusable knowledge:
- `origin/develop` 刷新后为 `eae90dd6aab64ed8276e071e7c4718ab6be6d1e6`。
- 创建命令：`git worktree add /Users/dalwin/.codex/worktrees/36a8/skcactivity-bugfix -b codex/bugfix-develop-20260423 origin/develop`。
- 新 worktree `/Users/dalwin/.codex/worktrees/36a8/skcactivity-bugfix`，分支 `codex/bugfix-develop-20260423`，跟踪 `origin/develop`，状态干净。
- 项目根目录没有 `pom.xml`；基线编译命令 `mvn -f skc-activity/pom.xml -DskipTests compile`，结果 `BUILD SUCCESS`。

Failures and how to do differently:
- 未发现项目内 `.worktrees/`、`worktrees/` 或 CLAUDE.md 目录约定，因此 worktree 放在 Codex worktree 组旁边。Maven 的 Nexus 401/systemPath/API 警告是现有环境问题，不影响本次 compile 成功判断。

References:
- commit: `eae90dd6aab64ed8276e071e7c4718ab6be6d1e6`
- worktree: `/Users/dalwin/.codex/worktrees/36a8/skcactivity-bugfix`
- branch: `codex/bugfix-develop-20260423`

### Task 2: 诊断复制活动 63761 的年龄显示异常

task: inspect production release branch and verify copied activity detail response
 task_group: courseOffline production debugging
 task_outcome: success

Preference signals:
- 用户要求使用生产部署分支并结合截图、SQL、截断日志分析 -> 类似线上问题交叉核对部署代码、Mapper SQL、生产数据与 `sys_oper_log`。
- 用户明确要求核对“复制后新建的63761这个记录的返回数据是否正确” -> 沿 Controller → Service → Mapper 还原详情接口，并逐字段对数据库。

Reusable knowledge:
- 生产表位于 `skcity` schema；只读查询使用 `/Users/dalwin/Library/ConfigFile/db/dbq '善于在杭正式查询' "<SELECT>"`。
- `CourseOfflineDao.xml:getById` 直接读取 `c.age` 与 `c.age_string`；`CourseOfflineService.getDetail` 将 `age` 以逗号拆成 `ageList`。对 `courseId=63761`，详情应返回：`age=7,8,9,10,11,12,13,14,15,16,17,18,19,20`、`ageString=6-48月龄`、`ageList=['7',...,'20']`。
- 生产日志确认 `2026-07-22 14:59:51` `/courseOffline/save` 提交 `ageList=[7..20]` 并返回 `courseId=63761`；数据库中 63761 同样保存 `age=7..20`、`age_string=6-48月龄`。
- 源活动 `63438` 使用 `[6,20]`，数据库为 `age_string=5月龄,36-48月龄`。截图旧值精确对应源活动，不是新活动。
- 时间线：63761 保存 14:59:51，上传海报 14:59:54，删除 15:01:34；63761 当前已 `state=-1`，详情 SQL过滤逻辑删除，所以不能直接重新请求复现历史响应。
- `alterPosterImg`（`CourseOfflineService.java:2681-2689`）只信任前端传入的 JPEG 路径并更新 `poster_img`，不生成或校验图片内容。服务端无法修正一张已由前端用旧 `ageString` 渲染的图片。
- 结论：后端新增保存、`ageToString`、详情 SQL均正确；页面旧年龄来自前端复制后未刷新新对象、错误传入源 `courseId`、或海报组件继续使用源活动缓存。服务端仍有防御漏洞：海报接口缺少活动版本/部门校验，且编辑保存分支存在未同步 `age`/`ageString` 的风险。

Failures and how to do differently:
- 不要仅凭截图判断数据库错误；必须核对保存请求、详情响应字段、海报上传请求和日志。
- 前端实现未在当前工作区中定位，前端责任点是由接口和生产数据证据推断；复现时检查 Network：保存返回 ID、是否请求 `/detail/63761`、该响应的 `ageString`、以及海报生成读取的数据对象。
- 要彻底消除同类问题，应让服务端根据新 `courseId` 查询持久化活动数据后生成海报；短期至少使用专用 DTO、权限/部门校验、版本校验、保存后返回完整详情并强制新记录清空 `poster_img`。

References:
- Controller detail: `skc-activity/src/main/java/com/iktapp/skc/activity/controller/staff/StaffCourseOfflineController.java:210-225`
- Service detail: `skc-activity/src/main/java/com/iktapp/skc/activity/service/courseoffline/CourseOfflineService.java:1289-1315`
- Mapper detail SQL: `skc-activity/src/main/resources/mapper/activity/CourseOfflineDao.xml:973-1053`
- Poster endpoint: `CourseOfflineController.java:1238-1244`; `CourseOfflineService.java:2681-2689`
- Read-only DB evidence: `courseId=63761`, `age=7..20`, `age_string=6-48月龄`; source `63438`, `age=6,20`, `age_string=5月龄,36-48月龄`
- Key log handles: `oper_id=14548336` save 63761; `oper_id=14548338` poster upload; deletion `oper_id=14548387`.

## Thread `019e4dcc-42a4-7cc3-9ee4-7c464ccf4969`
updated_at: 2026-07-20T13:13:44+00:00
cwd: /Users/dalwin/Library/IdeaProject/ZhiJin/SunkidCloud/skcservers/skcdatasum
rollout_path: /Users/dalwin/.codex/sessions/2026/05/22/rollout-2026-05-22T11-48-12-019e4dcc-42a4-7cc3-9ee4-7c464ccf4969.jsonl
rollout_summary_file: 2026-05-22T03-48-12-d3yp-jianye_dynamic_key_independent_transactions.md

description: 修复南京建邺驾驶舱定时汇总整批事务回滚问题，将每个动态 key 隔离为独立 REQUIRES_NEW 事务，并推送 develop
 task: 南京建邺动态指标事务隔离与定时任务异常隔离
 task_group: skc-datasum/nanjing-dashboard
 task_outcome: success
 cwd: /Users/dalwin/Library/IdeaProject/ZhiJin/SunkidCloud/skcservers/skcdatasum
 keywords: NanjingJianyeDashboardDynamicServiceImpl, DataSchedule, REQUIRES_NEW, TransactionTemplate, biz_*, query timeout, nurseryList-320105, stateCorp, develop, f642d84e
---

### Task 1: 建邺动态指标独立事务

task: 将建邺驾驶舱每个动态 key 的查询、计算、落库拆为独立事务
 task_group: skc-datasum/nanjing-dashboard
 task_outcome: success

Preference signals:
- 用户要求“每个指标key的动态统计是独立事物，一个事物失败不要影响其他统计指标的事物统计和提交更新” -> 后续类似汇总任务应按 key 建立事务边界，而不是使用整批事务。

Reusable knowledge:
- `NanjingJianyeDashboardDynamicServiceImpl.refreshDynamicData` 当前按 10 个 key 顺序调用 `refreshMetric`。
- `refreshMetric` 使用 `TransactionTemplate`，传播级别为 `PROPAGATION_REQUIRES_NEW`；单项异常被捕获并记录，后续 key 继续执行。
- 成功日志格式：`南京建邺动态指标刷新完成，key=...，areaCode=...`。
- 失败日志格式：`南京建邺动态指标刷新失败，已回滚当前指标并继续后续任务，key=...，areaCode=...`。
- 本地回归测试模拟 `selectChildHealthOverview` 抛出 `query timeout`，验证 10 个独立事务、1 次回滚、9 次提交。

Failures and how to do differently:
- 原实现外层 `@Transactional(rollbackFor = Exception.class)` 包住所有查询与写入；任一 `biz_*` 查询超时会中断后续 key，并导致已写入数据整体回滚。未来不要在此入口恢复整批事务。

References:
- `src/main/java/com/iktapp/skc/datasum/service/nanjing/impl/NanjingJianyeDashboardDynamicServiceImpl.java:100`
- `src/main/java/com/iktapp/skc/datasum/service/nanjing/impl/NanjingJianyeDashboardDynamicServiceImpl.java:428`
- `mvn -q -Dtest=NanjingJianyeDashboardDynamicServiceImplTest,NanjingJianyeDashboardDynamicWriterContractTest test`

### Task 2: 南京总定时任务模块隔离

task: 防止南京动态任务前置模块失败阻断建邺 writer
 task_group: skc-datasum/nanjing-scheduler
 task_outcome: success

Reusable knowledge:
- `DataSchedule.updateNanjingDailyDynamicData()` 通过 `executeNanjingDynamicTask` 分别执行照护机构、中央审核、首页总览、街道托位分布、建邺驾驶舱任务。
- 每个模块异常单独记录并继续后续模块，最终仍可执行 `nanjingJianyeDashboardDynamicService.refreshDynamicData("320105")`。

References:
- `src/main/java/com/iktapp/skc/datasum/schedule/nbbl/DataSchedule.java:1245`
- `executeNanjingDynamicTask(String, Runnable)`

### Task 3: 验证、提交与推送

task: 验证事务隔离改动并提交推送
 task_group: git-release/skc-datasum
 task_outcome: success

Reusable knowledge:
- 验证通过：建邺服务测试、writer 合同测试、模块编译、`git diff --check`。
- 本地忽略的测试文件未提交；最终仅提交两个生产源码文件。

References:
- Commit: `f642d84e fix(nanjing): 隔离建邺动态指标统计事务`
- Push result: `200af27f..f642d84e develop -> develop`
- `git push origin develop`

## Thread `019e8803-ba74-7971-aa42-eb412d4148cb`
updated_at: 2026-06-03T07:20:14+00:00
cwd: /Users/dalwin/Library/IdeaProject/ZhiJin/gongshu/gsskservers
rollout_path: /Users/dalwin/.codex/sessions/2026/06/02/rollout-2026-06-02T19-06-46-019e8803-ba74-7971-aa42-eb412d4148cb.jsonl
rollout_summary_file: 2026-06-02T11-06-46-nKrh-course_offline_deleted_activity_production_sql_fix.md

---
description: 生产环境修复 course_offline 已删除活动残留预约影响，生成 DBeaver 可执行的事务型 SQL 脚本；关键结论是优先修复 course_offline_appointment.state 残留记录，避免继续阻塞移动端预约。
task: 生产数据修复 SQL 生成：清理已删除 course_offline 活动残留预约
task_group: gsskservers / course_offline / production data maintenance
question_type: sql-report-query-builder
cwd: /Users/dalwin/Library/IdeaProject/ZhiJin/gongshu/gsskservers
keywords: course_offline, course_offline_appointment, course_offline_sign, DBeaver, production SQL, transaction, SELECT FOR UPDATE, ROW_COUNT, APPOINTMENT_OTHER_LIMIT, state=2, state=1, mobile appointment, overlap check
---

### Task 1: 生成删除活动残留预约的生产修复 SQL

task: 生产数据修复 SQL 生成：清理已删除 course_offline 活动残留预约
task_group: gsskservers / course_offline / production data maintenance
task_outcome: success

Preference signals:
- 用户说“我将通过 dbeaver 连接工具去运维生产环境的数据库相关业务表数据” -> 后续应默认输出可直接在 DBeaver 执行的、分步骤的运维脚本，而不是只给抽象结论。
- 用户要求“根据业主需求结合代码勘查结论给出数据运维的 sql 脚本” -> 后续类似任务应把代码勘查结论落到具体 SQL，且要区分预检 SQL、执行 SQL、复核 SQL。
- 用户追问脚本而不是再要解释 -> 表明此类场景更需要可执行脚本优先于长篇分析。

Reusable knowledge:
- 真实业务表名是 `course_offline_appointment`，不是口述中的 `course_offline_appoint`。
- 移动端预约冲突校验使用 `course_offline_appointment` 关联 `course_offline` 的时间段，但没有过滤 `course_offline.state`，所以删除态主表仍可能通过残留预约记录影响新预约。
- 后台删除链路把 `course_offline.state` 置为 `2`，并且只在特定时机级联处理预约状态；时机较晚时，残留 `state=1` 预约会继续影响冲突校验。
- 代码与实体注释存在状态语义不一致：实体注释写了 `2=未签到且活动删除`，但后台删除预约记录的实际代码是把 `course_offline_appointment.state` 置为 `0`；运维脚本应跟随代码实际行为而不是只看注释。

Failures and how to do differently:
- 需要先锁定唯一 `course_offline.id`，不能按活动名称直接更新；脚本里把名称模糊匹配只放在查找候选 id 的预检步骤。
- `course_offline_sign` 不应作为修复对象；它不参与新活动预约的主门禁，只影响签到/评价/详情按钮态。
- 遇到生产修复脚本时，默认写成可回滚事务脚本，并包含预检、复核、`ROW_COUNT()`。

References:
- `sunkidsh5server/src/main/java/com/iktapp/api/controller/CourseOfflineController.java:124-168` — 移动端预约入口 `makeAppointment()`。
- `sunkidsh5server/src/main/java/com/iktapp/api/service/courseoffline/CourseOfflineServiceImpl.java:186-270` — 预约前校验：截止时间、人数上限、同时间段冲突、同课重复预约、年龄段匹配、仅 `courseOffline.getState() == COURSE_ON` 才可插入预约。
- `sunkidsh5server/src/main/resources/mapper/CourseOfflineDao.xml:93-106` — `getOtherAppointment()` 只按 `a.state = 1` + 时间段 join `course_offline` 判断冲突，未过滤 `course_offline.state`。
- `sunkidsdistdrserver/src/main/java/com/iktapp/api/controller/CourseOfflineController.java:253-260` — 管理端删除活动接口把状态设为 `COURSE_DELETE`。
- `sunkidsdistdrserver/src/main/java/com/iktapp/api/service/courseoffline/CourseOfflineServiceImpl.java:410-462` — 删除活动实际只改主表状态；仅在“删除且当前时间早于签到开始时间”时才会把预约状态改为 0 并发消息。
- `sunkidsh5server/src/main/java/com/iktapp/api/constants/BusinessConstants.java:165-175, 271-272` — `APPOINTMENT_OTHER_LIMIT=10114`，提示文案为“您已经在该活动时间范围内预约了其他活动，请预约其他时间范围的活动”；`APPOINT_ERROR=1029`。

### Task 2: 校对生产运维脚本的执行边界

task: DBeaver 生产库运维脚本边界校对
task_group: gsskservers / course_offline / production data maintenance
task_outcome: success

Preference signals:
- 用户强调要“通过 dbeaver 连接工具”运维生产库 -> 后续脚本要默认包含事务、预检、复核，且提示关闭 auto-commit 或手工 COMMIT/ROLLBACK。
- 用户场景是生产数据修复 -> 后续应明确区分“查找候选”“预检”“执行”“复核”四段，避免直接给危险的单句 UPDATE。

Reusable knowledge:
- 如果目标是修复“已删除活动仍阻塞移动端预约”，优先修复 `course_offline_appointment.state` 的残留有效预约，而不是动 `course_offline_sign`。
- 复核标准应是：残留 `state=1` 且关联删除态主表的预约记录应归零，且同身份证再次预约重叠新活动不再命中 `10114`。

Failures and how to do differently:
- 不要将代码里的可能状态语义误当成数据库修复目标；应以已确认的后台实际更新语句为准。
- 生产脚本默认先写事务型可回滚版本，而不是直接给最终 UPDATE。

References:
- `find . -maxdepth 3 -type d -name sql -o -path './sql/.index' -o -path './sql/biz-rules'` → 仅发现 `./sunkidsdistdrserver/docs/sql`。
- `rg -n "course_offline_appointment|CREATE TABLE.*course_offline|course_offline_sign" . -g '*.sql' -g '*.xml'` → 相关表/SQL 主要分布在 `sunkidsh5server` 和 `sunkidsdistdrserver` 的 mapper/liquibase 中。
- `sunkidsh5server/src/main/resources/mapper/CourseOfflineAppointmentMapper.xml`、`CourseOfflineMapper.xml` — 用于判断表结构/状态字段和更新方式。

## Thread `019e9b0c-3968-7bd2-baf0-5114a5379f17`
updated_at: 2026-07-28T06:30:54+00:00
cwd: /Users/dalwin/Library/IdeaProject/ZhiJin/SunKidServer
rollout_path: /Users/dalwin/.codex/sessions/2026/06/06/rollout-2026-06-06T11-48-50-019e9b0c-3968-7bd2-baf0-5114a5379f17.jsonl
rollout_summary_file: 2026-06-06T03-48-50-Ay8f-sunkidserver_gaode_migration_and_xinchuang_qrcode_routing.md

---
description: Migrated basic GaoDe geocoding from Redis queue polling to direct public API and diagnosed Xinchuang QR-code routing configuration; key takeaway is to trace the producer service's Nacos Data ID, not just the H5 service config.
task: GaoDe direct API migration and QR-code Nacos routing diagnosis
task_group: SunKidServer multi-repository Java/Spring deployment workflow
task_outcome: partial
cwd: /Users/dalwin/Library/IdeaProject/ZhiJin/SunKidServer
keywords: GaoDeServiceImpl, GaoDeMapUtil, Redis, qrcode_register_url, qrcode_register_param, h5_url, sknurseryserver-prod, skh5server-prod, Nacos, MinIO, DatabaseType
---

### Task 1: GaoDe direct public API migration

task: Replace `sunkids-basic` Redis-based GaoDe lookup with direct `GaoDeMapUtil` invocation.
task_group: skframework/sunkids-basic service migration
task_outcome: partial

Preference signals:
- The user asked for the implementation to be “consistent with pubserver” and to call the public network directly -> reuse the existing common `GaoDeMapUtil` implementation and preserve existing API/error semantics.

Reusable knowledge:
- `/gaode/getLatLng` in both `skdistdrserver` and `skstreetdrserver` delegates to `skframework/sunkids-basic` `GaoDeService`; changing `GaoDeServiceImpl` centralizes the behavior.
- Old flow: `convertAndSend("getLatLng", dto)` -> `Thread.sleep(500)` -> read Redis key `getLatLng + address`.
- Implemented `GaoDeCoordinateClient` wrapping `com.iktapp.common.utils.GaoDeMapUtil.getLngAndLat`; `GaoDeServiceImpl` now validates input, calls the client, and preserves `ParamErrorException` for null/missing coordinates.
- Dependency workflow: after changing `sunkids-basic`, run `mvn -q -pl sunkids-basic -DskipTests install` before compiling dependent API repositories.

Failures and how to do differently:
- `skstreetdrserver` compilation is independently blocked by missing `com.iktapp.common.enums.DatabaseType` in `DataBaseConfiguration`; treat it as pre-existing dependency/branch debt, not a GaoDe regression.
- Global ignore rules hide `**/*Test.java` and `**/spec-architect/`; explicitly inspect ignored files when checking deliverables.

References:
- `skframework/sunkids-basic/src/main/java/com/iktapp/basic/service/gaode/GaoDeServiceImpl.java`
- `skframework/sunkids-basic/src/main/java/com/iktapp/basic/service/gaode/GaoDeCoordinateClient.java`
- `skframework/sunkids-basic/src/test/java/com/iktapp/basic/service/gaode/GaoDeServiceImplTest.java`
- Passing: `mvn -q -pl sunkids-basic -Dtest=GaoDeServiceImplTest test`; `mvn -q -pl sunkids-basic -DskipTests compile`; `mvn -q -pl sunkids-basic -DskipTests install`; `mvn -q -DskipTests compile` in `skdistdrserver`.

### Task 2: Xinchuang QR-code routing diagnosis

task: Identify which Nacos settings control institution activity QR-code destinations after migration.
task_group: production Nacos/H5/QR deployment troubleshooting
task_outcome: success

Preference signals:
- After confirming the Xinchuang Nacos database is correct, the user specifically redirected investigation to `qrcode_register_url` -> separate database, URL, service, and Data ID checks instead of repeating database diagnosis.

Reusable knowledge:
- Institution QR generation is in `sknurseryserver/src/main/java/com/iktapp/api/controller/CourseOfflineController.java`, where the QR content is `qrcode_register_url + qrcode_register_param + courseId`.
- The screenshot’s `skh5server-prod` settings are not the controlling source for institution QR generation. The producer loads `sknurseryserver-prod`; this is the first Nacos Data ID to correct.
- Required effective configuration shape is: `h5_url=<externally reachable Xinchuang H5 root>`, `qrcode_register_url=${h5_url}activityDetail`, `qrcode_register_param=?courseId=`. For course 1498, decode the QR and expect `<root>/#/activityDetail?courseId=1498`.
- Also validate `minio.endpoint`, `minio.port`, and `minio.bucketName` in the producer environment. `uploadfpath.QRcode` is local QR file output in `QrCodeUtil`, not the public QR routing URL.
- Updating Nacos does not rewrite previously generated QR images/posters; restart/reload the producer as needed and regenerate the QR artifact.

Failures and how to do differently:
- Do not modify only `skh5server-prod` based on the screenshot; trace the `@Value` consumer first. The relevant consumer is `sknurseryserver`.

References:
- `sknurseryserver/src/main/java/com/iktapp/api/controller/CourseOfflineController.java:75-120`
- `skh5server/src/main/resources/application-prod.properties`
- `sknurseryserver/src/main/resources/application-prod.properties`
- `skframework/sunkids-basic/src/main/java/com/iktapp/basic/utils/qrcode/QrCodeUtil.java`
- Production Data IDs: `sknurseryserver-prod`, `skh5server-prod`, `skdistserver-prod`, `skstreetdrserver-prod`.

## Thread `019eb147-cc27-75f2-8a8f-429830a72983`
updated_at: 2026-07-31T06:22:53+00:00
cwd: /Users/dalwin/Library/IdeaProject/ZhiJin/SunkidCloud/skcservers/skcnursery/skc-nursery
rollout_path: /Users/dalwin/.codex/sessions/2026/06/10/rollout-2026-06-10T19-25-33-019eb147-cc27-75f2-8a8f-429830a72983.jsonl
rollout_summary_file: 2026-06-10T11-25-33-eWUb-skc_nursery_tu.md

---
description: 诊断善于在杭托育券两类“无权查询/出生日期为空”问题，并更新排查报告；关键 takeaway 是区分空家庭关系缓存误判与前端儿童证件号错传
 task: diagnose-and-document-infant-query-authorization-errors
task_group: skc-nursery/善于在杭托育券排查
 task_outcome: success
cwd: /Users/dalwin/Library/IdeaProject/ZhiJin/SunkidCloud/skcservers/skcnursery/skc-nursery
keywords: skc-nursery, 善于在杭, getInfantOwnInfo, getInfantInfo, infantIdCard, validateMobileInfantCaller, family-relationship-cache, zheliban_user, user_child, dbq
---

### Task 1: 定位杨帆、杨婷异常

task: diagnose-and-document-infant-query-authorization-errors
task_group: skc-nursery/托育券东软链路
task_outcome: success

Preference signals:
- 用户要求将错误原因写入指定排查报告，并明确杨婷“前端调用的哪个接口传入了错误的参数” -> 类似问题应主动给出接口路径、参数名、错误参数语义、正确参数来源。

Reusable knowledge:
- 杨帆的正式库 `user_child` 关系显示其确实绑定目标儿童，但日志命中 `dr-family-cache cacheHit=true, result=[]`；这是空家庭关系缓存造成的水平越权误判，不是真实无权。清缓存后重试，并确认出现 `dr-family-request`、`dr-family-raw-response`、`dr-family-parsed-result`。
- 杨婷调用 `GET /app/nursery/coupon/getInfantOwnInfo` 时，把家长证件号传入 `infantIdCard`。该接口要求婴幼儿证件号；前端应传用户选择/录入的儿童证件号，不能传 `guardianIdCard` 或登录用户证件号。
- `NurseryCouponDrServiceImpl.getInfantOwnInfoDetail()` 先调用 `validateMobileInfantCaller()`，随后才查询儿童详情；空家庭关系和目标儿童不匹配最终都可能表现为“当前用户无权查询该证件号信息”。

Failures and how to do differently:
- 生产 SQL UNION 因 boolean/text 类型冲突失败：`ERROR: UNION types boolean and text cannot be matched`；后续改用独立查询和 EXISTS。
- 脱敏查询初次输出异常，后续先核查字段类型/长度，再用首尾字符脱敏和布尔等值判断，避免误读结果。

References:
- `/Users/dalwin/Library/ConfigFile/db/dbq '善于在杭正式查询'`
- `src/main/java/com/iktapp/skc/nursery/service/nurserycoupon/NurseryCouponDrServiceImpl.java:204`
- `src/main/java/com/iktapp/skc/nursery/service/nurserycoupon/NurseryCouponDrServiceImpl.java:1164`
- 关键日志：`stage=dr-family-cache cacheHit=true, result=[]`

### Task 2: 更新排查报告

task: update-infant-birthday-troubleshooting-report
task_group: skc-nursery/文档交付
 task_outcome: success

Preference signals:
- 用户希望报告记录完整证据链，而不是只写结论；杨婷案例必须写明 `GET /app/nursery/coupon/getInfantOwnInfo` 与错误的 `infantIdCard` 参数。

Reusable knowledge:
- 报告已新增杨帆、杨婷汇总行和独立章节，并扩展“无权查询”统一判断口径：空缓存误判、前端错传家长证件号、真实关系不匹配需分开处理。
- 最终文件：`/Users/dalwin/Downloads/善于在杭托育券-婴幼儿出生日期为空问题排查报告.md`，最终校验为 345 行。

Failures and how to do differently:
- 报告先复制到 `/private/tmp/善于在杭托育券-婴幼儿出生日期为空问题排查报告.md` 修改，再覆盖回 Downloads；这种方式适合受限文件系统下的外部文档更新。

References:
- `/Users/dalwin/Downloads/善于在杭托育券-婴幼儿出生日期为空问题排查报告.md`
- 校验关键词：`GET /app/nursery/coupon/getInfantOwnInfo`、`infantIdCard=3306**********5024`、`空家庭关系缓存`

## Thread `019ec015-039a-7fd0-8d4e-8d95235648cd`
updated_at: 2026-07-30T10:39:54+00:00
cwd: /Users/dalwin/Library/IdeaProject/ZhiJin/SunkidCloud/skcservers/skcadminframework
rollout_path: /Users/dalwin/.codex/sessions/2026/06/13/rollout-2026-06-13T16-24-23-019ec015-039a-7fd0-8d4e-8d95235648cd.jsonl
rollout_summary_file: 2026-06-13T08-24-23-7zgp-skc_system_liquibase_dual_db_delivery.md

---
description: Repository-ready MySQL/Kingbase Liquibase workflow in skc-system, including safe handling of unrelated changes, Maven verification, rebase conflict resolution, commit, and push
task: maintain dual-database Liquibase create-table migrations
task_group: skc-system-liquibase
task_outcome: success
cwd: /Users/dalwin/Library/IdeaProject/ZhiJin/SunkidCloud/skcservers/skcadminframework
keywords: liquibase, skc-system, mysql, kingbase, changelog, rebase, maven, git-push, physical-lab-report
---

### Task 1: Repository Liquibase workflow

task: create-table Liquibase migrations for MySQL and Kingbase
 task_group: skc-system-liquibase
 task_outcome: success

Preference signals:
- When the user provides source DDL, use it as the primary source and preserve the requested author exactly, e.g. `wangzhiheng`.
- The user expects verification, commit, rebase on conflict, and push when explicitly requested.
- Preserve unrelated working-tree edits; stage only files belonging to the requested migration.

Reusable knowledge:
- Liquibase lives under `skc-modules/skc-system/src/main/resources/liquibase`; helper-script repo root is `skc-modules/skc-system`.
- Create-table work always uses separate `_mysql.sql` and `_kingbase.sql` files and one changeSet per file.
- Kingbase project style uses `bigserial`/`serial` for auto-increment IDs, named primary-key constraints, and indexes outside `CREATE TABLE`.
- Monthly changelog paths follow `changelog/YYYY/MM/changelog-YYYYMM.xml`; `master.xml` includes the changelog directory recursively.
- Use `scripts/ensure_month_changelog.py` and `scripts/next_changeset_id.py` rather than hand-counting IDs.

Failures and how to do differently:
- Root-level `src/main/resources/liquibase` does not exist; locate the module containing `master.xml` first.
- Full `git diff --check` can fail on unrelated pre-existing files. Run scoped checks on migration files and leave unrelated edits untouched.
- Startup without external configuration failed with `dynamic-datasource can not find primary datasource`; configured startup then could not reach Kingbase (`Connection ... refused` / sandbox network restriction). Report startup as unverified/blocked rather than claiming success.

References:
- `mvn -q -pl skc-modules/skc-system -am test`
- `mvn -q -pl skc-modules/skc-system -am -DskipTests package`
- `git rebase origin/develop`
- `git push origin develop`

### Task 2: Git delivery and conflict handling

task: rebase, commit, and push Liquibase changes on develop
 task_group: git-delivery
 task_outcome: success

Preference signals:
- The user wants conflicts handled by rebase and expects the requested commit to be pushed, not merely prepared locally.
- The user wants unrelated API changes left in the working tree and excluded from the commit/push.

Reusable knowledge:
- Rebase may require elevated permission to write `.git/rebase-merge`.
- For changelog tail conflicts, preserve remote changeSets and append local changeSets with unique IDs; validate XML and duplicate IDs before `git add` and `git rebase --continue`.
- A push may fail under restricted DNS/network; retry the same push with elevated network permission. Successful evidence was `1dd86aeb..2e7d9025 develop -> develop`.

References:
- Commit: `2e7d9025 feat(system): 嘉善体检数据同步需求v1.3.2需求表结构ddl`
- Final status after push: `## develop...origin/develop`; unrelated API files remained modified.

## Thread `019ece8b-abb3-7af1-83fc-70dba6b3819d`
updated_at: 2026-07-24T08:54:31+00:00
cwd: /Users/dalwin/Library/CodeRepo/AI
rollout_path: /Users/dalwin/.codex/sessions/2026/06/16/rollout-2026-06-16T11-48-40-019ece8b-abb3-7af1-83fc-70dba6b3819d.jsonl
rollout_summary_file: 2026-06-16T03-48-40-h0KN-aipalace_scheduled_upstream_sync_with_local_skill_exclusion.md

description: AiPalace GitHub 上游 skill 定时同步已落地并持续成功；需保护本地 skill-management 版本，按文件报告并自动提交
 task: recurring AiPalace upstream repository sync and hard-copy skill refresh
 task_group: /Users/dalwin/Library/CodeRepo/AI scheduled workflow
 task_outcome: success
 cwd: /Users/dalwin/Library/CodeRepo/AI
 keywords: AiPalace, upstream_sync.py, schedule-sync-github2palace, heartbeat, git fetch, git pull, hard-copy sync, skill-management, EXCLUDED_TARGETS, langchain master, codex定时任务, repo-local logs
---

### Task 1: 执行 AiPalace 上游同步

task: Run `python3 AiPalace/tools/upstream_sync.py --commit` for the recurring heartbeat workflow.
task_group: AiPalace scheduled upstream sync
task_outcome: success

Preference signals:
- 用户要求结果回报包含“本次自动处理了哪些文件，策略是什么” -> 类似任务必须报告具体 updated/added/kept 文件、未映射项和同步策略。
- 用户要求提交 message 附带“(codex定时任务)” -> 保持提交信息 `chore: 同步上游 skills 硬拷贝（codex定时任务）`。
- 用户明确要求 `skills/community/garveyhu/method/skill-management` 不再从 awesome-skills 覆盖，因为 AiPalace 已有本地迭代版本 -> 默认始终保护并在报告中说明跳过。

Reusable knowledge:
- 执行入口固定为 `AiPalace/tools/upstream_sync.py`。
- `--commit` 会先更新七个上游仓，再同步来源明确的 AiPalace 硬拷贝，最后仅在有 AiPalace 变更时提交。
- `langchain` 的远端默认分支是 `master`，不是 `main`；脚本会自动回退并报告。
- 只复制源中存在的文件；AiPalace 目标目录独有文件保留，不自动删除。
- `EXCLUDED_TARGETS` 中固定包含 `skills/community/garveyhu/method/skill-management`。

Failures and how to do differently:
- 首次受限执行 `git fetch origin` 报 `CalledProcessError ... exit status 128`；重试需使用联网/提权环境，先区分环境网络失败与脚本逻辑失败。
- 不要把上游仓库更新数量等同于 AiPalace skill 更新数量；分别统计。

References:
- Command: `python3 AiPalace/tools/upstream_sync.py --commit`
- Verification: `python3 AiPalace/tools/upstream_sync.py --skip-pull`
- Commit message: `chore: 同步上游 skills 硬拷贝（codex定时任务）`
- Automation id: `schedule-sync-github2palace`

### Task 2: 日志与调度配置

task: Remove launchd configuration and move logs into the repository.
task_group: AiPalace scheduling/logging
 task_outcome: success

Reusable knowledge:
- 旧的 `AiPalace/tools/com.dalwin.aipalace-upstream-sync.plist` 和系统 `~/Library/LaunchAgents/com.dalwin.aipalace-upstream-sync.plist` 已删除；不要再假设 launchd 仍承载任务。
- 脚本自动创建 `AiPalace/logs/` 并写入：`AiPalace/logs/aipalace-upstream-sync.log`、`AiPalace/logs/aipalace-upstream-sync.err.log`。
- `.gitignore` 已忽略 `logs/`。

References:
- Commit: `8dd4344 chore: 移除launchd并切换仓库日志`
- Log paths: `AiPalace/logs/aipalace-upstream-sync.log`, `AiPalace/logs/aipalace-upstream-sync.err.log`

### Task 3: 本地 skill-management 排除规则

task: Exclude AiPalace's locally evolved skill-management from awesome-skills synchronization.
task_group: AiPalace local override policy
 task_outcome: success

Preference signals:
- 用户明确说明该 skill“我的 AiPalace 内已经迭代了自己的版本” -> 该本地版本优先于上游，除非用户明确撤销例外，否则不得覆盖。

Reusable knowledge:
- 脚本中的 `EXCLUDED_TARGETS` 会把 `skills/community/garveyhu/method/skill-management` 放入保留列表；报告应出现“该 skill 在 AiPalace 内已演进为本地版本，按约定跳过上游覆盖”。
- 2026-07-24 运行验证了该排除规则仍有效；即使 awesome-skills 有更新，也不应同步该目录。

References:
- Code handle: `EXCLUDED_TARGETS`
- Exact path: `skills/community/garveyhu/method/skill-management`
- Report wording: `该 skill 在 AiPalace 内已演进为本地版本，按约定跳过上游覆盖`
- Latest verified commit: `973a49b`

## Thread `019ed42b-af9f-7230-bd50-9ea7f7de4fb5`
updated_at: 2026-06-17T08:05:57+00:00
cwd: /Users/dalwin/Library/IdeaProject/ZhiJin/SunkidCloud/skcservers/skcactivity
rollout_path: /Users/dalwin/.codex/archived_sessions/rollout-2026-06-17T14-01-33-019ed42b-af9f-7230-bd50-9ea7f7de4fb5.jsonl
rollout_summary_file: 2026-06-17T06-01-33-qOG1-skcactivity_physicalexam_deptid_and_hospital_config_fixes.md

---
description: New physical-exam module fixes: moved dept_id anchoring from request DTOs to server-side login/binding sources, then added a separate hospital-config controller/service for the new physicalExam module that reuses Hospital table but avoids the old南京硬匹配 path; both changes were compiled/tested, synced to Apifox, and committed.
task: physical-exam review fixes plus new hospital-config endpoints
 task_group: /Users/dalwin/Library/IdeaProject/ZhiJin/SunkidCloud/skcservers/skcactivity
task_outcome: success
cwd: /Users/dalwin/Library/IdeaProject/ZhiJin/SunkidCloud/skcservers/skcactivity
keywords: physicalexam, dept_id, SecurityUtils, InfantUtil, StaffUtil, NurseryUtil, Hospital, HospitalMapper, HospitalExample, HospitalController, HospitalConfigAppService, Apifox, 南京, 建邺, Maven, JUnit4, BUILD_SUCCESS
---

### Task 1: Physical-exam dept_id anchoring fix

task: fix physical-exam dept_id source and remove DTO-supplied orgDeptId

task_group: physicalexam module

task_outcome: success

Preference signals:
- user required: "管理端由服务端从登录台获取，移动端改为从绑定的业务机构获取该机构的deptId，去掉接收参数dto的前端传入口径" -> prefer server-side authority over request-body deptId in this module
- user asked: "把当前工作区的修复内容commit提交一下" -> after verified fix, stage only the relevant files and commit

Reusable knowledge:
- H5 appointment flow is `AppPhysicalExamController -> AppointmentAppService.create`; admin direct-record flow is `ResultController -> ExamResultAppService.createDirect`
- `AppointCreateDTO` and `DirectExamCreateDTO` no longer carry `orgDeptId`; `PeAppointment.deptId` is filled server-side
- CHILD_ENTRY should derive deptId from default bound child nursery via `InfantUtil.getDefaultFamilyNurseryId()` -> `NurseryUtil.getDeptId(nurseryId)`
- STAFF_HEALTH should derive deptId from `StaffUtil.getStaffInfo()` / `deptId`, with fallback via `nurseryId -> NurseryUtil.getDeptId(...)`
- admin direct-record path should use `SecurityUtils.getDeptId()` and throw if null

Failures and how to do differently:
- one-size-fits-all binding lookup was wrong; the repo uses different binding sources for child/family vs staff flows, so branch by exam type
- `SecurityUtils.getDeptId()` can be null; guard it explicitly rather than assuming login context is always populated

References:
- `skc-activity/src/main/java/com/iktapp/skc/activity/physicalexam/application/appointment/AppointmentAppService.java`
- `skc-activity/src/main/java/com/iktapp/skc/activity/physicalexam/application/report/ExamResultAppService.java`
- `skc-activity/src/main/java/com/iktapp/skc/activity/physicalexam/dto/app/AppointCreateDTO.java`
- `skc-activity/src/main/java/com/iktapp/skc/activity/physicalexam/dto/admin/DirectExamCreateDTO.java`
- commit `62710409 fix(physicalexam): 修复体检机构权限锚点来源`
- compile/test evidence: `BUILD SUCCESS`, 88 physical-exam tests passed

### Task 2: Add dedicated physicalExam hospital-config endpoints and sync Apifox

task: add new module-local physicalExam hospital config endpoints backed by Hospital table

task_group: physicalexam config surface

task_outcome: success

Preference signals:
- user said the physical-exam unit config UI should reuse `Hospital` table and asked for the same-function interfaces under the new module -> prefer module-local wrapper endpoints over reusing legacy南京-only `/physicalExamination/*`
- user required: "改完代码后同步更新apifox接口文档，然后通过后直接提交" -> Apifox sync is part of done criteria before commit

Reusable knowledge:
- old 南京 `PhysicalExaminationServiceImpl.configHospital()` and `getHospitalDetail()` have南京-specific behavior: name hard-match against login username and token refresh side effects
- the new physical-exam module already splits config surfaces into `activity`, `slotPlan`, `signature`; `hospital` now fits as another dedicated controller under `/physicalExam/hospital`
- `HospitalMapper` + `HospitalExample` are sufficient to implement current-dept list/read/write without touching old `physicalExamination` code
- Apifox project `saas` -> module `activity` -> 南京 -> 配置管理端 is the right folder for the new endpoints

Failures and how to do differently:
- trying to reuse the old南京体检医院配置 path would preserve the wrong name-based readback logic; add a new module-local endpoint instead
- Apifox needed folder discovery before creation; create endpoints only after confirming the right folder to avoid misfiling

References:
- `skc-activity/src/main/java/com/iktapp/skc/activity/physicalexam/application/config/HospitalConfigAppService.java`
- `skc-activity/src/main/java/com/iktapp/skc/activity/physicalexam/controller/admin/HospitalController.java`
- Apifox endpoint IDs: `474898375` (`/physicalExam/hospital/configHospital`), `474898528` (`/physicalExam/hospital/getHospitalDetail`)
- old legacy code path: `skc-activity/src/main/java/com/iktapp/skc/activity/service/physicalexamination/PhysicalExaminationServiceImpl.java` (`configHospital`, `getHospitalDetail`)
- commit `11ccb793 feat(physicalexam): 新增体检单位配置接口`
- verification: `git diff --cached --check` clean; `mvn -nsu -f skc-activity/pom.xml -DskipTests compile` success; `mvn -nsu -f skc-activity/pom.xml -Dtest='com.iktapp.skc.activity.physicalexam.**.*Test' test` success (88 tests)

## Thread `019f2b20-8375-7e30-a545-b6ac7778967a`
updated_at: 2026-07-21T07:59:20+00:00
cwd: /Users/dalwin/Library/IdeaProject/WaveFlow/wavetrans
rollout_path: /Users/dalwin/.codex/sessions/2026/07/04/rollout-2026-07-04T11-16-18-019f2b20-8375-7e30-a545-b6ac7778967a.jsonl
rollout_summary_file: 2026-07-04T03-16-18-EdNU-jiashan_lab_sync_create_missing_report_and_push.md

---
description: 嘉善检验同步跨 wavetrans/activity 双仓改造成功，支持无 physical_enter_result 报告的预约同步并已推送
 task: jiashan lab sync missing physical_enter_result report
 task_group: cross-repo Java/Spring data synchronization
 task_outcome: success
 cwd: /Users/dalwin/Library/IdeaProject/WaveFlow/wavetrans
 keywords: jiashan, kafka, physical_enter_result, physical_appoint_user, pauId, enterResultId, convert_history, LEFT JOIN, refactor/micro-core-dev, surefire
---

### Task 1: 嘉善检验同步支持缺失报告

task: 修改双侧嘉善检验同步链路，使仅有预约记录的对象也能同步
 task_group: wavetrans + skcactivity cross-repo workflow
 task_outcome: success

Preference signals:
- 用户说“双侧提交推送一下” -> 跨仓库改动应分别提交、推送，并核对本地 HEAD 与远端引用。

Reusable knowledge:
- wavetrans 分支为 `develop`；activity 实际部署分支为 `refactor/micro-core-dev`。
- 候选 SQL 从 `INNER JOIN physical_enter_result` 改为 `LEFT JOIN`，移除 `pau.pe_state` 过滤；有效 `pau` 且有身份证即可进入同步。
- 消息契约允许 `enterResultId=null`，activity 消费端按 `pauId` 定位或创建 `physical_enter_result`。
- 新报告创建后设置 `pauId/deptId/detail/isSign/isDelete/createTime/updateTime`，插入生成主键后再写完成标记。
- activity 先发布、wavetrans 后发布，避免旧消费者跳过缺失 `enterResultId` 的消息。
- 测试：wavetrans 3 个测试通过；activity 合并器 10 个、归一器 13 个测试通过；聚合编译和 `git diff --check` 通过。

Failures and how to do differently:
- 聚合测试首次因无测试模块触发 Surefire 失败；使用 `-Dsurefire.failIfNoSpecifiedTests=false`。
- activity 测试目录被 `.gitignore` 的 `**/src/test/` 排除且此前已从版本库删除，因此测试仅本地验证，不应强制重新提交。

References:
- `489ae43 fix(jiashan): 支持无体检报告预约同步`
- `47a449a2 fix(jiashan): 同步检验数据时自动创建报告`
- `wavetrans-job/src/main/resources/mapper/jiashan/JiaShanLabCandidateMapper.xml`
- `skc-activity/activity-plugin-jiashan/src/main/java/com/iktapp/skc/activity/plugin/jiashan/physical/service/impl/JiaShanPhysicalAppointmentServiceImpl.java`
- `git push origin develop`
- `git push origin refactor/micro-core-dev`

### Task 2: 南京日志收敛扫描

task: 扫描并压缩南京数据清洗过程日志
 task_group: wavetrans Nanjing logging
 task_outcome: uncertain

Preference signals:
- 用户要求“只最小限度保留便于运维排查的日志，去掉重复性的多余的日志输出” -> 保留任务级开始/结束、异常和必要统计，删除高频阶段明细。

Reusable knowledge:
- 重点范围：`wavetrans-job/src/main/java/com/iktapp/wavetrans/job/data/nanjing`。
- 主要噪声在多个 service 的 `processorContext.log(...)` Load/Transform 明细，以及 `NanjingProdSingleBatchCursorProcessor` 的 Extract/Transform/Load 阶段完成日志。

Failures and how to do differently:
- 本任务仅完成扫描和定位，未修改代码、未提交、未验证；后续需从上述文件继续处理。

References:
- `wavetrans-job/src/main/java/com/iktapp/wavetrans/job/data/nanjing/prod/support/NanjingProdSingleBatchCursorProcessor.java`
- 典型日志前缀：`南京疾控儿童监护关系 Load 明细`、`南京疾控高危体弱随访 Load 明细`、`南京儿童疫苗同步 Transform 明细`

## Thread `019f5a0d-b0b3-75b3-a8b8-531319b8b326`
updated_at: 2026-07-17T07:09:14+00:00
cwd: /Users/dalwin/Library/IdeaProject/ZhiJin/SunkidCloud/skcservers/skcinfant
rollout_path: /Users/dalwin/.codex/sessions/2026/07/13/rollout-2026-07-13T13-57-54-019f5a0d-b0b3-75b3-a8b8-531319b8b326.jsonl
rollout_summary_file: 2026-07-13T05-57-54-cFW6-skcinfant_exam_detail_code_dictionary_fix.md

description: 修复 skcinfant 儿童体检详情码值转换并推送，仅提交业务源文件；验证全模块测试通过
 task: 修复儿童体检详情面色、皮肤、发育评估、指导意见、是否转诊等码值展示
 task_group: skcinfant-infant-health-portrait
 task_outcome: success
 cwd: /Users/dalwin/Library/IdeaProject/ZhiJin/SunkidCloud/skcservers/skcinfant
 keywords: ExamCodeDict, ChildHealthPortraitServiceImpl, ExamDetailVO, 多选字典, yesNo, 生产码值, Maven, git push, develop

### Task 1: 儿童体检详情字典转换

task: 根据生产码值和官方省级字典修复详情接口展示
 task_group: skcinfant-infant-health-portrait
 task_outcome: success

Preference signals:
- 用户要求“提交推送src源文件，测试文件先留在本地自行维护即可” -> 提交时只暂存并提交 `src/main` 业务源文件，测试文件留在本地。

Reusable knowledge:
- 面色使用专用字典：`1=红润, 2=黄染, 3=潮红, 4=苍白, 5=发绀, 9=其他`。
- 皮肤是多选字符串：`01=未见异常, 02=潮红, 03=苍白, 04=发绀, 05=黄染, 06=色素沉着, 07=湿疹, 08=糜烂, 99=其他`。
- 发育评估：`0=未评估, 1=通过, 2=未通过`。
- 指导意见多选：`1=科学喂养, 2=生长发育, 3=疾病预防, 4=预防伤害, 5=口腔保健, 6=合理膳食, 9=其他指导`。
- 生产 `yesNo` 口径为 `0=否, 1=是`，同时用于沙眼和是否转诊。
- 多选解析支持逗号/中文逗号、尾逗号、重复码、`1、科学喂养` 形式；按首次顺序去重，未知值原样返回。
- 已修改 `ExamCodeDict.java`、`ChildHealthPortraitServiceImpl.java`、`ExamDetailVO.java`。

Failures and how to do differently:
- Maven 首次因本机依赖仓库权限报 `FileNotFoundException ... resolver-status.properties (Operation not permitted)`；需要允许 Maven 访问本机依赖仓库后重试。
- 测试文件受全局 `**/*Test.java` 忽略规则影响，若以后需要提交必须使用 `git add -f`；本次按用户要求未提交。

References:
- Production evidence: `complexion=1` 48342 条、`skinCheck=01` 53643 条、`deveAsse=0` 66928 条、`dealOpinion=1` 70133 条、`ifTran=0` 81612 条。
- Commit: `519d018654bb1f26aec77b9367464b4252558e23`。
- Push: `git push origin develop` succeeded; local and remote develop synchronized (`0 0`).
- Verification: `mvn -q test` passed with 24 tests, 0 failures/errors; `git diff --check` passed.

## Thread `019f648a-a580-7b61-a7cc-7e3433c971e8`
updated_at: 2026-07-21T04:13:17+00:00
cwd: /Users/dalwin/Library/IdeaProject/ZhiJin/SunkidCloud/skcservers/skcnursery/skc-nursery
rollout_path: /Users/dalwin/.codex/sessions/2026/07/15/rollout-2026-07-15T14-50-35-019f648a-a580-7b61-a7cc-7e3433c971e8.jsonl
rollout_summary_file: 2026-07-15T06-50-35-NyWY-shanyu_zai_hang_coupon_analysis_and_district_code_mapping_fi.md

---
description: 修复机构详情范围查询因 MyBatis 隐式映射导致 districtCode 为空的问题，并覆盖 7415aa4877 的同类风险
 task: 修复 NurseryDao.selectNurseryByIdForScope 的实体字段映射并提交推送
 task_group: skc-nursery / MyBatis / 数据权限详情查询
task_outcome: success
cwd: /Users/dalwin/Library/IdeaProject/ZhiJin/SunkidCloud/skcservers/skcnursery/skc-nursery
keywords: 7415aa4877, NurseryDao.xml, selectNurseryByIdForScope, BaseResultMap, district_code, districtCode, MyBatis, DataScope, HorizontalAuthDataScopeContractTest, Maven, git push
---

### Task 1: 修复机构详情地区编码映射

task: 将范围查询从隐式 resultType 映射改为显式 NurseryMapper.BaseResultMap，并补回归测试
 task_group: skc-nursery / MyBatis / 水平越权修复
task_outcome: success

Preference signals:
- 用户说“按照你的建议修复来处理一下这个bug，同时针对7415aa4877这个提交中所有一样的问题一起用同样的方案进行修复，修复完成后直接提交推送” -> 明确授权后应完成全流程：盘点同类问题、修改、验证、commit、push。

Reusable knowledge:
- `7415aa4877` 新增的 `NurseryDao.selectNurseryByIdForScope` 使用 `select n.*` + `resultType=Nursery`，在项目未启用下划线转驼峰时不会把 `district_code` 映射为 `districtCode`。
- `NurseryMapper.xml` 的 `com.iktapp.skc.nursery.mapper.NurseryMapper.BaseResultMap` 明确包含 `district_code -> districtCode`，以及其他多单词字段映射；范围查询应复用该 resultMap。
- 根因调用链：`NurseryAuditController.getDetailById` → `NurseryService.getNurseryById(BaseEntity,id)` → `selectNurseryByIdForScope` → `getNurseryDetail` → `communityService.getNameByCode(nursery.getDistrictCode())`。
- 盘点 `7415aa4877` 后确认只有 `selectNurseryByIdForScope` 同时符合“实体 resultType + `select n.*`”风险模式；其他同类查询使用显式映射或列别名，无需扩大修改。

Failures and how to do differently:
- 一次运行期全量解析 `NurseryDao.xml` 的测试失败于夹具缺少无关依赖：`Could not find result map 'com.iktapp.skc.nursery.mapper.NurseryExtraInfoMapper.BaseResultMap'`。这不是修复代码失败；移除该不隔离测试，保留 XML 契约测试。以后做运行期 Mapper 测试要加载全部依赖或隔离目标映射。

References:
- 修改：`src/main/resources/mapper/nursery/NurseryDao.xml` 将 `resultType="com.iktapp.skc.nursery.domain.Nursery"` 改为 `resultMap="com.iktapp.skc.nursery.mapper.NurseryMapper.BaseResultMap"`，保留 `${scope.params.dataScope}`。
- 测试：`src/test/java/com/iktapp/skc/nursery/security/HorizontalAuthDataScopeContractTest.java` 新增 `scopedNurseryLookupShouldReuseExplicitNurseryResultMap`。
- 验证：定向 Maven 测试退出码 0；模块 `-DskipTests compile` 退出码 0；`git diff --check` 通过。
- 提交/推送：`1a2724b2b fix(nursery): 修复机构详情地区编码映射`，推送结果 `fe6122168..1a2724b2b develop -> develop`，最终工作区干净。

### Task 2: 善育在杭托育券月度天数工单分析

task: 结合代码和善于在杭正式库查询托育券月度天数异常并生成运维 SQL
 task_group: 善育在杭 / skc-nursery / 托育券 / 只读数据库分析
task_outcome: partial

Preference signals:
- 用户明确说“这是一个只读分析任务”，并允许查正式库 -> 默认只执行 SELECT，最终输出人工执行 SQL，不直接写库。
- 用户要求结合指定分支代码和正式环境数据，而不是仅凭截图猜测 -> 先核对代码口径、表结构、线上数据，再给 SQL。

Reusable knowledge:
- 正式库实例通过 `/Users/dalwin/Library/ConfigFile/db/dbq '善于在杭'` 访问，数据库使用 PostgreSQL 风格 `skc` schema。
- 已确认存在：`skc.nursery_child_sign_month_statistic`、`skc.nursery_coupon`、`skc.nursery_coupon_qualification_apply`、`skc.nursery_coupon_record`、`skc.nursery_coupon_subsidy_apply_detail` 等表。
- `NurseryCouponServiceImpl.nurseryChildSignMonthStatistic` 按 `id_card + data_month + coupon_type` 维护月度汇总；`NurseryCouponDao.xml` 多处以该汇总表关联券数据，补助明细读取 `in_nursery_days`。

Failures and how to do differently:
- 本阶段未完成截图中具体人员/月份的数据逐条核验，也未交付最终运维 SQL；后续必须继续从截图提取具体标识，查询月度汇总、2026 分区签到明细、券及核销/补助关联，再生成带校验条件的 SQL。
- 初次 dbq 连接被本机沙箱拦截，错误为 `ssh: connect to host 121.36.242.166 port 22: Operation not permitted`；申请网络授权后查询成功。

References:
- 代码定位：`src/main/java/com/iktapp/skc/nursery/service/nurserycoupon/NurseryCouponServiceImpl.java` 约 3864 行起。
- SQL 定位：`src/main/resources/mapper/nursery/NurseryCouponDao.xml`，月度汇总和托育券关联约 596、720、808、918、985、1137、1156、1211-1356 行。
- 成功查询表名的只读命令：`/Users/dalwin/Library/ConfigFile/db/dbq '善于在杭' "SELECT table_schema, table_name FROM information_schema.tables WHERE table_type = 'BASE TABLE' AND (...) ORDER BY table_schema, table_name LIMIT 500"`。

## Thread `019f69dd-503d-79f1-acb9-8d11d0d58eb5`
updated_at: 2026-07-16T07:58:47+00:00
cwd: /Users/dalwin/Library/IdeaProject/ZhiJin/SunkidCloud/skcservers/skcactivity
rollout_path: /Users/dalwin/.codex/archived_sessions/rollout-2026-07-16T15-38-59-019f69dd-503d-79f1-acb9-8d11d0d58eb5.jsonl
rollout_summary_file: 2026-07-16T07-38-59-6Z8N-apifox_nanjing_appointment_import_sync_and_delete_md.md

---
description: 将南京从业人员体检导入接口文档同步到 Apifox 的 saas/activity/体检管理/体检预约列表，并在确认后删除本地 md；关键 takeaway 是先刷新 Apifox 配置、核对同名目录、再创建并回读验证，且外发到 SaaS 需先取得用户明确确认。
task: sync apifox docs for nanjing physical appointment import APIs and delete local md
task_group: skcactivity / Apifox 文档同步
track_outcome: success
cwd: /Users/dalwin/Library/IdeaProject/ZhiJin/SunkidCloud/skcservers/skcactivity
keywords: Apifox, mcp__apifox__getProjectSummary, mcp__apifox__getStructureInfo, mcp__apifox__createHttpEndpoint, mcp__apifox__getHttpEndpoint, form-data, responseExamples, SaaS upload confirmation, folderId 76611615, projectId 6776425, activity module, local md delete
---

### Task 1: 同步南京从业人员体检导入接口到 Apifox 并删除本地 md

task: update docs/spec-architect/2026-07/16/nanjing-physical-appointment-import-api.md into Apifox saas project and delete local file
task_group: Apifox 文档同步 / skcactivity
task_outcome: success

Preference signals:
- 用户说“把这个文档通过mcp更新到我配置的apifox文档saas项目下。配置是正常的，你重新读取一下配置。文档更新好后删掉这个本地的md接口文档” -> 这类任务的默认完成标准是：先同步到 Apifox，再删除本地 md，不要只同步不清理。
- 用户在被提示外发风险后回复“确认同意，开始同步” -> 当 Apifox 上传被安全策略拦截时，先说明风险并等待明确确认；确认后再继续执行。

Reusable knowledge:
- `.apifox/6776425_saas.settings.json` 是本仓库的 Apifox 本地缓存入口；`getProjectSummary` 会返回 `saas` 项目结构、模块、endpointFolders、testCaseCategories 等。
- `saas` 项目 `activity` 模块下的 `体检管理 / 体检预约列表` folderId 是 `76611615`；同名嘉善旧目录是 `77355311`，两者需要先用 `getStructureInfo` 区分。
- 本次创建成功的接口 ID：`488219523`（`/physicalAppointment/appointUser/import`）和 `488219797`（`/physicalAppointment/appointUser/idCardPhoto/import`）。
- 回读时 `requestBody.type` 为 `form-data`，且 `responseExamples[].data` 必须保持字符串化 JSON，Apifox 桌面端才稳定渲染。
- 本地 md 删除后用 shell 复核最直接：`test -e <file> && echo PRESENT || echo DELETED`。

Failures and how to do differently:
- 首次同步被安全策略拒绝，原因是外部 SaaS 未被标记为可信外发目标；处理方式不是绕过，而是先请求用户明确同意再继续。
- 目录名存在同名项时不能凭名字猜测，必须用 `getStructureInfo` 或已有接口路径前缀核对所属目录。

References:
- `docs/spec-architect/2026-07/16/nanjing-physical-appointment-import-api.md`
- `mcp__apifox__getProjectSummary({projectId:6776425})`
- `mcp__apifox__getStructureInfo({projectId:6776425,moduleId:6989525,folderId:76611615,entityType:"endpoint"})`
- `mcp__apifox__getStructureInfo({projectId:6776425,moduleId:6989525,folderId:77355311,entityType:"endpoint"})`
- `mcp__apifox__createHttpEndpoint(...)` -> `id: 488219523`, `id: 488219797`
- `mcp__apifox__getHttpEndpoint({projectId:6776425,httpApiId:488219523})`
- `mcp__apifox__getHttpEndpoint({projectId:6776425,httpApiId:488219797})`
- shell delete verification output: `DELETED`

## Thread `019f745b-3e18-7380-ae80-6bb31cb57072`
updated_at: 2026-07-20T11:42:03+00:00
cwd: /Users/dalwin/Library/CodeRepo/AI/Codex-Dream-Skin
rollout_path: /Users/dalwin/.codex/sessions/2026/07/18/rollout-2026-07-18T16-32-44-019f745b-3e18-7380-ae80-6bb31cb57072.jsonl
rollout_summary_file: 2026-07-18T08-32-44-AXUm-bloodborne_lady_maria_theme_signature_backup_and_main_sync.md

---
description: Bloodborne 玛丽亚本机主题准备、ChatGPT 内置 Node 签名排查、Codex 数据备份与 main 同步；主题安装最终未完成
 task: prepare-and-apply-local-lady-maria-codex-theme
 task_group: Codex-Dream-Skin macOS workflow
 task_outcome: partial
 cwd: /Users/dalwin/Library/CodeRepo/AI/Codex-Dream-Skin
 keywords: macos, codex-dream-skin, bloodborne, lady-maria, custom-theme, codesign, spctl, trustd, ditto, rsync, git-rebase
---

### Task 1: 玛丽亚本机私用主题设计

task: design-local-lady-maria-theme
task_group: Codex-Dream-Skin theme customization
task_outcome: partial

Preference signals:
- 用户选择“本机私用”方案 A，并明确不接受把受版权保护素材做成仓库内置预设 -> 类似素材默认只进入用户主题库，不进入 Git、preset 或发行包。
- 用户确认视觉浏览器预览后选择 A -> 先用可视对比确认构图和安全区，再实施视觉主题。
- 用户选择“当前会话内联执行：按计划顺序完成” -> 后续偏好同一会话逐步执行。

Reusable knowledge:
- 项目 macOS 引擎位于 `macos/`；安装目标 `~/.codex/codex-dream-skin-studio`；用户状态 `~/Library/Application Support/CodexDreamSkinStudio/`。
- 主题设计参数：2560×1440 JPEG、`appearance: auto`、`safeArea: left`、`taskMode: ambient`、`focusX: 0.72`、`focusY: 0.48`；主色 `#c8a55a`、次色 `#742f31`、高亮 `#bcc7c2`。
- `write-theme.mjs` 自动生成 `custom-<timestamp>` 活动 ID 和 `img-<timestamp>-<pid>` 主题库快照；不要承诺固定 ID。

Failures and how to do differently:
- 主题未完成下载、安装、应用和最终视觉验收；下次应从已通过的运行时预检继续，不要把“设计完成”当作“皮肤已应用”。
- 受限来源只标注私人非商业使用，禁止静默发布或加入 `preset-*`。

References:
- `docs/superpowers/specs/2026-07-18-lady-maria-local-theme-design.md`
- `docs/superpowers/plans/2026-07-18-lady-maria-local-theme.md`
- `https://wall.alphacoders.com/big.php?i=641193`

### Task 2: 签名校验排查

task: diagnose-chatgpt-bundled-node-signature
 task_group: macOS runtime verification
 task_outcome: success

Preference signals:
- 用户要求先查明签名问题，不绕过安全校验；后续应保留签名、Gatekeeper、CDP 进程归属等安全门槛。

Reusable knowledge:
- 受限执行环境曾错误报告签名无效；在正常系统权限环境验证才是可信结果。
- 正常权限结果：`/Applications/ChatGPT.app` 严格签名通过；`Contents/Resources/cua_node/bin/node` 满足 `anchor apple generic and certificate leaf[subject.OU] = "2DC432GLL2"`；`spctl --assess` 返回 `accepted` 且来源为 `Notarized Developer ID`。
- DMG 内原始应用和内置 Node 也通过；DMG SHA/容器完整性通过。

Failures and how to do differently:
- 受限 sandbox 中 `codesign`/`spctl` 可能因无法访问 trustd/系统签名服务产生假阳性。遇到此症状应在正常系统权限下复核，而不是重签应用、关闭 Gatekeeper 或修改项目校验。
- 项目完整测试后来被独立错误阻塞：`Explicit theme directory is missing theme.json`，不要把该错误归因于签名。

References:
- `./tests/run-tests.sh` with escalated permissions
- Error: `The Node.js runtime bundled with ChatGPT failed code-signature validation.`
- Success strings: `valid on disk`, `explicit requirement satisfied`, `accepted`, `source=Notarized Developer ID`

### Task 3: Codex 敏感数据备份

task: backup-codex-state-before-reinstall
 task_group: macOS local data preservation
 task_outcome: success

Preference signals:
- 用户先暂停备份，之后明确授权复制可能包含令牌、会话和聊天记录的数据 -> 敏感数据复制必须先获得明确授权，并说明只保存到本机。

Reusable knowledge:
- macOS 自带 `openrsync 2.6.9` 不支持 `--protect-args`，且 `rsync -aE` 对深层 AppleDouble 路径可能失败；使用 `/usr/bin/ditto` 可保留 macOS 资源、扩展属性和 ACL，并成功复制。
- 已完成正式快照：`/Users/dalwin/Library/ConfigFile/codex/2026-07-20-codex-reinstall-backup`。
- 校验结果：50,718 文件、50,718 SHA-256 校验项全部匹配；正式 sources 约 6.5 GB，总目录约 7.3 GB。`attempts/` 下的失败 rsync 部分副本不是恢复源。

Failures and how to do differently:
- 首次 `rsync` 因 `mkstempsock: Invalid argument`、AppleDouble 文件名过长和权限问题失败；先做工具能力探测，macOS 上优先考虑 `ditto`。

References:
- `.../manifests/SHA256SUMS`
- `.../manifests/files.txt`
- `files=50718 checksums=50718 size=7.3G verification=PASS partial_attempt_retained=yes`

### Task 4: 更新远端 main

task: rebase-local-theme-docs-on-origin-main
 task_group: git repository maintenance
 task_outcome: success

Preference signals:
- 用户要求安装前先同步最新 main -> 先检查 `git status --short --branch`, remote 和本地提交，再决定 fetch/rebase，避免覆盖未跟踪或本地提交。

Reusable knowledge:
- 当本地 `main` ahead 2、behind 4 且本地提交与远端无重叠时，`git fetch origin` 后 `git rebase origin/main` 成功保留本地文档提交并纳入远端更新。
- 受限环境下 Git 可能无法写 `.git/FETCH_HEAD`；需在获批的正常权限环境执行 fetch/rebase。

References:
- `git fetch origin`
- `git rebase origin/main`
- 最终本地提交：`4b70e25`, `65fe270`
- 最终状态：`main...origin/main [ahead 2]`；未跟踪 `.superpowers/` 和计划文件未被删除。

## Thread `019f841d-ef6e-7fa0-bd1b-af3a77c62b79`
updated_at: 2026-07-27T03:59:49+00:00
cwd: /Users/dalwin/Library/IdeaProject/ZhiJin/SunkidCloud/skcservers/skcactivity
rollout_path: /Users/dalwin/.codex/sessions/2026/07/21/rollout-2026-07-21T17-59-42-019f841d-ef6e-7fa0-bd1b-af3a77c62b79.jsonl
rollout_summary_file: 2026-07-21T09-59-42-ZyuB-nanjing_physical_type_isolation_apifox_sync.md

description: 南京体检预约类型隔离、直录响应与 Apifox 契约修复，已测试并推送 develop；关键经验是以预约时段关联配置类型为权威，不能信任前端残留 peType
 task: 修复南京体检预约 peType 串用并同步 Apifox
 task_group: skc-activity physical-examination / Apifox
 task_outcome: success
 cwd: /private/tmp/nanjing-physical-type-fix
 keywords: Nanjing, physical-examination, peType, appointTimeId, PhysicalAppointmentServiceImpl, PhysicalExaminationDao.xml, Apifox, 475638055, Maven, 8d1ee4a5

### Task 1: 生产数据根因定位
task: 根据 SQL 与代码确认体检类型串用原因
task_group: skc-activity physical-examination RCA
task_outcome: success

Preference signals:
- 用户明确说明预约业务时间应看预约表的时间段，而不是 `create_time`；类似排查应优先按 `physical_appoint_time.start_time/end_time` 查询。
- 用户在方案明确后说“确认按这个方案实施本次任务修复”，表明先完成根因定调和方案确认，再编辑代码。

Reusable knowledge:
- `pau_id=55` 通过 `appoint_time_id=204` 关联到 `config_pe_type=2` 从业人员体检；`pau_id=53` 通过 `appoint_time_id=197` 关联到 `config_pe_type=1` 儿童入托体检。两条记录独立存在，异常直接原因是前端选错预约时段，不是姓名匹配或同一记录跨列表。
- `detail_pe_type` 为空、`user_id` 相同只说明未传 peType 和使用同一登录账号。

Failures and how to do differently:
- 初始线程 ID 在本机不可检索；后续以当前代码、提交 `41599c33`、生产 SQL 和 Apifox 现状交叉核对，不能凭截图猜字段。

References:
- SQL 结果关键链路：`appoint_time_id=204 -> appoint_id=13 -> pe_id=2 -> config_pe_type=2`；`appoint_time_id=197 -> appoint_id=12 -> pe_id=1 -> config_pe_type=1`。

### Task 2: 代码修复
task: 修复预约类型校验、类型隔离与直录响应
task_group: skc-activity physical-examination implementation
task_outcome: success

Reusable knowledge:
- 新增 `PeResultDirectSaveVO`，直录保存返回 `{perId, pauId}`。
- 南京预约保存根据 `appointTimeId -> physical_appoint -> physical_examination.type` 获取权威类型；传入 `peType` 时必须一致，否则抛出“预约类型与所选时间段不一致”；成功后以配置类型覆盖落库 `appointDetail.peType`。
- 重复预约查询增加 `pe.type=#{peType}`；MySQL 与 Kingbase 均已更新。
- 列表、统计、婴幼儿管理查询均改为配置类型优先、无预约配置时才使用 JSON `peType` 兜底。
- `resolveChildDirectUserId` 与 `resolveStaffDirectUserId` 分离，分别处理儿童关联用户和从业人员本人用户。
- 修改已有直录记录时禁止跨 `peType` 更新。

References:
- 文件：`skc-activity/src/main/java/com/iktapp/skc/activity/service/physicalexamination/PhysicalAppointmentServiceImpl.java`
- 文件：`skc-activity/src/main/resources/mapper/activity/PhysicalExaminationDao.xml`
- 文件：`skc-activity/src/main/java/com/iktapp/skc/activity/dto/physical/examination/PeResultDirectSaveVO.java`
- 提交：`8d1ee4a5 fix(physical): 修复南京体检类型隔离并补充直录返回`

### Task 3: 测试验证
task: RED/GREEN 回归与完整模块测试
task_group: skc-activity Maven verification
task_outcome: success

Reusable knowledge:
- RED 阶段 4 个契约测试全部失败，覆盖响应对象、预约类型校验、配置优先过滤、用户匹配拆分。
- GREEN 阶段 4 个测试全部通过。
- 完整命令：`mvn -s /Users/dalwin/Library/ConfigFile/maven/saas/settings.xml -Dmaven.repo.local=/Users/dalwin/Library/Repository test`
- 最终结果：`Tests run: 37, Failures: 0, Errors: 0`；`git diff --check` 通过。

Failures and how to do differently:
- Maven 输出存在项目已有的 systemPath/POM 警告，但不影响本次编译和测试成功；后续应区分环境警告与真正失败。

### Task 4: Apifox 同步
task: 更新直录接口请求与响应契约
task_group: Apifox saas activity contract
 task_outcome: success

Reusable knowledge:
- 项目 ID `6776425`，接口 ID `475638055`，路径 `/physicalAppointment/peResult/direct`。
- 更新时保留原接口内容，仅修改 requestBody schema、responses、responseExamples 和描述。
- Apifox 硬约束：`requestBody.type` 使用 `application/json`；示例数据使用字符串化 JSON。回读确认均满足。

References:
- 回读结果：`peType` schema 已存在；响应 `data` 为 object，属性 `perId/pauId`，两者 required；成功示例为字符串化 JSON。

### Task 5: 提交推送
task: 将已验证修复提交并推送 develop
task_group: git delivery
 task_outcome: success

Preference signals:
- 用户明确要求“直接提交推送到develop”；完成验证后类似任务可直接执行提交和非强制推送。

Reusable knowledge:
- 提交前先 `git fetch origin develop` 并检查 `git rev-list --left-right --count HEAD...origin/develop`；本次结果 `0 0`。
- 只提交 5 个生产代码文件，不提交被全局 ignore 的本地契约测试。
- 远端 `develop` 已回读指向 `8d1ee4a5d2ef797ee61e7bdd5b385732f7afc89e`，工作区干净。

References:
- 分支：`codex/fix-南京体检类型隔离/20260727_v1.0.0`
- Worktree：`/private/tmp/nanjing-physical-type-fix`
- 推送命令：`git push origin HEAD:develop`

## Thread `019f97d7-0361-7cb0-81e4-d00b8544a1bc`
updated_at: 2026-07-27T03:50:17+00:00
cwd: /Users/dalwin/Library/IdeaProject/ZhiJin/SunkidCloud/skcservers/skciotdevice
rollout_path: /Users/dalwin/.codex/sessions/2026/07/25/rollout-2026-07-25T13-54-38-019f97d7-0361-7cb0-81e4-d00b8544a1bc.jsonl
rollout_summary_file: 2026-07-25T05-54-38-jtik-quantum_bed_off_bed_vital_alarm_fix.md

---
description: Fixed quantum mattress false heart-rate/breathing alarms during off-bed zero-vital samples; added regression tests and pushed commit
 task: quantum mattress off-bed zero-vital alarm mutual exclusion
 task_group: skciotdevice quantum bed alarm
 task_outcome: success
cwd: /Users/dalwin/Library/IdeaProject/ZhiJin/SunkidCloud/skcservers/skciotdevice
keywords: Java, Maven, quantum, off-bed, zero-vitals, alarm, TDD, git-add-force, git-push
---

### Task 1: Quantum off-bed vital alarm mutual exclusion

task: Prevent heart-rate/breathing alarms for zero-valued off-bed data while preserving leave-bed and nonzero vital alarms
task_group: skciotdevice quantum bed alarm
task_outcome: success

Preference signals:
- when the fix was ready, the user said: "确认包括测试文件一并提交" -> include the regression test files in the same confirmed commit.
- the user approved commit and push -> verify first, then commit and push only the confirmed files.

Reusable knowledge:
- In `QuantumRealtimeRecordProcessorImpl`, when `heartRate == 0 && breathe == 0`, skip vital-sign alarm generation but retain normal state/data processing.
- In `QuantumWarnIngestServiceImpl`, `warnValue == 0` vital warnings must be filtered before relying on possibly stale asynchronous realtime cache state.
- Explicit off-bed status still generates only the leave-bed alarm; nonzero vital warnings still use the existing latest-on-bed check.
- Maven verification requires the dedicated settings/repository: `mvn -s /Users/dalwin/Library/ConfigFile/maven/saas/settings.xml -Dmaven.repo.local=/Users/dalwin/Library/Repository ...`.

Failures and how to do differently:
- The repository ignores `src/test/` via local exclude rules. Add only the intended ignored tests with `git add -f`, not the whole test tree.
- Initial tests were deliberately expected to fail: 5 new assertions reproduced the bug. After the two production guards, targeted tests passed 11/11 and full tests passed 101/101.

References:
- Production files: `src/main/java/com/iktapp/skc/device/service/impl/QuantumRealtimeRecordProcessorImpl.java`, `src/main/java/com/iktapp/skc/device/service/impl/QuantumWarnIngestServiceImpl.java`
- Regression tests: `src/test/java/com/iktapp/skc/device/service/impl/QuantumRealtimeRecordProcessorImplTest.java`, `src/test/java/com/iktapp/skc/device/service/impl/QuantumWarnVitalAlarmMutualExclusionTest.java`
- Commit: `0a7ad0780954bd50ac343c3c2ece4d15f439f175` (`fix(量子床垫): 修复离床生命体征告警误报`)
- Final state: local `HEAD` matched `origin/develop`; worktree clean.

## Thread `019fad83-096c-79b1-a919-d38bc7c8c8be`
updated_at: 2026-07-30T01:26:52+00:00
cwd: /Users/dalwin/Library/IdeaProject/WaveFlow/wavetrans
rollout_path: /Users/dalwin/.codex/sessions/2026/07/29/rollout-2026-07-29T18-54-33-019fad83-096c-79b1-a919-d38bc7c8c8be.jsonl
rollout_summary_file: 2026-07-29T10-54-33-PUGG-jiashan_lab_report_second_round_review.md

---
description: 两轮嘉善检验报告同步代码审查完成；首轮新增功能发现 3 个严重、2 个重要问题，修复提交关闭跨租户 fail-open 但仍有 1 个严重、3 个重要问题
 task: review commit d82aafec against prior 2d0e722 review
 task_group: wavetrans Java/Spring 嘉善检验报告同步
 task_outcome: success
 cwd: /Users/dalwin/Library/IdeaProject/WaveFlow/wavetrans
 keywords: d82aafec, 2d0e722, JiaShanLabReportSyncService, JiaShanLabCandidateMapper, convert_history, pauId, reportKey, Oracle, Kafka, Maven, JDK8
---

### Task 1: 第二轮审查嘉善检验报告同步修复提交

task: review commit d82aafec against original report 2d0e722-review.md
task_group: wavetrans 嘉善检验报告同步
task_outcome: success

Preference signals:
- 用户说“根据最新的代码，继续完成第二轮代码审查”并给出原报告路径 -> 修复审查应把上一轮问题逐条作为验收基线，同时独立检查新风险。
- 用户要求的是代码审查而非确认式总结；rollout采用独立 reviewer、真实下游调用链、文件行号和验证命令 -> 类似任务应保持批判、证据驱动口径。

Reusable knowledge:
- 修复提交 `d82aafec461a6ac35ff25baae4308a3c95038f8e` 的父提交为 `4febbe2f2dfa4872979688442fac4ff5ab4d159c`，变更 3 文件、+197/-28。
- 已关闭：`deptIds` 为空时跨租户 fail-open。Java `parseDeptIds` 对空值、空白、非法 ID 抛异常；MyBatis 候选 SQL 对空列表使用 `AND 1 = 0`。
- 仍存在严重归属问题：`JiaShanLabReportSyncService.java:94-96` 按当前预约日期 ±3 天同时查询报告和候选预约。不同预约会得到不同候选集合，同一报告可能在不同轮次分别归属两个 `pauId`。此外 `filterRowsOwnedByCandidate` 在预约查询为空时回退当前候选单例，错误地把查询失败当成唯一归属。
- 仍存在固定窗口问题：`candidate-days:30` / `buildMinExamDate` 只扫描近 30 天；第 31 天后补出、补项目或更正的报告不会自动同步。
- 删除 `convert_history` 排除后，近 30 天候选每轮都会重复查询 Oracle、查询 MySQL 归属并发送 Kafka。下游按 `pauId + reportKey` 和 `reportId + itemKey` 幂等更新，因此重复消息不新增重复业务行，但仍造成跨库 N+1、Kafka 和消费开销。
- 修复提交没有新增任何测试；旧 `JiaShanLabResultSyncServiceTest` 仅 3/3 通过，无法验证新报告同步链路。
- 标准验证：JDK 8；Maven settings `/Users/dalwin/Library/ConfigFile/maven/saas/settings.xml`；本地仓库 `/Users/dalwin/Library/Repository`。六模块 compile 成功，旧嘉善测试 3/3 成功，`git diff --check` 成功。

Failures and how to do differently:
- 不要把“近 30 天扫描”当作迟到报告完整解决方案；应使用源端更新时间/稳定源键，或增加周期性历史回扫、超窗告警和 backfill。
- 不要按当前预约的局部日期窗口裁决报告归属；应按每条报告日期构造固定候选集合，遇到无法唯一归属时拒绝发送，移除空候选回退逻辑。
- 不要只运行旧测试；必须新增覆盖相邻预约、等距歧义、空候选、迟到报告、第 30/31 天边界、`fullMode/pauId` 和重复消息的测试。

References:
- 报告路径：`docs/commit-review/2026-07/30/d82aafe-review.md`（目录被 `/Users/dalwin/.config/git/ignore-ideaproject` 全局忽略）。
- 关键验证命令：`export JAVA_HOME=/Library/Java/JavaVirtualMachines/jdk-1.8.jdk/Contents/Home && mvn -s /Users/dalwin/Library/ConfigFile/maven/saas/settings.xml -Dmaven.repo.local=/Users/dalwin/Library/Repository -pl wavetrans-job -am -DskipTests compile`
- 定向测试：`mvn -s /Users/dalwin/Library/ConfigFile/maven/saas/settings.xml -Dmaven.repo.local=/Users/dalwin/Library/Repository -pl wavetrans-job -am -Dtest=JiaShanLabResultSyncServiceTest -Dsurefire.failIfNoSpecifiedTests=false test`
- 首轮报告：`docs/commit-review/2026-07/29/2d0e722-review.md`
- 下游契约核对：commit `8b2de706`，按 `pauId + reportKey`、`reportId + itemKey` 幂等更新。

