# RAG 技术设计 — kb-agent

对齐文档：`specs/req.md`、`specs/architecture.md`、`specs/mcp-design.md`、`specs/mvp-2-3-delivery.md`。本文细化**库内检索增强生成管道**与确认后索引；外部源路由见架构 §7，本文只定义与 RAG 相交的接口。

应用元数据与 Pending 状态在 **PostgreSQL**；向量在 **Qdrant**。检索结果经 MCP/REST 同一 `KbService` 暴露（见 `mcp-design.md`）。MVP-2 闭环交付须 `USE_FAKE_EMBEDDER=false` + 真 DashScope embed（见 `specs/mvp-2-3-delivery.md`）。不含排期日期。

---

## 1. 目标与范围

### 1.1 目标

在 VPS 上为每位使用者维护隔离的知识索引，提供：

1. **确认后索引**：正文 → 分块 → 向量 → Qdrant（带 `user_id`）
2. **库内检索**：混合检索（稠密 + 稀疏）→ 融合 → 结构化命中（供 MCP/REST / 调用方 LLM）
3. **查重辅助**：精确 hash + 近邻，服务 propose 阶段

### 1.2 非范围

- 调用方业务答案生成（属调用方 LLM）
- 外部 Web 搜索实现细节（属 Source Router；RAG 只消费「已确认正文」或「库内 chunk」）
- 训练 / 微调 embedding 模型

### 1.3 设计原则

| 原则 | 含义 |
| --- | --- |
| 索引滞后于确认 | 无 `confirm` 不写 Qdrant / 正式 `KnowledgeItem` |
| 租户隔离 | 所有 upsert / search 强制 `user_id` filter |
| 可引用 | 命中必须带回 `knowledge_id`、`chunk_id`、原文定位信息 |
| 混合检索 | 语义 + 关键词，降低专有名词漏检 |
| 配置化模型 | embedding 模型 ID 与维度仅来自配置 |

---

## 2. 组件与数据流

```text
                    ┌─────────────┐
  confirm 正文 ───► │ Indexer     │──► BlobStore（原文）
                    │             │──► PostgreSQL（KnowledgeItem/Chunk 元数据）
                    │             │──► Embedder ──► Qdrant
                    └─────────────┘

  query + user_id ─► │ Retriever   │
                     │  dense      │──► Qdrant
                     │  sparse     │──► BM25 或 Qdrant 全文
                     │  RRF fuse   │
                     │  dedupe     │──► Hit[]（结构化）
                     └─────────────┘
```

| 组件 | 职责 |
| --- | --- |
| `TextNormalizer` | Unicode 规范化、空白折叠、可选去 HTML |
| `Chunker` | RecursiveCharacter 分块 |
| `Embedder` | DashScope Qwen embedding 批调用 |
| `Indexer` | confirm 后写入三存储 |
| `DenseStore` | Qdrant 客户端 |
| `SparseIndex` | 每用户或全局+filter 的 BM25；或 Qdrant sparse/full-text |
| `Retriever` | 混合检索 + RRF + 去重 |
| `Deduper` | content_hash + 向量近邻（propose 用） |

---

## 3. 分块（Chunking）

| 参数 | 建议默认 | 说明 |
| --- | --- | --- |
| 策略 | `RecursiveCharacterTextSplitter` | 分隔符优先：段落 → 换行 → 句 → 字符 |
| `chunk_size` | 约 600–800 tokens（或 1200–1600 字符作近似） | 中英混合可配置 |
| `chunk_overlap` | 约 10% | 避免边界切断定义句 |
| 最小块 | &lt; 50 字符可并入邻块或丢弃 | 减少噪声 |
| 元数据 | `knowledge_id`, `user_id`, `version_id`, `ordinal`, `title`, `tags`, `project`, `knowledge_type` | 写入 Qdrant payload |

**版本：** 正文变更并确认后，删除旧 version 的全部 chunk 向量，再写入新 version（避免幽灵命中）。

**批量导入：** 每文件确认后独立走同一 Indexer；不跨文件合并为一个 KnowledgeItem（除非产品日后增加「合并」能力）。

---

## 4. 向量与 Qdrant

### 4.1 Embedding

| 项 | 规范 |
| --- | --- |
| Provider | DashScope |
| 模型 | 配置项 `QWEN_EMBED_MODEL`（维度固定后写入 `EMBED_DIM`） |
| 输入 | 单 chunk 文本；过长则先按 chunker 保证上限 |
| 批大小 | 配置（如 16–64），受 API 限流 |
| 失败 | 整次 confirm 事务失败可回滚元数据或标 `index_status=failed` 可重试 |

**中文 / 英文：** 选用 DashScope 多语文本向量模型；换模型须全量重嵌（记录 `embedding_model_id` 于集合或配置快照）。

### 4.2 Collection 设计

建议**单 collection、多租户 filter**（个人规模）：

```text
collection: kb_chunks
point id: chunk_id (UUID)
vector: float[EMBED_DIM]
payload:
  user_id: keyword
  knowledge_id: keyword
  version_id: keyword
  ordinal: int
  title: text
  tags: keyword[]
  project: keyword | null
  knowledge_type: keyword
  content_preview: text   # 前 N 字，便于调试；全文以 PostgreSQL/Blob 为准
  language: keyword
```

索引：`user_id` 必建；`project`、`tags`、`knowledge_type` 按过滤需要建。

