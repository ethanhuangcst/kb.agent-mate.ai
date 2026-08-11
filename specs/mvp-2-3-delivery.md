# MVP-2 / MVP-3 闭环交付规划

对齐：`specs/story-mapping.md`、`specs/test-strategy.md`、`common-test-strategy`、[`specs/mcp-design.md`](./mcp-design.md)。  
前提：**MVP-1 Done**（Admin Key、Bearer、空检索、Blob/PG、禁提案索引）。

---

## 1. 闭环交付定义（本仓库）

一批 MVP **可独立闭环交付**，当且仅当同时满足：

| 条件 | 含义 |
| --- | --- |
| **价值闭环** | 本批故事组成一条完整、可演示的用户旅程；不依赖本批未交付能力才能「看起来可用」 |
| **真实栈验收** | DoD 验收跑在真实进程与真实依赖上：Postgres、Qdrant、kb-agent ↔ kb-rag **真实 HTTP**、本批所需的真实第三方（见下） |
| **禁止替代品** | DoD / 本批回归门禁中：**不得**用 Fake Embedder、假 KM、httpx mock RAG、内存 Outbox 冒充 Resend、Stub SourceAdapter 等 **冒充本批系统行为** |
| **允许的非产品替身** | 仅：独立测试库 / 测试 collection / 临时 Blob 目录 / 每测隔离的 `user_id`；以及厂商提供的 **官方沙箱**（如 Resend test mode）——沙箱仍是真 API，不是代码内 stub |

**与 CI 的关系：** CI 默认可保留廉价 fixture 车道（见 `test-strategy.md`）。**标 `Done` / 宣称本批交付完成**必须以本文「闭环验收套件」全绿为准，不能只靠 mock 车道。

**对上一批的依赖：** 允许依赖已 `Done` 的 MVP（如 Key、Bearer）。不允许把本批关键路径再打成 mock。

---

## 2. 两批切分原则

| 批 | 一句话 | 为何能闭环 |
| --- | --- | --- |
| **MVP-2 知识闭环 + MCP** | MCP 模块 `mcp-01`…`05` + 粘贴→提案→确认→真索引→可引用检索；Cursor 可手挂 MCP 验真 | 领域管道真栈；MCP 仅门面，与 REST 同 `KbService` |
| **MVP-3 操作面扩展** | 批量导入、体系整理、多管理员、对话向越界；**mcp-06** 扩展工具面 | 建立在 MVP-2 真索引与最小 MCP 之上 |

**仍延后（MVP-4）：** `agent-ingest-02`（URL）、`agent-source-01/02`、`agent-chat-01`。

---

## 3. MVP-2 — 知识闭环 + MCP 门面

### 3.1 范围（故事）

| ID | 名称 | 角色 |
| --- | --- | --- |
| **mcp-01…05** | MCP 门面（传输 `/mcp`、鉴权、最小工具、契约、Cursor 手测） | 见 `mcp-design.md`；先于批量/org |
| agent-ingest-01 | 粘贴 / 单文件提案 | 入口 |
| agent-km-01 | 内部 Qwen 仅 KM | 提案摘要/分类/查重辅助（真 DashScope chat） |
| agent-ingest-03 | 确认单条入库 | 持久化 + 触发索引 |
| rag-index-01 | 确认后分块索引 | 真 Embed + 写 Qdrant |
| rag-retrieve-01 | 混合检索与引用 | 真检索；命中带 citation（可先 dense，再补稀疏） |
| agent-list-01 | 知识列表 | 确认后可列 |
| agent-scope-03 | 拒绝无确认自动入库 | 边界 |
| agent-scope-04 | 拒绝伪造库内引用 | 边界 |

**本批最小 MCP / REST 工具集**

| 工具名 | 作用 |
| --- | --- |
| `kb_internal_search` | 库内检索（MVP-1 已有 REST；本批升级真命中） |
| `kb_propose_add` | 粘贴/正文 → Pending（KM ≤400 字内容概述） |
| `kb_confirm_add` | 确认 → 索引 |
| `kb_list_knowledge` | 可选；列表已确认条目（含 summary） |
| `kb_knowledge_summary` | 读/刷新单条内容概述 |

