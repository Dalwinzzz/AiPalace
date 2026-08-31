# sql-expert-dba 双版本迭代设计（求同存异）

> 日期：2026-06-06
> 范围：Codex 版（`~/.agents/plugins/sql-expert-dba`，v1.1.0）与 Claude 版（`~/Library/CodeRepo/AI/claude-plugins/sql-expert-dba`，v1.1.0）
> 索引入口：`~/Documents/AI/plugins/codex-sql-expert-dba`、`~/Documents/AI/plugins/claude-sql-expert-dba`
> 前置报告：`docs/superpowers/specs/2026-06-05-sql-expert-dba-dual-version-capability-comparison.md`

---

## 1. 目标与设计哲学

### 一句话目标

把 sql-expert-dba 双版本从「各自分化」收敛为「求同存异」——核心 SQL 专家能力两版逐字一致，工具 harness 差异隔离到 `_shared/` 分片，并借此修掉双版共有的记忆机制短板。

### 规则 0（优先级最高）：差异化内容必先查官方文档

凡涉及工具 harness 差异化的内容（hook 机制、插件目录约定、路径变量 `${CLAUDE_PLUGIN_ROOT}` / `CODEX_HOME`、`plugin.json` 字段、memory/data 持久化位置、skill 加载规则等），**无论处于设计阶段还是执行阶段**，动手前必须先查阅对应工具的官方文档，以该工具 harness 的设计哲学为准，不靠记忆或想当然。

- **Claude 版差异**：查 Claude Code / Claude Agent SDK 官方文档（plugin 结构、`${CLAUDE_PLUGIN_ROOT}`、`plugins/data/` 数据约定、hooks 规范等）。
- **Codex 版差异**：查 Codex 官方文档（`.codex-plugin/` 结构、`CODEX_HOME` / `~/.codex/memories/` 约定、plugin_hooks 实验特性等）。
- **查询途径**：优先 `context7` MCP（符合全局规则）；Codex 侧若 context7 无覆盖，回退官方文档站 / 本地已安装版本实证。
- **落地要求**：每个差异分片（`.codex.md` / `.claude.md`）在实现时需标注「依据来源」，执行时验证现网行为与文档一致。

### 原则 1：动作强制、过程静默、仅产出可见（读写对称）

记忆的「读」（检索）与「写」（沉淀）两侧对称：

- **动作每轮必做**——收尾自评估、分诊前检索都是不可省略的强制动作。
- **过程与「无产出」结果一律静默**——评估过程、判定丢弃、检索未命中，都不输出任何过程性内容。
- **仅产出可见**——只有真正写入 candidate/approved，或命中 approved 且实际影响了本轮结论时，才输出一行可见结果。

### 原则 2：Skill 执行层是唯一沉淀真源

彻底移除两版的 Stop hook 机制（对「开发中部分场景才用」的低频插件，全局常驻 hook 太重）。记忆写入只发生在 workflow 收尾的强制自评估中，直接调用 `memory_capture.py`。

### 原则 3：同则一字不差、异则命名隔离

`_shared/` 主文档两版逐字一致（可 zero-diff 校验）；工具差异（脚本调用写法、路径解析）抽到 `.codex.md` / `.claude.md` 分片，两版都携带全部分片、运行时各读其一。

### memory 落点（保持现状，仅文档化）

| 版本 | 真源落点 | 状态 |
|------|---------|------|
| Codex | `~/.codex/memories/sql-expert-dba/`（复用 Codex 原生 memories 区） | 已与插件源码物理分离，重装不丢 |
| Claude | `~/.claude/plugins/data/sql-expert-dba/memory/`（Claude 官方插件 data 区） | 已与插件源码物理分离，重装不丢 |

两版均可用环境变量 `SQL_EXPERT_DBA_MEMORY_DIR` 覆盖。本次**不动 `paths.py` 解析逻辑**，仅在注释与 README 中把「真源位置 · 与源码分离 · 重装不丢」说清楚。

> 核查结论：前置对比报告中「插件重装丢 memory」的担忧，经核查两版其实都已解决——真源均在工具用户级数据区，与插件源码分离。本次迭代因此不迁移落点。

