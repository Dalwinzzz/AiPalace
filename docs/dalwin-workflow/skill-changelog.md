# Skill Changelog

记录 `~/.claude/skills/` 的增删变更。格式：日期 / skill 名 / 圈层 / 操作 / 备注。

---

## 2026-06-01

### 新增：liquibase-dual-db-writer（外圈）

- **SOT**：`~/Library/CodeRepo/AI/awesome-skills/liquibase-dual-db-writer`
- **链路**：`.claude/skills/liquibase-dual-db-writer` → `.agents/skills/liquibase-dual-db-writer` → SOT（双跳）
- **圈层**：外圈 tail（不预加载，按描述触发）
- **触发描述**：为 MySQL + Kingbase 双库生成 Liquibase SQL 及 changelog 条目，适用于 SKC-style 布局（`src/main/resources/liquibase`）
- **分类依据**：Liquibase/SaaS 域专属工具，非跨域 process；触发频率低且场景具体，不进 pack-java 中圈，归外圈按需触发
- **跨工具共享**：工具语义中性（无 Claude Code 专属 API），放 awesome-skills/，codex 同步可用
