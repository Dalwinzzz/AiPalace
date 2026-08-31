# Git Merge Conductor — v1 设计稿

> 文档目的：作为 v1 版本的设计定稿，保留中文描述以便后续迭代追溯设计思路。
> SKILL.md 主体与 references/ 内的模型 prompt 按规则采用英文；templates/ 中给用户呈现的文本采用中文。
> 状态：v1 设计稿，待用户复核后进入 writing-plans 阶段。
> 作者：jpdalwin（czw）+ Claude Opus 4.7（brainstorming co-pilot）
> 日期：2026-05-11

---

## 0. 背景与动机

### 0.1 业务场景（用户痛点）

复杂代码归并主要落在两类场景：

1. **跨版本/重构回灌**：不同项目分版本部署。某功能在部署分支/重构分支上线后，需要把同一功能再同步到 develop 主线，但主线在过去 1-2 个月里已经发生重构。
2. **正向回灌 + hotfix 集成**：feature 分支基于较老的 develop 拉出做迭代需求；期间 develop 修了同模块的 bug；需求完成后，feature 合回 develop 时要把 bug fix 融入新需求逻辑。

### 0.2 现有工具的不足

- 原始 git 终端交互过于原始，对复杂 merge 场景需要的"策略 → 决策 → 执行"链路缺乏可视化
- lazygit 等 TUI 在分类、策略呈现上仍不够清晰
- JetBrains 系列 GUI 工具体验最好，但仍要开发者全程手动决策，缺少"模型辅助的策略层"

### 0.3 本 skill 的定位

- **不是**：更好的合并 UI（你用 JetBrains/VSCode 看结果即可）
- **是**：合并战略家 + 安全执行者——模型可承担的部分全自动化，把人决策点收敛到最小、最清晰的单选

---

## 1. Skill 概览

### 1.1 名字
**`git-merge-conductor`**——"指挥家"，端到端编排复杂 git 归并。

### 1.2 Skill description（frontmatter，英文）

```
Use when you need to merge / backport / forward-integrate code across branches
in scenarios git cannot 3-way merge cleanly: cross-version backport (deployed
or refactored branch → develop), forward-integrate upstream hotfix into a
feature branch and merge feat back, cherry-pick set across diverged code,
patch/diff application to a moved target, etc. Drives the full flow end-to-end:
branch reconnaissance → mode inference → strategy report → working branch
creation → automatic trivial conflict resolution → method-level conflict
report (terminal markdown + self-contained HTML mirror) → user single-point
decisions → commit. Triggers on phrases like "把 X 合并到 dev"、"backport"、
"归并到主线"、"feature 合 dev 同时带上 dev 的 hotfix"、"跨版本合并"、"patch
应用". Do NOT use for fast-forward merges or single-commit cherry-picks where
plain git handles it cleanly.
```

### 1.3 关键能力对照（用户 a-h 需求映射）

| 用户需求 | skill 能力 |
|---|---|
| a. 明确来源/目标分支 | 模型自动探查 git 状态推断 + 策略报告里一句话确认/纠正 |
| b. `merge/${task-name}` 工作分支 + 基于目标分支指定 commit | Stage 3 自动创建，每步前打 backup tag |
| c. 业务无关冲突 → take target | A/B/C/D 四类规则集（mode-aware，backport 模式自动升级 A 类为「报告而非静默」） |
| d. 业务逻辑冲突 → 高可视化反馈 + 逻辑说明 | 决策点：方法级 diff + 模型双侧改动意图分析 + 5 个候选方案（含自由输入） |
| f. 方法级 diff + 高可视化 | `git diff -W --function-context` + 终端 markdown + 自包含 HTML 镜像（含轻量 JS） |
| g. 三种输入归一化 | Stage 1 探查器接受：分支引用 / .diff / .patch / 任务描述 |
| h. 处理前输出合并策略 | Stage 2 强制策略报告 + 用户一次性确认 gate |

### 1.4 非目标

- 不做 DB 连接，不执行被合并代码的业务逻辑
- 不替代 GUI diff 工具（事后可视化检查仍由你自己用 JetBrains/VSCode）
- 不自动 push、不开 PR（团队规范差异大，止于本地工作分支）
- 不处理 fast-forward 或 git 已能干净合并的简单场景（直接告诉你用原生命令）
- 不处理「需要重写业务逻辑」的场景（那是写代码，不是 merge）
- 不内置 tree-sitter/AST 依赖（v1 选定方案 A，零依赖）

### 1.5 已知约束 / 风险

- 模型对函数边界的识别依赖 `git diff -W` + git 内置 funcname pattern；对未知/小众语言可能不够精确（v1 接受这种损失）
- HTML 报告由模型 prompt 生成，自包含 + 轻量 JS；视觉一致性需用模板兜底
- 语义辅助映射有错判可能；缓解靠"映射依据"可视化 + 决策权在用户

---

## 2. 核心决策日志（brainstorming 沉淀）

| # | 维度 | 选定结论 |
|---|---|---|
| 1 | 角色定位 | **端到端执行者**：模型驱动全流程，把待决冲突逐个抛给用户做单点选择 |
| 2 | merge 形态识别 | **自动识别 + 策略报告阶段一次性确认** |
| 3 | 冲突自动化边界 | **保守智能 + mode-aware**：A 类静默 take target（backport 模式升级为汇报）/ B 类静默 take source / C 类抛人 / D 类标注后抛人 |
| 4 | 跨版本/重构语义 | **语义辅助映射**：识别重命名/搬家/重构后对应符号，给出"建议合并方案 + 映射依据" |
| 5 | 决策点呈现 | **终端 markdown 主交互 + 自包含 HTML 报告作全貌镜像**（允许轻量 JS） |
| 6 | 分发形态 | **单 skill in `/skills/git-merge-conductor/`，兼容 Claude Code + Codex** |

### 2.1 已收敛的默认行为

- **commit 粒度**：按 mode 默认（cherry-pick/backport 保源 commits，整支 merge 保 merge commit，必要时 squash 由用户在策略报告里勾选）
- **出口动作**：止于本地工作分支（不自动 push/PR）
- **失败回滚**：每步打 backup tag，工作分支独立于目标分支，**目标分支永远不被触碰**
- **入口姿势**：自然语言触发为主（skill description 配合），启动后模型自动探查 git status / branches，主动推断源/目标后让用户确认
- **清理策略**：backup tags 默认保留 7 天 + wrap-up 列清单 + 给 3 选项（按 commit 次数 / 永久 / 手动）

---

## 3. 实现方案

### 3.1 v1 选定方案 A：轻量零依赖

