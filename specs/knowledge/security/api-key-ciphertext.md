---
title: API Key ciphertext for admin view
date: 2026-08-11
tags: [security, api-keys, admin]
related:
  - adr/ADR-007-api-key-ciphertext-storage.md
---

# API Key 密文存库（管理台可查看）

## Lesson
鉴权用不可逆 `key_hash`；管理台「查看」需要可逆 `key_ciphertext`（AES-256-GCM）。二者并存，职责分离。

## Practice
- 签发/重签同时写 hash + ciphertext。
- 环境变量 `API_KEY_ENCRYPTION_SECRET`（生产必设）；本地可回退 pepper。
- 历史无密文行：查看返回 `CIPHERTEXT_MISSING`，引导重签。
- 轮换加密密钥会使旧密文失效。
- 吊销：用给定 key id 解析 `user_id`，再吊销该用户全部 `active` Key（ADR-010；避免重签后旧 id 空操作）。

## See also
- ADR-007：`specs/adr/ADR-007-api-key-ciphertext-storage.md`
