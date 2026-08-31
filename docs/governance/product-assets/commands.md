# commands.md — 斜杠命令机制规范

> 关联哲学：[P2 声明式管理工具派生](../../../PHILOSOPHY.md#p2--声明式管理工具派生限内容资产)、[P7 机制分治](../../../PHILOSOPHY.md#p7--内容统一源机制分治)。

---

## 定位

命令（command）是工具原生的**斜杠命令**——`~/.claude/commands/*.md` 等，由工具在 `/` 菜单暴露、用户显式调用。属**产品资产**：与工具形态耦合，遵循 P7 机制分治。

---

## 受管派生（P2）

命令真源在 `AiPalace/commands/<name>.md`；派生到工具挂载点为**软链**：

```
~/.claude/commands/<name>.md  →  AiPalace/commands/<name>.md
```

改真源即改命令；**禁止手碰派生软链**。新增命令需建派生软链 `ln -s <AiPalace>/commands/<name>.md ~/.claude/commands/<name>.md`。

---

## commands vs skills 边界

| 维度 | command（斜杠命令） | skill |
|------|--------------------|-------|
| 触发 | 用户显式 `/<name>` | 模型据 description 自动判断 + 用户可调 |
| 形态 | 单 md（frontmatter `description` + 步骤指令） | `SKILL.md` + 可带 references / scripts / assets |
| 注册 | 工具原生 commands 目录（软链派生，本规范） | `registry.yaml` → `skillctl` 派生 |
| 适用 | 固定流程、用户主动触发的 SOP | 可复用能力、需模型自主触发的方法论 |

> 判断：纯用户触发的固定流程 → command；需模型自动识别场景触发、或带配套资源的能力 → skill。

---

## 现有命令

| 命令 | 真源 | 派生(Claude) | 派生(Codex) |
|------|------|---------------|--------------|
| ~~`/wrap`~~ | —— | —— | **已退役**(ADR-0021,M5-C 执行完毕;能力由 `/ai-palace` 承接) |
| `/ai-palace` | [`commands/ai-palace.md`](../../../commands/ai-palace.md) | `~/.claude/commands/ai-palace.md` | `~/.codex/prompts/ai-palace.md` |

> Codex 侧机制:`~/.codex/prompts/*.md` 即自定义斜杠命令(custom prompts),按 P7 各自派生、内容求同源。

---

## 维护

1. 改 `AiPalace/commands/<name>.md`（真源）。
2. 命令内容若含 how-to 细节，遵循[指令文件渐进披露约定](../../../context/howto/instruction-file-maintenance.md)：主体留步骤指令，繁复细节移 `context/howto/`。
3. 变更经 git 追溯（P8）。
