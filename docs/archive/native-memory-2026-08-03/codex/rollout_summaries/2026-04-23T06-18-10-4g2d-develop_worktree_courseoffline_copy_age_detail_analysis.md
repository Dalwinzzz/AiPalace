thread_id: 019db8fd-2366-75d0-a90f-48999e97e7e9
updated_at: 2026-07-22T08:37:32+00:00
rollout_path: /Users/dalwin/.codex/sessions/2026/04/23/rollout-2026-04-23T14-18-10-019db8fd-2366-75d0-a90f-48999e97e7e9.jsonl
cwd: /Users/dalwin/.codex/worktrees/36a8/skcactivity
git_branch: release/bj/20250928

# 基于 develop 创建 bugfix worktree，并定位 courseOffline 复制活动年龄显示异常

Rollout context: 用户先要求以最新 develop 为基准创建专用 bugfix worktree，随后要求按生产部署分支 `release/syzh260110` 分析 `/courseOffline/subStatisticsList` 相关问题，并进一步核查复制活动 `63761` 的详情接口返回是否正确。主要工作目录为 `/Users/dalwin/.codex/worktrees/36a8/skcactivity`。

## Task 1: 创建 develop 基准 bugfix worktree

Outcome: success

Preference signals:

- 用户要求“先以develop分支的最新代码commit情况为基准检出一个专用于bug修复任务的worktree” -> 类似任务应先刷新远端基线，再创建隔离 worktree，不直接依赖本地缓存。

Key steps:

- 检查仓库状态、当前 detached worktree、已有 worktree 布局及项目约定。
- 执行 `git fetch origin develop`，确认 `origin/develop` 与本地 `develop` 均为 `eae90dd6aab64ed8276e071e7c4718ab6be6d1e6`。
- 创建 `/Users/dalwin/.codex/worktrees/36a8/skcactivity-bugfix`，分支为 `codex/bugfix-develop-20260423`，跟踪 `origin/develop`。
- 新 worktree 状态干净；执行 `mvn -f skc-activity/pom.xml -DskipTests compile` 成功。项目根目录没有 `pom.xml`，存在 `skc-activity`、`skc-evaluation`、`skc-qa` 三个模块。

Failures and how to do differently:

- 项目内没有 `.worktrees/`、`worktrees/` 或 `CLAUDE.md` 约定，因此将 worktree 放在当前 Codex worktree 组旁边，避免嵌套污染仓库。
- Maven 有 Nexus 401、systemPath 和内部 API 警告，但编译最终 `BUILD SUCCESS`；后续应区分现有环境警告与真正编译失败。

References:

- 基准提交：`eae90dd6aab64ed8276e071e7c4718ab6be6d1e6`
- 分支：`codex/bugfix-develop-20260423`
- Worktree：`/Users/dalwin/.codex/worktrees/36a8/skcactivity-bugfix`
- 基线命令：`mvn -f skc-activity/pom.xml -DskipTests compile`

## Task 2: 分析复制活动年龄显示异常及详情接口

Outcome: success

Preference signals:

- 用户要求使用生产部署分支代码，结合截图、理论 SQL、生产数据库和截断日志“一并提取扫描分析” -> 类似线上问题应交叉核对部署分支、Mapper SQL、真实生产数据和 `sys_oper_log`，不能只看代码推断。
- 用户进一步要求核查“详情接口结合现有数据库数据情况下复制后新建的63761这个记录的返回数据是否正确” -> 应沿 Controller → Service → Mapper 还原接口响应，并逐字段核对数据库，而不是只比较页面截图。

Key steps:

