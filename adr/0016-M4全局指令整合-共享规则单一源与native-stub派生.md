# ADR-0016 · M4 全局指令整合：共享规则单一源 + native stub 软链派生

- 状态：Accepted
- 日期：2026-07-03
- 承继：ADR-0013（登记 M4 待决项）、ADR-0014（always-on 瘦身，本 ADR 定义豁免边界）
- 关联 spec：`docs/superpowers/specs/2026-07-03-M4全局指令整合-design.md`（D1–D8）

## 背景

`~/.claude/CLAUDE.md` 与 `~/.codex/AGENTS.md` 平行维护全量全局指令：共享内容双侧重复、改一处易漏另一处；文件在仓外不可版本化、双机不可同步——ADR-0013 登记的最后一个 P9 待决项。

## 决策

1. **共享规则单一源**：工具无关规则（个人偏好/Context7/指令文件维护/ConfigFile 审慎/dbq 只读通道/superpowers ask-first/跨工具 skill SOT/AiPalace 治理）收敛至 `vault/memory/00-RULES/operating-rules.md`；dbq 随规则进共享层，Codex 同获（用户拍板）。
2. **注入**：既有机制 A 扩展——`inject_index` 默认 files=`("00-RULES/operating-rules.md", "INDEX.md")`（法律在前、导航在后），双工具入口同源生效。
3. **native stub 入仓派生**：`context/native/{claude-global,codex-global}.md` 为真源，`~/.claude/CLAUDE.md`、`~/.codex/AGENTS.md` 改软链（同 commands 模式）；stub 只留工具专属规则（superpowers 注入前言/ConfigFile 第一道防线实现/Codex Workflow Memory Boundary）+ 兜底指针（未见 `[操作规则]` 注入块则手读 vault 绝对路径）。
4. **always-on 豁免边界**：operating-rules.md 是 ADR-0014 后 00-RULES 第二个获准 always-on 项。豁免理由：内容原本即经 native 文件 always-on，本次只换源+去双侧重复，净 token ≈ 持平或下降；此后再增 always-on 项仍须新 ADR。
5. 原件快照存档 `docs/archive/native-globals-2026-07-03/`（P8）；本地另有 `.bak-m4` 副本，回滚 = 删软链恢复原件 + 还原 inject 默认元组。

## 后果

- 全局指令改一处即双工具生效；全局配置入 git，双机同步（Windows 侧软链仍属 evolution §6.1 既有待决）。
- hook 成为共享规则唯一注入通道（stub 兜底指针缓解单点）；native 文件不再承载共享内容。

## 验证（P5 实测门）

- 软链后 `cat ~/.claude/CLAUDE.md`、`cat ~/.codex/AGENTS.md` 读出 stub；新会话见 `[操作规则]` + INDEX 双块有序无重复。
- hooks 16 例 + pytest 33 例 + memory 26 例全绿；doctor 无漂移。
- Codex 侧交互实测与 M5 收尾验证合并执行，结论回填本 ADR 验证节。
