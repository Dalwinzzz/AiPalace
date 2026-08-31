# 个人工作流实施计划 — 2026-05-26

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 2026-05-25 个人工作流设计 spec 落到本机文件系统，分 4 阶段（memory seed → hooks/wrap → 来源迁移 → 模板推迟），每阶段独立可验证、独立可回滚。

**Architecture:** 改动分布在三个 namespace —— `~/.claude/`（memory + hooks + settings + commands）、`~/.agents/skills/` & `~/Library/CodeRepo/AI/`（skills 来源单源化）、`~/Documents/AI/dalwin-workflow/`（spec + 实施日志 + archive 索引）。前两者**不在 git 仓库内**，只通过 `~/Documents/AI/` repo 里的实施日志承担"frequent commits"。

**Tech Stack:** Python 3 stdlib（hooks）、JSON（settings.json）、Markdown（memory & slash command & 实施日志）、Bash（迁移与验证）。

---

## Spec 覆盖映射

| Spec 节 | 实施位置 |
|---|---|
| §3.2 15 条 seed | Phase 1（4 个 task：user / feedback / project / reference） |
| §3.3 物理布局 | Phase 1 task 1.5（MEMORY.md 索引重写） |
| §4.2 SessionStart hook | Phase 2 task 2.1-2.2 |
| §4.3 PreCompact hook | Phase 2 task 2.3-2.4 |
| §4.4 `/wrap` slash command | Phase 2 task 2.5 |
| §4.5 settings.json 注册 | Phase 2 task 2.6 |
| §5.3 6 步迁移 | Phase 3 task 3.1-3.7 |
| §6 Tier 2/3 模板 | Phase 4（推迟，首次创建新 skill 时启动） |

---

## 文件结构总览

**新增文件**（不在 git 仓库 = 不 commit；通过实施日志承担追溯）：

```
~/.claude/projects/-Users-dalwin/memory/
├── user_role.md                       # u1, u2
├── feedback_workflow.md               # f1, f2, f3
├── feedback_minimal_change.md         # f4, f5
├── feedback_commit_split.md           # f6
├── feedback_review_stance.md          # f7
├── feedback_worktree_semantics.md     # f8
├── project_saas_repos.md              # p1
├── project_spec_location.md           # p2
├── reference_skills_root.md           # r2
└── reference_cross_tool_memory.md     # r3

~/.claude/hooks/
├── sessionstart-domain.py
└── precompact-memory.py

~/.claude/commands/
└── wrap.md
```

**修改文件**（不在 git 仓库 = 不 commit）：

```
~/.claude/projects/-Users-dalwin/memory/
├── MEMORY.md                          # 重写索引：从 1 条扩到 11 条
└── maven-config.md                    # 扩充（p3：添加跨链 + 改 type=project）

~/.claude/settings.json                 # SessionStart + PreCompact 追加 hook
```

**改动文件**（在 `~/Documents/AI/` git repo 内 = 每个 Phase 末尾 commit）：

```
~/Documents/AI/dalwin-workflow/
├── docs/superpowers/plans/
│   ├── 2026-05-26-personal-workflow-implementation.md  # 本计划
│   └── logs/
│       ├── phase-1-memory-seed.md
│       ├── phase-2-hooks-wrap.md
│       └── phase-3-source-migration.md
└── archived_skills/
    └── README.md                      # 从 ~/.claude/skills/ 移除的软链 + 复链方法
```

**迁移涉及**（Phase 3 详述）：

```
~/Documents/AI/skills/                  # 整目录删除（迁移到 awesome-skills 后）
~/.claude/skills/{svg-logo-creator, resume-generator, app-icon}  # 删软链
~/.agents/skills/{11 个 real dir}       # mv 到 SOT + 替换为 symlink
~/Library/CodeRepo/AI/awesome-skills/   # 接收迁入的 skills
```

---

## Phase 0：实施前置

### Task 0.1：提交计划文件本身

**Files:**
- Modify: `~/Documents/AI/dalwin-workflow/docs/superpowers/plans/2026-05-26-personal-workflow-implementation.md`（本文件）
- Create: `~/Documents/AI/dalwin-workflow/docs/superpowers/plans/logs/.gitkeep`

- [ ] **Step 1：创建 logs 目录**

```bash
mkdir -p /Users/dalwin/Documents/AI/dalwin-workflow/docs/superpowers/plans/logs
touch /Users/dalwin/Documents/AI/dalwin-workflow/docs/superpowers/plans/logs/.gitkeep
```

- [ ] **Step 2：暂存并提交**

```bash
git -C /Users/dalwin/Documents/AI add dalwin-workflow/docs/superpowers/plans/
git -C /Users/dalwin/Documents/AI status -s -- dalwin-workflow/
```

Expected: 两个新文件出现在 staging（`plans/2026-05-26-...md` + `plans/logs/.gitkeep`）。

```bash
git -C /Users/dalwin/Documents/AI commit -m "docs(dalwin-workflow): 落地 2026-05-26 个人工作流实施计划"
```

Expected: `1 file changed`/`2 files changed`，commit message 符合 `<type>(<scope>): <subject>` 中文 subject。

---

## Phase 1：Memory Seed（11 个种子文件 + 索引）

### Task 1.1：写 user 类种子（user_role.md）

**Files:**
- Create: `~/.claude/projects/-Users-dalwin/memory/user_role.md`

- [ ] **Step 1：写入文件**

````bash
cat > /Users/dalwin/.claude/projects/-Users-dalwin/memory/user_role.md <<'EOF'
---
name: user-role
description: 用户角色、工作分布与协作偏好（Java/SaaS 主、AI 自建副、Go/Python 学习方向、Codex+Claude 双工具协作）
metadata:
  type: user
---

主战场 Java/Spring SaaS 后端（saas 项目，55%），AI 工具自建（20%，包括本工作流设计本身），知识与内容沉淀（10%），Go/Python 学习方向（15%，未来转后端的预备）。

Codex 与 Claude 双工具协作；偏好共享源 + symlink，两边共用同一份 skill 更新。详见 [[reference-skills-root]] 与 [[reference-cross-tool-memory]]。
EOF
````

- [ ] **Step 2：验证**

```bash
test -f /Users/dalwin/.claude/projects/-Users-dalwin/memory/user_role.md && head -5 /Users/dalwin/.claude/projects/-Users-dalwin/memory/user_role.md
```

Expected: 文件存在；前 5 行显示 frontmatter `name: user-role` 等。

---

### Task 1.2：写 feedback 类种子（5 个文件）

**Files:**
- Create: `~/.claude/projects/-Users-dalwin/memory/feedback_workflow.md`
- Create: `~/.claude/projects/-Users-dalwin/memory/feedback_minimal_change.md`
- Create: `~/.claude/projects/-Users-dalwin/memory/feedback_commit_split.md`
- Create: `~/.claude/projects/-Users-dalwin/memory/feedback_review_stance.md`
- Create: `~/.claude/projects/-Users-dalwin/memory/feedback_worktree_semantics.md`

- [ ] **Step 1：写 feedback_workflow.md（f1/f2/f3）**

````bash
cat > /Users/dalwin/.claude/projects/-Users-dalwin/memory/feedback_workflow.md <<'EOF'
---
name: feedback-workflow
description: 主任务链路偏好——review/brainstorming/spec/实施 + spec 落盘后的执行边界 + 代码修复默认手势
metadata:
  type: feedback
---

## 主链路偏好 (f1)

大任务接受 "review → brainstorming → spec → 实施" 主链；每步沉淀为 repo-local 文档，不停留在聊天。

**Why:** 用户希望复杂任务可追溯、可复盘，仅口头结论不足以承担后续协作。
**How to apply:** 任务规模评估为"大/复杂"时，主动建议 spec-architect 或 brainstorming → writing-plans 流程；产物落到 repo `docs/` 路径。

## Spec 落盘后的执行边界 (f2)

任务**小且简单**时，落盘 spec 后默认直接执行，不再确认方向；任务大/复杂时，即便 spec 已落盘也先简短确认方向再动手。

**Why:** 小任务 spec 是 fast-pass；大任务 spec 不能替代方向确认（避免误读）。
**How to apply:** 看到 "按照 xxx-spec.md 完成编码" 类指令时，先评估改动范围（如 ≤3 个文件、单模块 → 小；跨模块/多链路 → 大）；小则直接做，大则先回 "确认范围 X/Y/Z，开始执行" 一句话再做。

