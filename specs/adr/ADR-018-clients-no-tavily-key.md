# ADR-018: Clients never configure TAVILY_API_KEY

## Status
Accepted

## Context
`kb_external_search` needs `TAVILY_API_KEY` on the process that runs `KbService` (ADR-015). Early guide copy told IDE stdio users to apply for their own Tavily key in `mcp.json`, while ChatBox/remote already used the agent host env. End users should not manage a second paid vendor key just to call MCP.

## Decision
- **Product path:** IDE and third-party tools connect via **remote MCP** (Cursor/CodeBuddy → Streamable HTTP `/mcp`; ChatBox → SSE `/sse`). Callers only configure the Bearer user API Key.
- **`TAVILY_API_KEY`** is configured only on the **kb-agent server** (production ops / local agent `.env`). Never in ChatBox forms or end-user client templates.
- **Local stdio** remains an optional contributor path for library tools against a local stack; client docs do **not** instruct end users to add Tavily. Full external search for product use goes through remote MCP to a host that already has the key.

## Rationale
One less secret for callers; platform controls outbound search quota and vendor billing; aligns IDE with ChatBox. Alternatives rejected: per-user Tavily in every mcp.json (friction + key sprawl); embedding Tavily inside ChatBox (wrong process boundary).

## Consequences
- `/guide` and deployment client recipes recommend remote first; remove `TAVILY_API_KEY` from client-facing mcp.json snippets.
- Ops must set `TAVILY_API_KEY` (or fixture) on kb-agent for external search to work in production.
- Self-host operators put the key in agent `.env`, not in each IDE.

## Date
2026-08-11
