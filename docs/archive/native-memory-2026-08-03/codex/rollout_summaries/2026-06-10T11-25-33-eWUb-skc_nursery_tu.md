thread_id: 019eb147-cc27-75f2-8a8f-429830a72983
updated_at: 2026-07-31T06:22:53+00:00
rollout_path: /Users/dalwin/.codex/sessions/2026/06/10/rollout-2026-06-10T19-25-33-019eb147-cc27-75f2-8a8f-429830a72983.jsonl
cwd: /Users/dalwin/Library/IdeaProject/ZhiJin/SunkidCloud/skcservers/skcnursery/skc-nursery
git_branch: release/syzh-20260416

# 诊断两位善于在杭托育券用户的婴幼儿信息查询异常，并更新排查报告

Rollout context: 在 skc-nursery 中结合代码、诊断日志和“善于在杭正式查询”生产库只读数据，分析两位用户的“无权查询/出生日期为空”问题，并将结论写入 `/Users/dalwin/Downloads/善于在杭托育券-婴幼儿出生日期为空问题排查报告.md`。

## Task 1: 定位杨帆、杨婷的异常根因

Outcome: success

Preference signals:
- 用户要求“把这两位的错误问题原因也加入到…排查报告.md”，并特别要求杨婷“列出前端调用的哪个接口传入了错误的参数” -> 类似排查应不仅给口头结论，还要同步沉淀到指定报告，并明确接口、参数名、错误语义和正确值来源。

Key steps:
- 阅读 `NurseryCouponDrServiceImpl`、`NurseryCouponServiceImpl` 及 H5 controller，确认 `/getInfantOwnInfo` 会先执行 `validateMobileInfantCaller`，再查询儿童详情。
- 确认家庭关系查询会读取缓存；空数组缓存也会被视为命中并直接返回，不再调用东软接口。
- 使用 `/Users/dalwin/Library/ConfigFile/db/dbq '善于在杭正式查询'` 对 `skcity` schema 做只读核验，字段结构确认了 `user`、`zheliban_user`、`user_child` 的关系。
- 生产库结果：杨帆 `user.id=5839210` 有效绑定儿童杨梓易；杨婷 `user.id=3196730` 有效绑定儿童姚钰晨、姚钰璐。证件号只以首尾脱敏形式核对。

Reusable knowledge:
- 杨帆：日志命中 `dr-family-cache cacheHit=true, result=[]`，但正式库存在其与杨梓易的有效 `user_child` 关系；因此是空家庭关系缓存导致的越权误判，不是真实无权访问。需清理家庭关系/儿童列表缓存后重新调用，并确认出现 `dr-family-request`、`dr-family-raw-response`、`dr-family-parsed-result`。
- 杨婷：调用 `GET /app/nursery/coupon/getInfantOwnInfo` 时，前端把家长证件号传给了儿童参数 `infantIdCard`。后端接口语义要求儿童证件号；应传用户选择/录入的儿童证件号，不能传 `guardianIdCard` 或登录用户证件号。
- `getInfantOwnInfoDetail()` 在 `NurseryCouponDrServiceImpl:204` 调用 `validateMobileInfantCaller()`；校验逻辑位于约 `:1164-1192`，空关系和目标儿童不匹配最终都抛出“当前用户无权查询该证件号信息”，前端提示因此不能直接等同于真实越权。

Failures and how to do differently:
- 一次生产 SQL 因 UNION 列类型不一致失败：`ERROR: UNION types boolean and text cannot be matched`。后续改用分开的 SELECT/EXISTS 查询完成核对。
- 初始脱敏 SQL 对 PostgreSQL 字段表现异常（输出 `t`），后续通过字段类型/长度核查和按首尾字符查询修正，避免把异常脱敏输出当成业务数据。

References:
- `/Users/dalwin/Library/ConfigFile/db/dbq '善于在杭正式查询'`
- `src/main/java/com/iktapp/skc/nursery/service/nurserycoupon/NurseryCouponDrServiceImpl.java:204`
- `src/main/java/com/iktapp/skc/nursery/service/nurserycoupon/NurseryCouponDrServiceImpl.java:1164`
- `GET /app/nursery/coupon/getInfantOwnInfo`
- 关键日志：`stage=dr-family-cache cacheHit=true, result=[]`

## Task 2: 更新排查报告

Outcome: success

Preference signals:
- 用户要求报告中“写清楚”杨婷前端调用的具体接口和错误参数 -> 报告应按独立案例记录日志证据、数据库证据、直接原因、根因分类、正确调用方式和前端修正要求。

Key steps:
- 读取原报告结构后，先复制到 `/private/tmp` 修改，避免直接编辑 Downloads 文件。
- 在汇总表新增杨帆、杨婷两行；新增“申请人杨帆”“申请人杨婷”章节；同步扩展统一判断口径与章节编号。
- 将更新后的文件复制回 `/Users/dalwin/Downloads/善于在杭托育券-婴幼儿出生日期为空问题排查报告.md`。
- 最终校验报告包含目标接口、杨帆空缓存结论、杨婷 `infantIdCard` 错参结论；文件共 345 行。

Reusable knowledge:
- 报告最终包含两类“无权查询”区分：真实关系存在但空缓存误判；前端把家长证件号作为儿童证件号传入。
- 杨婷前端修正检查点包括表单绑定、页面初始化、编辑回显、切换儿童时不得用 `guardianIdCard` 覆盖 `infantIdCard`，并需用两名儿童证件号回归验证 `infantBirthday`。

References:
- `/Users/dalwin/Downloads/善于在杭托育券-婴幼儿出生日期为空问题排查报告.md`
- 校验命中：`GET /app/nursery/coupon/getInfantOwnInfo`、`infantIdCard=3306**********5024`、`空家庭关系缓存`
