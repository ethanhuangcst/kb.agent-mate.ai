# ADR-010: 吊销按 user 失效全部 active Key

## Status
Accepted

## Context
吊销 API 原按路径中的 `api_keys.id` 且要求 `status = active` 更新。重签后旧 id 已是 `revoked`；若客户端仍持旧 id（陈旧列表行、竞态），吊销会变成空操作，新 active Key 仍可用。E2E 在「查看 → 重签 → 吊销」路径上复现。

## Decision
1. `POST /api/admin/keys/:id/revoke`：用给定 id（**任意 status**）解析 `user_id`。
2. 将该用户下全部 `status = active` 的 Key 软吊销，并将 `users.status` 置为 `disabled`。
3. 继续遵守 ADR-003：不硬删用户/知识；列表仅展示 active。

## Rationale
| 方案 | 取舍 |
| --- | --- |
| 仅吊销路径中的那一行 | 重签后旧 id 空操作；管理意图是「停用该使用者」 |
| **按 user 吊销全部 active** | 与产品「一人一把有效 Key」一致；容忍陈旧 id |
| 客户端强制刷新后再吊销 | 仍有竞态；服务端应对齐意图 |

## Consequences
- 吊销语义 = 停用该使用者当前访问能力，而非「精确删某一历史 key 行」。
- 与 ADR-003 兼容；本 ADR 澄清 id 解析与 multi-active 边界（正常路径一人一把 active）。

## Date
2026-08-11
