# ADR-0022：vault 维护宪法、二轮归档与 INDEX 瘦身

- 状态：已接受
- 日期：2026-08-03
- 决策人：dalwin
- 关联：承接 [ADR-0021](0021-三套记忆收敛与wrap退役.md)（三套记忆收敛，方案 C）；兑现其"二轮归档"待办与 [ADR-0020](0020-注入机制实测纠偏.md) 的"INDEX 瘦身"待办

## 背景

ADR-0021 首轮归档时，为求稳采用"追加不合并"，在每个 vault 文件末尾留了一节「自 Codex memories 首轮归档」+ 两行迁移说明，条目还带着 Codex 内部的 `[Task N]` 标记。

dalwin 指出这类内容**根本不该进 vault**：vault 的每个字都注入未来每次会话，**迭代过程叙述对未来零价值，只消耗预算、稀释信号**。要求先清干净，再把这条规矩写成项目级注入文档约束后续。

## 决策

### 1. 立 vault 维护宪法

新增 `vault/CLAUDE.md`（`vault/AGENTS.md` 软链同源，Codex 侧同样加载）。读写 `vault/` 下任何文件时自动加载，核心是一条铁律与一张对照表：

**vault 只存事实与约束，不存迭代过程。** 禁止：变更叙述、迁移说明、时序自指（此前/本轮/曾把/改为指针）、决策论证、过程中间量、会话级自省。允许：当前为真的事实、约束与规则、实测结论与踩坑（只写结论和正确做法）、导航指针。

**变更历史归 ADR，不归 vault。** vault 出现 ADR 编号只有一种合法用法：当前规则本身需要引用；用来解释"这条为什么变了"即违规。

### 2. 清除既有过程叙述

- 11 个文件的「首轮归档」小节标题与两行迁移说明、174 处 `[Task N]` 标记。
- 逐处清理存量：`skills-root.md` 的"旧版本曾把 X 当 SOT"对比块、`cross-tool-memory.md` 的"已知的重复案例（归档时清理）"、`INDEX.md` 的划线条目与并入说明、`ops.md`/`operating-rules.md`/`identity.md` 的 ADR 编号旁注、`skc-datasum.md` 的"曾把某分支改名"、`codeisland-distill.md` 的"此前仅 CLT 时"、`skc-activity.md` 的会话级自省。
- `source:` frontmatter 统一收敛为来源类别（`native-memory 迁入` / `codex-memory 迁入` / `ai-palace 晋升`），不写迁移批次与 ADR 编号。

**`promote.py` 停止落 `score`/`freq` 留痕**：这两个值是晋升过程的中间量，`_stamp()` 写出去后**从没有任何代码读回**，纯属注入成本。行尾留痕只保留日期（判断新鲜度要用）与"UPDATE 待人工合并"（待办信号）；存量 13 个文件同步剥除。打分复盘去 `04-FEEDBACK/DREAMS.md` 看。飞轮 13 个用例仍全绿。

### 3. 二轮归档：10 个 per-project memory

ADR-0021 保留未动的约 400KB 逐 repo 知识，本轮全部归档。**按宪法只留稳定事实**，逐 commit 实现进度、待办清单、"本轮未接入"之类的在途状态一律丢弃——那属于各仓自己的 `docs/`，不是跨设备记忆。

主要落点：`skc-nursery.md`（dbq 双区域查库入口、JDK8 编译、画像 scope=0 与 seal NPE 两条已验证根因、鄂尔多斯/善育在杭区域口径、min-kernel 分支状态）、`skc-activity.md`（无聚合 pom 构建、包结构约定、南京体检遗留层路线、可预约时间物化模型、mchis 对接口径、驿站统计性能）、`skc-infant.md`（三层库拓扑与取数归属、两套数据世界、v1.0.4 写入侧、契约与 Apifox 约定）、`architecture.md`（framework 源码查找顺序、禁用 PUT/DELETE 网关限制）、`ops.md`（分支交付约定、AI 产物落盘、Bash cwd 陷阱）、新建 `projects/rainmeter-skin.md`、重写 `projects/waitfortickets.md`。

归档中发现并解决的两处**冲突**：
- `architecture.md` §11 定「测试只留本地、不要 `git add -f`」，但 skcnursery 侧记忆写着"入库需 `git add -f`（8 个测试类都这么加的）"。以 vault 规则为准，改为"默认不强推，仅用户明确要求时逐个 `-f`"。
- skciotdevice 侧记「不要在本地找 framework/common 源码」，`architecture.md` §3 记「直接从父目录找 kernel-framework 源码工程读」。二者其实是不同前提，合并为三步顺序：找同级/上级源码工程 → 无则 grep 调用侧推断 → 再不行去本地 Maven 仓库 `jar tf`/`javap`（绝不用 `~/.m2`）。

`waitfortickets.md` 原本停留在已废弃的 v3 Web 方案，本轮按当前 v4.1 Android 形态重写，并写明 Web 路线撞死墙的技术原因（HttpOnly cookie 拿不到）以免回头再提。

工具侧 10 个目录全部改为指针。**Claude auto memory 总量 450KB → 48KB；Codex 记忆索引 64KB → 2.2KB。**

### 4. INDEX 瘦身

`INDEX.md` 末尾的「当前整树文件索引」ASCII 树是上半部决策树的**逐条重复**（同样的文件、同样的说明写两遍），占近三分之一篇幅，直接删除。触发机制三门从表格压成一行。决策树本身保留全部路由能力，并补上本轮新增的 7 个 note。

**6393 → 3156 字符（-51%）。**

## 后果

**正面**：always-on 预算 **14403 → 9872 字符（-31%）**，其中 hook 注入 9698 → 6338。vault 里不再有"解释这里发生过什么变化"的句子，注入的每一句都是当下为真的事实或约束。两处跨文件冲突被显式消解而不是各留一份。宪法作为 path-scoped 文档挂在 `vault/` 上，改 vault 时自动加载，比写进 governance 文档更贴近动作发生的位置。

**取舍 / 待观察**：
- 二轮归档丢弃了大量在途实现状态（分支进度、commit 号、TODO）。这是**有意的**——它们在各仓 `docs/` 里有更完整的版本，且几周内必然过期。若日后发现某类在途状态确实需要跨设备可见，应设计专门的载体，而不是放回 vault。
- 归档采用人工判读而非机械搬运，可能漏掉个别有价值条目。原始记忆全量备份在本次会话 scratchpad `memory-backup-20260803/`（704KB），**随 scratchpad 生命周期存在**，需要长期留存应尽早另存。
- 宪法靠 `vault/CLAUDE.md` 的 path-scoped 加载生效，而 ADR-0020 实测确认该机制是**读文件才触发**——只在对话里谈论 vault 而不读写其中文件时不会加载。真正的执行保障仍是写入时的自检习惯。
