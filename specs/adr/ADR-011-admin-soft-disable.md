# ADR-011: Soft-disable admins instead of hard delete

## Status
Accepted

## Context
web-acct-08 requires removing an admin from the effective list and blocking login, while forbidding delete-self and delete-last-admin. Hard-deleting `admin_users` rows would cascade invite/reset tokens and complicate audit; listing needs a clear `status`.

## Decision
1. Add `admin_users.status` (`active` | `disabled`). Delete sets `disabled` and bumps `session_version`.
2. List (`GET /api/admin/admins`) returns **active** rows only.
3. Login rejects non-`active` admins.
4. JWT carries `sessionVersion`; `getSession` rejects mismatches (password reset and disable both bump version).

## Consequences
- Disabled admins remain in DB for audit.
- Re-invite of a previously disabled email: accept path **reactivates** the disabled row (sets **username**, password, display_name, `active`).
- JWT carries `sessionVersion`; `getSession` rejects mismatches (password reset and disable both bump version).

## Date
2026-08-11
