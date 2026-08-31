# Git Merge Conductor — v2 设计稿

> 文档目的：作为 v2 版本的设计定稿。v2 是基于 care-class-to-develop 真实任务实践 + 用户反馈对 v1 的迭代。
> SKILL.md 主体与 references/ 内的模型 prompt 按规则采用英文；templates/ 中给用户呈现的文本采用中文。
> 状态：v2 设计稿，待用户复核后进入 writing-plans 阶段。
> 作者：jpdalwin（czw）+ Claude Opus 4.7（brainstorming co-pilot）
> 日期：2026-05-13
> 上一版：[2026-05-11-git-merge-conductor-design.md](2026-05-11-git-merge-conductor-design.md)

---

## 0. 背景：v1 实践揭示的失配

### 0.1 用户反馈的 4 个核心问题

1. **stage 阶段不够明晰** → 强化工作流感知
2. **复杂归并需求需要多轮 diff 变更** → 工作流增加 final 校验阶段，未达需求则 loop 回前置 diff/merge
3. **缺少反向约束** → 需求外的代码变更也被归并；执行阶段需要负向规则
4. **复杂归并应考虑 worktree**

### 0.2 用户对 skill 写法的 2 个 meta 原则

- **M1**：SKILL.md 主文件少用命令式描述，避免明确约束模型实际该干什么，而是指导模型成为问题的决策者
- **M2**：从 care-class-to-develop 实践提炼失败原因，作为负向约束放入 v2

### 0.3 care-class-to-develop metadata 直接证据

来自 `.git/merge-conductor/care-class-to-develop/`：

- `state.json::decisions: []`（空）、`auto_resolved_summary.A_count: 0`、`B_count: 0`
- `state.json::stage_history` 只有 stage 3 和 stage 7 两条 —— stage 4 / 5 / 5.5 / 6 完全没记录
- 但 `decision-log.md` 写明实际工作走的是"语义回并"（semantic transplant），不是 v1 设计的"conflict 分类 + 决策队列"
- `decision-log.md` 显示实际经历 3 轮迭代：
  - round 1：首次提交 `58860138`（首轮回并）
  - round 2：续接 `4ac7b54b`（补漏：`course_offline_teacher` / `course_offline_js` 等）
  - round 3：Review 修正 `4f98e9ec`（`normalizeCareClassTeacherName` 用 `projectName==JIASHAN` 守卫过严，反而拦截了其他地区复用课堂模块）

### 0.4 失配的本质诊断

v1 的 8-stage pipeline 假设是"git 自己冒 conflict → 分类 → 自动消化 trivial → 人工逐 hunk 决策 non-trivial"。但 care-class-to-develop 这种"目标分支已发生重构、源分支结构不直接落地"的场景，根本不会冒出 git 意义上的 conflict —— 模型只能"语义回并"，但 v1 没有这条路径的工作流，所以 model 即兴做了 3 轮，state machine 全程失效。

同时，round 3 的 scope creep（`projectName==JIASHAN` 套到通用方法）和 round 2 的范围遗漏（漏了 5.5 个 graft item）也佐证：缺少负向约束 + 缺少"需求清单 vs 已合并差异"的最终校验。

v2 不是给 v1 打补丁，而是承认两个 pipeline shape 不同，并把"自动化 + 用户兜底"放到首尾两个明确的 Gate 上。

---

## 1. v2 核心决策（4 项已与用户确认）

| 决策点 | v2 选择 |
|---|---|
| **校验循环触发** | 自动化优先（compile/lint/test → model 自修复 loop，N=3 上限）+ 用户兜底（需求清单 vs 已合并差异表，唯一最终 Gate） |
| **Worktree 启用** | 复杂模式强制（`backport-transplant` / `semantic-transplant` / `rebase-onto` / `forward-integrate`）；简单模式仍主仓 checkout |
| **反向约束落地** | Stage 6.5 per-unit self-audit + `references/negative-constraints.md` 集中规则库；NC-05（不引入 requirements.yaml 外的变更）升级为 Safety Invariant 第 6 条 |
| **决策导向形态** | 每 Stage 五字段模板（Goal / Inputs / Decisions you own / Hard constraints / Outputs）；详细契约下沉到 `references/contracts/*.md`，SKILL.md 主薄化 |

## 2. v2 方案选型

候选 3 方案（保守演进 / 双轨制 / 抽象重构）中选定 **双轨制（Mode-Aware）**：

- 现有 `backport` mode 一拆为二：
  - `backport-cherry`：merge-base 近、target 改动少，cherry-pick 可行 → 走 conflict-pipeline
  - `backport-transplant`：merge-base 远、target 已重构，必须语义嫁接 → 走 transplant-pipeline
- 判定阈值在 `references/mode-inference.md`：`merge_base_age_days > T1` 或 影响范围内 target 端 ≥ N 个 rename/move/refactor signal → 升级为 `backport-transplant`
- `semantic-transplant` 直接进 transplant-pipeline
- 其余 mode（`full-merge` / `cherry-pick-set` / `patch-apply` / `rebase-onto` / `forward-integrate`）仍 conflict-pipeline

两条 pipeline 在 Stage 4-6 内 fork；Stage 0-3、Stage 6.5、Stage 7、Stage 7.5、Stage 8 共享。

---

## 3. v2 Pipeline 总览