## 代码修复默认手势 (f3)

默认 "确认入口/调用点 → 最小化改动服务层 → 编译/模块静态验证 → `git diff --check`"。

**Why:** 用户重视定向证据、最小改动、diff 纯度；不喜欢猜测式修改。
**How to apply:** Java/Spring 修复任务的固定收尾流程；mvn 命令按 [[maven-config]] 附加参数。
EOF
````

- [ ] **Step 2：写 feedback_minimal_change.md（f4/f5）**

````bash
cat > /Users/dalwin/.claude/projects/-Users-dalwin/memory/feedback_minimal_change.md <<'EOF'
---
name: feedback-minimal-change
description: 局部兼容修复的最小改动 + 审核/回显/副作用问题的全链路复扫习惯
metadata:
  type: feedback
---

## 局部兼容修复 (f4)

局部兼容修复优先在现有入口最小改动，不主动抽新类/扩配置。

**Why:** 用户多次纠正过早抽象（如 "这个类看起来不太需要……就在原先方法内加入项目判断即可"）。
**How to apply:** 看到"项目白名单/特例处理"类需求时，先评估能否在已有方法（如 `enableClassSnapshotProject()`）内追加，再考虑抽类；用户未明确同意前不主动扩配置。

## 全链路复扫 (f5)

审核/回显/副作用类问题做全链路复扫，不只改单点。

**Why:** 审核链路（提交、审批、回显、正式表）通常多入口，单点改完仍漏。
**How to apply:** 修复审核/回显类问题时，主动枚举该问题域的所有方法（如 `submitAuditNursery` / `getAuditDetail` / `applyClassLimitSnapshotFromWorkflow` / `buildNurseryClass` / `fillClassLimitFromDb`）一起检查。
EOF
````

- [ ] **Step 3：写 feedback_commit_split.md（f6）**

````bash
cat > /Users/dalwin/.claude/projects/-Users-dalwin/memory/feedback_commit_split.md <<'EOF'
---
name: feedback-commit-split
description: 默认将单元测试与源码拆成 2 个 commit 提交（方便 IDEA 复核）
metadata:
  type: feedback
---

## 单元测试与源码拆 2 commit (f6)

**默认**将单元测试与源码拆成 2 个 commit 提交。

**Why:** 用户在 IDEA 编辑器做最终确认时，分开 commit 便于逐步核对。
**How to apply:** 修复任务完成后，先 `git add <src>` + commit（feat/fix），再 `git add <test>` + commit（test）；commit message 按 `<type>(<scope>): <subject>` 中文规范。
EOF
````

- [ ] **Step 4：写 feedback_review_stance.md（f7）**

````bash
cat > /Users/dalwin/.claude/projects/-Users-dalwin/memory/feedback_review_stance.md <<'EOF'
---
name: feedback-review-stance
description: review 默认"独立、客观、批判"口径，主动给"预期外的"意见
metadata:
  type: feedback
---

## Review 口径 (f7)

review 默认"独立、客观、批判"口径，主动给"预期外的"意见。

**Why:** 用户要求 review 是"怀疑式、证据驱动的风险审查"，而不是确认式总结。
**How to apply:** 接到 review 任务（含 vendor 替换、架构兼容、复杂修复 review），先锚定真实代码路径和当前文档；输出按 P0/P1 风险排序；主动给至少 1 条 "预期外的"意见（用户没有要求但通过证据发现的风险）。
EOF
````

- [ ] **Step 5：写 feedback_worktree_semantics.md（f8）**

````bash
cat > /Users/dalwin/.claude/projects/-Users-dalwin/memory/feedback_worktree_semantics.md <<'EOF'
---
name: feedback-worktree-semantics
description: "置空 worktree" = detach + 删分支，不等于清理未跟踪文件
metadata:
  type: feedback
---

## Worktree 置空语义 (f8)

"置空 worktree" = `git switch --detach <base>` + `git branch -D <branch>`，**不**等于清理未跟踪文件。

**Why:** 用户在 cherry-pick 完成后说 "本 worktree 置空然后删掉这个分支"，意图是释放分支占用；未明确要求前不要擅自删未跟踪目录。
**How to apply:** 收到"置空 worktree"指令时，按 `git worktree list --porcelain` 查占用 → `git switch --detach <base>` → `git branch -D <branch>` 顺序操作；若用户要全清空未跟踪文件，需用户单独确认。
EOF
````

- [ ] **Step 6：验证 5 个文件**

```bash
ls -la /Users/dalwin/.claude/projects/-Users-dalwin/memory/feedback_*.md | wc -l
```

Expected: `5`（5 行输出）。

---

### Task 1.3：写 project 类种子（p1/p2 + 扩充 maven-config）

**Files:**
- Create: `~/.claude/projects/-Users-dalwin/memory/project_saas_repos.md`
- Create: `~/.claude/projects/-Users-dalwin/memory/project_spec_location.md`
- Modify: `~/.claude/projects/-Users-dalwin/memory/maven-config.md`（扩充 + 改 type 到 project）

- [ ] **Step 1：写 project_saas_repos.md（p1）**

````bash
cat > /Users/dalwin/.claude/projects/-Users-dalwin/memory/project_saas_repos.md <<'EOF'
---
name: project-saas-repos
description: SaaS 三大 sub-repo 路径（skc-nursery / skc-activity / skciotdevice）+ 高频项目白名单常量
metadata:
  type: project
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
EOF
````

- [ ] **Step 2：写 project_spec_location.md（p2）**

````bash
cat > /Users/dalwin/.claude/projects/-Users-dalwin/memory/project_spec_location.md <<'EOF'
---
name: project-spec-location
description: spec 文件落到 docs/spec-architect/YYYY-MM/ 时遵循 .gitignore；仅用户明确要求才 git add -f
metadata:
  type: project
---

## Spec 文件落地规则 (p2)

spec 文件落到 `docs/spec-architect/YYYY-MM/` 时**遵循 .gitignore**；仅当用户明确要求纳入 git 追踪才 `git add -f`。

**Why:** `.gitignore` 是项目的权威配置；不应擅自把被忽略文件纳入追踪。
**How to apply:** 落 spec 后用 `git check-ignore <path>` 确认；若被 ignore 则保留在 working tree 不 add；用户明确说 "把这个 spec 提交" 才 `git add -f`。
EOF
````

- [ ] **Step 3：扩充 maven-config.md（p3）**

````bash
cat > /Users/dalwin/.claude/projects/-Users-dalwin/memory/maven-config.md <<'EOF'
---
name: maven-config
description: 本地 Maven 仓库和 settings.xml 的非默认路径，Java 项目编译/测试/打包时必须使用这些路径
metadata:
  type: project
---

## Maven 本地配置 (p3)

- 本地 Maven 仓库：`/Users/dalwin/Library/Repository`
- settings.xml：`/Users/dalwin/Library/ConfigFile/maven/saas/settings.xml`

**Why:** 用户本地 Maven 配置不在默认的 `~/.m2`，使用 `mvn` 命令时必须显式指定。

**How to apply:** 凡是执行 `mvn` 命令编译、测试、打包时，始终附加：

```
mvn -s /Users/dalwin/Library/ConfigFile/maven/saas/settings.xml -Dmaven.repo.local=/Users/dalwin/Library/Repository <goal>
```

相关：[[project-saas-repos]] 列出 saas 三大 sub-repo 路径；[[feedback-workflow]] 收尾步骤会使用 mvn 命令做静态验证。
EOF
````

- [ ] **Step 4：验证 3 个 project 类文件**

```bash
ls -la /Users/dalwin/.claude/projects/-Users-dalwin/memory/project_*.md /Users/dalwin/.claude/projects/-Users-dalwin/memory/maven-config.md
```

Expected: 3 个文件存在；查 maven-config 的 type 已改为 project：

```bash
grep "type:" /Users/dalwin/.claude/projects/-Users-dalwin/memory/maven-config.md
```

Expected: `  type: project`

---

### Task 1.4：写 reference 类种子（r2/r3）

**Files:**
- Create: `~/.claude/projects/-Users-dalwin/memory/reference_skills_root.md`
- Create: `~/.claude/projects/-Users-dalwin/memory/reference_cross_tool_memory.md`

