# Task Group: wavetrans 嘉善检验报告同步两轮代码审查

scope: 适用于 `wavetrans-job` 嘉善检验报告同步的 commit review、报告归属、迟到报告、跨库/Kafka 负载和测试覆盖评估；当前修复提交结论为不可合入。
applies_to: cwd=/Users/dalwin/Library/IdeaProject/WaveFlow/wavetrans; reuse_rule=同一嘉善报告同步链路可复用；commit、下游契约与候选窗口须从当前代码重新核对

## Task 1: 审查新增同步提交 `2d0e722`，成功

### rollout_summary_files

- rollout_summaries/2026-07-29T10-54-33-PUGG-jiashan_lab_report_second_round_review.md (cwd=/Users/dalwin/Library/IdeaProject/WaveFlow/wavetrans, rollout_path=/Users/dalwin/.codex/sessions/2026/07/29/rollout-2026-07-29T18-54-33-019fad83-096c-79b1-a919-d38bc7c8c8be.jsonl, updated_at=2026-07-30T01:26:52+00:00, thread_id=019fad83-096c-79b1-a919-d38bc7c8c8be, success; baseline review)

### keywords

- 2d0e722, 489ae43, JiaShanLabReportSyncService, JiaShanLabCandidateMapper, deptIds, pauId, reportKey, Oracle, Kafka, JiaShanLabResultSyncServiceTest, JDK8

## Task 2: 复审修复提交 `d82aafec`，结论不可合入

### rollout_summary_files

- rollout_summaries/2026-07-29T10-54-33-PUGG-jiashan_lab_report_second_round_review.md (cwd=/Users/dalwin/Library/IdeaProject/WaveFlow/wavetrans, rollout_path=/Users/dalwin/.codex/sessions/2026/07/29/rollout-2026-07-29T18-54-33-019fad83-096c-79b1-a919-d38bc7c8c8be.jsonl, updated_at=2026-07-30T01:26:52+00:00, thread_id=019fad83-096c-79b1-a919-d38bc7c8c8be, success; 1 severe, 3 important remain)

### keywords

- d82aafec, 4febbe2f, convert_history, candidate-days:30, buildMinExamDate, filterRowsOwnedByCandidate, pauId + reportKey, reportId + itemKey, 30/31 天边界, 不可合入

## User preferences

- 当用户要求“对这个 commit 进行一下代码审查”时，使用独立、批判、带风险排序、文件行号和验证证据的审查，不给确认式泛泛总结。 [Task 1]
- 当用户要求“根据最新的代码，继续完成第二轮代码审查”并指定旧报告时，将旧问题逐条作为验收基线，同时独立检查新风险、真实下游调用链和边界场景。 [Task 2]

## Reusable knowledge

- 该仓验证使用 JDK 8、`/Users/dalwin/Library/ConfigFile/maven/saas/settings.xml` 与 `/Users/dalwin/Library/Repository`。六模块 compile、旧 `JiaShanLabResultSyncServiceTest` 3/3 与 `git diff --check` 通过，只能证明旧覆盖范围，不能证明新增同步链路正确。 [Task 1][Task 2]
- `d82aafec` 已将空 `deptIds` 改为 Java fail-fast 和 SQL `AND 1 = 0` fail-closed，关闭跨租户 fail-open；但不同预约按各自预约日 ±3 天查询候选，会让同一报告面对不一致候选集，可能分别归属两个 `pauId`。候选查询为空时回退当前候选单例同样会把查询失败误判为唯一归属。 [Task 2]
- 下游按 `pauId + reportKey` 和 `reportId + itemKey` 幂等，重复消息不会新增业务行，但删除 `convert_history` 排除后仍会重复 Oracle/MySQL 查询、Kafka 投递和消费。固定 `candidate-days:30` 会漏第 31 天后补出或更正的报告。 [Task 2]
- 合入前应为每条报告日期构造稳定统一候选集；无法唯一归属则拒发。补充相邻预约、等距歧义、空候选、迟到报告、30/31 天、`fullMode/pauId`、重复消息及 MyBatis mapper 集成测试；迟到报告用源端更新时间/稳定源键，或周期性历史回扫与超窗告警。 [Task 2]

## Failures and how to do differently

- 症状：Maven 在受限环境不能写本地仓库，或 `git status` 看不到被全局 ignore 的审查报告。处理：在允许写 Maven repo 的上下文执行；直接检查 `docs/commit-review/` 路径，而非以 Git 状态判断。 [Task 1]
- 症状：以“编译通过 + 旧测试 3/3”宣称修复正确。处理：新报告同步没有新增测试，且第二轮仍为 🔴 1、🟡 3；在补齐归属、迟到数据和重复投递覆盖前保持不可合入结论。 [Task 2]

# Task Group: SunKidServer 高德公网直连与信创活动二维码 Nacos 路由

scope: 适用于 `/Users/dalwin/Library/IdeaProject/ZhiJin/SunKidServer` 多仓中的共享 `skframework` 高德查询改造，以及信创活动二维码的生产者、Nacos Data ID 与 URL 路由核对。
applies_to: cwd=/Users/dalwin/Library/IdeaProject/ZhiJin/SunKidServer; reuse_rule=共享 basic 的调用链可复用；具体依赖版本、Nacos Data ID、外网 H5 根路径和运行时配置必须现场复核

## Task 1: 将高德经纬度查询从 Redis 改为公网直连，部分完成

### rollout_summary_files

- rollout_summaries/2026-06-06T03-48-50-Ay8f-sunkidserver_gaode_migration_and_xinchuang_qrcode_routing.md (cwd=/Users/dalwin/Library/IdeaProject/ZhiJin/SunKidServer, rollout_path=/Users/dalwin/.codex/sessions/2026/06/06/rollout-2026-06-06T11-48-50-019e9b0c-3968-7bd2-baf0-5114a5379f17.jsonl, updated_at=2026-07-28T06:30:54+00:00, thread_id=019e9b0c-3968-7bd2-baf0-5114a5379f17, implementation verified; street-server compile blocked by pre-existing dependency)

### keywords

- sunkids-basic, GaoDeServiceImpl, GaoDeCoordinateClient, GaoDeMapUtil, getLatLng, Redis, getLatLng + address, ParamErrorException, DatabaseType

## Task 2: 定位信创活动二维码的 Nacos 路由配置，成功

### rollout_summary_files

- rollout_summaries/2026-06-06T03-48-50-Ay8f-sunkidserver_gaode_migration_and_xinchuang_qrcode_routing.md (cwd=/Users/dalwin/Library/IdeaProject/ZhiJin/SunKidServer, rollout_path=/Users/dalwin/.codex/sessions/2026/06/06/rollout-2026-06-06T11-48-50-019e9b0c-3968-7bd2-baf0-5114a5379f17.jsonl, updated_at=2026-07-28T06:30:54+00:00, thread_id=019e9b0c-3968-7bd2-baf0-5114a5379f17, success; producer/Data ID traced)

### keywords

- qrcode_register_url, qrcode_register_param, h5_url, sknurseryserver-prod, skh5server-prod, CourseOfflineController, QrCodeUtil, MinIO, courseId=1498

## User preferences

- 当用户要求“与 pubserver 服务中根据关键字通过高德地图 api 获取经纬度的业务实现一致的方式，直接调公网请求”时，优先复用已存在的对照实现，保持接口路径、返回字段和业务异常兼容。 [Task 1]
- 当用户已确认信创 Nacos 数据库正确、转而要求回归 `qrcode_register_url` 时，区分数据库正确性与 URL/路由配置，沿 `@Value` 消费者追到实际生产服务和 Data ID，不重复数据库诊断。 [Task 2]

## Reusable knowledge

- `/gaode/getLatLng` 的 `skdistdrserver` 与 `skstreetdrserver` 均委托 `skframework/sunkids-basic` 的 `GaoDeService`，改 shared basic 可覆盖两端。复用 common 的 `GaoDeMapUtil.getLngAndLat`，无需复制 pubserver 私有类；移除 Redis publish/sleep/readback 后，空结果或缺少 coordinate 仍保留 `ParamErrorException("单位地址不正确或不够详细，无法获取经纬度")`。 [Task 1]
- `skframework` 是独立 Git 仓库，顶层 `SunKidServer` 不是；改动 `sunkids-basic` 后先执行 `mvn -q -pl sunkids-basic -DskipTests install`，再编译独立调用端。 [Task 1]
- 机构活动二维码在 `sknurseryserver/.../CourseOfflineController` 由 `qrcode_register_url + qrcode_register_param + courseId` 生成。截图中的 `skh5server-prod` 不是其控制源；先修正生产者的 `sknurseryserver-prod`。 [Task 2]
- 有效形态为 `h5_url=<外网可达信创 H5 根路径>`、`qrcode_register_url=${h5_url}activityDetail`、`qrcode_register_param=?courseId=`；解码课程 1498 的二维码应为 `<root>/#/activityDetail?courseId=1498`。同时核验生产者的 `minio.endpoint`、`minio.port`、`minio.bucketName`；`uploadfpath.QRcode` 仅是 `QrCodeUtil` 本地输出路径，不决定公开路由。改 Nacos 后按需重载生产者并重新生成二维码/海报，旧图不会自动改写。 [Task 2]

