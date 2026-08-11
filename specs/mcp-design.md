# MCP 技术设计 — kb-agent

对齐文档：`specs/req.md`、`specs/architecture.md`、`specs/agent-design.md`、`specs/rag-design.md`、`specs/mvp-2-3-delivery.md`、`specs/story-mapping.md`（模块 **MCP**：`mcp-01`…`mcp-06`）。

本文专述 **MCP 门面**：传输、鉴权、工具注册、与 REST 的契约对齐、Cursor/ChatBox 接入。  
领域语义（propose / confirm / 越界码）以 `agent-design.md` 为准；本文不重复业务状态机全文。

不含排期日期。实施批次：**MVP-2** 最小工具集；**MVP-3+** 扩展工具面。

---

## 1. 定位与原则

### 1.1 角色（agent-builder）

| 角色 | 谁 | 做什么 |
| --- | --- | --- |
| Agent 循环 | Cursor / ChatBox / 宿主 LLM | 选工具、解读结果、对用户说话、写业务结论 |
| Harness | kb-agent **MCP Server** | 暴露少而清晰的 tools；鉴权；截断；透出稳定 `code` |
| 领域层 | `KbService`（与 REST 共用） | 唯一业务实现；MCP **禁止**第二套逻辑 |

**不在 MCP 内：** 服务端 `while model.tool_calls`、业务策略工具、把整库塞进 prompt、静默 confirm。

### 1.2 设计约束

1. **薄门面** — MCP 只做协议适配 + 参数校验 + 调用 `KbService`。  
2. **少工具** — MVP-2 仅 3～4 个；全量能力表见 `agent-design.md` §4，按批 unlock。  
3. **同一把 Key** — 与 REST 相同 `Authorization: Bearer <api_key>` → 同一 `user_id`。  
4. **身份不可覆盖** — 工具参数不得接受客户端 `user_id`；租户只来自 Key。  
5. **写入两步** — propose → confirm；工具描述写死「不会自动入库」。  
6. **上下文卫生** — 结果截断规则与 `agent-design.md` §9 一致。  
7. **契约同源** — 工具名 / 入参 / 出参字段与 REST 对齐；漂移用 `contracts/mcp-tools.json` 门禁。

### 1.3 非目标

- stdio 作为生产主路径（本地调试可选；公网 / Cursor 远程以 HTTP 为准）  
- 在 MCP 内实现 OAuth Authorization Server（产品 Key 已由 Admin 签发）  
- Resources / Prompts 作为 MVP-2 交付物（可后补只读 resource；不阻塞 `mcp-01`…`mcp-05`）  
- 把 Admin Cookie JWT 当作 MCP 凭证  

---

## 2. 运行时拓扑

```text
┌──────────────────────────────────────────┐
│ Cursor / ChatBox / MCP Inspector         │
│  Cursor: Streamable HTTP → /mcp          │
│  ChatBox: http/sse → /sse (+ /messages/) │
│  Header: Authorization: Bearer <api_key> │
└────────────────────┬─────────────────────┘
                     │ HTTPS or http://127.0.0.1:8000
                     ▼
┌──────────────────────────────────────────┐
│ kb-agent (FastAPI, :8000)                │
│                                          │
│  GET  /healthz                           │
│  POST /api/v1/kb/*     ← REST 门面       │
│  ALL  /mcp             ← Streamable HTTP │
│  GET  /sse             ← legacy SSE      │
│  POST /messages/       ← SSE posts       │
│                                          │
│  Auth (pepper+sha256 → user_id)          │
│       ↓                                  │
│  KbService → RAG / KM / Blob / Postgres  │
└──────────────────────────────────────────┘
```

生产：Nginx Proxy Manager 将 `/mcp`、`/sse`、`/messages/`（及 `/api/v1/kb/*`）反代到 `kb-agent:8000`（见 `deployment-plan.md`）。  
本地：Cursor `http://127.0.0.1:8000/mcp`；ChatBox `http://127.0.0.1:8000/sse`。起栈推荐 `make up-daemon`（见 `knowledge/ops/local-apps-keep-dying.md`）。