- 纯 `SKILL.md` + `references/` + `templates/`，全部逻辑 prompt-driven
- 零外部依赖，拷贝目录即可用
- 方法级 diff 用 `git diff -W --function-context` + 模型识别函数头（git 内置支持 java/python/js/go/rust 等 funcname pattern）
- HTML 报告由模型生成（每决策点 append），自包含 inline CSS + 轻量 vanilla JS（折叠、跳转、高亮）

### 3.2 备选方案（v2+ 演进参考）

- **方案 B**：提炼 helper scripts（Python/Bash）处理机械活（方法级 diff 提取、冲突分类、HTML 渲染），模型只做高层编排和模糊判断
- **方案 C**：引入 tree-sitter AST 解析 + 跨语言精确符号表 + Web UI

v2 优先推进方案 B（用户确认）。

---

## 4. 架构 + 8 阶段流水线

### 4.1 总览图

```
[Stage 0] 入口探测（守卫 + 自动探查）
   ↓ (auto)
[Stage 1] 输入归一化 + 双分支探查
   ↓ (auto)
[Stage 2] 形态推断 + ★合并策略报告★  ─── 用户一次性确认 (gate)
   ↓
[Stage 3] 工作分支创建 merge/${task-name}
   ↓ (auto)
[Stage 4] 源侧改动应用（按 mode 跑 cherry-pick/merge/am/rebase）
   ↓ (auto)
[Stage 5] 冲突分类 + A 类自动处理（backport 模式下转为汇报）
   ↓ (auto, 条件触发)
[Stage 5.5] 语义辅助映射（仅 backport / rebase-onto / 跨版本类）
   ↓
[Stage 6] ★决策点交互循环★ ─── 每个 C/D 类决策点单点确认
   ↓
[Stage 7] 终态化 + commit（按 mode 决定 commit 粒度）
   ↓ (auto)
[Stage 8] 收尾报告 + HTML archive
```

### 4.2 各阶段责任表

| 阶段 | 责任 | 关键 git 命令 / 操作 | 产出 |
|---|---|---|---|
| **0. 入口探测** | 自动跑只读探查，echo 当前状态；触发守卫拦截不合法启动 | 只读 | 终端简报：仓库状态、推断的源/目标候选 |
| **1. 双分支探查 + 输入归一化** | 接收 3 类输入（分支引用 / .diff / .patch / 任务描述）；对每分支跑 `git log/diff --stat`；patch 解析 hunk；任务描述抽取关键词 | 只读 | 内部数据结构：commit 列表、影响文件、关键词集 |
| **2. 形态推断 + 策略报告** | 按 mode-inference 推断 mode；生成策略报告；**用户审核确认 gate** | 只读 | 落盘 `strategy.md` + 终端呈现 |
| **3. 工作分支创建** | `git checkout -b merge/${task} <base-commit>`；写 state.json + decision-log.md；打 tag `before-step-3` | 写：建分支、tag | 工作分支 + 状态文件 |
| **4. 源侧应用** | 按 mode 跑：`cherry-pick --no-commit` / `merge --no-commit --no-ff` / `apply --3way` / `am --3way` / `rebase --onto`；收集 unmerged 列表 | 写：暂存区改动 | unmerged 文件 + hunk 列表 |
| **5. 冲突分类 + 自动处理** | 按 A/B/C/D 规则集分类；A 类应用（backport 模式：不静默，append 到日志）；C/D 类收集到决策点队列 | 写：A 类 hunk 改动 | 决策点队列 |
| **5.5. 语义辅助映射** | 仅在 backport / rebase-onto / 跨版本类 mode 触发。对每个 C/D 决策点：grep/follow rename 搜索源侧符号在 target 的对应；生成"建议合并方案 + 映射依据" | 只读 | 决策点附加 metadata |
| **6. 决策点交互循环** | 逐个抛决策点：终端 markdown + 同步 append 到 merge-report.html；等用户回 1-5 或 abort/pause；应用用户选择 | 写：被选方案应用到暂存区 | 每个决策点 resolved |
| **7. 终态化 + commit** | 按 mode 决定 commit 粒度；commit message 含决策摘要 + 源 reference + 中文说明；打 final tag `done` | 写：commits + tag | 工作分支 ready |
| **8. 收尾报告** | 终端汇总：分支位置、决策分布、HTML 路径、清理建议（3 选项）；HTML 报告 archive 状态 | 写：state 标 finalized | 完整 HTML 报告 + 终端总结 |

### 4.3 状态持久化位置

所有状态文件写在 `.git/merge-conductor/${task-name}/`：

```
.git/merge-conductor/${task}/
├── state.json             # 机器读：完整执行状态
├── decision-log.md        # 人读：时间线日志
├── strategy.md            # Stage 2 输出的策略报告
├── merge-report.html      # 全貌镜像（自包含、可断网开、含轻量 JS）
├── merge-report.js        # （可选）独立 JS 文件，若 HTML 体积过大时拆分
└── patches/               # 若入口含 .patch / .diff 文件，副本留底
```

**为什么写在 `.git/` 下**：不污染工作树、不出现在 `git status`、不会被 commit 进任何分支。用户可放心 `rm -rf` 清理。

### 4.4 Backup tag 策略

每个 Stage 开始前打 tag `merge/${task}/before-step-N`，最终成功打 `merge/${task}/done`。

失败 / 中止：
```bash
git reset --hard merge/${task}/before-step-N   # 回到第 N 步前
git branch -D merge/${task}                     # 完全丢弃
rm -rf .git/merge-conductor/${task}             # 清状态
```

工作分支独立于目标分支，**目标分支永远不被触碰**（直到用户自己 merge 工作分支回去）。

---

## 5. 核心工作流详解

### 5.1 入口契约（Stage 0-1）

**Stage 0 触发后模型立即做**（一次性、只读、并行）：

```bash
git rev-parse --is-inside-work-tree
git status --porcelain
git branch --show-current
git branch -a --sort=-committerdate | head -30
```

终端 echo「我看到的」：当前分支、最近修改分支、未提交改动状态。

**Stage 0 守卫**：

| 触发条件 | 行为 |
|---|---|
| 不在 git repo | 报错并请用户 cd 到 repo |
| 工作树有未提交改动 | 询问「先 stash / 先 commit / 取消」 |
| 已存在同名 `merge/${task-name}` 分支 | 询问「恢复未完成会话 / 删除后重建 / 取消」 |
| 检测到子模块 / LFS | 中止并提示预处理（v1 不支持） |

**Stage 1 输入归一化**——把 3 类输入合成一份「合并任务规约」（merge task spec）：

