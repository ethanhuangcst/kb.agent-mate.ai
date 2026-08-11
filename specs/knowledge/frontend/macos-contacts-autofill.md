---
title: macOS Contacts 自动填充与表单陷阱
type: ops-lesson
status: active
as_of: 2026-08-11
tags:
  - safari
  - autofill
  - admin-ui
related_spec: specs/web-ui-design.md
related:
  - adr/ADR-003-revoke-soft-hide-from-list.md
---

# macOS Contacts 自动填充与表单陷阱

## Summary
签发 Key 的「英文姓名」框会触发 macOS/Safari **通讯录自动填充**；`autocomplete="off"` 往往无效。用**可见或未真正隐藏的 honeypot 输入框**当诱饵时，在本项目底边线表单样式下会渲染成**多余输入行**，不可用。

## Evidence
- 字段名 `displayName` / `autocomplete="name"` / 标签含「姓名」时，输入 Ethan 会弹出 Contacts 同名联系人。
- 提交后 Contacts 浮层可残留在「Key 已生成」页上方（系统级 UI）。
- 曾加入 off-screen honeypot（name/email/nickname）；Safari 仍画出多条底边线，用户看到「多了两个输入框」。

## Lesson / guidance
1. **禁止**为挡 Contacts 增加额外可见或「假隐藏」`<input>`（本设计系统的 `input` 底边线会暴露它们）。
2. 可用组合：`readonly` 至首次 focus、`autocomplete="one-time-code"`、非 `name` 字段名、提交后 `blur` 再切页。
3. 无法 100% 关掉系统 Contacts 时，在 UI 规格中写明限制；勿再引入 honeypot 回归。
4. 实现参考：`apps/kb-web/app/non-contact-text-input.tsx`。

## Links
- UI 规格：`specs/web-ui-design.md` §6
- 相关产品行为（吊销列表）：`specs/adr/ADR-003-revoke-soft-hide-from-list.md`
