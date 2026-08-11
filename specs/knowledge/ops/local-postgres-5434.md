---
title: 本地 Compose Postgres 映射 5434
type: ops-lesson
status: active
as_of: 2026-08-11
tags:
  - postgres
  - docker-compose
  - local-dev
related_spec: specs/architecture.md
related:
  - adr/ADR-002-admin-next-same-postgres.md
---

# 本地 Compose Postgres 映射 5434

## Summary
本机宿主机 `:5432` 常被其他容器占用。kb 本地栈把 Postgres 映射到 **`127.0.0.1:5434`**，库名 `kb_agent`。MVP-1 与 `make migrate` / 测试默认应连此地址，勿误连远程尚无 `kb_agent` 的实例。

## Evidence
- `docker-compose.yml`：`5434:5432`
- 远程 `101.132…` 曾无 `kb_agent` 库；本地开发应以 Compose 为准
- Shell 环境若已 export 旧 `DATABASE_URL`，会覆盖 `.env`；跑 migrate/test 前应确认或显式 export 本地 URL

## Lesson / guidance
- 默认：`postgresql+psycopg://kb:kb_dev_password@127.0.0.1:5434/kb_agent`
- Qdrant：`127.0.0.1:6333`；检索 MVP-1 可用 `USE_FAKE_EMBEDDER=true`
- 空字符串环境变量（如曾设 `EMBED_DIM=`）会让 pydantic-settings 校验失败——`.env` 填具体整数，或 settings 使用 `env_ignore_empty`

## Links
- `specs/adr/ADR-002-admin-next-same-postgres.md`
- `docker-compose.yml`、`.env.example`
