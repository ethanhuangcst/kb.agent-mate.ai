# 密钥与连接清单（模板）

本地复制为已 gitignore 的填写副本（如 `specs/keys.local.md` 或项目根 `.env.local`），**勿将填好密钥的文件提交仓库**。变量约定见 `specs/architecture.md` → **tech-stack** → 环境变量。

面向中国大陆 / 香港：LLM 用 **DashScope（通义千问）**，不用 `api.openai.com`。

---

```env
# ── QWEN DashScope（通义千问）────────────────────────────────
QWEN_API_KEY=
QWEN_HOST=dashscope.aliyuncs.com
QWEN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
QWEN_WORKSPACE=
QWEN_REGION=
QWEN_CHAT_MODEL=
QWEN_CHAT_MODEL_FALLBACK=
QWEN_EMBED_MODEL=
EMBED_DIM=
QWEN_KEY_MGMT_SITE=https://dashscope.console.aliyun.com/

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

# ── 服务发现 / 引导 ─────────────────────────────────────────
AGENT_BASE_URL=
RAG_BASE_URL=
PUBLIC_BASE_URL=https://kb.agent-mate.ai
BOOTSTRAP_ADMIN_EMAIL=
# 可选：给种子管理员绑定联系邮箱（便于重置邮件）。首位账号固定：用户名 admin / 初始密码 admin，仅种子强制改密；邀请/重置设密不走强制改密。
API_KEY_PEPPER=
SESSION_SECRET=

# ── 外部知识源（按需；未接入则留空）─────────────────────────
# TAVILY_API_KEY=
# EXA_API_KEY=
```

## 填写说明

| 区块 | 说明 |
| --- | --- |
| QWEN_* | 内部知识管理（分类 / 摘要 / 可选改写）与 Embedding |
| RESEND_* | 管理员邀请、重置密码等事务邮件 |
| DATABASE_* | 优先使用完整 `DATABASE_URL`；凭证仅服务端，禁止 `NEXT_PUBLIC_*` |
| QDRANT_* | 向量库；通常仅内网 URL |
| PUBLIC_BASE_URL | 生产公网基址：`https://kb.agent-mate.ai` |
| BOOTSTRAP_ADMIN_EMAIL | 可选；绑定种子管理员联系邮箱。首位账号为 `admin`/`admin` + 仅种子强制改密 |
| SESSION_SECRET / API_KEY_PEPPER 等 | 会话与 Key 派生盐 |
| TAVILY / EXA | 外部候选检索；未启用前保持注释 |

## 从旧草稿迁入时

| 旧内容 | 新位置 |
| --- | --- |
| `OPENAI_*` / ChatGPT | **删除** — 本项目默认不用；改填 `QWEN_*` |
| `RESEND_API_KEY_AGENT_MATE.AI` 等带后缀名 | → `RESEND_API_KEY` |
| 散落的主机 / 用户名 / 密码行 | → `DATABASE_HOST` / `DATABASE_USER` / `DATABASE_PASSWORD`，并拼好 `DATABASE_URL` |

## 不要写入本文件（已填值的副本也不要进 git）

- 真实 API Key、数据库密码
- 已废弃的 OpenAI 密钥块
