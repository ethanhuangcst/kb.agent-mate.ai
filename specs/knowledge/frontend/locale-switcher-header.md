---
title: Locale switcher — gray links in header, not ink plate
type: design-direction
status: active
as_of: 2026-08-11
tags:
  - frontend
  - i18n
  - 性冷淡
related_spec: specs/web-ui-design.md
related:
  - knowledge/frontend/guide-figure-full-bleed.md
---

# Locale switcher placement and look

## Summary
Language control lives in the **header top-right** (`.header-end` / `.shell-locale`), not the footer. Prefer **quiet gray text links** over a high-contrast ink-filled segment plate.

## Evidence
- First redesign used a mono “type-case” with black fill on active (`中` | `EN`); rejected as too heavy for 性冷淡.
- Prior footer underline links were directionally right but under-tuned (size / tracking / gap).

## Lesson / guidance
- Placement: admin + guide → `.header-end` (after Hello / back); home + auth → `.shell-locale` absolute top-right.
- Look: Outfit ~`0.78rem`, weight 500, `letter-spacing: 0.16em`, gap ~`0.95rem`; idle `--mute-soft`; active `--ink` + `1px` bottom hairline; labels `中文` / `EN`.
- Avoid: bordered segment control, ink reverse fill, globe icons, rounded pills.
- Spec: `specs/web-ui-design.md` §4.3; implementation `.locale-switch` in `admin-ui.css`.

## Links
- `apps/kb-web/app/locale-switcher.tsx`
- Mockups: `specs/mockup/index.html`, `admins.html`, `login.html`
