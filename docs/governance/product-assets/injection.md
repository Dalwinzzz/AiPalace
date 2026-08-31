# injection.md — 注入机制规范

> 关联哲学：[PHILOSOPHY P7](../../../PHILOSOPHY.md#p7--内容统一源机制分治)
>
> 本规范定义「如何把 AiPalace 内容资产注入到双工具运行时」的机制，不涉及内容本身的格式与规则（见 `content-assets/`）。

> ⚠️ **过渡态说明（ADR-0013，2026-06-30）**：`context/self/` 与 `context/memory/` 已迁移至 `vault/memory/`（`00-RULES/` + `01-PROJECTS/`），原 `context/INDEX.md` 与 `context/memory/INDEX.md` 已废弃。SessionStart hook 现注入单一的 **`vault/memory/INDEX.md`**。本文档下文的「机制 A」按此新现实更新；`rules/` 仍在 `context/rules/` 原处，机制 B/C/D 不受影响。M4 已完成（ADR-0016）：机制 A 现为双文件注入，native 全局文件为受管 stub 派生。

---

## 原则

**内容统一源、注入机制分治（P7）。**

- `context/`、`memory/`、`rules/`、`skills/` 等内容资产工具无关，由各自 `content-assets/` 规范约束。
- 注入机制（hooks / path-scoped 触发 / native 协同）与各工具 harness 形态耦合，**每种工具独立维护自己的注入配置**，不共享同一份钩子脚本。

---

## 注入机制总览

AiPalace 通过三条独立但互补的路径把内容注入到双工具会话：

| 机制 | 触发时机 | 注入内容 | 双工具实现 |
|------|----------|----------|------------|
| **A. SessionStart hook** | 每次会话启动 | `00-RULES/operating-rules.md` + `00-RULES/identity.md` + `INDEX.md` | Claude `~/.claude/hooks` / Codex `~/.codex/hooks` |
| **B. path-scoped 硬触发** | **读取工作区内匹配 `paths` 的文件时**加载（ADR-0020 实测） | `rules/` 下各域规则 | Claude `rules-glob`（`paths:` 软链，已验证生效）/ Codex **无接线**（见下） |
| **C. native memory 协同** | 持续生效（工具原生） | 双工具自身的 native memory 沉淀 | 各工具原生机制（不修改） |

三条路径**正交**：A 管「每次会话共性上下文」，B 管「路径相关规则」，C 管「工具原生积累」。任何一条失效不影响其他两条兜底。

> 说明：上述「三条」指的是**内容注入**路径（A/B/C），负责把内容资产注入会话。机制 D（非内容类 hooks）管理 commit 规范、pre-commit 检查等工具自动化钩子，不计入注入三门。

---

## 机制 A：SessionStart hook（全局上下文注入）

### 目的

在会话启动时按序注入三件套：`00-RULES/operating-rules.md`（双工具共享操作规则，法律在前）→ `00-RULES/identity.md`（精简身份卡）→ `INDEX.md`（决策树导航，在后），保证会话始终持有全局约定、身份与记忆索引，无需人工粘贴（ADR-0016；identity 于 ADR-0020 并入直注）。

### 双工具实现

| 工具 | 钩子注册位置 | 触发事件 | 逻辑 |
|------|-------------|----------|------|
| Claude Code | `~/.claude/hooks/` | `SessionStart` | 按序读取 always-on 三件套，拼接后以 `additionalContext` 注入 |
| Codex | `~/.codex/hooks/` | `SessionStart`（同逻辑） | 与 Claude 版逻辑一致，harness 差异隔离于各自目录 |

- 两工具 hook **注入逻辑语义相同**，但脚本各自维护——不共享同一可执行文件（工具 harness 格式不同）。
- 注入粒度：always 注入三件套 + 整棵 INDEX；按 cwd 裁剪 INDEX 子树为演进项（树已达 6.4KB／占 always-on 近半，ADR-0020 记为待办，等记忆层收敛定形后再做）。

### 分治要点

- Claude hook 配置只在 `~/.claude/hooks/` 维护，不混入 Codex 目录。
- Codex hook 配置只在 `~/.codex/hooks/` 维护，不混入 Claude 目录。
- 两者共享的**唯一源**是 AiPalace 仓库里的内容文件本身，且**共用同一份实现** `tools/hooks/sessionstart.py`（两侧 `sessionstart-domain.py` 均为其软链）。

### native 全局文件派生（M4，ADR-0016）

`~/.claude/CLAUDE.md` 与 `~/.codex/AGENTS.md` 为 `context/native/{claude-global,codex-global}.md` 的**软链派生**（同 commands 模式）：stub 只留工具专属规则 + 受管头注 + 兜底指针（hook 失效时手读 operating-rules 绝对路径）；工具无关共享内容一律在 `operating-rules.md`，不回流 native。改 stub 走仓内真源，勿手改派生。

---

## 机制 B：path-scoped 硬触发（rules 按路径加载）

### 目的

当 AI 工具**打开**特定技术域的文件时，自动加载该域的编码规则（如 `java-spring`、`frontend-web`），无需用户每次手动激活。

### 触发语义（ADR-0020 实测，勿凭直觉理解）

触发条件是**读取工作目录树内匹配 `paths` 的文件**，**不是** cwd 落在该项目：

| 场景 | 是否注入 |
|------|---------|
| 在 Java 项目根启动会话，但不读任何文件 | ❌ 不注入 |
| 同一会话读一个 `.java` | ✅ 注入（`load_reason: path_glob_match`，payload 带 `globs` + `trigger_file_path`） |
| 在别处启动，读**工作区之外**的 `.java` | ❌ 不注入（glob 相对工作目录树匹配） |

推论：`paths` 要按"这个域会打开哪些文件"设计；仅靠"在这个目录里干活"是拉不到规则的。

### 双工具实现

| 工具 | 实现方式 | 状态 |
|------|----------|------|
| Claude Code | `~/.claude/rules/<域>.md` → `~/.agents/context/<域>.md` → AiPalace `context/rules/<域>.md`（两跳软链），`paths:` glob 触发 | ✅ **已实测生效**：`file_path` 直解到 AiPalace 真源，`memory_type: User` |
| Codex | —— | ❌ **无接线**：项目树上溯至根无任何 `AGENTS.md`，Codex 侧不消费 `context/rules/`。原文档所称"目录树 AGENTS.md 方案"从未落地 |

- Claude 方案：软链保持统一源，多工程共用同一规则文件，无重复；glob 精准匹配避免跨项目污染。
- Codex 侧现状与去向见 [ADR-0020](../../../adr/0020-注入机制实测纠偏.md)：**不补第二份副本**，改由 [ADR-0021](../../../adr/0021-三套记忆收敛与wrap退役.md) 的记忆收敛（工具侧记忆去重、指针回指 vault）统一解决。

---

## 机制 C：native memory 协同（不替代、只增强）

### 原则

**尊重双工具自身 harness 的原生 memory 机制；AiPalace 仓库只做增强，不替代。**

### 定位

- Claude Code 与 Codex 各自维护原生 memory（会话产生的摘要、用户偏好、持久化上下文）。
- AiPalace `memory/` 是**人工策展的持久化真源**，与原生 memory 互补而非冲突。
- 原生 memory 的沉淀可作为 AiPalace `memory/` 的**上游提炼源**——周期性从双工具 native memory 中凝练提取高价值条目，合并写入仓库 `memory/` 对应域。

### 工作流

```
工具原生 memory 自动积累
        │
        │ (周期蒸馏，/ai-palace 飞轮；ADR-0021 决策 C)
        ▼
AiPalace vault/memory/<域>.md  ←─── 人工直接编辑
        │
        │ SessionStart hook 注入
        ▼
  会话启动时注入 operating-rules.md + INDEX.md
```

- native memory 不被删改，AiPalace 仓库 memory 是在其之上的**人工提炼层**。
- `/ai-palace` 是唯一沉淀路径（`/wrap` 已于 ADR-0021 退役）：工具原生记忆是**入口层**，只攒未归档的本机新发现；归档进 vault 后原处删除留指针，不留副本。

---

## 机制 D：非内容类 hooks（自动化钩子分治）

commit-msg 强制格式（`<type>(<scope>): <subject>`）、pre-commit 检查等非内容类自动化钩子，**不属于内容注入范畴**，但同样遵循工具分治原则：

- Claude 的 commit-msg / pre-commit 等钩子登记在 `~/.claude/hooks/`。
- Codex 的对应钩子登记在 `~/.codex/hooks/`。
- 各自目录自治，不交叉依赖。

---

## SOT 切换归属说明

> **本规范只定义机制，不执行 SOT 切换。**

「把双工具 hooks / rules 软链 / 沉淀落盘目标从旧工作区改指向 AiPalace」属于 **SOT 切换操作**。该切换已完成（hooks 双侧软链回仓、rules 两跳软链回仓并经 ADR-0020 实测确认、沉淀目标为 vault）。

当前状态：AiPalace 为机制与内容规范的 SOT；实际工具注入点指向切换留待 final-spec。

---

## 参考

- [PHILOSOPHY.md P7](../../../PHILOSOPHY.md) — 内容统一源、机制分治原则
- [context.md](../content-assets/context.md) — context 资产规范（含 INDEX 结构）
- [memory.md](../content-assets/memory.md) — memory 资产规范（含 `/ai-palace` 飞轮流程）
- [rules.md](../content-assets/rules.md) — rules 资产规范
- 设计 spec §7.1：`docs/superpowers/specs/2026-06-18-aipalace治理与设计哲学-design.md`