## Failures and how to do differently

- 症状：`skstreetdrserver` 编译报 `找不到符号: 类 DatabaseType`。处理：错误位于 `DataBaseConfiguration.java` 且为既有 common 依赖缺失，不要归因于高德改造；新增 `**/*Test.java` 与 `**/spec-architect/` 又会被全局 ignore，交付/提交前明确处理。 [Task 1]
- 症状：根据截图只改 `skh5server-prod` 后二维码仍指向旧路径。处理：先追踪 `@Value` 消费者；机构活动二维码的相关生产者是 `sknurseryserver`，配置在 `sknurseryserver-prod`。 [Task 2]

# Task Group: skcactivity 南京体检预约 `peType` 隔离、直录响应与 Apifox 契约修复

scope: 适用于旧 `physicalexamination` 南京预约的类型权威来源、儿童/从业人员隔离、直录返回、MySQL/Kingbase 查询和 Apifox 契约同步；不要套用到新 `physicalexam` 模块。
applies_to: cwd=/Users/dalwin/Library/IdeaProject/ZhiJin/SunkidCloud/skcservers/skcactivity（验证 worktree=/private/tmp/nanjing-physical-type-fix）; reuse_rule=同南京旧预约链路可复用；预约配置、接口或地区规则改变时，先以 `appointTimeId` 关联配置和当前代码复核

## Task 1: 定位并修复南京体检预约 `peType` 串用，同步直录接口 Apifox，成功

### rollout_summary_files

- rollout_summaries/2026-07-21T09-59-42-ZyuB-nanjing_physical_type_isolation_apifox_sync.md (cwd=/Users/dalwin/Library/IdeaProject/ZhiJin/SunkidCloud/skcservers/skcactivity, rollout_path=/Users/dalwin/.codex/sessions/2026/07/21/rollout-2026-07-21T17-59-42-019f841d-ef6e-7fa0-bd1b-af3a77c62b79.jsonl, updated_at=2026-07-27T03:59:49+00:00, thread_id=019f841d-ef6e-7fa0-bd1b-af3a77c62b79, success; git_branch=develop)

### keywords

- Nanjing, physical-examination, peType, appointTimeId, PhysicalAppointmentServiceImpl, PhysicalExaminationDao.xml, PeResultDirectSaveVO, /physicalAppointment/peResult/direct, Apifox, 6776425, 475638055, 8d1ee4a5

## User preferences

- 当用户指出“预约时间不等于创建时间”时，按 `physical_appoint_time.start_time/end_time` 判断业务发生时间，不能用 `create_time` 代替。 [Task 1]
- 当用户确认“按这个修订方案实施本次任务修复”时，先完成 RCA、给出可验证方案并等待确认，再进入编码。 [Task 1]
- 当用户要求“直接提交推送到develop”时，完成测试、`git diff --check` 和远端基线核对后，直接 commit + 非强制 push。 [Task 1]

## Reusable knowledge

- 预约时段关联的配置类型才是权威：`appointTimeId -> physical_appoint -> physical_examination.type`。传入 `peType` 时必须与之相同，否则报“预约类型与所选时间段不一致”；保存后用配置类型覆盖 `appointDetail.peType`，缺失参数仍兼容旧前端。 [Task 1]
- `pau_id=55 -> appoint_time_id=204 -> pe_id=2 -> config_pe_type=2` 与 `pau_id=53 -> appoint_time_id=197 -> pe_id=1 -> config_pe_type=1` 是独立记录；直接根因是前端选错预约时段，不是姓名匹配或同一记录跨列表。 [Task 1]
- 重复预约查询增加 `pe.type=#{peType}`；MySQL/Kingbase 的列表、统计和婴幼儿管理查询均配置类型优先，无预约配置的直录才回退 JSON `peType`。儿童和从业人员直录用户匹配拆为独立方法，既有直录记录不得跨类型更新。 [Task 1]
- `/physicalAppointment/peResult/direct` 返回 `PeResultDirectSaveVO { perId, pauId }`。Apifox `saas` 项目为 `6776425`，接口 `475638055`；只更新 requestBody schema、responses、responseExamples 和描述，`requestBody.type=application/json`、示例字符串化 JSON，写后用 `getHttpEndpoint` 回读。 [Task 1]
- 本次 RED 4 项契约测试均失败、GREEN 均通过；完整 Maven 测试为 37 tests、0 failures/errors，提交 `8d1ee4a5` 已推送 develop。 [Task 1]

## Failures and how to do differently

- 症状：初始线程无法检索或只有截图。处理：以当前代码、生产只读 SQL、已知提交和 Apifox 当前契约交叉核对，不能凭截图猜字段。 [Task 1]
- 症状：Maven 出现已有 systemPath/POM 警告。处理：区分环境警告与真实编译/测试失败；本次完整测试和 `git diff --check` 均通过。 [Task 1]

# Task Group: skciotdevice 量子床垫离床零生命体征告警互斥

scope: 适用于 `/Users/dalwin/Library/IdeaProject/ZhiJin/SunkidCloud/skcservers/skciotdevice` 的量子床垫实时帧、第三方预警回调、离床/零生命体征告警边界和回归测试交付。
applies_to: cwd=/Users/dalwin/Library/IdeaProject/ZhiJin/SunkidCloud/skcservers/skciotdevice; reuse_rule=同量子床垫告警链路可直接复用；新厂商 MQTT 协议勘察尚未交付，不能由本块推断已实现

## Task 1: 修复离床时零生命体征误报并提交推送，成功

### rollout_summary_files

- rollout_summaries/2026-07-25T05-54-38-jtik-quantum_bed_off_bed_vital_alarm_fix.md (cwd=/Users/dalwin/Library/IdeaProject/ZhiJin/SunkidCloud/skcservers/skciotdevice, rollout_path=/Users/dalwin/.codex/sessions/2026/07/25/rollout-2026-07-25T13-54-38-019f97d7-0361-7cb0-81e4-d00b8544a1bc.jsonl, updated_at=2026-07-27T03:50:17+00:00, thread_id=019f97d7-0361-7cb0-81e4-d00b8544a1bc, success; git_branch=develop)

### keywords

- quantum, off-bed, zero-vitals, QuantumRealtimeRecordProcessorImpl, QuantumWarnIngestServiceImpl, warnValue=0, QuantumWarnVitalAlarmMutualExclusionTest, Maven, git add -f, 0a7ad078

## User preferences

- 当用户确认“包括测试文件一并提交”时，将回归测试与生产修复一同提交；若测试受本地 ignore 影响，只强制加入已确认的测试文件。 [Task 1]
- 用户确认提交并推送时，先完成验证并明确暂存范围，再只提交已确认文件。 [Task 1]

## Reusable knowledge

- `heartRate == 0 && breathe == 0` 时，`QuantumRealtimeRecordProcessorImpl` 跳过生命体征告警但保留正常状态/数据处理；明确离床仍只生成离床告警，非零生命体征维持既有最新在床状态校验。 [Task 1]
- `/third/quantum/warn` 可先于异步实时缓存更新；`QuantumWarnIngestServiceImpl` 必须先过滤 `warnValue == 0` 的生命体征预警，不能依赖可能陈旧的 realtime cache。 [Task 1]
- Maven 使用专用 settings/repository。定向回归 11/11、全量测试 101/101、`git diff --check` 均通过；`0a7ad078 fix(量子床垫): 修复离床生命体征告警误报` 已推送 develop，HEAD 与 origin/develop 一致。 [Task 1]

## Failures and how to do differently

- 症状：新增测试受 `.gitignore/.git/info/exclude` 的 `src/test/` 规则拦截。处理：用 `git add -f` 精确加入 `QuantumRealtimeRecordProcessorImplTest.java` 与 `QuantumWarnVitalAlarmMutualExclusionTest.java`，不要强制加入整个测试树。 [Task 1]
- 症状：TDD 的初始 5 项断言失败被误判为实现故障。处理：它们是稳定复现 bug 的 RED 证据；加两处生产 guard 后重新验证 11/11 和 101/101。 [Task 1]

# Task Group: skc-datasum 南京建邺动态指标事务隔离与定时任务异常隔离

scope: 适用于 `/Users/dalwin/Library/IdeaProject/ZhiJin/SunkidCloud/skcservers/skcdatasum` 中南京建邺驾驶舱动态指标、`DataSchedule` 定时汇总、按指标失败隔离与验证后直推；不要把建邺指标口径直接外推给其他区域。
applies_to: cwd=/Users/dalwin/Library/IdeaProject/ZhiJin/SunkidCloud/skcservers/skcdatasum; reuse_rule=同仓 `NanjingJianyeDashboardDynamicServiceImpl` / 南京日汇总链路可直接复用；更换区域、指标集或事务框架时先复核

## Task 1: 建邺动态指标按 key 独立事务并推送，成功

### rollout_summary_files

- rollout_summaries/2026-05-22T03-48-12-d3yp-jianye_dynamic_key_independent_transactions.md (cwd=/Users/dalwin/Library/IdeaProject/ZhiJin/SunkidCloud/skcservers/skcdatasum, rollout_path=/Users/dalwin/.codex/sessions/2026/05/22/rollout-2026-05-22T11-48-12-019e4dcc-42a4-7cc3-9ee4-7c464ccf4969.jsonl, updated_at=2026-07-20T13:13:44+00:00, thread_id=019e4dcc-42a4-7cc3-9ee4-7c464ccf4969, success)

