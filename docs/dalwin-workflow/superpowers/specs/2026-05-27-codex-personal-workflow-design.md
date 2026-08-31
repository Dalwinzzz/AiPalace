# Codex 个人工作流设计 spec — 2026-05-27

> 范围：在已完成的 Claude 个人工作流基础上，为 Codex / Codex CLI 建立一套 Codex-native 的配置、skills、MCP、hooks、memory 对账方案。
>
> 决策：采用 **方案 2 + 方案 3**。即“Codex + Claude 双工具对账”作为长期架构，同时把当前 Codex 漂移项作为 Phase 0 先修复。

---

## 1. 背景与目标

### 1.1 现有 Claude 侧基线

Claude 版个人工作流已经完成 design、plan 和三阶段实施，核心包括：

- memory seed：用户画像、工作流偏好、SaaS 项目路径、Maven 配置、skills SOT、跨工具 memory 对账。
- hooks：`SessionStart` 工作域识别、`PreCompact` memory 候选提示、`/wrap` 清理前补偿。
- skills SOT：`~/Library/CodeRepo/AI/` 作为唯一源，`~/.agents/skills` 和 `~/.claude/skills` 做软链视图。
- 哲学：少而精，规则只落在一个权威位置，避免重复占用上下文窗口。

这些目标继续适用，但 Claude 的实现原语不能原样搬到 Codex。

### 1.2 当前 Codex 侧状态

本机状态：

- Codex CLI：`0.130.0`
- 全局指令：`~/.codex/AGENTS.md`
- 主配置：`~/.codex/config.toml`
- hooks：`~/.codex/hooks.json`
- rules：`~/.codex/rules/`
- memories：`~/.codex/memories/`
- skills：`~/.codex/skills/`

发现的漂移：

- `codex mcp list` 当前只有 `node_repl`，没有 `context7`；但 `~/.codex/AGENTS.md` 已写入 Context7 使用规则，规则和实际工具状态不一致。
- `~/.codex/config.toml` 当前使用 `features.codex_hooks = true`，Codex feature list 中 `hooks` 是 stable，`codex_hooks` 已不是主推荐名。
- `~/.codex/skills/git-merge-conductor` 仍指向 `/Users/dalwin/Documents/AI/skills/git-merge-conductor` 旧路径，而 `~/.agents/skills/git-merge-conductor` 已迁到 SOT：`/Users/dalwin/Library/CodeRepo/AI/awesome-skills/git-merge-conductor`。
- `~/.codex/skills/req-to-ai-spec` 是 Codex 私有实目录，但 SOT 里也存在 `awesome-skills/req-to-ai-spec`，需要 diff 后决定是否改为软链。
- Codex memories 功能当前未启用；即便启用，也不能替代 `AGENTS.md` 或 repo-local docs 作为强规则源。

### 1.3 目标

1. 让 Codex 和 Claude 共享同一套工作流意图，但分别使用各自官方支持的配置面。
2. 修复当前 Codex 漂移：MCP、hooks feature、skills 软链、重复 skill 源。
3. 建立 Codex 侧 memory / hooks / AGENTS / rules 的职责边界，避免“什么都塞进全局指令”。
4. 形成可执行计划，后续可按阶段验证、回滚、提交实施日志。

---

## 2. 官方约束与映射原则

Codex 侧采用 OpenAI 官方机制为边界。

| 能力 | Codex 官方定位 | 本设计用法 |
|---|---|---|
| `AGENTS.md` | Codex 会读取全局和项目级指令文件，并按目录层级合并 | 只放每次都值得携带的稳定协议 |
| `config.toml` | Codex CLI、IDE extension、desktop app 共享的用户配置层 | 模型、features、MCP、项目 trust、桌面偏好 |
| hooks | Codex 支持事件驱动 hooks，当前本机 feature list 中 `hooks` 为 stable | 用于轻量上下文提示、通知桥、非阻塞记录 |
| memories | 默认关闭，适合本地偏好召回；官方建议强规则仍放 `AGENTS.md` 或受版本控制文档 | 作为辅助召回，不承载硬约束 |
| skills | 通过 `SKILL.md` description 触发，初始 skill 列表会占上下文预算 | 只挂高价值技能；长尾放 SOT 但不全挂 |
| MCP | 通过 `codex mcp add` 注册 stdio 或 HTTP server | 恢复 Context7，补 OpenAI Developer Docs |
| rules | 控制哪些命令可在 sandbox 外运行 | 只做执行审批，不做行为规范 |

