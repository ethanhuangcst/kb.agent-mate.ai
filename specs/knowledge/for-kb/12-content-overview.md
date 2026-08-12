# 知识内容概述：summary ≤400 字

每条知识有字段 `summary`，用作 **内容概述**（不是标题一行）。长度上限 **400** 个 Unicode 字符。

## 何时生成

- **提案时**（`kb_propose_add` / `POST /api/v1/kb/proposals`）：由平台模型写一次概述。
- **刷新**：`kb_knowledge_summary(..., refresh=true)`，或 REST `POST /api/v1/kb/items/{id}/summary/refresh`。

## 怎么读

- MCP：`kb_knowledge_summary`（可用 `knowledge_id` 或 `pending_id`）
- REST：`GET /api/v1/kb/items/{id}/summary`
- 列表与检索命中里也会带上概述（`kb_list_knowledge`、`kb_internal_search`）

## 补短概述

若概述过短或空：对已确认条目调用 `kb_knowledge_summary(knowledge_id=…, refresh=true)`。需要正文 blob 仍在；**不会**因此重跑向量索引。

## 不要做的事

- 不要把 RAG 切块原文拼成概述。
- 不要在每次搜索时现调模型编造概述。