### keywords

- NanjingJianyeDashboardDynamicServiceImpl, DataSchedule, refreshMetric, TransactionTemplate, PROPAGATION_REQUIRES_NEW, biz_*, query timeout, nurseryList-320105, kindergartenList-320105, stateCorp, f642d84e

## User preferences

- 当用户要求“每个指标key的动态统计是独立事物，一个事物失败不要影响其他统计指标的事物统计和提交更新”时，按 key 建立事务边界、保留失败隔离日志，不要保留整批事务。 [Task 1]
- 当用户要求“直接提交推送”时，完成相关测试、编译和 diff 检查后直接 commit + push，不额外停在待确认状态。 [Task 1]

## Reusable knowledge

- `refreshDynamicData` 按 10 个 key 调 `refreshMetric`；每个 key 的查询、计算、序列化和落库通过 `TransactionTemplate` + `PROPAGATION_REQUIRES_NEW` 独立执行，异常捕获后继续下一个 key。 [Task 1]
- 成功日志为 `南京建邺动态指标刷新完成，key=...，areaCode=...`；失败日志为 `南京建邺动态指标刷新失败，已回滚当前指标并继续后续任务，key=...，areaCode=...`。 [Task 1]
- `DataSchedule.updateNanjingDailyDynamicData()` 用 `executeNanjingDynamicTask(String, Runnable)` 将照护机构、中央审核、首页总览、街道托位分布、建邺驾驶舱分开；前置模块失败不能阻断 `refreshDynamicData("320105")`。 [Task 1]
- 回归可模拟 `selectChildHealthOverview` 抛出 `query timeout`，验收为 10 个独立事务、1 次回滚、9 次提交；已通过服务测试、writer 合同测试、`mvn -q -DskipTests compile` 与 `git diff --check`。提交为 `f642d84e fix(nanjing): 隔离建邺动态指标统计事务`。 [Task 1]
- 建邺指标排查中，`nurseryList-320105` 的正确社会办托口径示例为 `stateCorp=9`，幼儿园列表为 `stateCorp=0`；生产 `update_by=建邺区` 而当前 writer 固定 `数据中心自动同步` 时，不能把旧生产记录归因于当前 writer。 [Task 1]

## Failures and how to do differently

- 症状：入口外层 `@Transactional(rollbackFor = Exception.class)` 包住所有 `biz_*` 查询和写入，一项 `query timeout` 后后续 key 中断、已写入数据整体回滚。处理：不要恢复整批事务；将事务缩小到单 key，并在边界外捕获异常继续执行。 [Task 1]
- 症状：调度端 Feign 调用不检查失败返回，fallback 可能让平台显示成功但数据未更新。处理：区分调度显示与 writer 实际执行，沿调用结果和更新人字段核验。 [Task 1]

# Task Group: skc-nursery 善于在杭托育券婴幼儿“无权查询/出生日期为空”排查

scope: 适用于 `skc-nursery` 善于在杭托育券的儿童信息授权提示、家庭关系缓存、前端 `infantIdCard` 传参和指定排查报告更新。
applies_to: cwd=/Users/dalwin/Library/IdeaProject/ZhiJin/SunkidCloud/skcservers/skcnursery/skc-nursery; reuse_rule=同一托育券东软链路可复用；人员、关系、缓存和报告路径均为现场证据，生产只读核验时不得外推

## Task 1: 定位杨帆、杨婷“无权查询/出生日期为空”根因并更新报告，成功

### rollout_summary_files

- rollout_summaries/2026-06-10T11-25-33-eWUb-skc_nursery_tu.md (cwd=/Users/dalwin/Library/IdeaProject/ZhiJin/SunkidCloud/skcservers/skcnursery/skc-nursery, rollout_path=/Users/dalwin/.codex/sessions/2026/06/10/rollout-2026-06-10T19-25-33-019eb147-cc27-75f2-8a8f-429830a72983.jsonl, updated_at=2026-07-31T06:22:53+00:00, thread_id=019eb147-cc27-75f2-8a8f-429830a72983, success; git_branch=release/syzh-20260416)

### keywords

- 善于在杭, skcity, dbq, getInfantOwnInfo, getInfantInfo, infantIdCard, guardianIdCard, validateMobileInfantCaller, dr-family-cache, family-relationship-cache, zheliban_user, user_child, 空家庭关系缓存

## User preferences

- 当用户要求“把这两位的错误问题原因也加入到…排查报告.md”，并要求杨婷“列出前端调用的哪个接口传入了错误的参数” -> 同步更新指定报告，写清接口、参数名、错误语义和正确值来源，不只给口头结论。 [Task 1]
- 报告应按独立案例保留日志证据、数据库证据、直接原因、根因分类、正确调用方式和前端修正要求。 [Task 1]

## Reusable knowledge

- `GET /app/nursery/coupon/getInfantOwnInfo` 的 `infantIdCard` 语义是婴幼儿证件号；不能传 `guardianIdCard` 或登录用户证件号。`getInfantOwnInfoDetail()` 先调 `validateMobileInfantCaller()`，所以“当前用户无权查询该证件号信息”可能是空关系缓存，也可能是儿童证件号错传，不能直接判作真实越权。 [Task 1]
- 空数组家庭关系缓存也会被当成命中而不再请求东软。遇到 `stage=dr-family-cache cacheHit=true, result=[]`，先以 `dbq '善于在杭正式查询'` 在 `skcity` 核验有效 `user_child` 关系；关系存在则清家庭关系/儿童列表缓存后重试，并确认有 `dr-family-request`、`dr-family-raw-response`、`dr-family-parsed-result`。 [Task 1]
- 前端修正应核对表单绑定、初始化、编辑回显和切换儿童：不得用 `guardianIdCard` 覆盖 `infantIdCard`，以不同儿童证件号回归 `infantBirthday`。最终报告路径为 `/Users/dalwin/Downloads/善于在杭托育券-婴幼儿出生日期为空问题排查报告.md`。 [Task 1]

## Failures and how to do differently

- 症状：生产 SQL 报 `ERROR: UNION types boolean and text cannot be matched`。处理：改用独立 `SELECT`/`EXISTS` 核验，不强拼异构列。 [Task 1]
- 症状：PostgreSQL 脱敏 SQL 输出 `t` 等异常值。处理：先核查字段类型和长度，再使用首尾字符脱敏/布尔等值判断，不能把异常脱敏输出当业务数据。 [Task 1]

# Task Group: skc-system Liquibase MySQL/Kingbase 双数据库建表与 develop 交付

scope: 适用于 `skc-modules/skc-system` 的 MySQL/Kingbase 建表 changeSet、模块测试/打包、rebase 与严格暂存后推送 `develop`。
applies_to: cwd=/Users/dalwin/Library/IdeaProject/ZhiJin/SunkidCloud/skcservers/skcadminframework; reuse_rule=仅在同仓、同 `skc-system` monthly changelog 结构下直接复用；启动、网络和远端状态须执行前重查

## Task 1: 创建 `nursery_class_daily_activity` 双数据库迁移，成功

### rollout_summary_files

- rollout_summaries/2026-06-13T08-24-23-7zgp-skc_system_liquibase_dual_db_delivery.md (cwd=/Users/dalwin/Library/IdeaProject/ZhiJin/SunkidCloud/skcservers/skcadminframework, rollout_path=/Users/dalwin/.codex/sessions/2026/06/13/rollout-2026-06-13T16-24-23-019ec015-039a-7fd0-8d4e-8d95235648cd.jsonl, updated_at=2026-07-30T10:39:54+00:00, thread_id=019ec015-039a-7fd0-8d4e-8d95235648cd, success)

### keywords

- skc-system, liquibase, nursery_class_daily_activity, MySQL, Kingbase, changelog-202606.xml, 20260613-01, 20260613-02, wangzhiheng, master.xml, serial

## Task 2: 创建嘉善 `physical_lab_report` / `physical_lab_report_item` 双数据库迁移并推送，成功

### rollout_summary_files

- rollout_summaries/2026-06-13T08-24-23-7zgp-skc_system_liquibase_dual_db_delivery.md (cwd=/Users/dalwin/Library/IdeaProject/ZhiJin/SunkidCloud/skcservers/skcadminframework, rollout_path=/Users/dalwin/.codex/sessions/2026/06/13/rollout-2026-06-13T16-24-23-019ec015-039a-7fd0-8d4e-8d95235648cd.jsonl, updated_at=2026-07-30T10:39:54+00:00, thread_id=019ec015-039a-7fd0-8d4e-8d95235648cd, success; commit 2e7d9025 pushed to develop)

### keywords

- physical_lab_report, physical_lab_report_item, changelog-202607.xml, 20260730-01, 20260730-04, uk_physical_lab_report_pau_id_unique_report_key, git diff --check, 2e7d9025, origin/develop

## User preferences

