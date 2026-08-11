# Test Strategy — kb.agent-mate.ai（kb-agent）

本文是本仓库的**项目测试策略**。它**扩展** Cursor 规则中的 `common-test-strategy`（公共基线），不得削弱该基线的金字塔、门禁或质量清单。冲突时取**更严**解释。

对齐：`specs/req.md`、`specs/architecture.md`、`specs/story-mapping.md`、`specs/rag-design.md`、`specs/agent-design.md`、`specs/mcp-design.md`、`specs/web-ui-design.md`、`specs/deployment-plan.md`、`specs/mvp-2-3-delivery.md`。

验收用例来源：`story-mapping.md` 中 Gherkin AC（ATDD）。实现前先写失败测试，再写生产代码（TDD / ATDD）。

---

## 1. 与 common-test-strategy 的关系

| 项 | 本项目 |
| --- | --- |
| 基线 | 完整遵守 `common-test-strategy`（金字塔、AAA、隔离、真实集成偏好、E2E 真浏览器、质量清单） |
| 扩展 | 下文：Web / Agent / RAG 分层工具、夹具、关键旅程、越界与租户门禁、CI 默认打桩规则 |
| 覆盖率 | 变更关键路径 **100%**；可测代码整体 **≥ 80%**（按服务分别报告：`kb-web`、`kb-agent`、`kb-rag`） |
| 禁止削弱 | 不得用「只有 mock 能绿」替代 confirm→检索、租户隔离、越界拒绝等关键行为 |

---

## 2. 测试目标

1. **知识正确性**：无 confirm 不索引；confirm 后可检索且可引用；提案态不可当已入库知识。  
2. **租户安全**：跨 `user_id` 不可见；请求体伪造身份无效；吊销 Key 立即 401。  
3. **职责边界**：越界请求稳定拒绝；不捏造库内引用；内部 Qwen 仅 KM。  
4. **管理面可用**：种子 `admin`/`admin`→强制改密；邀请设密不二次强制改密；管理员删除约束；Key 签发明文一次。  
5. **契约一致**：MCP 工具与 REST 同领域层语义（见 `mcp-design.md`；工件 `contracts/mcp-tools.json`）。  
6. **可部署**：健康检查与冒烟路径与 `deployment-plan.md` 对齐；MCP 公网路径 **`/mcp`**。

---

## 3. 金字塔与工具

目标比例（与基线一致）：**单元 ~70% · 集成/契约 ~20% · E2E ~10%**。

| 层 | Web（Admin） | Agent（MCP/REST/KM） | RAG（索引/检索） |
| --- | --- | --- | --- |
| 单元 | Vitest + Testing Library | pytest | pytest |
| 集成 | Vitest/Playwright API 或 BFF 对真实 Postgres（测试库） | pytest + 真实 Postgres + 真实 Qdrant（Compose 测试栈） | 同左；Indexer/Retriever 端到端 |
| 契约 | — | MCP schema ↔ REST 路径对照表自动化或快照 | Hit 结构 schema |
| E2E | Playwright 真浏览器（`file://` 仅静态稿冒烟；动态用 `make up` / `with_server`） | 经 REST/MCP HTTP 的旅程脚本（可与 Playwright 或 pytest+httpx 组合） | 由 Agent 旅程间接覆盖；另保留检索回归夹具 |

**不做：** 在 VPS 上跑破坏性测试；对生产库写入；CI 默认调用付费 DashScope / 真实 Tavily（另设 `online` 可选 job）。

---

## 4. 环境与数据

| 环境 | 用途 |
| --- | --- |
| 本地 `make up` | 开发 + 手工 / E2E；Postgres + Qdrant + 三服务 |
| CI fixture | Compose 或 service container：Postgres、Qdrant；应用 env 指向测试库名（如 `kb_agent_test`） |
| Online（可选） | 真实 DashScope embed/chat、Resend test mode、外部搜索；人工或 nightly |

**数据规则：**

- 每测隔离：事务回滚、schema truncate、或唯一 `user_id` / 前缀。  
- 向量：测试 collection（如 `kb_chunks_test`），跑完可删。  
- 原文 Blob：临时目录；禁止写生产卷。  
- 密钥：仅 CI secrets / `.env.test`（gitignore）；规格与仓库无真实 Key。  
- Fixture 允许本地 JSON **仅作测试种子**，不得作为产品持久化路径。

**第三方打桩（CI 默认廉价车道 — 不得单独作为 MVP 批交付门禁）：**

