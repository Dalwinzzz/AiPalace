# 个人工作流设计 spec — 2026-05-25

> 范围：dalwin 在本机使用 Codex + Claude 的个人 AI 工作流。覆盖已装 skills 编排、自创 skill 迭代、新 skill 设计、memory/context 加载策略。
>
> 哲学：少而精——完美不是无一分可增，而是无一分可减。同时保持可拓展。

---

## 1. 上下文与目标

### 1.1 用户画像

- 深度使用 Codex + Claude Code 3-4 个月
- 主战场 Java/Spring SaaS 后端（saas 项目，55%）
- AI 工具自建（20%，包括本设计本身）
- 知识与内容沉淀（10%）
- Go/Python 学习方向（15%，未来转后端的预备）
- 偏好系统化思考、直接挑战错误假设、不喜谄媚回应（已在 `~/.claude/CLAUDE.md` 全局加载）

### 1.2 现状盘点

| 维度 | 现状 | 问题 |
|---|---|---|
| 已装 skills | 15 软链 + 14 superpowers + 5 插件命令组 ≈ 50+ | 来源分散 4 目录，3 组重叠（svg、grill、spec-architect 与 brainstorming 链） |
| 自创 skills | git-merge-conductor / docker-best-practices / spec-architect 等已成体系，但散落多目录 | 缺一致模板，缺统一 SOT |
| memory | 仅 1 条（maven-config） | 3-4 个月几乎未沉淀 |
| hooks | tree-suggest / uv-python-rewrite / codeisland 通知桥 | 无 SessionStart 域识别、无 PreCompact memory 评估 |
| CLAUDE.md | 仅全局一份 | 无项目级 override |

### 1.3 工作流形态决策

**双模混合**：
- 复杂任务 / 多步任务 → 走主链 spine（脑暴 → 规划 → 执行 → 核验 → 收束）
- 琐碎/咨询/单次 → 工具腰带，skills 凭描述触发
- 入口由 brainstorming / find-skills 决定走向

### 1.4 设计哲学落地准则

- skills 是 **liability**，不是 asset，每个都要维护，创造门槛要高
- 每条规则只在一个地方持久化（CLAUDE.md / hook / memory 三选一），避免上下文窗口被重复占用
- "可拓展" 不是 "预先建好"，是 "知道下一个该加在哪"

---

## 2. 整体架构：三圈两轴

### 2.1 划分依据（两轴交叉）

| 轴 | 取值 |
|---|---|
| **形态** | Process（流程性，定义"怎么做"）/ Tool（任务性，做某件具体事） |
| **复用面** | 跨域 / 域内 / 长尾 |

交叉后：

| | Process | Tool |
|---|---|---|
| **跨域** | 内圈 spine（主链 + 阶段附属 + meta） | — |
| **域内** | — | 中圈 domain packs（Java / AI 自建 / 学习 / 知识 4 包） |
| **长尾** | — | 外圈 tail（不预热，靠 find-skills + 描述触发） |

### 2.2 量级目标

- 内圈活跃 process skills：**11**（主链 5 + 阶段附属 4 + meta 2）
- 中圈 4 packs × 3-5 件 = **8-15**
- 外圈不限，但 90% 会话不主动触及
- 来源目录：**1 个 SOT + 2 个视图**（双跳 symlink）

### 2.3 两条横向轴

- **memory**：4 类型种子（user / feedback / project / reference），15 条骨干 + PreCompact 增量评估
- **hooks/context**：SessionStart 输出工作域索引 + 置信度；PreCompact 输出 memory 评估被动 hint；`/wrap` slash command 在 `/clear` 之前由用户主动触发评估

---

## 3. Section ①：Memory 策略

### 3.1 去重映射

下列内容**已在他处持久化**，**不再写入 memory**，避免上下文窗口浪费：

| 内容 | 现有落地位置 |
|---|---|
| Structured Thinking / Objective Peer / 中文默认 | `~/.claude/CLAUDE.md`（每会话全局加载） |
| Context7 MCP 优先使用 + 流程 | `~/.claude/CLAUDE.md` |
| Git commit 规范 | `~/.claude/git-commit-convention.txt` + `PreToolUse Bash(git commit*)` 条件注入 |
| `tree` 替代 `ls -R` / `find -type d` | `~/.claude/hooks/tree-suggest.py`（PreToolUse deny + 建议） |
| `python` → `uv run python` | `~/.claude/hooks/uv-python-rewrite.py`（PreToolUse 改写） |

