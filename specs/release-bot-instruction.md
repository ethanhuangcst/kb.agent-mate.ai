# New project instruction — deploy via release-bot to 野草云3

**Audience:** authors of a **new application repository** that will later be deployed with **release-bot**.  
**Output you must produce in the app repo:** `deployment-plan.md` (path may be `specs/deployment-plan.md` or repo-root `deployment-plan.md`).  
**Consumer:** when starting a release job, the operator feeds that file into release-bot as the primary input (together with secrets held outside git).

This document describes the **target architecture and steps** for the default edge node **野草云3**. Write your `deployment-plan.md` so an agent that only knows release-bot’s handbook can fill placeholders and run the semi-auto checklist without inventing a second deploy style.

### This repository (kb-agent)

| Field | Value |
| --- | --- |
| GitHub | **`ethanhuangcst/kb.agent-mate.ai`** |
| GHCR | `ghcr.io/ethanhuangcst/kb.agent-mate.ai/{web,agent,rag}` |
| Public domain | **`kb.agent-mate.ai`** |
| `PUBLIC_BASE_URL` | `https://kb.agent-mate.ai` |
| Target node | 野草云3 · **`38.55.192.140`** |
| Prod compose | `docker-compose.prod.yml` |
| Env template | `.env.prod.example` |
| External Postgres | Aliyun **`101.132.156.250:5432` / `kb_agent`** |
| Host ports | web **3006** · agent **3202** · rag **3203** · qdrant **127.0.0.1:6336** |
| Related apps on same zone | `hcp.agent-mate.ai`, `mypoke.trade` — isolate stack / ports / NPM host |
| Canonical plan | [`specs/deployment-plan.md`](./deployment-plan.md) |

---

## 1. What release-bot is (and is not)

| Is | Is not |
| --- | --- |
| A **conversational guide** that walks ops one step at a time | Unattended full CI/CD that SSHs and mutates the node alone |
| Driven by local handbook `release-bot/knowledge/` + your `deployment-plan.md` | A place to store production passwords |
| Expects **GHCR images** built in GitHub Actions; Portainer **only pulls** | Building app images on the VPS or on the operator laptop for prod |

Secrets stay in local key stores / Portainer env / node `.env`. Never put passwords, PATs, or API keys in `deployment-plan.md` or in release-bot git.

---

## 2. Target runtime architecture (野草云3)

```text
[Browser]
    → Cloudflare DNS (optional orange cloud later)
        → Nginx Proxy Manager on 野草云3 (:80 / :443)
            → Docker container(s) on shared network `portainer_network`
                → outbound to external DB / LLM / third parties
```

| Layer | How it works on 野草云3 |
| --- | --- |
| Node | **野草云3** · public IP **`38.55.192.140`** (confirm in `specs/hk_vps_3_resources.md` if stale) |
| Containers | Docker; managed in **Portainer** `https://portainer.agent-mate.ai/` |
| Shared network | **`portainer_network`** — already exists; **never delete or recreate** |
| TLS / HTTP entry | **Nginx Proxy Manager** `https://nginx.agent-mate.ai/` |
| Images | **`ghcr.io/<owner>/<repo>/<service>:<tag>`** from GitHub Actions |
| Primary DB | Usually **outside** the app compose (AliCloud / other VPS Postgres or MySQL) |
| Optional sidecars | Agent, RAG, pgvector, Qdrant — only if the product needs them; still on the same external network |

### Multi-app coexistence (hard)

The node already runs other stacks (examples historically: `hcp-engagement-agent`, `mypoke-trade`, `media-mkt-agent`). Your plan must:

- Use a unique **Stack name**, **container names**, **volume names**, **host ports**, **domain**, and preferably a dedicated **DB name**
- Touch **only** your NPM Proxy Host and your DNS records
- After go-live, require a **spot-check of ≥1 existing app**

Canonical isolation rules live in release-bot `knowledge/09-isolation-safety.md`.

### Port mapping convention

| Where | Which port |
| --- | --- |
| Compose `ports:` | `"<HOST_PORT>:<CONTAINER_PORT>"` — host port must be free on 野草云3 |
| NPM Forward Port | **container listen port** (e.g. Next often `3000`), **not** the host-mapped port |
| Forward Hostname | Prefer **Docker DNS name** = `container_name` on `portainer_network` (e.g. `myapp-web`) |

Reserve host ports by reading the current resource sheet (`release-bot/specs/hk_vps_3_resources.md`) or asking ops; do not reuse `3001` / `3002` / `3003` / … already taken.

---

## 3. Release flow your plan must align with

release-bot follows `knowledge/03-semi-auto-release.md`. Your `deployment-plan.md` should make each step **answerable without guessing**:

| Step | Ops action | What your plan must specify |
| --- | --- | --- |
| 0 | Preflight | Repo, default branch/tag, services, images, ports, domain, DB need |
| 0b | Isolation gate | Proposed `STACK_NAME` / `APP_SLUG` / ports / domain; conflict notes |
| 1 | Compose in **app** repo | Path to prod compose; `image:` only (no local `build:` for app services); `external` network |
| 2 | CI → GHCR | Workflow path; image names; tags (`latest` + sha if any) |
| 3 | Env on node / Portainer | Env **names** (not secret values); which are required |
| 4 | DB connectivity + migrate | How to verify DB; migrate command/path or “no migrate” |
| 5 | Portainer deploy | Stack name; compose snippet or file; volume mounts |
| 6 | Cloudflare / DNS | Zone; record type; target IP; grey/orange guidance |
| 7 | NPM | Domain spelling; upstream host:port; SSL; SSE/WebSocket extras |
| 8 | Smoke | URLs/paths to hit; existing-app spot-check list |

**Order reminder:** DB reachable → pull/deploy containers → DNS → NPM → smoke. Do not expect public HTTPS before the container is healthy.

---

## 4. What the app repository must contain

Before a release job starts, the **application** repo should already have:

1. **`deployment-plan.md`** (this instruction’s deliverable)  
2. **Production Dockerfile(s)** under something like `docker/Dockerfile.*`  
3. **`docker-compose.prod.yml`** (or equivalent) with:
   - `image: ghcr.io/...` only for app services  
   - `networks.default.external: true` + `name: portainer_network`  
   - Stable `container_name` / volumes prefixed with an app slug  
4. **GitHub Actions** workflow that builds and pushes to GHCR on the agreed branch/tag  
5. **`.env.prod.example`** (or equivalent) listing every required variable — **no real secrets**  
6. If needed: migrate docs/commands, Playwright/xvfb notes, SSE proxy notes, first-login runbook  

release-bot will **not** invent a second architecture. If your local docs say “PM2 on bare metal” but the platform standard is Portainer+GHCR, **`deployment-plan.md` must state the Portainer path as the production path** (or explicitly document an approved exception).

---

## 5. `deployment-plan.md` — required sections

Use the following outline. Keep placeholders where values are environment-specific; fill concrete values when known.

```markdown
# Deployment plan — <PRODUCT_NAME>

## 0. Meta
- App repo: `<GITHUB_OWNER>/<GITHUB_REPO>`
- Default git ref for first deploy: `main` (or tag policy)
- Target node: 野草云3 (`38.55.192.140`) unless ops overrides
- Stack name: `<STACK_NAME>`
- App slug: `<APP_SLUG>`
- Public domain: `<APP_DOMAIN>`  (spell carefully; typos break SNI)

## 1. Architecture (runtime)
- Diagram or bullet list: browser → NPM → which containers → DB / APIs
- Process model: single process vs multi-service
- What is **in-process** vs separate container
- What must be persistent (paths → volume names)

## 2. Services table
| Service | container_name | Image | Container port | Host port | Public? | Role |
| --- | --- | --- | --- | --- | --- | --- |
| web | `<APP_SLUG>-web` | `ghcr.io/.../web` | 3000 | `<HOST_PORT>` | yes via NPM | ... |

## 3. Images & CI
- Dockerfile path(s)
- Workflow path: `.github/workflows/...`
- Registry: `ghcr.io`
- Tags: `latest` and/or git sha
- Build notes (Node version, monorepo workspaces, Playwright install, mirrors)

## 4. Compose contract
- Path to prod compose file
- Confirms: no app `build:`; external `portainer_network`
- Volumes and bind mounts
- `shm_size` / special Docker flags if required (e.g. Chromium)

## 5. Environment variables
| Name | Required | Notes |
| --- | --- | --- |
| `DATABASE_URL` | yes | DB name `<DB_NAME>` only; password not in this file |
| `APP_URL` | yes | `https://<APP_DOMAIN>` |

## 6. Database
- Engine / host role (external AliCloud Postgres, etc.)
- `<DB_NAME>` / schema
- Migrate: command or “schemas applied by app on boot” / “manual once”
- Isolation: never migrate another app’s database

## 7. DNS & TLS
- Zone and record (`A` / `CNAME`)
- Prefer grey cloud until Let’s Encrypt succeeds on NPM
- NPM: Forward `http://<container_name>:<CONTAINER_PORT>`
- Force SSL; certificate domain must **exactly** match `<APP_DOMAIN>`

## 8. Reverse-proxy extras
- WebSockets: on/off
- SSE: `proxy_buffering off` + long timeouts (if streaming UI/agent)
- Custom locations only if Advanced config unavailable