---

## 2. 文件级改动清单

> 基于对两版现状的逐文件 diff 实证。真正存在差异的只有：5 个 `SKILL.md` 中的脚本调用写法、`router` 的检索段、`memory-policy.md`、`output-contract.md`。`dialect-guidelines.md`、`missing-input-checklists.md` 及 6 个核心脚本两版已完全一致。

### A. 删除（移除 Stop hook 机制，两版对称）

| 文件 | Codex 版 | Claude 版 | 说明 |
|------|:--:|:--:|------|
| `hooks/hooks.json` | 删 | 删 | hook 配置入口 |
| `scripts/auto_memory_runner.py` | 删 | 删 | hook 消费脚本 |
| `scripts/test_auto_memory_runner.py` | 删 | 删 | 对应测试 |
| `scripts/test_plugin_hooks_manifest.py` | 删 | —（无此文件） | Codex 独有（验证 hooks 清单） |
| `plugin.json` 内 `hooks` 字段引用 | 改（移除字段） | —（本就未声明） | 见规则 0 |

> **规则 0 适用点**：删 hook 前，分别查 Claude Code / Codex 官方文档确认——删掉 `hooks.json` 后 `plugin.json` 是否有残留必填字段、是否影响插件加载。以文档为准再动手。

### B. `_shared/` 分片化（方案 A：主文档 + 指向分片）

新建分片（两版都带全部分片）：

```
skills/_shared/
  memory-policy.md           ← 改：主文档，公共内容；差异处插指向标记
  memory-policy.codex.md     ← 新建：Codex 差异（脚本裸名调用 + CODEX_HOME / ~/.codex/memories 路径）
  memory-policy.claude.md    ← 新建：Claude 差异（${CLAUDE_PLUGIN_ROOT} 全路径 + plugins/data 落点）
  output-contract.md         ← 改：主文档（记忆判定段改为「仅沉淀可见」）；脚本调用处复用 memory-policy 分片，不单独建分片
  dialect-guidelines.md      ← 不动（已完全一致）
  missing-input-checklists.md ← 不动（已完全一致）
```

指向标记格式（主文档差异处统一使用）：

```markdown
<!-- TOOL-VARIANT: memory-policy -->
> 工具相关的脚本调用与路径解析见对应分片：
> Codex → memory-policy.codex.md ｜ Claude → memory-policy.claude.md
```

分片文件内容约定（每片需标注「依据来源」，见规则 0）：

- `memory-policy.codex.md`：脚本以裸名调用（如 `memory_search.py`），路径由 `paths.py` 运行时解析；全局 memory 落点 `~/.codex/memories/sql-expert-dba/`（或 `CODEX_HOME`）。
- `memory-policy.claude.md`：脚本以 `${CLAUDE_PLUGIN_ROOT}/scripts/...` 全路径调用；全局 memory 落点 `~/.claude/plugins/data/sql-expert-dba/memory/`。

### C. 5 个 SKILL.md 修改（统一记忆措辞 + 脚本调用改引分片）

| 文件 | 改动 | 改后两版是否逐字一致 |
|------|------|:--:|
| `sql-expert-router/SKILL.md` | 检索段统一为「命中才可见」措辞；脚本调用改引分片标记 | 是 |
| `sql-query-optimizer/SKILL.md` | 记忆评估段统一为新措辞；脚本调用改引分片 | 是 |
| `sql-error-diagnostician/SKILL.md` | 同上（此文件原本已一致） | 是 |
| `sql-schema-reviewer/SKILL.md` | 同上 | 是 |
| `sql-report-query-builder/SKILL.md` | 同上 | 是 |

> 改完后 5 个 `SKILL.md` 应可通过 **zero-diff 校验**（脚本写法差异已下沉到分片）。

### D. `paths.py` 与 README（memory 落点文档化，不动逻辑）

| 文件 | Codex | Claude | 改动 |
|------|:--:|:--:|------|
| `scripts/paths.py` | 改注释 | 改注释 | 在 `resolve_user_memory_dir` 上方补注释：真源位置、与插件源码分离、重装不丢、可用 `SQL_EXPERT_DBA_MEMORY_DIR` 覆盖 |
| `README.md` | 改 | 改 | 删除 hook 启用指南章节；新增「记忆真源位置与重装不丢」「Skill 执行层为唯一沉淀真源」说明 |

