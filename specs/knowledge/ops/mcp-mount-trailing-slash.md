---
title: Starlette Mount /mcp needs trailing-slash rewrite
type: ops-lesson
status: active
as_of: 2026-08-11
tags:
  - mcp
  - starlette
  - fastapi
related_spec: specs/mcp-design.md
related:
  - knowledge/ops/chatbox-mcp-sse.md
---

# Bare `/mcp` 404 under Starlette Mount

## Summary
`fastapi_app.mount("/mcp", streamable)` compiles to regex `^/mcp/(?P<path>.*)$`. A POST to exact `/mcp` (no trailing slash) does **not** match and FastAPI returns `{"detail":"Not Found"}`. `/mcp/` works. Cursor and the true-stack journey post to `/mcp`.

## Fix
In Bearer auth middleware (before routing), rewrite scope path `/mcp` → `/mcp/` (and `raw_path`). Clients may keep configuring `http://127.0.0.1:8000/mcp`.

## Evidence
- MVP-2 journey failed at `mcp_init_ok` with 404 until rewrite landed.
- Live probe: `/mcp` 404 → after rewrite 200; `/mcp/` always 200.

## Links
- `services/kb-agent/app/mcp_server.py` (`BearerAuthMiddleware`)
- `services/kb-agent/tests/test_mcp_mount.py`