- [ ] **Step 1：写 reference_skills_root.md（r2）**

````bash
cat > /Users/dalwin/.claude/projects/-Users-dalwin/memory/reference_skills_root.md <<'EOF'
---
name: reference-skills-root
description: AI skills 主目录布局（~/Library/CodeRepo/AI/ 是唯一 SOT，含 awesome-skills、superpowers fork、skills 三仓）
metadata:
  type: reference
---

`/Users/dalwin/Library/CodeRepo/AI/` 是 AI skills 的唯一 Source of Truth：

- `awesome-skills/` — 自创/精选 skills（如 docker-best-practices、spec-architect、git-merge-conductor）
- `superpowers/` — superpowers 仓库 fork
- `skills/` — 外部克隆（如 grill-me、grill-with-docs）

注册表与视图（双跳 symlink）：

- `/Users/dalwin/.agents/skills/{name}` → 软链 → SOT 下对应路径
- `/Users/dalwin/.claude/skills/{name}` → 软链 → `/Users/dalwin/.agents/skills/{name}`

相关：[[reference-cross-tool-memory]] 中说明 codex 与 claude 的跨工具协作约定。
EOF
````

- [ ] **Step 2：写 reference_cross_tool_memory.md（r3）**

````bash
cat > /Users/dalwin/.claude/projects/-Users-dalwin/memory/reference_cross_tool_memory.md <<'EOF'
---
name: reference-cross-tool-memory
description: 跨工具事实唯一源——codex memory 与 claude memory 的物理位置 + 对账要求
metadata:
  type: reference
---

跨工具事实唯一源：

- Codex memory：`/Users/dalwin/.codex/memories/MEMORY.md` + `memory_summary.md` + `raw_memories.md`
- Claude memory：`/Users/dalwin/.claude/projects/-Users-dalwin/memory/`

两侧定期对账；如发现 codex 中已有的稳定事实但 claude 未沉淀（或反之），主动建议补全。

相关：[[reference-skills-root]] 中说明 skills 也走类似 SOT + symlink 跨工具共享模式。
EOF
````

- [ ] **Step 3：验证 2 个 reference 文件**

```bash
ls -la /Users/dalwin/.claude/projects/-Users-dalwin/memory/reference_*.md
```

Expected: 2 个文件。

---

### Task 1.5：重写 MEMORY.md 索引 + Phase 1 验证

**Files:**
- Modify: `~/.claude/projects/-Users-dalwin/memory/MEMORY.md`
- Create: `~/Documents/AI/dalwin-workflow/docs/superpowers/plans/logs/phase-1-memory-seed.md`

- [ ] **Step 1：重写 MEMORY.md 索引（11 条 + 原 Maven 1 条）**

````bash
cat > /Users/dalwin/.claude/projects/-Users-dalwin/memory/MEMORY.md <<'EOF'
# Memory Index

- [User Role](user_role.md) — 用户角色、工作分布与协作偏好（Java/SaaS 主、AI 自建副、Go/Python 学习方向、Codex+Claude 双工具协作）
- [Workflow Preferences](feedback_workflow.md) — 主任务链路偏好——review/brainstorming/spec/实施 + spec 落盘后的执行边界 + 代码修复默认手势
- [Minimal Change & Full-Chain Rescan](feedback_minimal_change.md) — 局部兼容修复的最小改动 + 审核/回显/副作用问题的全链路复扫习惯
- [Commit Split](feedback_commit_split.md) — 默认将单元测试与源码拆成 2 个 commit 提交（方便 IDEA 复核）
- [Review Stance](feedback_review_stance.md) — review 默认"独立、客观、批判"口径，主动给"预期外的"意见
- [Worktree Semantics](feedback_worktree_semantics.md) — "置空 worktree" = detach + 删分支，不等于清理未跟踪文件
- [SaaS Repos](project_saas_repos.md) — SaaS 三大 sub-repo 路径（skc-nursery / skc-activity / skciotdevice）+ 高频项目白名单常量
- [Spec Location](project_spec_location.md) — spec 文件落到 docs/spec-architect/YYYY-MM/ 时遵循 .gitignore；仅用户明确要求才 git add -f
- [Maven Config](maven-config.md) — 本地 Maven 仓库和 settings.xml 的非默认路径，Java 项目编译/测试/打包时必须使用这些路径
- [Skills Root](reference_skills_root.md) — AI skills 主目录布局（~/Library/CodeRepo/AI/ 是唯一 SOT，含 awesome-skills、superpowers fork、skills 三仓）
- [Cross-Tool Memory](reference_cross_tool_memory.md) — 跨工具事实唯一源——codex memory 与 claude memory 的物理位置 + 对账要求
EOF
````

- [ ] **Step 2：验证 Phase 1 全部 memory 文件**

```bash
ls /Users/dalwin/.claude/projects/-Users-dalwin/memory/*.md | wc -l
```

Expected: `12`（11 个 seed 文件 + MEMORY.md 索引）。

```bash
ls /Users/dalwin/.claude/projects/-Users-dalwin/memory/*.md
```

Expected output (顺序可能不同):
```
.../MEMORY.md
.../feedback_commit_split.md
.../feedback_minimal_change.md
.../feedback_review_stance.md
.../feedback_workflow.md
.../feedback_worktree_semantics.md
.../maven-config.md
.../project_saas_repos.md
.../project_spec_location.md
.../reference_cross_tool_memory.md
.../reference_skills_root.md
.../user_role.md
```

- [ ] **Step 3：写 Phase 1 实施日志**

````bash
cat > /Users/dalwin/Documents/AI/dalwin-workflow/docs/superpowers/plans/logs/phase-1-memory-seed.md <<'EOF'
# Phase 1 实施日志：Memory Seed

完成时间：(填实际完成日期)

## 新增/修改文件

- 新增 10 个 seed 文件（user_role / 5 feedback / 2 project / 2 reference）
- 修改 1 个文件（maven-config.md 扩充 + type 改 project）
- 重写 MEMORY.md 索引（从 1 条扩到 11 条）

## 验证结果

- 文件总数：12（11 seed + 1 索引）
- 所有种子 frontmatter 含 `type: <user|feedback|project|reference>`
- 跨文件链接（[[name]]）已建立 user_role → reference 两条、project_saas_repos → maven-config、maven-config → feedback-workflow / project-saas-repos

## 下一步

进入 Phase 2：Hooks + /wrap。
EOF
````

- [ ] **Step 4：提交 Phase 1 日志**

```bash
git -C /Users/dalwin/Documents/AI add dalwin-workflow/docs/superpowers/plans/logs/phase-1-memory-seed.md
git -C /Users/dalwin/Documents/AI commit -m "docs(dalwin-workflow): Phase 1 memory seed 实施完成"
```

Expected: 1 file changed，commit 成功。

---

## Phase 2：Hooks + /wrap

### Task 2.1：写 sessionstart-domain.py

**Files:**
- Create: `~/.claude/hooks/sessionstart-domain.py`

- [ ] **Step 1：写入 Python hook**

````bash
cat > /Users/dalwin/.claude/hooks/sessionstart-domain.py <<'EOF'
#!/usr/bin/env python3
"""SessionStart hook: detect work domain from cwd and emit confidence index.

输出格式（注入到 SessionStart additionalContext）：
  [工作域] java/spring=0.90; pack-java: spec-architect, grill-with-docs, ...
或多域：
  [工作域] java/spring=0.70, ai_build=0.60
    pack-java: ...
    pack-ai-build: ...
或无主域：
  [工作域] cwd=...: 无主域；仅 spine 可用

置信度阈值：≥0.5 主域；<0.3 不出现在索引。
"""

import json
import os
import sys
from pathlib import Path

THRESHOLD = 0.5
NOISE_FLOOR = 0.3

DOMAIN_PACKS = {
    'java/spring': ['spec-architect', 'grill-with-docs', 'git-merge-conductor',
                    'requesting-code-review', 'security-review'],
    'ai_build': ['skill-creator', 'writing-skills', 'skill-security-audit',
                 'subagent-driven-development', 'claude-api'],
    'knowledge': ['Notion:find', 'Notion:search', 'Notion:create-page',
                  'Notion:create-task', 'Notion:database-query', 'deep-research'],
    'learning': ['grill-me', 'claude-api'],
}

