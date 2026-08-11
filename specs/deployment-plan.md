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
| App repo | `<GITHUB_OWNER>/<GITHUB_REPO>` *(confirm before first deploy; local folder today: `knowledge.base`)* |
| Default git ref | `main` (or release tag policy once tags exist) |
| Target node | **野草云3** · public IP **`38.55.192.140`** (confirm in release-bot `specs/hk_vps_3_resources.md` if stale) |
| Stack name | `kb-agent` |
| App slug | `kb` |
| Public domain | **`kb.agent-mate.ai`** (exact spelling; typos break SNI) |
| `PUBLIC_BASE_URL` | `https://kb.agent-mate.ai` |
| Production path | **Portainer + GHCR + Nginx Proxy Manager** on 野草云3 — **not** Caddy/PM2 on bare metal |

### Placeholders still owned by ops / preflight

| Placeholder | Meaning |
| --- | --- |
| `<GITHUB_OWNER>` / `<GITHUB_REPO>` | GHCR image path owner/repo |
| `<HOST_PORT_WEB>` / `<HOST_PORT_AGENT>` / `<HOST_PORT_RAG>` / `<HOST_PORT_QDRANT>` | Free host ports on 野草云3 (debug only; NPM uses container ports) |
| `<IMAGE_TAG>` | Usually `latest` or git sha |
| `<DB_NAME>` | Dedicated Postgres database, proposed: **`kb_agent`** |
| `<EXISTING_APPS>` | Live list from node inventory for spot-check |

### Blockers before first release job (dev still incomplete)

Mark these **done in app repo** before asking release-bot to deploy:

- [ ] `docker/Dockerfile.web` (Next.js Admin)
- [ ] `docker/Dockerfile.agent` (FastAPI MCP + knowledge REST)
- [ ] `docker/Dockerfile.rag` (FastAPI RAG)
- [ ] `docker-compose.prod.yml` (image-only; external `portainer_network`)
- [ ] `.github/workflows/ghcr.yml` (or equivalent) builds/pushes three images
- [x] `.env.prod.example` (names only, no secrets) — 仓库根目录
- [ ] Migrate command or boot-migrate documented
- [ ] Exact public paths for MCP + Admin + health confirmed in code

---

## 1. Architecture (runtime)

```text
[Browser / Cursor / ChatBox / HCP]
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

- **PostgreSQL** — AliCloud (or other) managed/VPS Postgres; dedicated DB `<DB_NAME>` = `kb_agent`
- DashScope, Resend, optional search APIs — SaaS egress only

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
| web | `kb-web` | `ghcr.io/<GITHUB_OWNER>/<GITHUB_REPO>/web:<tag>` | `3000` | `<HOST_PORT_WEB>` | yes via NPM | Admin UI (+ optional BFF) |
| agent | `kb-agent` | `ghcr.io/<GITHUB_OWNER>/<GITHUB_REPO>/agent:<tag>` | `8000` | `<HOST_PORT_AGENT>` | yes via NPM path | MCP + knowledge REST |
| rag | `kb-rag` | `ghcr.io/<GITHUB_OWNER>/<GITHUB_REPO>/rag:<tag>` | `8001` | `<HOST_PORT_RAG>` | no | RAG / index |
| qdrant | `kb-qdrant` | `qdrant/qdrant:<pin-version>` | `6333` | `<HOST_PORT_QDRANT>` optional | no | Vectors |

Pin Qdrant image tag at first deploy (do not float unpinned `latest` forever without a note).

Reserve host ports from release-bot `specs/hk_vps_3_resources.md`; do not reuse ports taken by `hcp-engagement-agent`, `mypoke-trade`, `media-mkt-agent`, etc.

---

## 3. Images & CI

| Item | Value / status |
| --- | --- |
| Dockerfile.web | `docker/Dockerfile.web` — **blocker until created** |
| Dockerfile.agent | `docker/Dockerfile.agent` — **blocker** |
| Dockerfile.rag | `docker/Dockerfile.rag` — **blocker** |
| Workflow | `.github/workflows/ghcr.yml` — **blocker** |
| Registry | `ghcr.io` |
| Image names | `.../web`, `.../agent`, `.../rag` |
| Tags | `latest` + git sha (sha preferred for rollback) |
| Build notes | Admin: Node/Next 16; use npmmirror when building in CN/HK runners if needed. Agent/RAG: Python 3.12. Qdrant: pull official image (no app build). No Playwright browsers required in **prod** runtime images (Playwright is for CI/E2E only). |

Portainer **only pulls**; never build app images on 野草云3 for prod.

---

## 4. Compose contract

| Item | Value |
| --- | --- |
| Path | `docker-compose.prod.yml` (repo root or `deploy/` — **blocker until created**) |
| App services | `image:` only — **no** `build:` for web/agent/rag |
| Network | `networks.default.external: true` + `name: portainer_network` |
| Volumes | `kb_qdrant_data`, `kb_blob_data` (prefix `kb_`) |
| Special flags | N/A unless Chromium crawler added later (not in baseline) |

### Suggested compose skeleton (specialize when Dockerfiles exist)

```yaml
name: kb-agent