```
Stage 0  Entry guards
Stage 1  Input normalization
Stage 2  Mode inference + 策略报告 + 需求清单提取                ★ GATE ★（用户唯一前置确认）
Stage 3  Working setup
         ├─ worktree（复杂模式）← superpowers:using-git-worktrees
         └─ 主仓 checkout merge/<task>（简单模式）
Stage 4-6  mode-aware fork（autonomous，对用户零中断）:
         ├─ conflict-pipeline:
         │     用于 full-merge, cherry-pick-set, patch-apply,
         │         backport-cherry, rebase-onto, forward-integrate
         │     4c: source-side apply  →  5c: A/B/C/D classify + auto-resolve
         │     →  6c: C/D autonomous decision (启发式 + locked rules)
         │
         └─ transplant-pipeline:                                【新】
               用于 backport-transplant, semantic-transplant
               4t: build grafting plan (requirement × target location matrix)
               →  5t: per-item draft (语义映射 → suggested diff，不落盘)
               →  6t: autonomous apply（模型自动选 strategy → apply）
Stage 6.5  Negative-Constraint Self-Audit                       【新】
           per-unit 即时审；失败则 rollback 并标 partial/unresolved
Stage 7    Finalization & commit
Stage 7.5  Verification Loop                                    【新】
           Phase 1: 自动化（compile/lint/scope-test）→ 失败 model 自修复 loop（N≤3）
           Phase 2: 用户兜底（需求清单 vs 已合并内容差异表）     ★ FINAL GATE ★
                    用户「完成」→ Stage 8
                    用户「REQ-X 没做对 / 不该做 / 还多 Z」→ loop 回 Stage 4-6
Stage 8    Wrap-up + cleanup（含 worktree 清理选项）
```

**用户中断点只有两个**：Stage 2 ★ GATE ★ 和 Stage 7.5 Phase 2 ★ FINAL GATE ★。Stage 4-6 全部 autonomous。

---

## 4. SKILL.md 主薄化 + Contracts 下沉

### 4.1 主 SKILL.md 形态（每 Stage 在主文件里的最薄形态）

```markdown
## Stage 2 — Mode Inference, Strategy & Requirement Extraction ★ GATE ★

**职责**：判断 mode、提取需求清单、产出策略报告。后续所有写操作以此为基础，
判断错则整个流程白费。

**Hard gate**：用户未明确「策略 OK」前禁止任何写操作。

**详细契约**：`references/contracts/setup-stages.md#stage-2`
**决策依据**：`references/mode-inference.md`
```

主 SKILL.md 整体规模 200-220 行（v1 是 378 行），保留：
- 头部 metadata + Safety Invariants（新增第 6 条）
- Pipeline 总览图（§3 那张）
- 每 Stage 3-4 行说明 + ★ Gate ★ 标记
- Language convention / Reading order / Quick sanity checks（含新加的 stage-self-check）

### 4.2 五字段契约模板（详细形态，落在 references/contracts/）

每 Stage 的完整契约在 contracts 文件里按这个模板填写：

```markdown
## Stage N — <name>

**Goal**
你要在这里做出 ___ 的判断。后续 ___ 都建立在你这里的判断之上，
判断错了 ___ 会被 ___（用第二人称叙述，进入决策者视角）。

**Inputs**
- <数据源 1>
- <数据源 2>
- <reference 文件路径>

**Decisions you own**
- <决策点 1>，依据 <数据 / 启发式 / 规则>
- <决策点 2>...
- （这是 M1 的核心落地：把"做什么"留给 model，"边界在哪里"留给 skill）

**Hard constraints**（违反就停下）
- <硬约束 1>
- <硬约束 2>

**Outputs**
- <产物 1>（落盘路径）
- <产物 2>（state.json 字段）
- <用户回显内容形式>
```

### 4.3 Contracts 目录结构

不按 stage 编号一文件一编号（会爆出 14 个文件），按"流程相位"合并：

```
references/contracts/
├── setup-stages.md        # Stage 0 / 1 / 2 / 3
├── pipeline-conflict.md   # Stage 4c / 5c / 6c
├── pipeline-transplant.md # Stage 4t / 5t / 6t                 【新】
├── audit-and-verify.md    # Stage 6.5 / 7 / 7.5                【新】
└── wrap-up.md             # Stage 8
```

每个 100-200 行，跟 v1 references 同量级，model 进入每个 stage 时只读一份契约。

### 4.4 Reading order 更新

主 SKILL.md 末尾的"Reading order"表，把 Stage 列对应到具体 contract 文件 + 锚点：

| Stage | 必读 reference |
|---|---|
| Stage 0 / 1 | `contracts/setup-stages.md#stage-0`、`#stage-1` |
| Stage 2 | `contracts/setup-stages.md#stage-2`、`references/mode-inference.md` |
| Stage 3 | `contracts/setup-stages.md#stage-3`、`references/state-schema.md` |
| Stage 4-6（conflict） | `contracts/pipeline-conflict.md`、`references/conflict-classification.md` |
| Stage 4-6（transplant） | `contracts/pipeline-transplant.md`、`references/semantic-mapping.md` |
| Stage 6.5 | `contracts/audit-and-verify.md#stage-65`、`references/negative-constraints.md` |
| Stage 7 / 7.5 | `contracts/audit-and-verify.md#stage-7`、`#stage-75` |
| Stage 8 | `contracts/wrap-up.md` |
| Recovery / Pause / Abort | `references/recovery-protocol.md` |

---

## 5. Stage 2 需求清单产物（`requirements.yaml`）

v2 Stage 2 在策略报告之外**强制额外产出**一份结构化需求清单。后续两处机制全部依赖它：
- Stage 6.5 自审：per-item 核对"本次改动是否落在 `target_locations` 内 + 是否触及 `out_of_scope`"
- Stage 7.5 Phase 2 差异表：把 items 的 status 列出来，「还缺 X / 还多 Y」直接对应 item id