- 当用户提供完整 DDL、要求 MySQL/Kingbase 版本并指定 author `wangzhiheng` 时，保留 DDL 业务语义和 author 原值。 [Task 1]
- 当用户要求编译/测试、提交、rebase 和 push 到 `develop` 时，验证后主动完成交付；若指定“保留既有 API 修改”，只暂存请求范围内的 Liquibase 文件。 [Task 1][Task 2]

## Reusable knowledge

- 实际 Liquibase 根目录是 `skc-modules/skc-system/src/main/resources/liquibase`，先定位模块的 `master.xml`，不要从 repo root 假设路径。建表使用 `_mysql.sql` 与 `_kingbase.sql` 分文件、每文件一个 changeSet；Kingbase 用 `serial`、命名主键约束，索引置于 `CREATE TABLE` 外。 [Task 1][Task 2]
- `master.xml` 递归包含 `liquibase/changelog/`；月份文件如 `changelog/2026/06/changelog-202606.xml` 是正确落点。嘉善两张表的 IDs 为 `20260730-01` 至 `20260730-04`，索引名须含表名片段并检查 63 字符限制；未确认的数据/索引操作不应把附件的既有表 backfill 一并迁入。 [Task 2]
- `mvn -q -pl skc-modules/skc-system -am test` 与 `mvn -q -pl skc-modules/skc-system -am -DskipTests package` 已通过。提交时只 `git add` 指定 SQL 与 changelog；`2e7d9025 feat(system): 嘉善体检数据同步需求v1.3.2需求表结构ddl` 已推送，`develop` 与 `origin/develop` 一致，三项无关 API 修改保持未提交。 [Task 2]

## Failures and how to do differently

- 症状：直接从仓库根目录找 Liquibase 路径失败。处理：先找 `skc-system` 模块的 `master.xml`。 [Task 1]
- 症状：启动 smoke test 报 `dynamic-datasource can not find primary datasource`，补参后 Kingbase 网络拒绝。处理：这是配置/网络边界；Maven test/package 通过不等于启动已验证，也不要归因于 Liquibase。 [Task 1]
- 症状：全局 `git diff --check` 命中无关 API 文件的既有 trailing whitespace。处理：对请求范围执行 path-scoped 检查，不修改或混入无关工作。 [Task 2]

# Task Group: AiPalace 上游同步、仓库日志与 heartbeat 验证

scope: 适用于 `/Users/dalwin/Library/CodeRepo/AI` 内 `AiPalace` 的多上游硬拷贝同步、定时执行、仓库内日志落点、heartbeat 配置回读、以及 heartbeat 触发后的结果回报；不要直接外推到其他自动化系统。
applies_to: cwd=/Users/dalwin/Library/CodeRepo/AI; reuse_rule=在同一 AiPalace 仓库、同一 upstream sync 脚本链路下可直接复用，若同步脚本、heartbeat 配置或仓库结构变化需重查

## Task 1: 把“多个开源仓库 -> AiPalace source-clear skill 硬拷贝同步”落成可重复的定时同步任务，成功

### rollout_summary_files

- rollout_summaries/2026-06-16T03-48-40-h0KN-aipalace_scheduled_upstream_sync_with_local_skill_exclusion.md (cwd=/Users/dalwin/Library/CodeRepo/AI, rollout_path=/Users/dalwin/.codex/sessions/2026/06/16/rollout-2026-06-16T11-48-40-019ece8b-abb3-7af1-83fc-70dba6b3819d.jsonl, updated_at=2026-07-24T08:54:31+00:00, thread_id=019ece8b-abb3-7af1-83fc-70dba6b3819d, success)

### keywords

- AiPalace, upstream_sync.py, schedule-sync-github2palace, automation_update, heartbeat, hard-copy sync, source-clear, registry.yaml, origin/HEAD, langchain master, codex定时任务

## Task 2: 删除 launchd 包装并把同步日志改到仓库内 `AiPalace/logs/`，成功

### rollout_summary_files

- rollout_summaries/2026-06-16T03-48-40-h0KN-aipalace_scheduled_upstream_sync_with_local_skill_exclusion.md (cwd=/Users/dalwin/Library/CodeRepo/AI, rollout_path=/Users/dalwin/.codex/sessions/2026/06/16/rollout-2026-06-16T11-48-40-019ece8b-abb3-7af1-83fc-70dba6b3819d.jsonl, updated_at=2026-07-24T08:54:31+00:00, thread_id=019ece8b-abb3-7af1-83fc-70dba6b3819d, success)

### keywords

- launchctl, LaunchAgents, logs/, aipalace-upstream-sync.log, aipalace-upstream-sync.err.log, .gitignore, 8dd4344, heartbeat

## Task 3: heartbeat 反复触发 `upstream_sync.py --commit` 并固化 `skill-management` 本地例外排除规则，成功

### rollout_summary_files

- rollout_summaries/2026-06-16T03-48-40-h0KN-aipalace_scheduled_upstream_sync_with_local_skill_exclusion.md (cwd=/Users/dalwin/Library/CodeRepo/AI, rollout_path=/Users/dalwin/.codex/sessions/2026/06/16/rollout-2026-06-16T11-48-40-019ece8b-abb3-7af1-83fc-70dba6b3819d.jsonl, updated_at=2026-07-24T08:54:31+00:00, thread_id=019ece8b-abb3-7af1-83fc-70dba6b3819d, success)

### keywords

- heartbeat, upstream_sync.py --commit, git fetch origin, exit status 128, browser-gen, grill-me, grill-with-docs, skill-management, EXCLUDED_TARGETS, local override, automation.toml, b3d5421

## User preferences

- 当用户说 `"这是一个定时任务"`、`"我需要你每天12:30定时帮我完成以下事情"` 时，未来类似需求默认按“可重复执行的自动化”处理，而不是只给一次性建议。 [Task 1]
- 当用户要求任务结果回报里 `"本次自动处理了哪些文件，策略是什么"` 时，这类同步任务默认输出“处理文件 + 依据什么策略 + 哪些保留不动”，不要只说“已执行”。 [Task 1][Task 3]
- 当用户要求 `"任务2完成后执行git提交，message需要附带(codex定时任务)"`，并限定 `"如果 pull 后有文件更新，则同步更新 AiPalace 中存在的，来源于上述仓库中的 skill 硬拷贝"` 时，默认只同步 source-clear / 来源明确的 skill 硬拷贝，且自动提交保留这个后缀。 [Task 1][Task 3]
- 当用户明确说 `"awesome-skills的.../AiPalace/skills/community/garveyhu/method/skill-management除外，这个skill我的AiPalace内已经迭代了自己的版本"` 时，把这个路径视为长期本地例外，不要再被 awesome-skills 覆盖。 [Task 3]
- 当用户说 `"把文件都提交一下，然后我会手动执行一遍这个任务测试一下看看效果"`，说明这类自动化改动交付后默认先整理到可试跑状态，再让用户做最终人工验证。 [Task 2]
- 当用户要求 `"删掉：当前用的 macOS launchd...然后调整一下定时任务的脚本，定时任务日志从/private/tmp/*直接改为落写本仓库的logs/目录下，如果不存在则手动创建"` 时，未来同类长期任务默认优先仓库内可审计日志，不保留系统级临时日志方案。 [Task 2]

## Reusable knowledge

- `AiPalace/tools/upstream_sync.py` 是这条自动同步链路的单一执行入口；它会拉上游、只同步 source-clear / 可明确映射的 skill 硬拷贝、保留本地独有文件，并在 `--commit` 时自动提交。 [Task 1][Task 3]
- 脚本的人类可读输出已经稳定成四段：`上游同步结果`、`硬拷贝同步结果`、`保留不动`、`策略`；后续结果回报可直接复用这个结构。 [Task 1][Task 3]
- `langchain` 的远端默认分支不是 `main` 而是 `master`；脚本已按 `origin/HEAD` 回退处理，这个分支特例要保留在结果说明里。 [Task 1][Task 3]
- 仓库日志路径现在是 `AiPalace/logs/aipalace-upstream-sync.log` 与 `AiPalace/logs/aipalace-upstream-sync.err.log`；脚本会自动创建 `logs/`，`AiPalace/.gitignore` 已忽略该目录。 [Task 2]
- 旧的 `AiPalace/tools/com.dalwin.aipalace-upstream-sync.plist` 与系统侧 `~/Library/LaunchAgents/com.dalwin.aipalace-upstream-sync.plist` 已移除，后续不要再假设 launchd 仍在承载这条任务。 [Task 2]
- heartbeat 配置文件落在 `~/.codex/automations/schedule-sync-github2palace/automation.toml`；已读回为 `kind = "heartbeat"`、`status = "PAUSED"`，并记录 `RRULE:FREQ=WEEKLY;BYHOUR=12;BYMINUTE=30;BYDAY=WE`，说明这条链路曾按周三 12:30 cadence 挂起保存。 [Task 3]
- 本地例外名单已经编码进脚本：`EXCLUDED_TARGETS` 包含 `skills/community/garveyhu/method/skill-management`，用于保护 AiPalace 内已演化的版本不被 awesome-skills 覆盖。 [Task 3]
- heartbeat 后的增量执行已验证脚本会按真实变更回报 mixed outcomes：有的上游 repo 更新、有的未更新、有的本地 skill 目录同步、有的只列 `kept:` 保留本地独有文件，还有被例外名单显式跳过的路径。 [Task 3]
- 已验证的自动提交示例包括 `8dd4344`、`a0c672d`、`84e3a93`、`b3d5421`；已验证的同步差异示例包括 `browser-gen`、`grill-me`、`grill-with-docs`、`skill-management`。 [Task 2][Task 3]
- Related skill: skills/aipalace-upstream-sync/SKILL.md [Task 1][Task 3]

