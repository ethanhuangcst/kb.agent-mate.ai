---
title: Admin mail uses Resend or log transport
type: ops-lesson
status: active
as_of: 2026-08-11
tags:
  - resend
  - admin
  - email
related_spec: specs/mvp-2-3-delivery.md
related:
  - adr/ADR-011-admin-soft-disable.md
---

# Admin transactional email (reset / invite)

## Summary
Forgot-password and admin invite send mail via Resend. Fixture/local without a key may set `EMAIL_TRANSPORT=log` (records links in-process / console). MVP-3 Done for the admin slice still requires real Resend sandbox evidence when claiming closed-loop mail delivery.

## Practice
- `RESEND_API_KEY` + `RESEND_FROM_EMAIL` for real sends
- `EMAIL_TRANSPORT=log` for CI/unit outbox assertions
- `ENABLE_TEST_RESET=1` exposes `x-debug-reset-token` / `x-debug-invite-token` for Playwright
- Password reset and admin disable bump `session_version` (ADR-011)
- Absolute link origin / Safari + `127.0.0.1`: ADR-012, `ops/safari-localhost-email-links.md`