官方参考：

- Codex config basics: https://developers.openai.com/codex/config-basic
- AGENTS.md: https://developers.openai.com/codex/guides/agents-md
- Hooks: https://developers.openai.com/codex/hooks
- Memories: https://developers.openai.com/codex/memories
- Agent Skills: https://developers.openai.com/codex/skills
- MCP: https://developers.openai.com/codex/mcp
- Rules: https://developers.openai.com/codex/rules

设计原则：

- **意图共享，原语分离**：Claude 的 memory/hook/slash-command 思路只翻译工作流意图，不照搬实现。
- **强规则落 AGENTS 或 Git hook**：必须可靠生效的行为约束不放 memories。
- **动态上下文落 hooks/memories**：工作域识别、会话总结、候选事实等可以用 hooks/memories 辅助。
- **权限审批归 rules**：`rules/` 不再承载 commit message、文档查询等模型行为规范。

---

## 3. Codex 侧整体架构

### 3.1 控制面分层

```
~/Library/CodeRepo/AI/                 # skills 源码 SOT
  ├── awesome-skills/
  ├── superpowers/
  └── skills/

~/.agents/skills/                      # 跨工具共享 registry
  └── {name} -> SOT

~/.codex/skills/                       # Codex 可见 skills 视图
  └── {selected-name} -> ~/.agents/skills/{name} 或 SOT

~/.codex/
  ├── AGENTS.md                        # 稳定全局协议
  ├── config.toml                      # features/MCP/projects/plugins
  ├── hooks.json                       # Codex hook 事件绑定
  ├── hooks/                           # Codex hook 脚本
  ├── memories/                        # 可选辅助召回
  └── rules/                           # sandbox 外命令审批
```

### 3.2 双工具职责矩阵

| 工作流意图 | Claude 落点 | Codex 落点 | 说明 |
|---|---|---|---|
| 中文、结构化思考、客观挑战 | `~/.claude/CLAUDE.md` | `~/.codex/AGENTS.md` | 稳定全局协议 |
| Context7 文档查询 | `~/.claude/CLAUDE.md` + MCP | `~/.codex/AGENTS.md` + MCP | Codex 当前缺 MCP，需修复 |
| Git commit message | Claude PreToolUse + Git hook | Git hook + Codex `AGENTS.md` 简短规则 | rules 只做审批 |
| Java/SaaS 项目记忆 | Claude memory files | Codex memories 辅助 + AGENTS 简短索引 | 不把大块项目事实塞 AGENTS |
| 工作域识别 | Claude `SessionStart` hook | Codex `SessionStart` hook | 输出短索引，不 dump skill 描述 |
| 压缩前 memory 评估 | Claude `PreCompact` hint + `/wrap` | Codex `PreCompact` 可选 hint/日志 | Codex 不依赖它保证写入 |
| skills 来源 | SOT + `~/.agents` + `~/.claude` | SOT + `~/.agents` + `~/.codex` | 统一软链策略 |

---

## 4. Phase 0：当前漂移修复

Phase 0 不改变工作流哲学，只修复“配置已声明但能力缺失”的问题。

### 4.1 MCP 恢复

目标：

- 恢复 `context7`：
  `codex mcp add context7 -- npx -y @upstash/context7-mcp`
- 安装 OpenAI Developer Docs MCP：
  `codex mcp add openaiDeveloperDocs --url https://developers.openai.com/mcp`