# 与 spec §5.1 命名保持一致；不直接由 domain key 推导（避免 java/spring → java-spring）
PACK_ID = {
    'java/spring': 'java',
    'ai_build': 'ai-build',
    'knowledge': 'knowledge',
    'learning': 'learning',
}


def has_marker(cwd: Path, marker: str, max_up: int = 5) -> bool:
    """Check if cwd or any ancestor (up to max_up levels) contains marker."""
    p = cwd
    for _ in range(max_up):
        if (p / marker).exists():
            return True
        if p.parent == p:
            break
        p = p.parent
    return False


def has_glob(cwd: Path, pattern: str) -> bool:
    try:
        return any(cwd.glob(pattern))
    except (OSError, ValueError):
        return False


def compute_confidence(cwd: Path) -> dict:
    cwd_str = str(cwd)
    scores = {}

    # java/spring (含 Maven monorepo 信号：cwd 自身无 pom.xml 但子目录有)
    s = 0.0
    if has_marker(cwd, 'pom.xml'): s += 0.5
    if has_glob(cwd, '*/pom.xml'): s += 0.3
    if has_marker(cwd, 'mvnw'): s += 0.2
    if has_marker(cwd, 'src/main/java'): s += 0.3
    if has_glob(cwd, '*/src/main/java'): s += 0.2
    if has_marker(cwd, '.idea'): s += 0.1
    scores['java/spring'] = min(s, 1.0)

    # ai_build
    s = 0.0
    if 'awesome-skills' in cwd_str: s += 0.4
    if 'superpowers/skills' in cwd_str: s += 0.4
    if '.claude/skills' in cwd_str: s += 0.4
    if cwd.name.startswith('skill-'): s += 0.3
    if 'AI' in cwd.parts: s += 0.2
    scores['ai_build'] = min(s, 1.0)

    # knowledge
    s = 0.0
    if '/docs/' in cwd_str or cwd_str.endswith('/docs'): s += 0.15
    if '/wiki/' in cwd_str or cwd_str.endswith('/wiki'): s += 0.3
    if 'Notion' in cwd_str or 'notion' in cwd_str: s += 0.5
    scores['knowledge'] = min(s, 1.0)

    # learning
    s = 0.0
    if has_marker(cwd, 'go.mod'): s += 0.6
    if has_glob(cwd, '*.go'): s += 0.4
    low = cwd_str.lower()
    if any(kw in low for kw in ['learn', '/study/', '/学习/']): s += 0.3
    scores['learning'] = min(s, 1.0)

    return scores


def format_output(scores: dict, cwd: Path) -> str:
    visible = {k: v for k, v in scores.items() if v >= NOISE_FLOOR}
    if not visible:
        return f"[工作域] cwd={cwd}: 无主域；仅 spine 可用"

    primary = sorted(
        [k for k, v in visible.items() if v >= THRESHOLD],
        key=lambda k: -visible[k]
    )
    if not primary:
        candidates = ', '.join(
            f'{k}={visible[k]:.2f}'
            for k in sorted(visible.keys(), key=lambda k: -visible[k])
        )
        return f"[工作域] cwd={cwd}: {candidates}（无主域，仅 spine 可用）"

    if len(primary) == 1:
        k = primary[0]
        v = visible[k]
        members = ', '.join(DOMAIN_PACKS[k])
        return f"[工作域] {k}={v:.2f}; pack-{PACK_ID[k]}: {members}"

    header = '[工作域] ' + ', '.join(f'{k}={visible[k]:.2f}' for k in primary)
    lines = [header]
    for k in primary:
        members = ', '.join(DOMAIN_PACKS[k])
        lines.append(f"  pack-{PACK_ID[k]}: {members}")
    return '\n'.join(lines)


def main():
    try:
        data = json.loads(sys.stdin.read() or '{}')
        cwd = Path(data.get('cwd') or os.getcwd())
    except (json.JSONDecodeError, ValueError, OSError):
        sys.exit(0)

    scores = compute_confidence(cwd)
    context = format_output(scores, cwd)

    print(json.dumps({
        'hookSpecificOutput': {
            'hookEventName': 'SessionStart',
            'additionalContext': context,
        }
    }, ensure_ascii=False))


if __name__ == '__main__':
    main()
EOF
chmod +x /Users/dalwin/.claude/hooks/sessionstart-domain.py
````

- [ ] **Step 2：语法检查**

```bash
python3 -c "import ast; ast.parse(open('/Users/dalwin/.claude/hooks/sessionstart-domain.py').read())" && echo "syntax OK"
```

Expected: `syntax OK`。

---

### Task 2.2：测试 sessionstart-domain.py（4 个场景）

- [ ] **Step 1：Java/Spring 场景**

```bash
echo '{"hook_event_name":"SessionStart","cwd":"/Users/dalwin/Library/IdeaProject/ZhiJin/SunkidCloud/skcservers/skcactivity"}' | python3 /Users/dalwin/.claude/hooks/sessionstart-domain.py | python3 -c "import json,sys; d=json.load(sys.stdin); ctx=d['hookSpecificOutput']['additionalContext']; print(ctx); assert 'java/spring' in ctx and 'pack-java:' in ctx, 'java/spring not primary'; print('PASS java/spring')"
```

Expected: 显示注入内容并打印 `PASS java/spring`。

- [ ] **Step 2：AI build 场景**

```bash
echo '{"hook_event_name":"SessionStart","cwd":"/Users/dalwin/Library/CodeRepo/AI/awesome-skills/spec-architect"}' | python3 /Users/dalwin/.claude/hooks/sessionstart-domain.py | python3 -c "import json,sys; d=json.load(sys.stdin); ctx=d['hookSpecificOutput']['additionalContext']; print(ctx); assert 'ai_build' in ctx and 'pack-ai-build:' in ctx, 'ai_build not primary'; print('PASS ai_build')"
```

Expected: `PASS ai_build`。

- [ ] **Step 3：Learning 场景（tmp 仿真）**

```bash
mkdir -p /tmp/test-go-learn && touch /tmp/test-go-learn/go.mod && echo '{"hook_event_name":"SessionStart","cwd":"/tmp/test-go-learn"}' | python3 /Users/dalwin/.claude/hooks/sessionstart-domain.py | python3 -c "import json,sys; d=json.load(sys.stdin); ctx=d['hookSpecificOutput']['additionalContext']; print(ctx); assert 'learning' in ctx, 'learning not detected'; print('PASS learning')"
rm -rf /tmp/test-go-learn
```

Expected: `PASS learning`。

- [ ] **Step 4：无主域场景（cwd = /Users/dalwin）**

```bash
echo '{"hook_event_name":"SessionStart","cwd":"/Users/dalwin"}' | python3 /Users/dalwin/.claude/hooks/sessionstart-domain.py | python3 -c "import json,sys; d=json.load(sys.stdin); ctx=d['hookSpecificOutput']['additionalContext']; print(ctx); assert '无主域' in ctx or 'spine' in ctx, 'should fall back to spine-only'; print('PASS no-domain')"
```

Expected: `PASS no-domain`。

---

### Task 2.3：写 precompact-memory.py

**Files:**
- Create: `~/.claude/hooks/precompact-memory.py`

- [ ] **Step 1：写入 Python hook**

````bash
cat > /Users/dalwin/.claude/hooks/precompact-memory.py <<'EOF'
#!/usr/bin/env python3
"""PreCompact hook: emit passive memory-eval hint without blocking compaction.

输出固定一行 additionalContext；不设 permissionDecision，不阻断流程。
"""

import json
import sys

HINT = (
    "[memory 候选评估·建议] 若本次会话已沉淀新事实，"
    "可在压缩前按 ~/.claude/CLAUDE.md auto memory 规则写入。"
    "本提示为建议性，无候选则忽略；不影响压缩流程。"
)


def main():
    try:
        sys.stdin.read()  # drain input; we don't use it
    except Exception:
        pass

    print(json.dumps({
        'hookSpecificOutput': {
            'hookEventName': 'PreCompact',
            'additionalContext': HINT,
        }
    }, ensure_ascii=False))


if __name__ == '__main__':
    main()
EOF
chmod +x /Users/dalwin/.claude/hooks/precompact-memory.py
````

- [ ] **Step 2：语法检查**

```bash
python3 -c "import ast; ast.parse(open('/Users/dalwin/.claude/hooks/precompact-memory.py').read())" && echo "syntax OK"
```

Expected: `syntax OK`。