- 按只读数据库规范使用完整路径 `/Users/dalwin/Library/ConfigFile/db/dbq` 查询“善于在杭正式”库；确认表在 `skcity` schema。
- 对生产记录和操作日志进行时间线核对：源活动 `63438` 使用 `ageList=[6,20]`，对应 `age='6,20'`、`age_string='5月龄,36-48月龄'`；复制创建的 `63761` 请求明确提交 `ageList=[7..20]`，数据库保存为 `age='7..20'`、`age_string='6-48月龄'`。
- `/courseOffline/save` 返回新 ID `63761`，随后 `/courseOffline/alterPosterImg` 绑定海报；该接口只保存前端传入的图片路径，不生成或校验图片内容。
- 详情接口 `/staff/courseOffline/detail/{courseId}` 调用 `courseOfflineService.getDetail(courseId)`；`CourseOfflineDao.xml` 的 `getById` 直接查询 `c.age` 与 `c.age_string`，Service 再将 `age` 拆为 `ageList`。
- 因此如果请求的是 `courseId=63761`，详情关键字段应为 `age='7,8,...,20'`、`ageString='6-48月龄'`、`ageList=['7',...,'20']`。截图中的旧值实际对应源活动 `63438`，不是新活动。

Reusable knowledge:

- 生产证据链闭合：`63438` 于 2026-07-20 创建；2026-07-22 14:59:51 保存 `63761`，14:59:54 上传 `63761` 海报，15:01:34 删除 `63761`。后续活动 `63770` 才保存为 `[1..20]` / `0-48月龄`。
- `SaveCourseOfflineVO.buildCourseOffline()` 用 `ageList` 生成主表 `age`；新增保存逻辑在部署分支对 `course_type=1` 执行 `ageToString(vo.getAgeList())`，所以本案例后端保存年龄值正确。
- `getDetail` / `getDetailById` 的详情 SQL没有复制源关联逻辑，不会把 `63438` 的年龄读给 `63761`。若页面显示旧值，优先检查前端是否仍传源 ID、保存后未重新请求新详情、或海报组件继续使用复制源缓存对象。
- 服务端确有边界漏洞：`alterPosterImg` 无条件信任前端生成的 JPEG，只更新 `poster_img`；无法验证图片内文字是否匹配当前数据库字段。另有编辑保存分支未同步更新 `age`/`ageString` 的风险，但这不是本次新增复制问题的直接原因。
- 现有 `/courseOffline/needCreate` 只查询待生成海报活动，仓库内未发现真正的服务端图片渲染能力。彻底方案是服务端基于新 `courseId` 查询持久化数据后生成海报；短期可增加新 DTO、权限/部门校验、版本校验、保存后返回完整详情并强制新记录 `poster_img=NULL`。

Failures and how to do differently:

- 不要把页面显示旧值直接归因于数据库或 `ageToString`；必须同时查看保存请求、详情响应、海报上传请求和操作日志。
- `63761` 当前已逻辑删除（`state=-1`），详情 SQL包含 `c.state != -1`，因此现在重新调用接口无法复现其历史响应；历史结论来自保存请求、操作日志和删除前数据库记录。
- 前端仓库未在现有工作区中找到明确的复制实现，因此前端责任点是基于接口和数据库证据推断的：应在 Network 中确认保存返回 ID、是否请求 `/detail/63761`、详情响应 `ageString` 以及 `/alterPosterImg` 前海报组件实际使用的数据源。

References:

- 详情 Controller：`skc-activity/src/main/java/com/iktapp/skc/activity/controller/staff/StaffCourseOfflineController.java:210-225`
- 详情 Service：`skc-activity/src/main/java/com/iktapp/skc/activity/service/courseoffline/CourseOfflineService.java:1289-1315`
- 详情 SQL：`skc-activity/src/main/resources/mapper/activity/CourseOfflineDao.xml:973-1053`
- 海报接口：`CourseOfflineController.java:1238-1244`；`CourseOfflineService.java:2681-2689`
- 生产日志关键记录：`oper_id=14548336` 创建 `63761`，`oper_id=14548338` 上传其海报；保存请求年龄为 `[7,8,...,20]`，接口返回 `data=63761`。
- 生产数据库关键结果：`63761` 为 `age=7..20`、`age_string=6-48月龄`；源 `63438` 为 `age=6,20`、`age_string=5月龄,36-48月龄`。
