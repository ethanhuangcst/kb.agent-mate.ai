# Deployment plan — kb-agent

**Consumer:** release-bot (野草云3 semi-auto release).  
**Spec sources:** `specs/architecture.md`, `specs/req.md`, `specs/keys.md`, `specs/release-bot-instruction.md`, `specs/mvp-2-3-delivery.md` (batch DoD; MCP first in MVP-2).  
**Secrets:** never in this file — use Portainer env / node `.env` / local key store (see `specs/keys.md` / `.env.prod.example`).

**Local vs prod:** local Postgres often **`:5434`**; production `USE_FAKE_EMBEDDER=false`. MCP：**Cursor** Streamable HTTP **`/mcp`**；**ChatBox** legacy SSE **`/sse`**（见 [`mcp-design.md`](./mcp-design.md)、下文 §7.1）。  
本地起栈推荐 **`make up-daemon`**（避免 Cursor Agent 回收子进程；[`knowledge/ops/local-apps-keep-dying.md`](./knowledge/ops/local-apps-keep-dying.md)）。

---

## 0. Meta

| Field | Value |
| --- | --- |
| Product | kb-agent (private AI knowledge-base agent) |
| App repo | **`ethanhuangcst/kb.agent-mate.ai`** (local folder: `knowledge.base`) |
| Default git ref | `main` (or release tag `v*`; CI also builds `3-mvp03`) |
| Target node | **野草云3** · public IP **`38.55.192.140`** (inventory: release-bot `specs/hk_vps_3_resources.md`) |
| Stack name | `kb-agent` |
| App slug | `kb` |
| Public domain | **`kb.agent-mate.ai`** (exact spelling; typos break SNI) |
| `PUBLIC_BASE_URL` | `https://kb.agent-mate.ai` |
| Production path | **Portainer + GHCR + Nginx Proxy Manager** on 野草云3 — **not** Caddy/PM2 on bare metal |
| Env template | **`.env.prod.example`**（本机已填密钥且 **gitignored**；Portainer 粘贴同内容；勿再提交） |
| Prod compose | **`docker-compose.prod.yml`** (repo root; local stack stays `docker-compose.yml`) |
| GHCR images | `ghcr.io/ethanhuangcst/kb.agent-mate.ai/{web,agent,rag}:<tag>` |

### Host ports (野草云3, as_of 2026-08-11)

Reserved from `hk_vps_3_resources.md` (avoid 3001–3003 / 3200–3201 / 6333 / 6335):

| Role | Host bind | Container | NPM uses |
| --- | --- | --- | --- |
| web | **`3006→3000`** | `kb-web:3000` | Forward **`kb-web:3000`** |
| agent | **`3202→8000`** | `kb-agent:8000` | Path locations → **`kb-agent:8000`** |
| rag | **`3203→8001`** | `kb-rag:8001` | not public |
| qdrant | **`127.0.0.1:6336→6333`** | `kb-qdrant:6333` | not public |

`<IMAGE_TAG>`: usually `latest` or git sha. Spot-check existing apps: `https://hcp.agent-mate.ai`, `https://mypoke.trade`.

### App-repo readiness (release-bot may proceed)

- [x] `apps/kb-web/Dockerfile`
- [x] `services/kb-agent/Dockerfile`
- [x] `services/kb-rag/Dockerfile`
- [x] `docker-compose.prod.yml` (image-only; external `portainer_network`)
- [x] `.github/workflows/ghcr.yml` → three images to GHCR
- [x] `.env.prod.example`（生产主机/模型 + 本机密钥；**gitignored**，Portainer 用同内容）
- [x] Migrate: `cd packages/kb_schema && DATABASE_URL=… alembic upgrade head` (or repo-root `make migrate` with `DATABASE_URL` set)
- [x] Public paths: Admin `/` `/admin` `/guide`; MCP `/mcp`; SSE `/sse` + `/messages/`; REST `/api/v1/kb/*`; agent `/healthz`

### Ops still required before go-live (not blockers in app repo)

