2026-06-12 起,产品从"大麦单平台+三项配置"升级为 **多平台(大麦/猫眼/票星球)零配置一键启动**:用户只点一个启动按钮,自己切到票务 App 的开票倒计时页,脚本精确匹配触发按钮文案秒点并走锁单流程,到支付页即停(红线不变)。关联 [[v4-android-pivot]]。

- **自主循环已完结**(2026-06-12,5/5 次执行,cron cbcd6bcb 已删):5 次执行产出 4 个提交 `97e30bd`(核心重构:registry/poller/flow/零配置)→ `f7cffad`(UI 美化+日志人类可读)→ `e6a52e9`(健壮性+票星球包名修正)→ `8c9e917`(审查修复+封包手册 v4.1)。测试 57→100 全绿,project.json 升 0.2.0。进度明细:docs/superpowers/plans/2026-06-12-loop-progress.md。
- **包名已核实**:猫眼 `com.sankuai.movie`、票星球 `com.piaoyou.piaoxingqiu`(⚠️ com.juqitech.niumowang 是摩天轮票务,初版误标已修正,勿回退)。两平台**按钮文案仍待真机标定**(calibrated:false),流程见 docs/superpowers/specs/v4/CALIBRATION-平台标定指引.md(debug 版有 [calib/screen_sample] 采样日志辅助)。
- **下一步(待用户真机)**:① 真机回归(假阳性/卡死修复验证、状态卡片、支付红线);② 猫眼/票星球标定;③ 大麦真实秒杀帧文案校正;④ release 按封包手册第 6 节清单(DEBUG=false 等)。
- 设计文档:docs/superpowers/specs/v4/2026-06-12-multiplatform-zero-config-refactor.md。
