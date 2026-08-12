# ADR-016: Bounded OpenAI-compatible chat facade

## Status
Accepted

## Context
`agent-chat-01` asks for an optional OpenAI-compatible entry that uses the same tools and scope rules without becoming a full business agent (scheme 2).

## Decision
- Ship `POST /v1/chat/completions` behind `CHAT_FACADE_ENABLED` (default false).
- Server-side tool loop (max `CHAT_MAX_TOOL_ITERATIONS`) calling the same `KbService` methods as MCP tool names.
- Pre-check user text with `scope_guard`; reject `OUT_OF_SCOPE_*` like MCP/REST.
- No `kb_chat_*` MCP tools. `stream=true` unsupported in this MVP.

## Rationale
Thin enough to stay a harness, strong enough to exercise the tool surface for debugging. Feature flag avoids accidental public agentization. Sharing `KbService` preserves ADR-004.

## Consequences
- Requires DashScope/`QWEN_API_KEY` when `USE_FAKE_KM=false`; tests use `FakeChatClient`.
- Not a multi-tenant chat product or conversation store.
- Host models (Cursor/ChatBox MCP) remain the primary agent loop.

## Date
2026-08-11
