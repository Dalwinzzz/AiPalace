---
name: project-personal-ai-repo
description: ~/Documents/AI/ 是个人 AI 工作流专属域（git repo，无 remote）；dalwin-workflow/ 子目录跟踪工作流演化史；docs/ 有管理规范需先读 README
metadata: 
  node_type: memory
  type: project
  originSessionId: d30c5b2c-756f-4acb-a963-317dc8397219
---

## 个人 AI 工作流域

`/Users/dalwin/Documents/AI/` 是**个人 AI 工作流专属域**，是一个 git repo（无 remote、单 main 分支）。此路径下的所有内容都属于 AI 工作流相关资产，包含：

- `dalwin-workflow/` — 个人工作流演化跟踪 subdir
  - `docs/superpowers/specs/` — 每次大调整的设计 spec
  - `docs/superpowers/plans/` — 实施计划
  - `docs/superpowers/plans/logs/` — 各 Phase 实施日志
  - `docs/adr/` — 需要长期追溯的决策记录（默认 commit message 承担；ADR 仅特殊情况）
  - `archived_skills/README.md` — 从 `~/.claude/skills/` 移除的软链 + 复链命令
  - `templates/` — Tier 2/3 skill 模板（首次新 skill 创建时落地）
- `docs/` — AI 工具生成的 design/plan/spec/log 文档统一存放处，有专属管理规范
- 其它子目录：用户既有 AI 实验/产物（如 `mon3tr-codex_v4`、各种 plugin 草稿等）

**Why:** 与 [[reference-skills-root]] 中的 `~/Library/CodeRepo/AI/`（skills 代码 SOT）不同——这里是工作流 meta 演化的 SOT，记录"我为什么这样配置"，不是"配置本身"。

**How to apply:** 用户提及工作流调整、想看历史决策、需要新建 spec/plan 时，默认 cwd 切换到 `~/Documents/AI/dalwin-workflow/`；commit 走 `<type>(<scope>): <subject>` 中文规范，scope 用 `dalwin-workflow`。涉及 `docs/` 目录操作时，先读 `docs/README.md`。
