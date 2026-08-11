# 野草云3 生产部署交接（kb-agent）

## When to use

Handing `kb.agent-mate.ai` to release-bot for first (or subsequent) Portainer deploy on 野草云3.

## Facts (as_of 2026-08-11)

| Item | Value |
| --- | --- |
| Node | 野草云3 · `38.55.192.140` |
| Domain | `kb.agent-mate.ai` |
| Stack | `kb-agent` |
| Compose | repo `docker-compose.prod.yml` |
| Images | `ghcr.io/ethanhuangcst/kb.agent-mate.ai/{web,agent,rag}` |
| Host ports | `3004` (web), `3202` (agent), `3203` (rag), `127.0.0.1:6336` (qdrant) |
| Postgres | Aliyun `101.132.156.250:5432` / DB **`kb_agent`** (created + migrated through `005_import_batch`) |
| Env template | `.env.prod.example` (fill secrets in Portainer only) |

Canonical runbook: [`deployment-plan.md`](../../deployment-plan.md).  
Node inventory to update after deploy: release-bot `specs/hk_vps_3_resources.md`.

## Aliyun DB checklist

1. Whitelist / security group allows **`38.55.192.140`** → `:5432`.
2. From the node (or a container on `portainer_network`): `select 1` and `select version_num from alembic_version`.
3. Never point this stack at `mypoke_trade_prod` / `media_marketing` / other DBs on the same host.

## Client URLs (production)

| Client | URL |
| --- | --- |
| Cursor / CodeBuddy | `https://kb.agent-mate.ai/mcp` |
| ChatBox | `https://kb.agent-mate.ai/sse` |

No client `TAVILY_API_KEY` (ADR-018).
