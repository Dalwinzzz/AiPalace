查鄂尔多斯生产数据：`dbq 鄂尔多斯-正式 "SELECT ... FROM skcity.<表> WHERE ..."`。

- 生产业务库是 **`skcproddb`**，业务表在 **`skcity`** 模式（注意不是 skccity），查询必须带 schema 前缀，如 `skcity.nursery`、`skcity.nursery_class_scope_limit`、`skcity.work_flow_service_info`。
- **坑**：dbq 实例默认曾连 `skctestdb`（测试库），且账号 `skcproduser` 在 skctestdb 对 skcity 无 USAGE 权限；已在另一会话给 dbq 加 `DBNAME_OVERRIDE` 让「鄂尔多斯-正式」连 skcproddb 修好。pg/kingbase 一实例=一固定库，`-d`/PGDATABASE 覆盖不了 dbq 写死的库。
- 同服务器(100.122.2.92:54321)还有 frontdb/security/skclogandb 等库；要查别的库需给 dbq 各建实例或加覆盖。

**How to apply**：本项目任何「查鄂尔多斯生产数据辅助排查」都走这条。相关排查见 [[nursery-eerduosi-portrait-scope-zero-bug]]。
