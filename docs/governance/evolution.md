# evolution.md — 演进流程规范

> 本文档定义 AiPalace 的演进操作 SOP：skill 工作流、ADR append-only 规则、上游同步策略与 SOT 指向切换路径。  
> 最高准绳：[`PHILOSOPHY.md`](../../PHILOSOPHY.md)（P1–P9）。

---

## 1. Skill 工作流

修改任何 skill（新增、下架、调整 tier/category）只经以下四步，不得绕过（体现 [P2](../../PHILOSOPHY.md#p2--声明式管理工具派生限内容资产)）：

```
1. 修改 registry.yaml          ← 唯一手改入口
2. skillctl sync --dry          ← 预览将生成/更新的软链，确认无误
3. skillctl sync                ← 实际派生软链到两个挂载点
4. skillctl doctor              ← 校验完整性，全绿才结束
```

**禁止：**

- 直接编辑或删除挂载点（`~/.claude/skills/`、`~/.codex/skills/`）下的受管软链
- 跳过 `doctor` 步骤提交变更
- 未经 `sync` 就在挂载点手动创建软链

`doctor` 不绿，不提交，不合并。skill 规范细则见 [`content-assets/skills.md`](content-assets/skills.md)。

---

## 2. ADR：append-only 与 supersede 规则

### 2.1 ADR 是不可变决策事件流

ADR（Architecture Decision Record）是 AiPalace 的决策事件流档案（体现 [P8](../../PHILOSOPHY.md#p8--决策留痕诚实标注)）：

- **只新增，不删改**：已合并的 ADR 一旦定稿，其内容不再修改，也不删除
- 每条 ADR 记录一次具体决策的背景、权衡与后果
- ADR 的编号单调递增，用前缀零补齐四位（`0001`、`0002`…）

### 2.2 被推翻的决策如何处理

当某次新决策推翻了既有 ADR 的结论：

1. **新建一条新 ADR**，在其正文中明确标注 `Supersedes ADR-XXXX`
2. **在被推翻的旧 ADR 头部**添加显著提示，注明"被 ADR-YYYY 推翻/修正（日期）"及推翻原因摘要
3. **旧 ADR 主体内容保留不删**——它是实证演进的真实记录，是 P8 留痕的核心体现

**旧 ADR 头部提示格式：**

```markdown
> ⚠️ **被 [ADR-XXXX](XXXX-文件名.md) 推翻/修正（YYYY-MM-DD）。**
> 简要说明推翻原因。本文保留不删改，作为实证演进的真实记录（P8 决策留痕）。

- 状态：~~已接受~~ → **被 ADR-XXXX 推翻/修正**
```

### 2.3 活案例：ADR-0005 推翻 ADR-0002

[ADR-0002](../../adr/0002-借鉴garveyhu方案但改硬拷贝.md) 基于 issue #14836 判定"symlink 进 `~/.claude/skills` 不出现在 `/` 斜杠菜单"，据此将 `skillctl sync` 的派生形态改为硬拷贝。

2026-06-17 本地实测证伪了该结论：symlink 形态的 skill 可正常出现在 `/` 菜单。[ADR-0005](../../adr/0005-实测修正symlink可见性并回归symlink派生.md) 记录了实测证据，明确标注 **Supersedes ADR-0002**，决策回归 symlink 派生。ADR-0002 头部同步添加了推翻提示，正文保留完整（体现 [P5](../../PHILOSOPHY.md#p5--实证选型不照搬) 实证选型 + [P8](../../PHILOSOPHY.md#p8--决策留痕诚实标注) 留痕）。

### 2.4 何时需要写 ADR

以下情形**必须写 ADR**：

| 情形 | 说明 |
|------|------|
| 推翻既有决策 | 新证据/新实测使某条已有 ADR 的结论失效 |
| 改变仓库结构 | 目录结构调整、资产分类体系变动、新增顶层目录 |
| 改变设计哲学 | 对 P1–P9 任一原则的修订或例外豁免 |
| 引入新机制 | 新增工具链（如新脚本、新 hook 机制）或废弃旧机制 |
| 重大取舍 | 多个方案有明显权衡，选定方案需保留推理过程以备追溯 |

**不需要写 ADR 的情形**：常规 skill 新增/修改（走工作流即可）、文档内容更新、小范围命名修正。

---

## 3. 上游同步（`upstream_sync.py`）

### 3.1 两层区分

AiPalace 对 community skill 的处理分两层，不可混淆：

| 层 | 机制 | 位置 | 性质 |
|---|------|------|------|
| **存储层（备份快照）** | `upstream_sync.py` 硬拷贝 | `skills/community/<source>/<skill>/` | 仓库内 SOT，不再修改 |
| **挂载层（派生软链）** | `skillctl sync` symlink 派生 | `~/.claude/skills/`、`~/.codex/skills/` | 派生产物，不作内容入口 |

两层相互独立：存储层保证仓库内有完整真身；挂载层把真身软链派生到工具可见路径。

### 3.2 `upstream_sync.py` 的职责

`upstream_sync.py` 是 Codex 定时任务：

- 将上游社区 skill 仓库（`git clone`）的内容**硬拷贝**进 `skills/community/` 作为**备份快照**
- 备份快照落入仓库后即为不变档案（不再追踪上游变更，除非手动触发新一轮 sync）
- 属"仓库内 SOT 存储层"，**与 `skillctl sync` 的 symlink 派生挂载层无关**

保留硬拷贝而非直接指向上游的理由：保证离线可用、防止上游变更污染本地配置、符合 P1 单一真源（所有真身在本仓库内可查）。

### 3.3 新增 community skill 的完整流程

```
1. upstream_sync.py        ← 将上游硬拷贝到 skills/community/<source>/<skill>/
2. 补充 _SOURCE.md         ← 标注 upstream / credit / license（见 skills.md 第 8 章）
3. 在 registry.yaml 登记   ← 填入 source / category / tier
4. 走 skill 工作流         ← sync --dry → sync → doctor
```

---

## 4. SOT 指向切换（final-spec 承接）

**终态目标**：双工具（Claude Code / Codex）的 hook、path-scoped rules 软链、`/wrap` 落盘目标，从 `~/Documents/AI/dalwin-workflow` 改指向 `AiPalace`；`dalwin-workflow` 退役为 git 历史。

**触发条件**：以下全部满足方可执行切换（体现 [P9](../../PHILOSOPHY.md#p9--显式过渡态)）：

- [ ] context / rules / memory 内容按规范完整落地
- [ ] skill 全部按 registry 规范迭代完毕，doctor 全绿
- [ ] 双工具 SessionStart hook 已按 `injection.md` 规范接入
- [ ] 以上验证通过后，由独立 **final-spec** 承接执行切换

**本文档不执行切换**——它只是记录切换的前提条件与操作归属。切换是整个工程的最终一步，在此之前 `dalwin-workflow` 与 `AiPalace` 并存，过渡态由 [P9](../../PHILOSOPHY.md#p9--显式过渡态) 显式管理。

---

## 5. 规范修订流程

修订任何治理规范文档（`docs/governance/` 下）时：

1. 若修订属于"改变结构或哲学"（见第 2.4 章），**先写 ADR**
2. ADR 定稿后再修改对应规范文档，在文档中引用该 ADR
3. 规范修订通过 PR 合并，commit message 遵循 `<type>(<scope>): <subject>` 约定

> `PHILOSOPHY.md` 是最高准绳，修订门槛最高：必须写 ADR，且 ADR 需明确说明修订理由与影响范围。

---

*本规范依据 spec §8（`2026-06-18-aipalace治理与设计哲学-design.md`）成文，引用 [P5](../../PHILOSOPHY.md#p5--实证选型不照搬)、[P8](../../PHILOSOPHY.md#p8--决策留痕诚实标注)、[P9](../../PHILOSOPHY.md#p9--显式过渡态)。*

---

## 6. 显式过渡态清单（P9）— 记忆层 feat/obsidian-memory-vault 分支登记（2026-06-30）

> 以下四条为 [ADR-0013](../../adr/0013-吸收记忆宫殿方法论建Obsidian记忆层.md) 所登记的已知不一致与待决项，由 P9 显式管理，非默默漂移。收敛后逐条划线 + 注明日期。

### 6.1 Windows symlink 派生（skillctl 跨 OS）—— 待专项

`skillctl sync` 依赖 `os.symlink()`，Windows 需开启 Developer Mode 或以管理员权限运行，否则软链失败。**vault 纯 markdown，不受此问题影响**，跨 OS 同步可正常使用。但工程机器（skills 派生）在 Windows 上尚无验证方案，待单独专项解决。

**收敛路径**：Windows 侧实测 + 若需适配改 skillctl 或改用 junction point → 写 ADR → 修 skillctl。

### 6.2 ~~M4 全局指令整合 + native 瘦身~~ —— 已收敛（2026-07-03，ADR-0016）

**结果**：共享规则单一源 `vault/memory/00-RULES/operating-rules.md`（SessionStart hook 双工具注入，顺序：操作规则→INDEX）；native 全局文件瘦为 `context/native/{claude-global,codex-global}.md` 双 stub 并经软链派生（`~/.claude/CLAUDE.md`、`~/.codex/AGENTS.md`），原件快照存档 `docs/archive/native-globals-2026-07-03/`。设计：spec `2026-07-03-M4全局指令整合-design.md`（D1–D8）。

### 6.3 ~~`/wrap` 退役时点~~ —— 已收敛（2026-08-03，ADR-0021）

**结果**：用户确认 `/ai-palace` 已跑两轮、可独立承接，M5-C 执行完毕——`commands/wrap.md` 真源与 `~/.claude/commands/wrap.md` 派生已删，PHILOSOPHY / injection / commands / memory / vault 五处指引改指 `/ai-palace`。M5-B `gather_sessions.py` sweep 通道**未实现即随 `/wrap` 一并放弃**：其定位是"补 `/wrap` 漏掉的会话"，`/wrap` 退役后该补漏需求由飞轮自身覆盖。

### 6.4 M5 飞轮引擎 —— M5-A 已交付（2026-07-02），余 M5-B/M5-C

**现状**：M5-A 已在 `feature/m5-flywheel` 分支交付并 dogfood 验收通过——`tools/memory/{core,promote}.py` 确定性内核（六维打分/去重/gate/白名单/DREAMS 留痕，18 用例）+ `04-FEEDBACK` 三件套 + `/ai-palace` 命令（真源 `commands/ai-palace.md`，Claude/Codex 双派生）。验收证据：影子复算两次分数逐位一致；global 候选 freq=2 过门、freq=1 暂缓（gate 正确）；promote 追加/done 防重验证通过。设计依据：spec `2026-07-02-M5手动飞轮-design.md`（D1–D8）。

**待决余项**：~~M5-B sweep~~（随 `/wrap` 退役放弃，见 6.3）、~~M5-C~~（已执行，ADR-0021）。本条已收敛。
