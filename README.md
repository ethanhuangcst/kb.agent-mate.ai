# kb.agent-mate.ai

Private knowledge-base agent: MCP + REST (`kb-agent`), RAG (`kb-rag`), admin/guide UI (`kb-web`).

## Local stack

```bash
cp .env.example .env   # fill secrets; see specs/keys.md
make install
make up-daemon         # preferred: Postgres + Qdrant + agent + rag + web (durable)
make status
make down              # stop apps + compose deps
# make down-apps       # apps only
```

Prefer **`make up-daemon`** when starting from Cursor Agent (avoids child processes dying with the agent shell). Details: [`specs/knowledge/ops/local-apps-keep-dying.md`](specs/knowledge/ops/local-apps-keep-dying.md).

| Service | Local URL |
| --- | --- |
| kb-web | http://127.0.0.1:3000 |
| kb-agent (REST + MCP) | http://127.0.0.1:8000 |
| MCP Cursor | http://127.0.0.1:8000/mcp |
| MCP ChatBox (SSE) | http://127.0.0.1:8000/sse |
| kb-rag | http://127.0.0.1:8001 |
| Postgres | 127.0.0.1:5434 |
| Qdrant | 127.0.0.1:6333 |

MCP config (Cursor / ChatBox, `KB_API_KEY` vs `API_KEY_PEPPER`): [`specs/deployment-plan.md`](specs/deployment-plan.md) §7.1.

## Layout

| Path | Role |
| --- | --- |
| `apps/kb-web` | Next.js admin + guide |
| `services/kb-agent` | Orchestration, MCP, REST |
| `services/kb-rag` | Embed + Qdrant |
| `packages/kb_schema` | SQLAlchemy / Alembic |
| `specs/` | Requirements, design, ADRs, ops knowledge |
| `contracts/` | MCP / search JSON contracts |

## Docs index

[`specs/README.md`](specs/README.md)