## 9. Smoke checklist
- [ ] `https://<APP_DOMAIN>/`
- [ ] Health/login paths (list exact paths)
- [ ] Critical user journey (one sentence)
- [ ] Spot-check ≥1 existing app on 野草云3

## 10. Isolation checklist (fill before first deploy)
- [ ] Stack / ports / domain / DB name conflict check vs current node inventory
- [ ] Will not recreate `portainer_network`
- [ ] Will not edit other NPM hosts

## 11. Ops caveats (app-specific)
- First login / QR / seed data
- Headful browser / Xvfb / `PLAYWRIGHT_BROWSERS_PATH` if crawling
- Do not “Update stack” without re-pulling when entrypoint/image fixes are in flight
```

---

## 6. Compose skeleton (copy into app repo, then specialize)

```yaml
name: <STACK_NAME>

services:
  web:
    image: ghcr.io/<GITHUB_OWNER>/<GITHUB_REPO>/web:${IMAGE_TAG:-latest}
    container_name: <APP_SLUG>-web
    restart: unless-stopped
    ports:
      - "<HOST_PORT>:3000"
    volumes:
      - <APP_SLUG>_data:/data
    environment:
      NODE_ENV: production
      PORT: "3000"
      HOSTNAME: "0.0.0.0"
      DATABASE_URL: ${DATABASE_URL:?set DATABASE_URL}
      APP_URL: ${APP_URL:-https://<APP_DOMAIN>}
    networks:
      - default

volumes:
  <APP_SLUG>_data:

networks:
  default:
    external: true
    name: portainer_network
```

Add more services only if the architecture section says they are separate containers. Prefer Docker DNS names between services on `portainer_network`.

---

## 7. Lessons learned (bake into the plan when relevant)

These failures already happened on 野草云3; call them out in §11 if your app is affected:

| Topic | Guidance |
| --- | --- |
| Image pull | Portainer “Update” often **does not** re-pull `latest`; document Recreate + Pull or delete local tag |
| NPM domain | Domain string must match DNS **exactly** (`media.mkt-agent.ai` ≠ `media.mkt-agents.ai`). Wrong name → Default Site / TLS `unrecognized_name` |
| NPM upstream | Use container name + **container** port; host port is for debugging only |
| Playwright in Docker | Install browsers to a path the runtime user can read (`PLAYWRIGHT_BROWSERS_PATH`); `appuser` HOME must be writable; headed QR needs Xvfb when `CRAWLER_HEADLESS=false` |
| Entrypoint | Prefer starting `Xvfb` then `exec` the app; fragile `xvfb-run -s "..."` quoting has failed under Docker |
| Health checks | “chromium_available” that only checks the Playwright JS module is not enough; smoke real login/crawl |
| Secrets | Rotate anything pasted into chat or shown in Portainer screenshots |

---

## 8. How release-bot will use your file

When an operator starts a new job:

1. Copies or links `deployment-plan.md` into `release-bot/Release-jobs/<job>/` (or points the agent at the app repo path)  
2. release-bot collects any missing placeholders and the live `<EXISTING_APPS>` list  
3. Runs isolation gate → CI verify → Portainer → DNS → NPM → smoke  
4. Writes session notes under `release-bot/Release-jobs/<job>/` / `specs/sessions/` — **without** copying secrets into git  

Your plan should be **stable enough** that Step 0 questions are mostly “confirm” rather than “design from scratch”.

---

## 9. Definition of done for *writing* `deployment-plan.md`

- [ ] All sections in §5 present (mark N/A explicitly if unused)  
- [ ] Services/ports/images/domain/stack/slug unambiguous  
- [ ] Compose + CI paths exist in the app repo (or listed as blockers)  
- [ ] Env table lists names only; `.env.prod.example` exists  
- [ ] Isolation and smoke checklists are concrete  
- [ ] No passwords, tokens, or private keys in the file  
- [ ] Production path is Portainer + GHCR + NPM on 野草云3 (or an explicit approved exception)

---

## 10. Pointers inside release-bot

| Doc | Use when |
| --- | --- |
| `knowledge/variables.md` | Placeholder vocabulary |
| `knowledge/03-semi-auto-release.md` | Step sequence |
| `knowledge/09-isolation-safety.md` | Multi-app safety |
| `knowledge/04-portainer.md` / `05-nginx-proxy-manager.md` / `08-cloudflare.md` | Tool details |
| `specs/hk_vps_3_resources.md` | Current ports/domains/stacks on 野草云3 (refresh if old) |
| `.claude/skills/release-guide/SKILL.md` | Agent conversational protocol |

When in doubt, prefer the handbook’s placeholders and this node’s shared stack over inventing a new reverse-proxy or registry.