### 3.2 种子清单（15 条）

#### user（2 条）

- **u1**：主战场 Java/Spring SaaS（55%）+ AI 工具自建（20%）+ 知识沉淀（10%）+ Go/Python 学习方向（15%）
- **u2**：Codex 与 Claude 双工具协作；偏好共享源 + symlink，两边共用同一份 skill 更新

#### feedback（8 条）

- **f1**：大任务接受"review → brainstorming → spec → 实施"主链，每步沉淀为 repo-local 文档，不停留在聊天
- **f2**：任务**小且简单**时，落盘 spec 后默认直接执行，不再确认方向；任务大/复杂时，即便 spec 已落盘也先简短确认方向再动手
- **f3**：代码修复默认 "确认入口/调用点 → 最小化改动服务层 → 编译/模块静态验证 → `git diff --check`"
- **f4**：局部兼容修复优先在现有入口最小改动，不主动抽新类/扩配置
- **f5**：审核/回显/副作用类问题做全链路复扫，不只改单点
- **f6**：**默认**将单元测试与源码拆成 2 个 commit 提交（方便 IDEA 复核）
- **f7**：review 默认"独立、客观、批判"口径，主动给"预期外的"意见
- **f8**："置空 worktree" = `git switch --detach <base>` + `git branch -D <branch>`，**不**等于清理未跟踪文件

#### project（3 条）

- **p1**：saas 三大 sub-repo：`skc-nursery`（worktree）/ `skc-activity`（IdeaProject）/ `skciotdevice`（IdeaProject）；Constants.PROJECT_NAME_JINAN 是高频项目白名单
- **p2**：spec 文件落到 `docs/spec-architect/YYYY-MM/` 时**遵循 .gitignore**；仅当用户明确要求纳入 git 追踪才 `git add -f`
- **p3**：Maven 配置（迁移自现有 `maven-config.md` 并保留）—— 仓库 `/Users/dalwin/Library/Repository`、settings `/Users/dalwin/Library/ConfigFile/maven/saas/settings.xml`；mvn 命令必带 `-s ... -Dmaven.repo.local=...`

#### reference（2 条）

- **r2**：AI skills 主目录 `~/Library/CodeRepo/AI/`（含 `awesome-skills/`、`superpowers/` fork、`skills/` 三仓）
- **r3**：跨工具事实唯一源：codex memory 在 `~/.codex/memories/MEMORY.md`；claude memory 在 `~/.claude/projects/-Users-dalwin/memory/`；两侧定期对账

> r1（Notion 工作区 URL）已删除——MCP 实时获取，无需 sediment。

### 3.3 物理布局

```
~/.claude/projects/-Users-dalwin/memory/
├── MEMORY.md                          # 索引
├── user_role.md                       # u1, u2
├── feedback_workflow.md               # f1, f2, f3
├── feedback_minimal_change.md         # f4, f5
├── feedback_commit_split.md           # f6
├── feedback_review_stance.md          # f7
├── feedback_worktree_semantics.md     # f8
├── project_saas_repos.md              # p1
├── project_spec_location.md           # p2
├── maven-config.md                    # p3（现有，扩充）
├── reference_skills_root.md           # r2
└── reference_cross_tool_memory.md     # r3
```

切分原则：每个文件 1 个语义簇，方便 description 触发命中，避免大块文件全量加载。

### 3.4 增量写入（PreCompact）

- PreCompact hook 注入被动 hint，建议 Claude 评估"本次会话是否产生新的可入 memory 事实"
- 决策原则：
  1. 跨会话价值（特定任务细节不写；可复用于未来类似任务才写）
  2. 去重（先查 CLAUDE.md / hooks / 现有 memory 是否已覆盖）
  3. 4 类型分流（fact → reference；偏好/纠正 → feedback；角色变化 → user；项目级事实 → project）

---

## 4. Section ②：Hooks

### 4.1 新增 2 个 hook + 1 个 slash command

