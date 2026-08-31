善育在杭(projectName=hangzhou) 幼儿园托育部(nurseryType=2) 机构信息表单迭代（2026-06-29 落地，commit c32ceab3f）。

**字段落库口径**：机构专属/移动端配置字段（咨询电话 consultPhone、预约入托展示 showAppointEntry）**存进 `nursery_extra_info.dynamic_info`（JSON，typeHandler=ObjectJsonTypeHandler）**，不新增 DB 列——这是本项目避免维护 DDL 的既定做法。读写经 `NurseryDynamicInfoUtil`（merge*/get* 方法，参照南京 specialService/园长字段）；DTO 顶层暴露字段、Util 在 dynamic_info 与顶层间转换。showAppointEntry 默认否(0)。

**机构信息表单全链路**：`NurseryAuditInfoAddDto`(录入/校验 checkParam) → `nursery_audit_info` 快照(BeanUtil.copyProperties) + 工作流 JSON → 审核通过 `NurseryService.saveNurseryExtraInfoByAudit`(copyProperties + apply*OnApprove 从 submitContent 合并 dynamic_info) → `nursery_extra_info`。审核详情回显走工作流 JSON 的 submitContent overlay，不依赖 audit 列。

**校验门控**：`isHangzhouType2 = PROJECT_NAME_HANGZHOU.equals(projectName) && nurseryType==2`；该条件放开食品/配餐必填，新字段不强校验（交前端）。

**Apifox**：saas 项目(6776425) → nursery 模块(7062226) → 文件夹「托育机构」(folder 86934951) 收录机构信息表单 7 个端点：/info/audit、/info/storage(POST+GET)、/audit/auditDetail、/info/getExtraInfo、/info/detail、/institution/detail/nursery。团队对该模块选择性收录，改字段时记得同步这里。

相关：[[urgent-piece-cherrypick-to-develop]]
