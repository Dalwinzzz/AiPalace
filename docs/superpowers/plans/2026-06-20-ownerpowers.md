# ownerpowers Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 AiPalace 建一个公司项目专用、复杂度分档（T0/T1/T2）、轻负重的统一工作流 skill `ownerpowers`，融合并增强 `biz-workflow`，蒸馏吸收 superpowers 的三纪律与 worktree/subagent 能力。

**Architecture:** 单个 `skills/mine/ownerpowers/` skill（SKILL.md 核心 + workflows/disciplines/policies/references 子文件），registry 登记、双工具 symlink 派生；cwd-gated 指针经现有 `sessionstart-domain.py` 注入；superpowers 降级为 ask-first 兜底（去注入 + CLAUDE.md override 中和铁律）；biz-workflow 验证期共存。

**Tech Stack:** Markdown skill 文件；`tools/skillctl.py`（sync/doctor）；`registry.yaml`；Python hook `sessionstart-domain.py`。

## Global Constraints

- 设计依据：[2026-06-20-ownerpowers-design.md](../specs/2026-06-20-ownerpowers-design.md)（spec 为准，本计划实现它）。
- SOT 唯一手改入口是 `registry.yaml` + `skills/` 真身；**禁止手碰挂载点派生软链**（P2）。
- 每次动 registry 后：`python3 tools/skillctl.py sync --dry` → `sync` → `doctor`，**doctor 必须保持全绿**（基线）。
- 分支命名硬规范：`<工具>/<类型-taskName>/<日期_版本号>`（工具∈claude/codex；类型∈feature/fix/refactor；类型与 taskName 用连字符 `-`，冒号被 git 拒绝）。例：`claude/feature-ownerpowers/20260620_v1.0.0`。
- 三档硬标准、决策点门控（T0不停/T1停②/T2停①②）、不可逆护栏全档通用 —— 严格按 spec §4/§5。
- 公司项目路径（v1）：`~/Library/IdeaProject/ZhiJin/**`（路径集做成可扩展常量）。
- commit-msg 格式：`<type>(<scope>): <subject>`，结尾 `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`。
- 本次在分支上做：先 `git checkout -b claude/feature-ownerpowers/20260620_v1.0.0`。

---

### Task 1: 脚手架 + SKILL.md 核心（triage 分诊 + 线×档路由 + 决策点门控）

**Files:**
- Create: `skills/mine/ownerpowers/SKILL.md`
- Modify: `registry.yaml`（在 mine 段加 `ownerpowers`）

**Interfaces:**
- Produces: skill 名 `ownerpowers`；其 SKILL.md 引用子路径 `workflows/{feature-dev,ops-triage}.md`、`disciplines/{tdd,rca,verify}.md`、`policies/{worktree,subagent}.md`、`references/step-*.md`（后续 Task 创建）。

- [ ] **Step 1: 建 SKILL.md**

内容要点（~100 行，frontmatter description 写公司项目开发/排查触发词）：
1. frontmatter：`name: ownerpowers`；`description:` 含"公司项目端到端开发/排查；做功能/改字段/加接口/查 bug/线上报错/数据对不上"等触发词 + "仅公司项目（ZhiJin/SunkidCloud/syzh）"限定 + "复杂度分档 T0/T1/T2"。
2. **第一步 triage 分诊**：先判线（需求开发线 / 运维排查线 / 杂活直做，二选一，模糊则问），再按 spec §4 升档阶梯判档（默认 T0，命中条件升 T1/T2）。
3. **线×档路由表**（spec §3 矩阵原样）→ 指向对应 workflow + 档位约束。
4. **决策点门控**（spec §5）：T0 不停 / T1 停② / T2 停①② + 🚧不可逆护栏全档通用。
5. **横切**：委托表（SQL→sql-expert-dba / 设计→spec-architect / 契约→Apifox）、状态播报、superpowers ask-first 兜底（需重 skill 先问用户）。
6. 各能力指向子文件：纪律→`disciplines/`，worktree/subagent→`policies/`，公共步骤→`references/`。

