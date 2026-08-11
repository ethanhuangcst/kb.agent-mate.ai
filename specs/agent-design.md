# Agent 技术设计 — kb-agent

对齐文档：`specs/req.md`、`specs/architecture.md`、`specs/rag-design.md`、`specs/story-mapping.md`、`specs/mvp-2-3-delivery.md`。

本文描述：**如何把能力交给调用方侧的模型**（MCP 为主），以及服务端工具实现与越界护栏。采纳 agent-builder 原则——**模型在调用方；kb-agent 是 harness（工具 + 知识管道），不做业务工作流引擎**。

实施批次与闭环 DoD 见 `specs/mvp-2-3-delivery.md` / `specs/story-mapping.md`「MVP 规划」。不含排期日期。

---

## 1. 定位

| 角色 | 谁 | 做什么 |
| --- | --- | --- |
| Agent（推理循环） | Cursor / ChatBox / HCP 内的 LLM | 理解意图、选工具、消费命中、写业务结论 |
| Harness（本服务） | kb-agent MCP + REST + 领域服务 | 鉴权、执行工具、RAG、提案确认、外部补给、越界拒绝 |
| 内部 KM LLM | Qwen（DashScope） | 仅分类 / 摘要 / organize 建议 / 可选改写 |

**方案 2：** 不在服务端为「无 LLM 调用方」跑全功能业务 Agent。可选 OpenAI 兼容薄门面仅调试用，且必须执行同一套工具与越界规则。

---

## 2. 设计原则

1. **少而清晰的工具** — 能力表固定；描述写清输入输出与禁止事项。  
2. **信任调用方模型选工具** — 服务端不做 DAG 编排「先搜再总结再策略」。  
3. **知识按需经工具加载** — 禁止把整库塞进 system prompt。  
4. **写入两步** — propose → confirm（含批量）。  
5. **越界硬拒绝** — 稳定 `code`，可附带降级检索。  
6. **上下文卫生** — 工具结果截断（top-k、最大字符）。

---

## 3. 运行时拓扑

```text
┌─────────────────────────────────────┐
│ 调用方宿主（ChatBox / Cursor / HCP） │
│  LLM Agent Loop                     │
│   think → tool_call → observe → …   │
└─────────────────┬───────────────────┘
                  │ MCP (或 REST 由宿主自行编排)
                  │ Bearer API Key
                  ▼
┌─────────────────────────────────────┐
│ kb-agent                            │
│  Auth → Tool Dispatcher → KbService │
│       → RAG / SourceRouter / QwenKM │
└─────────────────────────────────────┘
```

MCP Server 与 REST 调用**同一** `KbService` 方法，避免双实现。

---

## 4. 工具清单（能力表面）

控制在「检索 / 补给 / 写入确认 / 整理」；不增加业务策略工具。

| 工具名 | 简述 | 副作用 |
| --- | --- | --- |
| `kb_search` | 库内混合检索，返回 hits + sufficiency | 无 |
| `kb_list` | 按 project/tag/type/时间列表 | 无 |
| `kb_organize` | 体系摘要或标签/分类调整建议；写操作需明确 flag | 视参数 |
| `kb_source_search` | 源路由外部候选（不入库） | 无（出站） |
| `kb_fetch` | URL 拉正文 | 无（出站） |
| `kb_propose_ingest` | 粘贴/正文 → Pending | Pending |
| `kb_confirm_ingest` | 确认单条 Pending → 索引 | **写库** |
| `kb_import_documents` | 多文件 → ImportBatch + Pendings | Pending |
| `kb_confirm_import_batch` | 批确认 | **写库** |

### 4.0 MVP-2 最小表面（Cursor 手测优先）

**MVP-2** 先交付薄 MCP + 知识闭环，便于在 Cursor 中手动添加 MCP 验真。本批**仅注册**下列工具（名称以实现为准，语义固定）：

| 工具名 | REST 等价（概念） | MVP |
| --- | --- | --- |
| `kb_search` | `POST /api/v1/kb/search` | 1 空检索；2 真命中+citation |
| `kb_propose_ingest` | propose 正文/粘贴 | 2 |
| `kb_confirm_ingest` | confirm → 索引 | 2 |
| `kb_list_knowledge`（可选同批） | list | 2 |