1. Fill Portainer env from `.env.prod.example` (**passwords / API keys / pepper / secrets**).
2. Confirm Aliyun Postgres whitelist allows egress from **`38.55.192.140`** (DB `kb_agent` created + schema migrated 2026-08-11 from ops workstation; re-verify from node).
3. Push images via GHCR workflow (merge/tag or `workflow_dispatch`).
4. DNS `kb` → A `38.55.192.140` + NPM host + Custom Locations (§7).
5. After deploy: smoke §9; update release-bot inventory with kb-agent ports/volumes.

---

## 1. Architecture (runtime)

```text
[Browser / Cursor / ChatBox / App]
    → Cloudflare DNS (prefer grey cloud until LE OK)
        → Nginx Proxy Manager on 野草云3 (:80/:443)
            → kb-web          (Admin UI; optional BFF)
            → kb-agent        (MCP + /api/v1/kb/* — same public host, path-routed)
            → (no public) kb-rag · kb-qdrant
                → outbound: external AliCloud PostgreSQL
                → outbound: DashScope (Qwen chat + embed), Resend, optional Tavily/Exa
```

### Process model

**Multi-service (four containers in this stack):**

| Process | Container | Role |
| --- | --- | --- |
| Admin Web | `kb-web` | Next.js App Router; admin session UI |
| Knowledge agent | `kb-agent` | MCP + knowledge REST; domain layer; source adapters; calls RAG |
| RAG | `kb-rag` | Chunk / embed / hybrid search / index after confirm |
| Vector DB | `kb-qdrant` | Qdrant single-node (sidecar on `portainer_network`) |

**Not in this compose (external):**

- **PostgreSQL** — Aliyun `101.132.156.250:5432`, dedicated DB **`kb_agent`** (same instance as mypoke / media; never share DB name)
- DashScope / 百炼 MaaS, Resend, optional Tavily — SaaS egress only

### Persistence

| Data | Where | Volume / note |
| --- | --- | --- |
| App metadata (users, keys, pending, etc.) | External Postgres | No Docker volume |
| Vectors | Qdrant | volume `kb_qdrant_data` |
| Knowledge originals (BlobStore LocalFs) | Agent or RAG data dir | volume `kb_blob_data` → e.g. `/data/kb/raw` |
| Admin session / nothing sticky on web | — | usually no durable web volume |

### Public vs private

- **Public (via NPM on `kb.agent-mate.ai`):** `kb-web` + path routes to `kb-agent`（Admin、`/api/v1/kb/*`、MCP **`/mcp`**、SSE **`/sse`** + **`/messages/`**、`/healthz`）。详见 [`mcp-design.md`](./mcp-design.md) 与 §7.1。
- **Not public:** `kb-rag`, `kb-qdrant`, Postgres. Host port publish is for debug only; prefer Docker DNS between services.

Internal URLs (compose / Portainer env):

- `AGENT_BASE_URL=http://kb-agent:8000` (from web if BFF calls agent)
- `RAG_BASE_URL=http://kb-rag:8001` (from agent)
- `QDRANT_URL=http://kb-qdrant:6333` (from rag)

---

## 2. Services table

| Service | container_name | Image | Container port | Host port | Public? | Role |
| --- | --- | --- | --- | --- | --- | --- |
| web | `kb-web` | `ghcr.io/ethanhuangcst/kb.agent-mate.ai/web:<tag>` | `3000` | `3006` | yes via NPM | Admin UI (+ BFF) |
| agent | `kb-agent` | `ghcr.io/ethanhuangcst/kb.agent-mate.ai/agent:<tag>` | `8000` | `3202` | yes via NPM path | MCP + knowledge REST |
| rag | `kb-rag` | `ghcr.io/ethanhuangcst/kb.agent-mate.ai/rag:<tag>` | `8001` | `3203` | no | RAG / index |
| qdrant | `kb-qdrant` | `qdrant/qdrant:v1.13.2` | `6333` | `127.0.0.1:6336` | no | Vectors |

Do not reuse ports taken by `hcp-engagement-agent` (3001/3200/6333), `mypoke-trade` (3002/3201/6335), or reserved `media-mkt-agent` (**3003**).

---

## 3. Images & CI

