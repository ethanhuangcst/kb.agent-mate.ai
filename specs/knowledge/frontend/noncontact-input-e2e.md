---
title: NonContactTextInput 与 E2E fill
type: ops-lesson
status: active
as_of: 2026-08-11
tags:
  - playwright
  - e2e
  - admin-ui
related_spec: specs/web-ui-design.md
related:
  - knowledge/frontend/macos-contacts-autofill.md
---

# NonContactTextInput 与 E2E fill

## Summary
签发姓名的 `NonContactTextInput` 在 focus 前为 `readOnly`（挡 macOS Contacts）。Playwright 的 `locator.fill` **不会**触发可编辑解锁，会一直报 `element is not editable`。

## Evidence
- MVP-1 E2E：`should_force_password_change_then_issue_key` / `should_revoke_and_reissue_key` 在直接 `fill` 时超时。
- 先 `click()` 再 `fill()` 通过。

## Lesson / guidance
1. E2E 对姓名框必须先 `click()`（或 `focus()`）再 `fill()`。
2. `reset-seed` 应顺带 soft-revoke 全部 active Key / disable active users，避免姓名碰撞导致 strict mode 双行。
3. 唯一姓名用随机字母，勿仅用 `Date.now() % 26`（碰撞率高）。

## Links
- `apps/kb-web/app/non-contact-text-input.tsx`
- `apps/kb-web/e2e/admin-journey.spec.ts`
- `apps/kb-web/app/api/admin/test/reset-seed/route.ts`
