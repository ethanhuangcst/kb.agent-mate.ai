# Ops: ChatBox MCP (SSE)

## Purpose
ChatBox **Remote (http/sse)** is legacy SSE, not Streamable HTTP. Misconfiguring `/mcp` yields `MCP SSE Transport Error: 404`.

## Config

| Field | Value |
| --- | --- |
| Type | Remote (http/sse) |
| URL | `http://127.0.0.1:8000/sse` (prod: `https://kb.agent-mate.ai/sse`) |
| HTTP Header | `Authorization=Bearer <api_key>` |

After Test succeeds: save, enable in the chat session, then call `kb_list_knowledge` / `kb_internal_search`.

## Contrast

| Client | Transport | URL |
| --- | --- | --- |
| Cursor | Streamable HTTP | `…/mcp` |
| ChatBox | SSE | `…/sse` (+ server posts to `/messages/`) |

Same Bearer key and tool set. Spec: [`../mcp-design.md`](../mcp-design.md) §7.2.