### 5.1 Schema

```yaml
task: <task-name>
extracted_at: <ISO timestamp>
items:
  - id: REQ-01
    title: <中文一句话>
    scope_tag: <自由文本，由 Stage 2 model 按 task 起>
                                      # 例："嘉善养育照护专属" / "通用课堂功能" /
                                      #     "tbd-待用户确认" 等；后续 NC 自审用它判断
                                      #     "通用代码是否被项目守卫"
    target_locations:                 # 你判断的目标改动位置
      - file: <relative path>
        symbol: <class/method/const，可选>
    acceptance:                       # 完成判据，Phase 2 兜底报表用
      - <中文一行>
      - <中文一行>
    out_of_scope:                     # per-item 负向约束（喂给 Stage 6.5）
      - <中文一行>
    status: pending | partial | completed | abandoned
                                      # Stage 6 / 6.5 / 7 维护；
                                      # Phase 2 用户「不该做」→ abandoned
    evidence:                         # 完成证据
      commits: [<sha>]
      files_touched: [<path>]
    ambiguous: false                  # 模糊条目标 true，必须用户确认才能进 Stage 3

global_out_of_scope:                  # 全局负向约束（适用所有 item）
  - <从 references/negative-constraints.md 自动注入通用条目>
  - <用户在 Stage 2 自定义补充>
```

### 5.2 关键设计选择

- **`scope_tag` 自由文本**：v2 不预设枚举（v1 一度想用 `jiashan-only | general | tbd`，但实际任务可能是任何场景）；由 Stage 2 model 按 task 自起 tag，在 Stage 6.5 自审时作为"该改动是项目专属还是通用"的判断锚
- **`out_of_scope` 在 item 级**：每个需求自带反向约束，避免"过严守卫被一刀切套到所有方法"
- **`ambiguous: true` 强制澄清**：Stage 2 模型不确定的条目必须显式标，逼用户在 Gate 之前澄清，不允许带着模糊条目进 Stage 3
- **`status` 不自动转 completed**：Stage 6.5 self-audit pass + Stage 7 commit 完才能转 `completed`；Phase 2 用户说「这个其实没做对」时回退到 `partial`；用户说「不该做」时转 `abandoned`

### 5.3 care-class-to-develop 反推示例

```yaml
task: care-class-to-develop
items:
  - id: REQ-01
    title: 课堂常量与表单配置类型补齐
    scope_tag: 通用课堂功能
    acceptance:
      - 课堂常量集合补齐
      - 表单配置 type 支持 CARE_CLASS
    out_of_scope:
      - 不引入 refactor 分支专属命名

  - id: REQ-02
    title: 课堂保存/详情/H5 列表中年龄与主讲老师逻辑回并
    scope_tag: 通用课堂功能
    target_locations:
      - file: skc-activity/.../CourseOffline*.java
        symbol: normalizeCareClassTeacherName
    acceptance:
      - 保存/详情/H5 三处使用 teacherList 维护展示名
    out_of_scope:
      - 不用 projectName==JIASHAN 作守卫
        # ⚠ 若 Stage 2 漏掉这条 out_of_scope，会重现 round-1 越界、round-3 才修正

  - id: REQ-05
    title: 嘉善课堂教师从表 + 指导单位
    scope_tag: 嘉善专属
    target_locations:
      - file: skc-activity/.../CourseOfflineTeacher.java
      - file: skc-activity/.../CourseOfflineJs.java
    acceptance:
      - 新增 ORM
      - 在保存/详情/列表/H5/预约详情按 projectName==JIASHAN 接入
    out_of_scope:
      - 不影响非嘉善项目的同名接口行为
        # ⚠ round-1 漏了这个 item 整体，导致 round-2 才补
```

---

## 6. transplant-pipeline 详细（Stage 4t / 5t / 6t）

这是 v2 最关键的结构性新增，直接回应 care-class 失配。

### 6.1 Stage 4t — Build Grafting Plan

**职责**：把 `requirements.yaml` 翻译成"per-item × per-target-location"的嫁接矩阵，作为 Stage 5t/6t 的逐项迭代输入。

**核心产物**：`.git/merge-conductor/<task>/grafting-plan.yaml`

```yaml
plan:
  - graft_id: G-01
    req_id: REQ-02                              # 指回 requirements.yaml
    source_evidence:                            # 源分支同名/同语义实现
      - sha: <commit>
        file: <source path>
        symbol: normalizeCareClassTeacherName
        hunk: <git show -W 的方法块>
    target_location:                            # 目标端落点（可能多个）
      - file: <target path>
        symbol: <target counterpart>
        confidence: high | medium | low         # 语义映射置信度
        evidence: [<git grep / rename trail / 模型判断要点>]
    graft_strategy: replace | merge-into | add-new | guarded-overlay
    guard_condition: <可选，e.g., projectName==JIASHAN>
    draft_status: pending | drafted | applied | rejected
```

**`graft_strategy` 四类**（安全度递增）：

| 类型 | 语义 | 适用 |
|---|---|---|
| `replace` | target 端方法直接被源端替换 | 仅当 target 是 stub 时；自审会盯紧 |
| `merge-into` | 把源端逻辑合并进 target 已有方法 | 最常见；需要语义对齐 |
| `add-new` | 源端引入的新方法/类在 target 不存在，直接新增 | 最安全；仅检查命名冲突 |
| `guarded-overlay` | 源端逻辑用 `guard_condition` 包起来叠加，不影响默认路径 | 嘉善 ORM 接入用此 |