---

### Task 2.4：测试 precompact-memory.py

- [ ] **Step 1：基本调用**

```bash
echo '{"hook_event_name":"PreCompact"}' | python3 /Users/dalwin/.claude/hooks/precompact-memory.py | python3 -c "import json,sys; d=json.load(sys.stdin); ctx=d['hookSpecificOutput']['additionalContext']; assert 'memory 候选评估' in ctx and 'permissionDecision' not in str(d), 'output structure failed'; print('PASS precompact')"
```

Expected: `PASS precompact`。

- [ ] **Step 2：确认不阻断（不输出 permissionDecision）**

```bash
echo '{}' | python3 /Users/dalwin/.claude/hooks/precompact-memory.py | python3 -c "import json,sys; d=json.load(sys.stdin); assert 'permissionDecision' not in d.get('hookSpecificOutput',{}), 'BUG: permissionDecision present'; print('PASS no-block')"
```

Expected: `PASS no-block`。

---

### Task 2.5：写 commands/wrap.md

**Files:**
- Create: `~/.claude/commands/wrap.md`

- [ ] **Step 1：确认 commands 目录**

```bash
ls -d /Users/dalwin/.claude/commands 2>/dev/null || mkdir -p /Users/dalwin/.claude/commands
```

- [ ] **Step 2：写 slash command**

````bash
cat > /Users/dalwin/.claude/commands/wrap.md <<'EOF'
---
description: 在 /clear 之前评估并写入 memory 候选
---

# /wrap

按 `~/.claude/CLAUDE.md` 的 auto memory 规则评估本会话候选并写入 memory。

## 步骤

1. 回顾本次会话已经发生的事实，判断是否产生新的：
   - **user**：用户角色/目标/知识背景的变化
   - **feedback**：用户确认或纠正过的工作方式
   - **project**：项目级事实（不会快速过期）
   - **reference**：外部资源指向（非 MCP 实时可获取的）

2. 去重检查：先确认该事实不在 `~/.claude/CLAUDE.md` / hooks 配置 / 现有 memory 中
3. 跨会话价值检查：本次特定任务的细节不写；可复用于未来类似任务才写
4. 如有候选，按 CLAUDE.md auto memory 规范写入 `~/.claude/projects/-Users-dalwin/memory/`
5. 完成后输出：

```
✅ memory 评估完毕，可执行 /clear
```

如无候选，输出：

```
本次会话无新 memory 候选；可执行 /clear
```
EOF
````

- [ ] **Step 3：验证**

```bash
test -f /Users/dalwin/.claude/commands/wrap.md && head -3 /Users/dalwin/.claude/commands/wrap.md
```

Expected: 显示 `---` / `description: 在 /clear 之前评估并写入 memory 候选` / `---`。

---

### Task 2.6：修改 settings.json 注册两个 hook

**Files:**
- Modify: `~/.claude/settings.json`（在 `SessionStart` 和 `PreCompact` 数组追加 entry，不动其它）

- [ ] **Step 1：备份当前 settings.json**

```bash
cp /Users/dalwin/.claude/settings.json /Users/dalwin/.claude/settings.json.bak.20260526
```

- [ ] **Step 2：用 Python 注入两个 hook（保护既有 codeisland 配置）**

```bash
python3 <<'EOF'
import json, pathlib

path = pathlib.Path('/Users/dalwin/.claude/settings.json')
data = json.loads(path.read_text())
hooks = data.setdefault('hooks', {})

NEW_HOOKS = {
    'SessionStart': {
        'command': 'python3 /Users/dalwin/.claude/hooks/sessionstart-domain.py',
    },
    'PreCompact': {
        'command': 'python3 /Users/dalwin/.claude/hooks/precompact-memory.py',
    },
}

for event, payload in NEW_HOOKS.items():
    entries = hooks.setdefault(event, [])
    # 幂等：若已存在同 command 的 entry，跳过
    already = any(
        any(h.get('command') == payload['command'] for h in entry.get('hooks', []))
        for entry in entries
    )
    if already:
        print(f"{event}: already configured, skip")
        continue
    entries.append({
        'matcher': '',
        'hooks': [{'type': 'command', 'command': payload['command'], 'timeout': 5}]
    })
    print(f"{event}: appended new hook")

path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n')
print('settings.json updated')
EOF
```

Expected: 输出
```
SessionStart: appended new hook
PreCompact: appended new hook
settings.json updated
```

- [ ] **Step 3：验证 JSON 合法 + 既有配置不丢**

```bash
python3 -c "import json; d=json.load(open('/Users/dalwin/.claude/settings.json')); print('codeisland still present:', any('codeisland' in h.get('command','') for entry in d['hooks'].get('SessionStart',[]) for h in entry.get('hooks',[]))); print('new hook present:', any('sessionstart-domain.py' in h.get('command','') for entry in d['hooks'].get('SessionStart',[]) for h in entry.get('hooks',[])))"
```

Expected:
```
codeisland still present: True
new hook present: True
```

- [ ] **Step 4：检查 effortLevel / theme / enabledPlugins 等顶层字段未丢**

```bash
python3 -c "import json; d=json.load(open('/Users/dalwin/.claude/settings.json')); assert 'effortLevel' in d and 'theme' in d and 'enabledPlugins' in d; print('OK: top-level fields intact')"
```

Expected: `OK: top-level fields intact`。

---

### Task 2.7：端到端冒烟测试

- [ ] **Step 1：手动模拟 SessionStart hook 链**

```bash
echo '{"hook_event_name":"SessionStart","cwd":"/Users/dalwin/Library/IdeaProject/ZhiJin/SunkidCloud/skcservers/skcactivity"}' | python3 /Users/dalwin/.claude/hooks/sessionstart-domain.py
```

Expected: 输出含 `[工作域] java/spring=` 与 `pack-java-spring:` 的合法 JSON。

- [ ] **Step 2：手动模拟 PreCompact hook 链**

```bash
echo '{"hook_event_name":"PreCompact"}' | python3 /Users/dalwin/.claude/hooks/precompact-memory.py
```

Expected: 输出含 `memory 候选评估·建议` 的合法 JSON，无 `permissionDecision`。

- [ ] **Step 3（可选，需用户启动）：在新 Claude 会话里观察 hook 是否生效**

> 此步骤无法在 plan 执行环境里自动验证；建议用户实施完 Phase 2 后开一个新 Claude session（任意 cwd），看 `[工作域]` 索引是否出现在 SessionStart 注入位置。

---

### Task 2.8：提交 Phase 2 实施日志

**Files:**
- Create: `~/Documents/AI/dalwin-workflow/docs/superpowers/plans/logs/phase-2-hooks-wrap.md`

- [ ] **Step 1：写 Phase 2 日志**

````bash
cat > /Users/dalwin/Documents/AI/dalwin-workflow/docs/superpowers/plans/logs/phase-2-hooks-wrap.md <<'EOF'
# Phase 2 实施日志：Hooks + /wrap

完成时间：(填实际完成日期)

## 新增/修改文件

- 新增 `~/.claude/hooks/sessionstart-domain.py`（~150 行；置信度计算 + 索引格式化）
- 新增 `~/.claude/hooks/precompact-memory.py`（~30 行；被动 hint，不阻断压缩）
- 新增 `~/.claude/commands/wrap.md`（slash command；`/clear` 前主动调用）
- 修改 `~/.claude/settings.json`（SessionStart + PreCompact 各追加一个 hook entry；codeisland 既有配置保留）
- 备份 `~/.claude/settings.json.bak.20260526`

## 验证结果

- 4 个 SessionStart 场景全部 PASS（java/spring、ai_build、learning、no-domain）
- PreCompact 输出结构 PASS，且无 permissionDecision（不阻断）
- settings.json JSON 合法，顶层字段（effortLevel、theme、enabledPlugins）未丢

## 已知遗留

- `/wrap` slash command 仅 markdown 描述，Claude 实际执行依赖 LLM 按描述完成评估写入；首次使用建议人工核对一次产出
- SessionStart 端到端冒烟需用户启动新会话观察（plan 自动验证无法触达此环节）

## 下一步

进入 Phase 3：来源单源化迁移。
EOF
````

- [ ] **Step 2：提交**