**进程模型：** MCP 与 REST **同进程同应用**（同一 uvicorn），共享连接池与配置；禁止单独起第二个「只有 MCP」的业务副本以免双实现。

---

## 3. 传输

| 项 | 决策 |
| --- | --- |
| 主传输 | **Streamable HTTP**（MCP 规范当前推荐；Cursor：`/mcp`） |
| 路径 | **`/mcp`**（固定；裸 `/mcp` 与 `/mcp/` 均须可用——Starlette `Mount` 只匹配 `/mcp/…`，服务端将裸路径改写为 `/mcp/`） |
| 遗留 SSE | ChatBox `http/sse`：`GET /sse` + `POST /messages/`（与 Streamable 并存） |
| stdio | 可选开发入口（`python -m app.mcp_stdio`）；**不**作为 Cursor 手测 DoD 主证据 |
| TLS | 生产终止于 NPM；本地明文 `127.0.0.1` 可接受 |

实现选用官方 **Python MCP SDK**（`mcp` 包）的 FastMCP / Streamable HTTP，**挂载**到现有 FastAPI app（`mount` 或 SDK 提供的 ASGI 集成）。实现时以当时 SDK 文档为准；本文约束语义与路径，不锁死某一小版本方法名。

会话：若传输带 `Mcp-Session-Id`，须与创建会话时的 Bearer **绑定**；换 Key 复用 session → 拒绝（404/401，与 SDK 行为对齐）。

---

## 4. 鉴权

### 4.1 凭证

| 规则 | 说明 |
| --- | --- |
| 方案 | 管理台签发的 **使用者 API Key**（`kb_live_…`） |
| Header | `Authorization: Bearer <raw_key>` |
| 哈希 | 与 REST 相同：`sha256(API_KEY_PEPPER + raw)` |
| 查找 | `api_keys` join `users`；`key.status=active` 且 `user.status=active` |
| 失败 | 无/坏 Header → `UNAUTHORIZED`；吊销 → `REVOKED_KEY` / `KEY_REVOKED`（与 REST 码表统一） |

**禁止：** 把 Key 放进 query string、工具参数、或 MCP URL 路径。

### 4.2 请求上下文

鉴权成功后把 `AuthContext(user_id, api_key_id, key_prefix)` 写入 **contextvar**（或等价请求作用域），工具 handler **只读上下文**，不从 args 取身份。

推荐与现有 `app/auth.py` 的 `require_bearer` **共用同一校验函数**，避免 MCP / REST 哈希或状态判断分叉。

### 4.3 与 MCP OAuth 草案的关系

产品已有 Admin 签发的长期 API Key。MVP-2 **不**实现完整 OAuth AS。若日后 SDK/Cursor 强制 OAuth 元数据，可增加 stub `/.well-known/*` 或 TokenVerifier 包装「把 Bearer API Key 当 opaque token」——仍须落到同一 `user_id` 解析，不得引入第二套用户体系。

---

## 5. 工具表面

### 5.1 MVP-2（`mcp-01`…`mcp-05` 必达）

仅注册下列 tools（名称稳定；实现前写入 `contracts/mcp-tools.json`）：

| Tool | REST 等价 | 副作用 | 说明 |
| --- | --- | --- | --- |
| `kb_internal_search` | `POST /api/v1/kb/search` | 无 | 已有 REST；MCP 同语义；MVP-2 须真命中+citation |
| `kb_propose_add` | `POST /api/v1/kb/proposals` | Pending | 粘贴/正文；KM 写入 ≤400 字内容概述；不写 Qdrant |
| `kb_confirm_add` | `POST /api/v1/kb/proposals/{id}/confirm` | **写库+索引** | 显式确认 |
| `kb_list_knowledge` | `GET /api/v1/kb/items` | 无 | **可选同批**；列表含 `summary` |
| `kb_knowledge_summary` | `GET/POST .../items/{id}/summary` | 仅 refresh 写元数据 | 读概述；`refresh` 可重生 |

概述语义见 [`knowledge-summary.md`](./knowledge-summary.md)。

**不**在 MVP-2 注册：`kb_import_*`、`kb_organize`、`kb_external_search`、`kb_fetch_url`。

