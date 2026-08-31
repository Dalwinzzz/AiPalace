体检"可预约时间"链路：管理端配置 cron 规则 → `physical_appoint_time_rule`（`CronModule.createCronExpression`，周=6段 `s m h ? * dow`，自定义指定一次=7段含年）→ `getAppointTime` 把规则展开成具体槽位写 `physical_appoint_time` → 移动端 `getAppointTimeList(paId, now)` 按 `[now, now+rule.max_days]` 窗口读。

**核心设计模型（非显而易见，靠跑 Hutool 复现才理清）：**
- 槽位**不是实时算**的，是**预先物化**的行。两个写入时机：① 保存配置 `createAppointTimeRule` 按 `[now, now+maxDays]` 整窗生成；② 每日补位任务 `assemblyAppointTime`（`RemoteScheduleController#/assemblyAppointTime`，外部 xxl-job 类调度每日调）用 `getAppointTime(rule, forceStartDays=maxDays)` 只补"地平线那天 now+maxDays"。靠每天滚动一格维持窗口。
- `maxDays`（可预约最大天数，≤15）= **可预约地平线**，是产品设计的预约范围上限，不是 bug。周期规则（每周五等）天然只显示 maxDays 内的若干次——maxDays 配小（如7/3）就只剩 1 个周五，属设计内。
- Hutool `cn.hutool.cron.pattern.CronPatternUtil.matchedDates(cron,start,end,count,false)`：dow 约定 **0周日~6周六，5=周五**，与前端 `convertChineseNumber`（5→"周五"）一致，**无 Quartz 错位**；7段表达式**第7位年份不解析不匹配**（只按 day+month 匹配任意年）；`count` 是返回数量上限，按分钟步进扫 `[start,end)`，要求 start<end。

**2026-06 修复的两处缺陷（已全局生效，非南京专属，见 fix(physical) 提交）：**
1. 自定义"指定一次"日期被同一 `[now,now+maxDays]` 窗口静默丢弃（"配3天只生成1天"）→ 改为 type==1 时窗口终点取该指定日期当天23:59，不受 maxDays 限制；并让补位任务跳过自定义（`isCustom && forceStartDays!=null → return null`）避免每日重复插入。
2. 补位任务窗口起点是 `now+maxDays` 的**当前时分**未归零 → 漏掉早于任务运行时刻的槽位（如任务14:30跑、09:00槽被丢）且永不补，形成永久空洞。改为 `DateUtils.truncate(now, Calendar.DATE)` 归零到00:00。

代码：`PhysicalExaminationServiceImpl#getAppointTime`（skc-activity）。构建见 [[skcactivity-build]]，南京体检整体方向见 [[nanjing-physical-exam-legacy-adapt]]。