## Failures and how to do differently

- 症状：`automation_update` 连续报参数校验错误。处理：别在接口层反复空转，尽早切换到本机已保存的 heartbeat 配置和脚本入口。 [Task 1][Task 3]
- 症状：一开始把日志落到 `/private/tmp`。处理：类似长期任务默认优先“可追溯、可复盘”的仓库日志目录，并让脚本自动建目录。 [Task 1][Task 2]
- 症状：直接跑 `python3 AiPalace/tools/upstream_sync.py --commit` 时 `git fetch origin` 报 `CalledProcessError ... exit status 128`。处理：这类需要拉上游的任务要预留受限环境下的重试路径，不要误判成脚本逻辑错误。 [Task 3]
- 症状：把同步边界误解成“整仓复制”或“所有 skill 都覆盖”。处理：继续以“只同步能明确映射到 AiPalace 的 skill 硬拷贝、其余保留不动”为边界，并把保留项与例外名单写进结果回报。 [Task 1][Task 3]
- 症状：本地已演化 skill 被上游更新覆盖。处理：把这类路径写入脚本例外名单，并在结果里显式说明是 intentional skip。 [Task 3]
- 症状：预设“每次同步都会有大范围变化”。处理：以后只按脚本当天实际检测到的文件变化、保留项、例外项和提交号来汇报，不预写空泛总结。 [Task 3]

# Task Group: skc-nursery 鄂尔多斯总托位数为0生产核验与 Kingbase 修复 SQL

scope: 适用于 `/Users/dalwin/.codex/worktrees/6308/skcnursery/skc-nursery` 内 nursery 画像总托位数异常、`NurseryClassDisplaySupport` / `refreshNurseryClassSummary` 链路勘查、以及生产只读核验后生成人工执行的 Kingbase 修复 SQL；不要直接外推到其他区域或其他汇总链路。
applies_to: cwd=/Users/dalwin/.codex/worktrees/6308/skcnursery/skc-nursery; reuse_rule=仅在同仓库 nursery capacity 汇总链路、且允许只读查库时可直接复用；涉及其他区域实例或表结构差异时先核对线上真实列

## Task 1: 鄂尔多斯 nursery 总托位数为0 的生产核验与修复 SQL 生成，部分完成

### rollout_summary_files

- rollout_summaries/2026-04-22T08-30-55-fz3A-eeds_nursery_class_capacity_repair_sql.md (cwd=/Users/dalwin/.codex/worktrees/6308/skcnursery/skc-nursery, rollout_path=/Users/dalwin/.codex/sessions/2026/04/22/rollout-2026-04-22T16-30-55-019db450-50c4-7b03-86dd-98747e2aabe2.jsonl, updated_at=2026-07-03T09:06:40+00:00, thread_id=019db450-50c4-7b03-86dd-98747e2aabe2, partial)

### keywords

- skc-nursery, Kingbase, dbq, 鄂尔多斯-正式, NurseryClassDisplaySupport, computeOrderedTypes, refreshNurseryClassSummary, nursery.scope=0, nursery_class_limit, nursery_class_scope_limit, nursery_audit_info, work_flow_service_info, 111824, read-only SQL, mismatch scan

## User preferences

- 当用户要 `"SQL DBA route"` / repair-oriented answer 时，默认交付“代码 review + 线上只读核验 + 可直接执行的修复 SQL”，不要只停在口头诊断。 [Task 1]
- 当环境是只读时，默认把 workflow 收敛为“读库核验 + 人工执行 SQL handoff”，不要尝试直接改库。 [Task 1]

## Reusable knowledge

- `NurseryClassDisplaySupport.buildFormalClassLimitSnapshot()` 同时驱动机构画像展示和主表摘要；snapshot 顺序陈旧不仅会让前台显示错，还会把错误派生值持久化进 `nursery.scope`。 [Task 1]
- `0a6ac6a32` 是预防层修复：`computeOrderedTypes()` 只保留当前有效编班类型，不再把旧 snapshot 顺序当成 whitelist。 [Task 1]
- 这次目标机构 `skcity.nursery.id=111824` 的证据链完整：主表 `scope=0`，但正式班级表汇总是 `type4=10班 / 200托位`，且最新通过审核快照也是 `class_types=4, scope=200`。 [Task 1]
- 线上 `skcity.nursery` 并没有 `record_class_num`；本任务的修复 SQL 只能更新真实存在的 `scope`、`class_types`、`class_num`、`class_scope`、`update_time`。 [Task 1]
- 全量 mismatch 扫描命中了 4 家 nursery，但本单只对证据闭环完整的 `111824` 输出修复 SQL；其余 mismatch 不能因为“看起来像同类问题”就一起回填。 [Task 1]

## Failures and how to do differently

- 症状：生产核验 SQL 一上来就查本地实体里有、线上未必有的列，例如 `record_class_num`。处理：先查 `information_schema.columns`，确认真实列集后再拼核验和修复 SQL。 [Task 1]
- 症状：把本地 entity 字段直接投射到 `nursery_audit_info` 等线上表。处理：线上表结构和本地模型可能不一致，跨表验证前先做生产列检查。 [Task 1]
- 症状：看到全量扫描里还有 3 个 mismatch 就想顺手批量修。处理：只修本单证据闭环的目标行，其他机构单独补 root-cause 证明再处理。 [Task 1]
- 症状：把 `computeOrderedTypes()` 修复误解成“历史数据会自动恢复”。处理：类似汇总链路 bug 要区分“预防层代码已修”与“历史脏数据仍需一次性 backfill”。 [Task 1]

# Task Group: gsskservers `course_offline` 已删除活动残留预约生产 SQL 修复

scope: 适用于 `/Users/dalwin/Library/IdeaProject/ZhiJin/gongshu/gsskservers` 内 `course_offline` 删除态活动仍阻塞移动端预约的代码勘查、DBeaver 生产运维脚本编写与执行边界校对；不要把这组记忆泛化成任意课程活动表修复。
applies_to: cwd=/Users/dalwin/Library/IdeaProject/ZhiJin/gongshu/gsskservers; reuse_rule=仅在同仓库 `course_offline` 预约冲突/删除态残留数据修复、且需要人工在生产库执行 SQL 时直接复用；若表结构、状态语义或执行工具变化需重查

## Task 1: 为已删除 `course_offline` 活动生成清理残留预约的生产修复 SQL，成功

### rollout_summary_files

- rollout_summaries/2026-06-02T11-06-46-nKrh-course_offline_deleted_activity_production_sql_fix.md (cwd=/Users/dalwin/Library/IdeaProject/ZhiJin/gongshu/gsskservers, rollout_path=/Users/dalwin/.codex/sessions/2026/06/02/rollout-2026-06-02T19-06-46-019e8803-ba74-7971-aa42-eb412d4148cb.jsonl, updated_at=2026-06-03T07:20:14+00:00, thread_id=019e8803-ba74-7971-aa42-eb412d4148cb, success)

### keywords

- gsskservers, course_offline, course_offline_appointment, DBeaver, production SQL, SELECT FOR UPDATE, ROW_COUNT, APPOINTMENT_OTHER_LIMIT, 10114, state=2, state=1, mobile appointment

## Task 2: 校对 DBeaver 生产运维脚本的执行边界，成功

### rollout_summary_files

- rollout_summaries/2026-06-02T11-06-46-nKrh-course_offline_deleted_activity_production_sql_fix.md (cwd=/Users/dalwin/Library/IdeaProject/ZhiJin/gongshu/gsskservers, rollout_path=/Users/dalwin/.codex/sessions/2026/06/02/rollout-2026-06-02T19-06-46-019e8803-ba74-7971-aa42-eb412d4148cb.jsonl, updated_at=2026-06-03T07:20:14+00:00, thread_id=019e8803-ba74-7971-aa42-eb412d4148cb, success)

### keywords

- DBeaver, transaction, precheck, review SQL, rollback, auto-commit, course_offline_sign, deleted activity, overlap check, candidate id

## User preferences

- 当用户说“我将通过 dbeaver 连接工具去运维生产环境的数据库相关业务表数据”时，默认输出可直接在 DBeaver 执行的、分步骤的运维脚本，而不是只给抽象结论。 [Task 1][Task 2]
- 当用户要求“根据业主需求结合代码勘查结论给出数据运维的 sql 脚本”时，默认把代码勘查结论落到具体 SQL，并且区分预检 SQL、执行 SQL、复核 SQL。 [Task 1]
- 用户在定位 root cause 后继续追问脚本而不是解释，说明这类生产修复场景默认“可执行脚本优先于长篇分析”。 [Task 1]
- 当场景明确是生产库运维时，默认把脚本拆成“查找候选”“预检”“执行”“复核”四段，并提示关闭 auto-commit 或手工 `COMMIT/ROLLBACK`。 [Task 2]