| 路径 | 角色 |
|---|---|
| `~/.claude/hooks/sessionstart-domain.py` | SessionStart → cwd 探测 → 输出工作域索引 + 置信度 |
| `~/.claude/hooks/precompact-memory.py` | PreCompact → 注入被动 memory 评估 hint，不打断压缩 |
| `~/.claude/commands/wrap.md` | 自定义 slash command；用户在 `/clear` 之前主动调用以触发 memory 评估 |

现有 hook（`tree-suggest.py`、`uv-python-rewrite.py`、`codeisland-hook.sh`）保持不动。

### 4.2 SessionStart：索引 + 置信度

不再 dump skill 描述，只输出**置信度索引**，Claude 看到后自己决定是否用 `find-skills` 展开对应 pack。注入体积控制在 ~50 tokens。

#### 置信度计算（确定性，无 LLM 介入）

| 域 | 信号 → 权重 | 阈值 |
|---|---|---|
| java/spring | pom.xml=0.5 / `*/pom.xml`=0.3 / mvnw=0.2 / src/main/java=0.3 / `*/src/main/java`=0.2 / .idea=0.1 | ≥0.5 主域 |
| ai_build | 路径含 `awesome-skills`=0.4 / `superpowers/skills`=0.4 / `.claude/skills`=0.4 / dir 匹配 `skill-*`=0.3 / dir 匹配 `AI/*`=0.2 | ≥0.5 主域 |
| knowledge | `/docs/`=0.15 / `/wiki/`=0.3 / Notion 同步目录=0.5 | ≥0.5 主域 |
| learning | go.mod=0.6 / `*.go` 文件=0.4 / 学习目录关键词=0.3 | ≥0.5 主域 |

每域累加，cap 1.0；多域可并列。**<0.3 直接不出现在索引里**。

#### 注入格式

主域明确：

```
[工作域] java/spring=0.90; pack-java: spec-architect, grill-with-docs, git-merge-conductor, requesting-code-review, security-review
```

多域并列：

```
[工作域] java/spring=0.70, ai_build=0.60
  pack-java: spec-architect, grill-with-docs, git-merge-conductor, requesting-code-review, security-review
  pack-ai-build: skill-creator, writing-skills, skill-security-audit, subagent-driven-development, claude-api
```

无主域：

```
[工作域] 无主域；仅 spine 可用
```

### 4.3 PreCompact：被动信号，绝不打断

输出固定一行 hint：

```
[memory 候选评估·建议] 若本次会话已沉淀新事实，可在压缩前按 CLAUDE.md auto memory 规则写入。本提示为建议性，无候选则忽略；不影响压缩流程。
```

实现约束：
- 不设 `permissionDecision`（不阻断）
- 仅用 `additionalContext` 字段
- `timeout: 5` 兜底；脚本本身不做任何阻塞 I/O

### 4.4 `/clear` 路径补偿：`/wrap` slash command

核实结论：**Claude Code 没有 PreClear hook**——`/clear` 既不触发 `SessionEnd` 也不触发 `UserPromptSubmit`，`SessionEnd` 的 `"clear"` matcher 是反向指向"上一次会话以 clear 终止"。

补偿方案：

```
~/.claude/commands/wrap.md
---
description: 在 /clear 之前评估并写入 memory 候选
---
按 ~/.claude/CLAUDE.md 的 auto memory 规则评估本会话候选并写入 memory；
完成后输出 "✅ memory 评估完毕，可执行 /clear" 给用户。
```

用户习惯：想清理时先敲 `/wrap`，再 `/clear`。

### 4.5 settings.json 改动（最小化）

在现有 `hooks` 下追加 2 条，不动其它（codeisland 系列保留）：

```json
"SessionStart": [
  { /* 现有 codeisland，不动 */ },
  { "matcher": "",
    "hooks": [{ "type": "command",
                "command": "python3 ~/.claude/hooks/sessionstart-domain.py",
                "timeout": 5 }] }
],
"PreCompact": [
  { /* 现有 codeisland，不动 */ },
  { "matcher": "",
    "hooks": [{ "type": "command",
                "command": "python3 ~/.claude/hooks/precompact-memory.py",
                "timeout": 5 }] }
]
```

### 4.6 风险与约束

