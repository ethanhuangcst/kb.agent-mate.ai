# ADR-019: Login closed-registration notice plate

## Status
Accepted

## Context
Login page copy「开放注册已关闭。联系管理员获得 api-key」was first shown as body lead under an Admin eyebrow, then as floating text between brand and title, then as a hairline “status rail”. Reviewers found those treatments abrupt or uneven versus the cold-minimal auth shell (logo lockup + underline fields + ink CTA).

Alternatives considered:
1. Keep `eyebrow` + `h1` + `.lead` (original)
2. Hairline top/bottom rail only (metadata strip)
3. **Fill plate** — `--fill` background, hairline border, zero radius; equal vertical gap to logo and to「管理员登录」

## Decision
Use a **closed-registration notice plate** (`.auth-status`) between brand and the login work block:
- Background `var(--fill)`, border `1px solid var(--line)`, `border-radius: 0`
- Vertical spacing to logo and to「管理员登录」both use `--auth-notice-gap` (default `2rem`)
- No Admin eyebrow on the login page; title is「管理员登录」/「Admin sign-in」
- `api-key` rendered in mono (`.auth-status-key`);「联系管理员」keeps WeChat QR hover

Canonical static: `specs/mockup/login.html`. Live: `apps/kb-web/app/login/`.

## Rationale
The plate reuses existing surface tokens (no alert color, no card shadow), so it reads as system metadata rather than marketing body copy, while still satisfying the request for a distinct background box and equal gaps.

## Consequences
- Other auth pages (forgot / reset / invite) may keep eyebrow + title + lead unless redesigned the same way.
- Mockup and `web-ui-design.md` §4.2 must stay in sync with `.auth-card-login` / `.auth-status` / `.auth-work`.

## Date
2026-08-12
