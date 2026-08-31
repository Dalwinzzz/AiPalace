# Final-Spec：本地 AI harness SOT 指向切换（dalwin-workflow → AiPalace）

- 日期：2026-06-25
- 状态：方案定稿，**待新会话分阶段执行**
- 作者：dalwin（与 Claude 协作勘察设计）
- 关联：收敛 [ADR-0001](../../../adr/0001-AiPalace为个人AI-harness唯一SOT.md) 标注的"两 SOT 并存"过渡态；前置工作 P1–P4 + 治理 spec 已全部合并 main
- 风险级别：**最高（动现役核心配置、难逆转）**。守 PHILOSOPHY **P6 零破坏演进**：每阶段独立、强备份、可验证、可回滚。

> ⚠️ **本 spec 是给执行者（新会话 agent）的自包含操作手册。** 执行前必读全文；逐阶段做，每阶段验证通过再进下一阶段；任一阶段异常立即按"回滚"还原。**不要一次性全切。**

---

## 1. 背景与目标

P1–P4 已把内容资产（skills/rules/context/memory）、治理规范、skillctl 工具全部建在 AiPalace 并合并 main。但**现役** `~/.claude`、`~/.codex`、`~/.agents` 仍指向旧 SOT **dalwin-workflow**（及 `awesome-skills` 等旧 clone）。本次把所有现役链路切到 AiPalace，dalwin-workflow 退役为 git 历史。

**目标终态**：双工具（Claude Code / Codex）的 skill 挂载、rules/context 注入、SessionStart hook、`/wrap` 落盘、plugins 全部源自 AiPalace；`grep -r dalwin-workflow` 在现役配置中零命中。

---

## 2. 现役全貌（2026-06-25 勘察）——七块切换对象

| # | 块 | 现役指向 | 目标（AiPalace） |
|---|----|---------|------------------|
| A | **skill 挂载** | `~/.claude/skills`（13 软链）、`~/.codex/skills`（混合）→ dalwin-workflow/awesome-skills/`~/.agents/skills` | `skillctl sync` 生成软链 → `AiPalace/skills`；扁平镜像 core→`~/.agents/skills`；`mount zhijin` |
| B | **rules/context 软链** | `~/.claude/rules/{java-spring,frontend-web}.md` → `~/.agents/context/*` → `dalwin-workflow/context/` | → `AiPalace/context/rules/`（两跳：`~/.agents/context/<域>.md`→AiPalace/context/rules，`~/.claude/rules/<域>.md`→`~/.agents/context/<域>.md`） |
| C | **SessionStart hook** ⚠️ | `~/.claude/hooks/sessionstart-domain.py`：`CONTEXT_BASE='~/.agents/context'` + `DOMAIN_CONTEXT` 指旧扁平 `memory/glossary.md`、`projects/syzh.md`… | 重写：CONTEXT_BASE→AiPalace/context；DOMAIN_CONTEXT 适配三级 5 域（`memory/reference/glossary.md`、`memory/enterprise/zhijin/syzh.md`）；**整合 P3 的 `tools/hooks/inject_index.py`** 注入 `context/INDEX`+`memory/INDEX` |
| D | **/wrap 落盘** ⚠️ | `~/.claude/commands/wrap.md`：SOT=dalwin-workflow/context；落点 `memory/projects/<代号>.md`、`glossary.md`、`ai-workflow.md`（旧扁平）；提交到 `~/Documents/AI` | 重写：SOT→AiPalace/context；落点→三级 5 域（`memory/enterprise/<公司>/`、`memory/projects/<类>/`、`memory/reference/`、`memory/workflow/`）+ self/；hook 接 INDEX；提交到 AiPalace |
| E | **plugins** | `~/.agents/plugins`（marketplace+sql-expert-dba） | → `AiPalace/plugins/{claude,codex}` |
| F | **Codex 侧** | `~/.codex/skills`（软链旧源）、`AGENTS.md`、`hooks/precompact-memory-hint.py`（systemMessage 文本提 dalwin-workflow） | skill 由 A 的 sync 处理；AGENTS.md 指向 AiPalace governance；precompact 提示文本改 AiPalace |
| G | **dalwin-workflow 退役** | 现役 SOT，被 A–F 引用 | 末步：确认零引用后，README 加退役说明，仅留 git 历史 |

