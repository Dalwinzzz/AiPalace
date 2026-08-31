# Codex 版 sql-expert-dba 插件 memory 自动沉淀修复设计

> 日期：2026-06-04 ｜ 范围：**仅 codex 版**插件源码（`/Users/dalwin/Documents/AI/plugins/sql-expert-dba`）
> 不涉及：Claude 版插件、Claude 侧 parse/socket 问题、`docs/problem/` 截图、全局 `~/.codex/config.toml`、用户级 `~/.codex/hooks.json`

## 一、问题与根因

### 现象

codex 安装处插件（`~/.codex/plugins/cache/local-plugins/sql-expert-dba/<version>/memory/`）的 memory 目录里，除 3 条 seed（glossary-001 / rule-001 / template-001）外，**没有任何运行时新增的知识沉淀**。插件声称的"守护式自动沉淀"从未生效。

### 根因（三层叠加，基于 OpenAI 官方文档 + codex 0.136.0 二进制实证）

| # | 根因 | 证据 |
|---|------|------|
| 1 | **插件清单从未声明 hooks** | `plugin.json` 只有 `skills` + `interface`，无 `hooks` 字段，也无约定式 `hooks/hooks.json`。官方文档（[Build plugins](https://developers.openai.com/codex/plugins/build)）明确：插件靠 `plugin.json` 的 `hooks` 字段或默认 `./hooks/hooks.json` 挂载生命周期 hook。→ `auto_memory_runner.py` 没有任何运行时入口去调用。|
| 2 | **`plugin_hooks` 实验特性未开启** | PR [#19705](https://github.com/openai/codex/pull/19705)（2026-04-28 合并）才让 codex "发现并加载插件捆绑 hooks"，需 `plugin_hooks` feature flag。codex 0.136.0 二进制确认该 flag 存在；但 `~/.codex/config.toml` 的 `[features]` 只有 `codex_hooks/hooks/memories/js_repl`，无 `plugin_hooks`。|
| 3 | **插件 hook 默认不受信任** | 官方明确：安装/启用插件不会自动信任其 hook，codex 跳过未 review+trust 的插件 hook。|

**一句话根因**：memory 自动沉淀依赖 codex hook 触发，但"声明 hook / 开 `plugin_hooks` / 信任 hook"三道闸门一道都没打通。

### 关键澄清：缓存目录 vs 真源目录

用户最初查看的"安装处 memory"是**插件缓存目录**，会随重装/升级被覆盖。插件源码的 `paths.py` 实际已设计了**用户级全局目录**作为运行时真源。因此"安装处 memory 没新增"的正确修复结果，不是让缓存目录多文件，而是让沉淀正确落到用户级全局目录，并在缓存目录留可见指针。

## 二、设计原则

1. **接线为主，不重写脚本**：核心 Python（`memory_capture.py` / `auto_memory_runner.py` / `paths.py`）已完整且健壮（去重 / 去敏 / 状态机 / 自动建目录 / 索引维护），本次不改其逻辑。修复以配置接线 + 契约强化为主。
2. **显式为主、hook 为辅**：核心沉淀走 skill 显式调用脚本，不依赖实验特性，100% 可沉淀；bundled hooks 作可选增强，开 `plugin_hooks` 才生效，关着不影响主路径。
3. **诚实边界**：不替用户改全局配置；增强路径标注"依赖实验特性、默认可能不生效"，附启用指南。

## 三、架构

### 双路径 + 可见指针

```
主路径（永远可用，不依赖实验特性）— 本次修复重点
  触发1：用户"记下来/值得沉淀/帮我复盘"  ── 硬触发
  触发2：workflow 收尾必填 [记忆判定] 段  ── 强制表态
         （丢弃 / 写candidate / 写approved 三选一，缺此段=任务未完成）
            └─ skill 显式调用 memory_capture.py
                 └─ ~/.codex/memories/sql-expert-dba/（真源，持久）✓

增强路径（开 plugin_hooks 才生效，关着不影响主路径）
  hooks/hooks.json (Stop事件)
    └─ auto_memory_runner.py ──> memory_capture.py（仅写 candidate，后台无感）

可见性（解决"从缓存目录看不到沉淀"）
  <plugin>/memory/WHERE-IS-MY-MEMORY.md（指针）
    └─> "运行时沉淀在 ~/.codex/memories/sql-expert-dba/"
```

### 三路径汇聚同一真源

三条路径最终都调同一个 `memory_capture.py`，落到同一真源 `~/.codex/memories/sql-expert-dba/`——去敏 / 去重 / 状态机 / 索引由脚本统一保证，不因路径不同而行为不一致。

## 四、修复点清单

| # | 修复点 | 文件 | 改动性质 |
|---|--------|------|---------|
| 1 | 补 bundled hooks 声明 | `.codex-plugin/plugin.json`（加 `hooks` 字段）+ 新建 `hooks/hooks.json` | 新增配置 |
| 2 | 修正虚假描述 | `.codex-plugin/plugin.json` 的 `description` / `longDescription` | 改文案 |
| 3 | 契约强化：可选段 → 必填段 | `skills/_shared/output-contract.md` | 改约定 |
| 4 | 主路径触发强化 | `skills/_shared/memory-policy.md` | 改约定（仅触发措辞，不改路径结构表述）|
| 5 | 读取闭环强化 | `skills/sql-expert-router/SKILL.md` | 改约定 |
| 6 | 缓存目录可见指针 | 新建 `memory/WHERE-IS-MY-MEMORY.md` | 新增文件 |
| 7 | 接线测试 | 新建 `scripts/test_plugin_hooks_manifest.py`；扩展 `scripts/test_auto_memory_runner.py` | 新增/扩展测试 |

**核心脚本（`memory_capture.py` / `paths.py` 等）本次不改逻辑。**

## 五、详细设计

### 5.1 增强路径：`hooks/hooks.json`（新建）

依据官方默认文件约定 + 官方确认的环境变量（`PLUGIN_ROOT` = 插件根；`PLUGIN_DATA` = 插件可写数据目录）：

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 ${PLUGIN_ROOT}/scripts/auto_memory_runner.py --input ${PLUGIN_DATA}/last-context.json",
            "timeout": 10,
            "statusMessage": "SQL Expert DBA: 评估记忆候选"
          }
        ]
      }
    ]
  }
}
```

`plugin.json` 同步加 `"hooks": "./hooks/hooks.json"`（显式声明；即使有默认文件约定，显式声明使意图清晰，并与官方"manifest 优先"行为一致）。

### 5.2 增强路径的两段式（解决"hook 拿不到结构化候选"的语义鸿沟）

codex 的 Stop hook 经 stdin 传的是 codex 自己的事件 payload（session_id/cwd/...），**不含**插件需要的 `global_candidate`（title/type/problem_pattern/conclusion）。这些结构化候选只有 AI 在对话中才能产出。因此增强路径采用"AI 落盘 + hook 读取"两段式：

```
对话中（AI 侧）：
  workflow 收尾时，AI 把本轮结构化候选写入
  ${PLUGIN_DATA}/last-context.json（由 memory-policy 指示）
            ▼
