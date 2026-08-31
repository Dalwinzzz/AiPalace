# Archived Skills 索引

记录从 `~/.claude/skills/` 中移除软链的 skills；源码仍保留在 `~/Library/CodeRepo/AI/awesome-skills/<name>/` 下，需要时随时复链回来。

## 当前 archive 名单（2026-05-27）

| Skill | 源码 SOT | 复链命令 |
|---|---|---|
| svg-logo-creator | `~/Library/CodeRepo/AI/awesome-skills/svg-logo-creator` | `ln -s ~/.agents/skills/svg-logo-creator ~/.claude/skills/svg-logo-creator` |
| resume-generator | `~/Library/CodeRepo/AI/awesome-skills/resume-generator` | `ln -s ~/.agents/skills/resume-generator ~/.claude/skills/resume-generator` |
| app-icon | `~/Library/CodeRepo/AI/awesome-skills/app-icon` | `ln -s ~/.agents/skills/app-icon ~/.claude/skills/app-icon` |

## Archive 准则

- 与现役 skill 职责完全重叠（如 svg-logo-creator 被 gemini-svg-creator 取代）
- 使用频次 < 一年一次（如 resume-generator）
- 用户不再使用该技术栈（如 app-icon 之于 RN/Expo）

## 复链流程

1. 确认源码在 SOT 内可读：`ls ~/Library/CodeRepo/AI/awesome-skills/<name>/SKILL.md`
2. 执行 `ln -s` 命令（见上表"复链命令"）
3. 在新 Claude 会话里输入触发该 skill 的描述，验证可被 find-skills 命中

## 备注

archive 仅指"不在 `~/.claude/skills/` 挂软链"，**不是删除源码**。`~/.agents/skills/` 中的对应软链仍保留（指向 SOT），所以 codex 仍可发现这些 skill。如要彻底从 codex 也下架，再额外 `rm ~/.agents/skills/<name>`。

## 现役自建 skill 软链（非 archive，仅登记）

源码 SOT 在本仓库 `skills/` 下，经软链注入 `~/.claude/skills/` 生效，便于 git 追溯。

| Skill | 源码 SOT（本仓库） | 生效软链命令 |
|---|---|---|
| biz-workflow | `dalwin-workflow/skills/biz-workflow` | `ln -s /Users/dalwin/Documents/AI/dalwin-workflow/skills/biz-workflow ~/.claude/skills/biz-workflow` |

> 可选：若要让 codex 也发现，另建 `ln -s <SOT> ~/.agents/skills/biz-workflow`。