- 验证：
  - `codex mcp list`
  - `codex mcp get context7`
  - `codex mcp get openaiDeveloperDocs`

设计理由：

- 当前 `AGENTS.md` 要求查询库/API/CLI 文档时使用 Context7，但 MCP 实际不存在，这是最优先漂移。
- 本任务后续会频繁依赖 OpenAI 官方 Codex 文档，OpenAI Docs MCP 应作为 Codex 侧标准能力。

### 4.2 Feature key 归一

目标：

- 将 `features.codex_hooks = true` 调整为 `features.hooks = true`。
- 保留其他 feature，不扩大实验功能。

设计理由：

- 本机 `codex features list` 中 `hooks` 是 stable；`codex_hooks` 不是当前稳定主名。
- 避免以后版本去掉兼容别名导致 hooks 无声失效。

### 4.3 Skills symlink 修复

目标：

- `~/.codex/skills/git-merge-conductor` 改指向 SOT：
  `/Users/dalwin/Library/CodeRepo/AI/awesome-skills/git-merge-conductor`
- `~/.codex/skills/spec-architect` 已指向 SOT，保留。
- `~/.codex/skills/docker-best-practices` 已指向 SOT，保留。
- `~/.codex/skills/req-to-ai-spec` 与 SOT 版本 diff；若 SOT 更新或一致，则改为 SOT symlink；若 Codex 私有版本有差异，先记录差异再决定。
- `~/.codex/skills/hatch-pet` 暂视为 Codex 私有技能，先保留实目录。

设计理由：

- 共享技能应由 `~/Library/CodeRepo/AI/` 单源维护，Codex/Claude 都通过软链加载。
- 不直接批量替换所有 Codex skills，避免破坏 Codex 专属技能。

---

## 5. AGENTS 策略

### 5.1 保留内容

`~/.codex/AGENTS.md` 保留以下稳定协议：

- Structured Thinking
- Objective Peer
- Default Language: Chinese Simplified
- Context7 MCP Usage

### 5.2 新增内容

建议新增短规则：

```text
Workflow Memory Boundary: Treat AGENTS.md as the source for stable, always-on behavior. Use memories and hooks only as auxiliary recall or context hints. Do not rely on memories for hard requirements that must always apply.

Cross-Tool Skill Source: Shared skills should resolve to /Users/dalwin/Library/CodeRepo/AI as the source of truth, usually through /Users/dalwin/.agents/skills. Prefer fixing symlinks over copying skill directories.
```

Git commit message 规则不再扩写大段进入 AGENTS；只保留“如果创建 commit，遵守本机 Git hook 和既有 commit convention”的短句即可。硬校验仍由 Git hook 实现。

### 5.3 不放入 AGENTS 的内容

- 15 条 memory seed 全文。
- 工作域 pack 列表全文。
- Maven 配置全文。
- 详细 skill 创建门槛。
- 每个项目的长路径表。

这些内容应放在 Codex memories、repo-local docs、skills 自身，或 hook 动态提示中。

---

## 6. Hooks 策略

### 6.1 保留 codeisland 通知桥

现有 `~/.codex/hooks.json` 中所有 codeisland bridge hook 保留：

- `PreToolUse`
- `PostToolUse`
- `SessionStart`
- `SessionEnd`
- `Stop`
- `UserPromptSubmit`

新增 hook 时只追加，不覆盖。

### 6.2 新增 `sessionstart-domain`

目标：

- 在 `SessionStart` 输出短工作域索引。
- 复用 Claude 版权重模型，但适配 Codex hook 输入输出。
- 控制在约 50-120 tokens，不 dump skill 描述。

输出示例：

```text
[工作域] java/spring=0.90; pack-java: spec-architect, git-merge-conductor, requesting-code-review
```

职责：

- 只提示，不强制。
- 只输出高置信度域；低于阈值不出现。
- 让模型自行决定是否使用对应 skills。

