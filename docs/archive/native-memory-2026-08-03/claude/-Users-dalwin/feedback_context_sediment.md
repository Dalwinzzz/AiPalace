---
name: feedback-context-sediment
description: 沉淀去向新规——项目级/工作域级事实经 /wrap 写 dalwin-workflow context，不再写 native memory
metadata: 
  node_type: memory
  type: feedback
  originSessionId: a7aba1e3-0608-4dd0-8f10-83cc926e41c8
---

2026-06-13 起，/wrap 的沉淀目标从 native memory 改为 `~/Documents/AI/dalwin-workflow/context/`（SOT，git 版本控制）。路由：项目级业务规则→`context/memory/projects/<代号>.md`；工作域级规则→`context/<域>.md`（path-scoped 自动注入）；术语→`memory/glossary.md`；工作流自身→`memory/ai-workflow.md`。SessionStart hook（`sessionstart-domain.py` 的 `DOMAIN_CONTEXT`）按工作域注入 context 指针（经 `~/.agents/context`）。

**Why:** native memory 按 git-root 隔离，项目规则沉淀后在其他 repo 的会话中注入不稳定；context 层是用户设计的跨项目、按工作域索引的唯一沉淀处。

**How to apply:** 沉淀项目级/域级事实一律走 /wrap 的 context 路由，不要直接写 `~/.claude/projects/-Users-dalwin/memory/`（该目录仅保留 user/feedback/reference 类存量，命中同主题时渐进迁移到 context 并删旧条目）。会话开头看到 `[工作域]` 注入的 context 指针时，涉及对应项目业务规则应先 Read 指向文件。相关：[[project-personal-ai-repo]]、[[reference-cross-tool-memory]]。
