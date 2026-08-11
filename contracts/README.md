# Contracts

Machine-readable API / MCP contracts for drift checks between facades.

| File | Role |
| --- | --- |
| [`search-response.schema.json`](./search-response.schema.json) | `kb_internal_search` / `POST /api/v1/kb/search` response（hit 可含 `title` / `summary`） |
| [`mcp-tools.json`](./mcp-tools.json) | MCP tools + transport（`/mcp` Streamable；`/sse` legacy SSE for ChatBox） |

Design: [`specs/mcp-design.md`](../specs/mcp-design.md), [`specs/agent-design.md`](../specs/agent-design.md), [`specs/knowledge-summary.md`](../specs/knowledge-summary.md), [`specs/test-strategy.md`](../specs/test-strategy.md).
