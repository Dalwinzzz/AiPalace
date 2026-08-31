# ADR-0007：SessionStart hook 重写——以 AiPalace INDEX 注入取代 dalwin-workflow domain-context，双工具单一受管源

- 状态：已接受
- 日期：2026-06-25
- 决策人：dalwin
- 关联：落实 [final-spec 阶段 3](../docs/superpowers/specs/2026-06-25-final-spec-SOT指向切换.md)；延续 [ADR-0001](0001-AiPalace为个人AI-harness唯一SOT.md)（AiPalace 唯一 SOT）；前置 P3 已建 `tools/hooks/inject_index.py`、`context/INDEX.md`、`context/memory/INDEX.md`

## 背景

现役 SessionStart 注入由**两个独立副本**承担：`~/.claude/hooks/sessionstart-domain.py`、`~/.codex/hooks/sessionstart-domain.py`。二者：

- `CONTEXT_BASE = ~/.agents/context`（经两跳软链最终指向 **dalwin-workflow**）；
- Claude 版含 `DOMAIN_CONTEXT` 字典，把工作域映射到**旧扁平 memory 路径**（`memory/projects/syzh.md`、`memory/ai-workflow.md`、`memory/glossary.md`、`memory/projects/go-transition.md`）；
- Codex 版只出 pack（技能建议），无 context 指针；
- 两份 cwd 域打分逻辑近乎重复，pack 成员各自维护、易漂移。

而 AiPalace 侧 P3 已建成：三级 5 域 memory（`projects/enterprise/tech/workflow/reference`）、`context/INDEX.md`（self/* 决策树）、`context/memory/INDEX.md`（**已含"门 cwd 打分"+ 5 域完整决策树 + 准入条件**）、`tools/hooks/inject_index.py`（INDEX 拼接注入器，双工具通用，尚未注册到现役）。

旧 `DOMAIN_CONTEXT` 的"域→单个扁平 memory 文件"路由，已被 `memory/INDEX.md` 的"5 域决策树（多门并集 + 细粒度条目 + 准入把关）"在能力上完全覆盖且更强。

## 决策

1. **单一受管源**：新建 `AiPalace/tools/hooks/sessionstart.py`，**合并** cwd 域打分（门 a）+ INDEX 注入两件事；**双工具共用**（Claude 与 Codex 的 SessionStart 均约定 `hookSpecificOutput.additionalContext`，输出格式一致）。复用 `inject_index.py` 的 INDEX 读取（不重复实现）。
2. **以 INDEX 注入取代 DOMAIN_CONTEXT**：移除旧"域→扁平 memory 文件"指针；SessionStart 输出 = `[工作域] 打分 + pack` ＋ always-on 注入 `context/INDEX.md` + `context/memory/INDEX.md`。后者承载 5 域决策树与按需拉取规则（P3 渐进披露），**supersede** 旧 domain-context 机制。
3. **context root 稳健解析**（兼容软链派生）：`AIPALACE_CONTEXT` 环境变量 → `realpath(__file__)` 上溯派生 → 硬编码 `~/Library/CodeRepo/AI/AiPalace/context` 兜底。三级回退确保副本/软链/异常 cwd 下都能定位。
4. **派生形态 = 软链，零注册改动**：现役 `~/.claude/hooks/sessionstart-domain.py`、`~/.codex/hooks/sessionstart-domain.py` 由真实副本**替换为软链 → 受管源**；`settings.json` / `hooks.json` 的 SessionStart 注册路径不变（仍 `python3 .../sessionstart-domain.py`）。脚本经 `realpath` 解回 AiPalace。
5. **保留 cwd 域打分 + pack，并补 AiPalace 域信号**：打分逻辑沿用现役（java/spring、ai_build、knowledge、learning 四域）；新增 `cwd 含 AiPalace → ai_build` 信号（令本仓库工作被识别为 AI 构建域）。pack 成员统一为一套（取 Claude 版较全集合）。

## 后果

**正面**：单源 DRY、双工具同逻辑（呼应治理 README"SessionStart 双工具同逻辑"）、INDEX 渐进披露落地、现役 dalwin-workflow 引用清零、零 `settings.json` 改动（降风险）。

**取舍 / 待观察**：
- always-on 注入 `INDEX.md` + `memory/INDEX.md`（约 125 行）增加每会话 token 成本——可接受（这是 P3 渐进披露的设计本意，细节仍按需 Read）。
- 软链派生依赖 `realpath(__file__)` 正确解析；已加 env + 硬编码兜底降风险。
- pack 成员沿用旧集合，个别名（如部分 superpowers/插件 skill）仅作文本提示，不保证都在当前挂载集——属提示性信息，低危，后续可按 registry 校正。

> 旧两份 `sessionstart-domain.py` 的逻辑记录不删改（备份留存于 `~/sot-switch-backup-*`），本 ADR 确立新机制取而代之。
