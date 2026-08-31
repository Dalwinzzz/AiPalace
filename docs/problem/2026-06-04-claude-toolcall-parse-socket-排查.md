# Claude session「tool call could not be parsed / socket closed」排查记录

> 日期：2026-06-04 ｜ 环境：Claude Code（Opus 4.x，`effortLevel: high`）
> 出错现场 session：`2d9a3893-3c91-41bb-90e7-6e8172c8f8d1`（即截图所在 session）

## 一、现象
- 多次 `The model's tool call could not be parsed (retry also failed).`
- `API Error: The socket connection was closed unexpectedly.`
- 两类错误**都发生在 11–19 分钟超长思考之后**，且**越到 session 后段越密集**（socket 错误集中在当前 session 行 164–214）。
- 初始怀疑：刚迭代的本地插件 `sql-expert-dba` 新增的 hook 有问题。

## 二、核心结论：**不是 sql-expert-dba 的 Stop hook**

插件 v1.1.0 确实在 Claude 侧新增了 Stop hook
（`hooks/hooks.json` → `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/auto_memory_runner.py`，
输出 `{"decision":"block","reason":REMINDER}`）。但三条独立证据排除了它：

1. **报错现场没有 hook 注入**：真实 parse 失败现场 `b75b0628`、socket 现场 `2d9a3893`，
   其 transcript 内 Stop hook 的 REMINDER 真实注入数 = **0**。报错发生在根本没有 hook 注入的 session 里。
2. **该 hook 在真实环境从未成功执行过**：`~/.claude/plugins/data/sql-expert-dba/memory/`
   与 `capture-log.jsonl` **都不存在**；但手动喂 stdin 跑脚本能 exit=0、正确 block、正常建目录。
   → 说明 Claude Code 实际调用时**静默失败**（疑似 `${CLAUDE_PLUGIN_ROOT}` 展开/环境问题）。
   一个从没跑起来的 hook，不可能是元凶。
3. **之前看到的 REMINDER 文本是内容污染**：来源全是 `tool_use:Write`（在 `docs/.../specs/2026-06-04-sql-expert-*` 写设计文档）
   和 Read 源码，不是 hook 注入。

补充：`retry also failed` 的畸形 turn **不写入 transcript**（所以现场 transcript 里 isMeta「malformed」=0）；
只有 retry 提示会以 `isMeta:true` 的 user 消息「Your tool call was malformed and could not be parsed. Please retry.」出现。

## 三、已执行的处置
- **已禁用** Claude 侧 Stop hook：
  `~/.claude/plugins/cache/dalwin-local-plugins/sql-expert-dba/1.1.0/hooks/hooks.json` → `{"hooks":{}}`
  原文件备份：同目录 `hooks.json.disabled-bak`
  **生效条件：需重启 Claude Code。**
- 注：仅禁用了当前生效的缓存版；开发目录已无 hooks.json，marketplace 源（`/Users/dalwin/Library/CodeRepo/AI/claude-plugins`）如有同名 hook，重装时可能复活，需要时一并处理。

## 四、真凶方向（强相关，待复现验证）
`effortLevel: high`（`~/.claude/settings.json:244`）+ Opus extended thinking + 上下文持续累积
→ 单轮推理耗时冲到 ~19 分钟、请求体巨大
→ 超过 API 网关/代理超时被掐断（socket closed），或 tool call 序列化时偶发畸形（parse failed）。
属**配置 + 上下文规模 + 网络/API 层**问题，与插件 hook 无关。
（无法 100% 坐实，因为 retry-also-failed 的畸形输出不落盘；但「不是 hook」已由上面三证确证。）

## 五、验证方案：开新 session 复现
1. **退出 Claude Code，开一个全新 session（不要 resume `2d9a3893`）。** hook 已禁，新 session 不挂该 Stop hook。
2. 在新 session 做同类任务（分析本插件 / 任何会触发较长 thinking 的活），先读本文件接上下文。
3. **判断标准**：
   - ✅ 新 session 不再出现 → 确认根因是「上下文累积 + 超长单轮」。根治：单 session 别拖太长、勤用 `/compact`、必要时 `effortLevel` 降到 `medium`。
   - ❌ 新 session 仍频繁出现 → 排除「上下文累积」，把 `effortLevel` 降到 `medium` 再试；仍有则查网络/代理/某个 MCP server。
4. **记录**：每次出现时的思考时长、当时上下文大小、正在做的操作。

## 六、关联问题：「memory 没起效」
根因即第二节第 2 条——自动沉淀 hook 从未真正执行成功，所以零沉淀。
这是**与 parse/socket 独立的另一个 bug**，待 `${CLAUDE_PLUGIN_ROOT}` / hook 执行问题查清后再单独修。