### 6.2 Stage 5t — Per-Item Draft

**职责**：对每个 `graft_id` 生成具体改动草案（diff），但**不直接落盘**（落到 `.git/merge-conductor/<task>/drafts/G-XX.diff`）。

每个 draft 包含：
- 上下文摘要（中文一段：你要把什么改成什么、为什么）
- proposed unified diff
- 置信度自评（结合 `target_location.confidence` 和 `out_of_scope` 自检）
- 反向约束初筛（"这个 draft 是否触及 REQ-X 的 out_of_scope"——Stage 6.5 是更严格的二次审，这里是 draft-time 一次轻筛）

### 6.3 Stage 6t — Autonomous Apply Loop

**职责**：对每个 graft 模型自动决策 strategy → apply → 立即 Stage 6.5 self-audit → pass 标 `applied`，fail 自动 rollback 并标 `partial` / `pending`，**全程不中断用户**。

自动决策依据：
- `target_location.confidence`：high/medium 直接 apply；low 标 ⚠ 进 Phase 2 报表但仍 apply（用 draft 占位）
- `graft_strategy` 的安全度（`add-new` < `merge-into` < `guarded-overlay` < `replace`）
- Stage 6.5 self-audit 结果（违反 out_of_scope → 强制 rollback）

**完全替代 v1 的 5 选项 decision-point**。care-class 实践证明 v1 那种逐 hunk 5 选项的设计跟 transplant 场景不匹配（state.json::decisions: [] 就是证据）。

### 6.4 与 conflict-pipeline 的差异

| 维度 | conflict-pipeline | transplant-pipeline |
|---|---|---|
| 工作单元 | 冲突 hunk | requirement × target location（graft） |
| 触发来源 | git 自己冒 conflict | Stage 2 提取 + Stage 4t 语义映射 |
| 自动消化 | A 类 take-target | 无（每个 graft 都要决策 strategy） |
| 决策粒度 | per-hunk | per-graft（通常 per-method） |
| 状态字段 | `state.json::decisions[]` | `state.json::grafts[]` |
| 中断用户 | 否（v2 改 autonomous） | 否 |

---

## 7. conflict-pipeline 改 autonomous（Stage 6c）

为了与 transplant-pipeline 对称，v2 把 v1 的 per-hunk 5 选项中断改为自动决策。

### 7.1 C/D 类自动决策启发式

按优先级匹配，第一个命中即用：

1. **locked_file_rules / global_out_of_scope 命中** → apply rule
2. **两侧都是纯增量段（无重叠逻辑）** → take both（concatenate）
3. **一侧是 whitespace-only / comment-only** → take 另一侧
4. **源端更老（merge-base 早于 target 同位置最近 commit）** → take target
5. **缺省（无法判定）** → 标 `unresolved`，**不在代码里留 `<<<<<<<` marker**

第 5 条尤其关键：v1 的"留 conflict marker 等用户改"在 v2 不可接受，因为 marker 会让 Stage 7.5 Phase 1 编译失败、触发自修复 loop、可能错得更离谱。v2 改为：

- 代码里**默认 take target**（最安全的回退，与 D 类 fallback 一致）
- unresolved 项写入 `.git/merge-conductor/<task>/unresolved.md`，记录被丢弃的 source 侧 hunk
- Phase 2 兜底报表里这些 unresolved 项是 "❓ 需你拍板" 类，用户在 Phase 2 可选择 take source / 自由文本改写

### 7.2 Stage 6c 输出

每个 hunk 处理完写一条 `state.json::decisions[]`：

```yaml
- id: <auto>
  file: <path>
  symbol: <method/function>
  class: C | D
  resolution: rule-id-matched / heuristic-N / unresolved
  taken: source / target / both / target-fallback
  resolved_at: <timestamp>
  audited_at: <timestamp>            # Stage 6.5 时间戳
```

---

## 8. Stage 6.5 — Negative-Constraint Self-Audit

### 8.1 触发时机

per-unit 即时审：
- transplant-pipeline：每个 graft apply 完立刻审
- conflict-pipeline：每个 C/D 类自动决策完立刻审
- 通过 → 标 `applied`；失败 → rollback + 标 `partial`/`unresolved` 进 Phase 2 报表

**不允许"一批做完再审"**——care-class 教训证明越界几轮才被发现是因为批量审。

### 8.2 自审三层检查

1. **Per-item `out_of_scope`**：当前改动是否触及 `requirements.yaml::items[i].out_of_scope`
2. **Global `out_of_scope`**：是否触及 `requirements.yaml::global_out_of_scope`（这里注入 negative-constraints.md 中"通用"类）
3. **领域反模式扫描**：是否命中 `references/negative-constraints.md` 中可检测的反模式

### 8.3 输出

`.git/merge-conductor/<task>/audit/<graft-or-hunk-id>.md`：

```markdown
# Self-audit G-02

**graft**: G-02 → REQ-02 normalizeCareClassTeacherName

**结论**: ❌ fail（NC-01 命中）

**检测项**:
- Per-item out_of_scope ❌ 命中「不用 projectName==JIASHAN 作守卫」
- Global out_of_scope ✅
- NC-01 项目守卫套通用代码 ❌ 命中

**后续动作**: rollback graft G-02；req REQ-02 标 partial；写入 Phase 2 报表 ⚠ 项
```

### 8.4 `references/negative-constraints.md` 初始内容

主文件只放**通用 NC 规则**（可检测、可跨项目复用），从 care-class 提炼：

