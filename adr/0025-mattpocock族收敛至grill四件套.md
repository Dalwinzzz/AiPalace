# ADR-0025：mattpocock 族收敛至 grill 四件套

- 状态：已接受
- 日期：2026-08-04
- 决策人：dalwin
- 关联：Supersedes [ADR-0024](0024-wayfinder不落地与ownerpowers吸收T3决策地图.md) 中"`wayfinder` 保持 `tier: extra` 在库，供个人项目按需使用"一句；其余部分仍有效

## 背景

ADR-0023 引入 mattpocock 族 8 个 skill 全部 `tier: extra`；ADR-0024 判定 wayfinder 不接公司 GitLab，但保留其挂载"供个人项目按需使用"。

wayfinder 的设计已在 ADR-0024 完整吸收进 `ownerpowers` T3（`workflows/decision-map.md`）。继续挂载一个不打算用的入口，只是在每次会话付它的描述预算。

## 决策

保留挂载 4 项，其余 4 项降 `parked`（仓内留档，不挂载、不占预算）。

| skill | tier | 理由 |
|---|---|---|
| `grilling` | extra | 全族地基；`ownerpowers` T2 脑暴与 T3 拷问型条目直接调用 |
| `grill-me` | extra | 原有资产，`/grilling` 的斜杠别名 |
| `grill-with-docs` | extra | 原有资产 |
| `domain-modeling` | extra | **`grill-with-docs` 的硬依赖**——后者全文只有"跑 `/grilling` + `/domain-modeling`"两行，卸它即断链 |
| `wayfinder` | parked | 设计已吸收进 ownerpowers T3 |
| `research` | parked | T3 的"查证型"只是条目分类标签、非 skill 调用；能力上另有 `deep-research` |
| `prototype` | parked | 同上，T3 的"原型型"是条目分类标签 |
| `setup-matt-pocock-skills` | parked | 唯一用途是给仓库配 issue tracker，随 wayfinder 一同失去场景 |

**`ownerpowers` T3 的条目四型改用中文标签**（拷问型 / 查证型 / 原型型 / 前置型），不再沿用 `research` / `prototype` 这类与 skill 同名的写法——避免读到剧本时误以为要去调用一个已 parked 的 skill。四型中只有拷问型对应真实 skill 调用（`grilling`）。

## 后果

**正面**：全局挂载 19 → 15，回到引入 mattpocock 族之前的水平，等于本轮净新增的常驻预算只有 `domain-modeling` 一项。T3 剧本内部再无指向未挂载 skill 的引用。

**取舍**：`prototype` 的内容（一次性代码六条规则、LOGIC/UI 双分支）本身通用且质量不错，parked 是场景判断而非质量判断。四项都是改一行 `tier` 即可复活，真身在仓内完整保留。