### 5.2 全量路线图（unlock 时再注册）

见 `agent-design.md` §4 全表。原则：每增工具 = 同批 REST + 契约更新 + 截断/越界检查。

### 5.3 工具描述（schema `description` 必含）

每个写工具描述必须包含（中英择一为主语言，建议中英要点并列或英文为主 + 中文边界）：

- Will not auto-ingest; requires explicit confirm  
- Does not generate business strategy / campaign conclusions  
- Operates only on the knowledge base bound to this API Key  

`kb_internal_search`：Returns citable fragments; the host model composes the user-facing answer.

### 5.4 输入 / 输出形状（概念；以实现契约为准）

```text
kb_internal_search
  in:  { query: string, project?: string, tags?: string[], top_k?: number }
  out: { hits: Hit[], sufficiency: { enough: boolean, reason?: string } }
  Hit: { knowledge_id, chunk_id, text, score?, title?, project?, tags? }
  # 禁止参数: user_id

kb_propose_add
  in:  { text: string, title?: string, project?: string, tags?: string[] }
  out: { pending_id, status: "proposed", summary? (<=400字概述), suggested_type?, duplicate_hint? }

kb_confirm_add
  in:  { pending_id: string }
  out: { knowledge_id, status: "confirmed", indexed: true }

kb_list_knowledge
  in:  { project?: string, tag?: string, knowledge_type?: string, limit?: number }
  out: { items: [{ knowledge_id, title, summary?, project?, tags?, updated_at? }] }

kb_knowledge_summary
  in:  { knowledge_id?: string, pending_id?: string, refresh?: boolean }
  # knowledge_id 与 pending_id 二选一（同一 UUID）
  out: { knowledge_id, title?, status?, summary, refreshed: boolean }
```

错误：工具结果或 MCP 错误载荷统一可解析为：

```json
{ "code": "OUT_OF_SCOPE_AUTO_INGEST", "message": "...", "degrade_hint": "kb_propose_add" }
```

码表与 `agent-design.md` §6.2 / `architecture.md` 一致。成功路径不得返回捏造的 `knowledge_id` / `chunk_id`。

### 5.5 Server instructions

MCP `instructions`（若 SDK 支持）写入短边界，与 `agent-design.md` §8 建议稿一致，供宿主展示；**不替代**工具层硬拒绝。

---

## 6. 与 REST / KbService 的关系

### 6.1 强制结构

```text
MCP tool handler  ──┐
                    ├──► KbService.<use_case>(user_id, ...)
REST route handler ─┘
```

今日（MVP-1）检索逻辑仍在 route 内；**MVP-2 实施顺序建议：**

1. 抽出 `KbService.search` / `propose_ingest` / `confirm_ingest` / `list_items`  
2. REST 改为调用 Service  
3. 再挂 MCP handlers → 同一 Service  

禁止：MCP handler 内直接 `httpx` 调 RAG 而 REST 走另一路径。

### 6.2 契约门禁

| 产物 | 用途 |
| --- | --- |
| `contracts/search-response.schema.json` | 已有；search 出参 |
| `contracts/mcp-tools.json`（已建初稿） | 工具名、JSON Schema 入参、出参摘要、REST 路径映射 |
| 测试 | 同 Key、同输入：MCP tool 结果与 REST JSON **字段级一致**（允许包装层差异，核心 payload 一致） |

### 6.3 幂等与重试

- `kb_internal_search` / `kb_list_knowledge` / `kb_knowledge_summary`（`refresh=false`）：只读，可重试  
- `kb_knowledge_summary`（`refresh=true`）：幂等写元数据（同正文可重复刷新）  
- `kb_propose_add`：允许内容 hash 幂等（同文同用户 → 同 pending 或明确 duplicate）  
- `kb_confirm_add`：已确认再 confirm → 返回已确认态，不双写索引（Indexer 幂等）

---

## 7. 客户端接入

### 7.1 Cursor / CodeBuddy（MVP-2 DoD 证据）

UI 图文步骤见 Admin「接入指南」`/guide` §3（截图：Settings → Customize → MCPs → `mcp.json`）。