## Reusable knowledge

- 真实业务表名是 `course_offline_appointment`，不是口述中的 `course_offline_appoint`。 [Task 1]
- 移动端预约冲突校验使用 `course_offline_appointment` 关联 `course_offline` 时间段，但没有过滤 `course_offline.state`；因此删除态主表仍可能通过残留 `state=1` 预约记录触发 `APPOINTMENT_OTHER_LIMIT=10114`。 [Task 1]
- 后台删除链路把 `course_offline.state` 置为 `2`，并且只在“删除且当前时间早于签到开始时间”这类特定时机级联处理预约状态；时机较晚时，残留 `state=1` 预约会继续影响新预约。 [Task 1]
- 代码与实体注释存在状态语义不一致：实体注释写 `2=未签到且活动删除`，但后台删除预约的实际代码是把 `course_offline_appointment.state` 置为 `0`；生产修复脚本应跟随代码实际行为，不要只信注释。 [Task 1][Task 2]
- 如果目标是修复“已删除活动仍阻塞移动端预约”，优先修正 `course_offline_appointment.state` 的残留有效预约，而不是动 `course_offline_sign`。 [Task 1][Task 2]
- 这仓内没有独立的课程业务 SQL 索引/规则目录可直接复用，相关表结构与状态更新方式主要还是从 `sunkidsh5server`、`sunkidsdistdrserver` 的 mapper 和 service 代码勘查得到。 [Task 1][Task 2]
- 复核标准应是：关联删除态主表的残留 `state=1` 预约归零，且同身份证再次预约重叠新活动时不再命中 `10114`。 [Task 2]

## Failures and how to do differently

- 症状：按活动名称直接写生产 `UPDATE`。处理：先锁定唯一 `course_offline.id`，名称模糊匹配只放在查找候选 id 的预检步骤。 [Task 1]
- 症状：把 `course_offline_sign` 当成主修复对象。处理：它不参与新活动预约主门禁，默认不要动；先修 `course_offline_appointment.state`。 [Task 1][Task 2]
- 症状：把代码注释里的状态语义直接当成数据库修复目标。处理：以已确认的后台实际更新语句为准，再决定 `state` 应改成什么值。 [Task 1][Task 2]
- 症状：生产脚本只给单句 `UPDATE`。处理：默认写成可回滚事务脚本，包含预检、`SELECT ... FOR UPDATE`、执行、`ROW_COUNT()` 与复核。 [Task 1][Task 2]

# Task Group: skcactivity physical-exam `dept_id` 权限锚点与医院配置接口

scope: 适用于 `/Users/dalwin/Library/IdeaProject/ZhiJin/SunkidCloud/skcservers/skcactivity` 内新 `physicalexam` 模块的 `dept_id` 归属、配置面拆分、`Hospital` 复用、Apifox 同步和提交验收；不要直接套用到旧 `physicalExamination` 南京链路。
applies_to: cwd=/Users/dalwin/Library/IdeaProject/ZhiJin/SunkidCloud/skcservers/skcactivity; reuse_rule=仅在同仓库新 `com.iktapp.skc.activity.physicalexam` 模块及相邻配置面中直接复用，若回到旧南京实现需重新核对

## Task 1: 修复 physical-exam `dept_id` 服务端锚点来源，成功

### rollout_summary_files

- rollout_summaries/2026-06-17T06-01-33-qOG1-skcactivity_physicalexam_deptid_and_hospital_config_fixes.md (cwd=/Users/dalwin/Library/IdeaProject/ZhiJin/SunkidCloud/skcservers/skcactivity, rollout_path=/Users/dalwin/.codex/archived_sessions/rollout-2026-06-17T14-01-33-019ed42b-af9f-7230-bd50-9ea7f7de4fb5.jsonl, updated_at=2026-06-17T08:05:57+00:00, thread_id=019ed42b-af9f-7230-bd50-9ea7f7de4fb5, success)

### keywords

- physicalexam, dept_id, orgDeptId, SecurityUtils, InfantUtil, StaffUtil, NurseryUtil, AppointCreateDTO, DirectExamCreateDTO, AppointmentAppService, ExamResultAppService, 62710409

## Task 2: 新增模块内 `Hospital` 配置接口并同步 Apifox，成功

### rollout_summary_files

- rollout_summaries/2026-06-17T06-01-33-qOG1-skcactivity_physicalexam_deptid_and_hospital_config_fixes.md (cwd=/Users/dalwin/Library/IdeaProject/ZhiJin/SunkidCloud/skcservers/skcactivity, rollout_path=/Users/dalwin/.codex/archived_sessions/rollout-2026-06-17T14-01-33-019ed42b-af9f-7230-bd50-9ea7f7de4fb5.jsonl, updated_at=2026-06-17T08:05:57+00:00, thread_id=019ed42b-af9f-7230-bd50-9ea7f7de4fb5, success)

### keywords

- Hospital, HospitalMapper, HospitalExample, HospitalController, HospitalConfigAppService, physicalExam/hospital, PhysicalExaminationServiceImpl, 南京, 建邺, Apifox, 474898375, 474898528, 11ccb793

## User preferences

- 当用户明确要求 `"管理端由服务端从登录台获取，移动端改为从绑定的业务机构获取该机构的deptId，去掉接收参数dto的前端传入口径"` 时，这个模块里默认优先服务端 authority，不再让请求体携带 `deptId`。 [Task 1]
- 当用户说 `"把当前工作区的修复内容commit提交一下"`，说明这类 review follow-up 修复在验证通过后要默认 stage 相关文件并提交，不要停在未提交状态。 [Task 1]
- 当用户说体检单位医院配置要 `"复用Hospital表"`，并要求在新模块下提供同功能接口时，默认优先做模块内 wrapper/controller，而不是硬复用旧 `/physicalExamination/*` 南京专用接口。 [Task 2]
- 当用户要求 `"改完代码后同步更新apifox接口文档，然后通过后直接提交"`，这条链路的 done criteria 默认包含 Apifox 同步、编译/测试、再 commit。 [Task 2]

## Reusable knowledge

- H5 预约写路径是 `AppPhysicalExamController -> AppointmentAppService.create`，管理端直录写路径是 `ResultController -> ExamResultAppService.createDirect`；这两个入口都会落 `PeAppointment.deptId`，因此都是权限锚点修复面。 [Task 1]
- `AppointCreateDTO` 和 `DirectExamCreateDTO` 已移除 `orgDeptId`；`PeAppointment.deptId` 改由服务端填充。 [Task 1]
- CHILD_ENTRY 应从 `InfantUtil.getDefaultFamilyNurseryId()` -> `NurseryUtil.getDeptId(nurseryId)` 取 `deptId`；STAFF_HEALTH 应优先取 `StaffUtil.getStaffInfo().deptId`，再 fallback 到 `nurseryId -> NurseryUtil.getDeptId(...)`。 [Task 1]
- 管理端直录应使用 `SecurityUtils.getDeptId()`，且这个值在仓库里可能为空，必须显式判空。 [Task 1]
- 旧南京 `PhysicalExaminationServiceImpl.configHospital()` / `getHospitalDetail()` 带有 `hospitalName == login username` 的硬匹配和 token/cache side effects，不适合建邺这类新模块配置面。 [Task 2]
- 新模块的配置面已经按 `activity`、`slotPlan`、`signature` 拆开，`hospital` 作为 `/physicalExam/hospital` 新控制器是自然延续；`HospitalMapper` + `HospitalExample` 已足够覆盖当前按 `deptId` 的查改写，不必动旧 `physicalExamination` 代码。 [Task 2]
- Apifox 正确落点是 `saas` 项目 -> `activity` 模块 -> `南京` -> `配置管理端` 文件夹；新增接口 ID 为 `474898375` 和 `474898528`。 [Task 2]
- 这条链路的有效验收是 `git diff --cached --check` clean、`mvn -nsu -f skc-activity/pom.xml -DskipTests compile` 成功、`mvn -nsu -f skc-activity/pom.xml -Dtest='com.iktapp.skc.activity.physicalexam.**.*Test' test` 成功，当前物理体检测试片段是 88 个测试。 [Task 1][Task 2]

## Failures and how to do differently

- 症状：想用一套统一绑定逻辑给所有 exam type 取 `deptId`。原因：仓库里 child/family 与 staff 的绑定来源不同。处理：按 exam type 分支，复用现有 `InfantUtil` / `StaffUtil` / `NurseryUtil` 路径。 [Task 1]
- 症状：默认假设 `SecurityUtils.getDeptId()` 一定有值。处理：管理端链路要显式 non-null guard，而不是把登录上下文完整性当成前提。 [Task 1]
- 症状：想直接复用旧南京体检医院配置接口。原因：忽略了旧逻辑的 `hospitalName == username` 读回约束。处理：新模块新增独立 controller/service，避免把南京读回 bug 带进来。 [Task 2]
- 症状：先建 Apifox 接口、后找目录。处理：先确认项目与 folder，再创建接口，避免文档落错位置。 [Task 2]

# Task Group: 个人 AI 工作流域约定

