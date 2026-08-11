---
title: Client-facing config snippets use angle-bracket placeholders
type: ops-lesson
status: active
as_of: 2026-08-11
tags:
  - docs
  - mcp
  - guide
related_spec: specs/deployment-plan.md
related:
  - knowledge/for-kb/01-mcp-clients.md
---

# Config examples: placeholders, not concrete hosts

## Summary
Guide / deployment / MCP client **copy-paste templates** must not hard-code loopback IPs, ports, or the production hostname. Use angle-bracket placeholders so readers fill real values and do not paste lab addresses into prod (or the reverse).

## Lesson / guidance
Typical placeholders:

| Placeholder | Role |
| --- | --- |
| `<REPO>` | Local clone root |
| `<HOST>` / `<AGENT_PORT>` | Agent HTTP base (MCP `/mcp`, SSE `/sse`) |
| `<PUBLIC_HOST>` | Public TLS host for remote clients |
| `<PG_HOST>` / `<PG_PORT>` | Postgres for stdio `DATABASE_URL` |
| `<RAG_HOST>` / `<RAG_PORT>` | RAG base for stdio env |
| `<password>`, key/pepper fields | Secrets — never commit |

Keep **runtime defaults** and inventory docs (`keys.md` local/prod map, Playwright `baseURL`, Compose port tables) as real values where they document the actual stack.

Touch points when editing: `apps/kb-web/app/guide/page.tsx`, `specs/mockup/guide.html`, `specs/deployment-plan.md` §7.1, `specs/mcp-design.md` §7, `for-kb/01-mcp-clients.md`.