**路径 A — 本地 stdio（与截图一致）**

1. Cursor Settings → **Customize** → **MCPs** → **New MCP Server**  
2. 按 [`deployment-plan.md`](./deployment-plan.md) §7.1 B 填写 `mcp.json`（`python -m app.mcp_stdio` + `KB_API_KEY` / `API_KEY_PEPPER` 等）  
3. CodeBuddy：在 MCP / 插件设置中用同类 `mcp.json` 字段

**路径 B — 远程 Streamable HTTP（手测备选）**

1. Transport = Streamable HTTP / Remote MCP  
2. URL：本地 `http://127.0.0.1:8000/mcp`；生产 `https://kb.agent-mate.ai/mcp`  
3. Auth：`Authorization: Bearer <api_key>`（管理台签发；可列表「查看」；**勿**写入仓库或公开截图）

| 项 | 值 |
| --- | --- |
| Transport | Streamable HTTP（或 Cursor 标注的等价 Remote MCP） |
| URL | 本地 `http://127.0.0.1:8000/mcp`；生产 `https://kb.agent-mate.ai/mcp` |
| Auth | Bearer = 使用者 Key 明文（勿提交 git） |

已实现工具（MVP-2）：`kb_internal_search`、`kb_propose_add`、`kb_confirm_add`、`kb_list_knowledge`、`kb_knowledge_summary`。均走同一 `KbService`。

手测剧本（与 `mvp-2-3-delivery.md` §3.2 一致）：

```text
propose(text) → 库内 search 仍无该条正式知识
confirm(pending_id) → search 出现 citation
换另一用户 Key → 搜不到
```

Admin「接入指南」页（`/guide`）§3–§4 为图文步骤；完整模板见 [`deployment-plan.md`](./deployment-plan.md) **§7.1**。

### 7.2 ChatBox

UI 图文步骤见 `/guide` §4。自定义 MCP：**Remote (http/sse)**（遗留 SSE，不是 Streamable HTTP）。

| 字段 | 值 |
| --- | --- |
| Type | Remote (http/sse) |
| URL | `http://127.0.0.1:8000/sse`（**不要**填 `/mcp`） |
| HTTP Header | `Authorization=Bearer <api_key>` |

工具集与 Cursor 相同。消息通道：`POST /messages/`（由 SSE 握手下发，无需手填）。

> Cursor 继续用 Streamable HTTP：`http://127.0.0.1:8000/mcp`。ChatBox 的 http/sse 模式会对 `/mcp` 发 SSE GET → **404**；须改用 `/sse`。

### 7.3 HCP / 应用

优先 **REST**；若嵌入 MCP Client，同一 Key、同一工具语义。

### 7.4 调试

- MCP Inspector：Streamable HTTP + Bearer  
- `GET /healthz` 不鉴权，仅探活，不证明 MCP 可用  

---

## 8. 可观测与安全

### 8.1 日志字段

`user_id`、`key_prefix`、`tool_name`、`latency_ms`、`code?`、`hit_count?`、`pending_id?`、`knowledge_id?`。  
**禁止**日志打印完整 Bearer 或明文 Key。

### 8.2 审计

至少：`kb_confirm_add` 成功；日后 `import_confirm` / `organize(apply=true)`。

### 8.3 滥用与成本

| 风险 | 缓解 |
| --- | --- |
| 大 `text` propose | 请求体大小上限（与 REST 同） |
| 高频 search | 可选每 Key 速率限制（MVP-2 可先日志；MVP-3+ 再硬限） |
| 结果撑爆宿主上下文 | 强制 top_k / 每 hit 字符上限 |

### 8.4 SSRF / 出站

MVP-2 无 `kb_fetch_url`。日后 fetch 工具须走 Source Router 的 URL 允许规则（architecture §7），与 REST 同。

---

## 9. 实现草图（非规范锁死）

目录建议（可微调）：

```text
services/kb-agent/app/
  main.py           # FastAPI：mount REST + MCP
  auth.py           # 共用 Bearer
  kb_service.py     # 领域用例
  mcp_server.py     # FastMCP 工具注册 → KbService
  routes/kb.py      # REST → KbService
```

