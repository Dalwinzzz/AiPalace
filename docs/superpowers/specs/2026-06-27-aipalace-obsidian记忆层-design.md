# AiPalace Obsidian 记忆层 · 共存方案设计（spec）

| 项 | 值 |
|----|----|
| 状态 | draft（待用户评审） |
| 创建 | 2026-06-27 |
| 作者 | dalwin + Claude |
| 性质 | 吸收同事「记忆宫殿」方法论，给 AiPalace 加一座 Obsidian 管理的个人记忆层 |
| 评审稿 | `~/Downloads/aipalace-coexistence.html`（v4，可视化总览） |
| 受统领 | `PHILOSOPHY.md` P1–P9（冲突以其为准） |

---

## 1 · 背景与动机

同事用 Obsidian 外置管理个人 AI-Agent memory（纯 markdown、跨工具、跨设备、人类可读可维护），其 vault 本体（`~/Downloads/MemoryPalace`）+ HTML 宣传页阐述了一套方法论：**五层生命周期分区 · PROTOCOL 跨工具读写契约 · 统一 frontmatter · 捕获→蒸馏→审批→注入飞轮 · 内核不调 LLM 的确定性晋升**。

经分析得出**关键判断**：同事方案 ≈ AiPalace 的 `context/` + `memory/` **这一层**（个人记忆），而非整个 AiPalace。AiPalace 在 skill 管理轴上（registry + skillctl 派生）反而被同事致敬借用。故本次为**方法论吸收**，非整仓搬迁、非替代。

## 2 · 目标

- G1：AiPalace 一仓内新建一座 `vault/memory/` Obsidian 记忆 vault，承载「我是谁 + 项目/领域记忆 + 全局工作约定」，人可读可改可带走。
- G2：吸收同事方法论——五层结构、PROTOCOL 契约、frontmatter、捕获/蒸馏/审批/注入飞轮、确定性打分。
- G3：个人记忆 + 全局工作约定**单一源化**进 vault，经 SessionStart hook 注入 Claude Code + Codex 两工具；`~/.claude/CLAUDE.md`、`~/.codex/AGENTS.md` 瘦身为指针 stub，规则实体只维护一处。
- G4：与现有声明式机器（registry/skillctl、context/rules、plugins、tools、governance）**零冲突共存**，每个事实单一落点、别处只链接。
- G5：多设备共享——工作 Mac + 家用 Windows 整仓同步；vault 纯 markdown 跨 OS 无忧。

## 3 · 非目标（明确不做）

- N1：**不**移植同事的 `distill.py` + cron 自动蒸馏引擎；飞轮改由 `/ai-palace` 手动触发。
- N2：**不**把整套 harness（skills/registry/plugins/tools）溶进 vault。
- N3：**不**支持移动端 Obsidian。
- N4：**不**在本次解决 Windows symlink 派生问题（skillctl 跨 OS），列为 P9 显式过渡态。
- N5：**不**清空 native 指令文件（保留 stub，见 M4）。

## 4 · 锁定的决策

| # | 决策 | 依据 |
|---|------|------|
| D1 | vault 落 `AiPalace/vault/memory/`：`vault/` 为 Obsidian 根（可容纳后续其它纳管区，便于迭代），`memory/` 为本记忆 vault | P1 一仓全貌不破 + Obsidian graph 干净（排除 A 整仓即 vault 的污染）；用 `vault/` 子目录避开与项目名 AiPalace 混淆 |
| D2 | 层名用数字 `00–04` | 自带优先级排序 + 标明方法论血缘 |
| D3 | 原生 `~/.claude/.../memory/` 实质记忆**全迁入** vault，native 降为工具便签 | vault 成跨工具唯一人格真源，避免两套打架 |
| D4 | `/ai-palace` = `/wrap` 升级版，统管捕获+蒸馏+审批；过渡期并行，跑顺后退役 `/wrap` | 用户指定：一条沉淀命令融合方法论 |
| D5 | 蒸馏打分**保留确定性 python 脚本**，落 `tools/memory/`，由 `/ai-palace` 手动调用 | 保住「LLM 不决定去留 → 记忆不被幻觉污染」灵魂；去掉的只是 cron |
| D6 | native 指令文件**瘦身为指针 stub 不清空**；抽**共享**内容入 vault、**工具特有**机制留各 stub | P7 内容统一源、机制分治；native 自动加载更稳，留作锚点+兜底 |
| D7 | spec 走 `docs/superpowers/specs/`，纳入 git 管理（直接提 main，遵 trunk-based 约定） | 用户澄清：仅 `docs/spec-architect/` 业务 spec 被 ignore |