**两个待执行时定的对账点**（spec 给建议，执行时实测确认）：
1. **Codex 发现路径**：现役 `~/.codex/skills` 有软链、`~/.agents/skills` 是扁平层。建议：扁平镜像 `~/.agents/skills`（core）兼作 Codex 发现层；`~/.codex/skills` 由 skillctl mounts 同步（core+extra）。执行时用一个 parked skill 实测 Codex 实际从哪发现。
2. **hook 整合形态**：`sessionstart-domain.py`（cwd 域打分，保留）与 `inject_index.py`（INDEX 注入，P3 新增）——建议合成一个 SessionStart 脚本，先打分定域、再注入对应 INDEX 子树（呼应 P3「三门并集」的门 a）。

---

## 3. 分阶段执行方案

### 阶段 0 · 全量备份（前置，必做，不可跳）

```bash
TS=$(date +%Y%m%d-%H%M%S); BK=~/sot-switch-backup-$TS; mkdir -p "$BK"
# 软链指向快照（关键：记录所有现役软链原始指向，回滚依据）
for d in ~/.claude/skills ~/.claude/rules ~/.codex/skills ~/.agents/skills ~/.agents/context ~/.agents/plugins; do
  echo "=== $d ==="; ls -la "$d"; done > "$BK/symlinks-before.txt" 2>&1
# 配置文件 + hook 脚本副本
cp -RL ~/.claude/hooks ~/.claude/commands/wrap.md ~/.claude/settings.json ~/.claude/CLAUDE.md "$BK/claude/" 2>/dev/null || (mkdir -p "$BK/claude" && cp ~/.claude/hooks/*.py ~/.claude/commands/wrap.md ~/.claude/settings.json ~/.claude/CLAUDE.md "$BK/claude/")
mkdir -p "$BK/codex"; cp ~/.codex/AGENTS.md ~/.codex/hooks.json ~/.codex/hooks/*.py "$BK/codex/" 2>/dev/null
# 整目录 tar（含软链本身，不跟随）
tar -czf "$BK/dirs.tgz" -C ~ .claude/skills .claude/rules .agents/context .agents/skills .codex/skills 2>/dev/null
echo "✓ 备份在 $BK"
```
- **验证**：`$BK/symlinks-before.txt` 记录了全部软链指向；`dirs.tgz` 可解。
- **回滚总策略**：任一阶段异常 → 从 `$BK` 还原对应目录/文件（软链按 `symlinks-before.txt` 重建）。

### 阶段 1 · skill 挂载切换

1. 确认 AiPalace `registry.yaml` 已配好（用户另一 session 已完成 26 skill：4 project=zhijin / 1 core / 11 extra / 10 parked）；按需取消注释 `flat_mirror: ~/.agents/skills`、`projects:` 段。
2. 删旧软链（已备份）：清空 `~/.claude/skills/*`、`~/.codex/skills/*`（保 `.system`）、`~/.agents/skills/*` 的非受管软链。
3. `cd AiPalace && python3 tools/skillctl.py sync --dry`（预览）→ `sync`（生成 ~/.claude/skills + ~/.codex/skills + 扁平镜像）。
4. `python3 tools/skillctl.py mount zhijin`（project skill 进 zhijin 项目 `.claude/skills/`）。
5. `python3 tools/skillctl.py doctor`。
- **验证**：新 session 在 AiPalace `/skills` 列表全部来自 AiPalace、标对 tier；在 zhijin 项目目录新 session 能看到 4 个 project skill；doctor 全绿。
- **回滚**：`rm` 新软链 + 按 `symlinks-before.txt` 重建旧软链。

### 阶段 2 · rules/context 软链切换

1. 重指两跳软链：`~/.agents/context/{java-spring,frontend-web}.md` → `AiPalace/context/rules/<同名>`；`~/.claude/rules/<域>.md` → `~/.agents/context/<域>.md`（保持现有两跳形态，仅换最终指向）。
2. （若启用 always-on context）`~/.agents/context/INDEX.md`、`self/` 指向 AiPalace/context。
- **验证**：新 session 在 Java 项目（含 pom.xml）java-spring rule 自动注入，内容来自 AiPalace/context/rules/java-spring.md。
- **回滚**：还原软链指向 dalwin-workflow。

