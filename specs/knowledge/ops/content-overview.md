# Ops: content overview (summary ≤400 chars)

## Purpose
Keep `KnowledgeItem.summary` as a **content overview**, not a title line. Cap: **400** Unicode characters. Spec: [`../knowledge-summary.md`](../knowledge-summary.md). Decision: [ADR-009](../../adr/ADR-009-content-overview-propose-and-summary-tool.md).

## When generated
- **Propose** (`kb_propose_add` / `POST /api/v1/kb/proposals`): KM writes overview once.
- **Refresh**: `kb_knowledge_summary` with `refresh=true`, or `POST /api/v1/kb/items/{id}/summary/refresh`.

## Read paths
- MCP: `kb_knowledge_summary` (`knowledge_id` or `pending_id`)
- REST: `GET /api/v1/kb/items/{id}/summary`
- Also exposed on `kb_list_knowledge` items and `kb_internal_search` hits

## Backfill short summaries
```text
kb_knowledge_summary(knowledge_id="<uuid>", refresh=true)
```
Requires blob body present; does not re-index Qdrant.

## Anti-patterns
- Do not stitch RAG chunk text as the overview
- Do not call LLM on every search to invent summaries