硬约束：

- MCP 与 REST **同一** `KbService`；禁止第二套业务逻辑。  
- 传输：Streamable HTTP（推荐本地 `http://127.0.0.1:8000/...`）或 Cursor 支持的等价远程 MCP；Bearer = 管理台签发的使用者 Key。  
- DoD：`USE_FAKE_EMBEDDER=false`；真 Qdrant；Cursor 手测 propose→confirm→search。  
- **不**在 MVP-2 暴露 import / source_search / fetch / organize（属 MVP-3 / MVP-4）。

### 4.1 工具描述要点（写入 MCP schema description）

每个写工具必须包含：

- 「不会自动入库；需 confirm」  
- 「不生成业务策略 / 投放结论 / 竞品战略」  
- 「仅操作用户 Key 所属知识库」

`kb_search` 说明：返回供引用的片段；由调用方模型组织对用户的回答。

### 4.2 建议参数形状（概念）

```text
kb_search(query, project?=, tags?=, top_k?=)
kb_list(project?=, tag?=, knowledge_type?=, limit?=)
kb_organize(action=summarize|retag|reclassify, …, apply?=false)
kb_source_search(query, constraints?=, project?=)
kb_fetch(url)
kb_propose_ingest(text, title?=, project?=, tags?=)
kb_confirm_ingest(pending_id)
kb_import_documents(files[], default_project?=, default_tags?=)  # MCP 侧或走 REST multipart
kb_confirm_import_batch(batch_id, pending_ids?=, confirm_all_viable?=false)
```

大文件批量更适合 **REST multipart**；MCP 可返回「请改用 REST /imports」或传文件引用——实现时二选一，契约保持批确认语义。

---

## 5. 服务端调度（非 Agent 循环）

```text
on tool_call(name, args, user_id):
  validate args
  if violates_policy(name, args): return error(code)
  result = KbService.*(user_id, ...)
  return truncate(result)
```

**没有**服务端 `while model.tool_calls` 作为主路径。薄 Chat 门面若启用：

```text
loop (max_iters):
  qwen_km_or_chat with tools=kb_tools  # 仅 KM 场景
  if tool_calls: execute → continue
  else: return message
  enforce: same OUT_OF_SCOPE codes; no business-strategy tools
```

薄门面不得扩大 Qwen 职责至业务洞察。

---

## 6. 越界与策略引擎

### 6.1 检测（务实组合）

1. **工具层：** 不存在 `generate_strategy` 类工具 → 结构上难越界。  
2. **参数 / 意图启发式（KbService 入口）：** 对「自由文本指令」类可选入口（若有）做关键词/分类器；MCP 主路径以工具为准。  
3. **organize / propose 的用户说明字段：** 若检测到「请直接给出投放策略」等，返回 `OUT_OF_SCOPE_BUSINESS_REASONING`，可建议改用 `kb_source_search`。  
4. **confirm：** 不接受「auto_ingest_all_web=true」。

### 6.2 错误码（与架构一致）

| code | 何时 |
| --- | --- |
| `OUT_OF_SCOPE_BUSINESS_REASONING` | 业务洞察 / 策略 |
| `OUT_OF_SCOPE_AUTO_INGEST` | 要求无确认入库 |
| `INSUFFICIENT_KB_EVIDENCE` | 可选：调用方要求「必须库内作答」且 hits 空 |
| `UNAUTHORIZED` / `REVOKED_KEY` | 鉴权 |
| `PENDING_NOT_FOUND` / `PENDING_EXPIRED` | 确认失败 |
| `FETCH_BLOCKED` / `IMPORT_FILE_REJECTED` | 出站或上传校验 |

错误体：`{ "code", "message", "degrade_hint?" }`。`degrade_hint` 可提示合法工具名，不含策略内容。

### 6.3 坏例子应对（实现检查清单）

请求：「根据我们 HCP 本周数据，上网查竞品并给出投放策略。」