| Item | Value / status |
| --- | --- |
| Dockerfile.web | `apps/kb-web/Dockerfile` |
| Dockerfile.agent | `services/kb-agent/Dockerfile` |
| Dockerfile.rag | `services/kb-rag/Dockerfile` |
| Workflow | `.github/workflows/ghcr.yml` |
| Registry | `ghcr.io` |
| Image names | `ghcr.io/ethanhuangcst/kb.agent-mate.ai/{web,agent,rag}` |
| Tags | `latest` (default branch) + git sha + `v*` tags |
| Build notes | Admin: Node/Next; Agent/RAG: Python 3.12. Qdrant: official pin `v1.13.2`. No Playwright in prod images. |

Portainer **only pulls**; never build app images on 野草云3 for prod.  
If packages are private, Portainer registry credentials need a GHCR PAT with `read:packages` (ops key store — not in git).

---

## 4. Compose contract

| Item | Value |
| --- | --- |
| Path | **`docker-compose.prod.yml`** (repo root; canonical — do not invent a second file) |
| Local compose | `docker-compose.yml` — **dev only** (`build:` + local Postgres `:5434`) |
| App services | `image:` only — **no** `build:` for web/agent/rag |
| Network | `networks.default.external: true` + `name: portainer_network` |
| Volumes | `kb_qdrant_data`, `kb_blob_data` (prefix `kb_`) |
| Special flags | N/A |

Prefer Docker DNS (`kb-agent`, `kb-rag`, `kb-qdrant`) between services. Do **not** recreate `portainer_network`. Full file is in repo; Portainer stack should load that compose + env from §.5 / `.env.prod.example`.

---

## 5. Environment variables

Names only. Values live in Portainer / node env. Template: `specs/keys.md` → copy to `.env.prod.example` when scaffolding.

| Name | Required | Notes |
| --- | --- | --- |
| `PUBLIC_BASE_URL` | yes | `https://kb.agent-mate.ai` |
| `DATABASE_URL` | yes | External Postgres; DB name `kb_agent` only; **no password in this plan** |
| `DATABASE_HOST` / `PORT` / `USER` / `PASSWORD` / `NAME` | optional | Prefer single `DATABASE_URL` |
| `SESSION_SECRET` | yes | Admin cookie signing |
| `API_KEY_PEPPER` | yes | API key hashing; do not rotate casually after keys issued |
| `API_KEY_ENCRYPTION_SECRET` | yes (prod) | AES-GCM for `key_ciphertext` (admin view); do not rotate casually (ADR-007) |
| `BOOTSTRAP_ADMIN_EMAIL` | no | Seed admin contact email; **default `me@ethanhuang.com`**. First account is always `admin`/`admin` + forced password change |
| `RESEND_API_KEY` | yes | Invite / password-reset mail |
| `RESEND_FROM_EMAIL` | yes | Verified sender; prod default **`noreply@agent-mate.ai`** |
| `RESEND_HOST` / `RESEND_BASE_URL` | no | Defaults OK |
| `SMTP_URL` / `EMAIL_TRANSPORT` | no | Leave SMTP empty; `EMAIL_TRANSPORT=resend` |
| `QWEN_API_KEY` | yes | 百炼 MaaS / DashScope |
| `QWEN_HOST` / `QWEN_BASE_URL` | yes | Prod template: `llm-xcw25ck2bdvchrw4.cn-beijing.maas.aliyuncs.com`（见 `.env.prod.example`） |
| `QWEN_WORKSPACE` / `QWEN_REGION` | no | Prod: workspace `llm-xcw25ck2bdvchrw4`, region `cn-beijing` |
| `QWEN_CHAT_MODEL` | yes | Internal KM only（prod template: `qwen-plus`） |
| `QWEN_CHAT_MODEL_FALLBACK` | no | Optional degrade（`qwen-flash`） |
| `QWEN_EMBED_MODEL` | yes | Embedding model id（`text-embedding-v3`） |
| `EMBED_DIM` | yes | Must match embed model（`1024`） |
| `AGENT_BASE_URL` | yes (web) | In-cluster: `http://kb-agent:8000` |
| `RAG_BASE_URL` | yes (agent) | In-cluster: `http://kb-rag:8001` |
| `RAG_SERVICE_TOKEN` | yes | Shared agent↔rag token |
| `QDRANT_URL` | yes (rag) | In-cluster: `http://kb-qdrant:6333` |
| `QDRANT_COLLECTION` | yes | e.g. `kb_chunks` |
| `TAVILY_API_KEY` / `EXA_API_KEY` | no | Server-only（ADR-018）；omit until external search enabled |
| `USE_FAKE_EMBEDDER` / `USE_FAKE_KM` | yes | Production **`false`** |
| `IMAGE_TAG` | yes (Portainer) | Tag to pull |