- [ ] **Step 2: registry 登记**

`registry.yaml` 的 `# ---- mine（原创） ----` 段加一行：
```yaml
  ownerpowers:                        {source: mine, category: workflow, tier: core}
```

- [ ] **Step 3: sync --dry 验证**

Run: `python3 tools/skillctl.py sync --dry`
Expected: 输出含 `ownerpowers`，无报错（注意现网 core/extra 多为外来非受管软链，"保护跳过"属正常）。

- [ ] **Step 4: doctor 校验**

Run: `python3 tools/skillctl.py doctor`
Expected: `✓ 全部通过，无漂移`（mine 类无需 _SOURCE.md，门槛 1-4 满足即可）。

- [ ] **Step 5: commit**

```bash
git add skills/mine/ownerpowers/SKILL.md registry.yaml
git commit -m "feat(ownerpowers): 脚手架 + triage 核心 SKILL.md 与 registry 登记"
```

---

### Task 2: disciplines/（TDD / RCA / verify 三纪律）

**Files:**
- Create: `skills/mine/ownerpowers/disciplines/tdd.md`
- Create: `skills/mine/ownerpowers/disciplines/rca.md`
- Create: `skills/mine/ownerpowers/disciplines/verify.md`

**Interfaces:**
- Consumes: SKILL.md 路由到 disciplines（Task 1）。
- Produces: 三纪律细则，被 workflows（Task 4）引用。

- [ ] **Step 1: 落 tdd.md**

