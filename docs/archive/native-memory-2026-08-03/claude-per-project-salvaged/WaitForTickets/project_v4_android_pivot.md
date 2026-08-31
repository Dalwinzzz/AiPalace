WaitForTickets 2026-06-10 发生**产品级转向**：从 v3 的「Web 自部署社区抢票系统（Python/FastAPI + React）」彻底转为 **v4「单机 Android 大麦本地抓票 App」**（AutoX.js/AutoJs6 无障碍脚本，纯本地无后端）。

**Why:** v3 Web 在 Phase 5 联调实测撞墙：`document.cookie`/F12 拿不到大麦/淘系 HttpOnly 核心登录 cookie（cookie2/sgcookie/unb），"粘贴 cookie"接入技术上不成立；iframe 嵌大麦被 X-Frame-Options 拦；服务端代理登录是 v2 废弃高封号路线。结论：Web/PC 在大麦移动优先+强反爬现实下走不通，改在用户手机本机用真实登录态脚本级抓票。

**How to apply:**
- **现状**：旧 Web 代码全删，完整保全在 `archive/v3-web` 分支（不是 tag）。main 只剩 `docs/`。v4 设计已落 `docs/superpowers/specs/v4/2026-06-10-android-grab-app-design.md`。
- **v4 关键定位**：仅 Android（放弃 iOS/PC/Web）；纯本地无后端无账号体系；技术栈 AutoX.js/AutoJs6（context7 有 `/aiselp/autox`、`/websites/autoxjs_dayudada`）；配置只三项「演出+场次+价位」（观演人用户预先在大麦填）；核心=盯抢票按钮倒计时切换那帧立即点击；**支付红线延续**=脚本最远点到「跳出到第三方支付页(微信/支付宝)」即停，付款方式选择+支付+密码全留用户。
- **开发前置依赖**：用户将提供大麦 App 抢票流程截图（识别层标定基础，无它无法开发）；需 Android 真机；大麦测试账号。
- **当前阶段**：初版实现已完成并 merge 回 main（merge commit 8f630c2，feat/v4-android-grab 已删）。subagent-driven 执行 13 Task：12 个源码模块（src/ 下 config/core/damai/debug/guard/lifecycle/notify/platform/ui + build_config）+ 10 测试，**纯逻辑 57 单测全绿**（PC `node test/run.js`）。最终审查闭环：发现 hasPaymentKeyword 运行时零调用→已接线，支付红线达成包名+关键词双保险。计划见 `docs/superpowers/plans/2026-06-11-android-grab-app-plan.md`。
- **真机待补（下一步）**：① 开抢瞬间按钮真实文案→校正 selectors.js 的 TRIGGER_TEXTS；② 轮询间隔 sleep(30) 真机调参；③ flow 选档控件遍历细化；④ APK 打包（release 变体）装测试机验证；⑤ notifier.beep 真机改真响铃。需 Android 真机 + 大麦测试账号 + 一张"按钮切换可点"那帧截图。
- 延续 [[feedback_staged_sdlc]]。v3 历史见 [[project_v3_restart]] / [[project_phase5_integration]]。