```bash
git -C /Users/dalwin/Documents/AI add dalwin-workflow/docs/superpowers/plans/logs/phase-2-hooks-wrap.md
git -C /Users/dalwin/Documents/AI commit -m "docs(dalwin-workflow): Phase 2 hooks 与 wrap 命令实施完成"
```

Expected: 1 file changed，commit 成功。

---

## Phase 3：来源单源化迁移

> **关键约束**：本阶段动文件。每步先做"读"操作（diff / ls / readlink）确认现状，再做"写"操作（mv / ln / rm）。任一步出错立即停止，待用户确认再续。

### Task 3.1：比对 Documents/AI/skills 与 awesome-skills 同名内容

**Files:**
- Read: `~/Documents/AI/skills/spec-architect/`
- Read: `~/Documents/AI/skills/git-merge-conductor/`
- Read: `~/Library/CodeRepo/AI/awesome-skills/spec-architect/`
- Read: `~/Library/CodeRepo/AI/awesome-skills/git-merge-conductor/`（如存在）

- [ ] **Step 1：检查目录存在性**

```bash
echo "--- Documents/AI/skills/ ---" && ls -la /Users/dalwin/Documents/AI/skills/ 2>/dev/null
echo "--- awesome-skills/spec-architect ---" && ls -la /Users/dalwin/Library/CodeRepo/AI/awesome-skills/spec-architect/ 2>/dev/null
echo "--- awesome-skills/git-merge-conductor ---" && ls -la /Users/dalwin/Library/CodeRepo/AI/awesome-skills/git-merge-conductor/ 2>/dev/null || echo "(not present)"
```

Expected: 输出三段；spec-architect 在两侧都存在；git-merge-conductor 仅在 `Documents/AI/skills/` 存在。

- [ ] **Step 2：对 spec-architect 做内容 diff**

```bash
diff -r /Users/dalwin/Documents/AI/skills/spec-architect/ /Users/dalwin/Library/CodeRepo/AI/awesome-skills/spec-architect/ 2>&1 | head -50
```

Expected: 列出差异。**不自动选**——把 diff 输出给用户，由用户选保留哪个版本作 SOT。

- [ ] **Step 3：检查 mtime 作为参考**

```bash
find /Users/dalwin/Documents/AI/skills/spec-architect/ -name 'SKILL.md' -exec stat -f '%m %N' {} \;
find /Users/dalwin/Library/CodeRepo/AI/awesome-skills/spec-architect/ -name 'SKILL.md' -exec stat -f '%m %N' {} \;
```

Expected: 两侧 SKILL.md 的最后修改时间戳（epoch）；用户决策时可参考"哪边更新"。

---

### Task 3.2：用户确认 spec-architect 选版 + 迁移 git-merge-conductor

> **本任务需要用户在线决策**——执行前列 diff，等用户确认。

- [ ] **Step 1：等用户确认 spec-architect 哪个版本作 SOT**

询问用户："spec-architect 在两侧的 diff 见 Task 3.1 Step 2；请选 awesome-skills 版本（直接保留）还是 Documents/AI/skills 版本（需覆盖 awesome-skills）？"

候选答案：
- A：保留 awesome-skills 版本
- B：用 Documents/AI/skills 版本覆盖 awesome-skills

- [ ] **Step 2A（用户选 A）：直接删 Documents/AI/skills/spec-architect**

```bash
rm -rf /Users/dalwin/Documents/AI/skills/spec-architect
```

- [ ] **Step 2B（用户选 B）：用 Documents/AI/skills 版本覆盖 awesome-skills**

```bash
rm -rf /Users/dalwin/Library/CodeRepo/AI/awesome-skills/spec-architect
mv /Users/dalwin/Documents/AI/skills/spec-architect /Users/dalwin/Library/CodeRepo/AI/awesome-skills/spec-architect
```

- [ ] **Step 3：迁移 git-merge-conductor 到 awesome-skills**

```bash
test ! -e /Users/dalwin/Library/CodeRepo/AI/awesome-skills/git-merge-conductor && \
  mv /Users/dalwin/Documents/AI/skills/git-merge-conductor /Users/dalwin/Library/CodeRepo/AI/awesome-skills/git-merge-conductor && \
  echo "OK migrated git-merge-conductor"
```

Expected: `OK migrated git-merge-conductor`。

- [ ] **Step 4：确认 Documents/AI/skills/ 已空，删除目录**

```bash
ls -la /Users/dalwin/Documents/AI/skills/
```

Expected: 仅 `.` 与 `..`（可能含 `.DS_Store`，可忽略）。

```bash
rm -f /Users/dalwin/Documents/AI/skills/.DS_Store
rmdir /Users/dalwin/Documents/AI/skills && echo "OK removed Documents/AI/skills/"
```

Expected: `OK removed Documents/AI/skills/`。

- [ ] **Step 5：修补 git-merge-conductor 在 ~/Documents/AI/ git 仓库内的引用（如有）**

```bash
git -C /Users/dalwin/Documents/AI status -s | grep -E "(deleted|modified|skills)" || echo "(no git changes related to skills)"
```

> 因 `~/Documents/AI/skills/` 原本是 untracked（之前 git status 显示 `dalwin-workflow/` 等 untracked），删除不会触发已跟踪文件丢失。若 git status 报有 modified/deleted，停止并报告用户。

---

### Task 3.3：移除 ~/.claude/skills/ 中的 archive 软链

**Files:**
- Remove (symlink only): `~/.claude/skills/svg-logo-creator`、`~/.claude/skills/resume-generator`、`~/.claude/skills/app-icon`

- [ ] **Step 1：确认是 symlink（不是 real dir）**

```bash
for s in svg-logo-creator resume-generator app-icon; do
  ls -la /Users/dalwin/.claude/skills/$s 2>/dev/null | grep -q '^l' && echo "$s: OK is symlink" || echo "$s: WARN NOT symlink, abort"
done
```

Expected: 三行 `OK is symlink`。如有 WARN，停止并报告。

- [ ] **Step 2：删除符号链接**

```bash
rm /Users/dalwin/.claude/skills/svg-logo-creator
rm /Users/dalwin/.claude/skills/resume-generator
rm /Users/dalwin/.claude/skills/app-icon
echo "removed 3 archive symlinks from ~/.claude/skills/"
```

- [ ] **Step 3：验证 ~/.claude/skills/ 软链数从 14 降到 11（不含 .DS_Store）**

```bash
ls -la /Users/dalwin/.claude/skills/ | grep '^l' | wc -l
```

Expected: `11`（原 14 个 symlink - 3 archive）。

> 注：原文档说 15 是把目录条目都算上了；其中 .DS_Store 不是 symlink，所以 symlink 数原本是 14。删 3 个后剩 11。

---

### Task 3.4：迁移 ~/.agents/skills/ 无冲突的 8 个 real dir 到 SOT

**Files:**
- Move: 8 个目录从 `~/.agents/skills/` → `~/Library/CodeRepo/AI/awesome-skills/`
- Create: 8 个 symlink 回 `~/.agents/skills/`

涉及目录（与 awesome-skills 无同名冲突）：

| 源 | 目标 SOT |
|---|---|
| `~/.agents/skills/ai-pdf-builder` | `~/Library/CodeRepo/AI/awesome-skills/ai-pdf-builder` |
| `~/.agents/skills/app-icon` | `~/Library/CodeRepo/AI/awesome-skills/app-icon` |
| `~/.agents/skills/deep-research` | `~/Library/CodeRepo/AI/awesome-skills/deep-research` |
| `~/.agents/skills/docx` | `~/Library/CodeRepo/AI/awesome-skills/docx` |
| `~/.agents/skills/find-skills` | `~/Library/CodeRepo/AI/awesome-skills/find-skills` |
| `~/.agents/skills/gemini-svg-creator` | `~/Library/CodeRepo/AI/awesome-skills/gemini-svg-creator` |
| `~/.agents/skills/resume-generator` | `~/Library/CodeRepo/AI/awesome-skills/resume-generator` |
| `~/.agents/skills/skill-security-audit` | `~/Library/CodeRepo/AI/awesome-skills/skill-security-audit` |
| `~/.agents/skills/svg-logo-creator` | `~/Library/CodeRepo/AI/awesome-skills/svg-logo-creator` |

> 实际是 9 个无冲突目录（含 archive 的 app-icon / resume-generator / svg-logo-creator——仍迁 SOT，archive 仅指"不在 `~/.claude/skills/` 挂软链"）。