```yaml
task_name: <从描述抽取或问用户>
sources:
  - type: branch | patch | diff
    ref: feature/x
    commits: [optional commit range]
  - type: patch
    file: hotfix.patch
target:
  branch: develop
  base_commit: <optional, 默认 target HEAD>
intent:
  description: <用户的自然语言需求>
  keywords: [<模型抽取，用于后续相关性判定>]
```

模型在终端展示 spec 让用户 quick-check（不是 gate，下个 Stage 才是 gate）。

### 5.2 策略报告契约（Stage 2，关键 gate）

策略报告 = 处理前的"作战图"。

**输出形式**：终端 markdown + 落盘 `.git/merge-conductor/${task}/strategy.md`。

**模板骨架**（中文，见 `templates/strategy-report.md`）：

```markdown
# 合并策略报告 — {task_name}

## 形态推断
- 推断结果：**{mode}**
- 依据：
  - {signal 1}
  - {signal 2}
- 不确定度：低/中/高（高时列出备选 mode）

## 分支双侧
- 源：{source_ref}（HEAD={sha}，与 target 的 merge-base={sha}）
- 目标：{target_ref}（HEAD={sha}）
- 工作分支：merge/{task}（基于 {base_sha}）

## 影响范围分类
| 文件 | 源侧 +/- | 目标侧 +/- | 相关性 |
|---|---|---|---|
| OrderService.java | +12/-3 | +8/-1 | 核心 |
| .gitignore | +1/-0 | 0 | 边缘 |

## 预估冲突分布
- A 类（自动 take target）：~N 处
- B 类（自动 take source）：~N 处
- C 类（需人决断）：~N 处
- D 类（标注后人决）：~N 处

## 计划执行命令链
1. `git checkout -b merge/{task} {base_sha}`
2. `git cherry-pick --no-commit {commit_a}..{commit_b}`
3. ...

## 你需要确认 / 可调整
- [ ] mode 推断对吗？
- [ ] 工作分支名 / 基准 commit OK 吗？
- [ ] 是否允许"语义辅助映射"（Stage 5.5）？默认开启
- [ ] commit 粒度偏好：保留源 commits / squash 单 commit / 按主题重组
- [ ] 锁定 take target 或 take source 的特定文件？（如"lock 文件统一 take target"）
```

**用户回复方式**：

- 「策略 OK」→ 继续 Stage 3
- 「mode 错了，应该是 cherry-pick-set」→ 模型纠正后重出报告
- 自由文本调整 → 模型解析应用，重出关键变化部分复核

### 5.3 各 mode 的命令链（Stage 4）

| mode | 触发信号 | 命令链 |
|---|---|---|
| **full-merge** | 源是活跃分支、commit 数多、无指定 commit 范围 | `git merge --no-commit --no-ff <source>` |
| **cherry-pick-set** | 用户指定 commit 范围 / 只挑几个 commit | `git cherry-pick --no-commit <A>..<B>` |
| **backport** | 源是老/部署/重构分支、merge-base 远 | 同 cherry-pick-set + Stage 5 backport 模式 + Stage 5.5 强制开启 |
| **forward-integrate** | 「先把 dev 的 fix 带进 feature 再 merge 回」 | 两阶段：① 在 feature 上 `git merge dev` 引入 fix；② `git checkout merge/{task} && git merge feature` |
| **patch-apply** | 输入含 .patch / .diff 文件 | `git am --3way < patch` 或 `git apply --3way patch` |
| **rebase-onto** | feature 长期落后于重构后的 main | `git rebase --onto <new-base> <old-base> <source>` |

**所有 mode 共通约束**：

- 用 `--no-commit` 把 commit 控制权留给 Stage 7
- 冲突收集：`git diff --name-only --diff-filter=U`
- 跑前 Stage 3 已建好工作分支

### 5.4 决策点契约（Stage 6）

**终端呈现**（templates/decision-point.md，中文）：

```markdown
─────────────────────────────────────────────
决策点 [3 / 7]：src/service/OrderService.java::calcDiscount()
分类：C 类（双侧均修改同一方法体逻辑）

▼ 源侧改动（feature/promo-v2 @ a1b2c3d）
@@ -45,7 +45,10 @@ public BigDecimal calcDiscount(Order order) {
  BigDecimal base = order.getAmount().multiply(RATE);
+ if (order.isVip()) {
+     base = base.add(VIP_BONUS);
+ }
  return base;

▼ 目标侧改动（develop @ x9y8z7w）
@@ -45,7 +45,10 @@ public BigDecimal calcDiscount(Order order) {
  BigDecimal base = order.getAmount().multiply(RATE);
+ Coupon c = couponService.find(order.getUserId());
+ if (c != null) base = base.subtract(c.value);
  return base;

▼ 模型分析
- 源侧意图：为 VIP 用户加 VIP_BONUS 加成
- 目标侧意图：应用用户已有优惠券抵扣
- 冲突点：两侧都在 base 计算后追加调整，维度不同（加成 vs 抵扣）
- 是否相互独立：✅ 语义正交，可叠加
- 语义映射：无（同方法、同位置）

▼ 候选方案
[1] take source：仅保留源侧改动
[2] take target：仅保留目标侧改动
[3] source-first-then-target：先保留源侧，后合并目标
[4] target-first-then-source：先保留目标侧，后合并源侧
[5] 自由输入：用一句话描述你的合并意图，模型解析后回显「我理解为...」请你二次确认

▼ 模型建议：[3]
依据：源侧是新增需求，目标侧是已上线规则；新需求应叠加在已上线规则之上

回复 1/2/3/4/5（5 为自由文本）
其它指令：[s] 跳过本点暂存到末尾  [p] 暂停退出（下次可恢复）  [a] 中止整个合并
─────────────────────────────────────────────
```

**HTML 报告同步**：每个决策点写入 `merge-report.html` 对应 `<article>` 节点（带 ID anchor），用户选择实时回填到 HTML 的状态字段。

**5 个候选方案的语义约定**：

| # | 名 | 含义 |
|---|---|---|
| 1 | take source | 仅保留源侧改动 |
| 2 | take target | 仅保留目标侧改动 |
| 3 | source-first-then-target | 先放源侧改动，再叠加目标侧（执行顺序/文本位置） |
| 4 | target-first-then-source | 先放目标侧改动，再叠加源侧 |
| 5 | 自由输入 | 用户描述合并意图，模型解析后回显「我理解为...」请用户二次确认 |

**Stage 5.5 触发的决策点**多一节「映射依据」：