| 项 | 状态 |
|---|---|
| SessionStart 仅索引 + 置信度，避免无效读取 | ✅ 设计层守住 |
| PreCompact 不打断压缩 | ✅ 不设 permissionDecision |
| PreClear hook 不存在 | ✅ 已核实；`/wrap` 作为用户主动调用的补偿 |
| 误判工作域 | 索引含完整置信度信号，Claude 可自行折扣信任 |
| Python 启动开销 | 纯 stdlib，<50ms；timeout=5s 兜底 |

---

## 5. Section ③：三圈剪枝 + 单源化

### 5.1 全量分类表

#### 内圈 spine（11 件 always-available）

| Skill | 角色 |
|---|---|
| brainstorming | 主链：脑暴 → spec |
| writing-plans | 主链：spec → 实施计划 |
| executing-plans | 主链：按计划执行 |
| verification-before-completion | 主链：声明完成前核验 |
| finishing-a-development-branch | 主链：收束分支 |
| test-driven-development | 阶段附属：执行阶段 TDD 触发 |
| systematic-debugging | 阶段附属：bug/异常触发 |
| receiving-code-review | 阶段附属：收到 review 时处理 |
| using-git-worktrees | 机制附属：多分支隔离 |
| find-skills | meta：检索 skill |
| using-superpowers | meta：skills 使用规范 |

#### 中圈 4 packs

| pack | 成员 |
|---|---|
| **pack-java** | spec-architect / grill-with-docs / git-merge-conductor / requesting-code-review / security-review |
| **pack-ai-build** | skill-creator / writing-skills / skill-security-audit / subagent-driven-development / claude-api |
| **pack-knowledge** | Notion:find/search/create-page/create-task/database-query / deep-research |
| **pack-learning** | grill-me / claude-api |

#### 外圈 tail（不预加载）

ai-pdf-builder / docx / frontend-design / typescript-lsp / docker-best-practices / agent-sdk-dev:new-sdk-app / dispatching-parallel-agents / Notion:tasks:setup-explain-diff-build-plan / 内置 commands（run / verify / init / code-review / review / loop / schedule / update-config / keybindings-help / fewer-permission-prompts）等。

#### Archive（移除 `~/.claude/skills` 软链，源码保留）

| Skill | 原因 |
|---|---|
| svg-logo-creator | 与 gemini-svg-creator 重叠，留更新更频繁的 gemini-svg |
| resume-generator | 一年用一次，留源码、不挂软链 |
| app-icon | RN/Expo 专属，不在该栈 |

#### 决策对照（重叠/冗余项）

| 项 | 处理 |
|---|---|
| spec-architect vs brainstorming+writing-plans | 同时保留分场景：小/简任务走 spec-architect 直接落盘；大/复任务走主链 |
| receiving-code-review vs requesting-code-review | receiving 内圈、requesting 中圈 pack-java |
| subagent-driven-development vs dispatching-parallel-agents | subagent 进中圈 pack-ai-build；dispatching 进外圈 |
| review 类心智模型 | 内圈留 receiving-code-review；其它（plugin code-review / built-in /review 等）归外圈 |
| svg-logo-creator vs gemini-svg-creator | 保 gemini-svg |
| grill-me vs grill-with-docs | grill-me 进 pack-learning（学习时反向问答）；grill-with-docs 进 pack-java（spec/plan 反向挑战 + ADR/CONTEXT.md inline 更新） |

### 5.2 来源单源化（双跳 symlink）

#### 当前散落

```
~/.agents/skills/        ← 主存放点（含实文件 + 部分软链）
~/Documents/AI/skills/   ← 历史遗留（git-merge-conductor, spec-architect 旧拷贝）
~/Library/CodeRepo/AI/   ← Git 仓库源（awesome-skills/, superpowers/, skills/）
~/.claude/skills/        ← 软链视图，多数指向 ~/.agents/skills
```

#### 目标 SOT

```
~/Library/CodeRepo/AI/         ← 唯一 SOT（git 仓库）
  ├── awesome-skills/          ← 自创/精选（docker-best-practices, spec-architect, git-merge-conductor, ...）
  ├── superpowers/             ← fork
  └── skills/                  ← 外部克隆（grill-me, grill-with-docs 等）

~/.agents/skills/{name}        ← 软链 → ~/Library/CodeRepo/AI/.../skill-name
~/.claude/skills/{name}        ← 软链 → ~/.agents/skills/{name}  （双跳，保 codex 共享）
~/Documents/AI/skills/         ← 弃用，迁移后删除
```