Stop 时（hook 侧）：
  auto_memory_runner.py 读该 JSON
    ├─ 有候选且过门槛 → 调 memory_capture.py 写 candidate
    └─ 无候选/不达标 → 静默 skip（脚本已有 insufficient_context / missing_global_candidate 分支）
```

hook 不需"理解对话"，只做"把 AI 已准备好的候选落库"这一确定动作。

`auto_memory_runner.py` 现有签名 `--input <JSON>` + `--memory-dir` 已满足此设计，**无需改脚本逻辑**；`--memory-dir` 缺省时回退 `resolve_user_memory_dir()`，正确落到用户级全局目录。

### 5.3 主路径：`output-contract.md` 可选段 → 必填段（关键改动）

当前第 88–90 行的"沉淀结果"是 v2 可选段、"未触发时默认省略"——这个"可选"正是 AI 能合法跳过的漏洞。

**改动**：在六段式之后增设固定必填段 `7. 记忆判定`（所有 workflow 收尾强制输出）：

```markdown
### 7. 记忆判定（必填，三选一，缺此段视为任务未完成）

按 memory-policy 5 硬门槛评估本轮是否产出可复用知识，必须明确表态其一：

- **丢弃** — 不满足沉淀门槛。一句话说明原因（如"一次性查询，无可复用结论"）。
- **写 candidate** — 有价值待复审。说明已调用 memory_capture.py
  （--capture-mode auto_background）、去敏处理、写入路径与 review_status。