---

## 6. Database

| Item | Value |
| --- | --- |
| Engine | **PostgreSQL** (Aliyun managed; external to compose) |
| Host | **`101.132.156.250`** |
| Port | **`5432`** |
| User | **`postgres`** (password only in Portainer / key store) |
| DB name | **`kb_agent`** (dedicated; never share with HCP / mypoke / media-mkt) |
| URL shape | `postgresql+psycopg://postgres:<PASSWORD>@101.132.156.250:5432/kb_agent` |
| Who connects | `kb-web`, `kb-agent`, `kb-rag` |
| Whitelist | Allow **野草云3** egress **`38.55.192.140`** on Aliyun PG security group / whitelist |
| Migrate | From CI/ops workstation or one-off on node: `cd packages/kb_schema && DATABASE_URL='postgresql+psycopg://…' alembic upgrade head` · or repo-root `make migrate` with `DATABASE_URL` set. **Not** auto-migrated on container boot. |
| Status (2026-08-11) | Database **created**; Alembic through **`005_import_batch`** applied from ops workstation. Re-check connectivity from 野草云3 before first Portainer deploy. |
| Verify | `psql "$DATABASE_URL" -c 'select 1'` / `select version_num from alembic_version` |
| Isolation | Never migrate or write another app’s database (`mypoke_trade_prod`, `media_marketing`, …) |

---

## 7. DNS & TLS

| Item | Value |
| --- | --- |
| Zone | `agent-mate.ai` |
| Record | `kb` → **A** `38.55.192.140` (or CNAME per Cloudflare policy) |
| Proxy | Prefer **DNS only (grey cloud)** until Let’s Encrypt succeeds on NPM; orange later if desired |
| Certificate | NPM Let’s Encrypt; domain must be exactly `kb.agent-mate.ai` |

### NPM Proxy Host(s)

**Primary host**

| Field | Value |
| --- | --- |
| Domain | `kb.agent-mate.ai` |
| Scheme | `http` |
| Forward hostname | `kb-web` |
| Forward port | `3000` (container port, **not** host port) |
| SSL | Force SSL; certificate for `kb.agent-mate.ai` |

**Path routing to agent** (required for same-origin MCP/REST; NPM Custom locations — paths fixed in `mcp-design.md`):

| Path prefix | Upstream | Notes |
| --- | --- | --- |
| `/api/v1/kb/` | `http://kb-agent:8000` | Knowledge REST |
| `/mcp` | `http://kb-agent:8000` | Streamable HTTP MCP（Cursor） |
| `/sse` | `http://kb-agent:8000` | Legacy SSE MCP（ChatBox http/sse） |
| `/messages/` | `http://kb-agent:8000` | SSE client→server posts（ChatBox） |
| `/healthz` (agent) | `http://kb-agent:8000` | Or aggregated health on web |
| `/admin` | `kb-web:3000` | Next Admin routes |

If Admin is only on web and API only on agent, do **not** point the whole host at agent.

Touch **only** this NPM host; do not edit other apps’ hosts.

### 7.1 如何编写 MCP 配置（Cursor / ChatBox）

专文语义：[`mcp-design.md`](./mcp-design.md) §7；接入指南 UI：`/guide`。  
**产品接入一律走远端 `https://kb.agent-mate.ai`**（勿在客户端配置本机 loopback）。  
**禁止**把明文 Key 写入本文件、Git 或截图；Key 仅放在本机客户端配置或密钥库。

#### 两个环境变量（勿混淆）

| 名称 | 填什么 | 谁用 |
| --- | --- | --- |
| **使用者 API Key 明文** | 管理台签发的整串（通常 `kb_live_…`） | 客户端：`Authorization: Bearer …` |
| **`API_KEY_PEPPER`** | 与 **kb-agent / 管理台 `.env` 完全相同** 的哈希盐 | **仅服务端**；**不是** API Key，客户端远程接入不填 |

