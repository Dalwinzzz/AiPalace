---
name: codeisland-distill
description: CodeIsland 个人蒸馏 fork 的目标、架构决策、回归修复与本机构建约束
metadata: 
  node_type: memory
  type: project
  originSessionId: e9af5012-dc96-4f58-a6f6-a70d112ae9c2
---

`~/Library/CodeRepo/CodeIsland` 是 wxtsky/CodeIsland 的个人蒸馏 fork（Swift macOS 灵动岛 App）。目标：只为 **Claude Code + Codex** 服务的精简监控器。第一版由 Opus 4.8 完成（2026-06-26）；**回归自查与缺口修复由 Fable 5 完成（2026-07-03）**，`swift build -c release` 0 错误 0 警告，**零第三方依赖**（Sparkle/Yams 全摘除）。

**架构核心（通知式，5 项需求全达成）：**
- hooks 集成/角色仅 claude+codex；HookFormat 只剩 .claude/.nested；`SessionSnapshot.supportedSources = {claude, codex}`（其他 source 的事件在 HookServer 边界被丢弃，抵御旧残留 hook）。
- **零决策回传**：主 App 不含任何 `behavior: allow/deny` 响应——handle* 立即回 `{}`；HookServer 超载/hiddenPlugin/autoApprove 分支全部中性化或删除；autoApproveTools 设置+UI 已删。
- 审批/问题只读卡片 + 10s 自动隐藏（`scheduleNoticeAutoHide` + noticeGeneration 防误杀）+ 点击跳转终端。
- hook 事件精简：claude 7 事件、codex 5 事件，全部 timeout 5s（无 PreToolUse/PostToolUse 每次工具调用的 hook 进程开销）。
- 音效默认开启（soundEnabled=true）；SessionStart/Stop/PostToolUseFailure/PermissionRequest/boot 映射保留。
- **升级自清洗**：installClaudeHooks 的 alreadyInstalled 改为"托管足迹精确匹配"（多余托管事件或 timeout 不符即整体重写）；installExternalHooks 先 removeManagedHookEntries 全量剥离再装；isHooksInstalled 同样识别 stray 事件。旧 12 事件配置首启自动清洗。
- Sparkle 摘除（Info.plist SU* keys、UpdateChecker、appcast.xml、build.sh 嵌入/签名段全删）——否则个人版会被 upstream 自动更新覆盖。

**本机构建环境（2026-07-03 起）：** 已装 **Xcode 26.3**（/Applications/Xcode.app，license 已接受），`./build.sh` 可完整出 .app（ad-hoc 签名，无开发者证书）。此前仅 CLT 时只能 `swift build -c release`（debug 因 #Preview 宏失败）。注意：Xcode 26.3 的 codesign 拒绝 entitlements 重复 key——upstream 的 CodeIsland.entitlements 曾有重复 disable-library-validation（已修复为仅保留 apple-events）。

**部署状态（2026-07-03 v2 迭代完成）：** 蒸馏版已装 `/Applications/CodeIsland.app` 并运行；`~/.claude` 7 事件、`~/.codex` 5 事件（全 timeout 5s）。

**v2 迭代（同日五项需求）：**
- 智能抑制修复：`isSessionTabVisible` 末端 fallback 翻转为 `return true`（app 前台+无标签内省=视为在看，ghostty/Claude 桌面端/未知终端不再误弹）；删除不可靠的 ghostty 窗口标题匹配（cc 会改写标题必失配）；`appBundleNames/Sources` 增加 `com.anthropic.claudefordesktop`。
- 音效实时性：根因是 LSUIElement 后台 app 被 **App Nap** 节流（事件积压、面板展开唤醒时集中迸发）→ `beginActivity(.userInitiatedAllowingIdleSystemSleep)` 长持断言 + HookServer NWListener 移到专用 `networkQueue`（不再与主线程 UI 抢队列）。
- 快捷键回迁：GlobalHotKeyManager + ShortcutsPage 恢复，但 ShortcutAction 只留 togglePanel(⌘⇧I)/jumpToTerminal（approve/deny/skip 透传动作永久移除）。
- 集成扩展至 5 工具（同事需求）：+Gemini CLI（nested、ms timeout、--event、BeforeTool→PermissionRequest）、+Google Antigravity（antigravityNamed、~/.gemini/config 标记门控）、+GitHub Copilot CLI。白名单/吉祥物（GeminiView/CopilotView 自 HEAD 恢复）同步。
- **软链 SOT 方案**：自研 hook 配置统一放 `~/.codeisland/hooks/`（现有 copilot.json）；工具侧路径只放 symlink（`~/.copilot/hooks/codeisland.json → SOT`），更新只改一处、卸载删软链；共享型配置(settings.json 类)仍走 JSON 最小 diff 合并。本机实测软链挂载成功。

