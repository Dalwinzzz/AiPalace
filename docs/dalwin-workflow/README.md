# dalwin-workflow

跟踪 dalwin 个人 AI 工作流（Codex + Claude Code）的演化史。

## 目录

- `docs/superpowers/specs/` — 设计 spec（每次大调整一份）
- `docs/adr/` — 决策记录（仅"需要长期追溯/争议大"的决策才独立写 ADR；常规变更靠 commit message）
- `skills/` — 自建现役 skill 的源码 SOT（如 `biz-workflow`），经软链注入 `~/.claude/skills/` 生效
- `archived_skills/`（实施后创建）— 从 `~/.claude/skills` 移除的软链清单 + 复链方法
- `templates/`（推迟到首次创建新 skill 时）— Tier 2/3 skill 模板示例

## 当前 spec

[2026-05-25 个人工作流设计](docs/superpowers/specs/2026-05-25-personal-workflow-design.md)
