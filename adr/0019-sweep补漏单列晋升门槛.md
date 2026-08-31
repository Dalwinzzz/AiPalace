# ADR-0019 · sweep 补漏单列晋升门槛

- 状态：Accepted
- 日期：2026-07-31
- 相关：ADR-0013（记忆层）、M5 手动飞轮 spec `2026-07-02-M5手动飞轮-design.md`

## 背景

M5 飞轮的晋升门槛 `[scoring].promote_threshold = 0.50` 是按**会话内 `/ai-palace`** 的场景标定的：同一事实在连续几天的 journal 里反复出现，`freq` 累积推高分数后达标。

`/ai-palace sweep`（A 主 B 补的 B 通道）场景不同：它一次性扫描历史漏网会话，把几十个会话里的事实**一次全部写进当天 journal**。这些条目天然 `freq = 1`，而 `w_frequency = 0.24` 是六维里第二大的权重，`frequency` 子分恒为 0.50，直接锁死约 0.12 的分数上限损失。

实测证据（DREAMS 可复算）：

| 轮次 | 日期 | 候选数 | 达标 | 分数区间 |
|------|------|--------|------|----------|
| sweep #1 | 2026-07-05 | 13 | 0 | 0.424 – 0.470 |
| sweep #2 | 2026-07-31 | 15 | 0 | 0.418 – 0.471 |

两轮 28 条候选**零达标**，且分布高度集中（全部落在 0.42–0.47），说明这不是内容质量的区分结果，而是参数与场景不匹配导致的结构性压分。后果是 journal 持续留痕但 vault 一条不进，enterprise 域知识长期滞后于实际工作。

## 决策

1. 在 `tools/memory/config.toml` 的 `[sweep]` 段新增 `promote_threshold = 0.42`，**仅供 sweep 补漏通道使用**。
2. `core.py distill` 新增 `--sweep` 开关：置位时用 `[sweep].promote_threshold` 覆盖 `[scoring].promote_threshold`，其余五维权重、合并/去重阈值一律不动。
3. **`min_freq_global` 不放宽**：`scope=global` 仍需 journal 出现 ≥2 次才可进 `00-RULES`，always-on 层的把门不因 sweep 而降低。
4. 会话内 `/ai-palace`（不带 `--sweep`）行为完全不变，仍是 0.50。
5. DREAMS 摘要行标注 `(sweep·门槛 0.42)`，人工提权的条目另行显式标注，保持全程可审计。

## 取舍

- **为什么不下调全局阈值**：会话内通道的 0.50 标定是有效的（2026-07-02 实测有条目正常达标），全局下调会连带放宽本不该放宽的路径。
- **为什么不改 `w_frequency`**：改权重会重写所有历史打分口径，DREAMS 里既有的分数不再可比，违背"确定性可复算"的设计前提。单列阈值是局部、可回滚的最小改动。
- **0.42 怎么定的**：取两轮实测分布下沿（0.418/0.424）之上一点，既让有实质信息量的条目通过，又保留对空泛条目的区分度。本轮 15 条中仍有 1 条（0.418）未自动达标，说明门槛没有退化成"全放行"。
- **接受的代价**：sweep 晋升条目的 `confidence` 均为 `low`，属于"先落库、后续被真实使用时再确认"的一次沉淀。若后续发现 sweep 条目噪声偏高，应回到本 ADR 重新标定，而非临时手改。

## 后果

- 2026-07-31 sweep 第二轮：14 条自动达标 + 1 条经用户审批人工提权，共 15 条晋升；新建 `skc-infant.md`、`linan-xinchuang.md` 两个 vault note 并给 INDEX 决策树接线。
- 2026-07-05 sweep 第一轮的 13 条仍留在 DREAMS：`scan_days = 3` 的窗口已滑过，不会被本次改动追溯捞回。若判断其中条目仍有价值，需重新写入 journal 走一遍飞轮。

## 验证

- `python3 -m pytest tools/memory/{test_core,test_promote,test_gather}.py` → 26 passed（gate 签名未变，既有用例零改动）。
- `core.py distill --shadow`（默认通道）→ 15 条候选、达标 0，与改动前一致。
- `core.py distill --sweep` → 达标 14 / 暂缓 1。