**规模：** 相对 upstream 净删 ~33600 行；ConfigInstaller 2497→~900 行。

**git 状态：** 改动按用户规范（`<type>(<scope>): <中文主题>`，hook 注入强制）主题化提交至 **`distill` 分支**（v2 九个 + v3 四个 commit）；`main` 与 upstream 对齐便于 diff/同步。remote 仍为 upstream，未 push。README.md（设计铁律/事件表/架构索引）与 CHANGELOG.md（distill-v1/v2/v3 需求→实现迭代史）是后续迭代必读。当前版本 `1.0.28-distill.3`（Info.plist + AppVersion.fallback 同步递增）。

**distill-v4 关键根因（2026-07-03，铁律级）：**
- **Codex 的 PermissionRequest 是决策型 hook**：注册即让 Codex 把审批委托给 hook 并抑制自身 GUI/TUI 弹窗——通知式监控器对 Codex **绝不能注册**该事件（"注册+回 {}"会让审批卡死）。Codex Desktop 的审批感知改由 app-server thread 状态（waitingOnApproval→提示音）承担。
- **app-server `requestUserInput` 是多客户端广播、先答先得**：任何应答（含空答案）都会抢答/作废桌面端弹窗——正确做法是完全不应答，等 `serverRequest/resolved` 撤卡。
- 状态栏图标必须直接加载 bundle AppIcon.icns：`NSWorkspace.icon(forFile:)` 是 Finder 评估图标，ad-hoc 未公证 app 会被打黄色警告角标（spctl assess=rejected）。
- 音效"任务开始"感知靠 UserPromptSubmit 音（默认已开启）；SessionStart 仅会话创建时响一次。音效链路已埋 os_log（subsystem=com.codeisland，"event arrived"/"sound play/skipped/debounced"），排延迟用 `log show --predicate 'subsystem == "com.codeisland"'`。
- **音效"集中响"结案（distill-v5，实测驱动）**：链路零延迟（到达→播放 2~6ms）；真因是事件风暴——① Claude Code 的 SessionStart 在 **resume/compact/clear** 时也触发（payload 原生 `source` 字段区分，仅 startup 播 start 音）；② 桌面端后台 spawn 的 1~2s 瞬时辅助 claude 进程也发 SessionStart；③ SoundManager 按 sound 名做 3s 防抖合并兜底（preview/boot 不受限）。

**distill-v3 关键根因（2026-07-03，谨防复发）：**
- **CG/NSScreen 坐标系混淆**是可见性三 bug 的同一根因：CGWindowList 全局顶左原点 vs NSScreen 底左原点——任何拿 CGWindow bounds 与 NSScreen.frame 比较的代码必须先过 `ScreenDetector.convertFromCGCoordinates`。
- **原生 App 会话（Claude 桌面端）宿主进程跨对话常驻**，"进程存活即会话存活"不成立：清理需靠 lastActivity 静默窗口（native 180s 置 idle / idle 10min 移除），transcript tailer 在真实输出期间会刷新 lastActivity 所以安全。
- 跳转/抑制类映射表有**两份**：`SessionSnapshot.appBundleNames/Sources`（抑制/native判定）与 `TerminalActivator.nativeAppBundles`（跳转）——新增桌面 App 支持时两处都要加（claudefordesktop 曾只加了前者导致跳转失效）。
