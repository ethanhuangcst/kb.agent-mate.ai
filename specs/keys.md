# 密钥与连接清单（模板）

本地复制为已 gitignore 的填写副本（如 `specs/keys.local.md` 或项目根 `.env.local`），**勿将填好密钥的文件提交仓库**。变量约定见 `specs/architecture.md` → **tech-stack** → 环境变量。

面向中国大陆 / 香港：LLM 用 **DashScope（通义千问）**，不用 `api.openai.com`。

---

```env
# ── QWEN（通义 / 百炼 MaaS；示例为 cn-beijing 专属实例形态）──
QWEN_API_KEY=
QWEN_HOST=
QWEN_BASE_URL=
QWEN_NATIVE_BASE_URL=
QWEN_WORKSPACE=
QWEN_REGION=
QWEN_CHAT_MODEL=
QWEN_CHAT_MODEL_FALLBACK=
QWEN_VL_MODEL=
QWEN_IMAGE_MODEL=
QWEN_EMBED_MODEL=
EMBED_DIM=
QWEN_KEY_MGMT_SITE=

# ── 邮件 / Resend ───────────────────────────────────────────
RESEND_API_KEY=
RESEND_HOST=api.resend.com
RESEND_BASE_URL=https://api.resend.com
RESEND_KEY_MGMT_SITE=https://resend.com/api-keys
SMTP_URL=

# ── PostgreSQL（应用元数据）──────────────────────────────────
DATABASE_HOST=
DATABASE_PORT=5432
DATABASE_USER=
DATABASE_PASSWORD=
DATABASE_NAME=
DATABASE_URL=postgresql://USER:PASSWORD@HOST:PORT/NAME

# ── Qdrant ──────────────────────────────────────────────────
QDRANT_URL=
QDRANT_COLLECTION=

# ── Embedder（MVP-2 闭环门禁须 false + 真 DashScope embed）──
# USE_FAKE_EMBEDDER=true   # 仅 CI/本地廉价车道；不得单独作为 MVP-2 Done
USE_FAKE_EMBEDDER=

# ── 服务发现 / 引导 ─────────────────────────────────────────
# 以下均为环境变量；本地与生产填不同值（见下方对照表）。勿把本地 127.0.0.1 拷进生产。
AGENT_BASE_URL=
RAG_BASE_URL=
RAG_SERVICE_TOKEN=
# MCP：Cursor = Streamable HTTP `/mcp`；ChatBox = legacy SSE `/sse`（+ `/messages/`）
# 客户端如何写配置（含 stdio mcp.json）：specs/deployment-plan.md §7.1
# 详见 specs/mcp-design.md §7；Bearer = 使用者 Key（勿把 Key 写进 URL）
# MCP_PUBLIC_PATH=/mcp
# MCP_SSE_PATH=/sse
PUBLIC_BASE_URL=https://kb.agent-mate.ai
NEXT_PUBLIC_APP_URL=https://kb.agent-mate.ai
BOOTSTRAP_ADMIN_EMAIL=me@ethanhuang.com
# 种子管理员联系邮箱（默认 me@ethanhuang.com）。首位账号固定：用户名 admin / 初始密码 admin，仅种子强制改密；邀请/重置设密不走强制改密。
API_KEY_PEPPER=
# 管理台「查看」解密用；生产须显式配置（≥32 字节随机）。未设时本地可回退派生自 API_KEY_PEPPER（ADR-007）
API_KEY_ENCRYPTION_SECRET=
SESSION_SECRET=

# ── 外部知识源（按需；未接入则留空；MVP-4）───────────────────
# TAVILY_API_KEY=
# EXA_API_KEY=
```

## URL 类环境变量：本地 vs 生产

| 变量 | 本地开发（根目录 `.env`） | 生产（Portainer / `.env.prod`） |
| --- | --- | --- |
| `PUBLIC_BASE_URL` | 可用 `http://127.0.0.1:3000` 或公网预览域 | **必须** `https://kb.agent-mate.ai` |
| `NEXT_PUBLIC_APP_URL` | `http://127.0.0.1:3000` | `https://kb.agent-mate.ai`（进前端包） |
| `AGENT_BASE_URL` | `http://127.0.0.1:8000` | Compose 内网如 `http://kb-agent:8000` |
| `RAG_BASE_URL` | `http://127.0.0.1:8001` | `http://kb-rag:8001` |
| `QDRANT_URL` | `http://127.0.0.1:6333` | `http://qdrant:6333` |
| `DATABASE_URL` | 本机 Compose（常映射 **`:5434`**）或远程实例 | 生产 Postgres；**禁止**写进 `NEXT_PUBLIC_*` |
| `USE_FAKE_EMBEDDER` | MVP-1/廉价车道可 `true`；**MVP-2 Done 须 `false`** | 生产 `false` |

