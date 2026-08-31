---
title: DeerFlow Agent Harness Learning Document Design
date: 2026-04-10
status: approved
audience: new-to-agents learner
output-language: Chinese (Simplified)
---

# DeerFlow Agent Harness 学习文档 — 设计方案

## 背景与目标 (Background & Goal)

The user wants to study the "agent harness" concept — a trending topic in LLM engineering — by using the open-source `bytedance/deer-flow` (v2.0) project as a concrete vehicle. DeerFlow 2.0 explicitly calls itself an *"open-source super agent harness"*, and its core Python package is literally named `deerflow-harness`, making it an ideal case study.

The deliverable is a **Chinese-language learning index + concept-map** living in its own subdirectory under `docs/`, with each harness concept explained at two levels:

1. **Universal principle** — what problem does this concept solve? (audience: new to agents)
2. **DeerFlow implementation** — how deer-flow actually implements it, via **file-path pointers only** (no full code dumps)

## Audience assumptions

- Reader is **new to LLM agent systems** — fundamental concepts like tool calling, ReAct loop, context window, memory must be introduced, not assumed.
- Reader has general software-engineering literacy (can read Python/file paths, understand "middleware" as a software pattern).
- Reader will use the document both as a **study guide** (read through) and as a **concept index** (look things up via the README mind map).

## Scope

**In scope — the core harness concepts**:

- What an agent harness is and why it exists
- The agent loop (ReAct, tool calls, interruption, streaming)
- Tool system (builtin, MCP, community tools)
- Context engineering (system prompt, summarization, dangling tool call repair, uploads, vision)
- Memory (short-term `ThreadState` vs long-term extracted facts)
- Sandbox (isolated execution, provider abstraction, virtual path translation)
- Sub-agents (delegation, concurrency limits, `task()` tool)
- Middleware pipeline (cross-cutting concerns pattern)
- Skills system (progressive disclosure, SKILL.md discovery)
- Design patterns & trade-offs (synthesis chapter)

**Out of scope**:

- Gateway REST API, frontend (Next.js), IM channels (Feishu/Slack/Telegram)
- Deployment topology, Docker/K8s specifics
- LangGraph internals beyond what's needed
- Provisioner service, sandbox Kubernetes mode details

## Directory Layout

```
docs/harness-learning/
├── README.md                       # Mind-map index + reading paths + glossary
├── 00-what-is-a-harness.md         # Conceptual foundation
├── 01-agent-loop.md                # The core ReAct/tool-call loop
├── 02-tools-and-mcp.md             # Tool system & MCP integration
├── 03-context-engineering.md       # What the LLM sees each turn
├── 04-memory.md                    # Short + long-term memory
├── 05-sandbox.md                   # Isolated execution environment
├── 06-subagents.md                 # Hierarchical delegation
├── 07-middleware.md                # Cross-cutting pipeline pattern
├── 08-skills.md                    # Progressive capability disclosure
└── 09-patterns-and-tradeoffs.md    # Synthesis: harness design principles
```

Total: **11 files** (1 index + 10 concept/synthesis files).

## README.md (mind-map index) structure

1. **What is an agent harness?** — 3-sentence definition
2. **Mind map** — nested-bullet hierarchy of concepts (NOT a mermaid diagram; nested bullets render everywhere and stay lightweight)
3. **Reading paths** — "If you're new: read 00 → 01 → 07 → 02 → ...", "If you want depth on X: read X"
4. **Concept-to-file index** — flat lookup table: concept → file
5. **Glossary** — key terms (agent, harness, tool, middleware, sandbox, sub-agent, MCP, skill, ReAct, thread)
6. **Cross-reference: DeerFlow source tree map** — one-line-per-dir summary of `backend/packages/harness/deerflow/` so readers can navigate source while studying

## Concept-file internal structure (uniform across files 00-08)

Each concept file follows the same 5-section structure (in Chinese):

```
# <Chapter title>

## 核心问题 (Core problem)
One paragraph: what breaks without this concept? Why does a bare LLM API call fall short here?

## 通用概念 (Universal principle)
2-5 paragraphs: the general idea, independent of deer-flow. Explain jargon inline. For a new-to-agents reader.

## DeerFlow 的实现 (DeerFlow's implementation)
Bulleted file pointers with one-line descriptions. Example:
- `backend/packages/harness/deerflow/agents/lead_agent/agent.py` — `make_lead_agent()` is the factory that assembles model + tools + middleware + system prompt.
No code dumps. Just paths + what's there.

## 设计权衡 (Design trade-offs)
2-4 bullets: alternative approaches, what deer-flow picked, the implicit bet.

## 延伸阅读 (Further reading)
Optional: links to other chapters, external references (LangChain, MCP spec, etc.)
```

The synthesis chapter (`09-patterns-and-tradeoffs.md`) has a different shape — it recaps principles across the whole system:
- Layered boundary (`deerflow.*` vs `app.*`, never importing upward)
- Middleware composition over monolithic logic
- Provider abstraction (sandbox, model)
- Configuration-driven assembly
- Per-thread isolation
- Lazy initialization

