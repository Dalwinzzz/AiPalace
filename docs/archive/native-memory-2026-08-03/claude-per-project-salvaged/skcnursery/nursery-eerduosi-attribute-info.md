鄂尔多斯(projectName=eerduosi) 机构性质信息表单迭代（2026-07-02 回归审查确认 Codex 首版满足需求）。

**表单 = 端点**：原型「机构性质信息」表单（10 字段全必填）对应 `NurseryAttributeInfo` DTO = `POST /audit/saveNurseryAttributeInfo`（NurseryAuditController，区级/市级后台）。**此表单直接持久化到业务表，不走 Activiti 审核工作流**——与机构信息大表单 `POST /info/audit`（NurseryController /info/*，走工作流）相互独立。用户口径原话：「本次字段不走工作流，相关接口直接保存就落库」，但鄂尔多斯整体机构信息修改仍走工作流。

**落库口径**：8 个复用既有列（isHygiene 卫生评价 / areaAttribute 所在区域 / isCheap 是否普惠 / nature 机构性质 / careType 办托性质 / officeUndertake 是否单位办托 / localeAttribute 机构场所性质 / isShutDown 运营状态0正常1暂停），另 2 个专属字段 careUnitName（办托单位名称）、nurseryPilot（是否纳入试点）**存 nursery_extra_info.dynamic_info**（不新增列，套路同 [[nursery-hangzhou-type2-dynamic-info]]，经 NurseryDynamicInfoUtil.mergeEerduosiAttributeInfo/getCareUnitName/getNurseryPilot）。校验集中在 `NurseryService.normalizeAndValidateEerduosiAttributeInfo`（仅 eerduosi 触发，10 项必填+枚举）；careUnitName 仅 officeUndertake=1 时必填、否则清空；isShutDown 空补 0。careType 值集限 {1,2,3,4}（排除 5事业单位/6企业）。回显：getNurseryDetail 把 dynamic_info 两字段提到 Nursery 顶层，走 `GET /audit/detail/{id}`。

**Apifox**（saas 6776425 → nursery 7062226 → 「托育机构」folder 86934951）：本次新建 2 端点——保存 `POST /audit/saveNurseryAttributeInfo`(id 481393675)、回显 `GET /audit/detail/{id}`(id 481395435)。注意该文件夹原有 7 个 `/info/*` 是**工作流大表单**，别混淆。

相关：[[nursery-hangzhou-type2-dynamic-info]]
