---
title: Safari HTTPS-First breaks http://127.0.0.1 email links
type: ops-lesson
status: active
as_of: 2026-08-11
tags:
  - ops
  - email
  - safari
  - auth
related_spec: specs/keys.md
related:
  - adr/ADR-012-email-public-base-url-localhost.md
  - knowledge/ops/admin-resend-mail.md
  - knowledge/for-kb/07-safari-email-localhost.md
---

# Safari opens `https://127.0.0.1` from reset/invite emails

## Summary
Local reset/invite emails that use `http://127.0.0.1:3000/...` can open in Safari as `https://127.0.0.1` (no port). Prefer `http://localhost:3000` locally and `https://kb.agent-mate.ai` in production; `publicAppBaseUrl()` enforces this (ADR-012).

## Evidence
- Resend API HTML still showed `http://127.0.0.1:3000/reset-password?token=...`.
- Safari address bar showed `https://127.0.0.1` after click → connection failure.
- Successful resets in logs used the same token when opened via a non-mangled path (e.g. other browser / copied URL with port).

## Lesson / guidance
- Local: set `PUBLIC_BASE_URL` / `NEXT_PUBLIC_APP_URL` to `http://localhost:3000` (not `127.0.0.1`).
- Production: both must be `https://kb.agent-mate.ai`; loopback is rejected at send time.
- Diagnose with Resend message HTML or `EMAIL_TRANSPORT=log` before blaming the mail provider.
- Product-facing copy: `for-kb/07-safari-email-localhost.md` (ingested).

## Links
- ADR-012: `specs/adr/ADR-012-email-public-base-url-localhost.md`
- Keys table: `specs/keys.md` (local vs prod URL rows)
- Admin mail transport: `specs/knowledge/ops/admin-resend-mail.md`
