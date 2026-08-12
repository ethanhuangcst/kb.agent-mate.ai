---
title: macOS Contacts 自动填充与表单陷阱
type: ops-lesson
status: active
as_of: 2026-08-12
tags:
  - safari
  - autofill
  - admin-ui
  - login
related_spec: specs/web-ui-design.md
related:
  - knowledge/frontend/noncontact-input-e2e.md
  - knowledge/for-kb/04-admin-forms-autofill.md
  - adr/ADR-019-login-closed-registration-plate.md
---

# macOS Contacts 自动填充与表单陷阱

## Summary
「英文姓名」签发框与**登录页「用户名或邮箱」**在 macOS / Safari / Chromium 上都会弹出 **Contacts / 地址建议**；`autocomplete="off"` 或 `autocomplete="username"` 往往无效。用可见或假隐藏 honeypot 会在底边线表单里露出多余输入行。统一用 `NonContactTextInput`。

## Evidence
- 字段名 `displayName` / `autocomplete="name"` / 标签含「姓名」→ Contacts。
- 登录框 `autocomplete="username"` + 标签含「邮箱」仍可弹出 Chrome「Manage Addresses…」类建议（2026-08-12 生产/本机复现）。
- 提交后 Contacts 浮层可残留在下一页上方。
- Honeypot 在本设计系统下会画出多条底边线。

## Lesson / guidance
1. **禁止** honeypot 挡 Contacts。
2. 推荐：`NonContactTextInput`（首焦前 `readonly`、`autocomplete="one-time-code"`、密码管理器 ignore 标记）。
3. 适用：**签发姓名**、**登录 login**；E2E 须先 `click` 再 `fill`。
4. 实现：`apps/kb-web/app/non-contact-text-input.tsx`；登录：`login/login-form.tsx`。

## Links
- for-kb：`specs/knowledge/for-kb/04-admin-forms-autofill.md`
- E2E：`specs/knowledge/frontend/noncontact-input-e2e.md`
- 登录布局：ADR-019
