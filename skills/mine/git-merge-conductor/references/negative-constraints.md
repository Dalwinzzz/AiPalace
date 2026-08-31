# Negative Constraints

每条规则结构：[ID] 名称 / 失败原因 / 检测信号 / 后置动作。

Stage 6.5 self-audit iterates these rules against every applied unit
(graft in 6t, hunk in 6c) and emits an `audit-report.md` entry per unit.
A fail triggers rollback per Stage 6.5 contract.

---

## NC-01 项目守卫不要套通用代码

- **失败原因**：通用方法被 `projectName == X` / `tenantId == X` / 类似 enum 比较守卫包裹，其他地区/项目复用同模块时被拦截。Care-class round 3 教训：`normalizeCareClassTeacherName` 套 `projectName==JIASHAN` 拦截了其他地区。
- **检测信号**：
  1. 当前 graft 引入的代码中 grep 命中 `projectName ==` / `tenantId ==` / 类似 enum 比较模式
  2. 对应 `requirements.yaml::items[i].scope_tag` 不含项目专属语义（自由文本但常见词如"嘉善专属"、"项目X限定"等）
- **后置动作**：把守卫降级到业务维度（如 courseType / channel / userRole），或完全移除。如果用户在 Stage 2 明确说该方法是项目专属，scope_tag 应包含项目语义，本 NC 不应该触发。

---

## NC-02 不回退目标已演进的逻辑

- **失败原因**：源分支是早期分叉，target 已有迭代；机械 `replace` 覆盖 target 进展。Care-class 教训：target 的 HZ/NJ regional logic 不可被 source 的 plugin-style 覆盖。
- **检测信号**：
  1. `grafting-plan.yaml::plan[i].target_location.evidence` 显示 target 端有比 merge-base 更新的同名方法 commit
  2. `graft_strategy == replace`
- **后置动作**：strategy 改为 `merge-into` 或 `guarded-overlay`，保留 target 已加入的代码路径。

---

## NC-03 源专属目录结构不带入目标

- **失败原因**：源分支的插件化 / 重构 / 独立 starter 形态污染 target 主线架构。Care-class 教训：refactor/micro-core-dev 的 plugins/ 目录不应整体迁入 develop。
- **检测信号**：
  1. graft 改动包含 target 中不存在的顶级目录（如 `plugins/`、新 `pom.xml` 模块、独立 starter）
  2. 或 graft 修改了顶层构建文件添加新模块
- **后置动作**：转写为 target 已有模块内的等效改动。如果必须新增模块，必须先回 Stage 2 升级 `requirements.yaml` 加 item 并请用户确认。

---

## NC-04 注释里的项目语义限定要解耦

- **失败原因**：源注释带项目限定，迁到 target 后语义错位。Care-class 教训：源注释「嘉善养育照护」搬到 target 后变成限定，但实际代码已经通用化。
- **检测信号**：
  1. 源 hunk 注释 / Javadoc / docstring 含 task 的 scope_tag 中出现的项目专属词
  2. target 同位置注释 / Javadoc 不含该词
- **后置动作**：移除项目限定词，保留业务语义。例如 `// 嘉善养育照护课堂教师` → `// 课堂教师展示名`。

---

## NC-05 不引入 requirements.yaml 外的变更

- **失败原因**：模型"顺手清理"把范围外改动混进合并，导致 PR 散乱 + scope creep。
- **检测信号**：
  1. graft.files_touched 中存在不属于任一 `requirements.yaml::items[*].target_locations` 的文件
- **后置动作**：rollback；若用户在 Phase 2 确认要纳入，必须先回 Stage 2 升级 `requirements.yaml` 加 item（重审 Gate）。
- **特别说明**：此规则在 `SKILL.md` Safety Invariants 第 6 条对应一行硬约束（hard rollback，不可由 NC 配置 disable）。本文件保留检测细节供模型在 self-audit 时引用。

---

## 附录 — 领域示例（参考，非硬规则）

以下示例从 care-class-to-develop 真实实践提炼，作为模型在判断时的参考案例。
不是 NC 编号规则，但在做 self-audit 时可以作为同类问题的识别锚。

### 例 1: PageHelper 分页前不要插入额外查询

- **背景**：Java/MyBatis 项目使用 PageHelper 时，`PageHelper.startPage()` 必须紧跟分页查询调用。
- **错误模式**：在 startPage 之前/之间插入其他查询调用 → 分页 limit 被前一个查询消费，分页失效。
- **care-class round 2 教训**：续接归并时差点把指导单位 filter 写成额外查询，幸而改为 SQL `exists` 内联。
- **应对**：如果 graft 引入了与分页查询同方法的额外 query 调用，self-audit 应该 flag 这条作为人工确认项（不强制 rollback，但报告中标注 ⚠）。

### 例 2: ORM 实体新增字段时的全链路核对

- **背景**：新增表/字段后，domain/example/mapper/service/controller/view 一条链路都要更新。
- **错误模式**：只改 domain，漏掉 mapper.xml 或 example builder。
- **应对**：如果 graft 改动了某 ORM 实体的字段定义，self-audit 应该建议核对同名 mapper.xml + Example.java；缺一则 status 标 partial。

(后续可在此附录持续累积领域示例，但 NC-01~NC-05 是结构性约束，不需要扩展枚举。)
