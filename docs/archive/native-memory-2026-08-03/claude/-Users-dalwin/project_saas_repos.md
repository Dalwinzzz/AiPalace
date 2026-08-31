---
name: project-saas-repos
description: SaaS 三大 sub-repo 路径（skc-nursery / skc-activity / skciotdevice）+ 高频项目白名单常量
metadata: 
  node_type: memory
  type: project
  originSessionId: d30c5b2c-756f-4acb-a963-317dc8397219
---

## SaaS 子仓库布局 (p1)

| 仓库 | 路径 |
|---|---|
| skc-nursery（worktree） | `/Users/dalwin/.codex/worktrees/3cdf/skcnursery-bugfix-parallel-20260417` |
| skc-activity（IdeaProject） | `/Users/dalwin/Library/IdeaProject/ZhiJin/SunkidCloud/skcservers/skcactivity` |
| skciotdevice（IdeaProject） | `/Users/dalwin/Library/IdeaProject/ZhiJin/SunkidCloud/skcservers/skciotdevice` |

`Constants.PROJECT_NAME_JINAN` 是高频项目白名单常量（济南项目）。

**Why:** 三个仓库分布于不同物理路径；项目白名单常量在多个审核/回显链路中复用。
**How to apply:** 用户提及 "saas/skc-X" 类目标时，优先在上述路径开展工作；Java 修复涉及"济南项目"或类似项目特例时，先搜 `PROJECT_NAME_JINAN` 看现有判断点。

相关：[[maven-config]] 所有 mvn 命令规则适用；[[feedback-minimal-change]] 全链路复扫常用于这三个仓库。