- **写 approved** — 高置信高通用，经校验。说明 promotion-reason、写入路径与 review_status。
```

**硬约束新增一条**：`workflow 收尾必须输出"记忆判定"段；省略该段等于交付不完整。`

效果：AI 无法静默跳过——必须显式说"判定为丢弃，因为……"或"已写 candidate，路径在……"。

> **实现明确**：本次**只新增**"7. 记忆判定"必填段，**不改动**现有 6 段结构，也**不删除/不改写**现有"沉淀结果"v2 可选段（第 88–90 行）。两者关系：必填的"记忆判定"段负责强制表态（丢弃/candidate/approved 三选一）；旧"沉淀结果"可选段在"写入"分支下作为可复用的展开细节模板，与新段不冲突、不重复要求。实现者无需合并或改写旧段。

### 5.4 主路径：`memory-policy.md` 触发强化

- **触发1（显式关键词，硬触发）**：保留现有"记下来/值得沉淀/帮我复盘/保存这个经验"，强化措辞为"用户说出这些词时，执行显式沉淀流程是强制动作，不是可选项"；显式模式优先尝试 approved（过校验），否则 candidate。
- **触发2（收尾评估，强制）**：把现有"默认在后台执行一次记忆评估"对齐到 5.3 必填段——评估结果必须通过"记忆判定"段可见呈现。
- **增强路径落盘指示（新增）**：workflow 收尾时，若判定为"写 candidate/approved"，同时把结构化候选写入 `${PLUGIN_DATA}/last-context.json`（供增强路径 hook 在 Stop 时落库；主路径已直接写库，此落盘仅为增强路径冗余兜底）。

**不改**：memory-policy 里的路径结构表述、v1/v2 目录结构描述（留待用户另开 session 的文档对齐任务）。

### 5.5 读取闭环：`router SKILL.md` 强化

router 已有"分诊前调用 memory_search.py 检索"。强化为："分诊前必须先 search；命中的 approved 记忆要在分诊结果里显式引用"——形成"沉淀 → 下次检索命中 → 复用"闭环，让 memory 价值可见。

### 5.6 可见指针：`memory/WHERE-IS-MY-MEMORY.md`（新建）

```markdown
# 运行时沉淀在哪里？

本目录（插件缓存目录）只存 seed memory（glossary-001 / rule-001 /
template-001），随插件版本分发，重装/升级会被覆盖。

运行时新沉淀的 SQL 知识不在这里，而在用户级全局目录：

    默认：~/.codex/memories/sql-expert-dba/
    可被覆盖：$SQL_EXPERT_DBA_MEMORY_DIR
          或 $CODEX_HOME/memories/sql-expert-dba/

结构（v2）：
    approved/{rules,cases,templates,glossary}/   ← approved 条目
    candidates/{rules,cases,templates,glossary}/ ← candidate 条目
    index.json          ← 检索索引
    capture-log.jsonl   ← 沉淀日志

