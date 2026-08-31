---
name: feedback-worktree-semantics
description: "置空 worktree" = detach + 删分支，不等于清理未跟踪文件
metadata:
  type: feedback
---

## Worktree 置空语义 (f8)

"置空 worktree" = `git switch --detach <base>` + `git branch -D <branch>`，**不**等于清理未跟踪文件。

**Why:** 用户在 cherry-pick 完成后说 "本 worktree 置空然后删掉这个分支"，意图是释放分支占用；未明确要求前不要擅自删未跟踪目录。
**How to apply:** 收到"置空 worktree"指令时，按 `git worktree list --porcelain` 查占用 → `git switch --detach <base>` → `git branch -D <branch>` 顺序操作；若用户要全清空未跟踪文件，需用户单独确认。
