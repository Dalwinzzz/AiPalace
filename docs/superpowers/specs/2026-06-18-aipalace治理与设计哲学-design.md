# AiPalace 治理与设计哲学 — 设计 spec

- 日期：2026-06-18
- 状态：设计定稿，待落地（writing-plans → 实施；SOT 指向切换另由 final-spec 承接）
- 作者：dalwin（与 Claude 协作打磨）
- 关联：[ADR-0001](../../../adr/0001-AiPalace为个人AI-harness唯一SOT.md) … [ADR-0005](../../../adr/0005-实测修正symlink可见性并回归symlink派生.md)

---

## 1. 背景与目的

AiPalace 的设计哲学此前是**隐性、散落、带"本轮"权宜性、无强制力**的——原则埋在 ADR、`registry.yaml` 注释、README 里。本 spec 把它**升格**为显式、稳定、可执行、有约束力的治理体系。

四个并重的目的：

| 目的 | 含义 |
|------|------|
| **演进护栏** | 给后续重构提供稳定原则护栏，防走样、防决策反复 |
| **纳入准绳** | 任何新资产纳入有明确可依据的合格标准与落位规则，长期一致不腐化 |
| **可分享方法论** | 沉淀成体系化、对外可读可复用的"个人本地 AI harness 方法论" |
| **个人秩序追溯** | 结构清晰、可 git 追溯，未来的自己（及双工具）能看懂为什么这么设计 |

**地基动作——剥离"永久哲学" vs "一次性范围"**：ADR 里"本轮只做 X 不做 Y"是临时约束，不是稳定原则。本 spec 后：永久原则上升为 `PHILOSOPHY.md`（极少改），某次决策的范围/取舍留在各自 ADR。

**最终目标——SOT 指向切换（不在本 spec）**：把双工具（Claude Code / Codex）的 hook、path-scoped rules 软链、`/wrap` 落盘目标，从 `~/Documents/AI/dalwin-workflow` 改指向 `AiPalace`、`dalwin-workflow` 退役。**这是整个工程的最终一步，但不属于本 spec**——它需待 context / rules / memory / skill 全部按规范**迭代完成**后，由独立的 **final-spec** 承接执行。本 spec 只负责前置的**规范打磨与结构落地**：先立规范护栏，再逐步迭代内容，最后才切。

---

## 2. 体系组织（分层规范集）

```
AiPalace/
├─ PHILOSOPHY.md            ← 设计哲学总纲（最高准绳，极少改）
├─ docs/governance/         ← 治理规范区（新增）
│  ├─ README.md             ← 索引：三层关系(哲学→规范→流程) + 资产分类总览
│  ├─ content-assets/       ← 内容资产规范（统一源）
│  │  ├─ skills.md
│  │  ├─ rules.md
│  │  ├─ context.md
│  │  └─ memory.md
│  ├─ product-assets/       ← 机制规范（分治）
│  │  ├─ injection.md       ← 注入机制：hooks / path-scoped / native 协同
│  │  └─ plugins.md
│  ├─ creations.md          ← 创作性产物（横切，单列）
│  └─ evolution.md          ← 演进流程（横切，单列）
└─ adr/                     ← 决策事件流（append-only，只记某次具体决策）
```

冲突时以 `PHILOSOPHY.md` 为准。元原则：**总纲稳定、细则可演进。**

---

## 3. 设计哲学总纲（`PHILOSOPHY.md`，P1–P9）