```markdown
▼ 语义映射依据
- 源侧改动 `OrderService.calcDiscount()`
- 目标侧已被重构：方法迁移到 `DiscountStrategy.apply()`（commit f0e1d2c）
- 映射置信度：高（方法签名一致 + 历史 trail 完整）
- 候选方案 [3]/[4] 已基于映射重写到 `DiscountStrategy.apply()` 位置
```

### 5.5 Commit 契约（Stage 7）

**Commit message 格式**（templates/commit-message.md，按用户规则 5）：

```
merge: <中文说明本 commit 做了哪些事情>

源: <source_ref>@<sha>（或 patch 文件名）
mode: <inferred-mode>
决策摘要:
- [src/service/OrderService.java::calcDiscount #3] 合并版本 source-first-then-target：融合 VIP 加成与优惠券抵扣
- [src/controller/OrderController.java::create #5] take source：移除目标侧旧实现
A 类自动处理: N 处（详见 .git/merge-conductor/${task}/decision-log.md）
```

**Commit 粒度按 mode 默认 + Stage 2 可覆盖**：

| mode | 默认 commit 粒度 |
|---|---|
| full-merge | 单 merge commit（message 用 `merge: ...` 覆盖默认） |
| cherry-pick-set / backport | 逐 commit cherry-pick（保留源 SHA 追溯），每个 message 改写为 `merge: <对应源 commit 主题>` |
| forward-integrate | 单 merge commit |
| patch-apply | 单 commit（除非 `git am` 自带多 commit） |
| rebase-onto | 逐 commit rebase |

Stage 2 勾选「squash 单 commit」可覆盖所有 mode 默认。

### 5.6 收尾契约（Stage 8）

**终端汇总**（templates/wrap-up-report.md，中文）：

```markdown
# 合并完成 — {task_name}

## 概要
- 形态：{mode}
- 工作分支：merge/{task}（HEAD = {sha}）
- 决策点：{resolved}/{total} 已解决，{skipped} 跳过
- 自动处理：A 类 {A_count} 处，B 类 {B_count} 处

## 决策亮点
{top 5 most impactful decisions, summarized}

## 报告位置
- 全貌 HTML（可浏览器打开）：`{repo_root}/.git/merge-conductor/{task}/merge-report.html`
- 决策日志（人读）：`{repo_root}/.git/merge-conductor/{task}/decision-log.md`
- 机器状态：`{repo_root}/.git/merge-conductor/{task}/state.json`

## 下一步建议
1. 复核：`git diff {target}..merge/{task}`
2. 在 JetBrains / VSCode 里打开工作分支做事后可视化检查
3. 满意后合并：`git checkout {target} && git merge merge/{task}`
4. 推送 / 开 PR 按团队规范自决

## 清理建议（满意后）
本次合并产生的可清理资产：
- 工作分支：`merge/{task}`
- 状态目录：`.git/merge-conductor/{task}/`（含 HTML 报告 / state.json / decision-log）
- backup tags：`merge/{task}/before-step-*` 共 N 个
- final tag：`merge/{task}/done`

请选择清理策略：
[1] 默认：backup tags 保留 7 天后自动清理（运行 skill 时检查并清理过期 tag）
[2] 按 commit 次数：保留最近 5 次合并的状态与 tags
[3] 永久保留：什么都不清理，全部留档
[4] 手动决定：现在告诉你清理命令，由你自己决定何时跑

选 [1] 后，本次清理仅清理超过 7 天的旧合并；本次合并资产将在 {now+7d} 后被清理。
```

---

## 6. References 规则集（英文，给模型）

按用户规则 4 + 在用户确认下扩展为完整规则集逐条列出。

### 6.1 `references/mode-inference.md`

**Purpose**: Given a merge task spec from Stage 1, output the inferred mode with confidence + alternatives + evidence.

**Input** (yaml from Stage 1): merge task spec
**Output** (yaml):

```yaml
mode: backport
confidence: high | medium | low
alternatives:  # only when confidence != high
  - mode: cherry-pick-set
    reason: "explicit commit range provided by user"
evidence:
  merge_base_age_days: 35
  source_commit_count: 8
  patch_files_present: false
  target_diverged_commits_since_merge_base: 142
  keyword_signals: ["回灌", "backport"]
  refactor_signals_in_target: true
```

**Decision tree**:

```
1. If sources contain any .patch or .diff files → patch-apply
2. Elif description contains "rebase onto" OR "feature 长期落后" OR "重构后的 main" → rebase-onto
3. Elif description matches "先把 X 的 fix 带进 Y 再 merge 回" pattern → forward-integrate
4. Elif user provided explicit commit range OR source_commit_count ≤ 5 → cherry-pick-set
5. Elif merge_base_age_days > 30 OR keyword in {"回灌", "backport", "跨版本"} OR target has refactor signals (renamed files in source's modified file set) → backport
6. Elif source is active branch (committed in last 7d) AND no commit range → full-merge
7. Else → low confidence, default to cherry-pick-set with alternatives [full-merge, backport]
```

**Refactor signal detection**:
- For each file modified on source side, run `git log --follow --diff-filter=R -- <file>` on target
- If ≥1 rename detected within target's history since merge-base → refactor_signals_in_target = true

**Confidence scoring**:
- **high**: ≥ 2 strong signals point to same mode AND no contradicting signals
- **medium**: 1 strong signal + no contradicting signals
- **low**: contradicting signals OR weak signals only → list alternatives in strategy report

### 6.2 `references/conflict-classification.md`

**Purpose**: For each unmerged hunk, classify as A/B/C/D class.

**Input**: One unmerged hunk (source side / target side / merge-base三方文本) + mode + task keywords + locked_file_rules (from Stage 2 user input)
**Output**: classification = A | B | C | D + reason + (for A class) applied action

#### A Class · silent take target

Applied silently in full-merge / forward-integrate / cherry-pick-set / patch-apply / rebase-onto modes.
**Demoted to `log-then-take-target`** in backport mode（仍 take target, but written to decision-log + summary, not silent）.

**A.1 — Pure whitespace / EOL diff**
- Detection: `git diff --ignore-all-space --ignore-blank-lines` produces empty diff for this hunk
- Action: take target side via `git checkout --theirs <file>` (or per-hunk apply)

**A.2 — Pure comment-only changes**
- Detection: All added/removed lines match comment syntax for the file's language
  - Java/JS/TS/Go/Rust/C/C++: lines start with `//` or wrapped in `/* */`
  - Python/Shell/Ruby: lines start with `#`
  - SQL: lines start with `--`
  - HTML/XML: lines wrapped in `<!-- -->`