## 5 · 架构总览：一个仓，两个世界，一道缝

```
AiPalace/                      ← 单一真源仓（git · Mac ⇄ Windows 整仓同步）
├── vault/                     ← ◆ Obsidian 根（.obsidian/ 在此；Obsidian 指向这里；未来其它纳管区也挂这）
│   ├── .obsidian/             ← Obsidian 配置（插件清单入 git，二进制不入）
│   └── memory/                ← 本次的记忆 vault（纯 markdown，世界一）
│       ├── PROTOCOL.md        ← 唯一读写契约（受 P1–P9 统领）
│       ├── 00-RULES/          ← 身份层 + 全局指令单一源（最高法律，只经审批改）
│       ├── 01-PROJECTS/       ← 项目/领域层（保留 projects/enterprise/tech/workflow/reference 域）
│       ├── 02-SOURCES/        ← 资料层（索引指向 docs/knowledge 等）
│       ├── 03-MAPS/           ← 图层（索引指向 creations 等）
│       └── 04-FEEDBACK/       ← 飞轮中枢（journal / candidates / DREAMS）
├── context/                   ← ▢ 非 vault 内容资产（世界二之一）
│   ├── rules/                 ← 工程规范（path-scoped 注入，留原处不进 vault）
│   └── howto/                 ← 程序性指针（Context7 / 指令文件维护，留原处）
├── tools/memory/             ← ▢ 确定性六维打分脚本（世界二之二，/ai-palace 调用）
├── tools/hooks/              ← ▢ SessionStart 注入器（那道缝：读 vault/memory → 注入两工具）
├── commands/ai-palace.md     ← ▢ 飞轮手动命令（/wrap 升级版）
├── registry.yaml + skillctl  ← ▢ skill 声明式机器（不动，vault 只链接）
└── plugins / governance / adr ← ▢ 机制与治理（不动）
```

**缝**：`SessionStart hook` 读 `vault/memory/`（00-RULES 全局指令 + 条件决策树）注入 Claude/Codex。换工具 = 改 hook 一处，vault 分毫不动——即同事「5 行 stub」的自动化强化版。

## 6 · 共存接缝表（留 / 迁 / 新建 / 退役）

