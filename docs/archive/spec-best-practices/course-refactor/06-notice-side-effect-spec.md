# Phase 5 Notice Side Effect 重构 Spec

## 1. 阶段目标

本阶段重构活动域剩余的通知副作用，把当前散落在 `CourseOfflineService` 与 `CourseOfflineSaveTemplate` 的浙里办定时提醒、上架参与提醒统一收口到轻量通知模板中。

## 2. 全局强制约束

1. controller 层所有接口的入参、出参与原先保持一致，重构完成后必须做回归校验。
2. 编码前必须重新扫描 `CourseOfflineService`、`CourseOfflineSaveTemplate`、相关 mapper/xml，确认本 spec 仍然准确；若不一致，应以“浙里办通知副作用收口 + 不扩大改造范围”为核心目标调整方案。
3. 所有新增或重构的方法必须补一句话 JavaDoc；方法内部需增加适量行级注释，说明兼容入口、通知筛选口径、容错处理和模板边界。

## 3. 本阶段范围

### 迁入通知模板的典型方法

- `sendSignMsg`
- `sendEvaluateMsg`
- `sendParticipateMsg`
- `sendZLBMessage`

### 本阶段明确不动

- `noticeAppoint`
- `noticeStart`
- 短信与站内信发送逻辑

## 4. 目标类

- `template/CourseOfflineNoticeTemplate`
- `gateway/CourseOfflineNoticeGateway`

## 5. 设计边界

### 要做什么

- 保持 `CourseOfflineService.sendSignMsg()` 与 `sendEvaluateMsg()` 的外部方法签名不变。
- 把 `CourseOfflineSaveTemplate` 中的活动上架参与提醒改为委托通知模板。
- 统一 `sendZLBMessage(...)` 的消息装配和容错行为，避免 service 与 save template 双份维护。
- 仅收口浙里办通知相关 mapper 查询与消息发送，不顺手扩张到短信、站内信和工作流通知。

### 不要做什么

- 不要修改 controller。
- 不要把 `noticeAppoint / noticeStart` 一起迁进本阶段。
- 不要把通知模板扩张成新的大而全消息中心。
- 不要让模板继续直接散落操作多个 mapper 与消息服务。

## 6. 阶段依赖

- 依赖 Query/Save/Appoint/Statistics/Sync 模板基础结构已稳定。
- `CourseOfflineService` 已具备模板化兼容入口风格。

## 7. 验收标准

1. `CourseOfflineService` 不再直接依赖浙里办消息服务和预约表查询来发送定时提醒。
2. `CourseOfflineSaveTemplate` 不再维护重复的 `sendParticipateMsg/sendZLBMessage` 实现。
3. `sendSignMsg / sendEvaluateMsg / sendParticipateMsg` 已收口到统一通知模板。
4. controller 接口保持兼容，编译与基础回归校验通过。
