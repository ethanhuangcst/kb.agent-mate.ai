# ADR-006: ChatBox uses legacy SSE alongside Streamable HTTP

## Status
Accepted

## Context
ChatBox “Remote (http/sse)” opens an SSE GET on the configured URL. Clients pointed at `/mcp` (Streamable HTTP only) received `MCP SSE Transport Error: 404`. Cursor continues to require Streamable HTTP at `/mcp`.

## Decision
Expose both transports from the same kb-agent process and tool registration:
- Streamable HTTP: `/mcp` (Cursor)
- Legacy SSE: `GET /sse` + `POST /messages/` (ChatBox)

Bearer auth middleware covers `/mcp`, `/sse`, and `/messages/`. Tools still call shared `KbService` only (ADR-004).

## Consequences
- Docs and `/guide` must list **different URLs per client**; “same URL for ChatBox and Cursor” is incorrect.
- Production NPM must forward `/sse` and `/messages/` in addition to `/mcp`.
- Prefer Streamable HTTP for new clients; keep SSE for ChatBox compatibility.

## Date
2026-08-11
