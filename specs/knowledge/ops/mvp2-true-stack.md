# Ops: MVP-2 true-stack journey

## Purpose
Closed-loop DoD for MVP-2 without Fake Embedder / fake KM / mocked RAG HTTP.

## Prerequisites
- Postgres `:5434`, Qdrant `:6333`
- `.env` with working `QWEN_API_KEY` / `QWEN_BASE_URL`
- `QWEN_EMBED_MODEL=text-embedding-v3`, `EMBED_DIM=1024`
- Prefer a dedicated collection when leaving fake(64) data: `QDRANT_COLLECTION=kb_chunks_v3`

## Run services
```bash
export USE_FAKE_EMBEDDER=false USE_FAKE_KM=false
export QWEN_EMBED_MODEL=text-embedding-v3 EMBED_DIM=1024
export QDRANT_COLLECTION=kb_chunks_v3
make up-daemon   # durable local stack (prefer over Agent-background uvicorn)
# or: system Terminal → make up && (cd apps/kb-web && npm run dev)
```

若服务「莫名停掉」，见 [local-apps-keep-dying.md](./local-apps-keep-dying.md)。

## Journey script
```bash
USE_FAKE_EMBEDDER=false USE_FAKE_KM=false \
  .venv/bin/python scripts/mvp2_true_stack_journey.py
```

Expect `TRUE_STACK_JOURNEY_PASSED` (propose → confirm → search citation → list → scope-03 → MCP initialize).

Registered MCP tools (after reload): `kb_internal_search`, `kb_propose_add`, `kb_confirm_add`, `kb_list_knowledge`, `kb_knowledge_summary`.

## Cursor hand-test
Settings → Customize → MCPs → + New → Streamable HTTP → `http://<HOST>:<AGENT_PORT>/mcp` + Bearer (never commit the key).

## ChatBox hand-test
Add MCP Server → Type **Remote (http/sse)** → URL **`http://<HOST>:<AGENT_PORT>/sse`** → HTTP Header `Authorization=Bearer <key>` → Test → Save.  
Do **not** use `/mcp` in ChatBox (SSE GET → 404). Same tools as Cursor. See [`../mcp-design.md`](../mcp-design.md) §7.2.

Optional: `kb_knowledge_summary(knowledge_id=…, refresh=true)` to backfill a short overview (see [content-overview.md](./content-overview.md)).

## Notes
- Qdrant client may warn on server/client minor mismatch; `check_compatibility=False` is set in `QdrantVectorStore`.
- Fixture CI may keep `USE_FAKE_EMBEDDER=true` with Qdrant + Fake embedder; that is not DoD evidence.
