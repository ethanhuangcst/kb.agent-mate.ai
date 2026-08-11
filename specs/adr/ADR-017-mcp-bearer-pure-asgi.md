# ADR-017: MCP Bearer auth must be pure ASGI (not BaseHTTPMiddleware)

## Status
Accepted

## Context
ChatBox uses legacy SSE (`GET /sse` + `POST /messages/`). Bearer auth originally used Starlette `BaseHTTPMiddleware`. That class buffers/rewrites the response body and asserts every follow-on message is `http.response.body`. MCP SSE later emits another `http.response.start`, which raises `AssertionError`, drops the session, and leaves ChatBox tool calls spinning forever (`POST /messages/` → 404 Could not find session). The first `endpoint` event can still leak out, which made the failure look intermittent.

## Decision
Implement MCP path Bearer authentication as a **pure ASGI** middleware (`__call__(scope, receive, send)`). Do **not** subclass or wrap MCP/SSE with `BaseHTTPMiddleware`. Keep auth on `/mcp`, `/sse`, and `/messages/`.

## Rationale
Alternatives considered:
- Keep `BaseHTTPMiddleware` and only auth non-SSE paths — still risks other streaming mounts and duplicates logic.
- Auth only inside MCP tool handlers — leaves unauthenticated handshake and weaker gate.
- Pure ASGI middleware — streams pass through unchanged; matches Starlette guidance for SSE.

## Consequences
- Any future global middleware that subclasses `BaseHTTPMiddleware` can regress ChatBox; prefer pure ASGI for streaming routes.
- After changing auth middleware, restart kb-agent (`make down-apps && make up-daemon`); hot-reload may not apply in daemon mode.
- Ops runbook: `specs/knowledge/ops/chatbox-mcp-sse.md`.

## Date
2026-08-11
