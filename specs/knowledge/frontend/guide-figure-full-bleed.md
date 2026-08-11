---
title: Guide step figures full-bleed width
date: 2026-08-11
tags: [frontend, guide, css]
related:
  - ../web-ui-design.md
---

# 接入指南步骤截图全宽对齐

## Lesson
`.guide-body ol { padding-left }` 会盖过 `.guide-steps { padding: 0 }`（选择器更具体），导致截图相对下方 `.guide-code` 缩进。

## Practice
- 步骤结构：编号+文案在 `.guide-step-head`；`.guide-figure` 作为步骤直接子节点，`width: 100%`。
- 必须声明 `.guide-body ol.guide-steps { padding-left: 0 }`（否则被 `.guide-body ol` 盖过）。
- 对齐参照：上方 `.guide-modes` / 下方 `.guide-code`，不是编号列。
- 避免用负 margin「拉回」编号列宽度——易与 `next/image` / 继承变量失效叠在一起；优先改 DOM 层级。

## See also
- `specs/web-ui-design.md` §4.5
- `apps/kb-web/app/admin-ui.css`（`.guide-steps` / `.guide-figure`）
