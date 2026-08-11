---
title: Admin username vs display name on invite
type: domain-note
status: active
as_of: 2026-08-11
tags:
  - admin
  - auth
  - i18n
related_spec: specs/story-mapping.md
related:
  - adr/ADR-014-accept-invite-requires-username.md
  - adr/ADR-011-admin-soft-disable.md
---

# 管理员：用户名 ≠ 姓名

## Summary
Invite landing must collect **用户名** (`username`, for login + list) and **姓名** (`display_name`, English, for Hello). They are different fields; leaving username null produces `—` in the admin table.

## Lesson / guidance
- UI label is always **用户名**, never「登录名」.
- Rules: `isValidUsername` — letter start; `[A-Za-z0-9._-]`; 3–64; unique case-insensitive.
- Login still accepts username **or** email.
- Legacy rows with null username: soft-disable + re-invite, or manual backfill—do not assume email local-part.

## Links
- ADR-014: `specs/adr/ADR-014-accept-invite-requires-username.md`
- `apps/kb-web/lib/username.ts`, accept-invite form/API
