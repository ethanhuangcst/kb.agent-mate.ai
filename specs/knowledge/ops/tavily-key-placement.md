---
title: Where TAVILY_API_KEY lives (server only)
type: ops-lesson
status: active
as_of: 2026-08-11
tags:
  - tavily
  - mcp
  - external-search
  - ops
related_spec: specs/adr/ADR-018-clients-no-tavily-key.md
related:
  - knowledge/ops/mcp-stdio-auth.md
  - knowledge/ops/chatbox-mcp-sse.md
  - adr/ADR-015-external-search-adapters.md
  - adr/ADR-018-clients-no-tavily-key.md
---

# Where `TAVILY_API_KEY` lives

## Summary
End-user clients (IDE remote MCP, ChatBox SSE, REST apps) **never** configure `TAVILY_API_KEY`. Only the **kb-agent server** env holds it (ADR-018). Product guide recommends remote Streamable HTTP for IDE so external search works without a second vendor key.

## Evidence
- Adapter selection: `TAVILY_API_KEY` or `KB_SOURCE_USE_FIXTURE=true`, else `SOURCE_UNAVAILABLE` (ADR-015).
- Remote `/mcp` and `/sse` execute tools in the agent process → server env.
- Local stdio is an optional contributor path; client templates omit Tavily.

## Lesson / guidance

| Actor | Configures `TAVILY_API_KEY`? |
| --- | --- |
| Cursor / CodeBuddy **remote** (`…/mcp` + Bearer) | No |
| ChatBox **Remote http/sse** (`…/sse`) | No |
| REST apps | No |
| kb-agent host (prod ops / local `.env`) | **Yes** |
| IDE local stdio (optional) | No in product docs; use remote for external search |

Ops: set key in **repo-root** `.env` for local `make up-daemon` (not in client mcp.json). Templates: `.env.example` / `.env.prod.example` keep empty placeholders + ADR-018 comments; production fill-in is ops-only. Restart agent after changes (`make down-apps && make up-daemon`). Do not put Tavily in ChatBox or end-user mcp.json snippets.

## Links
- Guide: `/guide` §§1 / 3 / 4
- ADR-015, ADR-018
- Env templates: `.env.example`, `.env.prod.example`
