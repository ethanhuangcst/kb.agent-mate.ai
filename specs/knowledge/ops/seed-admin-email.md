---
title: 种子管理员默认邮箱
type: domain-note
status: active
as_of: 2026-08-11
tags:
  - admin
  - seed
  - env
related_spec: specs/keys.md
related:
  - adr/ADR-002-admin-next-same-postgres.md
---

# 种子管理员默认邮箱

## Summary
空库种子管理员固定为用户名 `admin` / 密码 `admin`；联系邮箱默认 **`me@ethanhuang.com`**，可由环境变量 `BOOTSTRAP_ADMIN_EMAIL` 覆盖。

## Evidence
- 产品指定默认邮箱为 `me@ethanhuang.com`。
- 实现：`apps/kb-web/lib/seed.ts`、`packages/kb_schema/src/kb_schema/seed.py`；`.env.example` / `specs/keys.md` 已同步。

## Lesson / guidance
- 新环境未设 `BOOTSTRAP_ADMIN_EMAIL` 时仍应得到 `me@ethanhuang.com`，不要落 `NULL`。
- 登录可用用户名或该邮箱；重置邮件依赖此联系邮箱。
- 已有库需手工 `UPDATE` 或跑 test reset-seed 才会改已存在行的 email。

## Links
- `specs/keys.md`、`specs/architecture.md` §2.3、`specs/deployment-plan.md`
