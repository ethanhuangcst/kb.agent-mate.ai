---
title: ClickFix / HTML inject incident (2026-08-12)
type: ops-lesson
status: active
as_of: 2026-08-12
tags:
  - security
  - clickfix
  - cve-2025-66478
  - csp
related:
  - adr/ADR-020-csp-nonce-clickfix-defense.md
  - knowledge/security/csp-and-next-cve.md
  - knowledge/ops/prod-yecaoyun3.md
  - knowledge/for-kb/14-security-clickfix-and-csp.md
---

# ClickFix / HTML inject incident (2026-08-12)

## Summary

Same-day after a clean production smoke of `kb.agent-mate.ai`, **kb-web** HTML was injected with a Fake CAPTCHA / ClickFix loader (`data:text/javascript;base64` → chain RPC → `eval`). An operator who pasted the clipboard command into Terminal lost the machine. Sibling apps on the node did not show the same injector at IR time. NPM Advanced was empty (not the rewrite path).

**Timeline clue:** smokes after the last deploy were clean → compromise was **post-deploy runtime**, not a poison-at-build of the first good image.

**Plausible initial access:** Next.js **15.5.2** / [CVE-2025-66478](https://nextjs.org/blog/CVE-2025-66478) (RSC RCE). Patched in release **`v0.1.3`** (Next **15.5.7**) together with nonce CSP (ADR-020).

Platform IR detail (Portainer/NPM/DNS order, sibling checks) lives in release-bot:  
`specs/knowledge/ops/kb-agent-clickfix-incident-2026-08-12.md`.

## App outcomes

| Tag | Meaning |
| --- | --- |
| `v0.1.2` | Clean rebuild from audited commit after containment |
| `v0.1.3` | Nonce CSP + Next 15.5.7; production verified |

## Operator rules (durable)

1. No legitimate CAPTCHA asks for Terminal / Run + paste.  
2. After Stack recreate: if `/` is 200 but `/healthz`/`/mcp` are 502 → NPM Proxy Host **Save** (no edit).  
3. Keep Next on patched releases; do not run known-vulnerable RSC lines in prod.  
4. Never commit prod secrets; rotate DB/API keys after credential exposure (still an open follow-up if skipped in IR).

## Detection (safe)

```text
data:text/javascript;base64
I'm not a robot
Complete these Verification Steps
```

```bash
curl -sS -D - -o /dev/null "https://kb.agent-mate.ai/" | grep -i content-security-policy
curl -sS "https://kb.agent-mate.ai/" | grep -c 'data:text/javascript;base64'  # expect 0
curl -sS "https://kb.agent-mate.ai/healthz"  # expect {"status":"ok"}
```
