# ADR-004: MCP facade shares KbService with REST

## Status
Accepted

## Context
MVP-2 adds a Streamable HTTP MCP endpoint at `/mcp` while REST already exposes knowledge APIs. Dual business paths would drift (auth, propose/confirm rules, tenant isolation).

## Decision
Mount MCP in the same kb-agent process as REST. Tools call the shared `KbService` only. Bearer validation reuses `authenticate_bearer` (same pepper/hash). No second domain layer for MCP.

## Rationale
- Matches `mcp-design.md` and agent-builder “thin harness” guidance.
- One place for scope codes (`OUT_OF_SCOPE_AUTO_INGEST`), confirm→index, and list filters.
- Alternatives rejected: separate MCP microservice; MCP calling REST over HTTP (extra hop + dual clients).

## Consequences
- MCP SDK upgrades (e.g. `mcp` 2.x `MCPServer`) stay in the facade; domain tests remain REST/KbService-centric.
- Parent FastAPI lifespan must run the StreamableHTTP session manager when mounting.
- Cursor / ChatBox and App REST stay on one Key and one library (ChatBox uses `/sse`; see ADR-006).

## Date
2026-08-11
