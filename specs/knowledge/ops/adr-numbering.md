---
title: Assign ADR numbers from highest existing
type: ops-lesson
status: active
as_of: 2026-08-11
tags:
  - adr
  - process
related:
  - adr/ADR-007-api-key-ciphertext-storage.md
---

# ADR 编号须先看目录最大值

## Summary
同日并行写入时曾出现两个 `ADR-004-*.md`（MCP 共用 KbService vs Key 密文）。密文记录后改为 ADR-007，并全局替换引用。

## Evidence
- `ls specs/adr/` 曾同时存在 `ADR-004-mcp-shares-kbservice.md` 与 `ADR-004-api-key-ciphertext-storage.md`。

## Lesson / guidance
1. 新建 ADR 前：`ls specs/adr/`，取最大 `ADR-NNN` + 1。
2. 文件名与文内标题编号必须一致；引用用稳定路径（`ADR-007-api-key-ciphertext-storage.md`）。
3. 发现撞号：保留先合入/已广泛引用的编号，给后写的一条重新编号并全局搜替换。

## Links
- 现行密文决策：`specs/adr/ADR-007-api-key-ciphertext-storage.md`
