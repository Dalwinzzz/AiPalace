# 需求开发线 · feature-dev（tier-aware）

> triage 判为"需求开发线"后读取。遵守 SKILL.md 的决策点门控与不可逆护栏。
> 条件步骤：`step-A` 仅当改动涉及 Controller 接口 / 字段变更；`step-D` 仅当涉及 DB。

## T0 直做

`step-B` 快速定位 → 改 → self-check（编译 / 快速验证）→ 交。无决策点，🚧 护栏仍在。

## T1 轻纪律（≤5 文件 / 新小功能单元 / 可逆逻辑改）

1. `[改接口?]` `step-A` 拉 Apifox 契约当靶子
2. `step-B` 代码定位（Controller → Service → Mapper/SQL）
   - 探查量大但只要一个结论 → 按 `policies.md` 派 subagent 卸载探查
3. 实现改动（写新功能单元建议 test-first，见 `disciplines.md`）
4. `[涉 DB?]` `step-D` 委托 sql-expert-dba
5. `step-C` 构建自测 —— 结论要有**本轮新鲜跑出的证据**，不口头带过
6. **★决策点②（停）**：摊"改了哪些文件 + diff 概要 + 提交计划"，等拍板
7. `[改接口?]` `step-A` 提交前核对契约 → `step-E` 提交

## T2 全纪律（跨模块 / 公共 API / 契约 / DB schema / 迁移 / 需先设计 / 显式要求）

> 第 1 步脑暴时若发现**未定决策多到一次会话收敛不完**（不是活多，是有雾）→ 就地升 T3，改走 `decision-map.md`。

1. **`grilling` 脑暴定方案**：一次一问、每问给推荐答案、能查代码就查，收敛到共识方案
2. **委托 `spec-architect` 出 spec**（契约见下）——其 Confirm 即决策点①
   - 需隔离 → 按 `policies.md` 起 worktree；探查/实现可并行 → 派 subagent
3. `[改接口?]` `step-A` 拉契约 → `step-B` 按 spec 核对定位
4. **★决策点①**：spec-architect Confirm 已承担则跳过，否则在此摊方案等拍板
   ───── 经①放行 ─────
5. 实现：**test-first 强制**（RED → GREEN → REFACTOR）
6. `[涉 DB?]` `step-D` → `step-C` 构建自测（带证据）
7. **★决策点②（停）**：摊 diff + 提交计划，等拍板
   ───── 经②放行 ─────
8. `[改接口?]` `step-A` 核对契约 → `step-E` 提交

## SDD 委托契约（T2 invoke spec-architect 时必须声明）

spec-architect 产出 spec 后会自动进入编码（其硬约束）。为不与本编排器的决策点冲突，invoke 时**必须**说明：

1. 任务上下文；
2. "**仅交付 spec，走 B 分支显式停止，不要衔接编码，产出后交还控制权给 ownerpowers**"；
3. 交还后把 spec 当"已确认方案输入"，继续 `step-B` 核对 → 决策点①（已由 Confirm 承担则跳）→ 实现 → D/C → 决策点② → E → A。