### E. 测试集对齐

| 文件 | 改动 |
|------|------|
| `scripts/test_auto_memory_runner.py` | 删（两版） |
| `scripts/test_plugin_hooks_manifest.py` | 删（Codex） |
| 新增回归测试 | ①「Skill 执行层沉淀链路」：`memory_capture.py` 直写真源；② 晋升与去敏测试（见 F）。注：两版 zero-diff / 分片文件名集合一致的校验统一收口到 `check_dual_sync.py`（见第 4 段），不在此处重复 |
| `scripts/test_skill_docs_v2.py` | 改：只增加「文档内容」断言（分片指向标记存在、记忆措辞符合统一规范），不做跨版本 diff（跨版本 diff 归 `check_dual_sync.py`） |

### F. 共有短板修复

两项都做，具体方案见第 3 段：

1. candidate → approved 缺明确**复审/晋升出口流程**。
2. 去敏目前靠手动 `--forbidden-token`，**不够硬**（无默认敏感模式拦截）。

---

## 3. 记忆措辞统一规范 + 共有短板修复方案

### 3.1 「仅产出可见」统一措辞（写入侧）

各 `SKILL.md` 收尾段 + `memory-policy.md` 评估流程，统一改写为：

> **收尾记忆自评估（强制动作，静默执行）**
> 每个 workflow 完成主任务后，**必须**执行一次记忆自评估（此动作不可省略）。评估过程、以及「判定丢弃 / 不满足门槛」的结果，**一律静默，不输出任何过程性内容**。
> **仅当**评估通过 5 硬门槛、实际写入了 candidate 或 approved 时，才在交付末尾输出一行**沉淀结果**：
> `📌 已沉淀：<title>（<type>，<review_status>）→ <相对路径>`
> 未写入任何内容时，**不输出**该行，也不解释为何不沉淀。

替换关系：

- Codex 版 `output-contract.md` 第 7 段「记忆判定（必填，三选一）」→ 改为「沉淀结果（仅写入时输出）」。
- Codex 版 `memory-policy.md`「收尾评估流程（强制表态）」→ 改为「收尾评估流程（强制动作 · 静默 · 仅产出可见）」。
- Claude 版「后台评估流程」→ 同步为上述统一措辞（动作变强制，可见性仍只在有产出时）。
- 两版 `output-contract.md` 中「增强路径落盘 / last-context.json / Stop hook 兜底」相关段落一并删除。

### 3.2 「命中才可见」统一措辞（检索侧）

`sql-expert-router/SKILL.md` 的 Memory 检索段统一为：

> **分诊前记忆检索（强制动作，命中才可见）**
> 分诊前**必须**调用 `memory_search.py` 检索（此动作不可省略）。
> **仅当**命中 approved 记忆**且其实际影响本轮分诊结论**时，才显式引用（注明 memory id / title + 适用要点）。
> 命中 candidate 仅作内部参考、不作为结论，**不强制输出**。
> 未命中时**静默**，不输出「无相关记忆」。

### 3.3 共有短板修复①：candidate → approved 晋升出口

**问题**：candidate 写入后无明确「复审 → 晋升」路径，只能手动改文件，approved 池难增长。

**方案**：新建独立脚本 `scripts/memory_promote.py`（单一职责，与 capture 解耦）：

- `memory_promote.py --id <memory-id>`：把指定 candidate 经校验（字段完整 + 去敏通过）后移到 approved，更新 `index.json`。
- `memory_promote.py --list-candidates`：列出所有待复审 candidate（供人工挑选）。
- 触发时机：用户说「复审记忆」「把这条转正」等显式词 → router / 相应 skill 引导调用。
- `memory-policy.md` 增「晋升流程」小节说明出口。
- 两版同步新增（脚本本体一致；调用写法差异走 `_shared` 分片约定）。

### 3.4 共有短板修复②：去敏硬化

**问题**：去敏靠手动传 `--forbidden-token`，模型若忘传则可能漏敏。

