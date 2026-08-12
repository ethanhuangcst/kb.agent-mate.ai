---
title: kb-web CSP + Next.js CVE hygiene
type: ops-lesson
status: active
as_of: 2026-08-12
tags:
  - security
  - csp
  - nextjs
related:
  - adr/ADR-020-csp-nonce-clickfix-defense.md
  - knowledge/security/clickfix-html-inject-2026-08-12.md
---

# kb-web CSP + Next.js CVE hygiene

## Why

Browser CSP cannot stop server compromise, but it **stops un-nonced inline / `data:` scripts** (the ClickFix loader pattern) from running for visitors. Separately, unpatched Next App Router / RSC lines can allow **RCE** ([CVE-2025-66478](https://nextjs.org/blog/CVE-2025-66478)) — a plausible path for post-deploy HTML rewrite.

## Implementation (shipped `v0.1.3`)

| Piece | Location |
| --- | --- |
| Policy builder | `apps/kb-web/lib/csp.ts` |
| Middleware | `apps/kb-web/middleware.ts` |
| Dynamic render | `apps/kb-web/app/layout.tsx` → `dynamic = 'force-dynamic'` |
| Tests | `apps/kb-web/__tests__/csp-unit.test.ts` |
| Decision | [ADR-020](../../adr/ADR-020-csp-nonce-clickfix-defense.md) |

Production highlights:

- `script-src 'self' 'nonce-…' 'strict-dynamic'` — no `'unsafe-inline'`, no `data:` for scripts  
- `connect-src 'self'` — limits loader C2 fetches if script ever runs  
- `style-src 'self' 'unsafe-inline'` — pragmatic for React style attrs  

## Deploy / verify

1. Ship a new GHCR tag after CSP or Next bumps.  
2. Portainer: `IMAGE_TAG=<tag>` + Re-pull.  
3. Confirm public header:

```bash
curl -sS -D - -o /dev/null "https://kb.agent-mate.ai/" | grep -i content-security-policy
```

4. If homepage OK but agent paths 502 → NPM host **Save**.  
5. Pin Next to a **patched** release in the current line (e.g. 15.5.x → ≥ 15.5.7); re-check advisories on every upgrade.