> 双跳的好处：`~/.agents/skills` 作为 codex 与 claude 共享注册表，符合 codex memory 中既定的"共享源 + symlink"偏好。

### 5.3 迁移步骤

| 步骤 | 操作 | 风险 |
|---|---|---|
| 1 | `diff -r ~/Documents/AI/skills/{spec-architect,git-merge-conductor}` vs `~/Library/CodeRepo/AI/awesome-skills/{spec-architect,git-merge-conductor}` → 列差异 | 低 |
| 2 | 用户确认/选择较新版本 → 写回到 `~/Library/CodeRepo/AI/awesome-skills/`（SOT 单点）| 中 |
| 3 | `~/Documents/AI/skills/` 整目录确认空后删除 | 低 |
| 4 | 移除 `svg-logo-creator` / `app-icon` / `resume-generator` 在 `~/.claude/skills/` 的软链；不动源 | 低 |
| 5 | 把 `~/.agents/skills/` 中**所有实文件目录**（11 个：`ai-pdf-builder` / `app-icon` / `deep-research` / `docsify-station-creator` / `docx` / `find-skills` / `gemini-svg-creator` / `resume-generator` / `skill-security-audit` / `svg-logo-creator` / `wiki-creator`）迁到 `~/Library/CodeRepo/AI/` 下合适子目录，原位置改软链。分桶规则（D4-A）：工具中性 → `awesome-skills/`；仅 Claude 风格 → `skills/`；archive 类（`svg-logo-creator` / `resume-generator` / `app-icon`）也按上述规则分桶，仅在 `~/.claude/skills` 不挂软链 | 中（需逐个核） |
| 6 | 建立 `archived_skills/` 目录（在 dalwin-workflow repo 内），记录移出的软链清单 + 复链方法 | 低 |

### 5.4 量级对照

| | 改前 | 改后 |
|---|---|---|
| `~/.claude/skills` 软链数 | 15 | 12 |
| 跨域 process（内圈活跃）| ~14 | 11 |
| 中圈活跃 skills | 散乱 | 4 packs × 3-5 ≈ 14 |
| 长尾（外圈）| 25+ | 14（按需触发）|
| 来源目录 | 4 | 1 SOT + 2 视图 |

---

## 6. Section ④：自创 skill 模板 + 迭代规则

### 6.1 创建新 skill 的判断门：心智规则（D1-A）

不设自动追踪、不设候选日志。当用户**自己意识到**"某动作/姿势手工重复 ≥ 3 次"时，主动评估：

```
某动作/姿势手工重复 ≥ 3 次
  ↓
现有 spine + 工具能拼出吗？  → 能：不造，沿用
  ↓ 不能
域包内有近邻 skill 可扩展吗？  → 能：升级既有 skill（commit message 承担理由）
  ↓ 不能
可造新 skill：走 brainstorming → writing-plans → executing-plans → verification → finishing 主链
```

> Skills 是 liability，不是 asset。创造门槛要高。

### 6.2 模板（Tier 2/3，按需参考，不强制 scaffold）

最简单的 skill（单 SKILL.md）由 Claude/codex/superpowers 自带约束承担最佳实践，**不再单独提供 Tier 1 模板**。Tier 2/3 模板保留在 `dalwin-workflow/templates/` 下，写新 skill 时按需 `cp` 参考。

#### Tier 2 — 带 references/ 的 skill

```
<name>/
├── SKILL.md                    # 主入口 + 决策树（≤100 行）
├── references/                 # 主入口不展开的细节
│   ├── error-cases.md
│   └── examples.md
└── assets/                     # 模板（如有）
```

#### Tier 3 — Pipeline skill（多阶段有状态）

```
<name>/
├── SKILL.md                    # 阶段总览 + 安全不变量
├── references/
│   ├── stage-0-setup.md
│   ├── stage-1-classify.md
│   └── negative-constraints.md
├── assets/
│   └── <templates>
├── requirements.yaml           # 状态机 schema（如适用）
└── docs/adr/                   # 决策记录（需要时才创建）
```