services:
  web:
    image: ghcr.io/<GITHUB_OWNER>/<GITHUB_REPO>/web:${IMAGE_TAG:-latest}
    container_name: kb-web
    restart: unless-stopped
    ports:
      - "<HOST_PORT_WEB>:3000"
    environment:
      NODE_ENV: production
      PORT: "3000"
      HOSTNAME: "0.0.0.0"
      PUBLIC_BASE_URL: ${PUBLIC_BASE_URL:-https://kb.agent-mate.ai}
      DATABASE_URL: ${DATABASE_URL:?set DATABASE_URL}
      SESSION_SECRET: ${SESSION_SECRET:?set SESSION_SECRET}
      API_KEY_PEPPER: ${API_KEY_PEPPER:?set API_KEY_PEPPER}
      API_KEY_ENCRYPTION_SECRET: ${API_KEY_ENCRYPTION_SECRET:?set API_KEY_ENCRYPTION_SECRET}
      RESEND_API_KEY: ${RESEND_API_KEY:?set RESEND_API_KEY}
      AGENT_BASE_URL: ${AGENT_BASE_URL:-http://kb-agent:8000}
      RAG_BASE_URL: ${RAG_BASE_URL:-http://kb-rag:8001}
      BOOTSTRAP_ADMIN_EMAIL: ${BOOTSTRAP_ADMIN_EMAIL:-me@ethanhuang.com}
    networks:
      - default

  agent:
    image: ghcr.io/<GITHUB_OWNER>/<GITHUB_REPO>/agent:${IMAGE_TAG:-latest}
    container_name: kb-agent
    restart: unless-stopped
    ports:
      - "<HOST_PORT_AGENT>:8000"
    volumes:
      - kb_blob_data:/data/kb
    environment:
      PUBLIC_BASE_URL: ${PUBLIC_BASE_URL:-https://kb.agent-mate.ai}
      DATABASE_URL: ${DATABASE_URL:?set DATABASE_URL}
      RAG_BASE_URL: ${RAG_BASE_URL:-http://kb-rag:8001}
      API_KEY_PEPPER: ${API_KEY_PEPPER:?set API_KEY_PEPPER}
      QWEN_API_KEY: ${QWEN_API_KEY:?set QWEN_API_KEY}
      QWEN_BASE_URL: ${QWEN_BASE_URL:-https://dashscope.aliyuncs.com/compatible-mode/v1}
      QWEN_CHAT_MODEL: ${QWEN_CHAT_MODEL:?set QWEN_CHAT_MODEL}
      QWEN_CHAT_MODEL_FALLBACK: ${QWEN_CHAT_MODEL_FALLBACK:-}
      # optional: TAVILY_API_KEY, EXA_API_KEY
    networks:
      - default

  rag:
    image: ghcr.io/<GITHUB_OWNER>/<GITHUB_REPO>/rag:${IMAGE_TAG:-latest}
    container_name: kb-rag
    restart: unless-stopped
    ports:
      - "<HOST_PORT_RAG>:8001"
    volumes:
      - kb_blob_data:/data/kb
    environment:
      DATABASE_URL: ${DATABASE_URL:?set DATABASE_URL}
      QDRANT_URL: ${QDRANT_URL:-http://kb-qdrant:6333}
      QDRANT_COLLECTION: ${QDRANT_COLLECTION:-kb_chunks}
      QWEN_API_KEY: ${QWEN_API_KEY:?set QWEN_API_KEY}
      QWEN_BASE_URL: ${QWEN_BASE_URL:-https://dashscope.aliyuncs.com/compatible-mode/v1}
      QWEN_EMBED_MODEL: ${QWEN_EMBED_MODEL:?set QWEN_EMBED_MODEL}
      EMBED_DIM: ${EMBED_DIM:?set EMBED_DIM}
    networks:
      - default

  qdrant:
    image: qdrant/qdrant:v1.13.2
    container_name: kb-qdrant
    restart: unless-stopped
    ports:
      - "<HOST_PORT_QDRANT>:6333"
    volumes:
      - kb_qdrant_data:/qdrant/storage
    networks:
      - default

volumes:
  kb_qdrant_data:
  kb_blob_data:

networks:
  default:
    external: true
    name: portainer_network
```

Prefer Docker DNS (`kb-agent`, `kb-rag`, `kb-qdrant`) between services. Do **not** recreate `portainer_network`.

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
| `RESEND_HOST` / `RESEND_BASE_URL` | no | Defaults OK |
| `SMTP_URL` | no | Leave empty if using Resend |
| `QWEN_API_KEY` | yes | DashScope |
| `QWEN_HOST` / `QWEN_BASE_URL` | yes | Compatible-mode base URL |
| `QWEN_WORKSPACE` / `QWEN_REGION` | no | Per DashScope account |
| `QWEN_CHAT_MODEL` | yes | Internal KM only |
| `QWEN_CHAT_MODEL_FALLBACK` | no | Optional degrade |
| `QWEN_EMBED_MODEL` | yes | Embedding model id |
| `EMBED_DIM` | yes | Must match embed model |
| `AGENT_BASE_URL` | yes (web) | In-cluster: `http://kb-agent:8000` |
| `RAG_BASE_URL` | yes (agent) | In-cluster: `http://kb-rag:8001` |
| `QDRANT_URL` | yes (rag) | In-cluster: `http://kb-qdrant:6333` |
| `QDRANT_COLLECTION` | yes | e.g. `kb_chunks` |
| `TAVILY_API_KEY` / `EXA_API_KEY` | no | External source adapters; omit until enabled |
| `IMAGE_TAG` | yes (Portainer) | Tag to pull |

---

## 6. Database

| Item | Value |
| --- | --- |
| Engine | **PostgreSQL 17+** (external) |
| Host role | AliCloud / other VPS Postgres — **outside** this compose |
| DB name | **`kb_agent`** (dedicated; never share with HCP / mypoke / media-mkt) |
| Who connects | `kb-web` (if BFF), `kb-agent`, `kb-rag` |
| Migrate | TBD in app repo: prefer documented one-shot `alembic upgrade head` / `make migrate` **or** “schemas applied by app on boot” — fill exact command before release |
| Verify | From a one-off container on `portainer_network` or node: `psql "$DATABASE_URL" -c 'select 1'` |
| Isolation | Never migrate or write another app’s database |

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
**禁止**把明文 Key 写入本文件、Git 或截图；Key 仅放在本机客户端配置或密钥库。

#### 两个环境变量（勿混淆）

| 名称 | 填什么 | 谁用 |
| --- | --- | --- |
| **使用者 API Key 明文** | 管理台签发的整串（通常 `kb_live_…`） | 客户端：`Authorization: Bearer …` 或 stdio 的 `KB_API_KEY` |
| **`API_KEY_PEPPER`** | 与 **kb-agent / 管理台 `.env` 完全相同** 的哈希盐 | 仅服务端与 **本地 stdio** 进程；**不是** API Key |

校验：`sha256(API_KEY_PEPPER + raw_key) == api_keys.key_hash`。  
Pepper 与签发时不一致，或 Key 已吊销 → `UNAUTHORIZED`。

本地默认 pepper（仅开发）：与仓库 `.env` / `.env.example` 一致，常见为 `dev-api-key-pepper-change-me`。生产须用随机长盐，且 **签发 Key 之后不要改 pepper**（见 §11）。

#### A. Cursor — Streamable HTTP（远程，推荐手测）

| 字段 | 本地 | 生产 |
| --- | --- | --- |
| Transport | Streamable HTTP / Remote MCP | 同左 |
| URL | `http://127.0.0.1:8000/mcp` | `https://kb.agent-mate.ai/mcp` |
| Auth | Bearer = 使用者 API Key 明文 | 同左 |

不要填 `/sse`。

#### B. Cursor — stdio（本机 spawn，`~/.cursor/mcp.json`）

适合本机已用 **`make up-daemon`**（或系统终端 `make up`）拉起依赖与 agent 时；进程入口：`python -m app.mcp_stdio`。

```json
{
  "mcpServers": {
    "kb-agent": {
      "command": "<REPO>/.venv/bin/python",
      "args": ["-m", "app.mcp_stdio"],
      "cwd": "<REPO>/services/kb-agent",
      "env": {
        "KB_API_KEY": "<paste_plaintext_user_api_key>",
        "API_KEY_PEPPER": "<same_as_agent_and_admin_dotenv>",
        "DATABASE_URL": "postgresql+psycopg://kb:<password>@127.0.0.1:5434/kb_agent",
        "RAG_BASE_URL": "http://127.0.0.1:8001",
        "RAG_SERVICE_TOKEN": "<same_as_dotenv>",
        "BLOB_ROOT": "<REPO>/data/blob",
        "PYTHONPATH": "<REPO>/services/kb-agent"
      }
    }
  }
}
```

编写要点：

1. **`KB_API_KEY`** = 管理台签发的使用者 Key 明文（不要加 `Bearer ` 前缀）。  
2. **`API_KEY_PEPPER`** = 与根目录 `.env` 中 `API_KEY_PEPPER` **逐字相同**（勿把 Key 误填进 pepper）。  
3. `DATABASE_URL` / `RAG_*` / `BLOB_ROOT` 指向本机真实栈。  
4. 改 Key 或 pepper 后在 Cursor **重载 MCP**。  
5. 日志若出现 `kb-agent mcp stdio: auth failed (UNAUTHORIZED)`：先查 Key 是否 active，再查 pepper 是否与签发环境一致。

#### C. ChatBox — Remote (http/sse)

| 字段 | 本地 | 生产 |
| --- | --- | --- |
| Type | **Remote (http/sse)**（不要选 Local stdio） | 同左 |
| URL | `http://127.0.0.1:8000/sse` | `https://kb.agent-mate.ai/sse` |
| HTTP Header | `Authorization=Bearer <api_key>`（`NAME=VALUE` 一行） | 同左 |

**不要**把 URL 写成 `/mcp`（ChatBox 会对 URL 发 SSE GET → `MCP SSE Transport Error: 404`）。  
消息通道 `POST /messages/` 由握手下发，无需手填。NPM 须同时反代 `/sse` 与 `/messages/`（上表）。

#### 对照速查

| 客户端 | 传输 | URL / 入口 | 鉴权 |
| --- | --- | --- | --- |
| Cursor（远程） | Streamable HTTP | `…/mcp` | Bearer Key |
| Cursor（本地 stdio） | stdio → `app.mcp_stdio` | `mcp.json` command/env | `KB_API_KEY` + 正确 `API_KEY_PEPPER` |
| ChatBox | Legacy SSE | `…/sse` | Header `Authorization=Bearer …` |

工具集相同（含 `kb_internal_search` / `kb_propose_add` / `kb_confirm_add` / `kb_list_knowledge` / `kb_knowledge_summary`）；与 REST 同一把使用者 Key、同一知识库。

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
- [ ] Cursor MCP：`…/mcp` + Bearer（或本地 stdio + 正确 `KB_API_KEY` / `API_KEY_PEPPER`）list tools 成功
- [ ] ChatBox MCP：`…/sse` + Header `Authorization=Bearer …` Test 成功（勿用 `/mcp`）
- [ ] Propose → confirm → search again sees new knowledge (one write journey)
- [ ] Spot-check ≥1 existing app on 野草云3, e.g. `https://hcp.agent-mate.ai` (or current inventory list `<EXISTING_APPS>`)

---

## 10. Isolation checklist (fill before first deploy)

- [ ] Stack name `kb-agent` free on Portainer
- [ ] Container names `kb-web` / `kb-agent` / `kb-rag` / `kb-qdrant` free
- [ ] Volume names `kb_qdrant_data` / `kb_blob_data` free
- [ ] Host ports `<HOST_PORT_*>` free per `hk_vps_3_resources.md`
- [ ] Domain `kb.agent-mate.ai` not used by another NPM host
- [ ] DB name `kb_agent` not used by another product
- [ ] Will **not** recreate `portainer_network`
- [ ] Will **not** edit other NPM hosts / DNS records
- [ ] Post-deploy spot-check of ≥1 existing app planned

---

## 11. Ops caveats (app-specific)

- **First admin:** on empty DB, seed **`admin` / `admin`** with default email **`me@ethanhuang.com`** (`BOOTSTRAP_ADMIN_EMAIL`) and `must_change_password`; seed login must change password before Key/invite ops. Invite/reset self-chosen passwords set `must_change_password=false` (no second forced change). Thereafter invite-only (R2). Confirm Resend domain/sender for invite/reset links under `https://kb.agent-mate.ai/...`.
- **Default password:** change immediately in prod smoke; do not leave `admin`/`admin` after go-live.
- **API keys:** issue/reissue store `key_hash` + `key_ciphertext`; admin may **view** plaintext again (ADR-007). Keep `API_KEY_PEPPER` and `API_KEY_ENCRYPTION_SECRET` stable after production keys exist.
- **Local stack:** prefer `make up-daemon` when driving services from Cursor Agent (ADR-008; `knowledge/ops/local-apps-keep-dying.md`).
- **LLM boundary:** DashScope Qwen is **internal KM only**; callers bring their own LLM (Cursor/ChatBox/HCP).
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
| 0 Preflight | Repo/ref, stack `kb-agent`, domain `kb.agent-mate.ai`, 3 app images + Qdrant, external Postgres `kb_agent` |
| 0b Isolation | §10 + live inventory |
| 1 Compose | `docker-compose.prod.yml` when present; skeleton in §4 |
| 2 CI → GHCR | `.github/workflows/ghcr.yml` when present |
| 3 Env | §5 names; values from ops key store |
| 4 DB | External Postgres; migrate command TBD in app |
| 5 Portainer | Stack `kb-agent`; volumes in §4 |
| 6 DNS | `kb` on `agent-mate.ai` → `38.55.192.140` |
| 7 NPM | §7–§8（含 `/mcp` `/sse` `/messages/`；客户端写法 §7.1） |
| 8 Smoke | §9（含 Cursor / ChatBox MCP 手测项） |

**Order:** DB reachable → pull/deploy containers → DNS → NPM → smoke. Do not expect public HTTPS before containers are healthy.