- [ ] **Step 1：再次确认目标 SOT 端无冲突**

```bash
for name in ai-pdf-builder app-icon deep-research docx find-skills gemini-svg-creator resume-generator skill-security-audit svg-logo-creator; do
  if [ -e /Users/dalwin/Library/CodeRepo/AI/awesome-skills/$name ]; then
    echo "$name: CONFLICT, dest exists, abort"
  else
    echo "$name: OK to migrate"
  fi
done
```

Expected: 9 行 `OK to migrate`。如有 CONFLICT，停止并报告（应该不会发生，因为我们已经过滤了已知冲突项）。

- [ ] **Step 2：逐个 mv + ln -s**

```bash
for name in ai-pdf-builder app-icon deep-research docx find-skills gemini-svg-creator resume-generator skill-security-audit svg-logo-creator; do
  mv /Users/dalwin/.agents/skills/$name /Users/dalwin/Library/CodeRepo/AI/awesome-skills/$name && \
    ln -s /Users/dalwin/Library/CodeRepo/AI/awesome-skills/$name /Users/dalwin/.agents/skills/$name && \
    echo "$name: migrated"
done
```

Expected: 9 行 `migrated`。

- [ ] **Step 3：验证 ~/.agents/skills/ 这 9 个变成 symlink**

```bash
for name in ai-pdf-builder app-icon deep-research docx find-skills gemini-svg-creator resume-generator skill-security-audit svg-logo-creator; do
  ls -la /Users/dalwin/.agents/skills/$name 2>/dev/null | grep -q '^l' && echo "$name: OK now symlink" || echo "$name: FAIL"
done
```

Expected: 9 行 `OK now symlink`。

- [ ] **Step 4：验证 ~/.claude/skills/ 双跳仍可达**

```bash
for name in ai-pdf-builder deep-research docx find-skills gemini-svg-creator skill-security-audit; do
  # 仅检查未 archive 的（archive 3 个已在 3.3 删 symlink）
  readlink -f /Users/dalwin/.claude/skills/$name 2>/dev/null | head -1
done
```

Expected: 6 行 `~/Library/CodeRepo/AI/awesome-skills/<name>`（archive 3 个不在 `~/.claude/skills/` 里所以不查；archive 项仍可通过 `~/.agents/skills/` 找到）。

---

### Task 3.5：对 docsify-station-creator / wiki-creator 做 diff-and-pick 后迁移

**Files:**
- Diff: `~/.agents/skills/{docsify-station-creator, wiki-creator}` vs `~/Library/CodeRepo/AI/awesome-skills/{同名}`
- Move (after user decision)

- [ ] **Step 1：对 docsify-station-creator 做 diff**

```bash
diff -r /Users/dalwin/.agents/skills/docsify-station-creator/ /Users/dalwin/Library/CodeRepo/AI/awesome-skills/docsify-station-creator/ 2>&1 | head -50
echo "---"
find /Users/dalwin/.agents/skills/docsify-station-creator -name 'SKILL.md' -exec stat -f '%m %N' {} \;
find /Users/dalwin/Library/CodeRepo/AI/awesome-skills/docsify-station-creator -name 'SKILL.md' -exec stat -f '%m %N' {} \;
```

- [ ] **Step 2：等用户决策（用户回 A 保留 awesome-skills 版 / B 用 .agents 版覆盖）**

- [ ] **Step 3A（A 路径）：删 .agents 实文件 + 加 symlink 指向 awesome-skills**

```bash
rm -rf /Users/dalwin/.agents/skills/docsify-station-creator
ln -s /Users/dalwin/Library/CodeRepo/AI/awesome-skills/docsify-station-creator /Users/dalwin/.agents/skills/docsify-station-creator
echo "docsify-station-creator: kept awesome-skills version, symlink updated"
```

- [ ] **Step 3B（B 路径）：用 .agents 版覆盖 awesome-skills + 加 symlink**

```bash
rm -rf /Users/dalwin/Library/CodeRepo/AI/awesome-skills/docsify-station-creator
mv /Users/dalwin/.agents/skills/docsify-station-creator /Users/dalwin/Library/CodeRepo/AI/awesome-skills/docsify-station-creator
ln -s /Users/dalwin/Library/CodeRepo/AI/awesome-skills/docsify-station-creator /Users/dalwin/.agents/skills/docsify-station-creator
echo "docsify-station-creator: replaced awesome-skills with .agents version, symlink created"
```

- [ ] **Step 4：对 wiki-creator 重复 Step 1-3（同样逻辑）**

```bash
diff -r /Users/dalwin/.agents/skills/wiki-creator/ /Users/dalwin/Library/CodeRepo/AI/awesome-skills/wiki-creator/ 2>&1 | head -50
echo "---"
find /Users/dalwin/.agents/skills/wiki-creator -name 'SKILL.md' -exec stat -f '%m %N' {} \;
find /Users/dalwin/Library/CodeRepo/AI/awesome-skills/wiki-creator -name 'SKILL.md' -exec stat -f '%m %N' {} \;
```

等用户决策 → 执行 4A 或 4B（与 3A/3B 完全对称，名字替换为 wiki-creator）。

- [ ] **Step 5：验证两者已 symlink**

```bash
ls -la /Users/dalwin/.agents/skills/docsify-station-creator /Users/dalwin/.agents/skills/wiki-creator
```

Expected: 两行均以 `l` 开头（symlink），目标指向 `~/Library/CodeRepo/AI/awesome-skills/<name>`。

---

### Task 3.6：建立 archived_skills/ 索引（在 dalwin-workflow repo 内）

**Files:**
- Create: `~/Documents/AI/dalwin-workflow/archived_skills/README.md`

- [ ] **Step 1：创建索引文件**

````bash
mkdir -p /Users/dalwin/Documents/AI/dalwin-workflow/archived_skills
cat > /Users/dalwin/Documents/AI/dalwin-workflow/archived_skills/README.md <<'EOF'
# Archived Skills 索引

记录从 `~/.claude/skills/` 中移除软链的 skills；源码仍保留在 `~/Library/CodeRepo/AI/awesome-skills/<name>/` 下，需要时随时复链回来。

## 当前 archive 名单（2026-05-26）

| Skill | 源码 SOT | 复链命令 |
|---|---|---|
| svg-logo-creator | `~/Library/CodeRepo/AI/awesome-skills/svg-logo-creator` | `ln -s ~/.agents/skills/svg-logo-creator ~/.claude/skills/svg-logo-creator` |
| resume-generator | `~/Library/CodeRepo/AI/awesome-skills/resume-generator` | `ln -s ~/.agents/skills/resume-generator ~/.claude/skills/resume-generator` |
| app-icon | `~/Library/CodeRepo/AI/awesome-skills/app-icon` | `ln -s ~/.agents/skills/app-icon ~/.claude/skills/app-icon` |

## Archive 准则

- 与现役 skill 职责完全重叠（如 svg-logo-creator 被 gemini-svg-creator 取代）
- 使用频次 < 一年一次（如 resume-generator）
- 用户不再使用该技术栈（如 app-icon 之于 RN/Expo）

## 复链流程

1. 确认源码在 SOT 内可读
2. 执行 `ln -s` 命令（见上表"复链命令"）
3. 在新 Claude 会话里输入触发该 skill 的描述，验证可被 find-skills 命中
EOF
````

- [ ] **Step 2：验证**

```bash
test -f /Users/dalwin/Documents/AI/dalwin-workflow/archived_skills/README.md && head -10 /Users/dalwin/Documents/AI/dalwin-workflow/archived_skills/README.md
```

---

### Task 3.7：最终拓扑验证

- [ ] **Step 1：~/.claude/skills/ 软链数与目标核对**

```bash
echo "=== ~/.claude/skills/ symlinks ==="
ls -la /Users/dalwin/.claude/skills/ | grep '^l'
echo "=== count ==="
ls -la /Users/dalwin/.claude/skills/ | grep -c '^l'
```

Expected: 11 个 symlink；archive 三项（svg-logo-creator / resume-generator / app-icon）不出现在列表。

- [ ] **Step 2：~/.agents/skills/ 全部为 symlink（除 superpowers 软链以外）**

