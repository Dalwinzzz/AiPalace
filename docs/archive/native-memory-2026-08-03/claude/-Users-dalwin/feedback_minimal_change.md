---
name: feedback-minimal-change
description: 局部兼容修复的最小改动 + 审核/回显/副作用问题的全链路复扫习惯
metadata: 
  node_type: memory
  type: feedback
  originSessionId: d30c5b2c-756f-4acb-a963-317dc8397219
---

## 局部兼容修复 (f4)

局部兼容修复优先在现有入口最小改动，不主动抽新类/扩配置。

**Why:** 用户多次纠正过早抽象（如 "这个类看起来不太需要……就在原先方法内加入项目判断即可"）。
**How to apply:** 看到"项目白名单/特例处理"类需求时，先评估能否在已有方法（如 `enableClassSnapshotProject()`）内追加，再考虑抽类；用户未明确同意前不主动扩配置。

## 全链路复扫 (f5)

审核/回显/副作用类问题做全链路复扫，不只改单点。

**Why:** 审核链路（提交、审批、回显、正式表）通常多入口，单点改完仍漏。
**How to apply:** 修复审核/回显类问题时，主动枚举该问题域的所有方法（如 `submitAuditNursery` / `getAuditDetail` / `applyClassLimitSnapshotFromWorkflow` / `buildNurseryClass` / `fillClassLimitFromDb`）一起检查。
