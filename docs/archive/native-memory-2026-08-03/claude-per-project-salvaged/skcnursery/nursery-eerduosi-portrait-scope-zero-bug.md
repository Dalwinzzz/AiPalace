鄂尔多斯运维反馈「机构画像总托位数=0」（乌兰镇托育照护服务中心 nursery.id=111824，2026-07-03 排查，基准分支 eeds-20260416）。

**根因**：机构把编班类型从 type3(托大班) 改成 type4(混龄班) 后，`NurseryClassDisplaySupport.resolveOrderedTypes`(:518) 把 `getPassedAuditSnapshotOrder` 返回的「最近审核通过快照班型顺序」当成**班型白名单/过滤集合**；`buildOrderedClassLimits`(:497) 只遍历 orderedTypes 输出，漏掉正式表里实际有 200 托位的 type4，托位求和=0。保护缺口在 :565（只防「快照有、正式表无」，没防「正式表有、快照无」）。

**双重危害**：同一 `buildFormalClassLimitSnapshot` 被两条路径依赖 —— ① 审核通过时 `refreshNurseryClassSummary` 回填主表 `nursery.scope`（写成0，**持久错误**，至今0）；② `/info/detail` 画像读时兜底 `fillClassLimitFromDb`。画像因最新快照已是 type4 已「自愈」=200，但主表 scope=0 持久，凡直接读主表 scope 的接口（如工作台 `/info/workbench` → `getWorkbenchVO`）仍显示0。

**修复（已实现，2026-07-03，未 push）**：把 `resolveOrderedTypes` 的顺序合并抽成纯函数 `computeOrderedTypes(snapshotOrder, availableTypes, classNumMap, classScopeMap)` —— 只保留有值班型(num>0 或 scope>0)、按快照顺序排序、补齐未覆盖班型，杜绝漏项与「审核补0的占位空班型」污染 class_types，全空时兜底回退全集。配 4 个 JUnit5 单测(TDD 红→绿)。commit `0a6ac6a3`(eeds-20260416, worktree 6308) 已 cherry-pick 到 develop(`8d6cfeb75`, worktree 3cdf, 基于 origin/develop 最新)。develop 主线**同样有此缺陷且启用项目更多**(比 eeds 多济南)，故一并修。**存量数据**：受影响 4 家(乌兰镇 111824 scope 0→200、乌审旗文苑 111685 漏 type4、杭锦旗塔然高勒 111765 主表错记 type4 实为 type3、测试机构 111950)。回填 SQL 已产出(2026-07-03，commit `41023dcf9`，worktree 分支 `claude/fix-鄂尔多斯存量托位回填/20260703_v1.0.0` 的 `docs/problem/20260703-鄂尔多斯存量托位回填.sql`)——按正式限制表(state=1 有值班型)重算 scope/class_types/class_num/class_scope 四字段，含预演+事务+校验三步，**待 DBA 人工执行**(dbq 只读，AI 不写生产库)。修复代码 push 情况：release/eeds-20260416 已 push；develop 由用户手动 push。编译须用 JDK8 见 [[skcnursery-build-jdk8-lombok]]。

**Why**：这是时序/一致性缺陷，机构改编班类型才触发，个案会「自愈」但缺陷持续，任何机构再改编班都会复发。
**How to apply**：排查详情见仓库 docs/problem/20260703-鄂尔多斯机构画像总托位数为0.md。查库用 [[dbq-eerduosi-query-skcproddb-skcity]]。与 [[nursery-eerduosi-attribute-info]] 同属鄂尔多斯机构信息链路。