scope: 适用于涉及 `/Users/dalwin/Documents/AI/` 路径族的读取、新建、整理和文档路由；这是个人 AI 工作流资产域，不要混入业务仓库默认语境。
applies_to: cwd=/Users/dalwin（或任何涉及 `~/Documents/AI/` 的任务）; reuse_rule=路径未变化时可直接复用；如 docs 结构调整需重新读入口说明

## Task 1: 确立 `~/Documents/AI/` 的工作流域边界与 docs 管理入口

### rollout_summary_files

- phase2_workspace_diff.md (cwd=/Users/dalwin, rollout_path=user-maintained-memory-via-workspace-diff, updated_at=2026-06-13T16:26:00+08:00, thread_id=n/a, authoritative manual memory carried in this Phase 2 diff)

### keywords

- /Users/dalwin/Documents/AI, docs/README.md, archive, knowledge, skill 活跃工作区, AI workflow domain, [ad-hoc note]

## User preferences

- `/Users/dalwin/Documents/AI/` 是个人 AI 工作流专属域；命中该路径时，默认先按工作流资产来理解任务，而不是把它当普通业务仓。 [Task 1]
- 访问 `~/Documents/AI/docs/` 下任何文档前，必须先读 `docs/README.md`，先分清 `archive/`、`knowledge/` 和各 skill 活跃工作区后再继续。 [Task 1]

## Reusable knowledge

- `~/Documents/AI/docs/README.md` 定义了 docs 目录的唯一管理规范：`archive/` 是已完成任务历史文档，只读参考；`knowledge/` 是无时效纯知识；各 skill 文件夹是当前活跃工作区。 [Task 1]
- `~/Documents/AI/` 是 git repo，职责是记录“工作流为什么这样演化”；它与 `~/Library/CodeRepo/AI/` 这种 skills 代码源仓不同。 [Task 1]

## Failures and how to do differently

- 症状：把 `~/Documents/AI/` 当普通业务仓处理。处理：命中该路径族时，先切到“个人 AI 工作流域”语境，再决定是否读文档、归档还是整理结构。 [Task 1]
- 症状：未读 `docs/README.md` 就直接打开子文档。处理：先读入口 README，再定位具体文档，避免把 `archive/`、`knowledge/`、活跃工作区混用。 [Task 1]

# Task Group: skcactivity courseOffline 复制活动年龄异常与 develop 隔离 worktree

scope: 适用于 `/Users/dalwin/.codex/worktrees/36a8/skcactivity` 的最新 develop 基线 worktree，以及复制后活动详情/海报年龄显示与生产证据交叉核验。
applies_to: cwd=/Users/dalwin/.codex/worktrees/36a8/skcactivity; reuse_rule=worktree 路径、commit 与活动 ID 是一次性证据；可复用 develop 基线和 Controller → Service → Mapper + 只读生产数据的排查法

## Task 1: 从最新 develop 创建 bugfix worktree，成功

### rollout_summary_files

- rollout_summaries/2026-04-23T06-18-10-4g2d-develop_worktree_courseoffline_copy_age_detail_analysis.md (cwd=/Users/dalwin/.codex/worktrees/36a8/skcactivity, rollout_path=/Users/dalwin/.codex/sessions/2026/04/23/rollout-2026-04-23T14-18-10-019db8fd-2366-75d0-a90f-48999e97e7e9.jsonl, updated_at=2026-07-22T08:37:32+00:00, thread_id=019db8fd-2366-75d0-a90f-48999e97e7e9, success)

### keywords

- git-worktree, origin/develop, eae90dd6aab64ed8276e071e7c4718ab6be6d1e6, codex/bugfix-develop-20260423, skc-activity/pom.xml, Nexus 401

## Task 2: 诊断复制活动 `63761` 年龄显示异常，成功

### rollout_summary_files

- rollout_summaries/2026-04-23T06-18-10-4g2d-develop_worktree_courseoffline_copy_age_detail_analysis.md (cwd=/Users/dalwin/.codex/worktrees/36a8/skcactivity, rollout_path=/Users/dalwin/.codex/sessions/2026/04/23/rollout-2026-04-23T14-18-10-019db8fd-2366-75d0-a90f-48999e97e7e9.jsonl, updated_at=2026-07-22T08:37:32+00:00, thread_id=019db8fd-2366-75d0-a90f-48999e97e7e9, success)

### keywords

- release/syzh260110, courseOffline, 63761, 63438, ageString, ageList, alterPosterImg, CourseOfflineDao.xml, getById, dbq, sys_oper_log, skcity

## User preferences

- 当用户说“先以develop分支的最新代码commit情况为基准检出一个专用于bug修复任务的worktree”时，先 `git fetch origin develop`、确认远端 commit，再创建隔离 worktree。 [Task 1]
- 当用户要求按生产部署分支，结合截图、SQL、截断日志分析，并核对“复制后新建的63761这个记录的返回数据是否正确”时，交叉核对部署代码、保存请求、详情响应、Mapper SQL、只读数据与 `sys_oper_log`。 [Task 2]

## Reusable knowledge

- 项目根目录没有 `pom.xml`；基线编译为 `mvn -f skc-activity/pom.xml -DskipTests compile`。本次基线为 `origin/develop` 的 `eae90dd6aab64ed8276e071e7c4718ab6be6d1e6`，worktree 位于 `/Users/dalwin/.codex/worktrees/36a8/skcactivity-bugfix`；现有 Nexus 401、systemPath/API 警告不等于 compile 失败。 [Task 1]
- `CourseOfflineDao.xml:getById` 直接取 `c.age`/`c.age_string`，`CourseOfflineService.getDetail` 将 `age` 拆为 `ageList`。`63761` 保存请求和数据库均为 `age=7..20`、`age_string=6-48月龄`；截图旧值对应源活动 `63438` 的 `[6,20]`/`5月龄,36-48月龄`，后端保存与详情链路正确。 [Task 2]
- `alterPosterImg` 仅保存前端 JPEG 路径，不生成/校验图中文字；页面旧年龄优先检查前端是否仍传源 ID、保存后未重拉 `/detail/63761`，或海报组件使用复制源缓存。`63761` 已 `state=-1`，详情 SQL 会过滤，不能靠现在重调接口复现历史响应。 [Task 2]

## Failures and how to do differently

- 症状：只凭页面截图归因于数据库或 `ageToString`。处理：同时核对保存返回 ID、详情响应字段、海报上传请求与操作日志；当前工作区未定位前端实现，因此前端结论应标为基于证据的推断。 [Task 2]
- 症状：把前端图片内容视为服务端持久化字段已错。处理：`alterPosterImg` 缺少版本/部门/内容一致性校验；彻底方案是服务端依据新 `courseId` 重生成海报，短期至少用专用 DTO、权限和版本校验，保存后返回完整详情并清空新记录 `poster_img`。 [Task 2]

# Task Group: skcinfant 儿童体检详情码值转换与仅提交业务源文件

scope: 适用于 `/Users/dalwin/Library/IdeaProject/ZhiJin/SunkidCloud/skcservers/skcinfant` 的儿童体检详情字典展示、多选码值解析、测试与只提交 `src/main` 的交付边界。
applies_to: cwd=/Users/dalwin/Library/IdeaProject/ZhiJin/SunkidCloud/skcservers/skcinfant; reuse_rule=同模块同省级体检码表可复用；新码表或生产值变化需重新核对

## Task 1: 修复儿童体检详情码值展示并推送，成功

### rollout_summary_files

- rollout_summaries/2026-07-13T05-57-54-cFW6-skcinfant_exam_detail_code_dictionary_fix.md (cwd=/Users/dalwin/Library/IdeaProject/ZhiJin/SunkidCloud/skcservers/skcinfant, rollout_path=/Users/dalwin/.codex/sessions/2026/07/13/rollout-2026-07-13T13-57-54-019f5a0d-b0b3-75b3-a8b8-531319b8b326.jsonl, updated_at=2026-07-17T07:09:14+00:00, thread_id=019f5a0d-b0b3-75b3-a8b8-531319b8b326, success)

### keywords

- ExamCodeDict, ChildHealthPortraitServiceImpl, ExamDetailVO, 多选字典, complexion, skinCheck, deveAsse, dealOpinion, yesNo, git add -f, 519d018654bb1f26aec77b9367464b4252558e23

## User preferences

- 当用户说“提交推送src源文件，测试文件先留在本地自行维护即可”时，只暂存提交 `src/main`，保留测试文件本地不提交。 [Task 1]

## Reusable knowledge

- 面色：`1=红润, 2=黄染, 3=潮红, 4=苍白, 5=发绀, 9=其他`；皮肤多选为 `01` 至 `08`、`99=其他`；发育评估 `0=未评估, 1=通过, 2=未通过`；`yesNo` 的生产口径为 `0=否, 1=是`，用于沙眼和是否转诊。 [Task 1]
- 多选解析支持英文/中文逗号、尾逗号、重复码、`1、科学喂养`，按首次顺序去重，未知值原样返回。`ExamCodeDict.java`、`ChildHealthPortraitServiceImpl.java`、`ExamDetailVO.java` 是修改面。 [Task 1]
- `mvn -q test` 通过（24 tests、0 failures/errors），`git diff --check` 通过；提交 `519d018...` 已推送 develop。 [Task 1]

