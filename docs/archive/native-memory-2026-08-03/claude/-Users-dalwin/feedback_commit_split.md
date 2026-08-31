---
name: feedback-commit-split
description: 默认将单元测试与源码拆成 2 个 commit 提交（方便 IDEA 复核）
metadata: 
  node_type: memory
  type: feedback
  originSessionId: d30c5b2c-756f-4acb-a963-317dc8397219
---

## 单元测试与源码拆 2 commit (f6)

**默认**将单元测试与源码拆成 2 个 commit 提交。

**Why:** 用户在 IDEA 编辑器做最终确认时，分开 commit 便于逐步核对。
**How to apply:** 修复任务完成后，先 `git add <src>` + commit（feat/fix），再 `git add <test>` + commit（test）；commit message 按 `<type>(<scope>): <subject>` 中文规范。
