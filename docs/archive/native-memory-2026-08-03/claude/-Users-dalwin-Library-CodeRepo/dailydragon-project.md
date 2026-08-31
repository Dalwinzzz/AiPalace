---
name: dailydragon-project
description: DailyDragon 手游日常自动化项目——位置、目标游戏、mac开发/win运行的双环境约束
metadata: 
  node_type: memory
  type: project
  originSessionId: 006a6b06-ef18-40fa-badd-c1aaf6a75895
---

`~/Library/CodeRepo/DailyDragon`：个人自用手游日常自动化 Agent（2026-07-04 通宵初版 v0.1.0），依据 `~/Documents/AI/国产大模型手游日常Agent_调研与技术方案.docx` 构建。

**Why:** 用户目标游戏是《明日方舟：终末地》《异环》PC 端；只自动化"菜单半"日常（签到/邮件/基建/委托），刻意不做 3D 寻路/实时战斗/内存读写（方案定死的风险边界）。

**How to apply:**
- 开发环境是 macOS 但运行目标是 Windows——改代码后用 `.venv/bin/python -m pytest tests/` + `python -m dailydragon demo` 验证（mock 后端），Windows 专属代码（capture/windows.py, control/windows.py）本机跑不了，改动要靠文档/context7 核实 API（pydirectinput 没有 scroll/drag/hotkey，已用 Win32 mouse_event 绕过）。
- 任务链是纯 YAML（config/games/*.yaml），加日常/新游戏优先改配置不改代码。
- 用户后续实测反馈可能要求校准 endfield.yaml 步骤顺序与模板名。进度见仓库 docs/DEVLOG.md。
