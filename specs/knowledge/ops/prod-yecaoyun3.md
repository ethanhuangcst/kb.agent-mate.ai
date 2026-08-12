# 野草云3 生产部署交接（kb-agent）

## When to use

Handing `kb.agent-mate.ai` to release-bot for Portainer deploy / update on 野草云3.

## Facts (as_of 2026-08-12)

| Item | Value |
| --- | --- |
| Node | 野草云3 · `38.55.192.140` |
| Domain | `kb.agent-mate.ai` |
| Stack | `kb-agent` |
| Compose | repo `docker-compose.prod.yml` |
| Images | `ghcr.io/ethanhuangcst/kb.agent-mate.ai/{web,agent,rag}` |
| **IMAGE_TAG（当前生产）** | **`v0.1.3`**（CSP + Next 15.5.7；此前事故重建 `v0.1.2`） |
| Host ports | `3006` (web), `3202` (agent), `3203` (rag), qdrant 宜 `127.0.0.1:6336` |
| Postgres | Aliyun `101.132.156.250:5432` / DB **`kb_agent`** |
| Env template | **`.env.prod.example`**（本机可填密钥且 **gitignored**；Portainer 粘贴同内容；勿提交） |

Canonical runbook: [`deployment-plan.md`](../../deployment-plan.md).  
Security: [`security/clickfix-html-inject-2026-08-12.md`](../security/clickfix-html-inject-2026-08-12.md)、[ADR-020](../../adr/ADR-020-csp-nonce-clickfix-defense.md).  
Platform IR / release-bot job: release-bot `Release-jobs/kb.agent-mate.ai/` + `specs/knowledge/ops/kb-agent-clickfix-incident-2026-08-12.md`.

## Aliyun DB checklist

1. Whitelist / security group allows **`38.55.192.140`** → `:5432`.
2. From the node: `select 1` and `select version_num from alembic_version`.
3. Never point this stack at `mypoke_trade_prod` / `media_marketing` / other DBs on the same host.
4. After any credential incident: rotate DB password and app secrets (open if skipped).

## Client URLs (production)

| Client | URL |
| --- | --- |
| Cursor / CodeBuddy | `https://kb.agent-mate.ai/mcp` |
| ChatBox | `https://kb.agent-mate.ai/sse` |

No client `TAVILY_API_KEY` (ADR-018).

## Post-update checks

See [for-kb/15-prod-release-health-checks.md](../for-kb/15-prod-release-health-checks.md): CSP header, no `data:text/javascript;base64`, `/healthz` ok; NPM **Save** if agent paths 502.
