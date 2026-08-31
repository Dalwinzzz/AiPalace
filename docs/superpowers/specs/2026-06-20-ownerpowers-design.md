# ownerpowers 设计 spec

> 设计 spec · 2026-06-20 · 状态：**待 dalwin 复审 → 通过后进 writing-plans**
> 上游输入：superpowers v6.0.3（obra, MIT）+ [dev-discipline 蒸馏 spec](file:///Users/dalwin/Documents/AI/dalwin-workflow/docs/superpowers/specs/2026-06-19-superpowers-distillation-design.md)（2026-06-19）+ 现役 `biz-workflow`
> 一句话：把 biz-workflow 编排 + superpowers 的三纪律/worktree/subagent 蒸馏融合成一个**公司项目专用、复杂度分档、轻负重**的统一工作流引擎。

---

## 1. 背景与目标

superpowers 能力强但「笨重」：每会话注入 121 行 `using-superpowers`、14 个 skill 描述常驻施压、且「1% 相关就必须用」的铁律给日常简单任务加了大量不必要的流程仪式。对 Claude Opus 4.8 这样的模型能力，多数日常任务不需要这么重的硬约束。

**目标**：自建 `ownerpowers` —— 把任务复杂度交由模型按**硬标准**自判，再按复杂度走**不同量级**的工作约束流程；融合并增强现有 `biz-workflow`；蒸馏吸收 superpowers 的三纪律（TDD/RCA/verify）与 worktree/subagent 能力，按自己的调性收编；只在公司项目生效，平时零负重。

---

## 2. 设计决策日志（本次 brainstorm 拍板）

| # | 决策 | 选定 | 备选（已否） | 理由 |
|---|------|------|------------|------|
| D1 | 档位模型 | **3 档 T0/T1/T2** | 2 档 / 4 档 | 梯度清晰且不过度，覆盖绝大多数场景 |
| D2 | triage 方式 | **升档阶梯，默认 T0** | 每任务显式分类 | 简单任务零 triage 仪式，只在踩红线时升档 |
| D3 | 决策点门控 | **T0 不停 / T1 停② / T2 停①②** | ②全档必停 / 全放开 | 减负落点：简单任务不被打断，复杂任务仍受控 |
| D4 | biz-workflow 关系 | **融合并增强**（非 invoke 调用） | 仅 invoke / 不动 | 逐步取代；验证期保留并存 |
| D5 | 形态/加载 | **混合：cwd-gated 微指针 + 按需 skill 体** | 纯按需 skill / 完整插件+hook | triage 可靠在场 + 几乎零常驻负重 |
| D6 | superpowers 处置 | **留 skill（ask-first 兜底）、去 SessionStart 注入、override 中和铁律** | 完全禁用 / 保现状+加规则 | 既减负又留兜底 |
| D7 | worktree/subagent | **蒸馏为本插件 policy + 探针自动触发** | 完全不搬 / 直接调 superpowers | 按自己调性收编，接进工作动线 |
| D8 | SOT 落点 | **AiPalace `skills/mine/ownerpowers/`** | dalwin-workflow | AiPalace 是声明 SOT，biz-workflow 也在此 |
| D9 | 作用域 | **仅公司项目（cwd 命中）** | 全局 | 不污染个人/通用任务，符合全局瘦身 |

---

## 3. 架构总览：`triage → 线 × 档 → 剧本`

triage 产出两个**正交维度**，交叉决定跑多重流程：

- **线（lane）**：需求开发线 / 运维排查线 / 杂活直做（继承 biz-workflow 分诊）
- **档（tier）**：T0 / T1 / T2（复杂度，升档阶梯）

| | **T0 直做** | **T1 轻纪律** | **T2 全纪律** |
|---|---|---|---|
| **需求开发线** | 直接改 + self-check | feature-dev 精简（跳设计、verify 必走）+ 停② | spec-architect 设计 → TDD → verify + 停①② |
| **运维排查线** | 一眼修 + verify | RCA 按需 → 修 → verify + 停② | RCA 强制 → 根因定调① → 修 → 回归测试 → verify + 停② |
| **杂活直做** | 直做 | — | — |

---

## 4. triage 硬标准（升档阶梯，默认 T0）

判档逻辑：**默认落 T0，命中任一上档触发条件即升到该档**。triage 本身不构成仪式——平时就是直做。

| 档 | 命中任一即进此档 | 强制约束 |
|---|---|---|
| **T0 直做**（默认） | 查询/读代码、单文件局部改、文档·配置编辑、一眼可见的笔误级修复 | 无，直接动手 |
| **T1 轻纪律** | • 改动 **≤5 文件** / 多函数协作<br>• 修一个非显而易见的 bug<br>• 改业务逻辑·查询·接口实现（有副作用但可逆）<br>• 写一个新的小功能单元 | **verify 必走**；是 bug 则**按需 RCA** |
| **T2 全纪律** | • 跨模块 / 改公共 API·接口契约 / DB schema 变更·迁移<br>• 不可逆或高风险（删数据、动核心配置、上线相关）<br>• 需先设计的多步新功能 / 重构<br>• 同一 bug 已修 ≥2 次仍不好（从 T1 升上来）<br>• 我显式要求走完整流程 | **spec-architect 设计 → TDD → RCA → verify** 全链 |

**两条横切规则：**
- **就地升档**：按初判档位开工，中途发现「简单任务」变复杂（牵连文件超预期 / bug 复发）→ 立即升档，不硬撑。
- **降级兜底**：任何档若模型判断需要 superpowers 的某个重 skill → **先问我再调**（superpowers ask-first 接入点）。

---

## 5. 决策点门控（继承 biz-workflow 决策点 + 档位化增强）

biz-workflow 原本「决策点①方案/根因定调、②落库/提交前」是任何剧本必停。融合后改为**档位门控**：

| 档 | 决策点① 方案/根因定调 | 决策点② 提交前 |
|---|---|---|
| T0 | 不停 | 不停（直做，靠护栏兜底） |
| T1 | 不停 | **停**（摊改动文件 + diff + 提交计划） |
| T2 | **停**（摊"怎么改/根因是什么"） | **停** |

**🚧 不可逆操作护栏（全档通用，不随档放松）**：删数据 / 改生产配置 / 执行非只读 SQL / push 到远端 —— **无论哪档哪步，一律额外停下显式确认**。

**决策点①归属动态绑定**（继承 biz-workflow）：T2 若委托了 spec-architect，其 Confirm 门即视为①，不重复问。

---

## 6. 三纪律（蒸自 dev-discipline spec §8，落 `disciplines/`）

| 纪律 | 文件 | 铁律 | 档位触发 |
|------|------|------|---------|
| **TDD** | `disciplines/tdd.md` | 没有先失败的测试就不写生产代码（RED→GREEN→REFACTOR）；含 Java/JUnit·Go/testing 落点 | **T2 强制**；T1 新功能单元建议 |
| **RCA** | `disciplines/rca.md` | 没做根因调查不准提修复方案（4 阶段）；≥3 次修不好→质疑架构 | **T2 排查强制**；T1 bug 按需 |
| **verify** | `disciplines/verify.md` | 没在本轮新鲜跑过验证命令，不能说「通过/完成/修好」；证据先于宣称 | **T1/T2 必走** |

> 三纪律全文细则按 dev-discipline spec §8.1–8.4 的草稿落地（已含 syzh Maven 命令、Java/Go 栈落点、反模式表）。

---

## 7. 能力配置层（`policies/`，蒸自 superpowers worktree/subagent）

按自己调性收编 `using-git-worktrees` / `dispatching-parallel-agents` / `subagent-driven-development`，并在 `references/` 步骤里埋探针自动触发。

### 7.1 `policies/worktree.md`

- **自动触发**（探针埋在 feature-dev 起步 / triage 出档）：**T2 需求开发线**（需隔离的复杂/多步功能），或**并行处理多个互不依赖任务**时 → 自动起 worktree；T0/T1 当前工作区直做。
- **分支命名硬规范**：`<工具>/<类型-taskName>/<日期_版本号>`（类型与 taskName 用连字符 `-`——冒号 `:` 被 git ref 规则拒绝，实测 `git check-ref-format` 报 invalid，故用 `-`）
  - 工具 ∈ `claude` / `codex`；类型 ∈ `feature` / `fix` / `refactor`；末段 `日期_版本号`
  - 示例：`claude/feature-体检预约改版/20260620_v1.2.1`、`codex/fix-大屏数据对不上/20260620_v1.0.0`、`codex/refactor-审核流重构/20260620_v2.0.0`
  - 生成不符此 pattern 的分支名 = 错。
- worktree 创建可逆 → **自动执行无需停**，但状态播报告知"已在 worktree `<path>` 起分支 `<name>`"。
- ⚠️ 注意：自动的只是「起 worktree」这个动作壳；worktree 内的**代码改动本身仍走档位门控的决策点①②**。

### 7.2 `policies/subagent.md`

**触发条件（满足任一即可派 subagent）：**
1. **并行 fan-out**：2+ 互不依赖子任务（独立模块/文件组、无共享状态、无顺序依赖）→ 并行多 subagent。
2. **探查卸载（核心准则 · 保护主上下文）**：任务需**大量探查/检索/通读、但只需要一个结论性结果** → 派单个 subagent 去探，主 session 只接回结论，避免探查过程把主上下文快速占满。
3. **状态文件协同**：互相依赖/有顺序的子任务，**若能用共享状态文件维护过程状态** → 也可开 subagent 协同（主 agent ↔ subagent 经状态文件来回），按需**先建好共同状态文件**再派。
   - 仅当紧耦合、需高频实时来回、不宜走状态文件中转时 → 主 session 串行直做。

**subagent 配置：**
- **模型一律 `opus`**。
- **`effort` 按任务复杂程度指定**：简单探查 → 低 effort；复杂分析/实现 → 高 effort。（实现时绑定到实际 subagent 调度工具的对应参数。）

**调度纪律：**
- 每个 subagent 任务边界清晰、产出**可独立验证或落到状态文件**。
- 主控汇总后**走 verify 纪律核对实际产出（看 diff / 读状态文件，不轻信"成功"自述）**。

**档位适用：**
- **探查卸载(2) 任何档都可用**（为省 context，T0/T1 探查重时照样派）。
- **并行 fan-out(1) + 状态协同(3) 一般 T2**。

---

## 8. 融合 biz-workflow（吸收 + 增强）

**吸收（原样继承）**：2 线分诊、委托表（SQL→`sql-expert-dba` / 设计→`spec-architect` / 契约→Apifox MCP）、不可逆护栏、状态播报、references 步骤库（step-A…F）。

**增强**：
1. 决策点：从「任何剧本必停」→ **档位门控**（§5）。
2. 织入三纪律（§6）到剧本对应步骤。
3. 前置 triage 分档层（§3–4）。
4. references 步骤里埋 worktree/subagent 探针（§7）。

---

## 9. 形态、加载与作用域（混合形态）

- **微指针**：在**公司项目 cwd** 下，复用现有 `sessionstart-domain` 注入器多注入 **1 行指针**——"本项目开发/排查任务走 ownerpowers triage"。不新起 hook、不搬 superpowers 的 121 行注入。
- **按需体**：完整 triage/剧本/纪律/policy = **按需 skill**（description 触发，继承 biz-workflow 已验证的触发方式）。常驻负重 ≈ 1 行。
- **作用域**：仅公司项目（`cwd ∈ ~/Library/IdeaProject/ZhiJin/**` 等，**具体路径集 plan 阶段确认补全**）。非公司/个人项目零侵入。

---

## 10. superpowers 处置

- 插件**保留**：14 个 skill 仍可被 **ask-first 调用作兜底**（任何档需要时先问用户再调）。
- **干掉其 SessionStart 121 行注入**（实现细节：禁用其 session-start hook 或等效抑制，**留给 plan 阶段勘察确定机制**——需查 settings.json 能否单独抑制插件 hook）。
- ownerpowers 的 CLAUDE.md override **中和「1%→MUST」铁律**（用户指令优先级高于 superpowers skill，是其自身 Instruction Priority 允许的）。

---

## 11. 文件结构

```
skills/mine/ownerpowers/
├── SKILL.md              # triage 分诊 + 线×档路由 + 决策点门控 + 横切规则（核心，~100 行）
├── workflows/
│   ├── feature-dev.md    # 需求开发线剧本（tier-aware，蒸自 biz-workflow + 增强）
│   └── ops-triage.md     # 运维排查线剧本（tier-aware）
├── disciplines/
│   ├── tdd.md            # 蒸自 dev-discipline §8.2
│   ├── rca.md            # 蒸自 dev-discipline §8.3
│   └── verify.md         # 蒸自 dev-discipline §8.4
├── policies/
│   ├── worktree.md       # 触发条件 + 分支命名硬规范
│   └── subagent.md       # 3 触发条件 + opus/effort + 状态文件协同
└── references/           # step-A…F（继承 biz-workflow，补埋 worktree/subagent 探针）
    ├── step-A-api-contract.md
    ├── step-B-code-locate.md
    ├── step-C-build-test.md
    ├── step-D-sql-delegate.md
    ├── step-E-commit.md
    └── step-F-triage-report.md
```

- `registry.yaml` 登记 `mine/ownerpowers {source: mine, category: workflow, tier: core}`。
- 双工具：core tier，sync 派生到 `~/.claude/skills` + `~/.codex/skills`（继承 biz-workflow 现状）。

---

## 12. 过渡与迁移（biz-workflow 共存 → 下线）

- ownerpowers 设为**主**；biz-workflow **保留作对照**，但 description **收窄/降优先**，避免两者在同一任务撞车。
- 验证清单跑稳后，再 PR 下线 biz-workflow（降 parked 或删，届时另决，写 ADR）。
- **验证清单（acceptance）**：
  1. 公司项目新会话顶部**不再有** superpowers 的 121 行 `<EXTREMELY_IMPORTANT>` 注入；装载列表 −14 superpowers、+1 ownerpowers。
  2. triage 判档**准确**：随机抽 T0/T1/T2 各若干真实任务，档位判定符合 §4 硬标准。
  3. 决策点门控**体感正确**：T0 不被打断、T1 停②、T2 停①②；不可逆护栏全档生效。
  4. 三纪律**按档触发**：T2 实现走 TDD、T2 排查走 RCA、T1/T2 完成前走 verify。
  5. worktree/subagent 探针**按 policy 自动触发**，分支名符合命名规范。
  6. 个人/非公司项目**零侵入**（不加载 ownerpowers、不注入指针）。

---

## 13. YAGNI / out of scope

- **不搬** superpowers 的 `finishing-branch`、`writing-skills`（git-merge-conductor + 提交规范 hook + skill-creator 已覆盖收尾/造 skill）。
- **不做** 4 档；**不写进**全局 `~/.claude/CLAUDE.md`（作用域隔离，靠 cwd-gate）。
- worktree/subagent **不直接调 superpowers 版本**，而是收编为本插件 policy（§7）。

---

## 14. 回滚

- ownerpowers 是独立新增 skill：删软链即下线，不影响其它。
- superpowers 注入抑制可一行配置切回；其插件实体始终保留。
- biz-workflow 全程保留至验证通过，随时可切回为主。

---

## 15. 待 plan 阶段补全的实现细节（非设计悬空，是实现待定）

1. 公司项目 cwd 路径集的**完整枚举**（当前已知 `~/Library/IdeaProject/ZhiJin/**`）。
2. **抑制 superpowers SessionStart hook 的确切机制**（settings.json 能否单独禁插件 hook，还是只能禁整插件）。
3. `sessionstart-domain` 注入器**接入 ownerpowers 指针的改法**。
4. subagent `effort` 参数到实际调度工具的**映射**。
5. biz-workflow references 蒸馏进 ownerpowers 时的**逐文件 diff**（哪些原样搬、哪些改写）。
