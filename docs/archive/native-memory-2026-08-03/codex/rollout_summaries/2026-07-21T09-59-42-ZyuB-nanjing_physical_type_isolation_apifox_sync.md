thread_id: 019f841d-ef6e-7fa0-bd1b-af3a77c62b79
updated_at: 2026-07-27T03:59:49+00:00
rollout_path: /Users/dalwin/.codex/sessions/2026/07/21/rollout-2026-07-21T17-59-42-019f841d-ef6e-7fa0-bd1b-af3a77c62b79.jsonl
cwd: /Users/dalwin/Library/IdeaProject/ZhiJin/SunkidCloud/skcservers/skcactivity
git_branch: develop

# 南京体检类型隔离修复并同步 Apifox，已提交推送成功

Rollout context: 在 skc-activity 中根据生产 SQL、代码现状和 Apifox 现有契约，修复南京入托/从业人员体检预约类型串用问题，并更新接口文档。

## Task 1: 生产数据定位与根因确认

Outcome: success

Preference signals:
- 用户提供 SQL 结果并明确指出“预约时间不等于创建时间”，后续类似排查应按预约时段 `start_time/end_time` 判断业务发生时间，不要误用 `create_time`。
- 用户确认“按这个修订方案实施本次任务修复”，表明完成 RCA 后先给出方案、等待确认，再进入编码。

Reusable knowledge:
- 生产数据显示两条记录分别为 `pau_id=55`（`appoint_time_id=204`、`config_pe_type=2`、从业人员体检）和 `pau_id=53`（`appoint_time_id=197`、`config_pe_type=1`、儿童入托体检），不是同一条记录被错误分到两个列表。
- 直接根因是前端第二次预约选中了从业人员体检时段；两条记录 `detail_pe_type` 为空，`user_id` 相同仅表示同一登录账号。
- 后端缺少预约请求 `peType` 与时段关联体检配置类型的一致性校验，也未将配置类型作为落库权威值。

References:
- 生产记录：`pau_id=55 -> appoint_time_id=204 -> pe_id=2 -> config_pe_type=2`；`pau_id=53 -> appoint_time_id=197 -> pe_id=1 -> config_pe_type=1`。

## Task 2: 代码修复与测试

Outcome: success

Reusable knowledge:
- `/physicalAppointment/peResult/direct` 改为返回 `PeResultDirectSaveVO { perId, pauId }`。
- 南京预约保存时校验传入 `peType`（若传入）与 `physical_examination.type` 一致；校验通过后覆盖 `appointDetail.peType` 为配置类型。缺失 `peType` 保持兼容，不立即阻断旧前端。
- 重复预约查询增加实际 `pe.type` 条件，避免儿童与从业人员类型互相阻断。
- MySQL/Kingbase 列表、统计和管理查询统一采用“有预约配置时以 `pe.type` 为准；无配置直录才回退 `pau.detail.peType`”。
- 儿童与从业人员直录用户匹配拆为独立方法。

References:
- Worktree/分支：`/private/tmp/nanjing-physical-type-fix`，`codex/fix-南京体检类型隔离/20260727_v1.0.0`。
- 关键文件：`PhysicalAppointmentServiceImpl.java`、`PhysicalExaminationDao.xml`、`PhysicalAppointmentService.java`、`PhysicalExaminationDao.java`、`PeResultDirectSaveVO.java`。
- RED 测试 4 项全部失败后实现；GREEN 通过，完整模块测试 `37 tests, 0 failures`；`git diff --check` 通过。

## Task 3: Apifox 文档同步

Outcome: success

Reusable knowledge:
- Apifox 项目 `saas`：`6776425`；接口 ID `475638055`，路径 `/physicalAppointment/peResult/direct`。
- 已补充 `appointDetail.peType` schema，成功响应 `data` 改为包含必填 `perId`、`pauId` 的对象，并更新成功示例。
- 回读确认 requestBody 为 `application/json`，schema 和示例均正确；这是 Apifox 桌面端渲染所需格式。

References:
- 回读确认：`peType` 已存在；响应 `data.type=object`，required=`[perId,pauId]`；示例为字符串化 JSON。

## Task 4: 提交与推送

Outcome: success

Preference signals:
- 用户明确要求“直接提交推送到develop”，类似任务在完成验证后可直接执行非强制 push，不必再次要求额外确认。

Reusable knowledge:
- 提交前刷新 `origin/develop`，确认分支与远端基线一致；本次 `0 0`。
- 仅提交 5 个生产代码文件，本地契约测试受全局忽略规则影响，未提交。
- 提交：`8d1ee4a5 fix(physical): 修复南京体检类型隔离并补充直录返回`。
- 非强制推送成功，远端 `develop` 回读指向完整哈希 `8d1ee4a5d2ef797ee61e7bdd5b385732f7afc89e`，工作区干净。