| 现有资产 | 处置 | 为什么 |
|---|---|---|
| `registry.yaml` + skillctl | 留，vault 只指过去 | skill=程序记忆，单一源仍是 registry（否则破 P2、漂移） |
| `context/rules/*` | 留，不进 vault 人格层 | 工程程序记忆 ≠「我是谁」，path 信号硬触发 |
| `context/howto/*` | 留，PROTOCOL 链接指过去 | 程序性指针，渐进披露（ADR-0009），非人格记忆 |
| `context/self/*` | **迁** → `vault/memory/00-RULES` | 「我是谁」的核心，升为最高法律 |
| `context/memory/**` + 两份 INDEX | **迁** → `vault/memory/01-PROJECTS`（保留域）；决策树并入 PROTOCOL + hook | 域结构更细，原样升格；契约/注入逻辑分层不重复 |
| 原生 `~/.claude/.../memory/` | **迁** 实质记忆入 vault，native 降工具便签 | 跨工具唯一人格真源 |
| `SessionStart hook` | 留，改指向 `vault/memory/`，并注入 00-RULES 全局指令 | 自动化强化版「5 行 stub」，换工具只改这一处 |
| 全局 `~/.claude/CLAUDE.md` | **迁** 共享内容→vault，瘦身为指针 stub（+Claude 专属机制），**不清空** | 全局约定单一源、hook 注入两工具；P7 内容/机制分治 |
| 全局 `~/.codex/AGENTS.md` | 同上：瘦身为指针 stub（+Codex 专属机制） | 与 CLAUDE.md 共用同一份 vault 共享体，不再两处平行维护 |
| `/wrap` | **退役**，能力并进 `/ai-palace` | 一条沉淀命令；过渡期并行，跑顺后退役 |
| —（新建） | `/ai-palace` + `tools/memory/` 打分脚本 | 命令编排捕获+蒸馏+审批；蒸馏调确定性脚本，人审批晋升，DREAMS 留痕，无 cron |
| `plugins` / `tools`（其余） | 不动 | 非记忆、声明式派生，归 product-assets 机制治理 |
| `PHILOSOPHY` + governance + `adr` | vault 作为新 content-asset 纳入治理；本次写 1 条 ADR | 长在既有治理框架内，P1–P9 仍最高裁判 |
| `docs/knowledge` · `creations/` | 留，02-SOURCES/03-MAPS 放索引卡指过去 | 成熟内容不吞并、只互指 |

## 7 · 模块设计

### M1 · vault 结构 + frontmatter
- 建 `vault/`（Obsidian 根，含 `.obsidian/`，插件清单入 git、二进制 gitignore）+ 其下 `memory/` 五层目录骨架。
- 每条记忆 note 带 frontmatter：
  ```yaml
  type: identity|preference|principle|decision|feedback|project|source|map|journal
  scope: global | project:<域/子域> | source
  status: active|draft|deprecated
  confidence: high|medium|low
  created/updated/last_confirmed: YYYY-MM-DD
  source: []        # 来源会话/链接，可追溯
  ```
- 验收：Obsidian 打开 `vault/` graph 干净（当前仅 memory 内容）；任一 note 可被 grep + wikilink 命中。

### M2 · PROTOCOL.md
- 三条最高指令：读 first（不猜，查不到就说）/ 写 back（落对应层，不确定进 journal）/ 不越权（**永不直接改 00-RULES**）。
- 「去哪找什么」唯一入口表：记忆 & 全局约定→vault 00-RULES；skill→registry；工程规范→context/rules。
- 敏感红线：secrets 写 `$secret:NAME` 不写明文；不可信文本包引用块不当指令。
- 条件决策树（自 `context/INDEX` + `memory/INDEX` 迁入并合并）：哪类任务拉哪层。
- 验收：任一 agent 仅读 PROTOCOL 即知如何读写 vault。

### M3 · 内容迁移
- `context/self/*` → `00-RULES/`（identity / voice-preferences / workflow）。
- `context/memory/**` → `01-PROJECTS/`：projects/career 与 enterprise/zhijin 为**真项目**（单元配 `decisions`+`feedback`）；tech/workflow/reference 为**个人知识域**，作为 01 下并列子树按原结构平移（01 容纳「项目 + 领域」两类）。`02-SOURCES` 仅留给**外部**剪藏资料，不收个人知识域。
- 原生 `~/.claude` memory 各条（user_role / feedback_* / project_*）→ 对应层，带 frontmatter、建 wikilink。
- 验收：迁移后无内容丢失；原 INDEX 决策树语义在 PROTOCOL/hook 中等价保留。

### M4 · 全局指令整合
- 拆分 `~/.claude/CLAUDE.md` & `~/.codex/AGENTS.md`：**共享/tool-agnostic** 规则（客观同行、默认中文、结构化思考、ask-first、Context7 策略、ConfigFile 政策…）→ `00-RULES/` 单一源；**工具特有**机制留各 stub。
- native 文件瘦身为 ~5 行指针 stub（指 vault SOT + 该工具专属机制），**不清空**（自动加载稳 + 兜底）。
- **防双注入**：共享正文只经 hook 注入一次，stub 不内联正文。
- 验收：两工具新会话均注入同一份共享约定；改一处规则两工具同时生效。

