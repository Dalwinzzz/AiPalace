鄂尔多斯普惠性托育认定申请(EerduosiCheapRecognitionSubsidyServiceImpl；提交链路 submit→saveSubsidy(fillSyncInfo回填classPriceInfos)→validate=ValidationUtils.validateEntity(JSR303)+validateConfigInfo(金额上限))：班级价格金额(全日托fully/半日托half/计时托hourly)必须按机构 Nursery.serverScope(逗号分隔字符串，1全日/2半日/3计时/4临时；NurseryConstants.ServerScope.FULLY/HALF/HOURLY)动态门控——机构无该服务类型则金额回填null且不校验。

**Why:** 只有全日托的机构(serverScope="1")，其 nursery_charge 的 half/js 列与 nursery.money_half/money_hour 全为null，回填出的 hourly/half 就是null。

**How to apply:**
- ClassPriceInfoDTO 的 fully/half/hourly **不要挂** @NotNull(groups=Eerduosi)——曾误报"计时托金额不能为空"卡住提交。金额必填与否由 service 按 serverScope 判断。
- buildClassPriceInfos 按 serverScope.contains(...) 门控回填，无关类型置null。
- validateConfigInfo 上限比较要 null 安全：`申请金额!=null && 配置上限!=null && >` 才拦截(否则 null 拆箱 NPE，且会判断无关类型)。
- **参照范例**：同类逻辑 HangZhouCheapRecognitionSubsidyServiceImpl 已正确实现，鄂尔多斯照抄即可。多地区策略类(杭州/伊犁/鄂尔多斯/南京)共用 ClassPriceInfoDTO，分组注解勿乱加。

**附带修的坑：** validateConfigInfo 的 public/nonPublic 两分支——SubsidyConditionSettingDTO 有 publicTable/nonPublicTable(公办/非公办收费金额)、publicCareType/nonPublicCareType(公办/非公办机构类型)两套独立字段。曾有复制粘贴bug把 nonPublicCareType 错解析成 getPublicCareType()、nonPublic分支错用 getPublicTable()，导致非公办机构跳过或用错上限表，已修。

落地：commit 85335d29d `fix(eeds)`(本地develop，尚未push远程develop)；已 cherry-pick 到 release/eeds-20260416 生成 b20fc6ca0 并 push 到远程 eeds-20260416 部署分支(cherry-pick零冲突+JDK8编译通过)。注意 release 分支经 995e95cfe classLimitList 重构，与develop分叉但该fix仍干净合入。同工作区当时另有 Codex 在改的 InstitutionService.java(杭州存量班型回显)非本次范围。相关 [[nursery-eerduosi-attribute-info]] [[nursery-eerduosi-portrait-scope-zero-bug]] [[nursery-hangzhou-type2-dynamic-info]]。