**硬约束：** MCP 只调领域层；`USE_FAKE_EMBEDDER=false`；不得 mock agent↔rag。MCP 传输/鉴权/工具注册见 [`specs/mcp-design.md`](./mcp-design.md)。  
**移出本批：** `agent-scope-01` / `02` → MVP-3；批量 import → MVP-3。

### 3.2 闭环旅程（验收剧本）

```text
签发 Key（MVP-1）
  →（可选）Cursor 添加 MCP：URL + Bearer Key
  → MCP/REST propose → proposed；Qdrant 无该条；list 无正式条目
  → MCP/REST confirm → Blob+PG confirmed；Qdrant 有 chunk（真 embed）
  → MCP/REST search → hits≥1 且含 knowledge_id/chunk_id/text
  → 跨 user Bearer 搜不到
  → 「全部自动入库」→ 拒绝（scope-03）
  → 空库/无关 query → enough=false，无捏造 citation（scope-04）
```

### 3.3 闭环验收套件（无 mock）

| 套件 | 要求 |
| --- | --- |
| 真栈 pytest / 旅程脚本 | Compose：Postgres + Qdrant + kb-agent + kb-rag；真 `QWEN_*`；禁止 patch `httpx` 伪装 RAG |
| MCP ↔ REST 对照 | 同 Key、同输入；propose/confirm/search 关键字段一致 |
| Cursor 手测（DoD 证据） | 手动添加 MCP 走通 propose→confirm→search；记录配置方式（HTTP URL + Bearer） |
| 回归 | 提案态不可索引；吊销 Key → 401 |

**DoD 出口：** 自动化真栈全绿 + Cursor/ChatBox 手测证据 + **用户确认可用（2026-08-11）**；本批故事 → `Done`。

---

## 4. MVP-3 — 操作面扩展

### 4.1 范围（故事）

| ID | 名称 | 角色 |
| --- | --- | --- |
| agent-import-01..03 | 批量导入 + 确认 + 格式限额 | 多文件闭环 |
| agent-org-01 | 体系整理 | 标签/项目等 |
| agent-scope-01 | 拒绝业务策略越界 | MCP/REST 同规则 |
| agent-scope-02 | 拒绝开放式决策 | 同上 |
| web-acct-03 | 忘记密码 / 重置 | 真 Resend |
| web-acct-04/05 | 邀请 + 接受设密 | 真邮件 |
| web-acct-07/08 | 管理员列表 / 删除 | 约束齐全 |

MCP：在 MVP-2 最小集上由 **`mcp-06`** 扩展 import/org 等工具，不重写门面（复用 `mcp-01`/`mcp-02`）。

### 4.2 闭环旅程

```text
A. 批量：上传 md/txt/pdf → 逐条或一键 confirm → search/list 可见
B. 管理：Resend 邀请/重置 → 设密 → 列表/删除约束
C. 越界：策略/开放决策经 MCP 与 REST 均拒绝（scope-01/02）
```

### 4.3 闭环验收套件（无 mock）

| 套件 | 要求 |
| --- | --- |
| 批量旅程 | 真文件 → 真 confirm → 真 Qdrant |
| Web E2E | Playwright + 真 Postgres + Resend test/sandbox |
| 越界 | 固定用例打真 Agent |

---

## 5. 依赖与顺序

```text
MVP-1 Done
    → MVP-2：领域闭环 + MCP 薄封装（Cursor 可手测）
        → MVP-3：批量 / 多管理员 / scope-01/02 / MCP 工具扩展
            → MVP-4：URL / 外部源 / Chat 门面
```

---

## 6. 明确不做（两批内）

- Fake Embedder / Fake KM 作为交付门禁  
- Mock `httpx` 伪装 RAG  
- Stub 外部搜索冒充 source（延后 MVP-4）  
- 无 confirm 的「导入即入库」  
- MCP 与 REST 双实现  

---

## 7. Backlog 批次变更摘要（相对更早切分）

| 故事 | 现批次 | 说明 |
| --- | --- | --- |
| mcp-01…05（取代 agent-mcp-01） | **MVP-2** | 传输/鉴权/最小工具/契约/Cursor 手测 |
| mcp-06 | **MVP-3** | 工具面扩展 import/org |
| agent-list-01 | MVP-2 | 确认后可观测 |
| agent-scope-01/02 | MVP-3 | 对话向越界 |
| agent-scope-03/04 | MVP-2 | 入库/引用诚实性 |
| MVP-4 四条 | MVP-4 | 不变 |