```bash
echo "=== ~/.agents/skills/ entries ==="
ls -la /Users/dalwin/.agents/skills/ | grep -v '^total' | grep -v '^d ' | grep -v '^d.* \.$\|^d.* \.\.$'
echo "=== real dirs left (should be 0 or only ~/.codex/skills view items) ==="
ls -la /Users/dalwin/.agents/skills/ | awk '/^d/ && $NF !~ /^\.{1,2}$/ {print $NF}'
```

Expected: 第二段输出空（或只剩平台预期的内容）；所有原 real dir 都已变 symlink。

- [ ] **Step 3：双跳路径完整可达**

```bash
for name in $(ls /Users/dalwin/.claude/skills/); do
  if [ -L /Users/dalwin/.claude/skills/$name ]; then
    target=$(readlink -f /Users/dalwin/.claude/skills/$name 2>/dev/null)
    [ -n "$target" ] && echo "$name → $target" || echo "$name: BROKEN"
  fi
done
```

Expected: 每个 symlink 都能 resolve 到 SOT 下的真实路径；无 `BROKEN`。

- [ ] **Step 4：Documents/AI/skills/ 已删除**

```bash
test ! -e /Users/dalwin/Documents/AI/skills/ && echo "OK Documents/AI/skills removed" || echo "FAIL still exists"
```

Expected: `OK Documents/AI/skills removed`。

---

### Task 3.8：提交 Phase 3 实施日志

**Files:**
- Create: `~/Documents/AI/dalwin-workflow/docs/superpowers/plans/logs/phase-3-source-migration.md`

- [ ] **Step 1：写 Phase 3 日志**

````bash
cat > /Users/dalwin/Documents/AI/dalwin-workflow/docs/superpowers/plans/logs/phase-3-source-migration.md <<'EOF'
# Phase 3 实施日志：来源单源化迁移

完成时间：(填实际完成日期)

## 变更摘要

### 源单点化
- `~/Documents/AI/skills/` 整目录已删除
- `spec-architect`、`git-merge-conductor` 均归位 `~/Library/CodeRepo/AI/awesome-skills/`
- `~/.agents/skills/` 中原 9 个 real dir + 2 个冲突 dir（docsify-station-creator、wiki-creator）已迁到 SOT，原位置改为 symlink
- `~/.claude/skills/` 双跳关系完整：`.claude → .agents → SOT`

### Archive 软链移除
- `~/.claude/skills/{svg-logo-creator, resume-generator, app-icon}` 已删除
- 源码仍在 `~/Library/CodeRepo/AI/awesome-skills/` 内可恢复
- 复链命令收录到 `~/Documents/AI/dalwin-workflow/archived_skills/README.md`

## 用户决策记录

- spec-architect 选版结果：(填 A 保留 awesome-skills / B 用 Documents 版覆盖)
- docsify-station-creator 选版结果：(填 A / B)
- wiki-creator 选版结果：(填 A / B)

## 验证结果

- `~/.claude/skills/` symlink 数：11（从 14 降到 11）
- `~/.agents/skills/` 实文件目录数：0（全部转为 symlink 或保持原 superpowers 软链）
- 所有双跳路径 resolvable，无 BROKEN

## 下一步

进入 Phase 4：模板沉淀（推迟，首次创建新 skill 时启动）。
EOF
````

- [ ] **Step 2：提交 Phase 3 实施日志 + archived_skills/README.md**

```bash
git -C /Users/dalwin/Documents/AI add dalwin-workflow/docs/superpowers/plans/logs/phase-3-source-migration.md dalwin-workflow/archived_skills/
git -C /Users/dalwin/Documents/AI commit -m "docs(dalwin-workflow): Phase 3 来源单源化迁移实施完成"
```

Expected: 2 files changed，commit 成功。

---

## Phase 4：模板沉淀（DEFERRED）

> 本阶段**不在本次实施范围**。Spec §6 已确认：Tier 2/3 模板"推迟到首次创建新 skill 时启动"。
>
> 触发条件：当用户首次按 "3 次手工重复" 心智规则识别出新 skill 候选并启动 brainstorming → writing-plans 流程时，由那一次的 writing-plans 决定 Tier 2 还是 Tier 3，并在过程中沉淀模板到：
>
> ```
> ~/Documents/AI/dalwin-workflow/templates/
> ├── tier2/SKILL.md.example
> ├── tier2/references/error-cases.md.example
> ├── tier3/SKILL.md.example
> ├── tier3/references/...
> └── tier3/requirements.yaml.example
> ```

无 Task。

---

## 最终验证（跨 Phase 综合）

- [ ] **Step 1：Memory + Hooks + Commands 全景列表**

```bash
echo "=== Memory ==="
ls /Users/dalwin/.claude/projects/-Users-dalwin/memory/

echo "=== Hooks ==="
ls /Users/dalwin/.claude/hooks/

echo "=== Commands ==="
ls /Users/dalwin/.claude/commands/ 2>/dev/null

echo "=== Skills count ==="
ls -la /Users/dalwin/.claude/skills/ | grep -c '^l'
```

Expected:
- Memory: 12 文件（11 seed + MEMORY.md）
- Hooks: 4 文件（tree-suggest.py / uv-python-rewrite.py / sessionstart-domain.py / precompact-memory.py）
- Commands: wrap.md 至少一个
- Skills count: 11

- [ ] **Step 2：settings.json 结构核对**

```bash
python3 -c "
import json
d = json.load(open('/Users/dalwin/.claude/settings.json'))
for event in ['SessionStart', 'PreCompact']:
    entries = d['hooks'].get(event, [])
    has_codeisland = any('codeisland' in h.get('command','') for e in entries for h in e.get('hooks',[]))
    has_new = any('hooks/' in h.get('command','') and 'codeisland' not in h.get('command','') for e in entries for h in e.get('hooks',[]))
    print(f'{event}: codeisland={has_codeisland}, new_hook={has_new}')
"
```

Expected:
```
SessionStart: codeisland=True, new_hook=True
PreCompact: codeisland=True, new_hook=True
```

- [ ] **Step 3：git log 查看本次实施的所有 commit**

```bash
git -C /Users/dalwin/Documents/AI log --oneline -10 -- dalwin-workflow/
```

Expected: 列表至少含
- docs(dalwin-workflow): 落地 2026-05-26 个人工作流实施计划
- docs(dalwin-workflow): Phase 1 memory seed 实施完成
- docs(dalwin-workflow): Phase 2 hooks 与 wrap 命令实施完成
- docs(dalwin-workflow): Phase 3 来源单源化迁移实施完成
- 以及之前已有的 spec 初版 + 复审修订两条

---

## 自审通过项

执行此 plan 前已自审：

1. **Spec 覆盖**：§3 / §4 / §5 / §6 全部映射到 Phase 1-4 的具体 task；§6 显式标注 "DEFERRED"
2. **占位词**：plan 内无 TBD/TODO/"…实现"/"参见 Task N（不给代码）" 等；所有代码、命令、期望输出都显式给出
3. **类型/命名一致性**：memory 文件名（11 个）与 MEMORY.md 索引完全一一对应；hook 文件名与 settings.json 内引用命令路径完全对应；symlink 源 / 目标路径在 Task 3 内多处复用都一致
4. **TDD**：Python hooks 在写完代码后立即 4 个场景测试 + 不阻断测试，先看到 PASS 再进 settings.json 注册
5. **频繁提交**：3 次实施日志 commit + 1 次 plan 自身 commit；commit message 全部符合 `<type>(<scope>): <subject>` 中文规范
6. **可回滚**：settings.json 在 Task 2.6 Step 1 备份；archive 软链有 archived_skills/README.md 留复链命令；memory 文件可整目录删除（最坏情况）
7. **决策点显式**：Task 3.2 与 Task 3.5 在 diff 后等用户在线决策，不擅自选 A/B

---

## 执行选项

**Plan 写完并保存到 `/Users/dalwin/Documents/AI/dalwin-workflow/docs/superpowers/plans/2026-05-26-personal-workflow-implementation.md`。两种执行方式：**

**1. Subagent-Driven（推荐）** — 每个 task 派一个 fresh subagent 执行，task 之间我做 review，迭代快、上下文隔离好。适合"我先看你怎么做，再决定下一步"。

**2. Inline Execution** — 在当前 session 里按 plan 顺序跑，到检查点（Phase 边界、Task 3.2 / 3.5 等待用户决策处）停下让用户 review。适合"一气呵成跑完，关键节点暂停"。

**哪种走？**