`git-merge-conductor` 是 Tier 3 标杆，可直接参考。

### 6.3 迭代规则

| 触发 | 动作 |
|---|---|
| 用户对该 skill 输出做出**相同纠正** ≥ 3 次 | 升级 skill 的步骤/约束（commit message 写清理由） |
| 某边界 case 让该 skill 失败/越界 ≥ 2 次 | 加 safety invariant（commit message 写清理由） |
| 该 skill 6 个月触发次数 < 3 次 | 评估是否降级（中圈 → 外圈，或外圈 → archive）|
| Claude Code 引入新原语覆盖了该 skill | 评估废弃 |
| description 反复匹配错（误触发/漏触发）| 优先重写 description |

**变更理由载体**（D3-B）：默认用 git commit message 承担；遇到需要长期追溯/争议大的决策，再单独写 ADR 到 `<skill>/docs/adr/` 或 `dalwin-workflow/docs/adr/`。

### 6.4 跨工具共享策略（D4-A）

| 决策 | 标准 |
|---|---|
| 放 `~/Library/CodeRepo/AI/awesome-skills/`（codex + claude 共享） | 工具语义中性（不依赖 Claude Code 或 codex 任一方专属能力） |
| 放 `~/Library/CodeRepo/AI/skills/`（仅 claude，外部克隆/superpowers 风格） | 依赖 Claude Code 专属语义（如 Agent 工具、TaskCreate 等） |
| 放 codex 私有目录 | 仅用 codex CLI 特定能力（如 execpolicy `rules/`） |

举例：
- `git-merge-conductor` → awesome-skills
- `spec-architect` → awesome-skills
- `subagent-driven-development` → 仅 claude（superpowers 内置，不动）

### 6.5 拓展机制（不设月度 eval，D5-B）

不主动 review，**问题发生时单点修**：

| 信号 | 单点修动作 |
|---|---|
| skill 误触发 / 漏触发 | 重写该 skill 的 description |
| 内圈某条主链阶段反复被跳过 | 评估该阶段是否真的属于主链 |
| memory 总条数过少（如几个月仍 < 5）| 评估 PreCompact hook 是否正常工作 |
| 新工作域占比超过 10% | 评估新增 pack |

---

## 7. 实施顺序建议

按"代价低 → 价值高"顺序，每步独立可验证：

1. **memory seed 写入**（最易交付，立即有价值）
   - 在 `~/.claude/projects/-Users-dalwin/memory/` 写入 15 条种子，更新 `MEMORY.md` 索引
   - 合并 `maven-config.md` 内容到 `p3` 节
2. **新增 2 个 hook + `/wrap` slash command**
   - 写 `sessionstart-domain.py`、`precompact-memory.py`
   - 写 `~/.claude/commands/wrap.md`
   - 修改 `~/.claude/settings.json` 追加 hook 引用
3. **来源单源化迁移**（动文件，需谨慎）
   - diff `~/Documents/AI/skills/` vs `awesome-skills/`，确认版本后迁移
   - 移除 archive 软链（svg-logo / resume / app-icon）
   - 重排 `~/.agents/skills` 实文件到 SOT，改软链
   - 在 `dalwin-workflow/archived_skills/` 留下复链清单
4. **模板沉淀**（推迟到首个新 skill 创建时，按需写 Tier 2/3 模板示例到 `dalwin-workflow/templates/`）

每步完成后做一次 `verification-before-completion`，确认不影响现有工作流。

---

## 8. 拓展性

| 加什么 | 加在哪 | 触发标准 |
|---|---|---|
| 新 process skill（跨域） | 内圈 spine（罕见，需充分理由） | 跨域出现 ≥3 次手工重复 |
| 新 domain skill | 对应 pack；若域不在 4 个已有 pack 里，先评估新增 pack | 单域出现 ≥3 次手工重复 |
| 长尾工具 skill | 外圈（不预加载） | 单次有用即可 |
| 新 pack（域） | 仅当用户工作分布出现 ≥10% 占比的新域时 | 工作分布事实变化 |
| 新 hook | 新原语（如新 hook 事件）出现，且能消除现有手工痛点 | Claude Code 升级 |
| 新 memory 类别 | **不允许**（4 类已覆盖；新增反而违反规范） | — |

