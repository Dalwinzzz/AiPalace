# Phase 3 Summary & Workflow 重构 Spec

## 1. 阶段目标

本阶段重构内容沉淀与审核链路，覆盖：

- 活动点滴
- 台账
- 活动总结
- 观察与评价表
- 活动审核
- 总结审核

## 2. 全局强制约束

1. controller 层所有接口的入参、出参与原先保持一致，重构完成后必须做回归校验。
2. 编码前必须重新扫描 `CourseOfflineService`、`ActivityWorkflowServiceImpl`、相关 summary/workflow Mapper 与 XML，确认本 spec 仍然准确；如不一致，应以“内容模型收口 + 工作流边界收口”为核心目标调整方案。
3. 所有新增或重构的方法必须补一句话 JavaDoc；方法内部需增加适量行级注释，解释内容模型选择、审核状态回写、项目差异与兼容处理。

## 3. 本阶段范围

### 内容模型

- `updateRecord`
- `getRecordByCourseId`
- `getSummarize`
- `getSummarizeList`
- `updateSummarize`
- `getSummary`
- `saveSummary`
- `getNurturActivRecode`
- `getNurturActivRecodeAll`
- `getEvaluationForm`
- `batchGetEvaluationForm`
- `saveEvaluationForm`

### 工作流模型

- `startActivityAuditWorkflow`
- `cancelActivityAudit`
- `startSummaryAuditWorkflow`
- `checkCourse`
- `auditCourse`
- `getWorkFlowList`

## 4. 目标类

- `template/CourseOfflineSummaryTemplate`
- `template/CourseOfflineWorkflowTemplate`
- `support/CourseOfflineSummaryContext`
- `support/CourseOfflineWorkflowContext`
- `strategy/project/ProjectSummaryStrategy`
- `strategy/project/ProjectWorkflowStrategy`
- `strategy/coursetype/CourseTypeSummaryStrategy`
- `gateway/CourseOfflineSummaryGateway`
- `gateway/CourseOfflineWorkflowGateway`

## 5. 要做什么

- 把 `record / summarize / summary / evaluationForm` 从大 service 中拆成有边界的内容模型流程。
- 把养育记录查询 `getNurturActivRecode / getNurturActivRecodeAll` 一并收口到 `CourseOfflineSummaryTemplate`，统一回填家庭数、月龄分布、家长评价和活动点滴。
- 把活动审核与总结审核从 `ActivityWorkflowServiceImpl` 中拆成统一模板流程。
- 让工作流实例查询、状态回写、审核记录补写边界清晰。

## 6. 不要做什么

- 不要把 appoint 域逻辑继续带进 summary/workflow 模板。
- 不要让内容模板直接操作 workflow 细节。
- 不要把所有内容模型强行抽成一个完全统一的表单对象。

## 7. 阶段依赖

- 依赖 Query/Save/appoint 的主链骨架已经稳定。

## 8. 验收标准

1. `record / summarize / summary / evaluationForm` 的流程边界清晰。
2. 养育记录查询不再散落在 `CourseOfflineService + CourseOfflineAppointService` 之间，`@DataScope` 已下沉到 `CourseOfflineSummaryTemplate` 的批量查询方法。
3. 工作流主流程不再散落在多个 service 中。
4. controller 接口保持兼容。
5. 总结保存、审核发起、审核通过/驳回的行为回归一致。