### 6.3 新增 `userprompt-workflow-router`

目标：

- 在 `UserPromptSubmit` 观察用户输入中的工作流关键词，如“spec / plan / review / commit / memory / skill”。
- 必要时注入一行短提示，提醒选择合适 skill 或规则边界。

示例：

```text
[工作流提示] 用户请求涉及 spec/plan；优先考虑 spec-architect 或 superpowers:brainstorming → writing-plans。
```

设计理由：

- Codex skills 已有 description 触发，但 UserPromptSubmit hook 可作为低成本兜底。
- 只提示，不阻断，避免变成隐性全局强规则。

### 6.4 PreCompact 降级处理

Codex 侧不把 PreCompact 当作 memory 写入保证。

可选策略：

- 输出一行非阻塞提示：本轮如产生稳定事实，结束前可写入 memories 或 dalwin-workflow docs。
- 或只写本地日志，供后续人工对账。

不做：

- 不在 PreCompact 中执行网络访问。
- 不做长时间 I/O。
- 不把 PreCompact 失败视为工作流失败。

---

## 7. Memories 策略

### 7.1 启用但降权

建议启用：

```toml
[features]
memories = true
```

但明确降权：

- memories 只用于“想起来”，不用于“必须遵守”。
- 稳定强规则仍在 `AGENTS.md`、Git hook、repo docs、skills 中。
- memories 中的事实要短、小、可对账。

### 7.2 Codex memory 初始内容

Codex 侧不复制 Claude 11 个 memory 文件全文，而是写一个短索引：

- 用户角色与工作分布摘要。
- SaaS 关键仓库路径摘要。
- Maven 配置摘要。
- skills SOT 摘要。
- Claude memory 位置和对账要求。

### 7.3 对账规则

当发现跨工具稳定事实不一致：

1. 先判断权威源。
2. 若是长期偏好或项目事实，更新 `dalwin-workflow` 文档或两侧 memory。
3. 若是强行为规则，更新 `AGENTS.md` / `CLAUDE.md` / Git hook / skill，而不是只写 memory。
4. 实施日志写入 `dalwin-workflow/docs/superpowers/plans/logs/`。

---

## 8. Skills 策略

### 8.1 Codex 可见 skills 分层

Codex 初始 skills 列表会占上下文预算，因此只挂高频或 Codex 专属：

内圈/高频：

- `spec-architect`
- `git-merge-conductor`
- `docker-best-practices`
- `req-to-ai-spec`
- `hatch-pet`
- system skills：`openai-docs`、`skill-installer`、`skill-creator` 等保留

通过 `~/.agents/skills` 暴露但不一定全部挂到 `~/.codex/skills`：

- `ai-pdf-builder`
- `deep-research`
- `docx`
- `wiki-creator`
- `skill-security-audit`
- `gemini-svg-creator`
- 其他长尾

### 8.2 SOT 规则

共享技能路径：

```text
/Users/dalwin/Library/CodeRepo/AI/awesome-skills/{name}
```

注册视图：

```text
/Users/dalwin/.agents/skills/{name} -> SOT
/Users/dalwin/.codex/skills/{name} -> /Users/dalwin/.agents/skills/{name}
```

例外：

- Codex 专属技能可以直接放在 `~/.codex/skills/{name}`。
- 但如果 SOT 中已经存在同名技能，必须 diff 后确定唯一源。

---

## 9. Rules 与 Git Hook 策略

### 9.1 Rules 的边界

`~/.codex/rules/` 只控制沙箱外命令是否允许或需要 prompt。

保留：

- `git-commit-message.rules` 可继续在 `git commit` 时提示审批，并附带 commit convention 提醒。

不依赖：

- 不依赖 rules 确保模型一定写对 commit message。
- 不把 rules 用作通用模型行为规则系统。

### 9.2 Commit message 硬约束

硬约束继续由全局 Git hook 执行：

