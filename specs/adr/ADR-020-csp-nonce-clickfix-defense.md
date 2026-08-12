# ADR-020: Nonce CSP on kb-web (ClickFix / HTML inject defense)

## Status
Accepted

## Context
On 2026-08-12, production `kb.agent-mate.ai` HTML was injected with a `data:text/javascript;base64` loader that drove a Fake CAPTCHA / ClickFix lure. Browser-enforced CSP cannot stop server compromise, but it can stop un-nonced inline/`data:` scripts from executing for visitors.

## Decision
- Emit a per-request **Content-Security-Policy** from Next.js `middleware.ts`.
- `script-src`: `'self' 'nonce-…' 'strict-dynamic'` (no `'unsafe-inline'`, no `data:`).
- Production `connect-src 'self'` to block typical loader C2 fetches (e.g. public chain RPC) even if script execution is somehow obtained.
- `style-src 'self' 'unsafe-inline'` (pragmatic; threat was script injection).
- Root layout `dynamic = 'force-dynamic'` so nonces apply on every document response.
- Policy builder lives in `apps/kb-web/lib/csp.ts` with unit tests.

## Rationale
Aligned with Next.js CSP guidance and the release-bot prevention note (`prevent-clickfix-html-inject`). Nonces require dynamic rendering; acceptable for this admin/private KB surface.

## Consequences
- Pages are not statically cached at the edge without extra design.
- After deploy, verify response header `Content-Security-Policy` contains `nonce-` and that the homepage still hydrates.
- CSP is defense-in-depth; continue host hardening, secret rotation, and HTML IOC monitoring.
- Same change set upgrades **Next.js 15.5.2 → 15.5.7** for [CVE-2025-66478](https://nextjs.org/blog/CVE-2025-66478) (RSC RCE). Unpatched 15.5.x is a plausible path for post-deploy host/app compromise; patching is mandatory, not optional.

## Date
2026-08-12
