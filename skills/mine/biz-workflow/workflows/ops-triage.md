# 运维排查线 · ops-triage

> 由 SKILL.md 分诊为"运维排查"后读取。按下列步骤推进，遵守 SKILL.md 的两个决策点与护栏。
> 注意：排查类任务**不强制产生代码提交**——给完结论即可结束（早退分支）。

## 步骤序列

```
1. 分析工单/报错              判断是代码问题还是数据问题
   [根因需结构化设计] → 委托 spec-architect 产出修复 spec（契约同 feature-dev）
2. step-B 代码定位            按报错堆栈反查 / 按现象定位
   [数据问题?] → step-D       委托 sql-expert-dba 查数/诊断（辅助定位根因）
3. step-F 产出结论            根因 + 影响面 + 修复建议 → 落 docs/problem
4. ★决策点①                  摊出根因与修复方案 → 等用户拍板
   ┌─ 只需结论、不改代码 → 到此结束（产出物已落盘）【早退分支】
   └─ 需修复 ↓ ───── 以下需经①放行 ─────
5. 实现修复                   按确认方案改代码
6. [涉及DB?] → step-D         委托 sql-expert-dba（修复涉及 DB）
7. step-C 构建自测            专属 Maven 命令验证修复
8. ★决策点②                  摊出 diff + 提交计划 → 等用户拍板
   ───────── 以下需经②放行 ─────────
9. step-E 提交               git-commit-convention 提交修复
10. [改了Controller接口?] → step-A  回归同步更新 Apifox 文档
```

## 早退分支（排查线特性）

排查任务的**核心交付是 step-F 的结论**（根因 + 影响面 + 修复建议）。
若用户只需结论、不需要立即改代码：在决策点①摊出结论后**即可结束**，
产出物已落 `docs/problem/`，可追溯可复盘。**不强制走到提交。**

## 条件触发说明

- **step-D**：数据问题定位辅助 / 修复涉及 DB，两处都可能触发。
- **step-C / step-E**：仅当真要改代码修复才走；纯结论型排查不碰。
- **step-A**：仅当修复**动到了 Controller 接口**才在收尾回归同步 Apifox 文档。

## SDD 委托契约

与 feature-dev 相同：invoke spec-architect 时必须声明"仅交付 spec、触发 B 分支显式停止、
不要 continue-to-coding、产出后交还控制权"。详见 feature-dev.md 的「SDD 委托契约」。
