# ADR-002: Admin 面经 Next Route Handlers 直连同一 Postgres

## Status
Accepted

## Context
MVP-1 需要管理台（登录、强制改密、签发/吊销/重签 Key）与 Agent Bearer 鉴权共用同一用户与 Key 表。可选：(A) 独立 Admin API 服务；(B) Next.js Route Handlers + `postgres` 客户端直连库；(C) 经 kb-agent 暴露管理 API。

## Decision
管理写读走 **kb-web Next Route Handlers**，使用 `postgres` 连接与 Agent/RAG **同一 PostgreSQL**（Compose `127.0.0.1:5434` / `kb_agent`）。**Alembic（`packages/kb_schema`）仍是唯一迁移源**。会话为 HttpOnly Cookie JWT（`jose`）；API Key 哈希为 `sha256(pepper + raw)`，与 kb-agent 一致。

## Rationale
| 方案 | 取舍 |
| --- | --- |
| 独立 Admin 服务 | 多一进程与部署面；MVP-1 过重 |
| 经 kb-agent 管理 API | Agent 面向 Bearer 调用方，掺管理会话语义会混淆边界 |
| **Next Route Handlers + 同库** | 与 Cookie 会话同进程；表模型已由 schema 包定义；迁移不分裂 |

## Consequences
- Web 与 Agent 必须共享 `DATABASE_URL` / `API_KEY_PEPPER`
- Schema 变更只改 `kb_schema` + Alembic，禁止在 Web 侧手写 DDL
- 测试重置种子账号用非生产路由 `/api/admin/test/reset-seed`（生产须显式 `ENABLE_TEST_RESET=1`）

## Date
2026-08-11
