# SOT 切换执行 Ledger

> 配套 [final-spec](2026-06-25-final-spec-SOT指向切换.md) 的逐阶段执行记录。中断后凭此恢复。
> 分支：`sot-switch-execution`。备份：见下。

## 备份位置（回滚依据）

- `~/Library/ConfigFile/claude/sot-switch-backup-20260625-182958/`（2026-06-25 归档至 ConfigFile 统一备份区；原在 `~/`）
  - `symlinks-before.txt` —— 全部现役软链原始指向（重建依据）
  - `dirs.tgz` —— `.claude/skills .claude/rules .agents/{context,skills,plugins} .codex/skills`（软链存软链，不跟随）
  - `claude/` —— hooks/ + wrap.md + settings.json + settings.local.json + CLAUDE.md
  - `codex/` —— AGENTS.md + hooks.json + hooks/

## 决策（用户本会话拍板）

- 执行到**阶段 5**（hook 重写走完整 ADR+plan+TDD）。
- `gemini-svg-creator`(Claude)、`req-to-ai-spec`(Codex) **视为有意下线**，不补登记。
- `hatch-pet`（Codex 真实目录）保护不删；`ai-pdf-builder`（已断链）丢弃。
- flat_mirror 暂保持 registry 现状（注释/禁用），`~/.agents/skills` 旧软链留待 reconciliation #1 实测后处理。

## 进度

- [x] **阶段 0 · 全量备份** —— done 2026-06-25 18:29。tar 213 项可解，软链指向记全。
- [x] **阶段 1 · skill 挂载切换** —— done 2026-06-25 18:32。
  - 删旧手建软链（claude 13 / codex 6，真实目录 hatch-pet/.system 受保护）。
  - `sync`：`~/.claude/skills` 与 `~/.codex/skills` 各 12 受管软链 → AiPalace 规范路径。
  - `mount zhijin`：`~/Library/IdeaProject/ZhiJin/.claude/skills` 挂 4 project skill（ownerpowers/biz-workflow/spec-architect/liquibase）。
  - `doctor` 26 skill 全绿无漂移；skill 软链零 dalwin-workflow/awesome-skills。
  - 本会话实时生效：`/` 菜单新增 grilling/html-diagram/skill-management/codex-image-gen。
- [x] **阶段 2 · rules/context 软链切换** —— done 2026-06-25 18:35（结构层）。
  - 重指第二跳：`~/.agents/context/{java-spring,frontend-web}.md` → `AiPalace/context/rules/<同名>`（第一跳 `~/.claude/rules/` 形态不变）。
  - 两跳链路解析终点 = AiPalace、可读。
  - ⏳ 行为级验证（Java 项目新 session 自动注入）待新 session 实测。
  - `~/.agents/context/memory` 仍指 dalwin-workflow → 阶段 3 处理。
- [x] **阶段 3 · memory + SessionStart hook 重写** —— done 2026-06-25 18:42（ADR + TDD）。
  - [ADR-0007](../../../adr/0007-SessionStart-hook以AiPalace-INDEX注入取代domain-context.md)：以 AiPalace INDEX 注入取代 domain-context，双工具单一受管源。
  - TDD：`tools/hooks/sessionstart.py`（合并 cwd 域打分 + INDEX 注入）+ `test_sessionstart.py`（11 测试，`-W error::ResourceWarning` 全绿）；顺手修 `inject_index.py` 未关文件告警。
  - 派生：`~/.claude/hooks/sessionstart-domain.py`、`~/.codex/hooks/sessionstart-domain.py` 改软链 → 受管源（注册路径不变，realpath 解回 AiPalace）。
  - memory 重指：`~/.agents/context/memory` → `AiPalace/context/memory`；INDEX 引用的 12 个 memory 文件全部存在、软链可读。
  - Codex `precompact-memory-hint.py` 文本 dalwin-workflow → AiPalace。
  - 验证：软链零 dalwin-workflow；ai_build 新信号生效（AiPalace cwd=0.60）。
  - ⏳ 行为级（新 session SessionStart 实注入、ZhiJin 项目导向 enterprise/zhijin）待新 session 实测。
- [x] **阶段 4 · /wrap + Codex 文本** —— done 2026-06-25 18:48（plugins 降级待决项）。
  - `/wrap` 纳入受管：新建 `AiPalace/commands/wrap.md`（重写为三级 5 域路由、SOT/提交目标→AiPalace、step4 改更新 INDEX 而非 hook DOMAIN_CONTEXT），`~/.claude/commands/wrap.md` 软链派生；本会话 skill 列表已实时刷新为"AiPalace context"。
  - Codex `~/.codex/AGENTS.md`：修过时的 skill SOT 表述（→ AiPalace registry 派生）+ 补 Harness Governance 指针（PHILOSOPHY/governance）。
  - ⚠️ **plugins 降级为待决项**（后经 [ADR-0008](../../../adr/0008-双工具plugins切到AiPalace并改Codex约定布局.md) 解决）：实测发现三处分叉（Claude marketplace 指 `~/Library/CodeRepo/AI/claude-plugins`、`~/.agents/plugins` 是 diverge 的 Codex 版、Codex 另有 cache），plugins 零 dalwin-workflow 不阻塞退役，按 P6 不蛮干。
  - ⏳ 行为级（实跑 /wrap 落 AiPalace 并提交）待真实 wrap 会话验证。
- [x] **阶段 5 · dalwin-workflow 退役** —— done 2026-06-25 18:52。
  - 全局复扫：现役**软链 0 / 活配置 0** 命中 dalwin-workflow（剩余命中仅 `file-history/`、`paste-cache/`、`.codex-global-state.json` 的 prompt-history、各 `.jsonl` —— 均属历史/缓存/transcript，按原则不改写）。
  - 清 `~/.claude/settings.local.json` 两条 dalwin-workflow mkdir 权限项（JSON-safe，合法）。
  - `~/Documents/AI/dalwin-workflow/README.md` 加退役横幅并在其仓提交（6b12038）。

## 验收（spec §4，2026-06-25 18:52）

| 项 | 结果 |
|----|------|
| ① 现役 dalwin-workflow 零引用 | ✅ 软链 0 / 活配置 0 |
| ② Claude：skill 来自 AiPalace / rules 自动注入 / SessionStart 注 INDEX / wrap 落 AiPalace | ✅ 结构全验；hook 实跑 Java cwd→`java/spring=0.70`+INDEX；本会话实时见证 skill 列表+wrap 描述刷新；⏳ 真·新 session 体感待下次开会话 |
| ③ Codex：skill 可发现 / AGENTS 指向 AiPalace | ✅ `~/.codex/skills` 12 受管软链 + hook 软链派生 + AGENTS 更新；⏳ Codex 实测发现路径（reconciliation #1）待 Codex 会话 |
| ④ AiPalace doctor 全绿 | ✅ 26 skill 无漂移 |
| TDD 回归 | ✅ 11 测试（`-W error`）全绿 |

## 遗留待决项（P9，后续均由各 ADR 接管）

- ⚠️ plugins SOT 切换（三处分叉，单独任务）。
- ⚠️ commands 受管治理文档（`docs/governance/product-assets/commands.md`）。
- ⏳ reconciliation #1（Codex 实际发现路径）/ #2（hook 整合形态已落地为单源，待 Codex 实测确认注入生效）。
- ⏳ 行为级验证：新 Claude/Codex/ZhiJin 项目/Java 项目会话实跑（结构已全绿，待真实会话体感）。