## Failures and how to do differently

- 症状：Maven 报 `resolver-status.properties (Operation not permitted)`。处理：允许 Maven 访问本机依赖仓库后重试。 [Task 1]
- 症状：测试文件不在 `git status`。处理：全局 `**/*Test.java` ignore 所致；只有用户要求提交时才 `git add -f`。 [Task 1]

# Task Group: skc-nursery 善于在杭托育券月度天数只读排查与补数 SQL

scope: 适用于 `/Users/dalwin/Library/IdeaProject/ZhiJin/SunkidCloud/skcservers/skcnursery/skc-nursery` 的善于在杭托育券月度天数异常、`skcity` 生产只读核验和人工审批补数 SQL。
applies_to: cwd=/Users/dalwin/Library/IdeaProject/ZhiJin/SunkidCloud/skcservers/skcnursery/skc-nursery; reuse_rule=同实例、同托育券统计链路可复用；任何写入仅作人工 handoff，不能由 agent 执行

## Task 1: 核验朱熤航、郑裕熙、沈初煦的月度天数并准备运维 SQL，部分完成

### rollout_summary_files

- rollout_summaries/2026-07-15T06-50-35-NyWY-shanyu_zai_hang_coupon_analysis_and_district_code_mapping_fi.md (cwd=/Users/dalwin/Library/IdeaProject/ZhiJin/SunkidCloud/skcservers/skcnursery/skc-nursery, rollout_path=/Users/dalwin/.codex/sessions/2026/07/15/rollout-2026-07-15T14-50-35-019f648a-a580-7b61-a7cc-7e3433c971e8.jsonl, updated_at=2026-07-21T04:13:17+00:00, thread_id=019f648a-a580-7b61-a7cc-7e3433c971e8, partial)

### keywords

- 善于在杭查询, skcity, nursery_coupon, nursery_child_sign_month_statistic, nursery_child_sign, coupon_type=2, district_code=330109, child_id_card, dbq, 身份证号不一致

## User preferences

- 当用户明确列出“朱熤航、郑裕熙、沈初煦”并要求“重新跟我的文本提供的名字来排查”时，以用户文字为准，不能依赖图片 OCR 或猜测。 [Task 1]
- 当用户限定“只读分析任务”且另一个线程负责编码时，不改代码、不直写生产库；只交付查询和待人工执行 SQL。 [Task 1]

## Reusable knowledge

- 正确入口是 `dbq '善于在杭查询'`，业务 schema 为 `skcity`；先验证候选实例的 schema 和关键表总量，不能由另一个 `善于在杭` 实例空表推断生产无数据。 [Task 1]
- 萧山托育券为 `coupon_type=2`、`district_code='330109'`；有效签到条件是机构 `state <> -1`、`is_record=1`、`is_cheap=1`，签到 `state <> 0`，按 `COUNT(DISTINCT sign_date)` 统计。 [Task 1]
- 页面以 `nursery_coupon.child_id_card + grant_month` 关联月汇总；券身份证与实际签到儿童身份证不一致时，即使签到汇总存在，页面也会显示 0。不能直接修改儿童主档身份证号。 [Task 1]

## Failures and how to do differently

- 症状：图片 OCR 把姓名识别错。处理：先锁定用户文本中的精确姓名。 [Task 1]
- 症状：补数脚本含 `INSERT` 却没有写后验证。处理：严格区分只读预检与待人工审批写入脚本；写入前要求人工确认。 [Task 1]

# Task Group: skcactivity 南京从业人员体检导入 Apifox 同步与本地 MD 清理

scope: 适用于 `/Users/dalwin/Library/IdeaProject/ZhiJin/SunkidCloud/skcservers/skcactivity` 的 Apifox MCP 文档同步、同名目录定位、外发确认、回读验证和本地接口 MD 删除。
applies_to: cwd=/Users/dalwin/Library/IdeaProject/ZhiJin/SunkidCloud/skcservers/skcactivity; reuse_rule=同 saas/activity 项目和接口文档迁移可复用；上传其他 SaaS 目标仍需独立取得确认

## Task 1: 同步南京从业人员体检导入接口到 Apifox 并删除本地 MD，成功

### rollout_summary_files

- rollout_summaries/2026-07-16T07-38-59-6Z8N-apifox_nanjing_appointment_import_sync_and_delete_md.md (cwd=/Users/dalwin/Library/IdeaProject/ZhiJin/SunkidCloud/skcservers/skcactivity, rollout_path=/Users/dalwin/.codex/sessions/2026/07/16/rollout-2026-07-16T15-38-59-019f69dd-503d-79f1-acb9-8d11d0d58eb5.jsonl, updated_at=2026-07-16T07:58:47+00:00, thread_id=019f69dd-503d-79f1-acb9-8d11d0d58eb5, success)

### keywords

- Apifox, mcp__apifox__getProjectSummary, mcp__apifox__getStructureInfo, mcp__apifox__createHttpEndpoint, mcp__apifox__getHttpEndpoint, form-data, responseExamples, projectId=6776425, folderId=76611615, 488219523, 488219797

## User preferences

- 当用户要求“通过mcp更新到我配置的apifox文档saas项目下…更新好后删掉这个本地的md接口文档”时，done criteria 是先同步、回读验证，再删除本地 MD。 [Task 1]
- Apifox 上传被安全策略拦截时，先说明外发风险并等待明确“确认同意，开始同步”。 [Task 1]

## Reusable knowledge

- 本仓 `.apifox/6776425_saas.settings.json` 是本地缓存入口；`saas -> activity -> 体检管理 / 体检预约列表` 的正确 folderId 为 `76611615`，同名嘉善旧目录是 `77355311`，必须以 `getStructureInfo` 区分。 [Task 1]
- `requestBody.type` 应为 `form-data`，`responseExamples[].data` 保持字符串化 JSON 才能稳定渲染。创建后必须用 `getHttpEndpoint` 回读；本次 ID 是 `488219523`、`488219797`。 [Task 1]

## Failures and how to do differently

- 症状：同名目录仅凭名字猜目标。处理：用结构信息或已有接口路径前缀核对。 [Task 1]
- 症状：同步成功但本地文档未清理。处理：删除后用 `test -e <file> && echo PRESENT || echo DELETED` 复核。 [Task 1]

# Task Group: Codex-Dream-Skin 本机主题签名阻断与重装前 Codex 用户数据备份

scope: 适用于 `/Users/dalwin/Library/CodeRepo/AI/Codex-Dream-Skin` 的 macOS 本机主题安装、codesign 预检，以及重装前敏感 Codex 用户数据备份规划；主题与备份均有明确安全边界。
applies_to: cwd=/Users/dalwin/Library/CodeRepo/AI/Codex-Dream-Skin; reuse_rule=主题参数和应用签名状态具有时效性；备份涉及敏感数据，任何实际读取/复制前都需重新获得明确授权

## Task 1: Bloodborne 玛丽亚本机主题安装被签名校验阻断，部分完成

### rollout_summary_files

- rollout_summaries/2026-07-18T08-32-44-AXUm-bloodborne_lady_maria_theme_signature_backup_and_main_sync.md (cwd=/Users/dalwin/Library/CodeRepo/AI/Codex-Dream-Skin, rollout_path=/Users/dalwin/.codex/sessions/2026/07/18/rollout-2026-07-18T16-32-44-019f745b-3e18-7380-ae80-6bb31cb57072.jsonl, updated_at=2026-07-20T11:42:03+00:00, thread_id=019f745b-3e18-7380-ae80-6bb31cb57072, partial)

### keywords

- Bloodborne, Lady Maria, Codex Dream Skin, codesign, invalid signature, cua_node, loopback CDP, custom-<timestamp>, backup, ~/.codex, codex-thread.json

## User preferences

- 当用户选择“本机私用”并要求“直接安装并应用”时，受版权保护的游戏素材只进入本机主题，不进入仓库预设或发行包；按计划在当前会话推进实际安装。 [Task 1]
- 当用户要求“先做好文件的备份”，且担心卸载清理用户数据时，备份应覆盖配置、线程记录和用户设置，不只备份应用程序文件。 [Task 1]

## Reusable knowledge

- macOS 主题边界是不修改官方 `.app`、`app.asar` 或签名；使用已验证的官方内置 Node + loopback CDP 注入。活动主题/快照 ID 由脚本生成，不能承诺固定 ID。 [Task 1]
- 计划备份根目录是 `/Users/dalwin/Library/ConfigFile/codex/2026-07-18-codex-reinstall-backup/`，要求新建、不覆盖、权限 700，并生成 `manifests/files.txt` 与 `manifests/SHA256SUMS`；不备份已损坏应用二进制本体。 [Task 1]

## Failures and how to do differently

- 症状：主题测试通过但运行预检失败。原因：`codesign --verify --strict` 对 `/Applications/ChatGPT.app` 和 `cua_node/bin/node` 报 `invalid signature (code or signature have been modified)`。处理：不绕过签名检查；先官方重装或修复应用。 [Task 1]
- 症状：以为同意主题安装就等于同意读取备份源。处理：备份可能含登录令牌、会话、聊天记录和路径信息；实际执行前必须告知风险并获得明确授权。 [Task 1]
