# ADR-003: 吊销 Key 软吊销 + 列表仅展示有效行

## Status
Accepted

## Context
管理员点「吊销」后，产品要求：确认对话框 → Key 立即失效 → **列表不再出现该行**；同时架构要求**知识数据保留**。`users` ← `knowledge_items` 为 `ON DELETE CASCADE`，硬删 `users` 会连带删知识，不可取。

## Decision
1. 吊销 API：将对应 `api_keys.status` 置为 `revoked`，并将 `users.status` 置为 `disabled`（不删行）。
2. 使用者列表 GET：仅返回 `api_keys.status = 'active'` 的行。
3. UI：确认对话框后调用吊销；列表刷新后该行消失。不展示「revoked 且无操作按钮」的僵尸行。

## Rationale
| 方案 | 取舍 |
| --- | --- |
| 硬删 user（及 CASCADE 知识） | 违背「知识保留」 |
| 仅软吊销 Key、列表仍展示 revoked | 出现无操作的死行（用户明确拒绝） |
| **软吊销 + 列表过滤 active** | 鉴权立即 401；知识/用户行仍在库；管理面清爽 |

## Consequences
- 库中可残留 revoked Key / disabled user，便于审计与同 `user_id` 知识保留；管理面默认不可见。
- 重签路径仍可在吊销前对 **active** Key 操作；已从列表消失的使用者不能再点「重签」（需重新签发则是新 user——与当前「一人一把」模型一致：列表无入口即需新签发）。
- 若未来要「恢复已吊销使用者」需另开故事（列表含 disabled 或独立恢复流）。

## Date
2026-08-11