- **P1 · 单一真源（SOT）** — 一仓即个人 harness 全貌，`git clone` 即得。选装/备份/自建三态由目录结构**显式表达**，不藏在软链拓扑里。
- **P2 · 声明式管理，工具派生（限内容资产）** — 声明源是唯一手改的事实源，派生物由工具生成，**手不碰派生物**。skill 全部进 registry，由 `skillctl` 统一软链(symlink)派生到两工具、`/` 菜单可见；context/memory 经各自 INDEX 声明、rules 经 path-scoped 声明。无手动特例。
- **P3 · 来源优先的归属分层（判别方式按资产分化）** — 顶层按"谁创建"分、靠证据不靠猜（git 作者 + 上游交叉比对）、无法溯源留 `_SOURCE.md` 不编造。skill 按创建者分层；memory 按内容域分层（见 §8）。
- **P4 · 分级控预算（tier）** — `core`/`extra`/`parked` 控 token 与 `/` 菜单；尊重 agent"启动只加载 name+description"机制与 `SLASH_COMMAND_TOOL_CHAR_BUDGET` 天花板。
- **P5 · 实证选型，不照搬** — 关键决策基于实测/issue 证据（symlink 可见性即由实测推翻照搬结论，见 ADR-0005），不赌 open bug、不盲抄。
- **P6 · 零破坏演进** — 动核心配置先勘察再出方案；变更默认纯增量；`.aipalace-managed` 受管标记隔离，工具只回收自己写的、对用户手建物保护跳过、零误删。
- **P7 · 内容统一源、机制分治** — **内容资产**(skills/rules/context/memory)工具无关，统一源、一次派生同步两工具；**机制**(各工具 hooks 注入器、native 机制协同、plugins)与产品形态耦合，分而治之。内容与机制正交两分。
- **P8 · 决策留痕，诚实标注** — 每次演进写 ADR(背景/决策/后果/取舍)；未定项与过渡态显式标注，不假装完备。
- **P9 · 显式过渡态** — 已知的不一致写成"必须收敛的待决项"管理，而非默默接受漂移。

---

## 4. 资产规范区骨架

内容/机制用**子目录**在结构层显式表达：`content-assets/`（统一源）vs `product-assets/`（机制分治）。`creations.md`、`evolution.md` 横切单列。

---

## 5. `content-assets/skills.md`

能力资产。三级结构 + `registry.yaml` 单一源 + tier 控 token + sync/doctor 防腐化。内/中/外圈概念**不进本规范**（仅迁移映射 tier 用）。

**5.1 三级物理结构**：`skills/<class>/<source>/<skill>/`，class ∈ {mine, enterprise, community}（封闭）；source 开放。

**5.2 registry 单一源**：每 skill 登记 `{source, category, tier}`。

**5.3 分类体系**：`category` 封闭集合 = `workflow / method / sql / stack / docs / design / diagram / media / meta`（9 类）。扩类走"先改规范、再加 skill"。

**5.4 tier 与挂载**：`core`/`extra` 进挂载、`parked` 仅备份；双 mount = `~/.claude/skills` + `~/.codex/skills`。

**5.5 派生形态**：**symlink**（ADR-0005，软链回仓库真身，`/` 菜单可见、即时生效、零额外磁盘）；`.aipalace-managed` 受管标记 + prune 零误删。区分两层：仓库内 community/enterprise 硬拷贝是**备份快照**（不变），sync **派生挂载**是 symlink。

**5.6 纳入合格标准（硬门槛，doctor 不绿不予 sync）**：