### 阶段 3 · memory + SessionStart hook 重写（最难，核心）

1. `~/.agents/context/memory` → `AiPalace/context/memory`（三级 5 域）。
2. 重写 `~/.claude/hooks/sessionstart-domain.py`（基于 AiPalace 副本管理；建议把脚本本身纳入 AiPalace `tools/hooks/` 受管，再软链/拷贝到 `~/.claude/hooks/`）：
   - `CONTEXT_BASE` → AiPalace/context（或 `~/.agents/context` 已重指 AiPalace）。
   - `DOMAIN_CONTEXT` 路径改三级 5 域（`memory/reference/glossary.md`、`memory/enterprise/zhijin/syzh.md`、`memory/projects/career/go-transition.md`、`memory/workflow/ai-workflow.md`）。
   - **整合 `inject_index.py`**：SessionStart 输出 = cwd 域打分（门 a）+ `context/INDEX` + `memory/INDEX` 注入（always-on 索引树），实现 P3 的渐进披露。
3. 更新 `~/.codex/hooks/precompact-memory-hint.py` 的 systemMessage 文本：dalwin-workflow → AiPalace。
- **验证**：新 session SessionStart 注入含正确域 + INDEX；按 INDEX 指针 Read 的 memory 路径都存在；在 zhijin 项目能被导向 `memory/enterprise/zhijin/`。
- **回滚**：从 `$BK` 还原 hook 脚本 + memory 软链。

### 阶段 4 · /wrap + plugins + Codex 文本

1. 重写 `~/.claude/commands/wrap.md`（建议纳入 AiPalace 受管再派生）：SOT→AiPalace/context；落点路由表改三级 5 域 + self/ + context/INDEX；步骤 4「接通注入索引」改为更新重写后的 hook；步骤 5 提交目标 → AiPalace 仓库。
2. plugins：`~/.agents/plugins` 指向/同步 AiPalace/plugins。
3. `~/.codex/AGENTS.md`：补一句指向 AiPalace PHILOSOPHY/governance（令 Codex 维护本仓库遵循设计哲学，呼应已建的 AGENTS.md）。
- **验证**：`/wrap` 试沉淀一条 → 落到 AiPalace/context 对的三级位置并提交 AiPalace。
- **回滚**：还原 wrap.md/plugins/AGENTS.md。

### 阶段 5 · dalwin-workflow 退役

1. 全局复扫：`grep -rl dalwin-workflow ~/.claude ~/.codex ~/.agents` 应零命中（软链用 `ls -la | grep dalwin-workflow` 复核）。
2. `~/Documents/AI/dalwin-workflow/README.md` 加退役说明（已被 AiPalace 收编、仅留 git 历史、勿再写入）。
- **验证**：零现役引用；双工具新 session 全功能正常（skill/rules/context/memory/hook/wrap）。

---

## 4. 风险与验收

- **每阶段独立可回滚**：阶段 0 全备 + 每阶段前对该部分再快照；异常即还原。
- **最危险**：阶段 3（hook 重写）——建议在此阶段前，把 `sessionstart-domain.py` 改造版先在 AiPalace `tools/hooks/` 写好 + pytest 覆盖（cwd 打分 + INDEX 注入），测过再派生到 `~/.claude/hooks/`。
- **验收（全部阶段后）**：① `grep -r dalwin-workflow` 现役零命中；② Claude 新 session：`/skills` 来自 AiPalace、Java 项目 rules 自动注入、SessionStart 注入 INDEX、`/wrap` 落 AiPalace；③ Codex 新 session：skill 可发现、AGENTS 指向 AiPalace；④ AiPalace `doctor` 全绿。

---

## 5. 执行建议

- **专注新会话执行**，带本 spec，逐阶段。阶段 0/1/2 相对安全可连做；**阶段 3 单独一段、充分测试**；阶段 4/5 收尾。
- 每阶段完成在本 spec 或新 ledger 记 `阶段 N done`，便于中断恢复。
- 阶段 3 的 hook 改造，建议走 ADR（推翻 dalwin-workflow 的 domain-context 机制、确立 AiPalace INDEX 注入）+ 小 plan + TDD，再派生到现役。