| 依赖 | CI fixture 车道 | MVP 闭环交付门禁（见 `specs/mvp-2-3-delivery.md`） |
| --- | --- | --- |
| DashScope chat / embed | 可暂用 Fake Embedder / Fake KM 保 PR 绿灯 | **MVP-2+ Done 禁止**：必须真 DashScope + 真 Qdrant；`USE_FAKE_EMBEDDER=false` |
| Resend | 可记录「发送意图」 | **MVP-3 Done 禁止**假 Outbox：须 Resend 官方 test/sandbox 真调用 |
| Tavily / Exa | Stub（能力属 MVP-4） | MVP-4 闭环再定；不得提前用 stub 宣称 source Done |
| 出站 fetch | 内嵌静态 HTML 服务器（非业务 stub） | SSRF / URL 批用本地真 HTTP 服务即可 |
| Agent→RAG | — | **禁止** mock `httpx` 伪装 RAG；一律真服务 HTTP |

---

## 5. 分层范围

### 5.1 单元（快、确定、无网络）

命名：`should_[expected]_when_[condition]`（或 pytest 等价清晰名）。AAA。

**RAG（`rag-*`）**

- Chunker：边界、overlap、过短块合并/丢弃  
- content_hash 幂等  
- RRF 融合与去重  
- Deduper：精确 hash + 近邻阈值（用假向量）  
-「无 confirm 不写 store」状态守卫（纯逻辑）

**Agent（`agent-*`）**

- 越界分类 → 稳定 `code`（策略 / 自动入库 / 伪造引用 / 开放式决策）  
- SSRF / URL 校验拒绝  
- API Key 哈希、一人一 active Key  
- 提案状态机：pending → confirmed；禁止 skip-confirm 参数  
- 工具结果截断（top-k、最大字符）  
- 身份：Bearer 解析；请求体 `user_id` 不可覆盖

**Web（`web-*`）**

- `must_change_password` 门禁（种子 vs 邀请/重置）  
- 删除管理员：禁删自己、禁删最后一名  
- i18n：关键文案走 key；默认 locale 解析  
- 表单 Zod 校验（签发姓名、邀请邮箱、改密）

### 5.2 集成 / 契约（真实 Postgres + Qdrant）

| 场景 | 故事锚点 | 断言要点 |
| --- | --- | --- |
| propose → confirm → search | agent-ingest-*, rag-index-01, rag-retrieve-01 | 确认前 search 无正式命中；确认后有引用字段 |
| 批量导入 → 逐条/一键 confirm | agent-import-* | 无静默全量索引；失败文件不阻塞同批可确认项 |
| 跨租户 | agent-auth-03, rag-isolate-01 | A 的 hit 永不含 B |
| 吊销 / 重签 Key | web-keys-03/04, agent-auth-01 | 旧 Key 401；新 Key 同库可读 |
| MCP ↔ REST | mcp-04, agent-rest-01 | 同输入同语义 `code` / hit shape；传输 `/mcp` Streamable HTTP + Bearer（`mcp-design.md`；`mcp-01`…`05`） |
| 越界 | agent-scope-* | 策略类请求拒绝；可附带候选但不给策略正文 |
| Admin 删管理员 | web-acct-08 | DB 约束与 API 一致 |

**契约工件：** [`contracts/mcp-tools.json`](../contracts/mcp-tools.json)（工具名 / 入参 / REST 映射）与 [`contracts/search-response.schema.json`](../contracts/search-response.schema.json)；对 OpenAPI/REST 路由表做生成或 diff，防止双门面漂移。细则见 [`mcp-design.md`](./mcp-design.md) §6、§10。

### 5.3 E2E（真浏览器 + 关键知识旅程）

工具：Playwright（Chromium）。动态应用：先起真实本地栈（`make up` 或 `with_server`），再跑脚本。选择器优先 `role` / 可见名 / `data-testid`；断言不绑单一语言硬编码（设 `zh-CN` 或测 test id）。

**Admin 旅程（对应 web-acct / web-keys）**

1. 空库登录 `admin`/`admin` → 强制改密页 → 改密成功 → 进入管理台  
2. 签发 Key → 明文一次可见 → 列表仅前缀  
3. 邀请管理员（Resend 打桩）→ 接受邀请设密 → 登录**无**二次强制改密  
4. 管理员列表 → 删除其他管理员成功；删自己 / 删最后一名失败  
5. 吊销 Key 后，用旧 Key 调知识 API 失败  

**知识旅程（Agent + RAG，可用 REST 驱动 + 可选 UI）**

1. Bearer Key：`kb_search` 空库 → 不足  
2. `kb_propose_ingest` → search 仍无正式命中 → `kb_confirm_ingest` → search 命中带引用  
3. `kb_import_documents`（md/txt）→ `kb_confirm_import_batch` → 可检索  
4. 越界：「给出投放策略」→ 稳定拒绝码  

