# ADR-014: Accept-invite requires username (UI label 用户名)

## Status
Accepted

## Context
Accept-invite previously collected only English `display_name` + password and inserted `admin_users.username = NULL`. Admin list showed `—` under the first column; invited admins could still sign in by email, but had no login username. UI copy mixed「登录名」with login form「用户名或邮箱」.

Alternatives considered:
1. Keep username nullable; login by email only — weak identity in lists and stdio/docs that say「用户名」.
2. Auto-derive username from email local-part — collisions and ugly names.
3. Require an explicit username on accept (and on disabled re-invite reactivation), unique case-insensitively; unify UI label to **用户名**.

## Decision
1. Accept-invite form and `POST /api/auth/accept-invite` require `username` + English `displayName` + password.
2. Validation: letter start; letters, digits, `._-`; length 3–64 (`isValidUsername`); reject `USERNAME_TAKEN` on case-insensitive clash (allow reuse of the same row when reactivating disabled).
3. Persist non-null `username` on insert and on disabled → active reactivation.
4. Product copy: column / field label **用户名** (i18n `admins.adminUsername` / `acceptInvite.usernameLabel`); do not use「登录名」in UI.

## Rationale
Empty username was a product defect, not a deliberate design. Explicit choice at invite time matches seed `admin` and login-by-username. Label alignment reduces zh confusion between list and login.

## Consequences
- Admins created before this change may still have `username IS NULL` until re-invite after soft-disable or a one-off backfill.
- Story AC: `web-acct-05` (and list copy in `web-acct-07`) updated 2026-08-11.
- ADR-011 reactivation path now also sets `username`.

## Date
2026-08-11
