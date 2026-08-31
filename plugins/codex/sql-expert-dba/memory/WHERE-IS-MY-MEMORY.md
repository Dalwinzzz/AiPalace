# 运行时沉淀在哪里？

本目录（插件缓存目录）只存 seed memory（glossary-001 / rule-001 /
template-001），随插件版本分发，重装/升级会被覆盖。

运行时新沉淀的 SQL 知识不在这里，而在用户级全局目录：

    默认：~/.codex/memories/sql-expert-dba/
    可被覆盖：$SQL_EXPERT_DBA_MEMORY_DIR
          或 $CODEX_HOME/memories/sql-expert-dba/

结构（v2）：
    approved/{rules,cases,templates,glossary}/   ← approved 条目
    candidates/{rules,cases,templates,glossary}/ ← candidate 条目
    index.json          ← 检索索引
    capture-log.jsonl   ← 沉淀日志

查看最近沉淀：
    ls -lt ~/.codex/memories/sql-expert-dba/candidates/*/
