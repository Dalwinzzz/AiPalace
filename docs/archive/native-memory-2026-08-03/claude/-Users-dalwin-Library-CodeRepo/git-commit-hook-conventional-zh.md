---
name: git-commit-hook-conventional-zh
description: 本机全局 git commit-msg 钩子强制 conventional type + 中文主题，所有仓库提交都受约束
metadata: 
  node_type: memory
  type: project
  originSessionId: 006a6b06-ef18-40fa-badd-c1aaf6a75895
---

用户机器设置了 `core.hooksPath=~/.config/git/hooks`（全局 commit-msg/validate-commit-msg 钩子），任何仓库（包括新建 git init 的）提交信息必须满足：`<type>(<scope>): <subject>`，type ∈ feat|fix|docs|style|refactor|perf|test|chore|revert|build|ci|context|config|workflow|skill|prompt|sync（scope 可省略），且 **subject 必须含汉字**。

**Why:** 不符合格式的 commit 直接被拒（exit 128），钩子只输出示例不解释规则。

**How to apply:** 在任何仓库提交时都用如 `feat: 中文描述` 的格式；纯英文 subject 会被拒。相关项目 [[dailydragon-project]] 首次提交时踩过。
