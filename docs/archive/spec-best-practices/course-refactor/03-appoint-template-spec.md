# Phase 2 Appoint Template 重构 Spec

## 1. 阶段目标

本阶段重构预约域，把当前散落在 `CourseOfflineService` 与 `CourseOfflineAppointService` 的预约、取消、签到、评价、核销等主流程迁入统一模板。

## 2. 全局强制约束

1. controller 层所有接口的入参、出参与原先保持一致，重构完成后必须做回归校验。
2. 编码前必须重新扫描 `CourseOfflineService`、`CourseOfflineAppointService`、相关 DAO/XML，确认本 spec 仍然准确；若不一致，应以“预约主流程收口 + 状态流转可维护”为核心目标调整方案。
3. 所有新增或重构的方法必须补一句话 JavaDoc；方法内部需增加适量行级注释，解释兼容入口、预约前置校验、状态流转、项目差异和后置副作用。

## 3. 本阶段范围

### 迁入预约模板的典型方法

- `appoint`
- `appointCheck`
- `cancelAppoint`
- `sign`
- `signWithQr`
- `evaluate`
- `verify`
- `verifyInfo`
- `getMyAppointRecord`
- `getAppointDetailByAppointId`

## 4. 目标类

- `template/CourseOfflineAppointTemplate`
- `support/CourseOfflineAppointContext`
- `support/CourseOfflineAppointScene`
- `strategy/project/ProjectAppointStrategy`
- `strategy/coursetype/CourseTypeAppointStrategy`
- `strategy/rule/AppointRuleStrategy`
- `gateway/CourseOfflineAppointGateway`

## 5. 设计边界

### 要做什么

- 保持 `CourseOfflineService.appoint(...)` 与 `CourseOfflineAppointService` 的外部方法签名不变。
- 统一预约前校验、状态流转、项目差异、课型差异。
- 历史兼容逻辑如 `judgeIsLimitAppoint(...)` 可先保留调用顺序，但规则实现逐步下沉到预约规则策略中。

### 不要做什么

- 不要在本阶段改 controller。
- 不要把预约域和 workflow、summary 同时混迁。
- 不要让模板继续直接拼多个 mapper/dao。

## 6. 阶段依赖

- 依赖 Query/Save 模板与 `CourseOfflineGateway` 基础结构已稳定。
- `CourseOfflineService` 已具备模板化兼容入口风格。

## 7. 验收标准

1. 预约链路主流程已从 `CourseOfflineService`/`CourseOfflineAppointService` 大方法中抽出。
2. 状态流转与项目差异边界清晰。
3. controller 接口保持兼容。
4. 关键链路具备回归校验：预约、取消、签到、评价、核销。
