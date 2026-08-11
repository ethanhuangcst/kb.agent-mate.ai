# ADR-005: Agent↔RAG vector store defaults to Qdrant even with Fake Embedder

## Status
Accepted

## Context
Tying `InMemoryVectorStore` to `USE_FAKE_EMBEDDER=true` broke propose→confirm→search across processes: agent and rag are separate uvicorn processes, so in-memory upserts are invisible to later search.

## Decision
Default kb-rag to Qdrant for vector persistence. Use process-local InMemory only when `USE_INMEMORY_VECTOR_STORE=true` (unit TestClient). `USE_FAKE_EMBEDDER` selects Fake vs DashScope embedder only, not storage.

## Rationale
- CI/local can keep Fake Embedder while still exercising agent↔rag HTTP + Qdrant.
- DoD true-stack sets `USE_FAKE_EMBEDDER=false` and a dedicated collection (e.g. `kb_chunks_v3`, dim 1024).

## Consequences
- Local `make up-deps` must include Qdrant for HTTP closed-loop tests.
- Collection dim must match embedder; switching fake(64) ↔ real(1024) needs a different collection name or recreate.

## Date
2026-08-11
