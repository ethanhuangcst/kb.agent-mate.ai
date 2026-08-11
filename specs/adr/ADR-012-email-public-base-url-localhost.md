# ADR-012: Email absolute links via PUBLIC_BASE_URL (localhost locally)

## Status
Accepted

## Context
Forgot-password and admin-invite emails embed absolute URLs from `publicAppBaseUrl()`. Local `.env` historically used `http://127.0.0.1:3000`. Safari HTTPS-First can open that as `https://127.0.0.1` (port dropped), so recipients cannot reach the reset/invite page even when Resend HTML still shows `:3000`. Production must never fall back to loopback if `PUBLIC_BASE_URL` is missing or wrong.

Alternatives considered:
1. Keep `127.0.0.1` and document “open in Chrome” — fragile for recipients.
2. Build links from the request `Host` header in all environments — host-header injection risk in production.
3. Prefer `PUBLIC_BASE_URL`, rewrite loopback `127.0.0.1` → `localhost` for local mail, and reject loopback / non-HTTPS when `NODE_ENV=production`.

## Decision
1. `publicAppBaseUrl()` prefers **`PUBLIC_BASE_URL`** over `NEXT_PUBLIC_APP_URL`, then a safe default (`http://localhost:3000` locally; `https://kb.agent-mate.ai` only as last-resort production default).
2. Hostname `127.0.0.1` is rewritten to **`localhost`**, keeping an explicit port for local HTTP (default `:3000` if missing).
3. In production, loopback or non-`https` bases **throw** at send time so misconfigured stacks cannot emit broken links.
4. Local templates (`.env.example`, compose defaults) set `PUBLIC_BASE_URL` / `NEXT_PUBLIC_APP_URL` to `http://localhost:3000`. Production templates and compose set both to `https://kb.agent-mate.ai`.

## Rationale
- Empirically verified: Resend payload kept `http://127.0.0.1:3000/...` while Safari navigated to `https://127.0.0.1`.
- `localhost` is treated more like a secure context exemption by Safari than bare `127.0.0.1`.
- Server-canonical `PUBLIC_BASE_URL` avoids stale client-bundled `NEXT_PUBLIC_*` for transactional mail.
- Fail-loud production validation beats silent wrong links.

## Consequences
- Local mail links are `http://localhost:3000/...`; Playwright may still use `127.0.0.1` for cookie isolation — do not mix hosts in the same browser profile when debugging auth.
- Production Portainer/env must set `PUBLIC_BASE_URL` (and usually `NEXT_PUBLIC_APP_URL`) to the public domain; loopback values break mail send.
- Ops lesson / product KB: `specs/knowledge/ops/safari-localhost-email-links.md`, `specs/knowledge/for-kb/07-safari-email-localhost.md`.

## Date
2026-08-11
