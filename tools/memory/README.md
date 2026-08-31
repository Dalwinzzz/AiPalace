# tools/memory — 手动飞轮确定性内核

> 飞轮的机器部分。**只调 `config.toml`**;脚本仅在改逻辑时动。
> 设计:LLM(在场 agent)只抽候选+提议落点;打分/去重/把门/写盘全确定性;人审批才晋升。
> 决策依据:spec `docs/superpowers/specs/2026-07-02-M5手动飞轮-design.md`(D1–D8)。

## 脚本

| 脚本 | 干什么 | 谁触发 |
|------|--------|--------|
| `core.py distill` | 扫 journal 近 N 天 → merge → 六维打分 → 去重(ADD/UPDATE/NOOP) → gate → 候选草稿进 `candidates.md`。**绝不改 00-RULES 正文** | `/ai-palace` 步骤 3(手动) |
| `promote.py` | 把 `candidates.md` 勾 `[x]` 的候选晋升到 dest(白名单复验;追加不覆盖;标 ✅done 防重),DREAMS 留痕。**不做 git** | `/ai-palace` 步骤 5(人审批后) |

## 跑法

```bash
python3 tools/memory/core.py distill --shadow   # 影子:只打印不落盘(先这样验)
python3 tools/memory/core.py distill            # 正式:写候选 + DREAMS
python3 tools/memory/promote.py --dry-run       # 看会晋升什么
python3 tools/memory/promote.py                 # 晋升
python3 -m unittest discover -s tools/memory -v # 测试(stdlib,零依赖)
```

## 调参(config.toml)

- `[scoring]`:候选太多 → 调高 `promote_threshold`;global 铁律太松 → 调高 `min_freq_global`。
- `[routing]`:晋升落点白名单(rules 封闭 5 文件 + 01-PROJECTS 五域前缀)。
- 依据 DREAMS 的达标/暂缓数据调,不拍脑袋。

## 边界

- UPDATE 是**追加并标注**,不自动覆盖——真合并人工做,安全优先。
- global 候选需 journal 出现 ≥2 次(可跨天/跨工具),一次性说法进不了 00-RULES——这是特性不是 bug。
- 与同事原版差异:无 cron、无 subprocess LLM 抽取(`[llm]` 段整段不存在);dedup 语料扩到 01-PROJECTS。