**静态稿（可选）：** `specs/mockup/*.html` 用 `file://` 做视觉/导航冒烟（侧栏三项、`.btn-page` 尺寸、首页/登录偏上对齐、全站页脚），**不**替代动态 E2E。

**延迟：** 遵循架构「软提示 ~10s / 目标 ≤20s」；E2E 禁止用冲突的 10s 硬杀替代可观测等待；断言用就绪选择器，避免无意义 `sleep`。

---

## 6. 与故事地图的追溯

| 模块 | 优先自动化的功能编号 | 最低层 |
| --- | --- | --- |
| Web 账号 | web-acct-01…08 | 单元门禁 + E2E 旅程 1/3/4 |
| Web Key | web-keys-01…04 | 集成 + E2E 旅程 2/5 |
| Web i18n | web-i18n-01 | 单元 + 一页 E2E locale |
| Agent 鉴权/隔离 | agent-auth-* | 单元 + 集成 |
| Agent 检索/整理 | agent-search/list/org | 集成 |
| Agent 写入 | agent-ingest/import-* | 集成 + E2E 知识旅程 |
| Agent 补给/越界 | agent-source/scope-* | 单元越界 + 集成 stub 源 |
| Agent 门面 | agent-mcp/rest/chat/km | 契约 + 薄门面越界单测 |
| RAG | rag-index/retrieve/isolate/store | 单元算法 + 集成真 Qdrant |

新故事：先补 Gherkin AC → 再补本表追溯 → 再写失败测试。

---

## 7. CI 门禁

**每个 PR / push（默认）：**

1. Lint / typecheck（Web + Python）  
2. 单元测试（三包）  
3. 集成测试（Postgres + Qdrant fixture；外部 API 打桩）  
4. 契约检查（MCP ↔ REST）  
5. Playwright：至少 Admin 关键旅程子集（登录改密、签发 Key）；知识 confirm→search 可用 API 级 E2E 以控时  

失败即阻断合并。发布覆盖率报告（或等价摘要）。

**可选 / nightly `online`：**

- 真实 DashScope embed + 一小段 confirm→search  
- Resend test mode 邀请邮件  
- 不作为默认绿路径依赖  

**生产部署后冒烟：** 见 `deployment-plan.md` §9（不含破坏性删库）。

---

## 8. 质量清单（本项目适用项）

在 common-test-strategy 清单之上，合并前确认：

### 功能

- [ ] Admin：种子改密、邀请、删管理员约束、Key 签发/吊销/重签可用  
- [ ] 知识：propose→confirm→search；批量确认；越界拒绝  
- [ ] 失败/空态：无效登录、无效邀请链接、无命中、索引失败不假装成功  

### 自动化

- [ ] E2E 等待渲染态；稳定选择器  
- [ ] 关键旅程有自动化或附证据的手工脚本  

### 安全与数据

- [ ] 无跨租户泄漏用例失败即红  
- [ ] 密钥不进日志断言（或日志夹具扫描）  
- [ ] Admin 会话与 API Key 面分离  

### 性能（基线）

- [ ] 常见检索/管理操作无多秒假死；长操作有按组件提示（与架构性能节一致）  

### 回归

- [ ] CI fixture 套件绿  
- [ ] 覆盖率：关键路径 100%；总体 ≥ 80%（分服务）  

---

## 9. 反模式（本项目特有）

| 禁止 | 原因 |
| --- | --- |
| 用假检索结果冒充「库内有知识」且无索引写入 | 破坏方案 2 与可引用原则 |
| CI 默认打真 DashScope 且无配额控制 | 不稳定、费钱 |
| 仅测 MCP 或仅测 REST | 双门面易漂移 |
| E2E 只点 Admin、不测 confirm | 核心价值未验 |
| 削弱越界测试「以后再说」 | 产品边界即功能 |
| SQLite 当正式集成库 | 与 tech-stack 冲突；测试可用临时库但产品路径是 Postgres |

---

## 10. 本地命令约定（实现后绑定 Makefile）

目标形态（脚手架落地后填实）：

| 命令 | 含义 |
| --- | --- |
| `make test` | 单元 + 集成（fixture） |
| `make test-unit` | 仅单元 |
| `make test-e2e` | Playwright + 必要服务 |
| `make test-online` | 可选真 API（显式） |

开发期可用 `python …/webapp-testing/scripts/with_server.py` 拉起服务再跑 Playwright。

---

## 11. 文档维护

- 架构变更影响测试时，同步改本节与 `architecture.md` §16。  
- 新用户故事合并前：AC + 本策略追溯表至少有一层自动化或明确「仅手工」理由（不得用于鉴权/写入/越界）。  
- DoD：功能可用前须满足 common-test-strategy + 本文适用项；再跑 retrospective。