```markdown
# Negative Constraints

每条规则结构：[ID] 名称 / 失败原因 / 检测信号 / 后置动作。

## NC-01 项目守卫不要套通用代码
- 失败原因：通用方法被 `projectName == X` 守卫包裹，其他地区/项目复用同模块时被拦截
- 检测信号：graft 引入了 `projectName ==` / `tenantId ==` / 类似 enum 比较；
  且对应 item.scope_tag 不含项目专属语义
- 后置动作：把守卫降级到业务维度（如 courseType / channel），或移除

## NC-02 不回退目标已演进的逻辑
- 失败原因：源分支是早期分叉，target 已迭代；机械 replace 覆盖 target 进展
- 检测信号：target_location.evidence 显示 target 端有比 merge-base 更新的同名方法 commit，
  且 graft_strategy == replace
- 后置动作：改为 merge-into 或 guarded-overlay

## NC-03 源专属目录结构不带入目标
- 失败原因：源分支的插件化/重构形态污染 target 主线架构
- 检测信号：graft 改动包含 target 不存在的顶级目录/模块/pom 块
- 后置动作：转写为 target 已有模块内的等效改动；若必须新增，升级 requirements.yaml 加 item 并请用户确认

## NC-04 注释里的项目语义限定要解耦
- 失败原因：源注释带项目限定，迁到 target 后语义错位
- 检测信号：源 hunk 注释含 task 的 scope_tag 关键词，target 同位置注释不含
- 后置动作：移除项目限定词，保留业务语义

## NC-05 不引入 requirements.yaml 外的变更
- 失败原因：模型"顺手清理"把范围外改动混进合并
- 检测信号：graft.files_touched 中存在不属于任一 item.target_locations 的文件
- 后置动作：rollback；若用户确认要纳入，必须先回 Stage 2 升级 requirements.yaml
- **注**：此规则在 SKILL.md Safety Invariants 第 6 条对应一行硬约束，本文件保留检测细节
```

附录区放**领域示例**（如"PageHelper 分页前不要插入额外查询"——care-class round-2 教训），作为参考案例，不是硬规则。

### 8.5 NC-05 升 Safety Invariant 第 6 条

主 SKILL.md `Safety Invariants` 加：

```markdown
6. **No change outside requirements.yaml.** 任何 graft / hunk 改动的文件不在
   `requirements.yaml::items[*].target_locations` 内即触发硬性 rollback。
   若用户希望纳入，必须先在 Stage 2 升级 requirements.yaml 加 item
   （回到 Stage 2 ★ Gate ★ 重审）。检测信号与后置见
   `references/negative-constraints.md#NC-05`。
```

---

## 9. Stage 7.5 — Verification Loop

### 9.1 Phase 1 — 自动化验证

**职责**：跑项目语言原生的 compile / lint / scope-test。失败 → model 进入修复 loop（有限）。

**项目类型自动检测**：

| 检测信号 | 执行命令 |
|---|---|
| `pom.xml` 存在 | `mvn -DskipTests compile`（先编译，最便宜） |
| `package.json` 存在 | `npm run typecheck` 或 `tsc --noEmit` |
| `go.mod` 存在 | `go build ./...` |
| `pyproject.toml` / `requirements.txt` | `python -m compileall` 或 `ruff check` |
| 多语言混合 | 各跑各的 |

**命令优先级**（便宜的先跑，快速失败）：

1. compile / typecheck（必跑）
2. lint（必跑）
3. **scope-test**（默认跑）：仅跑 `requirements.yaml` 涉及模块的相关 test

Stage 2 在 `state.json::config.verification` 字段持久化用户对 Phase 1 的偏好：

```yaml
verification:
  compile: true        # 默认 true，禁用需用户显式
  lint: true           # 默认 true
  test: scope          # 默认 scope；可改 full / off / suites: [<name>...]
```

**修复 loop 规则**：

- 每次修复前打 tag `merge/<task>/before-fix-iter-N`
- 修复定位：解析错误信息 → 映射到具体 graft / hunk → rollback 那条 + 重新生成 draft + 走 6.5 self-audit
- **硬性上限 N=3**。3 次后投降，把 compile/lint/test 错误原封带入 Phase 2 兜底报表
- 每轮 iteration 写 `state.json::iterations[]`

### 9.2 Phase 2 — 用户兜底差异表（唯一最终中断点）

报表同时写到 `merge-report.html` 和回显终端。结构：

```markdown
# 合并验证报告 — <task>

## 自动化校验
- compile: ✅ passed (iter 2)
- lint: ✅ passed
- test: ✅ passed (scope: REQ-01, REQ-02, REQ-05)

## 需求清单兑现
| REQ | 标题 | scope_tag | status | evidence | 备注 |
|---|---|---|---|---|---|
| REQ-01 | 课堂常量补齐 | 通用课堂 | ✅ completed | G-01 → 3 files | |
| REQ-02 | 年龄与主讲老师回并 | 通用课堂 | ⚠ partial | G-02 → rollback | NC-01 命中，需用户拍板 |
| REQ-05 | 嘉善教师从表 | 嘉善专属 | ❌ pending | 无 | low-confidence，请确认目标位置 |

## Self-Audit 拦截项（共 N 处）
- G-02 / REQ-02：命中 NC-01（项目守卫套通用代码），已 rollback
- ...

## 范围外尝试（NC-05 拦截）
- 模型尝试改动 `<file>`，但不在任一 item.target_locations 内 → rollback