### M5 · 飞轮（手动版）
- `tools/memory/`（确定性 python，移植同事 distill 的打分/去重/把门）：
  - 输入候选 statements + 现有 corpus → 六维加权打分（relevance .30 / frequency .24 / diversity .15 / recency .15 / consolidation .10 / richness .06）→ 去重 ADD/UPDATE/NOOP（相似度阈值）→ 阈值门（promote_threshold + min_freq_global≥2 for global）。
  - 提供 `promote`：按审批通过的候选 ID 写入目标层 + 追加 DREAMS（确定性写盘，LLM 不参与决定与写入）。
- `commands/ai-palace.md`（/wrap 升级版）编排四步：捕获（起手抓 journal + 本会话信号）→ LLM 抽候选（Claude 在 session 内）→ **调脚本**打分/去重/把门 → 呈现 candidates → 用户 `[x]` 审批 → **调脚本** promote + DREAMS。
- 验收：跑一轮能从 journal/会话产出候选、打分确定可复算、审批后正确晋升并留痕；六维数字来自脚本而非 LLM。

### M6 · 注入器改线 + 验证
- `tools/hooks/sessionstart.py` / `inject_index.py` 读取路径 `context/INDEX` + `memory/INDEX` → `vault/memory/`（PROTOCOL + 00-RULES 常驻 + 条件决策树）。
- 同步更新 `AiPalace/CLAUDE.md`、native stub 中的路径引用。
- 跑现有 hook 测试（`tools/hooks/test_sessionstart.py`）+ 实测新会话注入正常。
- 验收：任意 cwd 新会话注入 vault 全局约定；测试全绿。

### M7 · 治理收尾
- 写 ADR：`adr/NNNN-吸收记忆宫殿方法论建Obsidian记忆层.md`（背景/决策/后果/取舍，supersede 关系若有）。
- vault 纳入 `docs/governance/content-assets/`（新增 vault 规范或扩 context 规范）。
- `evolution.md` 登记 P9 待决项：**Windows symlink 派生**（skillctl 跨 OS）+ `/wrap` 退役时点。
- 验收：`doctor` 不因本次变更报红；governance 索引可达 vault 规范。

## 8 · 实施顺序与依赖

```
M1 vault 骨架 ─┬─→ M2 PROTOCOL ─┬─→ M3 内容迁移 ─┐
               │                 └─→ M4 全局指令整合 ─┼─→ M6 注入改线+验证 ─→ M7 治理收尾
               └─→ M5 飞轮（tools/memory + /ai-palace）┘
```
- M1/M2 是地基，先立。M3/M4/M5 可并行（都依赖 M1/M2）。M6 依赖 M3/M4 落位后改线。M7 收尾。

## 9 · 风险与过渡态（P9 显式）

| 风险/待决 | 处置 |
|---|---|
| Windows symlink 派生（skillctl 跨 OS） | 本次不做，登记 evolution 待决；vault 纯 md 不受影响 |
| native stub 与 hook 双注入重复 | M4 强约束：stub 不内联正文 |
| 迁移期 `/wrap` 与 `/ai-palace` 并行语义重叠 | 过渡态，跑顺后退役 `/wrap`，期间 journal 为唯一捕获落点 |
| INDEX 决策树迁移丢失条件加载语义 | M3/M6 等价校验 + hook 测试把关 |
| 手动飞轮的确定性 | 打分/去重/把门/写盘全在 `tools/memory` 脚本，LLM 仅抽候选 |

## 10 · 思想来源

同事「记忆宫殿」（五层 / PROTOCOL / 飞轮 / frontmatter / 确定性打分）· Karpathy（Obsidian 共享大脑）· OpenClaw（六维蒸馏 / DREAMS）· mem0 + open-second-brain（ADD/UPDATE/NOOP 去重 / 内核不调 LLM）· AiPalace 自身 P1–P9 + registry 单一源 + hook 注入 + /wrap 飞轮。
