# Course Offline 重构 Spec 索引

本目录用于沉淀 `course_offline` 活动域重构的分阶段执行 spec，供后续按阶段或按子域分派多 agent 并行实施。

## 文档索引

- [00-refactor-overview-spec.md](./00-refactor-overview-spec.md)
  活动域重构总览、分层边界、类图、迁移顺序、全局硬约束。
- [01-query-template-spec.md](./01-query-template-spec.md)
  第一阶段 Query 链路重构，重点兼容 `@DataScope`。
- [02-save-template-spec.md](./02-save-template-spec.md)
  第一阶段 Save 链路重构，重点收口 `save / updateOfflineState / deleteOffline / alterPosterImg / editSignTime`。
- [03-appoint-template-spec.md](./03-appoint-template-spec.md)
  第二阶段预约域重构，覆盖预约、取消、签到、评价、核销等链路。
- [04-summary-workflow-spec.md](./04-summary-workflow-spec.md)
  第三阶段总结与工作流重构，覆盖点滴、台账、总结、观察表、审核。
- [05-statistics-sync-spec.md](./05-statistics-sync-spec.md)
  第四阶段统计、导出、同步链路重构。
- [06-notice-side-effect-spec.md](./06-notice-side-effect-spec.md)
  第五阶段活动通知副作用收口，覆盖浙里办定时提醒与上架参与提醒。

## 使用顺序

建议执行顺序如下：

1. 先阅读 [00-refactor-overview-spec.md](./00-refactor-overview-spec.md)，确认总边界与公共约束。
2. 第一阶段优先执行 [01-query-template-spec.md](./01-query-template-spec.md)。
3. Query 稳定后执行 [02-save-template-spec.md](./02-save-template-spec.md)。
4. 在 Query/Save 骨架稳定后，再进入 [03-appoint-template-spec.md](./03-appoint-template-spec.md)。
5. 然后进入 [04-summary-workflow-spec.md](./04-summary-workflow-spec.md)。
6. 最后处理 [05-statistics-sync-spec.md](./05-statistics-sync-spec.md)。
7. 若仍有通知副作用散落，再执行 [06-notice-side-effect-spec.md](./06-notice-side-effect-spec.md)。

## 并发执行建议

- `00` 为所有后续阶段的前置，不建议并发。
- `01` 与 `02` 都会触达 `CourseOfflineService`，建议串行，先 `01` 后 `02`。
- `03` 依赖 `01/02` 的基础结构稳定后再执行。
- `04` 依赖 `02/03` 完成后再执行。
- `05` 依赖 `01/04` 的查询与内容模型边界稳定后再执行。
- `06` 依赖 `02/03` 稳定后再执行，避免通知模板与保存/预约模板边界反复调整。

## 所有阶段统一强制约束

1. controller 层所有接口的入参、出参与原先保持一致，重构完成后必须做回归校验。
2. 每个阶段真正开始编码前，必须重新扫描当前分支代码，重新校验 spec 与代码现实是否一致；如果不一致，应以完成该阶段核心目标为第一优先级，允许在不破坏总边界的前提下调整实现方案。
3. 所有新增或重构的方法都必须补一句话 JavaDoc；方法内部需要增加适量行级注释，说明关键流程、兼容处理点、策略分发点和易错分支，提升代码审查效率。
