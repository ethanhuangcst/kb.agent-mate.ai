# ADR-007: API Key 可逆密文存储（管理台可反复查看）

## Status
Accepted

## Context
原设计：库内仅存 `key_hash` + `key_prefix`，明文只在签发/重签响应里出现一次。产品改为：列表「查看」可再次展示完整 Key。哈希不可逆，必须改存储。

## Decision
1. `api_keys` 增加可空列 `key_ciphertext`（Text）：AES-256-GCM 密文（含 nonce），**不是**明文落库。
2. 鉴权仍只用 `key_hash`（pepper + SHA-256）；密文仅服务管理台「查看 / 签发结果页」。
3. 加密密钥：环境变量 `API_KEY_ENCRYPTION_SECRET`（不足时回退派生自 `API_KEY_PEPPER`，仅便于本地；生产必须显式配置）。
4. 签发与重签时写入 `key_ciphertext`；`GET /api/admin/keys/:id`（需管理员会话）解密返回 `apiKey` + `displayName`。
5. 历史行无密文时：查看返回明确错误，提示重签以生成可查看 Key。

## Rationale
| 方案 | 取舍 |
| --- | --- |
| 明文列 | 实现简单；库备份即等于全量 Key 泄露 |
| **AES-GCM 密文列 + 仍存 hash** | 管理可查看；磁盘泄漏需同时拿到加密密钥；鉴权路径不变 |
| 外置 KMS/保险柜 | 更强；MVP 过重 |

## Consequences
- 管理员会话可反复取回有效 Key 明文；吊销后的 Key 仍可解密但不应用于新鉴权（列表已隐藏）。
- 轮换 `API_KEY_ENCRYPTION_SECRET` 会导致旧密文无法解密（需重签或迁移脚本）。
- 日志与审计仍禁止打印明文；仅经 TLS 管理 API 返回。

## Date
2026-08-11