模板文件：

- 本地：`.env.example` → 复制为 `.env`（gitignore）
- 生产名册：[`.env.prod.example`](../.env.prod.example)（无密钥）→ 填入 Portainer / 节点 env
- 交付批次：[`mvp-2-3-delivery.md`](./mvp-2-3-delivery.md)、[`story-mapping.md`](./story-mapping.md)

本地起栈：复制 `.env` 后 **`make install`** → **`make up-daemon`**（durable；见 [`knowledge/ops/local-apps-keep-dying.md`](./knowledge/ops/local-apps-keep-dying.md)）。根目录 [`README.md`](../README.md) 有端口表。MCP 写入法见 [`deployment-plan.md`](./deployment-plan.md) §7.1。

应用代码只读这些环境变量，不硬编码主机名。

## 填写说明

| 区块 | 说明 |
| --- | --- |
| QWEN_* | 内部 KM 对话 / 可选 VL·生图；Embedding 用 `QWEN_EMBED_MODEL` + `EMBED_DIM`。可为公共 DashScope 或百炼 MaaS 专属 `HOST`/`BASE_URL`/`WORKSPACE` |
| RESEND_* | 管理员邀请、重置密码等事务邮件（**MVP-3** 闭环须真 Resend test/sandbox） |
| DATABASE_* | 优先使用完整 `DATABASE_URL`；凭证仅服务端，禁止 `NEXT_PUBLIC_*`；本地常见端口 **5434** |
| QDRANT_* | 向量库；通常仅内网 URL（环境变量 `QDRANT_URL`） |
| `USE_FAKE_EMBEDDER` | `true` 仅廉价测试；MVP-2+ 闭环交付门禁必须 `false` + 真 embed |
| `AGENT_BASE_URL` / `RAG_BASE_URL` | 服务间调用；环境变量配置，生产用服务名而非 `127.0.0.1` |
| MCP `/mcp` | Streamable HTTP（Cursor）；URL = `{基址}/mcp`；配置写法见 `deployment-plan.md` §7.1 |
| MCP `/sse` | Legacy SSE（ChatBox http/sse）；URL = `{基址}/sse`；配套 `/messages/`；§7.1 |
| `API_KEY_PEPPER` | 服务端 Key 哈希盐；stdio 的 `mcp.json` 必须与签发环境相同（勿填成 API Key） |
| PUBLIC_BASE_URL | 生产公网基址：`https://kb.agent-mate.ai` |
| NEXT_PUBLIC_APP_URL | 浏览器可见公网源；与 `PUBLIC_BASE_URL` 通常同域 |
| BOOTSTRAP_ADMIN_EMAIL | 种子管理员联系邮箱（默认 `me@ethanhuang.com`）。首位账号为 `admin`/`admin` + 仅种子强制改密 |
| SESSION_SECRET / API_KEY_PEPPER / API_KEY_ENCRYPTION_SECRET / RAG_SERVICE_TOKEN | 会话与 Key 盐/加密；生产勿用 `dev-*` |
| TAVILY / EXA | 外部候选检索（MVP-4）；未启用前保持注释 |

## 从旧草稿迁入时

| 旧内容 | 新位置 |
| --- | --- |
| `OPENAI_*` / ChatGPT | **删除** — 本项目默认不用；改填 `QWEN_*` |
| `RESEND_API_KEY_AGENT_MATE.AI` 等带后缀名 | → `RESEND_API_KEY` |
| 散落的主机 / 用户名 / 密码行 | → `DATABASE_HOST` / `DATABASE_USER` / `DATABASE_PASSWORD`，并拼好 `DATABASE_URL` |

## 不要写入本文件（已填值的副本也不要进 git）

- 真实 API Key、数据库密码
- 已废弃的 OpenAI 密钥块
