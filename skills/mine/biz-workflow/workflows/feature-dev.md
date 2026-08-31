# 需求开发线 · feature-dev

> 由 SKILL.md 分诊为"需求开发"后读取。按下列步骤推进，遵守 SKILL.md 的两个决策点与护栏。

## 步骤序列

```
1. 分析需求原型               理解要做什么、影响哪些接口/表
   [Medium+ 或用户要求] → 委托 spec-architect（见下方「SDD 委托契约」）产出 spec
2. [改接口?] → step-A         先拉 Apifox 契约当靶子（改接口才执行）
3. step-B 代码定位            Controller→Service→Mapper/SQL 定位改动点
                              （若已走 spec，B 退化为"按 spec 核对定位"）
4. ★决策点①                  摊出实现方案 → 等用户拍板
                              （若走了 spec-architect，①由其 Confirm 承担，不重复问）
   ───────── 以下需经①放行 ─────────
5. 实现改动                   按确认方案改代码
6. [涉及DB?] → step-D         委托 sql-expert-dba 评审/优化
7. step-C 构建自测            专属 Maven 命令编译+跑测
8. ★决策点②                  摊出 diff 概要 + 提交计划 → 等用户拍板
   ───────── 以下需经②放行 ─────────
9. [改接口?] → step-A         提交前核对实现与契约一致
10. step-E 提交               git-commit-convention 生成 message 并提交
```

## 复杂度判定与 SDD 委托

沿用 spec-architect 自身的复杂度判定：

| 复杂度 | 是否委托 spec-architect | 决策点①归属 |
|--------|------------------------|------------|
| Small（加字段/改校验/调查询条件） | 可跳过，直接 step-B | 我自己把控 |
| Medium / Complex（跨模块/多表/迁移/架构变更） | **委托，走 SDD** | spec-architect Confirm 承担 |
| 用户显式说"先写 spec / 先规划" | **强制委托** | 同上 |

## SDD 委托契约（invoke spec-architect 时必须声明）

spec-architect 自身会在产出 spec 后**强制进入编码**（其硬约束#3 + Step 7）。
为不与本编排器的决策点冲突，invoke 时**必须包含**：

1. 任务上下文；
2. **"仅交付 spec，触发 spec-architect 的 B 分支（显式停止），不要 continue-to-coding，
   产出 spec 后交还控制权给 biz-workflow"**；
3. 交还后我把 spec 当"已确认方案输入"，继续 step-B（核对）→ 决策点①（已由其 Confirm
   承担则跳过）→ D/C → 决策点② → E → A。

## 条件触发说明

- **step-A**：仅当改动涉及 Controller 接口/字段变更才执行（前置拉契约 + 提交前核对，两个时点）。
- **step-D**：仅当改动涉及 DB 才执行。
- 不涉及接口 → 整段跳过 A；不涉及 DB → 跳过 D。
