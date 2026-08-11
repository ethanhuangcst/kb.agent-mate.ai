# 知识内容概述（summary overview）

对齐：`agent-design.md`、`mcp-design.md`、`contracts/mcp-tools.json`。  
决策：方案 **1（propose 时生成）+ 2（`kb_knowledge_summary` 读取/刷新）**（[ADR-009](./adr/ADR-009-content-overview-propose-and-summary-tool.md)）。上限 **400 字**（Unicode 字符）。

## 1. 字段语义

`KnowledgeItem.summary` 存**内容概述**（overview），不是标题句：

| 约束 | 值 |
| --- | --- |
| 上限 | 400 字 |
| 目标长度 | 约 150–400 字（过短应尽量写满要点；过长截断） |
| 内容 | 主题、结构要点、适用范围；不代替全文；不做业务策略/投放结论 |
| 生成 | `kb_propose_add` → KM（真 DashScope；Fake 用启发式长概述） |
| 持久化 | propose 写入；confirm 不改 summary（除非 refresh） |

## 2. 方案 1 — Propose / KM

`KmClient.propose_metadata`：

- Prompt 要求 `summary` 为内容概述，**≤400 字**。  
- 服务端对返回做 `truncate_summary()` 硬截断。  
- Fake KM：取正文前若干段拼成概述，截断至 400。

## 3. 方案 2 — 工具 `kb_knowledge_summary`

| 项 | 说明 |
| --- | --- |
| 入参 | `knowledge_id` 与 `pending_id` 二选一（同一 UUID 空间）；`refresh` 默认 false |
| `refresh=false` | 只读 PG `summary`（及 title/status） |
| `refresh=true` | 读 Blob 正文 → KM 重生概述 → 写回 `summary`（proposed/confirmed 均可；须同租户） |
| 副作用 | 仅 refresh 时写元数据；**不**改 Qdrant、不自动 confirm |
| REST | `GET /api/v1/kb/items/{id}/summary`；`POST .../summary/refresh` |

禁止参数：`user_id`。

## 4. 消费面增强

| 表面 | 行为 |
| --- | --- |
| `kb_propose_add` | 响应继续带 `summary`（应为长概述） |
| `kb_list_knowledge` | 每项增加 `summary` |
| `kb_internal_search` | 每个 hit 增加可选 `summary`（按 knowledge_id join；截断展示可与字段同上限） |

## 5. 旧数据

已入库短 summary：用 `kb_knowledge_summary(..., refresh=true)` 或脚本 backfill。

## 6. 非目标

- 用 RAG chunk 拼接冒充概述  
- 每次 search 都现场 LLM 生成  
- 把 overview 当作可引用全文替代 citation
