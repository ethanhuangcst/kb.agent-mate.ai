# ADR-001: Logo 光学左对齐（CSS token，不改资产）

## Status
Accepted

## Context
品牌锁头 `logo.png` 画布含透明边距与射线；若按图片包围盒与正文左缘对齐，黄色灯泡主体会视觉偏右。需在全站（首页、auth、管理顶栏、gallery）统一处理。

## Decision
不裁切/重导 PNG。用共享 CSS 变量按展示宽度等比负 margin，使**黄色灯泡左缘**与相邻文案左缘光学对齐；射线允许伸出左缘。

- Token：`--logo-optical-shift: calc(var(--logo-w, 56px) * -19 / 56)`（以 56px → −19px 标定）
- 各尺寸通过 `--logo-w`（36 / 56 / 72）参与计算
- 挂在 `.logo img`，全站锁头共用

## Rationale
| 方案 | 取舍 |
| --- | --- |
| 重导/裁切资产 | 永久改图；顶栏小尺寸与大锁头比例难一次对齐 |
| 仅首页硬编码 `margin-left` | 易漂移；auth/顶栏不一致 |
| **CSS 等比光学偏移** | 资产保持完整；一处标定、全站比例一致；可微调 |

## Consequences
- 改对齐只需调 `--logo-optical-shift` 的分子（当前 −19）或 `--logo-w`
- 射线会溢出内容左缘，父级勿 `overflow: hidden` 裁掉品牌
- 设计规格须写明「黄泡左缘」而非「图片盒左缘」——见 `specs/web-ui-design.md`、`specs/knowledge/design/logo-optical-alignment.md`

## Date
2026-08-11