- 若经薄 Chat：模型若乱调工具，仍**不得**有「输出策略」的服务端成功路径；最终回复模板拒绝策略部分。  
- 若仅 MCP：无策略工具；调用方模型若自行编造策略，不属 kb-agent 输出。  
- 允许：`kb_source_search("竞品 X 公开能力")` → 候选列表。

---

## 7. 典型交互序列

### 7.1 库内问答（调用方模型消费）

```text
User → 宿主 LLM
LLM → kb_search(q)
kb → Hits[]
LLM → 用 hits 生成对用户回答（带引用 id）
```

### 7.2 外部补给并入库

```text
LLM → kb_search(q)           # 不足
LLM → kb_source_search(q)
LLM → kb_fetch(url)          # 用户/模型选定
LLM → kb_propose_ingest(text)
LLM → 向用户展示提案，等待确认
User → 「确认」
LLM → kb_confirm_ingest(pending_id)
```

### 7.3 批量文档

```text
Client → POST /imports (multipart)   # 或 MCP 等价
kb → batch_id + pendings[]
User/LLM → kb_confirm_import_batch(..., confirm_all_viable=true)
```

### 7.4 体系整理

```text
LLM → kb_list / kb_organize(action=summarize)
LLM → 展示建议
LLM → kb_organize(..., apply=true)  # 或先提案再确认（若破坏性变更）
```

---

## 8. System / 工具提示（调用方侧建议稿）

供使用者贴进 ChatBox/Cursor 的短策略（非服务端强制，但推荐）：

```text
你通过 MCP 使用 kb-agent。
- 用 kb_search 取知识；回答基于返回片段并引用。
- 新材料：propose 后必须等用户确认再 confirm。
- 不要让 kb-agent 写业务策略；策略由你结合用户业务数据自行完成。
- 库内不足时可用 kb_source_search / kb_fetch，仍须确认才入库。
```

服务端 MCP `instructions` 字段应包含同样边界摘要。

---

## 9. 上下文与截断

| 结果类型 | 截断规则 |
| --- | --- |
| search hits | `final_k` 条；每条 text ≤ N 字符（可配 1500） |
| source_search | 候选 ≤ M 条；摘要字段短 |
| fetch | 正文硬顶（字节）；超出截断并标记 |
| import batch | 返回每文件摘要，不回传全文到 MCP 若过大 |

---

## 10. 鉴权与多租户

- 每个 MCP / REST 请求：Bearer Key → `user_id`  
- 工具实现禁止接收客户端传入的 `user_id` 覆盖  
- 一人一库：无「切换 workspace」工具  

---

## 11. 与 RAG / 源路由的衔接

| Agent 工具 | 下游 |
| --- | --- |
| `kb_search` | `Retriever`（rag-design） |
| `kb_confirm_*` | `Indexer`（rag-design） |
| `kb_propose_*` / import | Deduper + QwenKM 元数据 + Pending |
| `kb_source_search` / `kb_fetch` | Source Router / Fetch（architecture §7） |

---

## 12. 可观测性

日志字段：`user_id`、`key_prefix`、`tool_name`、latency、`code`（若错误）、hit_count / pending_id / batch_id。  
审计：confirm / import_confirm / organize(apply=true)。

---

## 13. 测试要点

| 层 | 内容 |
| --- | --- |
| 单元 | 越界码、截断、一人 Key 绑定、confirm 状态机 |
| 契约 | MCP schema 与 REST 对齐；无「跳过确认」参数 |
| 集成 | search→propose→confirm；batch import→confirm；跨用户隔离 |
| 场景 | HCP 策略类话术拒绝；合法 source_search 仍可用 |

---

## 14. 反模式

- 服务端再包一层「万能业务 Agent」循环  
- 工具数量膨胀（邮件、日历、CRM…）  
- 将整库或长 fetch 灌入单次 tool_result  
- 静默 confirm  
- 合成答案 API 直接当知识写入  

---

## 15. 小结

kb-agent 的 Agent 设计 = **稳定工具面 + 强写入确认 + 越界硬挡 + RAG/补给后端**。智能在调用方模型；本服务把私人知识库用得安全、可引用、可多客户端共用一把 Key。
