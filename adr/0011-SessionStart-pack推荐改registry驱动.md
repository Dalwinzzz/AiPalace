# ADR-0011：SessionStart pack 推荐改 registry 驱动

- 状态：已接受
- 日期：2026-06-26
- 决策人：dalwin
- 关联：延续 [ADR-0007](0007-SessionStart-hook以AiPalace-INDEX注入取代domain-context.md) 的 SessionStart hook；强化 [P2 声明式单一源](../PHILOSOPHY.md#p2--声明式管理工具派生限内容资产)

## 背景

`sessionstart.py` 的 `DOMAIN_PACKS` 是**手写硬编码的 skill 名清单**，与 `registry.yaml` 脱节、随时间漂移成"老清单"：

- `java/spring` 域漏掉 `ownerpowers` / `biz-workflow`（用户在该域的**主力 project skill**，tier:project:zhijin），SessionStart 即使 skill 文件可见也不提示用它们；
- 清单里混入 registry 中已不存在或从未登记的名字。

违背 P2——registry 应是 skill 的单一事实源，推荐不应另维护一份会漂移的平行硬编码。

## 决策

**pack 推荐改为 registry 驱动**：

1. **`DOMAIN_PROJECT`**（cwd 工作域 ↔ registry project）：公司域 `java/spring → zhijin`，运行时**动态拉取** `project==zhijin` 的全部 project skill。registry 增减该项目 skill，pack 自动跟随，永不漏、不漂移。
2. **`DOMAIN_EXTRA`** 补充推荐：裸名 = registry 内 skill basename，脚本**校验存在性、漂移名自动剔除**；`+` 前缀 = registry 外的 superpowers/MCP/bundled **兜底推荐**（恒保留，输出去前缀）。
3. **`build_pack(domain, skills)`** = `sorted(project skill)` + 校验后的 extra；`_registry_skills()` 经 `import skillctl` 复用 `load_registry()`（`skillctl.REG` 由其 `__file__` 解析回 AiPalace，软链/异常 cwd 下均定位正确）；registry 不可用时优雅降级（空 + 仅保留 `+` 兜底名）。
4. **双工具即时生效**：`~/.claude/hooks/` 与 `~/.codex/hooks/` 的 `sessionstart-domain.py` 均软链回本文件，改动对两工具同时即时生效，无需重派生。

## 后果

**正面**：`ownerpowers`/`biz-workflow` 等主力 project skill 在公司域 SessionStart 必被推荐且随 registry 同步；推荐源唯一（registry），消除平行清单漂移（P2）；extra 校验机制让 registry 中删除的 skill 自动从推荐消失；`+` 前缀显式区分 registry 内/外，兜底推荐（含 superpowers）与单一源解耦并存。

**取舍 / 待观察**：
- **域↔project 映射仍硬编码**（`DOMAIN_PROJECT`），但仅一行稳定映射，远比 skill 名清单稳定；新增公司 project 时需补一行。
- **SessionStart 每次 `load_registry()`**：读 85 行 registry + 正则，开销极小（一次/会话），可接受。
- `DOMAIN_EXTRA` 的 `+` 兜底名（superpowers/MCP）仍是人工维护的小清单——与 [task4 superpowers 兜底软约束] 协同，二者职责区分：pack 是"域内顺手推荐"，软约束是"流程级前置触发"。
