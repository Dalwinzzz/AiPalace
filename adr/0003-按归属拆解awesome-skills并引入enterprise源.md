# ADR-0003：按真实归属拆解 awesome-skills，引入 enterprise 源与 github-skills

- 状态：已接受
- 日期：2026-06-16
- 决策人：dalwin
- 关联：[ADR-0001](0001-AiPalace为个人AI-harness唯一SOT.md)、[ADR-0002](0002-借鉴garveyhu方案但改硬拷贝.md)

## 背景

初版（ADR-0001/0002）把三处开源来源整份硬拷贝进 `community/`，其中
`community/awesome-skills/`（26 skill）实为公司内部仓
`git@repo.iktapp.com:ai/skills/awesome-skills.git` 的快照——它是同事 garveyhu 上游的
**内部 fork**，与 `community/garveyhu/` 大量同源同名，造成：

1. **同一 skill 存两份**（awesome-skills 与 garveyhu），备份冗余、易漂移；
2. **归属混淆**：里面混有「我原创的」「公司专属的」「我误拷进来的社区/官方 skill」，
   全被笼统当作 community 备份，无法体现真实 ownership；
3. 原 `community/anthropic-skills/` 命名不准——它实际只放了从 mattpocock/skills 选装的
   grill 系，名字却叫 anthropic。

## 决策

### 1. 用 git 作者 + 上游交叉比对判定归属（不靠猜）
以公司仓的 `git log` 作者区分：`Links`=garveyhu（同事），`czw`=dalwin（我）。
再与 garveyhu 上游 skill 清单交叉比对。结合我本人点名，最终：

| 归属 | skill | 落位 |
|------|-------|------|
| 我原创 | spec-architect、git-merge-conductor | `skills/mine/` |
| 公司内部 | liquibase-dual-db-writer（SKC MySQL+Kingbase 双库专属） | `skills/enterprise/zhijin/` |
| 与 garveyhu 重复 | docker/fastapi/react/website-best-practices、style-vault(-sediment)、html-diagram、wiki/req-to-ai/solution/spechub/docsify/notion 等 14 个 | **删除**，保留 garveyhu 最新版 |
| 误拷的开源/官方 | docx、find-skills、gemini-svg-creator、svg-logo-creator、app-icon、ai-pdf-builder、resume-generator、skill-security-audit | `skills/community/github-skills/` |
| garveyhu 上游没有 | deep-research | 并入 `garveyhu/method/deep-research` |

拆解后 `community/awesome-skills/` 清空删除。

### 2. 新增 `enterprise/` 顶层来源
公司内部 skill 既非个人原创、也非公开开源，单列一层，按公司代号分子目录
（`enterprise/zhijin/`），与 `mine/`、`community/` 三足并立。

### 3. `anthropic-skills/` → `github-skills/`，按来源性质分子目录
- `anthropic-official/`（docx，license: Proprietary）
- `third-party/`（skill-security-audit=SlowMist、app-icon=RN/Expo 社区）
- `misc/`（未能精确溯源到某 upstream repo 的社区 skill）
- 顶层保留选装的 grill-me / grill-with-docs（mattpocock/skills）

每个无法精确溯源的 skill 旁放 `_SOURCE.md` 记录已知线索（license/credit/进入路径），
诚实标注「精确 upstream 待补」，而非硬塞一个可能错误的 repo 名。

### 4. 配套：4 个开源 clone 强制对齐远端
`everything-claude-code / get-shit-done / skills / superpowers` 久未更新，
`git fetch + reset --hard origin/<默认分支>` 拉最新主分支（确认无本地改动，按指示强制对齐）。
`garveyhu` 目录非 git repo（手动拷贝），本轮维持现状不动。

## 后果

- 正面：skill 真实 ownership 由目录结构显式表达（mine / enterprise / community）；
  去除 awesome-skills↔garveyhu 冗余；registry 由 49 条精简到 35 条，doctor 全绿。
- 取舍：8 个 community skill 的精确 upstream 暂未定位，以 `_SOURCE.md` 留线索待后续补全。
- 工具适配：`skillctl.skill_dir` 增加 `skills/enterprise/<source>` 候选路径。
