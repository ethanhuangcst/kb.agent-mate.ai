---
title: MCP stdio auth — KB_API_KEY vs API_KEY_PEPPER
type: ops-lesson
status: active
as_of: 2026-08-11
tags:
  - mcp
  - stdio
  - auth
  - api-key
related_spec: specs/deployment-plan.md
related:
  - knowledge/ops/chatbox-mcp-sse.md
  - knowledge/security/api-key-ciphertext.md
  - adr/ADR-007-api-key-ciphertext-storage.md
---

# MCP stdio: `KB_API_KEY` vs `API_KEY_PEPPER`

## Summary
Cursor stdio MCP (`python -m app.mcp_stdio`) fails with `auth failed (UNAUTHORIZED)` when the **pepper** in `~/.cursor/mcp.json` does not match the agent/admin `.env`, or when the **API key** is missing/revoked. A common mistake is pasting the user Key (`kb_live_…`) into `API_KEY_PEPPER`.

## Evidence
- Log: `kb-agent mcp stdio: auth failed (UNAUTHORIZED)`
- Hash check: `sha256(API_KEY_PEPPER + raw_key) == api_keys.key_hash`
- Local default pepper (dev only): `dev-api-key-pepper-change-me` — must match the `.env` used when the Key was issued
- Zero active keys in DB also yields UNAUTHORIZED even with a correct pepper

## Lesson / guidance

| Env in `mcp.json` | Meaning | Typical value |
| --- | --- | --- |
| `KB_API_KEY` | Plaintext user Key from admin | `kb_live_…` |
| `API_KEY_PEPPER` | Server hash salt (same as agent `.env`) | `dev-api-key-pepper-change-me` locally — **never** a `kb_live_` string |

Checklist when auth fails:
1. Admin has an **active** Key; copy full plaintext into `KB_API_KEY` (no `Bearer ` prefix).
2. `API_KEY_PEPPER` equals root `.env` used at issue time (byte-for-byte).
3. `DATABASE_URL` points at the same DB that holds that Key (local often `:5434`).
4. Reload MCP in Cursor after edits.

Remote Cursor HTTP (`…/mcp` + Bearer header) does not need pepper in the client — only the Bearer Key.

## Links
- Config cookbook: [`specs/deployment-plan.md`](../../deployment-plan.md) §7.1
- ChatBox SSE (different transport): [`chatbox-mcp-sse.md`](./chatbox-mcp-sse.md)
