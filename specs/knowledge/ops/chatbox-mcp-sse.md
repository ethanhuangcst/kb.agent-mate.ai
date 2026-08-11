---
title: ChatBox MCP (SSE) and hang diagnosis
type: ops-lesson
status: active
as_of: 2026-08-11
tags:
  - mcp
  - chatbox
  - sse
  - ops
related_spec: specs/mcp-design.md
related:
  - knowledge/ops/tavily-key-placement.md
  - knowledge/ops/mcp-stdio-auth.md
  - adr/ADR-006-chatbox-legacy-sse.md
  - adr/ADR-017-mcp-bearer-pure-asgi.md
  - adr/ADR-018-clients-no-tavily-key.md
---

# Ops: ChatBox MCP (SSE)

## Purpose
ChatBox **Remote (http/sse)** is legacy SSE, not Streamable HTTP. Misconfiguring `/mcp` yields `MCP SSE Transport Error: 404`. Clients do not configure `TAVILY_API_KEY` (ADR-018).

## Config

| Field | Value |
| --- | --- |
| Type | Remote (http/sse) |
| URL | **`https://kb.agent-mate.ai/sse`** |
| HTTP Header | `Authorization=Bearer <api_key>` |

After Test succeeds: save, enable in the chat session, then call `kb_list_knowledge` / `kb_internal_search` / `kb_external_search`.

## Contrast

| Client | Transport | URL |
| --- | --- | --- |
| Cursor | Streamable HTTP | `https://kb.agent-mate.ai/mcp` |
| ChatBox | SSE | `https://kb.agent-mate.ai/sse` (+ server posts to `/messages/`) |

Same Bearer key and tool set. Spec: [`mcp-design.md`](../../mcp-design.md) §7.2.

## Hang: tool spinner never returns

**Symptom:** ChatBox shows `mcp__kb_list_knowledge` (or search) spinning forever; MCP Test may look connected then fail on tool calls.

**Cause:** wrapping the FastAPI app with Starlette `BaseHTTPMiddleware` for Bearer auth. SSE needs a pure ASGI middleware (`__call__(scope, receive, send)`). With `BaseHTTPMiddleware`, logs show:

```text
AssertionError: Unexpected message: {'type': 'http.response.start', ...}
POST /messages/?session_id=… → 404 Could not find session
```

The first `endpoint` event can still leak out (curl sees it), then the stream crashes and the session is gone — ChatBox waits forever for the tool result.

**Fix:** pure ASGI Bearer middleware in `mcp_server.mount_mcp` (do not subclass `BaseHTTPMiddleware`). Decision: [ADR-017](../../adr/ADR-017-mcp-bearer-pure-asgi.md). Restart kb-agent after the change (`make down-apps && make up-daemon`). Local stack smoke (contributor only; product clients use `https://kb.agent-mate.ai/sse`):

```bash
# keep SSE open; expect event: endpoint with session_id
curl -sN -H "Authorization: Bearer <api_key>" -H "Accept: text/event-stream" \
  http://127.0.0.1:8000/sse
```

Then POST `initialize` / `tools/call` to `/messages/?session_id=…` while that connection stays open. Agent log must not contain `AssertionError` from `starlette/middleware/base.py`.

## Links
- Tavily placement: [`tavily-key-placement.md`](./tavily-key-placement.md)
- ADR-006 (SSE transport), ADR-017 (auth middleware), ADR-018 (no client Tavily)
