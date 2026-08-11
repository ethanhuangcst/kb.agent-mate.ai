---
title: Outbound fetch SSRF and RPM quotas
type: ops-lesson
status: active
as_of: 2026-08-11
tags:
  - ssrf
  - quota
  - fetch
related_spec: specs/architecture.md
related:
  - adr/ADR-015-external-search-adapters.md
---

# Outbound fetch SSRF and RPM quotas

## Summary

`kb_fetch_url` validates URLs (http/https only, blocks loopback/private/link-local after DNS) and raises `FETCH_BLOCKED`. Per-user process-local RPM limits (`KB_FETCH_RPM`, `KB_EXTERNAL_SEARCH_RPM`) raise `RATE_LIMITED` (429).

## Ops notes

- Single-node limiter is in-process; multi-instance needs a shared store later.
- Soft-delete calls RAG `POST /internal/delete` so Qdrant points for `knowledge_id` are removed.
- Enable chat only with `CHAT_FACADE_ENABLED=true`.