- Exclusion: lines containing code followed by inline comment do NOT count
- Action: take target side

**A.3 — Import / using statement reorder**
- Detection: All added/removed lines are import statements; set of imported deps is identical, only ordering changed
- Language-specific patterns:
  - Java: `^import\s+.+;$`
  - Python: `^(import |from )`
  - JS/TS: `^import\s+.+\s+from\s+`
  - C#: `^using\s+`
  - Go: lines inside `import (...)` block
  - Rust: `^use\s+`
- Action: take target side (respect target's import ordering)

**A.4 — Code formatting (no semantic change)**
- Detection: `git diff --ignore-all-space --ignore-blank-lines` after hunk is empty AND only punctuation/brace position changed
- Includes: semicolon add/remove, brace placement, indentation, intra-line whitespace
- Action: take target side

**A.5 — Pure local variable rename**
- Heuristic detection:
  - Rename confined to a single method body
  - No signature change
  - No method/class name change
  - Model prompt: judge "is this hunk purely a local variable rename?"
- Action: take target side
- Note: this is heuristic and may miss; if uncertain → escalate to C class

#### B Class · silent take source (auto-resolved by git 3-way merge)

These do NOT produce unmerged state in standard git; only included for completeness in statistics.

- **B.1**: Source modified hunk where target untouched
- **B.2**: Source added new symbol (class / method / file) absent in target

skill 只需在策略报告 + decision-log 里记录"B 类已自动 take source 共 N 处"。

#### C Class · require human decision

**C.1 — Same method body, both sides logic change**
- Detection: both source and target modified hunks overlap within the same method (identified by `git diff -W` function context)
- Action: collect into decision queue, no auto-apply

**C.2 — Same expression / constant value, both sides change**
- Detection: same line(s) modified on both sides with different content (excluding whitespace/comment differences)
- Action: collect into decision queue

**C.3 — Incompatible signature change**
- Detection: method/function signature modified on both sides differently (param list / return type / annotations)
- Action: collect into decision queue with `signature_conflict: true` flag (will be highlighted in decision point)

#### D Class · flag + require human decision

**D.1 — Symbol removed by one side, modified/depended on by other side**
- Detection: source modifies a symbol that target deleted (or vice versa); detect via `git log --diff-filter=D` for deleted symbols
- Action: collect with `[需注意：单侧删除]` flag

**D.2 — Both sides modified imports**
- Detection: both sides added/removed different deps in import block
- Action: collect with `[需注意：依赖差异]` flag

**D.3 — Rename tracking ambiguity**
- Detection: `git diff -M --find-renames` similarity score borderline (50-70%)
- Action: collect with `[需注意：rename 追踪不确定]` flag + show both possible rename pairs

**D.4 — Binary file conflict**
- Detection: file is binary (per `.gitattributes` or git's heuristic)
- Action: collect with `[需注意：二进制]` flag; only options [1] take source / [2] take target available (no merge variant)

**D.5 — Hunk in file with detected refactoring**
- Detection: file appears in `refactor_signals` set (from mode-inference Stage 2)
- Action: collect with `[需注意：目标侧有重构]` flag + trigger Stage 5.5 semantic mapping for this hunk

**D.6 — (patch-apply only) Patch context mismatch**
- Detection: patch context lines off by > 5 from target file
- Action: collect with `[需注意：patch 上下文偏差]` flag + show context drift

#### Locked file rules (user input in Stage 2)

User can specify in Stage 2 confirmation:
- `lock_take_target: ["*.lock", "package-lock.json", "yarn.lock"]`
- `lock_take_source: ["docs/**"]`

These override classification for matching files (apply lock action regardless of A/B/C/D classification).

### 6.3 `references/semantic-mapping.md`

**Trigger**: Only in `backport`, `rebase-onto`, or any mode with `refactor_signals_in_target: true`. Run for each C/D class hunk in Stage 5.5.

**Goal**: For each conflict hunk, search target branch for "the refactored counterpart" of source-side modified symbols.

**Search strategy**:

1. **Extract source-side modified symbols** (per hunk):
   - methods/functions: name + signature
   - classes/types: name + key members
   - constants: name + value

2. **For each symbol, run candidate searches** (in order):
   - **Direct grep** on target HEAD: `git grep -n "<symbol_name>" -- '*.{ext}'`
   - **Rename trail**: `git log --all --follow --diff-filter=R -- <original_file>` to find rename history
   - **Cross-file rename**: for each file modified on source, run `git log --all --diff-filter=R --find-renames=70%`
   - **Similar-signature heuristic**: search target for methods with same param types/return type, within neighboring files (proximity by directory)

3. **Score mapping confidence**:
   - **high**: direct grep hit + signature unchanged + same calling context
   - **medium**: rename trail follows + signature similar but changed
   - **low**: similar-signature heuristic match only OR multiple candidates

4. **Attach mapping evidence** to decision point metadata.

**Output schema** (per decision point):

```yaml
semantic_mapping:
  source_symbols:
    - name: OrderService.calcDiscount
      type: method
      signature: "BigDecimal calcDiscount(Order)"
  target_counterpart:
    - source: OrderService.calcDiscount
      mapped_to: DiscountStrategy.apply
      confidence: high
      evidence: "renamed in commit f0e1d2c; signature preserved; same caller chain (OrderController.create)"
  suggested_merged_version_A: |
    // [3] source-first-then-target, rewritten on target's DiscountStrategy.apply
    public BigDecimal apply(Order order) {
        BigDecimal base = order.getAmount().multiply(RATE);
        if (order.isVip()) base = base.add(VIP_BONUS);  // from source
        Coupon c = couponService.find(order.getUserId());
        if (c != null) base = base.subtract(c.value);    // from target
        return base;
    }
  suggested_merged_version_B: |
    // [4] target-first-then-source
    ...
```

**Low-confidence handling**: When confidence = low, still present the mapping in decision point but mark with `⚠ 映射置信度低，请人工校验`. Do NOT auto-apply.

### 6.4 `references/html-report-template.md`

**Purpose**: Define the structure of `merge-report.html` (the full-view mirror written alongside terminal interactions).

**Constraints (updated per user feedback)**:

- Self-contained: inline CSS + inline JS (or sibling `.js` if size > 200KB)
- **Allow vanilla JS for**: section folding, decision-point jump links, syntax highlighting, real-time selection state styling
- No external resources (CDN, fonts, images)
- Offline-openable, printable
- Append-mode writes: each new decision point appended as a new `<article>`; status updates rewrite in-place

**Skeleton**:

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <title>合并报告 — {{task_name}}</title>
  <style>
    /* inline CSS: monospace diff, code highlighting, decision state colors */
    body { font-family: -apple-system, sans-serif; max-width: 1200px; margin: 2em auto; padding: 0 1em; }
    pre { font-family: ui-monospace, monospace; background: #f6f8fa; padding: 1em; overflow-x: auto; }
    code.added { background: #e6ffec; }
    code.removed { background: #ffebe9; }
    article.decision { border: 1px solid #d0d7de; border-radius: 6px; margin: 1em 0; padding: 1em; }
    article.decision.pending { border-left: 4px solid #fb8500; }
    article.decision.resolved { border-left: 4px solid #2da44e; }
    article.decision.skipped { border-left: 4px solid #6e7781; }
    .selected { background: #ddf4ff; font-weight: bold; }
    nav.toc { position: sticky; top: 0; background: white; padding: 0.5em 0; border-bottom: 1px solid #eee; }
    /* ... */
  </style>
</head>
<body>
  <header>
    <h1>合并报告 — {{task_name}}</h1>
    <dl>
      <dt>形态</dt><dd>{{mode}}</dd>
      <dt>源</dt><dd>{{source_ref}}@{{source_sha}}</dd>
      <dt>目标</dt><dd>{{target_ref}}@{{target_sha}}</dd>
      <dt>工作分支</dt><dd>merge/{{task_name}}（基于 {{base_sha}}）</dd>
      <dt>状态</dt><dd id="overall-status">{{status}}</dd>
    </dl>
  </header>

  <nav class="toc">
    <a href="#strategy">策略</a> ·
    <a href="#auto-resolved">自动处理</a> ·
    <a href="#decisions">决策点 (<span id="decisions-count">{{resolved}}/{{total}}</span>)</a>
  </nav>

  <section id="strategy"><h2>合并策略报告</h2>{{strategy_html}}</section>

  <section id="auto-resolved">
    <h2>A 类自动处理（{{a_count}} 处）</h2>
    <details><summary>展开查看明细</summary>{{auto_table}}</details>
  </section>

  <section id="decisions">
    <h2>决策点</h2>
    <article id="decision-3" class="decision c-class resolved" data-decision-id="3">
      <h3>决策点 3 · src/service/OrderService.java::calcDiscount()</h3>
      <p class="meta">分类：C 类 · 状态：<span class="status">✅ 已解决</span></p>
      <div class="diff-pair">
        <div class="source-diff"><h4>源侧改动</h4><pre><code class="lang-java">...</code></pre></div>
        <div class="target-diff"><h4>目标侧改动</h4><pre><code class="lang-java">...</code></pre></div>
      </div>
      <div class="model-analysis">...</div>
      <ol class="options">
        <li>take source</li>
        <li>take target</li>
        <li class="selected">source-first-then-target ★</li>
        <li>target-first-then-source</li>
        <li>自由输入</li>
      </ol>
      <div class="user-choice">用户选择：3</div>
      <div class="free-text-explanation" hidden>{{free_text_echo}}</div>
    </article>
  </section>

  <footer><p>报告生成于 {{generated_at}} · skill version v1</p></footer>

  <script>
    // vanilla JS, ≤ 100 lines:
    // - smooth scroll to anchor
    // - keyboard shortcut (j/k) to jump between decisions
    // - update sticky TOC counts on decision state change
    // - collapsible long diffs (auto-collapse if > 80 lines)
  </script>
</body>
</html>
```

**Write semantics**:
- Stage 2 → write skeleton + strategy section
- Stage 5 → append auto-resolved summary
- Stage 6 → append each decision article as pending, rewrite class to resolved/skipped on user choice
- Stage 8 → finalize footer status

### 6.5 `references/state-schema.md`

```json
{
  "version": "1.0",
  "task_name": "promo-vip-backport",
  "mode": "backport",
  "created_at": "2026-05-11T14:00:00+08:00",
  "paused_at": null,
  "finalized_at": null,
  "status": "in-progress",
  "source": {
    "type": "branch",
    "ref": "feature/promo-v2",
    "sha": "a1b2c3d",
    "merge_base_with_target": "x0y0z0w"
  },
  "target": {
    "branch": "develop",
    "head_sha": "x9y8z7w",
    "base_sha": "x9y8z7w"
  },
  "working_branch": "merge/promo-vip-backport",
  "stage": 6,
  "stage_history": [
    { "stage": 3, "tag": "merge/promo-vip-backport/before-step-3", "completed_at": "2026-05-11T14:05:00+08:00" },
    { "stage": 4, "tag": "merge/promo-vip-backport/before-step-4", "completed_at": "2026-05-11T14:08:00+08:00" }
  ],
  "decisions": [
    {
      "id": 1,
      "file": "src/service/OrderService.java",
      "symbol": "calcDiscount",
      "class": "C",
      "status": "resolved",
      "choice": 3,
      "free_text": null,
      "model_recommendation": 3,
      "semantic_mapping": { "mapped_to": "DiscountStrategy.apply", "confidence": "high" },
      "resolved_at": "2026-05-11T14:15:00+08:00"
    },
    {
      "id": 2,
      "status": "skipped",
      "skip_reason": "deferred to end"
    }
  ],
  "auto_resolved_summary": {
    "A_count": 14,
    "B_count": 22,
    "A_files": ["..."],
    "demoted_A_in_backport_mode": ["..."]
  },
  "config": {
    "commit_granularity": "preserve-source-commits",
    "semantic_mapping_enabled": true,
    "locked_file_rules": {
      "take_target": ["*.lock", "package-lock.json"],
      "take_source": []
    }
  },
  "cleanup_policy": "default-7d"
}
```

**Validation rules**:
- `stage` must match the most recent entry in `stage_history`
- `working_branch` must exist in git (validated on resume)
- `source.sha` and `target.head_sha` must still exist (otherwise force-push detected, refuse to resume)

### 6.6 `references/recovery-protocol.md`

| Scenario | Detection | Action |
|---|---|---|
| Session interrupted (terminal closed) | Next invocation finds `state.json` with `status: in-progress` and no recent activity | Prompt 中文：「检测到未完成会话 (task=X, paused at stage=Y)，要恢复 / 丢弃重来 / 仅查看状态？」 |
| Git command failure mid-stage | Non-zero exit from git op | Roll back to `before-step-N` tag automatically, report error to user 中文, ask: 重试 / 调整策略后重试 / 中止 |
| User typed `[p]` in Stage 6 | Inline command | Save state with `status: paused`, write summary to decision-log, exit gracefully |
| User typed `[a]` in Stage 6 | Inline command | Confirm 中文「将丢弃工作分支和状态目录，确定？」→ on yes: `git checkout target && git branch -D merge/${task} && rm -rf .git/merge-conductor/${task}` |
| Model unrecoverable error | Internal exception | Save state with `status: error`, print recovery instructions 中文 |
| Force-pushed source branch during process | On resume, `source.sha` not found in `git rev-list` | Refuse resume, instruct user to abort and restart |
| Existing same-name working branch on startup | Stage 0 守卫 | Prompt 中文：「检测到同名 merge/X 分支，要恢复未完成会话 / 删除后重建 / 取消？」 |

**Resume flow**:

1. Read `state.json`
2. Reconstruct in-memory context (mode, decisions list, current decision queue position)
3. Verify git state matches expected:
   - Working branch exists
   - Last `before-step-N` tag exists
   - `source.sha` resolvable
4. If verification fails → fall back to "manual intervention required" with diagnostic info dump
5. Else → resume from `stage` field

**Cleanup runs**:
- On every skill invocation: scan `.git/merge-conductor/*/` for `status: finalized` with `finalized_at > 7d ago` → delete according to `cleanup_policy`
- Cleanup policies:
  - `default-7d`: delete state dir + backup tags after 7 days
  - `last-N`: keep most recent N finalized merges
  - `permanent`: never auto-clean
  - `manual`: never auto-clean, print cleanup commands at wrap-up

---

## 7. Templates 中文呈现规范

按用户规则 3 + 4：templates 骨架包含「英文 placeholder（给模型）+ 中文固定字符串（给用户）」。

| 文件 | 用途 | 主要语言 |
|---|---|---|
| `templates/strategy-report.md` | Stage 2 策略报告 | 中文（见 §5.2） |
| `templates/decision-point.md` | Stage 6 决策点 | 中文（见 §5.4，5 项候选方案） |
| `templates/commit-message.md` | Stage 7 commit message | 中文（`merge: 中文说明`，见 §5.5） |
| `templates/wrap-up-report.md` | Stage 8 收尾报告 | 中文（含 4 项清理策略选项，见 §5.6） |

每个 template 文件内部约定：

- placeholder 用 `{{var_name}}` 形式（英文 var name）
- 固定文本用中文
- 模板顶部用英文注释说明「what fields to fill, where this template is used」

---

## 8. 失败 / 中止 / 恢复（完整协议）

见 §6.6 `recovery-protocol.md`。

**关键不变量**：

1. **目标分支永远不被触碰** — 所有写操作仅发生在 `merge/${task}` 工作分支
2. **每个 Stage 前必打 backup tag** — 失败可回任意 Stage
3. **状态在 `.git/merge-conductor/${task}/`** — 不污染工作树、可放心丢弃
4. **用户可随时 `[p]` pause / `[a]` abort** — 无副作用退出

---

## 9. 验收标准

### 9.1 MVP v1 必须跑通的 5 个场景

| 场景 | 输入 | 期望行为 |
|---|---|---|
| **A. 用户场景 2：feature → dev + 期间 hotfix** | feature 分支（拉出时 dev 在 X，期间 dev 在 Y 修复同模块 bug） | mode = `forward-integrate`；两阶段执行；C 类决策点呈现 fix 与新需求融合方案；commit 含融合记录 |
| **B. 用户场景 1：跨版本 backport** | 部署分支/重构分支的某功能 → develop（差异 X 月、含重构） | mode = `backport`；Stage 5.5 触发；策略报告标注高置信映射；cherry-pick 保留源 commits；message 改写 `merge: <中文>` |
| **C. 纯 patch-apply** | 一个 .patch 文件 + target 分支 | mode = `patch-apply`；用 `git am --3way`；冲突走完整决策流程 |
| **D. 中断 / 恢复** | 跑到 Stage 6 第 3 决策点时用户 `[p]` | state.json 写明 stage=6 + 已解决/待决分布；下次启动检测并提示恢复 |
| **E. 守卫** | 工作树有未提交改动时启动 | Stage 0 拦截，问 stash/commit/取消 |

### 9.2 通用形式契约（所有场景必须满足）

- 整流程不抛 unhandled 异常
- HTML 报告自包含、可断网开
- backup tags 按计划完整
- 最终 commit 符合 `merge: 中文说明` 格式
- **工作分支独立于目标分支，目标分支零改动**
- state.json 字段完整，可被 resume 流程消费
- decision-log.md 时间线连续，可作为人读 audit trail

---

## 10. 已知边界（v1 不处理）

| 边界 | 处理 |
|---|---|
| 二进制冲突 | 仅检测 + 标 D 类，提示用户在 JetBrains 处理 |
| 子模块 (.gitmodules) | 中止 + 提示预处理 |
| LFS 文件 | 同上 |
| 三方及以上合并（多源） | v1 仅 单源→单目标，多源视为多个串行任务 |
| 非 UTF-8 编码 | 走 git 默认，终端可能乱码（HTML 报告正常） |
| 跨仓库 merge（subtree / monorepo split） | v1 不处理 |
| force-pushed source 期间改写 history | state.json SHA 校验失败 → 要求用户重启 |
| Fast-forward 可直解的简单 merge | skill 拒绝接收，echo 原生命令让用户自跑 |

---

## 11. 演进路径

### 11.1 v2 优先：Helper scripts（方案 B 演进，用户选定）

把以下机械活提炼到 `scripts/`：

| 候选脚本 | 职责 | 触发提炼信号 |
|---|---|---|
| `scripts/method_diff.py` | 用 `git diff -W` + 后处理，输出稳定的方法级 diff 结构 | 模型在 prompt 里反复识别函数边界出错 |
| `scripts/classify_conflict.py` | 按 §6.2 规则集判定 A/B/C/D 类 | 模型分类不一致或漏类 |
| `scripts/render_html_report.py` | 模板化渲染 merge-report.html，避免模型手写 HTML 不稳 | HTML 结构破损或大文件时模型 token 消耗高 |
| `scripts/state_manager.py` | state.json 读写 + validation | state 校验/恢复出错 |

提炼后 SKILL.md 的 prompt 链显著缩短，模型只负责：

- 高层编排（推断 mode、决定走哪个 sub-flow）
- 语义判断（A.5 局部 rename 启发、C/D 类边界判定的模糊情况）
- 用户交互（策略报告呈现、决策点抛出、自由文本解析）
- 语义辅助映射（Stage 5.5 的 grep/follow rename 搜索）

### 11.2 后续候选

| 候选 | 触发信号 | 估计代价 |
|---|---|---|
| Tree-sitter AST 解析 | 跨语言、大文件精度不够 | 大 |
| 多源合并 | 用户要求 2+ 源并入同一目标 | 中 |
| PR 描述自动生成 + 自动 push | 用户要求合并后直接开 PR | 小 |
| 合并知识库（同 repo 历史决策复用） | "上次你这模块这样选" | 中 |
| Web UI（方案 C） | 终端 + HTML 不够用 | 大 |

---

## 12. 文件结构

```
skills/git-merge-conductor/
├── SKILL.md                              # 主入口 + 8 阶段编排（英文，约 800-1200 行）
├── references/
│   ├── mode-inference.md                 # §6.1 形态推断决策树
│   ├── conflict-classification.md        # §6.2 A/B/C/D 规则集
│   ├── semantic-mapping.md               # §6.3 Stage 5.5 探查策略
│   ├── html-report-template.md           # §6.4 HTML + JS 模板
│   ├── state-schema.md                   # §6.5 state.json 字段定义
│   └── recovery-protocol.md              # §6.6 失败/中止/恢复协议
└── templates/
    ├── strategy-report.md                # §5.2 策略报告（中文）
    ├── decision-point.md                 # §5.4 决策点（中文，5 候选方案）
    ├── commit-message.md                 # §5.5 commit message（中文，`merge:` 前缀）
    └── wrap-up-report.md                 # §5.6 收尾汇总（中文，含清理 4 选项）
```

运行时 state（不在 skill 仓库，而在使用 skill 的目标 repo 的 `.git/`）：

```
<target-repo>/.git/merge-conductor/${task-name}/
├── state.json
├── decision-log.md
├── strategy.md
├── merge-report.html
├── (merge-report.js)         # 可选拆分文件
└── patches/
```

---

## 13. 语言约定（汇总）

按用户规则 1-5：

| 内容 | 语言 |
|---|---|
| 本 design 文档 | **中文为主**，技术名词保留英文（v1 定稿） |
| `SKILL.md` frontmatter + body | **英文**（干练精准、节省 token） |
| `references/*.md` 主体（给模型看的 prompt/规则/schema） | **英文** |
| `templates/*.md` 中给用户呈现的固定文本 | **中文** |
| `templates/*.md` 中的 placeholder 和模板说明 | **英文** |
| 模型运行时给用户的进度提示 / 思考反馈 / 选项呈现 | **中文** |
| 模型运行时的内部 prompt / 约束 / 流程指令（用户不直接看到） | **英文** |
| skill 产生的 commit message | **`merge: 中文说明`** |
| HTML 报告中可见的文字 | **中文**（`<html lang="zh-CN">`） |
| HTML 报告中的注释、CSS 类名、JS 变量名 | **英文** |
| commit message 的 trailing fields（源/mode/决策摘要/A 类自动处理） | **中文字段名** |

---

## 14. 测试样例 / fixtures（写入 spec 附录）

实际写测试代码不在 design 阶段，只列「验证场景的 fixture 构造方案 + expected outputs 的 shape」。

### 14.1 Fixture toy repo 构造

构造一个有以下结构的 mock repo：

- `main`：基线
- `develop`：从 main 拉出，含若干 commits
- `feature/promo-v2`：从 main 拉出，含若干迭代 commits，含一个会触发冲突的方法改动
- `release/v1.0`（部署分支）：从 main 早期 commit 拉出，含已上线功能
- `refactor/v2.0`：从 main 拉出，把 `OrderService.calcDiscount` 重命名为 `DiscountStrategy.apply`

构造脚本（伪代码）：

```bash
mkdir merge-conductor-fixture && cd merge-conductor-fixture
git init
# 创建初始 OrderService.java
git commit -m "init: OrderService"
git branch develop
git branch -c develop release/v1.0
# 在 release/v1.0 上加 VIP_BONUS 功能
# 在 develop 上加优惠券抵扣
# 在 refactor/v2.0 上重命名为 DiscountStrategy
```

### 14.2 Expected output shape（每个场景）

每个验收场景的 expected output 由以下要素组成：

- `state.json` 最终字段：mode、stage、status、decisions[].class/status/choice 数量分布
- 最终 commit 数量 + commit message regex（必须含 `^merge: .+` 中文部分）
- 工作分支 git log shape：linear / merged / cherry-picked
- HTML 报告 DOM 关键元素存在性：`<section id="strategy">`、`<article class="decision resolved">` × N
- target 分支零改动（`git diff <target>@before <target>@after == empty`）

---

## 附录 A：Brainstorming Q&A 完整记录

| Q | 决定 |
|---|---|
| Q1 | 角色定位 = **端到端执行者**：模型驱动全流程，把待决冲突逐个抛给用户做单点选择 |
| Q2 | 形态识别 = **自动识别 + 策略报告阶段一次性确认** |
| Q3 | 冲突边界 = **保守智能 + mode-aware**（A/B/C/D 四类规则） |
| Q4 | 语义映射 = **语义辅助映射**，含映射依据 |
| Q5 | 决策点呈现 = **终端 + HTML 报告镜像**（允许轻量 JS） |
| Q6 | 形态 = **单 skill in `/skills/git-merge-conductor/`，双 runtime** |

## 附录 B：用户规则附加约束

| # | 规则 |
|---|---|
| 1 | design 文档保留中文 v1 定稿 |
| 2 | SKILL.md 主内容英文（干练精准） |
| 3 | 给用户呈现的 references/templates 中文 |
| 4 | 不直接给用户看的模型 prompt / 约束 / 规则 / schema 英文 |
| 5 | skill 产生的 commit 统一格式：`merge: 中文说明` |

## 附录 C：默认行为汇总（速查表）

| 项 | 默认 |
|---|---|
| 工作分支命名 | `merge/${task-name}` |
| 工作分支基准 | target HEAD（Stage 2 可改） |
| commit 粒度 | 按 mode 默认（Stage 2 可勾选 squash 覆盖） |
| 出口动作 | 止于本地工作分支（不 push / 不 PR） |
| 语义辅助映射 | backport / rebase-onto 自动开；其它 mode 默认关 |
| backup tags 清理 | 默认 7 天（wrap-up 给 4 选项覆盖） |
| HTML 报告 JS | 允许 inline vanilla JS ≤ 100 行 |
| Stage 0 守卫 | 不在 repo / dirty work tree / 同名分支 / 子模块 / LFS / 二进制 → 中止或询问 |
| 失败回滚 | 自动回到 `before-step-N` tag，报错后询问用户 |

---

文档版本：v1（2026-05-11 初版）
下一步：交付用户复核 → 进入 writing-plans 阶段生成实现计划。