依赖：在 `pyproject.toml` / `requirements.txt` 增加官方 `mcp`（版本钉死）；实现前对照当时 [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk) / Streamable HTTP 文档。

伪代码：

```python
# mcp_server.py — 示意
mcp = FastMCP("kb-agent", instructions=KB_INSTRUCTIONS)

@mcp.tool(description="... no auto-ingest ...")
async def kb_internal_search(query: str, top_k: int = 8) -> dict:
    ctx = current_auth()  # from contextvar
    return await kb_service.search(user_id=ctx.user_id, query=query, top_k=top_k)
```

挂载：Streamable HTTP ASGI 挂到 FastAPI `/mcp`；SSE 路由注册为 `GET /sse` 与 `POST /messages/`；鉴权中间件覆盖上述路径（勿用会破坏流式响应的错误中间件写法）。

---

## 10. 测试策略（扩展 test-strategy）

| 层 | 内容 |
| --- | --- |
| 单元 | 工具参数拒绝 `user_id`；截断；越界码（scope-03/04） |
| 契约 | `mcp-tools.json` ↔ REST OpenAPI/路由；无「skip_confirm」参数 |
| 集成 | 同进程：MCP client（SDK）+ REST client，同 Key propose→confirm→search |
| 手测 | Cursor 配置证据（截图或文字记录 URL 形态，**不含** Key） |
| 回归 | 吊销 Key → MCP 与 REST 均 401；提案未 confirm 不进 search 命中 |

CI：可用 MCP SDK 内存/HTTP 客户端打 `/mcp`；**Done 门禁**禁止 Fake Embedder（见 `mvp-2-3-delivery.md`）。

---

## 11. 验收对照（`mcp-01`…`mcp-05`）

| AC（摘要） | 设计落点 | 故事 |
| --- | --- | --- |
| Streamable HTTP + `/mcp` | §3 | mcp-01 |
| Bearer Key；禁 query | §4 | mcp-02 |
| 仅注册最小工具集 | §5.1 | mcp-03 |
| 与 REST 同 `KbService` / 契约 | §6 | mcp-04 |
| Cursor propose→confirm→search | §7.1 | mcp-05 |
| MVP-3 扩展工具面 | §5.2 | mcp-06 |
| 未确认不进正式检索 | `kb_propose_add` / Indexer 规则（rag-design） |

---

## 12. 反模式

| 反模式 | 为何禁止 |
| --- | --- |
| MCP 内再写一套 RAG/SQL | 双实现、租户漏洞 |
| 工具参数带 `user_id` | 身份覆盖 |
| Key 进 URL | 泄露进日志/历史 |
| MVP-2 注册 import/source/org | 超出闭环、拖垮 Cursor 手测 |
| 服务端业务 Agent 循环 | 违背方案 2 / agent-builder |
| 成功返回伪造 citation | scope-04 |
| 默认 Fake Embedder 当 Done | 闭环门禁失败 |

---

## 13. 文档关系

| 文档 | 职责 |
| --- | --- |
| **本文** | MCP 传输、鉴权、工具注册、客户端、契约、实现边界 |
| `agent-design.md` | 全量工具语义、越界、交互序列、截断 |
| `knowledge-summary.md` | 内容概述 ≤400 字；`kb_knowledge_summary` |
| `architecture.md` | 系统拓扑、REST 表、部署 |
| `mvp-2-3-delivery.md` | 批交付与无 mock DoD |
| `keys.md` | `AGENT_BASE_URL`、本地 `/mcp` 与 `/sse`、生产域名 |
| `deployment-plan.md` | NPM `/mcp`、`/sse`、`/messages/` location |

---

## 14. 小结

kb-agent 的 MCP = **双传输薄工具门面**：Cursor 走 Streamable HTTP（`/mcp`）；ChatBox 走遗留 SSE（`/sse`）；Bearer 一人一库、当前 **5** 个工具、与 REST 共享 `KbService`。智能留在调用方模型；本服务保证可引用、可确认、可多客户端共用一把 Key。
