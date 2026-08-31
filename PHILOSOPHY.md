# AiPalace 设计哲学总纲

> **元原则：总纲稳定、细则可演进；冲突以本总纲为准。**

本总纲定义 AiPalace 的九条设计原则（P1–P9）。任何规范、ADR、实现细节在与本文冲突时，均以本文为准。细则（`docs/governance/` 下各文档）可随演进修订，本总纲只在有充分理由时才整体修订并留 ADR 记录。

---

## P1 · 单一真源（SOT）

一仓即个人 harness 全貌，`git clone` 即得。选装/备份/自建三态由目录结构**显式表达**，不藏在软链拓扑里。

**如何体现：** 所有内容资产（skills/rules/context/memory）统一存放于本仓库；工具侧挂载点（`~/.claude/`、`~/.codex/`）为派生产物，不作为内容修改入口。

---

## P2 · 声明式管理，工具派生（限内容资产）

声明源是唯一手改的事实源，派生物由工具生成，**手不碰派生物**。skill 全部进 registry，由 `skillctl` 统一软链（symlink）派生到两工具、`/` 菜单可见；context/memory 经各自 INDEX 声明、rules 经 path-scoped 声明。无手动特例。

**如何体现：** 只改 `registry.yaml` → `sync --dry` → `sync` → `doctor`；禁止直接编辑挂载点下的受管软链或拷贝。

---

## P3 · 来源优先的归属分层（判别方式按资产分化）

顶层按"谁创建"分、靠证据不靠猜（git 作者 + 上游交叉比对）、无法溯源留 `_SOURCE.md` 不编造。skill 按创建者分层；memory 按内容域分层。

**如何体现：** `skills/` 三级结构 `<class>/<source>/<skill>/`，class ∈ {mine, enterprise, community}（封闭）；community 附 `_SOURCE.md`，enterprise 附可见性边界标注；memory 按五域（projects/tech/workflow/reference/enterprise）组织。

---

## P4 · 分级控预算（tier）

`core`/`extra`/`parked` 控 token 与 `/` 菜单；尊重 agent"启动只加载 name+description"机制与 `SLASH_COMMAND_TOOL_CHAR_BUDGET` 天花板。

**如何体现：** `core`/`extra` 进挂载，`parked` 仅备份不挂载；registry 条目必须声明 tier；超出预算前先降 tier 再新增。

---

## P5 · 实证选型，不照搬

关键决策基于实测/issue 证据（symlink 可见性即由实测推翻照搬结论，见 ADR-0005），不赌 open bug、不盲抄。

**如何体现：** 任何影响挂载机制或工具行为的选型，须附实测结论或 issue 引用后再写入 ADR；口述"应该可以"不作为落地依据。

---

## P6 · 零破坏演进

动核心配置先勘察再出方案；变更默认纯增量；`.aipalace-managed` 受管标记隔离，工具只回收自己写的、对用户手建物保护跳过、零误删。

**如何体现：** `skillctl --fix` 默认 dry-run，加 `--confirm` 才落盘；工具绝不给无标记软链补标记（禁止擅自收编）；孤儿 skill 只 warning 不自动登记。

---

## P7 · 内容统一源、机制分治

**内容资产**（skills/rules/context/memory）工具无关，统一源、一次派生同步两工具；**机制**（各工具 hooks 注入器、native 机制协同、plugins）与产品形态耦合，分而治之。内容与机制正交两分。

**如何体现：** `content-assets/` 规范覆盖全部四类内容；`product-assets/` 规范覆盖 injection/plugins；内容规范不含工具名硬编码，机制规范不含内容格式规定。

---

## P8 · 决策留痕，诚实标注

每次演进写 ADR（背景/决策/后果/取舍）；未定项与过渡态显式标注，不假装完备。

**如何体现：** `adr/` append-only，被推翻的决策不删改、由新 ADR 标注 supersede（ADR-0005 推翻 ADR-0002 为活案例）；文档中"待决"/"过渡"状态必须用 `> ⚠️` 或 `[TODO]` 显式注明。

---

## P9 · 显式过渡态

已知的不一致写成"必须收敛的待决项"管理，而非默默接受漂移。

**如何体现：** 每个 governance 文档维护"过渡态/待决项"小节；`evolution.md` 汇总全局待决项清单；`/ai-palace` 沉淀时主动识别新的不一致并纳入管理。

---

## 统领说明

本总纲统领 `docs/governance/` 各细则。细则文档解读规范的具体规则与执行路径；本文定义原则优先级与裁判权。

> 参考：设计决策完整依据见 [`docs/superpowers/specs/2026-06-18-aipalace治理与设计哲学-design.md`](docs/superpowers/specs/2026-06-18-aipalace治理与设计哲学-design.md)