---

## 9. 风险与降级

| 风险 | 缓解 |
|---|---|
| SessionStart 误判工作域 | 注入仅"索引 + 置信度"，Claude 可自行折扣信任；置信度 <0.3 直接不出现 |
| PreCompact 打断压缩 | 仅 additionalContext，不设 permissionDecision |
| `/clear` 时未保存的事实丢失 | `/wrap` 习惯化；遗忘时承担信息损失（不致命，下次会重新积累） |
| 来源迁移过程中破坏现有软链 | 迁移步骤按"diff → 选版本 → 写 SOT → 改软链"严格分段；每步可回滚 |
| memory 写入 fuzzy（漏写/误写） | 接受 fuzzy；问题发生时单点修 description / 调整种子 |
| codex / claude memory 不同步 | r3 reference 记录两侧位置；定期对账放 dalwin-workflow TODO |
| 模板被滥用变重 | Tier 2/3 仅"按需参考"，不强制 scaffold；最简单 skill 由自带约束承担 |

---

## 10. 关键决策一览

| # | 决策项 | 最终选项 |
|---|---|---|
| **核心** | 主骨架方案 | A. 三圈两轴（process/tool × 跨域/域内/长尾） |
| **核心** | 工作流形态 | 双模混合（复杂走主链；琐碎走腰带） |
| **D1** | 新 skill 创建门 | A. 心智规则（用户主动判断 3 次重复） |
| **D2** | Skill 模板 | 改造：去掉 Tier 1；保留 Tier 2/3 按需参考 |
| **D3** | 变更理由载体 | B. 默认 commit message；需要时再 ADR |
| **D4** | 跨工具共享 | A. 工具中性 → awesome-skills；Claude 专属 → skills；codex 专属 → codex 私有 |
| **D5** | 月度 eval | B. 不设；问题发生时单点修 |
| **D6** | spec 文档位置 | `~/Documents/AI/dalwin-workflow/`（独立 namespace，跟踪工作流演化史） |

---

## 11. 涉及修改的文件 / 目录清单

| 路径 | 改动类型 |
|---|---|
| `~/.claude/projects/-Users-dalwin/memory/MEMORY.md` | 改（追加索引） |
| `~/.claude/projects/-Users-dalwin/memory/*.md` | 新增 11 个 seed 文件（详见 §3.3） |
| `~/.claude/projects/-Users-dalwin/memory/maven-config.md` | 改（扩充 p3） |
| `~/.claude/hooks/sessionstart-domain.py` | 新增 |
| `~/.claude/hooks/precompact-memory.py` | 新增 |
| `~/.claude/commands/wrap.md` | 新增 |
| `~/.claude/settings.json` | 改（追加 2 个 hook 引用） |
| `~/.claude/skills/{svg-logo-creator, resume-generator, app-icon}` | 删（软链；不动源） |
| `~/.agents/skills/{ai-pdf-builder, deep-research, ...}` | 改（实文件 → 软链到 SOT） |
| `~/Library/CodeRepo/AI/awesome-skills/{spec-architect, git-merge-conductor}` | 改（如 Documents/AI/skills 有更新版本） |
| `~/Documents/AI/skills/` | 删（迁移后） |
| `~/Documents/AI/dalwin-workflow/archived_skills/README.md` | 新增（移出的软链清单 + 复链方法） |
| `~/Documents/AI/dalwin-workflow/templates/{tier2,tier3}.md` | 推迟到首次创建 skill 时新增 |

---

## 12. 复审条件（什么时候应该重新看这份 spec）

- 工作分布发生显著变化（如 Go/Python 占比从 15% 升到 ≥ 30%）
- 内圈 spine 数量自然超过 13 / 中圈超过 20
- Claude Code 引入颠覆性新原语（如 PreClear hook、新的 memory 子系统）
- 某次"心智规则"触发的 skill 在 1 个月内被否决/废弃 ≥ 2 次（说明 D1-A 心智规则失效）
- Codex 与 Claude 的 memory 系统出现不可调和的分歧

---

*本文档将随实施进度滚动更新；后续每个里程碑产出实施记录，存放在 `~/Documents/AI/dalwin-workflow/docs/`。*
