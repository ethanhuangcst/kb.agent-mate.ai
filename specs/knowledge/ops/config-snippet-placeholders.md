---
title: Client config snippets — prod host real; secrets placeholders
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
  - knowledge/for-kb/10-config-placeholders.md
---

# Config examples: production host vs placeholders

## Summary

Product MCP / ChatBox templates use **only** the canonical origin **`https://kb.agent-mate.ai`**. Secrets stay angle-bracket placeholders. Do not document loopback URLs in `/guide` or client-facing access copy.

## Lesson / guidance

| Kind | What to write |
| --- | --- |
| Product Cursor / ChatBox | `https://kb.agent-mate.ai/mcp` · `https://kb.agent-mate.ai/sse` |
| Secrets | Always placeholders — never commit real keys |
| Contributor stdio / local stack | Ops notes only (`mcp-stdio-auth.md`, local README) — **not** product access guide |

Touch points: `apps/kb-web/app/guide/page.tsx`, `specs/deployment-plan.md` §7.1, `specs/mcp-design.md` §7, `for-kb/01-mcp-clients.md`, `.env.prod.example`.