**方案**：在 `memory_capture.py` 写入前加一道**默认敏感模式扫描**（实现为独立 `scripts/sanitize.py`，供 capture 与 promote 复用）：

- 内置默认敏感模式（正则）：手机号、邮箱、身份证号、IP 地址，以及疑似真实标识符的常见模式（具体清单在实现时确定并加测试）。
- 命中时：**硬拦截写入并报错**，提示需 `--forbidden-token` 显式脱敏或确认，而非静默放行。
- 保留 `--forbidden-token` 作为补充；新增 `--allow-token` 用于误判豁免。
- 作用域：全局 memory（`~/.codex/memories/` 与 `~/.claude/plugins/data/`）强制扫描；项目级 `./sql/biz-rules/`（允许真实表名）**不扫描**。
- 新增测试覆盖：命中拦截、`--allow-token` 豁免、`biz-rules` 不扫描三类场景。

---

## 4. 双版源码同步机制

> 对应「双版源码同步」勾选项。当前用符号链接 + 双轨文档维护，本次确立轻量同步约定。

### 同步分层

| 层 | 内容 | 同步要求 |
|----|------|---------|
| **完全共享层** | 6 个核心脚本、`dialect-guidelines.md`、`missing-input-checklists.md`、5 个 `SKILL.md`、`_shared` 主文档 | 两版 **zero-diff**（逐字一致） |
| **分片差异层** | `memory-policy.codex.md` / `memory-policy.claude.md` | 内容不同，但两版都各带全部分片（即两版的 `_shared/` 目录文件列表一致） |
| **harness 适配层** | `plugin.json` / `.codex-plugin/` vs `.claude-plugin/`、目录约定 | 各自符合官方约定（规则 0） |

### 校验脚本

新增独立脚本 `scripts/check_dual_sync.py`（专管跨版本一致性；文档内容断言归 `test_skill_docs_v2.py`，二者职责不重叠）：

- 对「完全共享层」清单逐一做两版 diff，任何非空 diff 即失败。
- 校验两版 `_shared/` 目录的文件名集合一致（都带全部分片）。
- 校验所有 `SKILL.md` 与 `_shared` 主文档中不再出现裸 `${CLAUDE_PLUGIN_ROOT}` 或裸脚本名的「未分片」差异写法。
- 实现要点：脚本需能定位两版插件根目录（默认用本仓库 `plugins/` 下的符号链接，允许参数覆盖）。

> 该校验是测试，不是 hook / 构建步骤——符合「对低频插件不引入重型自动化」的取向。

---

## 5. 验收标准

1. 两版 `hooks/` 目录、`auto_memory_runner.py` 及相关测试全部移除；`plugin.json` 无残留 hooks 引用；插件仍能被各自工具正常加载（按规则 0 查文档验证）。
2. 两版 `_shared/` 含 `memory-policy.md` + `.codex.md` + `.claude.md` 全部分片；主文档两版 zero-diff。
3. 5 个 `SKILL.md` 两版 zero-diff；记忆读写措辞符合「动作强制 / 过程静默 / 仅产出可见」「命中才可见」。
4. `memory_promote.py` 可列出 candidate 并将指定条目晋升至 approved，含测试。
5. 去敏硬化生效：全局 memory 写入命中默认敏感模式时硬拦截报错；`biz-rules` 不扫描；含测试。
6. `paths.py` 注释与两版 README 已说明「真源位置 · 重装不丢 · `SQL_EXPERT_DBA_MEMORY_DIR` 覆盖」；README 删除 hook 启用指南。
7. `check_dual_sync.py`（或等价测试）通过；两版原有测试集（去掉已删项后）全绿。

---

## 6. 不在本次范围（YAGNI）

- 不迁移 memory 落点（两版现状已满足重装不丢）。
- 不引入构建期生成 / 模板渲染（方案 C 被否决，过重）。
- 不保留任何形式的 Stop hook 兜底（包括「提醒型」hook）。
- 不重构 6 个已一致的核心脚本的内部实现（仅在其外围加 promote / sanitize）。
- 不改动 `dialect-guidelines.md`、`missing-input-checklists.md`（已一致）。
