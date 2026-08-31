thread_id: 019fad83-096c-79b1-a919-d38bc7c8c8be
updated_at: 2026-07-30T01:26:52+00:00
rollout_path: /Users/dalwin/.codex/sessions/2026/07/29/rollout-2026-07-29T18-54-33-019fad83-096c-79b1-a919-d38bc7c8c8be.jsonl
cwd: /Users/dalwin/Library/IdeaProject/WaveFlow/wavetrans
git_branch: develop

# 两轮嘉善检验报告同步代码审查均完成，修复提交仍不可合入

Rollout context: 在 `/Users/dalwin/Library/IdeaProject/WaveFlow/wavetrans` 对 commit `2d0e722` 及其修复提交 `d82aafec` 进行中文结构化代码审查，报告落盘到被全局 Git ignore 的 `docs/commit-review/` 目录。

## Task 1: 审查新增嘉善体检报告同步提交 2d0e722

Outcome: success

Preference signals:
- 用户直接要求“对这个 commit 进行一下代码审查”，并接受独立、批判、带文件行号和验证证据的审查形式 -> 后续类似 review 应优先给出风险排序、具体定位和验证结果，而不是泛泛总结。

Key steps:
- 将单 commit 转换为 `489ae43..2d0e722`，确认提交意图为“feat: 增加嘉善体检报告同步”。
- 识别 8 个文件、`+551/-11` 的跨 MySQL、Oracle、Kafka 链路改动，派发独立 reviewer 深追下游 activity 消费契约。
- 使用 JDK 8、指定 Maven settings 和本地仓库编译；6 个模块编译通过。
- 运行 `JiaShanLabResultSyncServiceTest`，3/3 通过；`git diff --check` 通过。

Reusable knowledge:
- 本仓库 Java/Maven 验证必须使用 JDK 8、本地仓库 `/Users/dalwin/Library/Repository` 和 settings `/Users/dalwin/Library/ConfigFile/maven/saas/settings.xml`。
- 首轮确认的 3 个严重问题：部门配置为空时候选 SQL fail-open 导致跨租户医疗数据误关联；按身份证+预约日前后 3 天会把相邻体检报告串到同一 `pauId`；下游按 `pauId` 写完成标记会让迟到报告永久漏同步。
- 另外 2 个重要问题：未命中报告时重复跨库 N+1；新增报告同步链路完全没有测试覆盖。

Failures and how to do differently:
- Maven 首次运行因受限环境无法写本地仓库失败，提升权限后成功；未来直接使用允许写入本地 Maven 仓库的方式运行。
- 报告目录被全局规则 `/Users/dalwin/.config/git/ignore-ideaproject` 忽略，不能用 `git status` 判断报告是否生成，应直接检查文件路径。

References:
- 首轮报告：`docs/commit-review/2026-07/29/2d0e722-review.md`
- 编译命令：`export JAVA_HOME=/Library/Java/JavaVirtualMachines/jdk-1.8.jdk/Contents/Home && mvn -s /Users/dalwin/Library/ConfigFile/maven/saas/settings.xml -Dmaven.repo.local=/Users/dalwin/Library/Repository -pl wavetrans-job -am -DskipTests compile`
- 回归命令：`mvn -s /Users/dalwin/Library/ConfigFile/maven/saas/settings.xml -Dmaven.repo.local=/Users/dalwin/Library/Repository -pl wavetrans-job -am -Dtest=JiaShanLabResultSyncServiceTest -Dsurefire.failIfNoSpecifiedTests=false test`

## Task 2: 第二轮审查修复提交 d82aafec

Outcome: success

Preference signals:
- 用户明确要求“根据最新的代码，继续完成第二轮代码审查”，并指定原审查报告作为基线 -> 后续修复审查应逐条复核旧问题是否关闭，同时重新检查修复引入的风险。
- 审查过程强调“最新代码”、真实下游行为和证据驱动，而非仅看编译是否通过 -> 必须核对调用链、幂等语义和边界场景。

Key steps:
- 确认 `d82aafec` 是单独修复提交，父提交为 `4febbe2`，变更范围 3 文件、`+197/-28`。
- 核对修复：部门 ID 空配置改为 Java fail-fast 和 SQL fail-closed；增加近预约归属裁决；删除报告同步的 `convert_history` 排除；增加近 30 天候选限制和严格分组。
- 复核下游 commit `8b2de706`，确认 activity 按 `pauId + reportKey`、`reportId + itemKey` 幂等更新，重复消息不会产生重复业务行，但仍有重复查询和投递成本。
- 6 个 Maven 模块编译通过，旧嘉善测试 3/3 通过，`git diff --check` 通过；修复提交没有新增测试。

Reusable knowledge:
- 第二轮关闭了跨租户 fail-open，但仍发现 1 个严重问题：候选预约按当前预约日期 ±3 天查询，导致同一报告在不同预约轮次面对不同候选集，可能分别归属两个 `pauId`；`filterRowsOwnedByCandidate` 在预约查询为空时回退当前候选单例，会把查询失败误当成唯一归属。
- 仍有 3 个重要问题：固定近 30 天候选窗口会漏掉第 31 天后补出/更正的报告；删除完成过滤后每轮重复 Oracle/MySQL 查询并发送 Kafka；关键归属、严格分组、等距歧义、30 天边界和重复投递仍无测试。
- 第二轮结论仍为“不可合入”，问题统计为 🔴 1、🟡 3、🟢 0；上一轮 5 项为 1 项已关闭、3 项部分关闭、1 项未关闭。

Failures and how to do differently:
- 仅通过编译和旧链路测试不足以证明修复正确；新服务没有任何测试，必须补充行为测试和 MySQL mapper 集成测试。
- 用固定 30 天水位替代完成标记只能缓解历史重复扫描，不能解决超窗迟到报告；应使用源端更新时间/稳定源键，或实现周期性回扫和超窗监控。
- 归属裁决必须对每条报告日期使用稳定、统一的候选集合，不能按当前候选预约分别查询不同 ±3 天窗口，也不能在候选查询为空时回退当前预约。

References:
- 第二轮报告：`docs/commit-review/2026-07/30/d82aafe-review.md`
- 修复提交：`d82aafec461a6ac35ff25baae4308a3c95038f8e`
- 关键代码：`wavetrans-job/src/main/java/com/iktapp/wavetrans/job/data/jiashan/lab/report/service/JiaShanLabReportSyncService.java:87-102, 152-170, 234-335`
- 关键 SQL：`wavetrans-job/src/main/resources/mapper/jiashan/JiaShanLabCandidateMapper.xml:94-153`
