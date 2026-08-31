# 溯源线索（community · mattpocock）

- **upstream**: https://github.com/mattpocock/skills
- **credit**: Matt Pocock（aihero.dev）
- **license**: MIT（Copyright (c) 2026 Matt Pocock）
- **本地 clone**: `~/Library/CodeRepo/AI/skills`（origin = `mattpocock/skills`），同步前先在该 clone `git pull`
- **同步基线**: 上游 commit `8b36d4f`（2026-08-06 拉取，仅为取 `teach` 而 pull；其余 7 项未随此次上游变更重新核对，勿误当整族已同步）
- **进入路径**: 按需节选，非完整镜像；本桶只放 mattpocock 上游的 skill

## 本桶内容与上游原路径

| 本地 | 上游路径 |
|---|---|
| `grilling` | `skills/productivity/grilling` |
| `grill-me` | `skills/productivity/grill-me` |
| `grill-with-docs` | `skills/engineering/grill-with-docs` |
| `wayfinder` | `skills/engineering/wayfinder` |
| `domain-modeling` | `skills/engineering/domain-modeling` |
| `research` | `skills/engineering/research` |
| `prototype` | `skills/engineering/prototype` |
| `setup-matt-pocock-skills` | `skills/engineering/setup-matt-pocock-skills` |
| `teach` | `skills/productivity/teach` |

全部与上游逐字一致（`agents/openai.yaml` 一并保留），未做本地改写。

## 上游内部依赖

同步时须整族一起看，单独更新会断链：

```
wayfinder ──→ grilling · domain-modeling · research · prototype
          └─→ setup-matt-pocock-skills（配 issue tracker，未配则退化到本地 markdown tracker）
grill-with-docs ──→ grilling · domain-modeling
grill-me ──────────→ grilling
teach ────────────→（无族内依赖，独立跨会话教学工作区）
```

`ADR-FORMAT.md` / `CONTEXT-FORMAT.md` 归 `domain-modeling`——上游曾放在 `grill-with-docs` 下，
后者现已瘦成两行委派，同步时勿把这两份文件留在 `grill-with-docs`。