- 只有显式 message source，如 `git commit -m ...` / `git commit -F ...` 时校验。
- `--no-verify` 不绕过 `prepare-commit-msg`，因此合规 message 通过，不合规 message 拒绝。
- commit 格式：
  `<type>(<scope>): <subject>` 或 `<type>: <subject>`，subject 中文。

---

## 10. 实施顺序

### Phase 0：漂移修复

1. 恢复 `context7` MCP。
2. 安装 `openaiDeveloperDocs` MCP。
3. 将 `features.codex_hooks` 归一为 `features.hooks`。
4. 修复 `git-merge-conductor` skill 软链。
5. diff `req-to-ai-spec`，决定是否改为 SOT 软链。

### Phase 1：Codex design/plan 文档化

1. 提交本 design 文档。
2. 基于本 design 写 Codex 实施计划。
3. 计划中每个 phase 都附验证命令和回滚说明。

### Phase 2：Codex hooks

1. 新增 `~/.codex/hooks/sessionstart-domain.py`。
2. 新增 `~/.codex/hooks/userprompt-workflow-router.py`。
3. 可选新增 `~/.codex/hooks/precompact-memory-hint.py`。
4. 追加到 `~/.codex/hooks.json`，不覆盖 codeisland。
5. 使用仿真 JSON 输入测试 hook 输出。

### Phase 3：Codex memories

1. 启用 `features.memories = true`。
2. 写入短索引 memory，不复制 Claude 全文。
3. 记录与 Claude memory 的对账规则。
4. 验证 `codex debug prompt-input` 不把大块 memory 全量塞入初始上下文。

### Phase 4：Skills 视图收敛

1. Codex 可见 skills 只保留高频和专属。
2. 长尾通过 `~/.agents/skills` 和 skill installer 按需接入。
3. 所有共享技能尽量改为 SOT 软链。

---

## 11. 验证标准

完成后应满足：

- `codex mcp list` 显示 `context7` 和 `openaiDeveloperDocs`。
- `~/.codex/config.toml` 中使用 `features.hooks = true`。
- `codex features list` 中 hooks 有效。
- `~/.codex/skills/git-merge-conductor` 指向 SOT。
- `~/.codex/hooks.json` 保留 codeisland，同时追加 Codex workflow hooks。
- `codex debug prompt-input` 中全局上下文保持短小，不出现 Claude memory 全量复制。
- Git commit message 规则仍由 Git hook 校验，不依赖 Codex rules。

---

## 12. 风险与降级

| 风险 | 缓解 |
|---|---|
| Codex hooks schema 与 Claude 不同 | 先写仿真测试，再注册 hooks；失败时只保留 codeisland |
| memories experimental 行为变化 | memories 只做辅助召回；关闭也不影响核心工作流 |
| skills 软链修复误伤 Codex 专属技能 | 只修明确漂移；同名 skill 先 diff |
| MCP 网络安装失败 | 记录失败，保留 AGENTS 规则但标注 MCP 未可用；下次网络恢复再安装 |
| AGENTS 过长 | 只放稳定短规则；详细偏好进入 memories/docs |
| rules 被误用为行为规则 | 文档明确 rules 只管 sandbox 外命令审批 |

---

## 13. 后续重看条件

- Codex memories 从 experimental 变为 stable，或官方语义改变。
- Codex hooks 引入更细的事件或支持更可靠的 compact 前写入。
- Context7 / OpenAI Docs MCP 安装方式变化。
- Codex skills 初始加载策略变化，导致当前挂载数量需要重估。
- 用户工作分布变化，新增工作域占比超过 10%。

---

## 14. 结论

Codex 版不复制 Claude 版配置，而是复制它的工作流意图：稳定规则少量常驻，动态上下文按需提示，技能源单一，工具间定期对账。

当前最先做的是 Phase 0：修复 MCP 和 skills 漂移。然后再进入 hooks、memories、skills 视图收敛。这样可以先恢复“现在就该有的能力”，再逐步建设更完整的 Codex 工作流层。
