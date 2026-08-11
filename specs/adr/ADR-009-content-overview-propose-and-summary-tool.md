# ADR-009: Content overview at propose + dedicated summary tool

## Status
Accepted

## Context
`KnowledgeItem.summary` was easy to treat as a title line. Callers (list, search, MCP) need a short **content overview** without re-reading the blob or inventing text from RAG chunks. Alternatives considered: (1) generate overview only at propose; (2) add a read/refresh tool; (3) LLM on every search; (4) stitch chunk text as overview.

## Decision
Use **方案 1 + 2**:
1. At `kb_propose_add` / propose REST, KM writes a real content overview into `summary`, hard-capped at **400** Unicode characters (`truncate_summary`).
2. Expose **`kb_knowledge_summary`** (and REST GET/refresh) to read by `knowledge_id` or `pending_id`; `refresh=true` regenerates from blob via KM and writes `summary` only — **does not** re-index Qdrant or auto-confirm.

## Rationale
- Overview at propose keeps list/search cheap and consistent after confirm.
- Refresh covers backfill of short/legacy summaries without a second index pipeline.
- Per-search LLM and chunk-stitching were rejected (cost, hallucination, wrong field semantics).

## Consequences
- Spec: `specs/knowledge-summary.md`; ops: `specs/knowledge/ops/content-overview.md`.
- Contracts / MCP tool set include `kb_knowledge_summary`.
- Fake KM must produce a long heuristic overview in tests, not a title line.

## Date
2026-08-11