## 你的决定
- [完成]                          → 进 Stage 8
- [REQ-X 没做对] + 说明           → 回 Stage 4-6 针对 REQ-X 重做
- [REQ-X 不该做]                  → 升级 requirements.yaml 移除 + rollback
- [还多 Z（路径或描述）]          → 找到引入项 → rollback
- [自由文本]                      → 模型解析 → 回显 → 二次确认
```

### 9.3 Loop 回退语义

| 用户反馈 | 模型动作 |
|---|---|
| REQ-X 没做对 | 找到 REQ-X 对应 grafts → rollback → 重回 Stage 4t（transplant）或 Stage 5c（conflict） |
| REQ-X 不该做 | `requirements.yaml::items[X].status = abandoned` + rollback grafts |
| 还多 Z | 找到引入 Z 的 graft → rollback；若 NC-05 应当拦下但没拦下，写到 audit 里供后续改进 |
| 我自己改完了 | 模型读 working tree，把 user 的 manual 改动 stage 进合适的 commit |

每轮 Phase 2 反馈后回到 Stage 4-6 重做，再次回到 Phase 1 → Phase 2，循环直到用户说"完成"。`state.json::iterations` 持续累加。

### 9.4 关键设计

- **唯一中断点**：除 Stage 2 Gate 外，整个流程只在 Phase 2 中断用户。care-class 的 3 轮迭代会被显式表达为 3 次 Phase 2 循环（v1 之前是隐性的人工 review 3 次）
- **iteration 上限**：Phase 1 自修复 ≤ 3 次；Phase 2 总轮数无上限（用户主权）
- **多轮可恢复性**：每轮 `before-iter-N` tag + `iterations[]` 数组，任何时刻 abort 都能回退到 last good state

---

## 10. Worktree 集成

### 10.1 触发条件

复杂模式自动走 worktree：
- `backport-transplant`
- `semantic-transplant`
- `rebase-onto`
- `forward-integrate`

`backport-cherry` / `full-merge` / `cherry-pick-set` / `patch-apply` 仍主仓 checkout `merge/<task>`。

### 10.2 实现：委托 superpowers:using-git-worktrees

v2 不自己实现 worktree 管理，直接调用 superpowers:using-git-worktrees skill。Stage 3 判定要走 worktree 时：

```
1. 主仓打 tag merge/<task>/before-step-3
2. 调用 superpowers:using-git-worktrees 创建隔离工作区
3. 拿到 worktree 路径写到 state.json::working_branch.worktree_path
4. 后续 Stage 4-7 的 cwd 切换到 worktree 路径
5. .git/merge-conductor/<task>/ 数据仍写在主仓的 .git 下
   （state / audit / drafts / 报告都在主仓 — metadata 主仓化）
