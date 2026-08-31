---
name: feedback-workflow
description: 主任务链路偏好——review/brainstorming/spec/实施 + spec 落盘后的执行边界 + 代码修复默认手势 + 执行 plan 前的事实核对
metadata: 
  node_type: memory
  type: feedback
  originSessionId: d30c5b2c-756f-4acb-a963-317dc8397219
---

## 主链路偏好 (f1)

大任务接受 "review → brainstorming → spec → 实施" 主链；每步沉淀为 repo-local 文档，不停留在聊天。

**Why:** 用户希望复杂任务可追溯、可复盘，仅口头结论不足以承担后续协作。
**How to apply:** 任务规模评估为"大/复杂"时，主动建议 spec-architect 或 brainstorming → writing-plans 流程；产物落到 repo `docs/` 路径。

## Spec 落盘后的执行边界 (f2)

任务**小且简单**时，落盘 spec 后默认直接执行，不再确认方向；任务大/复杂时，即便 spec 已落盘也先简短确认方向再动手。

**Why:** 小任务 spec 是 fast-pass；大任务 spec 不能替代方向确认（避免误读）。
**How to apply:** 看到 "按照 xxx-spec.md 完成编码" 类指令时，先评估改动范围（如 ≤3 个文件、单模块 → 小；跨模块/多链路 → 大）；小则直接做，大则先回 "确认范围 X/Y/Z，开始执行" 一句话再做。

## 代码修复默认手势 (f3)

默认 "确认入口/调用点 → 最小化改动服务层 → 编译/模块静态验证 → `git diff --check`"。

**Why:** 用户重视定向证据、最小改动、diff 纯度；不喜欢猜测式修改。
**How to apply:** Java/Spring 修复任务的固定收尾流程；mvn 命令按 [[maven-config]] 附加参数。

## 执行 plan 前的事实核对 (f9)

执行已落盘的 plan / spec 时，每个结构性操作（`git init` / `mkdir` / `mv` / `rm -rf` / 跨 repo 文件操作）前仍需现场核对状态——不要盲从 plan 写的前提假设。

**Why:** plan 与执行之间可能间隔数日或数周，文件系统/git 状态会漂移；plan 自身也可能误判初始条件（例如 plan 假设某目录不是 git repo，实际是）。盲从执行会产生不可逆破坏。
**How to apply:** 进入"动文件 / 动 git 状态"的步骤前，用 `pwd`、`git rev-parse --show-toplevel`、`test -e`、`ls` 等只读命令确认当前真实状态匹配 plan 假设；不匹配则停下与用户对齐，不擅自调整 plan 继续执行。
