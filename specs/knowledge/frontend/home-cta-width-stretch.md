---
title: Home CTA width stretch pitfall
type: ops-lesson
status: active
as_of: 2026-08-12
tags:
  - css
  - home
  - layout
related_spec: specs/web-ui-design.md
---

# Home CTA：`width: 100%` + `max-content` 父级会塌宽

## Summary
首页「接入指南」与「登录」要对齐同宽时，父级用 `width: max-content` / flex column，子按钮再设 `width: 100%`，在不定宽包含块下百分比会回落到内容宽（「登录」两字），再配上 `--control-h`（2.75rem）会变成又高又窄的方块。

## Evidence
- 短标签「登录」+ 固定 `height: var(--control-h)` → 视觉上接近竖条/方块（2026-08-12 反馈）。
- `align-items: stretch` 被显式 `width: 100%` 干扰时无法拉到与「接入指南」同宽。

## Lesson / guidance
1. 用 **CSS grid** `grid-template-columns: max-content` + `justify-items: stretch`，子按钮 **不要** 写 `width: 100%`。
2. 首页 CTA 单独压低高度（如 `2.125rem`），勿盲用管理台 `--control-h`。
3. 参考：`.home-actions` in `apps/kb-web/app/admin-ui.css`。