```

好处：
- 用户主仓 working tree 完全不被打扰，可并行做别的事
- 中间产物统一在主仓 `.git/merge-conductor/<task>/`，资源管理一致
- 代码改动在 worktree，主仓不变；abort 时 superpowers 自己负责清理

### 10.3 state.json 新增字段

```json
{
  "working_branch": {
    "name": "merge/<task>",
    "worktree_path": "<absolute path>",      // null = 主仓 checkout
    "use_worktree": true
  }
}
```

### 10.4 失败 / Abort / Resume 处理

- abort `[a]`：先 `git worktree remove --force <path>`，再 `git branch -D merge/<task>`，再 `rm -rf .git/merge-conductor/<task>`
- pause `[p]`：worktree 保留（用户可以直接进去看），`state.json::status=paused`，resume 时验证 worktree 仍存在 + branch 仍指向预期 commit
- 中途崩溃：state.json 写在前，git worktree 命令成功在后；如果 `worktree_path` 写了但目录不存在 → resume 时识别为"worktree missing"，让用户选重建 / 主仓 fallback / 放弃

### 10.5 Stage 8 cleanup 增项

4 个 cleanup 选项保持原样，但每个末尾加一行"worktree 是否同步清除"。默认与 cleanup-policy 联动：
- 默认 7-day：worktree 同删
- Last-N 保留：保留 worktree 路径
- 永久保留：保留 worktree
- 手动：打印 `git worktree remove <path>` 命令

### 10.6 降级路径

如果 superpowers:using-git-worktrees 不可用或失败，Stage 3 退回主仓 checkout 模式 + warn 用户「worktree 创建失败，已降级到主仓模式，建议 stage 完成后立刻 review」。

---

## 11. Stage 可见性强化（P1 解法）

### 11.1 单行 Banner

每个 Stage 入口必输出固定格式中文单行 banner：

```
[Stage 4t · Build Grafting Plan · iter 1 · tag: merge/<task>/before-step-4]
```

`iter` 是 Phase 2 循环计数器（每轮 Phase 2 回 Stage 4-6 时 +1）。

### 11.2 State 写入是 Stage 转换的硬条件

写到 Safety Invariants：模型不允许在 stage 转换时只更新内存而不写 state.json。每次 stage 切换流程：

```
1. 完成本 stage 的所有 Outputs
2. 写 state.json::stage = next, state.json::stage_history.append({stage, kind, tag, completed_at})
3. 输出新 stage 的 banner
4. 才能开始下一 stage 的工作
```

state.json 写入失败 → 终止流程并报告用户，禁止"继续往下做"。

### 11.3 Stage 边界对应 git tag

每个 stage 入口都打 `merge/<task>/before-step-<N>` tag，`state.json::stage_history` 一一对应。最终 stage_history 完整 11 条记录（0/1/2/3/4(c-or-t)/5(c-or-t)/6(c-or-t)/6.5/7/7.5/8），缺一就是 bug。care-class 那种 3 → 7 直跳 v2 不允许出现。

### 11.4 Quick sanity check 增项

主 SKILL.md 末尾 Quick sanity checks 加：

> **Before any user-facing output**: am I at the stage I think I'm at?
> Read `state.json::stage` and compare. Mismatch → 立刻停下来 reconcile 而不是继续。

### 11.5 不做的事

- ❌ 每条回复开头加 `[stage N]` 前缀（banner 够了）
- ❌ stage 内子步骤都写 state.json（用 `state.json::substep` 可选记录给 debug）
- ❌ 强制用户在每个 stage 回复 ack

### 11.6 state.json 字段增强

```json
{
  "version": "2.0",
  "stage": 4,
  "stage_kind": "4t",                    // 区分 4c/4t/5c/5t/6c/6t
  "pipeline": "transplant",              // 或 conflict
  "iter": 1,
  "iterations": [
    { "iter": 1, "started_at": "...", "trigger": "initial", "ended_at": "..." }
  ],
  "stage_history": [
    { "stage": 0, "kind": "0", "tag": null, "completed_at": "..." },
    { "stage": 1, "kind": "1", "tag": null, "completed_at": "..." },
    { "stage": 2, "kind": "2", "tag": null, "completed_at": "..." },
    { "stage": 3, "kind": "3", "tag": "merge/.../before-step-3", "completed_at": "..." },
    { "stage": 4, "kind": "4t", "tag": "merge/.../before-step-4", "completed_at": "..." }
  ]
}
```

---

## 12. 文件清单 diff（v1 → v2）

| 文件 | 状态 | 说明 |
|---|---|---|
| **SKILL.md** | 大改 | 主薄化（200-220 行），五字段模板套薄壳；详细契约下沉；Safety Invariants 新增第 6 条 |
| `references/mode-inference.md` | 改 | 加 `backport-cherry` vs `backport-transplant` 拆分判定 |
| `references/conflict-classification.md` | 改 | C/D 类增加自动决策启发式小节（autonomous 需要） |
| `references/semantic-mapping.md` | 改 | 给 transplant-pipeline 用，输出格式对齐 `grafting-plan.yaml::target_location` |
| `references/state-schema.md` | 改 | 新字段：`version`、`stage_kind`、`pipeline`、`iter`、`iterations[]`、`working_branch.worktree_path`、`requirements[]`、`grafts[]` |
| `references/html-report-template.md` | 改 | 新增 Phase 2 兜底报表 section 模板 |
| `references/recovery-protocol.md` | 改 | 加 worktree resume / abort 场景 + iteration 中断恢复 |
| `references/contracts/setup-stages.md` | **新** | Stage 0/1/2/3 五字段契约 |
| `references/contracts/pipeline-conflict.md` | **新** | Stage 4c/5c/6c 五字段契约 |
| `references/contracts/pipeline-transplant.md` | **新** | Stage 4t/5t/6t 五字段契约 |
| `references/contracts/audit-and-verify.md` | **新** | Stage 6.5 / 7 / 7.5 五字段契约 |
| `references/contracts/wrap-up.md` | **新** | Stage 8 五字段契约 |
| `references/negative-constraints.md` | **新** | NC-01~NC-05 通用规则 + 领域示例附录 |
| `templates/strategy-report.md` | 改 | 加 requirements.yaml 渲染锚点 |
| `templates/requirements.yaml` | **新** | Stage 2 需求清单 schema 模板 |
| `templates/grafting-plan.yaml` | **新** | Stage 4t 嫁接矩阵 schema 模板 |
| `templates/draft.md` | **新** | Stage 5t per-item draft 模板 |
| `templates/audit-report.md` | **新** | Stage 6.5 self-audit 输出模板 |
| `templates/verification-report.md` | **新** | Stage 7.5 Phase 2 兜底报表模板（终端 + HTML 两版） |
| `templates/decision-point.md` | **删** | autonomous pipeline 不再需要逐项 5 选项 |
| `templates/commit-message.md` | 改 | 加 iteration 信息 + rolled-back 项 |
| `templates/wrap-up-report.md` | 改 | 加 worktree 清理选项 |
| `agents/` | 保留 | v1 留下的，本次迭代不动 |

---

## 13. 兼容性、验证、实施分阶段

### 13.1 v1 → v2 兼容

- v1 启动的**未完成**任务（`state.json::status == in-progress | paused`）：v2 启动时检测缺少 `version: "2.0"` 字段 → 提示用户「这是 v1 会话，无法平滑升级，建议 abort 后用 v2 重跑，或保留 v1 形态手工完成」。不做自动迁移
- v1 已 `finalized` 任务：v2 不读不动，cleanup 仍走原 cleanup-policy
- state.json 顶层加 `version: "2.0"`，v1 是 `"1.0"`，永远不混存

### 13.2 验证矩阵

v1 现有 5 个 smoke 场景（SMOKE-TEST.md）全部继续 passing，加 4 个新场景：

| 场景 | 验证目标 |
|---|---|
| F. backport-transplant | care-class-to-develop 的 git history 做成 fixture，跑完整 transplant-pipeline → 验证 Phase 2 上 NC-01 拦截 → 用户给反馈 → loop → finalize |
| G. worktree 生命周期 | 复杂模式创建 worktree → 中途 `[a]` abort → 验证 worktree 完全清理 + 主仓 unchanged |
| H. Phase 1 修复 loop 上限 | 注入 compile error → model 自修 3 次失败 → 自动投降进 Phase 2 |
| I. Phase 2 多轮迭代 | 用户「REQ-X 没做对」→ 回 Stage 4t 重做 → 再 Phase 2 → 完成；验证 iterations[] 完整记录 |

### 13.3 实施分阶段（给 writing-plans 的草图）

为了避免一次性 PR 太大、又能让每阶段独立通过 smoke 场景：

- **Phase 1 — 基础设施**：state schema 升级（version 2.0 + 新字段）、worktree 集成（调 superpowers:using-git-worktrees）、单行 Banner、stage_history 完整性硬约束、Safety Invariant 第 6 条
- **Phase 2 — 主薄化 + contracts**：SKILL.md 重写、新建 references/contracts/ 5 文件、五字段模板套到每 stage
- **Phase 3 — Stage 2 需求清单**：requirements.yaml schema + 模板 + Stage 2 提取流程；scope_tag 自由文本、ambiguous 标记
- **Phase 4 — transplant-pipeline**：Stage 4t/5t/6t、grafting-plan.yaml、draft 模板、模型自动决策 strategy
- **Phase 5 — Stage 6.5 + 反向约束**：negative-constraints.md（NC-01~05）、self-audit 流程、NC-05 hard-fail rollback、领域示例附录
- **Phase 6 — Stage 7.5 校验循环**：Phase 1 项目类型检测 + 修复 loop（N=3 上限）、Phase 2 兜底报表模板、loop 回退语义
- **Phase 7 — conflict-pipeline autonomous**：Stage 6c 改 autonomous + C/D 启发式、unresolved 项落 audit 不留 conflict marker
- **Phase 8 — 收尾**：删 decision-point.md、verification-report 模板、wrap-up 加 worktree 选项、SMOKE-TEST 加场景 F/G/H/I + care-class fixture

**Phase 顺序设计依据**：先把 transplant-pipeline + 反向约束 + 自审 + 校验循环跑通（Phase 1-6 直接解决 care-class 主诉），再回头补 conflict-pipeline 对称性（Phase 7）。每个 Phase 完结都跑对应 smoke 场景，全绿才进下一 Phase。

---

## 14. 风险与未决项

### 14.1 风险

| 风险 | 缓解 |
|---|---|
| transplant-pipeline 的语义映射置信度可能高估，导致 high confidence 项实际错位 | confidence 评分纳入 Stage 6.5 自审；low confidence 进 Phase 2 标 ⚠；用户兜底是最终防线 |
| Phase 1 修复 loop 走 3 次仍 fail，但 Phase 2 报表里的错误信息不够帮用户定位 | 报表里附 graft id → file path → 编译错误原文链路；rollback 历史也展示 |
| NC-05 hard rollback 太严，可能拦下用户期望的"顺带改一行"的合理改动 | 设计上是"先 rollback，再让用户在 Phase 2 决定是否纳入 requirements.yaml"——拦截不是终止，是 reroute |
| autonomous Stage 6c/6t 让用户失去过程控制感 | banner 强化感知 + state.json 完整 stage_history + Phase 2 看到所有自动决策结果；用户随时可 `[p]` pause + 手工进 worktree 检查 |

### 14.2 未决项（v2 内不解决，作为 v3 候选）

- transplant-pipeline 的 grafting plan 是否需要更细的"重命名追踪"（git --find-renames 已被 v1 用到，v2 复用）
- 是否需要把 negative-constraints.md 按领域分文件（如 `negative-constraints/java.md`、`negative-constraints/typescript.md`），让 model 按 task 主语言加载子集 —— 现阶段先单文件
- 多人协作场景：另一开发者也在 base commit 上做了变更，v2 仍假设单人单仓 —— v3 再处理
- 大型仓库（>10 万文件）Stage 4t grafting plan 计算耗时 —— 现阶段 care-class 量级（千级文件）够用

---

## 15. 与 v1 的关系总结

v2 不是 v1 的小修小补，而是**承认 v1 的 8-stage pipeline 假设过于狭隘**：v1 假设所有复杂归并都能归约为 conflict-driven 工作流，而 care-class-to-develop 揭示了 transplant-driven 工作流是另一类独立形态，必须用不同的 stage 结构。

v2 通过：
- 双轨 pipeline（解决形态失配）
- Stage 2 需求清单（建立"宪法"）
- Stage 6.5 即时自审 + NC-05 升 Safety Invariant（堵 scope creep）
- Stage 7.5 自动化 + 兜底（显式表达"复杂归并需多轮"的客观规律）
- Stage 可见性 4 层强化（解决"模型自己也忘了在哪"）
- Worktree 委托（隔离影响）
- 五字段契约下沉（主薄化、决策导向 over 命令式）

直接回应用户 4 个核心问题 + 2 个 meta 原则。失败案例（care-class）的每条教训都映射到具体机制：

| care-class 失败模式 | v2 对应机制 |
|---|---|
| `decisions:[]` + 3→7 stage 跳跃 | transplant-pipeline + stage_history 硬约束 |
| Round 1 漏 REQ-05 | requirements.yaml + Phase 2 差异表 |
| Round 3 修 `projectName==JIASHAN` 越界 | scope_tag + NC-01 + Stage 6.5 即时审 |
| 全程隐性 3 轮 | Phase 2 显式 loop + iterations[] |
| 模型自由发挥 | NC-05（Safety Invariant 第 6 条）|
| 主仓被改动 | worktree 委托（复杂模式默认隔离） |

---

> 文档结束。等待用户复核 → 进入 writing-plans 阶段生成可执行的 8-phase 实施计划。