**硬约束：** 每次 search 的 filter 必须包含 `user_id == current_user`。

### 4.3 删除与软删

- `KnowledgeItem.deleted_at` 置位 → 异步/同步删除该 knowledge 下所有 points
- 吊销 API Key **不**删向量；仅拒绝新请求

---

## 5. 稀疏检索

**方案 A（推荐基线）：** 在 PostgreSQL 对 `Chunk.text` 做全文检索（`tsvector`/`pg_trgm`，按 `user_id` 过滤），BM25 或等价排序。  
**方案 B：** Qdrant 稀疏向量 / 全文能力（若版本与运维允许）。

无论 A/B，输出统一为 `(chunk_id, sparse_score)` 列表，供融合。

---

## 6. 检索管道（Retriever）

### 6.1 输入 / 输出

**输入**

```text
query: str
user_id: str
filters?: { project?, tags?, knowledge_type? }
top_k_dense: int = 10
top_k_sparse: int = 10
final_k: int = 6..8
```

**输出 `Hit`**

```text
chunk_id, knowledge_id, version_id, ordinal
score_fused, score_dense?, score_sparse?
title, tags, project, knowledge_type
text                    # chunk 正文（或截断后完整可引用段）
body_uri?               # 原文定位
```

### 6.2 步骤

```text
1. （可选）Query rewrite — 内部 Qwen 轻量改写；失败则用原 query
2. Embed(query) → dense search（filter user_id + 可选 metadata）
3. Sparse search（同 filter）
4. RRF 融合：score = Σ 1/(k_rrf + rank_i)，默认 k_rrf=60
5. 权重（可选）：0.7 dense / 0.3 sparse 在 RRF 前对 rank 列表截断或分通道配额
6. 按 knowledge_id 去重（同文档保留最高分 chunk；或保留 top-2 chunk/文档可配置）
7. 截断至 final_k
8. 回填 chunk 全文（PostgreSQL）与 citation 字段
```

### 6.3 「库内是否足够」信号（供 Source Router）

供架构「库内优先」使用的启发式（可配置）：

| 信号 | 示例阈值 |
| --- | --- |
| 命中数 | `final_k` 命中 &lt; 2 |
| 最高融合分 | 低于经验阈值（需校准，先占位配置） |
| 调用方强制 | `force_external=true` 时忽略足够性 |

RAG 模块只返回信号；是否出站由 Source Router / KbService 决定。

---

## 7. 查重（Deduper）

用于 `propose` / 批量导入：

1. `content_hash = sha256(normalize(body))`
2. 若同 `user_id` 已存在相同 hash → 提案标 `duplicate_exact` + 已有 `knowledge_id`
3. 否则 embed 全文或代表 chunk → Qdrant 近邻（高相似度阈值，如 cosine &gt; 0.92，可配）→ `duplicate_near` 候选列表
4. 批内文件：先算 hash 集合，批内重复标 `duplicate_in_batch`

确认时：exact 默认 no-op 或仅合并 tags；near 由调用方在确认前决定覆盖 / 跳过 / 新条（API 参数）。

---

## 8. 确认后索引事务

```text
begin (逻辑事务)
  write BlobStore body_uri
  upsert KnowledgeItem + KnowledgeVersion
  chunk → insert Chunk rows
  embed batches
  upsert Qdrant points
  mark index_status=ready
commit
on failure:
  compensate: delete partial points / mark failed + retry job
```

个人 VPS 可用「同步 confirm + 失败可重试」；不必上独立队列，但接口预留 `reindex(knowledge_id)`。

---

## 9. 与内部 Qwen 的边界

| 步骤 | RAG | 内部 Qwen |
| --- | --- | --- |
| 分块 / 向量 / 检索 | 是 | 否 |
| 提案 title/summary/tags | 否 | 是（propose 管道） |
| query rewrite | 可选触发 | 是 |
| 证据 LLM 打分 | 可选后置 | 是（非基线必做） |
| 业务回答 | 否 | 否 |

---

## 10. 配置项（示意）

```text
QWEN_EMBED_MODEL=
EMBED_DIM=
CHUNK_SIZE_TOKENS=700
CHUNK_OVERLAP_RATIO=0.1
RETRIEVE_FINAL_K=8
RETRIEVE_DENSE_K=10
RETRIEVE_SPARSE_K=10
RRF_K=60
DENSE_SPARSE_WEIGHT=0.7,0.3
DEDUP_NEAR_COSINE=0.92
QDRANT_URL=
QDRANT_COLLECTION=kb_chunks
```

---

## 11. 可观测性与质量

**日志：** `user_id`、query hash、命中数、dense/sparse 耗时、embed 耗时、confirm 索引耗时；不记全文。

**测试：**

| 类型 | 用例 |
| --- | --- |
| 单元 | 分块边界、RRF、hash 规范化、filter 必带 user_id |
| 集成 | confirm → search 命中；跨 user 不可见；软删后不可检；重复 hash 行为 |
| 回归 | 固定语料 golden queries 的 hit@k |

**反模式：** 仅靠 mock 向量宣称检索正确；无 `user_id` 的 search；confirm 前 upsert。

---

## 12. 接口契约（供 Agent / REST）

`kb_search` / `POST /api/v1/kb/search` 返回上述 `Hit[]`，外加可选 `sufficiency` 信号。  
不在 RAG 层返回「最终业务结论」字符串（薄 Chat 门面若拼接，须在 Agent 设计中约束）。