## Authoritative source material used

1. **DeerFlow README.md** — defines the term "super agent harness", lists core features
2. **DeerFlow `backend/CLAUDE.md`** — architectural overview and runtime modes
3. **DeepWiki (`deepwiki.com/bytedance/deer-flow`)** — structured summary of middleware, sandbox, memory, subagents
4. **Source tree exploration** — `backend/packages/harness/deerflow/` walked directly for file-path verification
5. **`agents/lead_agent/agent.py`** — read in full for authoritative middleware assembly logic

## Verified file-path anchors (per concept)

| Concept | Primary file pointers |
|---|---|
| Agent loop | `agents/lead_agent/agent.py`, `agents/lead_agent/prompt.py`, `agents/thread_state.py` |
| Tools | `tools/__init__.py`, `tools/tools.py`, `tools/builtins/*.py` |
| MCP | `mcp/client.py`, `mcp/tools.py`, `mcp/cache.py`, `mcp/oauth.py` |
| Context engineering | `agents/lead_agent/prompt.py`, `config/summarization_config.py`, `agents/middlewares/{dangling_tool_call,uploads,view_image}_middleware.py` |
| Memory | `agents/memory/{storage,queue,updater,prompt}.py`, `agents/middlewares/memory_middleware.py`, `config/memory_config.py` |
| Sandbox | `sandbox/sandbox.py`, `sandbox/sandbox_provider.py`, `sandbox/local/`, `sandbox/middleware.py`, `sandbox/security.py`, `sandbox/tools.py` |
| Sub-agents | `subagents/executor.py`, `subagents/registry.py`, `subagents/builtins/`, `tools/builtins/task_tool.py`, `agents/middlewares/subagent_limit_middleware.py` |
| Middleware | `agents/middlewares/` (15 files) + `agents/middlewares/tool_error_handling_middleware.py` `_build_runtime_middlewares` + `sandbox/middleware.py` + `guardrails/middleware.py` |
| Skills | `skills/{manager,loader,parser,installer,security_scanner,types,validation}.py`, `tools/builtins/skill_manage_tool.py` |

## Middleware list (authoritative, verified in agent.py)

Base chain built by `build_lead_runtime_middlewares()` in `tool_error_handling_middleware.py`:

1. `ThreadDataMiddleware` — per-thread isolated dirs
2. `UploadsMiddleware` — inject uploaded files into context (inserted at position 1 for lead)
3. `SandboxMiddleware` — acquire sandbox
4. `DanglingToolCallMiddleware` — repair missing ToolMessages in history (lead only)
5. `LLMErrorHandlingMiddleware` — LLM-layer errors
6. `GuardrailMiddleware` — auth/safety policy (if configured)
7. `SandboxAuditMiddleware` — audit sandbox operations
8. `ToolErrorHandlingMiddleware` — convert tool exceptions → `ToolMessage(status="error")`

Then lead-only additions in `_build_middlewares()`:

9. `SummarizationMiddleware` (from `langchain.agents.middleware`) — context trimming (if enabled)
10. `TodoMiddleware` — `write_todos` tool (if plan mode)
11. `TokenUsageMiddleware` — token accounting (if enabled)
12. `TitleMiddleware` — auto conversation title
13. `MemoryMiddleware` — queue async memory extraction
14. `ViewImageMiddleware` — vision model image injection (if supported)
15. `DeferredToolFilterMiddleware` — hide deferred tools (if tool_search enabled)
16. `SubagentLimitMiddleware` — cap concurrent sub-agents (if subagent enabled)
17. `LoopDetectionMiddleware` — break repetitive tool call loops
18. (custom middlewares)
19. `ClarificationMiddleware` — **always last**, intercepts clarification requests

## Deliverables checklist

- [x] Verified file paths via direct source read
- [x] Verified middleware list from `agent.py`
- [x] Consulted DeepWiki for cross-check
- [ ] `docs/harness-learning/README.md` (Chinese, mind map + index)
- [ ] `00-what-is-a-harness.md` (Chinese)
- [ ] `01-agent-loop.md` (Chinese)
- [ ] `02-tools-and-mcp.md` (Chinese)
- [ ] `03-context-engineering.md` (Chinese)
- [ ] `04-memory.md` (Chinese)
- [ ] `05-sandbox.md` (Chinese)
- [ ] `06-subagents.md` (Chinese)
- [ ] `07-middleware.md` (Chinese)
- [ ] `08-skills.md` (Chinese)
- [ ] `09-patterns-and-tradeoffs.md` (Chinese)

## Non-goals / principles

- **Not a DeerFlow reference manual** — this is a harness-concepts study guide that happens to use DeerFlow as a specimen. If forced to choose, favor the universal concept over DeerFlow-specific details.
- **Not a code-reading guide** — pointers only; the reader follows up in source if they want.
- **Not auto-maintained** — this is a snapshot at 2026-04-10. Future DeerFlow changes may drift.
- **Independent of docs/superpowers** — lives at `docs/harness-learning/`, sibling of `docs/spec-best-practices/` and `docs/superpowers/`.
