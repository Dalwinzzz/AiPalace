thread_id: 019e4dcc-42a4-7cc3-9ee4-7c464ccf4969
updated_at: 2026-07-20T13:13:44+00:00
rollout_path: /Users/dalwin/.codex/sessions/2026/05/22/rollout-2026-05-22T11-48-12-019e4dcc-42a4-7cc3-9ee4-7c464ccf4969.jsonl
cwd: /Users/dalwin/Library/IdeaProject/ZhiJin/SunkidCloud/skcservers/skcdatasum
git_branch: develop

# 南京建邺驾驶舱动态指标事务隔离并推送

Rollout context: 在 skc-datasum 中排查建邺国企机构数异常及定时任务超时回滚问题，并按用户要求实现独立事务隔离。

## Task 1: 建邺国企指标异常根因分析

Outcome: success

Key steps:
- 对比生产数据、字段映射、SQL 与提交历史，确认旧数据来自旧版机构承办类型映射：旧版将类型 3/4 分别映射为国企/学校，导致生产 JSON 出现 `school=9,stateCorp=2`。
- 当前代码已修正映射：类型 2=学校、3=机关事业单位、4=国企；并通过社会办托专题查询覆盖建邺国企数。
- 确认生产记录 `update_by=建邺区`，而当前 writer 固定写入 `update_by=数据中心自动同步`，说明生产数据不是当前 writer 生成的结果。
- 进一步确认调度端 Feign 调用未检查失败返回，fallback 可能导致调度平台显示成功但数据未更新。

Reusable knowledge:
- 建邺动态 key：`nurseryList-320105`、`kindergartenList-320105`。
- 当前正确口径示例：`nurseryList-320105` 应由社会办托专题返回 `stateCorp=9`；幼儿园列表 `stateCorp=0`。
- 相关代码：`CareServiceNurseryConfigDataBO.java`、`NanjingJianyeDashboardDynamicServiceImpl.java`、`JianyeTopicReportDao.xml`。

## Task 2: 每个动态 key 独立事务重构

Outcome: success

Preference signals:
- 用户明确要求“确保每个指标key的动态统计是独立事物，一个事物失败不要影响其他统计指标的事物统计和提交更新” -> 类似定时汇总任务应优先按指标/key划分事务边界，并保留失败隔离与可观测日志。
- 用户要求“直接提交推送” -> 完成并验证后可直接提交推送，不必额外等待确认。

Key steps:
- 为 `NanjingJianyeDashboardDynamicServiceImpl` 注入 `PlatformTransactionManager`。
- 移除整批 `@Transactional`，将 10 个动态 key 分别通过 `TransactionTemplate` + `PROPAGATION_REQUIRES_NEW` 执行：查询、计算、序列化、落库均属于当前 key 的事务。
- 单 key 失败捕获并记录错误，继续处理后续 key；新增逐 key 成功日志。
- 将机构列表构建拆入独立 key 计算，避免 nursery 与 kindergarten 共享同一失败事务。
- 在 `DataSchedule.updateNanjingDailyDynamicData()` 中对南京各统计模块增加异常隔离，前置模块失败不再阻断建邺驾驶舱 writer。
- 添加本地忽略的回归测试，模拟首个 `biz_*` 查询超时，验证 1 个事务回滚、其余 9 个事务提交。

验证证据:
- `mvn -q -Dtest=NanjingJianyeDashboardDynamicServiceImplTest,NanjingJianyeDashboardDynamicWriterContractTest test` 通过。
- `mvn -q -DskipTests compile` 通过。
- `git diff --check` 通过。
- 测试验证：超时 key 回滚，后续 key 继续执行并生成 `stateCorp=9`。
- 提交并推送成功：`f642d84e fix(nanjing): 隔离建邺动态指标统计事务`，远端 `develop` 已更新。

Failures and how to do differently:
- 首次回归测试在旧代码上按预期直接抛出 `query timeout`，证明原问题是整批流程被异常中断；随后改为独立事务并转绿。
- 普通 `git fetch` 因 `.git/FETCH_HEAD` 权限失败，使用授权 Git 权限重试后成功；未来遇到同类沙箱权限错误可直接请求提升权限。

References:
- `src/main/java/com/iktapp/skc/datasum/service/nanjing/impl/NanjingJianyeDashboardDynamicServiceImpl.java`
- `src/main/java/com/iktapp/skc/datasum/schedule/nbbl/DataSchedule.java`
- Commit: `f642d84e`
- Push: `git push origin develop`