校验：`sha256(API_KEY_PEPPER + raw_key) == api_keys.key_hash`。  
Pepper 与签发时不一致，或 Key 已吊销 → `UNAUTHORIZED`。

生产须用随机长盐，且 **签发 Key 之后不要改 pepper**（见 §11）。贡献者本机 stdio 调试见 [`mcp-design.md`](./mcp-design.md) 附录与 [`knowledge/ops/mcp-stdio-auth.md`](./knowledge/ops/mcp-stdio-auth.md)（**不**作为产品接入路径）。

#### A. Cursor — Streamable HTTP（远端）

| 字段 | 值 |
| --- | --- |
| Transport | Streamable HTTP / Remote MCP |
| URL | **`https://kb.agent-mate.ai/mcp`** |
| Auth | Bearer = 使用者 API Key 明文 |

不要填 `/sse`。**不要**配置 `TAVILY_API_KEY`（仅 kb-agent 服务端；ADR-018）。**不要**使用本机地址。

```json
{
  "mcpServers": {
    "kb-agent": {
      "url": "https://kb.agent-mate.ai/mcp",
      "headers": {
        "Authorization": "Bearer <paste_plaintext_user_api_key>"
      }
    }
  }
}
```

#### B. ChatBox — Remote (http/sse)

| 字段 | 值 |
| --- | --- |
| Type | **Remote (http/sse)**（不要选 Local stdio） |
| URL | **`https://kb.agent-mate.ai/sse`** |
| HTTP Header | `Authorization=Bearer <api_key>`（`NAME=VALUE` 一行） |

**不要**把 URL 写成 `/mcp`（ChatBox 会对 URL 发 SSE GET → `MCP SSE Transport Error: 404`）。  
**不要**在客户端填写 `TAVILY_API_KEY`：由 kb-agent `.env` / 生产运维配置。  
**不要**使用本机地址。  
消息通道 `POST /messages/` 由握手下发，无需手填。NPM 须同时反代 `/sse` 与 `/messages/`（上表）。

#### 对照速查

| 客户端 | 传输 | URL | 鉴权 | 客户端 Tavily |
| --- | --- | --- | --- | --- |
| Cursor / CodeBuddy | Streamable HTTP | `https://kb.agent-mate.ai/mcp` | Bearer Key | 否 |
| ChatBox | Legacy SSE | `https://kb.agent-mate.ai/sse` | Header `Authorization=Bearer …` | 否 |

工具集相同（含 `kb_internal_search` / `kb_propose_add` / `kb_confirm_add` / `kb_list_knowledge` / `kb_knowledge_summary` / `kb_external_search` 等）；与 REST 同一把使用者 Key、同一知识库。

---

## 8. Reverse-proxy extras

| Feature | Setting |
| --- | --- |
| SSE / streaming | **必开**（ChatBox `/sse`、Streamable HTTP）：`proxy_buffering off`；`proxy_read_timeout` / `proxy_send_timeout` ≥ 300s |
| WebSockets | **On** if MCP or Admin uses WS |
| Upload / batch import | Raise `client_max_body_size` for Admin batch upload (e.g. 50m–100m; confirm product limit) |
| Custom locations | Prefer NPM UI Custom Location；须含 `/mcp`、`/sse`、`/messages/`（见 §7） |

---

## 9. Smoke checklist

After DB reachable → stack healthy → DNS → NPM:

- [ ] `https://kb.agent-mate.ai/` (or redirect to `/admin`) loads without NPM Default Site
- [ ] `https://kb.agent-mate.ai/admin` — login page
- [ ] First login (seed only): `admin` / `admin` → forced password change → then Admin usable
- [ ] Invite flow: accept invite → set own password → login with full Admin access (no second forced change)
- [ ] Admin: issue API key for a display name (no rename)
- [ ] Agent health: documented `/healthz` returns OK (via public path or internal curl to `kb-agent:8000`)
- [ ] Knowledge path: Bearer key → `kb_internal_search` or `GET` knowledge search returns structured result (empty OK)
- [ ] Cursor MCP：`https://kb.agent-mate.ai/mcp` + Bearer list tools 成功
- [ ] ChatBox MCP：`https://kb.agent-mate.ai/sse` + Header `Authorization=Bearer …` Test 成功（勿用 `/mcp`）
- [ ] Propose → confirm → search again sees new knowledge (one write journey)
- [ ] Spot-check ≥1 existing app on 野草云3: `https://hcp.agent-mate.ai` or `https://mypoke.trade`