| # | 硬门槛 |
|---|--------|
| 1 | 有 `SKILL.md` 且 `name`+`description` 非空（触发语质量为正文最佳实践建议，非硬门槛） |
| 2 | 落在三级路径 `skills/<class>/<source>/<skill>/` |
| 3 | registry 登记 `{source, category, tier}` 三字段齐全 |
| 4 | `category` ∈ 封闭集合 |
| 5a | community 附 `_SOURCE.md`（license/credit/upstream，无法溯源标"待补"不编造） |
| 5b | enterprise 附标注（公司/项目/**可见性边界** + license） |

> license 不单列门槛，作为 5a/5b 标注文件的**必填字段**。

**5.7 doctor 校验项**：

| 校验 | 覆盖 | 行为 |
|------|------|------|
| registry 条目的三级真身存在且含 SKILL.md(name/desc 非空) | 门槛 1/2 | 缺失→报错 |
| registry 三字段齐全、category 在封闭集 | 门槛 3/4 | 违规→报错 |
| community 有 `_SOURCE.md` / enterprise 有标注 | 门槛 5 | 缺失→报错 |
| 两挂载点无同名冲突 | 挂载安全 | 冲突→报错 |
| 受管软链悬挂检测（`.aipalace-managed` 软链指向真身仍在） | symlink 健康 | 悬挂→报错 |
| **孤儿检测**：`skills/` 有真身但 registry 未登记 | 防漏登记 | **warning** |

**5.8 `doctor --fix` 安全边界（守 P6）**：仅自动修受管域内对象（清带标记的悬挂软链、对 registry 已声明且指向真身但缺标记的补标记）；**绝不**给无标记软链补标记（=擅自收编）、绝不删非受管对象、孤儿不自动登记（仅 warning）。`--fix` 默认 dry-run，加确认才落盘。

**5.9 工作流**：只改 `registry.yaml` → `sync --dry` → `sync` → `doctor`。

---

## 6. 内容资产四分与 INDEX 同构

skills 之外，内容资产还有 **rules / context / memory** 三类，按**注入哲学**区分：

| 类 | 本质 | 注入 | INDEX |
|----|------|------|-------|
| **rules** | 硬配置（路径/条件匹配后**必须**注入） | 硬触发 path-scoped | 无（硬匹配即 when） |
| **context** | 个人沉淀的**可选**上下文，关于"我" | 软·模型自选时机 | `context/INDEX.md`（when→what） |
| **memory** | 事实/历史**知识**沉淀，关于"事" | 渐进 pull | `memory/INDEX.md`（when→what） |

边界：**context 是"我"的画像（稳定、自选轻注），memory 是"事"的知识库（增长、按需深取）。** context 与 memory **同构**——各自一个 INDEX 决策树约束 `when`、指向各自目录下的内容 md（`what`）。

### 6a. `rules.md`

硬配置域规约（如 java-spring、frontend-web）：路径/条件匹配后**必须注入整篇**。**内容统一源**（域规约工具无关）、**注入机制分治**（见 §7）。无需 INDEX——path-scoped 匹配本身就是它的触发条件。

### 6b. `context.md`

可选上下文，模型自选注入。context = 关于"我"的画像：身份、技术栈偏好、工作方式、环境偏好——偏稳定，几乎任何任务都可能瞄一眼。

- **`context/INDEX.md`**：决策树，约束 `when` 去看 `context/` 下哪个 `what` md。always-on 注入（轻）。
- **`context/<what>.md`**：按维度拆分（如 identity / tech-stack / workflow-style / env-preference），模型按 INDEX 的 when 条件自选加载。
- 注入：INDEX always-on，模型据当前任务**自选**展开 what（不强制，软注入）。

### 6c. `memory.md`

知识沉淀，按需 pull。memory = 关于"事"的知识库，随沉淀增长。

**三级化（域 → 主题 → 条目）**：

```
memory/
├─ projects/   个人项目          └─ career/go-transition.md
├─ enterprise/ 公司项目·二级=公司  └─ zhijin/syzh.md
├─ tech/       技术深度·二级=技术域 go/ · java/
├─ workflow/   工作流            ai-workflow.md
└─ reference/  参考              glossary.md
```

- **`memory/INDEX.md`**：同构决策树，约束 when 去 pull 哪个条目；命中 `enterprise` 不全量注入，细到 `enterprise/zhijin/syzh` 才取。
- **L1 域封闭** = `projects / tech / workflow / reference / enterprise`（5，扩域走"先改规范"）；**L2/L3 开放**（公司名/技术域/项目类别/条目随沉淀增长）。
- **浅填原则**：三级是为精细化注入预留的框架，不强制填满，随沉淀向下展开。
- **触发 = 三门并集（OR，最大化召回）**：门 a（cwd 打分，复用 `compute_confidence()`）∪ 门 b（模型读全树语义判断）∪ 门 c（任务描述 × 索引目录主动匹配）。
- **注入粒度**：MVP = always 注入整棵 INDEX；hook 按 cwd 裁剪子树注入**记入演进项**（树大了再启用）。
- **沉淀来源**：`/wrap` 主动沉淀 + **从双工具 native memory 沉淀中凝练提取**（见 §7 native 协同）。

> context/INDEX 与 memory/INDEX 均 always-on，落地时可合并为**一个注入块**省一次开销（实现细节，见 §7）。

---

## 7. `product-assets/`（机制分治）

**7.1 `injection.md`（注入机制）**：
- 原则：内容统一源，**注入机制按工具分治**。
- **SessionStart hook**（Claude `~/.claude/hooks` + Codex `~/.codex/hooks`，**同逻辑**）：注入 `context/INDEX` + `memory/INDEX`。
- **path-scoped 硬触发**（服务 rules）：Claude `~/.claude/rules/<域>.md`（`paths:` glob，软链统一源）；Codex 目录树 AGENTS.md（dir-scoped）。
- **native memory 协同（不弃用）**：**尊重两工具自身 harness 的原生 memory 机制，本仓库只做增强、不替代**；且本仓库 `memory/` 的沉淀**可从双工具 native memory 沉淀中再凝练提取**（native 是仓库 memory 的上游提炼源之一）。
- 非内容类 hooks（commit 规范等自动化）：各工具 hooks 目录分治维护并登记。

**7.2 `plugins.md`**：承接 `plugins/README.md` 双版本布局（claude/codex marketplace + sql-expert-dba）；插件↔skill 边界（何时做插件、何时做 skill）；memory 真源落点。

---

## 8. `evolution.md`（演进流程）

- **skill 工作流**：只改 registry → sync --dry → sync → doctor。
- **ADR append-only & supersede**：ADR 是不可变决策事件流，被推翻的决策**不删改**，由新 ADR 标注 supersede（ADR-0005 推翻 ADR-0002 即活案例）。
- **上游同步**：`upstream_sync.py`（codex 定时任务）把上游 clone 硬拷贝进 `community/` 做**备份快照**——属"仓库内 SOT 存储层"，与 sync 派生挂载层无关，保留硬拷贝。
- **SOT 指向切换**：把双工具 hook / rules 软链 / `/wrap` 落盘目标改指向 AiPalace；dalwin-workflow 退役为 git 历史。

---

## 9. 待落盘改动清单（实施待办，交 writing-plans 拆解）

1. **新建** `PHILOSOPHY.md`（P1–P9）。
2. **新建** `docs/governance/` 全套（README + content-assets/{skills,rules,context,memory} + product-assets/{injection,plugins} + creations + evolution）。
3. **skillctl**：`sync` 从 copytree 改回 symlink（保留双 mount + `.aipalace-managed` prune 保护 + 三级前缀）；doctor 加孤儿检测、悬挂检测换下漂移检测；新增 `--fix`（安全边界）。
4. **registry.yaml / README.md**：删除/修正"为规避 symlink bug 改硬拷贝"表述，改为 symlink。
5. **context/memory 落地**：
   - context 拆分：身份/技术栈/工作方式/环境偏好等 `context/<what>.md` + `context/INDEX.md`。
   - memory 重组为三级 5 域（`enterprise/zhijin/syzh.md`、`projects/career/go-transition.md` 等）+ `memory/INDEX.md`。
   - rules 正名：`java-spring` / `frontend-web` 归 rules（硬配置）。
   - 双工具 SessionStart hook 注入两个 INDEX；Claude rules-glob / Codex 目录-AGENTS.md 硬触发。
6. **迁移期一次性**：内/中/外圈 ↔ tier 映射（只在迁移用，不进规范）。
> **范围边界——SOT 指向切换不在本清单。** 它是整个工程的**最终一步**，需待 context / rules / memory / skill 全部按规范**迭代完成**后，由独立的 **final-spec** 执行（届时才改 hook / rules 软链 / `/wrap` 落盘目标指向 AiPalace、dalwin-workflow 退役）。本 spec 落盘止于上面 1–6。

---

## 10. 实施顺序

**本 spec 范围**：规范成文（§9.1–§9.4）→ context/memory/rules 落地（§9.5）→ 迁移映射（§9.6）。

**之后（独立推进，不在本 spec）**：context / rules / memory / skill 内容持续迭代 → 全部完成后，由 **final-spec** 执行 SOT 指向切换。

规范是护栏：**先立规范 → 再迭代内容 → 最后才切。**