查看最近沉淀：
    ls -lt ~/.codex/memories/sql-expert-dba/candidates/*/
```

### 5.7 路径落点（代码已就绪，仅供参照，不改代码）

`paths.py::resolve_user_memory_dir` 实际解析顺序：
1. `SQL_EXPERT_DBA_MEMORY_DIR`（显式）→ 直接用
2. `CODEX_HOME` → `$CODEX_HOME/memories/sql-expert-dba`
3. 兜底 → `~/.codex/memories/sql-expert-dba`

`ensure_global_memory_dirs` 自动建 v2 两层结构（`approved/{...}`、`candidates/{...}`）+ `index.json` + `capture-log.jsonl`。

## 六、测试策略

| 层 | 测试内容 | 方式 |
|---|---------|------|
| 配置合法性 | `plugin.json` valid JSON 且 `hooks` 字段合法；`hooks/hooks.json` valid JSON 且 Stop 事件结构正确、command 含 `${PLUGIN_ROOT}` | 新建 `test_plugin_hooks_manifest.py` |
| 两段式落盘 | `auto_memory_runner.py` 读 `last-context.json`：有合法候选→调 capture；无候选/不达标→skip | 扩展现有 `test_auto_memory_runner.py` |
| 主路径回归 | `memory_capture.py` 去敏/去重/状态机/index 不被破坏 | 现有 `test_memory_v2.py` / `test_memory.py` 全绿 |
| 路径解析 | `paths.py` 解析到 `~/.codex/memories/sql-expert-dba/` | 现有 `test_paths.py` 全绿 |

**原则**：不为没改的代码写新测试；只为新增接线（manifest + hook 两段式）写新测试。

## 七、验收标准（可执行、可证伪）

1. **配置正确**：`plugin.json` 含合法 `hooks` 字段；`hooks/hooks.json` 按官方格式声明 Stop hook。（`python3 -m json.tool` 校验 + 新测试通过）
2. **主路径可证**：在临时 `SQL_EXPERT_DBA_MEMORY_DIR` 下，按显式沉淀流程调 `memory_capture.py`，正确生成 `candidates/rules/xxx.md`（或 approved）+ 更新 `index.json`。（命令行实证）
3. **契约强化生效**：`output-contract.md` 含必填"记忆判定"段 + 对应硬约束；`memory-policy.md` 触发措辞已强化。（diff 可见）
4. **可见指针就位**：`memory/WHERE-IS-MY-MEMORY.md` 存在且指向正确真源路径。
5. **现有测试不回归**：`scripts/` 下所有 `test_*.py` 全绿。
6. **诚实边界**：增强路径在 spec/README 标注"依赖 plugin_hooks 实验特性，默认可能不生效"，附启用指南；未代改全局 config.toml。

### 无法在本次验证的边界（诚实声明）

"自动后台沉淀真的在日常 codex 里自动触发"无法在本次完全验证——它依赖用户开 `plugin_hooks` + trust hook（用户选择只出指南不代开）。验收聚焦"主路径 100% 可证 + 增强路径配置正确且按官方格式接通"，自动触发留给用户按指南启用后实测。

## 八、风险与对策

| 风险 | 等级 | 对策 |
|---|------|------|
| 两段式"AI 落盘候选"仍依赖 AI 自觉写 last-context.json | 中 | 主路径（必填记忆判定段）不依赖落盘文件，独立可靠；增强路径落盘是 best-effort 叠加，失败不影响主路径 |
| `~/.codex/memories/sql-expert-dba/` 与 codex 原生 memories git 仓库交互 | 低 | 用独立子目录隔离，不碰 `~/.codex/memories/` 根下 MEMORY.md/raw_memories.md；该子目录为插件私有 |
| 改 output-contract 影响所有 workflow 输出 | 低 | 新增段而非改现有 6 段；现有结构不变 |

> 注：`${PLUGIN_ROOT}` / `${PLUGIN_DATA}` 语义已经 OpenAI 官方文档核实（PLUGIN_ROOT=插件根；PLUGIN_DATA=插件可写数据目录），原"变量名不确切"风险已消除。

## 九、不做什么（YAGNI + 用户边界）

- ❌ 不重写任何核心 `*.py` 逻辑
- ❌ 不动 Claude 版插件、parse/socket 问题、`docs/problem/` 截图
- ❌ 不代改全局 `~/.codex/config.toml`、不动用户级 `~/.codex/hooks.json`
- ❌ 不做文档结构对齐（README.md 结构描述、memory-policy 路径结构表述）—— 用户另开 session 处理
- ❌ 不动 seed 物理位置

## 十、启用指南（写入插件 README，供用户可选启用增强路径）

```
增强路径（自动后台沉淀）默认不生效，依赖 codex 实验特性。如需启用：

1. 开启 plugin_hooks：在 codex 的 /experimental 中开启 "plugin_hooks"，
   或在 ~/.codex/config.toml 的 [features] 加 plugin_hooks = true，重启 codex。
2. 信任本插件 hook：首次触发时 codex 会提示 review，确认信任本插件的
   hooks/hooks.json。
3. 验证：执行一次 SQL 任务并结束会话，检查
   ~/.codex/memories/sql-expert-dba/candidates/ 是否新增条目。

不启用也不影响主路径——用户说"记下来"或 workflow 收尾必填记忆判定段，
沉淀照常进行。
```
