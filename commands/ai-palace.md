---
description: 沉淀本会话到 vault 记忆层并驱动手动飞轮(capture→distill→审批→promote);/wrap 升级版
---

# /ai-palace

评估本会话已验证的新事实,经**手动飞轮**沉淀到 `AiPalace/vault/memory/`。

- **SOT**:`~/Library/CodeRepo/AI/AiPalace/vault/memory/`(五层结构见 `INDEX.md`;读写契约先读 `PROTOCOL.md`)
- **内核**:`tools/memory/{core,promote}.py`(确定性打分/把门/写盘;参数见 `tools/memory/config.toml`;详见 `tools/memory/README.md`)
- **铁律**:你(agent)只做**抽候选 + 提议 type/scope/dest**;六维分数只能来自脚本输出,**禁止自估分数**;是否晋升由 gate + 用户审批决定
- **本命令受管**:真源 `AiPalace/commands/ai-palace.md`;`~/.claude/commands/` 与 `~/.codex/prompts/` 均为软链派生,勿手碰

## 模式

- `/ai-palace` —— 默认:沉淀**本会话**(下方步骤 1–7)。
- `/ai-palace sweep` —— 补漏:先跑
  `python3 ~/Library/CodeRepo/AI/AiPalace/tools/memory/gather_sessions.py --commit-ledger`
  拿到漏网会话的 user 发言 blob,从 blob 抽候选(**忽略本 sweep 会话自身的内容**;
  journal 行 source 写 `sweep:claude` / `sweep:codex`),之后走同样的步骤 2–7。
  blob 为空则输出「没有新的漏网会话」结束。

## 步骤

### 1. 复盘会话,抽候选

从本会话抽**已验证、可复用**的事实,分三组:

- **vault 候选**(走飞轮):纠正 / 决策 / 偏好 → 按下列路由判断(公司项目→`01-PROJECTS/enterprise/<公司>/<模块>.md`;个人项目→`01-PROJECTS/projects/`;技术深度→`01-PROJECTS/tech/`;工作流→`01-PROJECTS/workflow/ai-workflow.md`;术语→`01-PROJECTS/reference/glossary.md`;自我画像→`00-RULES/`)逐条提议 `type/scope/dest`;拿不准的记「观察」(只留底不进候选)
- **工程规则**(直写旁路,不过飞轮):域级编码/构建约定 → 直接合并写 `context/rules/<域>.md`;新域需 `paths:` frontmatter + 两跳 symlink(`~/.agents/context/<域>.md → AiPalace/context/rules/<域>.md`,`~/.claude/rules/<域>.md → ~/.agents/context/<域>.md`)
- **不沉淀**:本次任务特有细节、一次性指令

红线:凭证/秘钥**绝不落 journal**(用 `$secret:NAME` 名称引用);enterprise 事实仅在 cwd ∈ ZhiJin 工程或任务明确涉及该公司时落库。

### 2. 写 journal(append-only)

追加到 `vault/memory/04-FEEDBACK/journal/<今日 YYYY-MM-DD>.md`(不存在则先建,frontmatter:title=Journal <日期>、type=journal、scope=global、status=active、confidence=high、created/updated/last_confirmed=<日期>、source=[ai-palace capture]),每条一行:

    - 决策: <一句话> <!--sig {"type":"decision","scope":"project:enterprise/zhijin","dest":"01-PROJECTS/enterprise/zhijin/skc-activity.md","source":"claude"}-->

- 前缀 ∈ {偏好/决策/纠正/观察};`source` = `claude` 或 `codex`(当前工具)
- 同一事实早前已写过 journal 的不重写(靠 distill merge 累积 freq)

### 3. 蒸馏(确定性)

    python3 ~/Library/CodeRepo/AI/AiPalace/tools/memory/core.py distill

把输出的候选表(六维/证据/dest)原样呈现给用户。无达标候选 → 如实说明「均暂缓(freq/分数不足,DREAMS 已留痕)」,跳到步骤 6。

### 4. 用户审批

征询用户:批哪几条、dest 要不要改。按答复把 `candidates.md` 对应行勾成 `[x]`(要改 dest 的先改行内 JSON 的 dest);用户否决要删的行,删除并在 DREAMS 手动补一行否决留痕。

### 5. 晋升(确定性)

    python3 ~/Library/CodeRepo/AI/AiPalace/tools/memory/promote.py

- 有「新建 …(记得给 INDEX 决策树接线)」输出 → 给 `vault/memory/INDEX.md` 决策树补一条(触发关键词 + 相对路径)
- 晋升进 00-RULES 暂存段的,提醒用户事后把「蒸馏晋升(待归位)」条目手动归位进规则结构

### 6. 提交

只暂存本次动过的具体文件(**禁止 add -A**):

    git -C ~/Library/CodeRepo/AI/AiPalace add vault/memory/ context/rules/<改过的域>.md
    git -C ~/Library/CodeRepo/AI/AiPalace commit -m "context(ai-palace): <一句话摘要>"

### 7. 输出

    ✅ 飞轮完毕:journal +N 行 / 晋升 M 条 / 暂缓 K 条(DREAMS 留痕),可执行 /clear

如无任何候选:`本次会话无新沉淀候选;可执行 /clear`