照 [dev-discipline spec §8.2](file:///Users/dalwin/Documents/AI/dalwin-workflow/docs/superpowers/specs/2026-06-19-superpowers-distillation-design.md) 的 `references/tdd.md` 完整草稿落地（RED→GREEN→REFACTOR、Java/JUnit·Go/testing 落点、syzh Maven 命令、合理化对照表、红旗清单）。

- [ ] **Step 2: 落 rca.md**

照 dev-discipline spec §8.3 完整草稿落地（4 阶段、≥3 次修不好→质疑架构、Spring/Go 常见根因入口、红旗）。

- [ ] **Step 3: 落 verify.md**

照 dev-discipline spec §8.4 完整草稿落地（Gate Function、声明↔证据表、最小验证命令模板、红旗、与决策点②叠加）。

- [ ] **Step 4: doctor**

Run: `python3 tools/skillctl.py doctor`
Expected: 全绿（新增子文件不影响门槛）。

- [ ] **Step 5: commit**

```bash
git add skills/mine/ownerpowers/disciplines/
git commit -m "feat(ownerpowers): 蒸馏 TDD/RCA/verify 三纪律细则"
```

---

### Task 3: policies/（worktree + subagent 能力配置）

**Files:**
- Create: `skills/mine/ownerpowers/policies/worktree.md`
- Create: `skills/mine/ownerpowers/policies/subagent.md`

**Interfaces:**
- Produces: 被 references 探针（Task 5）与 workflows（Task 4）引用的能力策略。

- [ ] **Step 1: 落 worktree.md**

照 spec §7.1：自动触发条件（T2 需求线 / 并行互不依赖任务）+ 分支命名硬规范 `<工具>/<类型:taskName>/<日期_版本号>`（含 3 个示例）+ "自动起 worktree 无需停，但代码改动仍走决策点①②" 的边界说明。

- [ ] **Step 2: 落 subagent.md**

照 spec §7.2：三触发条件（并行 fan-out / 探查卸载-核心准则 / 状态文件协同）+ 配置（模型一律 opus、effort 按复杂度）+ 调度纪律（产出可验证或落状态文件、主控走 verify 核对）+ 档位适用（探查卸载任何档、fan-out/状态协同一般 T2）。

- [ ] **Step 3: doctor + commit**

```bash
python3 tools/skillctl.py doctor   # 期望全绿
git add skills/mine/ownerpowers/policies/
git commit -m "feat(ownerpowers): worktree/subagent 能力策略（含分支命名规范）"
```

---

### Task 4: workflows/（feature-dev + ops-triage，tier-aware 融合增强）

**Files:**
- Create: `skills/mine/ownerpowers/workflows/feature-dev.md`
- Create: `skills/mine/ownerpowers/workflows/ops-triage.md`
- Read（蒸馏来源）：`skills/mine/biz-workflow/workflows/{feature-dev,ops-triage}.md`

**Interfaces:**
- Consumes: disciplines（Task 2）、policies（Task 3）、references（Task 5）。
- Produces: 两条线的 tier-aware 剧本。

- [ ] **Step 1: 落 feature-dev.md**

以 biz-workflow `workflows/feature-dev.md` 为底，按 spec §3/§8 增强：
- 每步标注**档位适用**（T0 跳设计直接改+self-check；T1 跳设计、引用 `disciplines/verify.md`、停②；T2 先 `spec-architect` 设计→引用 `disciplines/tdd.md`→verify→停①②）。
- 编码步骤埋 worktree 探针（引用 `policies/worktree.md`：T2 自动起 worktree）。
- 多部件时埋 subagent 探针（引用 `policies/subagent.md`）。

- [ ] **Step 2: 落 ops-triage.md**

以 biz-workflow `workflows/ops-triage.md` 为底增强：
- T0 一眼修+verify；T1 RCA 按需→修→verify→停②；T2 强制 `disciplines/rca.md` 4 阶段→根因定调①→修→回归测试→verify→停②。
- 排查步骤埋探查卸载 subagent 探针（大量探查只需结论时派 subagent，引用 `policies/subagent.md` 触发②）。

- [ ] **Step 3: doctor + commit**

```bash
python3 tools/skillctl.py doctor
git add skills/mine/ownerpowers/workflows/
git commit -m "feat(ownerpowers): tier-aware 需求/运维剧本（融合 biz-workflow + 三纪律/探针）"
```

---

### Task 5: references/（step-A…F，继承 biz-workflow + 埋探针）

**Files:**
- Create: `skills/mine/ownerpowers/references/step-A-api-contract.md` … `step-F-triage-report.md`（6 个）
- Read（来源）：`skills/mine/biz-workflow/references/step-*.md`

**Interfaces:**
- Consumes: policies（Task 3）。
- Produces: 公共步骤库 + worktree/subagent 探针埋点。

- [ ] **Step 1: 复制 6 个 step 文件**

把 biz-workflow `references/step-{A,B,C,D,E,F}-*.md` 内容原样搬入 ownerpowers `references/`（委托对象、Maven 命令、提交规范等不变）。

- [ ] **Step 2: 埋探针**

- `step-B-code-locate.md` 末尾加探针：定位涉及 2+ 独立模块/文件组、或需大量探查只取结论时 → 按 `policies/subagent.md` 派 subagent。
- `step-C-build-test.md` 加探针：T2 需求线进入编码前 → 按 `policies/worktree.md` 起 worktree。

- [ ] **Step 3: doctor + commit**

```bash
python3 tools/skillctl.py doctor
git add skills/mine/ownerpowers/references/
git commit -m "feat(ownerpowers): 继承 biz-workflow 公共步骤 + worktree/subagent 探针埋点"
```

---

### Task 6: CLAUDE.md override（中和 superpowers "1%→MUST" 铁律，双工具）

**Files:**
- Modify: `~/.claude/CLAUDE.md`（全局，真身）
- Modify: `~/.codex/AGENTS.md`（全局，真身）

**Interfaces:**
- Consumes: 无（独立指令层）。
- Produces: 让 ownerpowers 的档位裁量优先于 superpowers 强制规则。

- [ ] **Step 1: 加 override 段（两文件同写）**

加一节"superpowers 流程裁量权（覆盖 using-superpowers 强制约束）"：公司项目走 ownerpowers triage 分档；`using-superpowers` 的"1% 相关就必须用/你没有选择"**不适用于常规任务**，由模型按档位判断；superpowers 重 skill 仅在 ownerpowers 判定需要时 ask-first 调用。依据：superpowers 自身 Instruction Priority（用户指令优先）。

- [ ] **Step 2: 验证生效**

新开一个 `claude` 会话（cwd 任意），确认 override 段进入上下文、未与既有规则冲突。

- [ ] **Step 3: commit**

> 注意：这两个是 AiPalace 仓外的全局真身文件，不进 AiPalace git。改完在各自位置生效即可；如需纳入 SOT，另起 ADR（spec 未要求，本版不做）。

---

### Task 7: cwd-gated 指针（经 sessionstart-domain.py 注入 ownerpowers）

**Files:**
- Modify: `~/.claude/hooks/sessionstart-domain.py`（先确认其 SOT 是否在 AiPalace/dalwin-workflow；若有 SOT 改 SOT 再派生）

**Interfaces:**
- Consumes: 公司项目 cwd 检测。
- Produces: 公司项目会话顶部 1 行 ownerpowers 指针。

- [ ] **Step 1: 定位脚本 SOT**

Run: `ls -l ~/.claude/hooks/sessionstart-domain.py`（看是否软链；是则改其指向的真身）。

- [ ] **Step 2: 加公司项目指针**

在注入逻辑里加：当 `cwd` 命中公司项目路径集（常量 `COMPANY_ROOTS = ['~/Library/IdeaProject/ZhiJin']`，可扩展）时，`[工作域]` 索引追加一行：
`ownerpowers: 本项目开发/排查任务走 ownerpowers triage(T0/T1/T2)`。

- [ ] **Step 3: 验证**

Run: 在 `~/Library/IdeaProject/ZhiJin/...` 下新开会话，确认顶部出现 ownerpowers 指针；在非公司项目（如 AiPalace）下确认**不出现**。

- [ ] **Step 4: commit**（若 SOT 在某 git 仓内则提交该仓）

```bash
git commit -am "feat(ownerpowers): sessionstart-domain 公司项目注入 ownerpowers 指针"
```

---

### Task 8: 抑制 superpowers SessionStart 121 行注入

**Files:**
- Modify: `~/.claude/plugins/cache/claude-plugins-official/superpowers/6.0.3/hooks/hooks.json`（插件自带 hook；删 SessionStart 项）

**Interfaces:**
- Produces: 去掉每会话 121 行注入（skill 仍可 ask-first 调）。

- [ ] **Step 1: 先备份**

```bash
cp ~/.claude/plugins/cache/claude-plugins-official/superpowers/6.0.3/hooks/hooks.json \
   ~/.claude/plugins/cache/claude-plugins-official/superpowers/6.0.3/hooks/hooks.json.bak
```

- [ ] **Step 2: 移除 SessionStart 注入**

把该 hooks.json 的 `hooks.SessionStart` 数组清空为 `[]`（保留文件结构，仅去掉 session-start 注入）。**保持插件 enabled**——14 个 skill 仍在册可 ask-first 调用。

- [ ] **Step 3: 验证减负生效**

Run: 新开 `claude` 会话，确认顶部**不再有** superpowers `<EXTREMELY_IMPORTANT>` 注入块；`/` 菜单里 `superpowers:*` skill **仍在**（可手动调）。

> ⚠️ 已知脆弱性（spec §15）：插件升级会覆盖此改动，需重做。记入 NEXT-STEPS 待决项；本版接受此取舍（可逆、低频）。

- [ ] **Step 4: 记录**（不进 git，是 cache 文件）

在 AiPalace `NEXT-STEPS.md` 加一条待决项："superpowers hook 抑制为 cache 手改，升级会回退，需重做或寻更稳机制。"

---

### Task 9: biz-workflow 降级（共存避撞车）

**Files:**
- Modify: `skills/mine/biz-workflow/SKILL.md`（description 收窄）

**Interfaces:**
- Produces: 验证期 ownerpowers 为主、biz-workflow 退居对照。

- [ ] **Step 1: 收窄 biz-workflow description**

在其 frontmatter description 前加："（**已被 ownerpowers 取代，验证期保留**；新任务优先走 ownerpowers，仅在显式 invoke 时使用本 skill。）" tier 保持 core 不动（仍可被显式调）。

- [ ] **Step 2: doctor + commit**

```bash
python3 tools/skillctl.py doctor
git add skills/mine/biz-workflow/SKILL.md
git commit -m "chore(biz-workflow): 验证期降级为对照，新任务优先 ownerpowers"
```

---

### Task 10: 验收（spec §14 验证清单）

**Files:** 无（手动验证）

- [ ] **Step 1: 注入与装载**

新开 ZhiJin 下会话：顶部无 superpowers 121 行注入（Task 8）、有 ownerpowers 指针（Task 7）；`superpowers:*` skill 仍可手调。

- [ ] **Step 2: triage 判档抽检**

对 3 个真实任务（T0 单文件改 / T1 ≤5 文件 bug / T2 跨模块功能）走一遍，确认档位判定符合 spec §4 硬标准、决策点门控体感正确（T0 不打断 / T1 停② / T2 停①②）。

- [ ] **Step 3: 纪律与探针触发**

确认 T2 实现触发 tdd、T2 排查触发 rca、T1/T2 完成前触发 verify；worktree 分支名符合命名规范；探查卸载 subagent 用 opus。

- [ ] **Step 4: 作用域隔离**

在非公司项目（AiPalace / 个人项目）确认 ownerpowers 不注入指针、不主动加载。

- [ ] **Step 5: 收尾**

更新 `NEXT-STEPS.md`：记 ownerpowers v1 上线 + biz-workflow 共存待观察 + superpowers hook 抑制脆弱性。最终 `python3 tools/skillctl.py doctor` 全绿。

---

## Self-Review

**1. Spec coverage（spec 各节 → 任务映射）：**
- §3 架构矩阵 → Task1(路由)+Task4(剧本)；§4 硬标准 → Task1；§5 决策点门控 → Task1；§6 三纪律 → Task2+Task4；§7 worktree/subagent → Task3+Task5；§8 融合 biz-workflow → Task4+Task5+Task9；§9 形态/作用域 → Task1(按需 skill)+Task7(指针)；§10 superpowers 处置 → Task6(override)+Task8(去注入)；§11 文件结构 → Task1-5；§12 过渡 → Task9；§14 验收 → Task10；§15 实现待定 → 已在 Task6-8 落实（路径集=ZhiJin、抑制机制=改 cache hooks.json、注入器=改 sessionstart-domain.py、effort=opos/复杂度映射记 policy）。**无遗漏。**
- §15「biz-workflow references 蒸馏 diff」→ Task5 逐文件搬+埋探针覆盖。
- §15「effort 参数映射」→ Task3 policy 记录意图，实际工具绑定在 subagent 调度时确定（Agent 工具支持 model=opus）。

**2. Placeholder scan：** disciplines/references 指向"dev-discipline §8 完整草稿 / biz-workflow 原文"是**指向已存在的完整内容**，非占位；net-new 内容（SKILL.md/policies/override/探针）均给了具体要点。无 TBD/TODO。

**3. Type consistency：** 子文件路径在 Task1（SKILL.md 引用）与 Task2-5（创建）一致（`disciplines/{tdd,rca,verify}.md`、`policies/{worktree,subagent}.md`、`workflows/{feature-dev,ops-triage}.md`、`references/step-{A..F}-*.md`）；分支命名 pattern 全程一致。

---

## 执行说明

- Task 1-5、9、10 在 AiPalace 仓内（走 doctor 绿灯 + 提交规范）。
- Task 6（全局 CLAUDE.md/AGENTS.md）、Task 7（hook 脚本，SOT 待定位）、Task 8（superpowers cache hooks.json）在 AiPalace 仓**外**，按各自位置生效，不进 AiPalace git；脆弱性记 NEXT-STEPS。
- 顺序：Task1→2→3→4→5 建 skill 本体（可连续）；Task6→7→8 接线减负；Task9 降级；Task10 验收。
