南京体检管理改版（2026-06 需求）**确定走"在遗留老模块上做适配改造"路线**，不是另起新模型。

- **落地层**：遗留控制器 `PhysicalAppointmentController`（`@RequestMapping("/physicalAppointment")`），数据基于老表 `physical_appoint_user` + `physical_enter_result`（活动层），代码在 `skc-activity`。
- **已废弃**：Apifox 项目 saas(6776425) 里「体检管理/南京（适配层）」目录下的一整套 `/physicalExam/*` 接口（新模型 `pe_appointment`/`pe_lab_result`、examType、statusBucket、"去活动层重构"）是**早期理解有误走的独立开发，要废弃**。重新评估后确认在老模块适配工作量更小——这就是本次任务的由来。**以遗留层代码为准。**
- **Apifox 文档位置**：老接口文档在 folder **76611615**（体检管理/体检预约列表），不是南京适配层 folder 88548136。本次同步：`appointUser`(407356885) 加 bizState；新建 `appointUser/statistics`、`peResult/direct`、`manage/list`。

**Why：** 不知道这条决策时，看 Apifox 会被「南京适配层（/physicalExam/*，更完整、更新）」误导，以为要按那套实现，实际方向相反。

**How to apply：** 南京体检相关需求一律在 `/physicalAppointment/*` 老模块上改；南京判断统一用 `@Value("${project.name:nanjing}")` + `"nanjing".equals(projectName)`；数据权限注意无预约的直录记录无 `physical_appoint` 关联，`@DataScope` 用 `deptAlias="pau"` 才不会漏。业务状态口径：bizState 1已预约未体检/2体检中/3不合格/4合格未盖章/5合格已盖章，由 pe_state + `per.detail.result`(1合格2不合格) + `per.is_sign` 派生。改 SQL 记得 `PhysicalExaminationDao.xml` 有 MySQL+Kingbase 双方言。详见 [[skcactivity-build]]。

**hospital ↔ 预约配置 的账号级绑定（2026-06，建邺/南京 H5 getHospitalList）：**
- **`physical_examination.hospital_id` 是死列**——建表起就在，但全代码无任何写入点（`addPhysicalExamination` 不写、`PhysicalExaminationDTO` 无此字段），别误以为它是 hospital↔体检配置的关联键。
- 同一 `dept_id` 下可有多个 sys_user 账号，各自配自己的 `hospital`（建邺走 `HospitalConfigAppService.configHospital`，`/physicalExam/hospital` 路径，这块是活的、非废弃适配层）和各自的预约规则。**精确匹配键是账号 `sys_id`**：`hospital.sys_id`（configHospital 新建时写当前 userId）↔ `physical_appoint.sys_id`（新增列，`activityPeAppointSave` 新增时写当前 userId）。`getPhysicalExaminationTimeIds` 取 paId 走 `pa.sys_id = h.sys_id` + `pa.pe_id→physical_examination.type` 过滤，**不要再用 dept_id 关联**（dept 被多账号共享）。
- `physical_examination` 配置业务规则：同 `dept_id`+同 `type` 仅一条正常数据（`checkPhysicalExaminationType`，只拦新增）。给 `physical_appoint` 这类老表加列要补 MyBatis Generator 四件套：domain + `PhysicalAppointExample`（criteria 方法）+ `PhysicalAppointMapper.xml` + DDL；项目无 liquibase，DDL 落 `docs/spec-architect/.../sql/` 手写双方言、被 gitignore、DBA 手动执行。

**体检结果明细 peResultDetail 的项目分流（2026-06）：** `PeResultDTO.peResultDetail` 已改为 `Object` 接收（南京报告结构与老 `PeResultDetail` 不同，前端视力等会传 "5.0" 字符串，强类型 Jackson 入参会 500）。消费侧走 `PhysicalAppointmentServiceImpl` 内部类 `PeResultStrategy`（`afterPropertiesSet` 按 `Constants.PROJECT_NAME_NANJING` 选 `DefaultPeResultStrategy`/`NanjingPeResultStrategy`，与 `UserAppointStrategy` 同款）：默认→解析 `PeResultDetail` 维持原逻辑；南京→解析 `JSONObject` 走自己定义、不复用 PeResultDetail。完成度→`pe_state`(7全完成/6体检中) 走 `resolvePeState`；直录 `activityPeResultDirectSave` 基本信息以 `appointDetail` 为准、不再从 peResultDetail 拼。**注意 pe_state（体格检查完成度）与 bizState 是两个独立维度**：bizState/统计/婴幼儿列表只认 `per.detail ->> '$.result'`（文本 '1'合格/'2'不合格）+ `is_sign`，`->>` 取文本与 result 存数字/字符串无关，故 peResultDetail 改 Object 不影响这些状态判断。项目名判断统一用 `Constants.PROJECT_NAME_NANJING`，勿再硬编码 `"nanjing"`。