---

## 10. Isolation checklist (fill before first deploy)

- [ ] Stack name `kb-agent` free on Portainer
- [ ] Container names `kb-web` / `kb-agent` / `kb-rag` / `kb-qdrant` free
- [ ] Volume names `kb_qdrant_data` / `kb_blob_data` free
- [ ] Host ports **3006 / 3202 / 3203 / 127.0.0.1:6336** free per `hk_vps_3_resources.md`
- [ ] Domain `kb.agent-mate.ai` not used by another NPM host
- [ ] DB name `kb_agent` not used by another product
- [ ] Will **not** recreate `portainer_network`
- [ ] Will **not** edit other NPM hosts / DNS records
- [ ] Post-deploy spot-check of ≥1 existing app planned (`hcp.agent-mate.ai` or `mypoke.trade`)

---

## 11. Ops caveats (app-specific)

- **First admin:** on empty DB, seed **`admin` / `admin`** with default email **`me@ethanhuang.com`** (`BOOTSTRAP_ADMIN_EMAIL`) and `must_change_password`; seed login must change password before Key/invite ops. Invite/reset self-chosen passwords set `must_change_password=false` (no second forced change). Thereafter invite-only (R2). Confirm Resend domain/sender for invite/reset links under `https://kb.agent-mate.ai/...`.
- **Default password:** change immediately in prod smoke; do not leave `admin`/`admin` after go-live.
- **API keys:** issue/reissue store `key_hash` + `key_ciphertext`; admin may **view** plaintext again (ADR-007). Keep `API_KEY_PEPPER` and `API_KEY_ENCRYPTION_SECRET` stable after production keys exist.
- **Local stack:** prefer `make up-daemon` when driving services from Cursor Agent (ADR-008; `knowledge/ops/local-apps-keep-dying.md`).
- **LLM boundary:** DashScope Qwen is **internal KM only**; callers bring their own LLM (Cursor/ChatBox/App).
- **No Gist storage;** originals on `kb_blob_data`; metadata Postgres; vectors Qdrant.
- **Image pull:** Portainer “Update stack” often does **not** re-pull `latest` — use Recreate + Pull or pin sha tags.
- **NPM domain:** must match DNS exactly (`kb.agent-mate.ai`).
- **NPM upstream:** container name + **container** port; host ports are debug-only.
- **Do not** build images on the VPS for prod; GHCR only.
- **Secrets:** rotate anything pasted into chat or Portainer screenshots; never commit `specs/.env`.
- Entrypoint / Playwright / Xvfb: **N/A** for baseline kb-agent prod images (no headed crawler).

---

## 12. Release step map (for release-bot)

| Step | This plan’s answer |
| --- | --- |
| 0 Preflight | Repo `ethanhuangcst/kb.agent-mate.ai`; stack `kb-agent`; domain `kb.agent-mate.ai`; images `…/web|agent|rag`; Qdrant pin `v1.13.2`; host ports 3006/3202/3203/6336 |
| 0b Isolation | §10 + live inventory (`hcp` / `mypoke` / reserved media **3003**) |
| 1 Compose | Repo-root **`docker-compose.prod.yml`** |
| 2 CI → GHCR | **`.github/workflows/ghcr.yml`** |
| 3 Env | `.env.prod.example` + §5; secrets only in Portainer |
| 4 DB | Aliyun `101.132.156.250:5432` / `kb_agent`; `alembic upgrade head` (§6) |
| 5 Portainer | Stack `kb-agent`; volumes `kb_qdrant_data` / `kb_blob_data` |
| 6 DNS | `kb` on `agent-mate.ai` → `38.55.192.140` |
| 7 NPM | §7–§8（`/mcp` `/sse` `/messages/`；客户端 §7.1） |
| 8 Smoke | §9（含 Cursor `…/mcp` / ChatBox `…/sse`） |

**Order:** DB reachable from node → pull/deploy containers → DNS → NPM → smoke. Do not expect public HTTPS before containers are healthy.
