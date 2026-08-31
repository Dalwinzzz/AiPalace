# AiPalace — Claude Code 项目指令

> **本仓库是 dalwin 个人 AI harness 的唯一 SOT。任何维护与迭代必须遵循设计哲学与治理规范。**

---

## 最高准绳

九条原则精要如下；**完整总纲在 `PHILOSOPHY.md`，要改结构 / 推翻决策 / 判定原则冲突时再读全文**
（ADR-0020：原为 `@PHILOSOPHY.md` 全文 include，与本表重复且每会话常驻 2.4KB，改为指针）。

| # | 原则 | 核心约束 |
|---|------|---------|
| P1 | 单一真源（SOT） | 本仓库是唯一内容源；`~/.claude/`、`~/.codex/` 是派生挂载点，不得作为修改入口 |
| P2 | 声明式管理，工具派生 | 只改 `registry.yaml`，由 `skillctl` symlink 派生；**禁止手碰派生物** |
| P3 | 来源优先归属分层 | `skills/<class>/<source>/<skill>/`，class ∈ {mine, enterprise, community}（封闭）；无法溯源留 `_SOURCE.md` |
| P4 | 分级控预算（tier） | core/extra 进挂载，parked 仅备份；超出预算先降 tier 再新增 |
| P5 | 实证选型，不照搬 | 影响挂载机制的选型须附实测结论或 issue 引用后再写 ADR |
| P6 | 零破坏演进 | **动核心配置先勘察再出方案**；`skillctl --fix` 默认 dry-run，`--confirm` 才落盘 |
| P7 | 内容统一源、机制分治 | content-assets 工具无关；product-assets 与工具形态耦合，分而治之 |
| P8 | 决策留痕，诚实标注 | ADR append-only；被推翻的决策不删改，由新 ADR supersede |
| P9 | 显式过渡态 | 已知不一致写成"待决项"管理，不默默接受漂移 |

---

## 资产维护规范

改任何资产前，**先读对应 governance 规范**（`docs/governance/README.md` 索引）：

### skills（最常操作）

```
1. 只改 registry.yaml（声明源）
2. python tools/skillctl.py sync --dry   # 验证变更
3. python tools/skillctl.py sync         # 执行派生
4. python tools/skillctl.py doctor       # 校验状态
```

> **doctor 现为全绿**（2026-06-19 起）：溯源 `_SOURCE.md`（community）与可见性标注（enterprise）已补齐，`doctor` 24 skill 全绿、无漂移。**绿灯是基线**——`sync` 依赖 doctor 绿灯，提交 skill 变更前须保持全绿；**再报红即为真实漂移**，需排查修复而非忽略。

规范文档：`docs/governance/content-assets/skills.md`，工具：`tools/skillctl.py`。

### memory / context / rules

- **self/memory（已迁）**：`vault/memory/` 是当前 SOT（`00-RULES/` 自我画像、`01-PROJECTS/` 五域项目知识）。SessionStart hook 按序注入 `00-RULES/operating-rules.md`(共享操作规则)与 `vault/memory/INDEX.md`(always-on 决策树)。维护指引见 `docs/governance/content-assets/memory.md`。
- **context/rules**：仍在 `context/rules/` 原处（path-scoped 自动注入域规则，未迁移）。维护指引见 `docs/governance/content-assets/{context,rules}.md`。

### 插件（plugins）

见 `docs/governance/product-assets/plugins.md`，注意插件↔skill 边界判断。

### 注入机制（hooks / SessionStart）

见 `docs/governance/product-assets/injection.md`，SessionStart hook 双工具同逻辑。

---

## 演进纪律

**任何推翻既有决策、改结构、改哲学**，必须写 ADR：

- 目录：`adr/`，文件名 `NNNN-<slug>.md`，append-only
- 被推翻的决策**不删改**，由新 ADR 用 `Supersedes: ADR-XXXX` 标注（活案例：ADR-0005 推翻 ADR-0002）
- 演进 SOP 见 `docs/governance/evolution.md`

---

## 关键禁忌

- **禁止手碰派生物**（`~/.claude/skills/`、`~/.codex/skills/` 下的受管软链）
- **禁止直接编辑挂载点**下任何受管文件
- **动核心配置前必须先勘察**（P6），输出方案后再执行
- **孤儿 skill 只 warning，不自动登记**；`skillctl --fix --confirm` 才清悬挂软链

---

## commit-msg 约定

钩子强制格式：`<type>(<scope>): <subject>`

---

## 导航

- **设计哲学总纲**：`PHILOSOPHY.md`（P1–P9，最高准绳）
- **规范索引**：`docs/governance/README.md`
- **决策记录**：`adr/`
