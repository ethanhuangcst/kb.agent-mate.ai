---
title: Logo 黄色灯泡光学左对齐
type: design-direction
status: active
as_of: 2026-08-11
tags:
  - logo
  - mockup
  - css
related_spec: specs/web-ui-design.md
related:
  - adr/ADR-001-logo-optical-alignment.md
---

# Logo 黄色灯泡光学左对齐

## Summary
锁头 PNG 的包围盒含透明边与射线；视觉对齐应对准**黄色灯泡左缘**，不是图片左缘。全站用 `--logo-optical-shift`（56px 时 −19px）等比偏移。

## Evidence
- 资产约 `600×600`；内容约 x=100 起，黄泡填充约 x=205 起（≈34% 画布宽）
- 按盒对齐时黄泡相对正文偏右约 15–19px（56px 展示）
- 用户微调序列：−15 → −22 → 右移 3 → **−19px**（56px 基准）后定稿并推广全站

## Lesson / guidance
1. 新锁头尺寸设 `--logo-w`，勿再写死单页 `margin-left`
2. 对齐验收：黄泡左缘 ≈ 说明文/表单列左缘；射线可略伸出
3. 勿对 `.logo` / 公网卡使用会裁切负 margin 的 `overflow: hidden`
4. 若换 logo 资产，重新量黄泡左缘占比后改 `* -19 / 56` 中的标定值

## Links
- ADR-001：`specs/adr/ADR-001-logo-optical-alignment.md`
- 实现：`specs/mockup/styles.css`（`:root` + `.logo img`）
- UI 规格：`specs/web-ui-design.md` §4
