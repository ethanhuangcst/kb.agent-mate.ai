# 架构设计 — kb-agent（私人 AI 知识库智能体）

本文档与 `specs/req.md` 对齐，采纳**方案 2**：调用方自带 LLM 做知识消费与业务推理；kb-agent 负责知识管理、受控外部补给与确认后入库。不含实施优先级与排期。

---

## 1. 目标与约束

### 1.1 产品定位

kb-agent 是公网可调用的**私人知识库智能体**：以 MCP 工具（及等价 REST）向 Cursor、ChatBox、HCP 等调用方暴露能力。调用方宿主中的大模型负责意图与业务；本服务负责管知识、找候选、确认后写入。

| 需求 | 架构含义 |
| --- | --- |
| Private、公网可调用 | 香港 VPS；公网域名 **`kb.agent-mate.ai`**；HTTPS |
| 多用户 | 管理员 Web 签发 Key；一人一把 Key ↔ 一份全局库；`user_id` 强制隔离 |
| 调用方自带 LLM | 主路径不托管「替业务做洞察」的全量 Agent 循环 |
| 内部用 Qwen | 仅用于归类、整理、提案摘要、可选查询改写 / 证据相关性辅助 |
| 检索已有知识 | RAG：混合检索，返回带引用的片段 |
| 按需获新知并确认入库 | 源路由补给 → 候选 → propose → confirm → 分块向量化 |
| 归纳知识体系 | `kb_list` / `kb_organize`（重大变更可走确认） |
| 本地存储 + 可扩展 | 原文 Blob 本地（可外置 S3）；元数据 PostgreSQL；向量 Qdrant；排除 Gist |
| 多调用方 | 同一领域层；MCP 与 REST 双门面；**共用使用者同一把 Key** |

### 1.2 调用方接入

| 调用方 | 接入 | 说明 |
| --- | --- | --- |
| Cursor | MCP（自定义 / 远程 MCP Server） | 宿主模型调工具；kb 不替代 Cursor 主模型 |
| ChatBox | 自定义 MCP | 同上；用户所选 ChatBox 模型做消费侧推理 |
| HCP Engagement Assistant | REST（及可选 MCP Client） | 应用侧已有 LLM；结构化 search / propose / confirm |

可选：OpenAI 兼容 `/v1/chat/completions`，仅作为调用同一工具集的薄 harness（例如调试），系统策略必须执行与 MCP 相同的越界拒绝规则，不得变成方案 1 全功能业务 Agent。

### 1.3 非目标

- 无调用方 LLM 时，由 kb-agent 包办业务洞察、策略、投放结论
- 静默爬取全网或未确认自动入库
- 在 VPS 上训练 / 微调模型
- 将 Perplexity 类「合成答案 API」的结果不经原文直接写入向量库
- 为每个调用方分叉独立业务逻辑（共用领域服务）

### 1.4 设计原则

1. **职责分离** — 调用方 LLM 消费与决策；kb-agent 仓储、补给、整理。
2. **写入需确认** — 外部与粘贴材料均 propose → confirm。
3. **回答以检索为据** — 声称来自知识库须带 chunk / item 引用。
4. **最优源 = 路由 + 证据优选** — 非单一搜索引擎锁定。
5. **一人一库一 Key** — 不按调用方拆密钥；所有知识实体带 `user_id` 并强制过滤。
6. **管理员与使用者分离** — Admin 会话只管 Key；知识面只认 Bearer API Key。
7. **模型即调用方侧 Agent** — kb 提供清晰工具；不在服务端堆业务工作流引擎。
8. **存储抽象** — `BlobStore` 默认本地；排除 Gist；可换 S3 兼容。

---

## 2. 多用户与鉴权

### 2.1 总览

```text
Admin Web (/admin)
  用户名或邮箱+密码会话 · 初始化 admin/admin（仅种子须改密）
  Resend 邀请/重置 · 签发/改/吊销使用者 API Key（填姓名；一人一把）
        │
        ▼
使用者持有一把 API Key
        │
        ├─ ChatBox MCP
        ├─ Cursor MCP
        └─ HCP / 其它 App REST
              │  Authorization: Bearer <api_key>
              ▼
        网关 → user_id → KbService（仅该用户数据）
```

### 2.2 使用者与 API Key

| 规则 | 说明 |
| --- | --- |
| 一人一把有效 Key | 一个 `User` 最多一把 `status=active` 的 Key |
| 签发输入 | **使用者姓名**（`display_name`） |
| 全局唯一库 | 该用户所有项目知识在同一库内；可用 `project`/`tag` 过滤，不按调用方分库 |
| 调用无关 | MCP 与 App 使用**同一把** Key |
| 明文 | 仅签发（或重签）时显示一次；库内只存 `key_hash` + 可展示的 `key_prefix` |
| 重签 | 吊销旧 Key + 签发新 Key，**同一 `user_id`**，知识不断；姓名在签发时确定，管理台不提供改姓名 |
| 吊销 | 立即 401；数据保留除非另做删除 |

请求中的 `user_id` / 姓名**不可信**，不得覆盖 Key 解析出的身份。

### 2.3 管理员 Web（R2 邀请制 + Resend）

| 能力 | 行为 |
| --- | --- |
| 初始化默认管理员 | 库中无 `AdminUser` 时自动种子账号：登录名 **`admin`**、密码 **`admin`**，并标记 `must_change_password=true`。**关闭**开放注册 |
| 种子账号强制改密 | **仅** `must_change_password=true`（种子默认口令）登录成功后须先改密；未改密不得访问 Key / 邀请等管理能力。**不适用于**邀请设密或忘记密码重置成功的账号（二者设密后即为 `false`，登录不再强制改密） |
| 邀请（R2） | 已登录且已完成改密的管理员输入邮箱 → Resend 发邀请链接 → 对方设**英文姓名**与密码（`must_change_password=false`）→ 成为管理员；顶栏 `Hello, {display_name}` |
| 开放注册 | **关闭** |
| 登录 | 用户名或邮箱 + 密码 → HttpOnly Secure Cookie 会话 |
| 重设密码 | 邮箱 → Resend 重置链接（短时、一次性）→ 设新密码（成功后 `must_change_password=false`）；可使旧会话失效 |
| 管理台 | **管理员**列表 / 邀请 / 删除（禁删自己、禁删最后一名）；**使用者**列表；签发 / 吊销 / 重签 Key（不提供改姓名） |

可选：`BOOTSTRAP_ADMIN_EMAIL` 仅用于给种子账号绑定联系邮箱（便于日后重置邮件）；**不**再作为创建首位管理员的唯一方式。未配置时种子账号仍可先用 `admin` / `admin` 登录并强制改密。

管理员账号表与使用者 API Key 表分离。管理员**不**用自己的登录会话直接调知识工具；若管理员也要当使用者，另签一把使用者 Key。

邮件：一律经 **Resend**（`RESEND_API_KEY`、已验证发件域）。登录 / 邀请 / 重置按 IP+邮箱限流。

同域部署：公网主机 **`kb.agent-mate.ai`** — `https://kb.agent-mate.ai/admin` 为管理面；`/api/v1/kb/*` 与 MCP 为知识面。

### 2.4 知识面鉴权

- Header：`Authorization: Bearer <api_key>`（`/healthz` 除外）
- 校验 hash → `user_id` → 注入领域层
- Qdrant payload 与 SQL **每条查询带 `user_id` 谓词**
- 默认无跨用户共享；配额（外部搜索等）按 `user_id` 或 Key 计

### 2.5 非目标（鉴权）

- 使用者自助注册 / OAuth 门户
- 按调用方（ChatBox/Cursor/HCP）拆多把 Key
- 用人轨 JWT 当 MCP 长期密钥
- GitHub Gist 或 GitHub 登录作为存储/鉴权前提

---

## 3. 职责边界与越界应对

### 3.1 能力边界

| 属于 kb-agent | 不属于 kb-agent |
| --- | --- |
| 库内 search / list / organize | 根据业务数据做投放策略、运营洞察、合规结论 |
| 外部源搜索候选、URL 拉取 | 开放式「研究完直接告诉我怎么做」的决策 |
| 入库提案、确认后持久化与向量化 | 未确认的自动入库 |
| 查重、分类标签建议（内部 Qwen） | 捏造库内不存在的「知识库结论」 |
| 返回候选与引用供调用方使用 | 接收调用方私有业务明细后直接产出策略方案 |

### 3.2 越界请求处理（规范行为）

当请求意图匹配「业务推理 / 策略生成 / 用调用方私有业务数据直接出方案」时：

1. **不调用**会把 kb 变成业务中台的隐式全量推理路径。
2. **工具 / API 返回**明确拒绝，使用稳定 `code`，例如：
   - `OUT_OF_SCOPE_BUSINESS_REASONING` — 要求业务洞察或策略
   - `OUT_OF_SCOPE_AUTO_INGEST` — 要求未确认批量入库
   - `INSUFFICIENT_KB_EVIDENCE` — 库内无据且调用方未授权外部补给
3. **可附带建设性降级**（仍不越界）：
   - 若可解析出「需要哪些公开知识」：可执行 `kb_search` 与/或外部候选检索，只返回**证据与来源**；
   - 文案须声明：业务策略 / 洞察须由调用方 LLM 结合其业务数据完成。

**坏例子（必须拒绝策略部分）：**

> 「根据我们 HCP 本周数据，上网查竞品并给出投放策略。」

**合规应对：**

- 拒绝「给出投放策略」及任何基于「本周 HCP 数据」的业务结论（kb-agent 也不应要求上传完整业务明细来「代算」）。
- 若调用方改述为「检索公开可用来源中与某某竞品能力相关的资料候选」：允许 `kb_source_search` / `kb_fetch`，返回候选列表。
- 投放策略由 HCP 应用侧 LLM 使用（业务数据 + 可选 kb 片段）自行生成。

MCP 工具描述与（若存在）薄 Chat 系统提示必须写入上述边界，减少模型越权调用。

---

## 4. 系统上下文

```text
┌──────────────────────────┐     ┌─────────────────────┐
│ Cursor / ChatBox / HCP   │     │ 管理员浏览器         │
│ 自带 LLM · 同一把 API Key│     │ Admin Web 会话       │
└────────────┬─────────────┘     └──────────┬──────────┘
             │ Bearer Key                   │ Cookie
             │ MCP / REST                   │ /admin
             ▼                              ▼
┌─────────────────────────────────────────────┐
│ 香港 VPS · kb.agent-mate.ai · 反代 (TLS)    │
│ kb-agent：领域服务 · 源路由 · RAG · Admin   │
│ PostgreSQL · Qdrant · 原文 LocalFs          │
└───────┬─────────────────────┬───────────────┘
        │                     │
        ▼                     ▼
  DashScope Qwen         Resend（邀请/重置邮）
  外部知识源适配器
```

**信任边界：** 公网仅暴露反代。Qdrant 与元数据库不公网。外部网页正文视为不可信数据。API Key 明文与管理员密码哈希策略见 §2 / §14。密钥与 `RESEND_API_KEY` 仅存 VPS 环境。

---

## 5. 逻辑架构

```text
        MCP Server                    REST /api/v1/kb/*
              \                         /
               \                       /
                ▼                     ▼
              ┌─────────────────────────┐
              │ 领域服务 KbService      │
              │ search · list · organize│
              │ propose · confirm       │
              │ source_search · fetch   │
              └───────────┬─────────────┘
                          │
           ┌──────────────┼──────────────┐
           ▼              ▼              ▼
    ┌────────────┐ ┌────────────┐ ┌──────────────┐
    │ RAG 核心   │ │ 源路由与   │ │ 内部 Qwen    │
    │ 分块向量   │ │ 外部适配器 │ │ 提案/整理    │
    └─────┬──────┘ └─────┬──────┘ └──────────────┘
          │              │
          ▼              ▼
   向量库/元数据    搜索 API / HTTP fetch
   原文 Storage
```

| 层级 | 职责 |
| --- | --- |
| MCP / REST | 协议适配；鉴权；参数校验；越界码透出 |
| KbService | 用例编排；确认态；边界策略 |
| RAG | 库内混合检索；确认后索引 |
| Source Router | 选通道、预算、候选融合打分 |
| LlmKmAdapter | 仅内部知识管理用 Qwen |
| Storage | 原文、元数据、向量；可替换实现 |

---

## 6. 工具与 API（领域能力）

能力以工具名表达；REST 提供等价资源。

| 能力 | 作用 | 改库 |
| --- | --- | --- |
| `kb_search` | 库内语义 + 关键词检索，返回引用片段 | 否 |
| `kb_list` | 按 project / tag / 类型浏览 | 否 |
| `kb_organize` | 体系归纳、标签/分类调整；破坏性变更可确认后写 | 视参数 |
| `kb_source_search` | 经源路由的外部搜索，返回候选（不入库） | 否 |
| `kb_fetch` | 按 URL 拉取正文（限额、超时、大小帽） | 否 |
| `kb_propose_ingest` | 对粘贴 / fetch 正文生成提案（元数据 + 查重） | 仅 Pending |
| `kb_confirm_ingest` | 确认单个 pending 后持久化并索引 | **是** |
| `kb_import_documents` | 批量上传文档 → 解析 → 每文件一条 Pending，挂到 ImportBatch | 仅 Pending |
| `kb_confirm_import_batch` | 对批次内指定 pending 或全部可确认项执行确认入库 | **是** |

可选调试门面可暴露同一集合，不得新增「业务策略」类工具。批量导入不得提供「跳过确认直接索引」参数。

---

## 7. 获取新知识 — 技术方案

### 7.1 目标与效用

在成本与安全约束下，为「补给入库」最大化可引用、相关、低重复的候选；**不**优化「一句话业务结论」。

效用代理：相关性 × 可引用性（可拉取正文）× 域信任 − 成本 − 与库内重复。

### 7.2 总流程

```text
意图（由调用方 LLM 给出 query / 约束 / 可选 URL）
        │
        ▼
  kb_search（库内）── 已足够？──是──► 返回库内命中（可不再外部）
        │否（或调用方显式要求外部）
        ▼
  Source Router
        │
        ├ user_url      → kb_fetch
        ├ domain_docs   → 白名单域 / 文档站
        ├ web_general   → 通用 Web 检索适配器（如 Tavily）
        └ semantic_disc → 语义发现适配器（如 Exa，可选）
        │
        ▼
  级联或小并行（每源 top_k、总字符/条数预算）
        │
        ▼
  Evidence rank（检索分 · 域权威 · 时效 · 库内查重）
        │
        ▼
  返回候选列表（不落库）
        │
        ▼ 调用方选用正文 / URL
  kb_propose_ingest → PendingIngest
        │
        ▼ 调用方确认
  kb_confirm_ingest → Storage + Chunk + Embed + Qdrant
```

### 7.3 Source Registry（源注册表）

可配置的源通道，而非硬编码单一引擎：

| 字段（概念） | 含义 |
| --- | --- |
| `source_id` | 如 `web_tavily`、`web_exa`、`docs_whitelist`、`url_fetch` |
| `type` | `web_general` / `semantic_disc` / `domain_docs` / `user_url` |
| `adapter` | 适配器实现与凭证引用 |
| `enabled` | 开关 |
| `default_quota` | 默认 top_k / 超时 |
| `trust_weight` | 域权威加权 |
| `allow_domains` / `deny_domains` | 可选过滤 |
| `project_affinity` | 可选：某 project 的偏好源 |

路由输入：query、可选 `project`、调用方声明的约束（只要官方文档 / 允许 Web 等）、库内命中质量信号。

路由输出：有序的通道列表 + 每通道预算（可对「偏好源」提高配额，类似简化的 preference-conditioned cap；其余源保留较小配额，避免单点押宝）。

### 7.4 选择策略（规范）

1. **库内优先**：先 `kb_search`；仅当命中不足（条数、分数阈值）或调用方显式要求外部时，启用外部通道。
2. **用户给定 URL 最高优先**：直接 `kb_fetch`，不强制先搜索。
3. **禁止预测唯一源且无回退**：至少保留「偏好通道 + 一个回退通道」或小并行，再在证据层截断。
4. **融合**：多通道结果合并后排序（检索分、RRF 或简单加权）；截断到上下文 / 响应预算。
5. **适配器分工**：通用事实与 Agent 友好结构化结果偏 Web 检索层；概念/相似文档发现可用语义发现层；**合成答案型 API 不作为入库主通道**。
6. **正文入库**：候选被选中后须有可抽取正文（fetch 或调用方粘贴），再 propose；禁止只存无法溯源的模型复述。

### 7.5 提案与确认

```text
材料（粘贴 | fetch 正文 | 批量导入中的单文件正文）
  → 规范化 + content_hash
  → 近邻查重（向量）+ 精确哈希
  → 内部 Qwen：title / summary / tags / project? / knowledge_type
  → PendingIngest（TTL，绑定 api_key_id / user_id；可选 batch_id）
  → 调用方确认（单条或批次）
  → 原文写入 Storage → 元数据 → 分块 → embedding → Qdrant upsert
```

规则：

- 无确认不得建正式 `KnowledgeItem` / 向量。
- 同哈希：提案标注已存在；确认时可 no-op 或仅合并元数据。
- 外部 HTML 等视为不可信；截断；不当系统指令执行。
- 批次一键确认 = 对批内多条 pending 依次执行与单条 confirm 相同的持久化逻辑，**不是**绕过确认态。

### 7.5.1 批量文档导入

```text
multipart 多文件（+ 可选默认 project/tags）
        │
        ▼
  校验：个数、单文件大小、批次总大小、MIME/扩展名白名单
        │
        ▼
  创建 ImportBatch（user_id）
        │
        ▼  每文件（可并行，受并发帽限制）
  抽取正文（md/txt 直读；PDF 文本层抽取）
        │ 失败 → BatchItem status=failed（原因码），继续其他文件
        ▼ 成功
  走与 7.5 相同的 propose 管道 → PendingIngest(batch_id)
        │
        ▼
  返回 batch_id + 各文件提案摘要 / 失败列表（仍不落正式库）
        │
        ▼ 调用方
  逐条 kb_confirm_ingest(pending_id)
  或 kb_confirm_import_batch(batch_id, pending_ids? | confirm_all_viable=true)
```

| 约束 | 规范 |
| --- | --- |
| 格式基线 | `.md`、`.txt`、可文本抽取的 `.pdf` |
| 限额 | 配置项：`max_files_per_batch`、`max_bytes_per_file`、`max_bytes_per_batch` |
| 解析失败 | 单文件失败不回滚整批已成功提案 |
| 查重 | 与单条 propose 相同；批内文件之间亦应去重（相同 hash 标重复） |
| 禁止 | 无确认自动索引；「上传即知识」开关 |

扫描/二进制 PDF 无文本层时：标记失败或 `needs_ocr`（OCR 非基线必做；未实现则失败并说明）。

### 7.6 安全与配额（获新知相关）

- 按 API Key（及 `user_id`）限制：外部搜索次数、fetch 次数、正文最大字节、并发、**批量导入次数与批次体积**。
- SSRF：禁止内网 / 元数据地址；仅 http(s)；DNS / IP 校验。
- 域黑名单与可选白名单模式（`domain_docs`）。
- 上传文件：扩展名/MIME 白名单；不执行文件内脚本；PDF/文本解析在沙箱或受限进程中为宜。
- 日志记录 `source_id`、`batch_id`、耗时、候选/文件数；默认不记全文。

---

## 8. RAG 核心（库内）

### 8.1 确认后入库路径

```text
已确认正文 → Storage 原文 → 元数据 → RecursiveCharacter 分块
  → Qwen embedding → Qdrant upsert（payload: knowledge_id, user_id, tags, project, type）
```

### 8.2 查询路径

```text
问题 → 可选轻量改写 → 稠密 + 稀疏 → RRF → 可选重排 → top-k 去重 → 返回引用
```

生成「自然语言业务答案」由**调用方 LLM**完成；kb 侧 REST/MCP 默认返回结构化命中。若薄 Chat 门面拼回答，须 grounded 且不得越界做策略。

### 8.3 内部 Qwen 角色

| 用途 | 允许 |
| --- | --- |
| 提案分类 / 摘要 / organize 建议 | 是 |
| 证据相关性辅助打分（可选） | 是 |
| 调用方业务洞察 / 投放策略 | **否** |
| 向量 | DashScope Qwen embedding（模型 ID 与维度配置化） |

---

## 9. 存储

### 9.1 当前部署形态（香港 VPS）

```text
/data/kb/
  raw/           # 原文（经 Storage 接口访问）
  exports/
  qdrant/
# PostgreSQL 由 Compose 服务提供（非 sqlite 文件）
```

| 存储 | 现实现 | 内容 |
| --- | --- | --- |
| 元数据 | PostgreSQL | 条目、版本、标签、Pending、User、ApiKey、AdminUser、邀请/重置 token、Source 配置 |
| 向量 | Qdrant 单节点 | chunk 向量 + 可过滤 payload（含 `user_id`） |
| 原文 | 本地文件系统 | 经 `BlobStore` 抽象 |

### 9.2 扩展与多用户存储约定

- **`BlobStore` 接口**：`put` / `get` / `delete`；现实现与默认路径为 **LocalFs（VPS 本地）**。**不采用 GitHub Gist** 作为原文或知识主存储。若因磁盘压力需外置，可增加 S3 兼容对象存储实现；业务不绑具体路径字符串。
- **多用户**：所有知识实体带 `user_id`；API Key 一对一绑定 User；检索与 confirm 强制 `user_id` 过滤；禁止跨用户默认共享。应用元数据以 **PostgreSQL** 为准（见 **tech-stack**）；禁止 SQLite/JSON 作为正式库。
- 向量 payload 与 SQL 查询一律带 `user_id` 谓词。

---

## 10. 数据模型（概念）

```text
AdminUser
  id, username?, email?, display_name?   # 邀请设密时填英文姓名；种子可用 Admin
  password_hash
  must_change_password   # 种子默认 admin 为 true；邀请/重置设密与主动改密成功后 false
  email_verified_at?, created_at

AdminInvite / PasswordResetToken
  token_hash, email 或 admin_user_id, expires_at, used_at?

User（使用者 — 知识库主人）
  id, display_name, status(active|disabled), created_at

ApiKey
  id, user_id          # 一人最多一把 active
  key_hash, key_prefix
  status(active|revoked), created_at, revoked_at?

KnowledgeItem
  id, user_id, content_hash, title, summary, body_uri, knowledge_type
  project?, language, created_at, updated_at, deleted_at?

Tag / KnowledgeTag
KnowledgeVersion

Chunk
  chunk_id, knowledge_id, version_id, ordinal, text  （向量在 Qdrant，payload 含 user_id）

PendingIngest
  pending_id, user_id, api_key_id, batch_id?, status
  proposed_metadata, body_ref, source_trace, dedupe_hits
  source_filename?, expires_at, confirmed_at?

ImportBatch
  batch_id, user_id, status(open|completed|expired|cancelled)
  default_project?, default_tags?, created_at, finished_at?
  # 关联多条 PendingIngest；另可记每文件失败原因

SourceChannel / SourceConfig
  注册表项（见 7.3）
```

`source_trace`：记录本次候选来自哪些 `source_id`，便于审计与偏好统计。

---

## 11. API 表面

### 11.1 知识 REST / MCP

与 MCP 工具一一对应即可。

| 方法 | 路径 | 用途 |
| --- | --- | --- |
| `POST` | `/api/v1/kb/search` | 库内检索 |
| `GET` | `/api/v1/kb/items` | 列表过滤 |
| `GET` | `/api/v1/kb/items/{id}` | 详情 |
| `POST` | `/api/v1/kb/sources/search` | 外部候选检索 |
| `POST` | `/api/v1/kb/fetch` | URL 拉取 |
| `POST` | `/api/v1/kb/proposals` | 创建单条提案 |
| `POST` | `/api/v1/kb/proposals/{id}/confirm` | 确认单条入库 |
| `POST` | `/api/v1/kb/imports` | 批量上传文档（multipart）→ 创建 ImportBatch + 多条提案 |
| `GET` | `/api/v1/kb/imports/{batch_id}` | 批次状态与提案/失败列表 |
| `POST` | `/api/v1/kb/imports/{batch_id}/confirm` | 确认批内选中或全部可确认提案 |
| `POST` | `/api/v1/kb/organize` | 体系整理 |
| `PATCH`/`DELETE` | `/api/v1/kb/items/{id}` | 更新 / 软删+删向量 |
| `GET` | `/healthz` | 存活 |

鉴权：`Authorization: Bearer <api_key>`（`/healthz` 除外）。越界与校验失败返回稳定 `code`。

MCP：使用 Streamable HTTP 或 ChatBox / Cursor 所支持的远程 MCP 传输；工具 schema 与上表语义一致；**配置同一把使用者 Key**。

### 11.2 管理员 Web / Admin API（会话）

| 能力 | 说明 |
| --- | --- |
| 登录 / 登出 | 用户名或邮箱 + 密码；Cookie 会话 |
| 接受邀请 / 设密 | 邀请链接落地 |
| 忘记密码 / 重置 | Resend 链接 |
| 种子强制改密 | `must_change_password` 为真时仅开放改密相关接口 |
| 邀请管理员 | 仅已登录且已改密管理员；Resend |
| 管理员列表 | 用户名/邮箱、状态、创建时间；不含密钥 |
| 删除管理员 | 可删其他管理员；**禁止**删自己；**禁止**使有效管理员数为 0；删除后其会话立即失效 |
| CRUD 使用者 Key | 签发（填姓名）、吊销、重签（不改姓名） |

Admin API 仅接受管理员会话，不接受使用者 API Key 做邀请、签发或删管理员。`must_change_password=true` 时拒绝 Key 管理、邀请与管理员删除类写操作。

---

## tech-stack

密钥清单模板见 [`specs/keys.md`](./keys.md)；本地填写 `specs/keys.local.md` 或根目录 `.env.local`（均已 gitignore）——切勿将真实密钥提交到公共仓库。产品行为写在 `specs/req.md` 与本架构其他章节，不在本节重复业务规则。面向**中国大陆**与**香港**；优先选用在这些地区可用的服务。

### 技术栈

| 类别 | 技术 | 版本 |
| --- | --- | --- |
| Admin Web | Next.js（App Router） | 16.2.x |
| UI / 语言 | React · TypeScript；i18n locales `zh-CN`（默认）/ `en`（可扩展 `ja`）；管理面用户可见文案走 i18n | 19.2.x · 5.9.x |
| 样式 | Tailwind CSS；视觉对齐 [`web-ui-design.md`](./web-ui-design.md) 与 `specs/mockup/`（性冷淡；公网/auth 偏上居中同壳；全站页脚；主按钮固定 `--control-h`） | 4.x |
| 状态 / 表单 | React Query · Zustand · RHF + Zod + `@hookform/resolvers`（管理面表单） | 按锁文件钉死 |
| Agent / API / MCP | Python 3.12 · FastAPI · MCP Python SDK | — |
| RAG 服务 | Python 3.12 · FastAPI；Qdrant（向量） | — |
| 应用存储 | PostgreSQL（用户、管理员、API Key、知识元数据、提案、批次等） | 17+ |
| ORM / 客户端 | 优先 `SQLAlchemy` / `psycopg`（或 Drizzle 仅若 Admin BFF 需独立访问）；避免第二套 ORM | — |
| AI | `openai` SDK → 通义千问 DashScope compatible-mode（内部 KM 对话 / 结构化 JSON）；Embedding 走 DashScope 文本向量模型 | openai 6.x |
| 邮件 | Resend（管理员邀请 / 重置密码） | — |
| 网关 / 编排 | 生产：野草云3 · NPM · Portainer（见 release-bot）；本地：Docker Compose + Makefile `dev` / `up` / `down` | — |
| 测试 | Vitest · RTL · Playwright（Admin Web）；pytest（Agent / RAG） | 按锁文件钉死 |

规则：尽量少依赖；优先平台与标准库；**应用持久化使用 PostgreSQL**——禁止把用户/业务数据写入本地 JSON（`data/`）或 **SQLite** 作为正式存储（测试 fixtures / 临时种子除外）。向量检索使用 **Qdrant**（非业务关系库）。只接入产品实际需要的第三方能力——不要默认把未列出的服务都接上。

### 部署拓扑（三独立服务）

产品运行时为 **三个可独立部署的服务**（外加 Postgres 与 Qdrant）：

| 服务 | 栈建议 | 持有密钥（示例） |
| --- | --- | --- |
| **kb-web** | Next.js（Admin UI + 可选 BFF） | 管理员会话密钥、`DATABASE_URL`（或经 BFF）、Resend、`AGENT_BASE_URL` + 服务凭证、`RAG_BASE_URL` + 服务凭证 |
| **kb-agent** | FastAPI：MCP + 知识 REST + 越界策略；调用 RAG / 外部源 | DashScope chat（KM）、Resend 不必须；`RAG_BASE_URL` + 凭证；外部搜索适配器密钥；**无** 浏览器会话 |
| **kb-rag** | FastAPI：分块 / 向量 / 混合检索 / 确认后索引 | Embedding、`DATABASE_URL`（元数据）、`QDRANT_URL`；**无** 用户会话、**无** DashScope chat（除非改写放本服务） |

浏览器只访问 **kb-web**（及经反代的公开 MCP/API，生产域名为 `kb.agent-mate.ai`）。Agent / RAG / Qdrant / Postgres 端口不对公网。本地 `make up` 应拉起三者（+ Postgres + Qdrant + 可选本地反代）。

### 最小依赖策略

- 尽量少用依赖——优先平台能力、标准库与现有技术栈，再考虑新增包。
- 保持架构干净：不为「以防万一」引入可选库。
- **存储：PostgreSQL 为应用数据唯一正式持久化**。禁止使用本地 JSON 文件、MongoDB、服务端 SQLite 等作为应用数据存储（fixtures / 测试种子除外）。向量状态以 Qdrant 为准。

### 国家 / 地区限制

可用性可能变化；在该地区构建或运行时，优先使用替代方案。

#### 中国大陆

| 不可用 / 不稳定 | 替代方案 |
| --- | --- |
| **OpenAI（ChatGPT API）**（`api.openai.com`） | **DashScope（通义千问）** — OpenAI 兼容 |
| **npmjs.org** 注册源（慢或被拦） | **npmmirror** — `https://registry.npmmirror.com` |

#### 香港

| 不可用 / 不稳定 | 替代方案 |
| --- | --- |
| **OpenAI（ChatGPT API）**（`api.openai.com`） | **DashScope（通义千问）** — OpenAI 兼容 |
| **npmjs.org** 注册源（往往较慢） | **npmmirror** — `https://registry.npmmirror.com` |

说明：

- 本项目部署目标含香港 VPS；默认 LLM / Embedding 优先使用 Qwen DashScope。
- 不接入地图、TCG 目录等与本产品无关的第三方。

### npm 安装

Admin Web（Next.js）在**中国大陆**与**香港**，请通过阿里云 npmmirror 安装包：

```bash
npm config set registry https://registry.npmmirror.com
# 或单次：
npm install --registry=https://registry.npmmirror.com
```

其他地区可用默认 npm 注册源。Python 依赖使用官方 PyPI 或国内镜像（按环境自选），与 npm 注册源相互独立。

### 第三方能力与 API

#### DashScope（通义千问）对话能力：`QWEN_CHAT_MODEL`

- API 配置
  - Model-name=`QWEN_CHAT_MODEL`（按项目可降级 `QWEN_CHAT_MODEL_FALLBACK`）
  - Host=`QWEN_HOST`
  - API-Key=`QWEN_API_KEY`
  - Base_URL=`QWEN_BASE_URL`
  - Workspace=`QWEN_WORKSPACE` · Region=`QWEN_REGION`
- 技术要点
  - 端点：经 `openai` SDK 调用 OpenAI 兼容 `/chat/completions`
  - 参数：在 OpenAI 兼容面使用 `max_completion_tokens`（**不要**用 `max_tokens`）
  - 用途：**仅**智能体内部知识管理（分类、摘要、organize 建议、可选 query 改写）；不承担调用方业务洞察
  - **中国大陆 / 香港优先选用**
  - 失败时：向调用方返回错误，供组件展示错误并重试——禁止静默空成功
  - 产品行为：见 `specs/req.md`、`specs/agent-design.md`

#### DashScope（通义千问）向量：`QWEN_EMBED_MODEL`

- API 配置
  - Model-name=`QWEN_EMBED_MODEL`
  - 维度=`EMBED_DIM`（与模型固定绑定，写入配置）
  - 共用 `QWEN_API_KEY` / `QWEN_BASE_URL` / `QWEN_WORKSPACE`（或文档要求的 embedding 端点）
- 技术要点
  - 用途：知识分块向量化、检索 query 向量、propose 近邻查重
  - 换模型须全量重嵌；记录所用 `embedding_model_id`
  - 失败时：confirm / 索引返回错误——禁止假装已写入向量
  - 产品行为：见 `specs/rag-design.md`

#### Resend 能力：事务性邮件

- API 配置
  - Service=`Resend`（或 SMTP）
  - Host=`RESEND_HOST`（或 `SMTP_URL`）
  - API-Key=`RESEND_API_KEY`（或 SMTP 用 `SMTP_URL`）
  - Base_URL=`RESEND_BASE_URL`
- 技术要点
  - 事务性邮件（管理员邀请、密码重置）
  - 密钥管理：`RESEND_KEY_MGMT_SITE` · `import { Resend } from 'resend'`（kb-web）或等价 HTTP 调用（若由 agent 代发）
  - 失败时：向调用方返回错误——未获提供商确认前不得声称发送成功
  - 产品行为：见 `specs/req.md`（R2 邀请制）

#### PostgreSQL 能力：应用持久化

- API 配置
  - Service=`PostgreSQL`
  - Host=`DATABASE_HOST`
  - Port=`DATABASE_PORT`（默认 `5432`）
  - User=`DATABASE_USER`
  - Password=`DATABASE_PASSWORD`
  - Database=`DATABASE_NAME`
  - URL=`DATABASE_URL`（`postgresql://USER:PASSWORD@HOST:PORT/NAME`，优先使用此连接串）
- 技术要点
  - 用途：AdminUser、邀请/重置令牌、User、ApiKey、KnowledgeItem 元数据、PendingIngest、ImportBatch、Source 配置等
  - **禁止**将上述数据写入本地 JSON（`data/`）或 SQLite 作为正式存储
  - 连接仅在服务端使用——禁止 `NEXT_PUBLIC_*` 暴露数据库凭证
  - 失败时：向调用方返回错误——禁止静默空成功或假装已写入
  - 产品行为：见本架构数据模型章节

#### Qdrant 能力：向量检索

- API 配置
  - Service=`Qdrant`
  - URL=`QDRANT_URL`
  - Collection=`QDRANT_COLLECTION`（如 `kb_chunks`）
- 技术要点
  - 用途：chunk 向量存储与稠密检索；payload 强制含 `user_id`
  - 不对公网暴露；仅 kb-rag（及受信内网）访问
  - 失败时：向调用方返回错误——禁止静默空命中冒充成功
  - 产品行为：见 `specs/rag-design.md`

### 环境变量

将密钥复制到 `.env.local` 或 `specs/keys.local.md`（已 gitignore；勿提交）。不要在源码中硬编码。规格与 [`keys.md`](./keys.md) 仅列出**环境变量名**——本地自行填值。

```env
# QWEN DashScope（通义千问）
QWEN_API_KEY=
QWEN_HOST=
QWEN_BASE_URL=
QWEN_WORKSPACE=
QWEN_REGION=
QWEN_CHAT_MODEL=
QWEN_CHAT_MODEL_FALLBACK=
QWEN_EMBED_MODEL=
EMBED_DIM=
QWEN_KEY_MGMT_SITE=

# 邮件 / Resend
RESEND_API_KEY=
RESEND_HOST=
RESEND_BASE_URL=
RESEND_KEY_MGMT_SITE=
SMTP_URL=

# PostgreSQL
DATABASE_URL=
DATABASE_HOST=
DATABASE_PORT=
DATABASE_USER=
DATABASE_PASSWORD=
DATABASE_NAME=

# Qdrant
QDRANT_URL=
QDRANT_COLLECTION=

# 服务发现 / 引导
AGENT_BASE_URL=
RAG_BASE_URL=
PUBLIC_BASE_URL=https://kb.agent-mate.ai
BOOTSTRAP_ADMIN_EMAIL=   # 可选：绑定种子管理员联系邮箱；首位账号固定为 admin/admin + 仅种子强制改密
API_KEY_PEPPER=
SESSION_SECRET=
```

### 性能

**延迟（所有组件——仅此一套约定）：**

- 软提示：约 **10s** 后展示「还需要更多时间」，同时继续等待（禁止使用「Timeout」字样）
- 目标：每个组件在 **≤20s** 内就绪
- **不要**另做一套冲突的 10s 硬超时，在无用户可见状态时提前放弃组件

**加载策略（所有组件）：**

- 独立组件之间**并行**请求
- 各块完成后即**流式 / 渲染**——不要因最慢的一块卡住整页
- 等待期间展示**按组件**的提示与进度
- **大列表分段加载**：知识条目列表、导入批次、管理员使用者列表等按页或游标分段——禁止一次性加载全量；首屏尽快可交互

**降级：**

- 仅在上游失败，或用户可见等待路径结束后组件仍为空时，使用**本地降级**（测试夹具等）
- **不要**在约 10s 时静默切到降级，而 UI 仍暗示正在实时生成

### 实现陷阱（必须遵守）

实现时对照 `specs/req.md` 与本架构核对：

| 领域 | 约定 |
| --- | --- |
| **地区 / LLM** | 中国大陆 / 香港 OpenAI 不可用或不稳定——使用 DashScope；不要假设全球统一 LLM 主机 |
| **对话** | OpenAI 兼容对话面使用 `max_completion_tokens`——**不要**用 `max_tokens` |
| **职责** | Qwen 仅 KM——禁止用服务端 LLM 做调用方业务洞察 / 投放策略 |
| **写入** | 知识必须 propose → confirm；禁止无确认自动索引 |
| **延迟** | 软提示约 10s · 就绪目标 ≤20s——**仅此一套约定**（见「性能」） |
| **存储** | PostgreSQL 为应用正式持久化——禁止本地 JSON / SQLite 作为业务数据源；向量用 Qdrant；凭证仅服务端环境变量 |
| **列表加载** | 大列表分段加载（页/游标）——禁止一次性拉全量 |
| **密钥** | 仅通过 `.env.local` 环境变量——切勿在规格或仓库中提交真实密钥 |

---

## 13. 部署与配置

**公网域名（已定）：** `kb.agent-mate.ai`  
`PUBLIC_BASE_URL=https://kb.agent-mate.ai`（邀请链接、重置密码、客户端配置基址均以此为准）。生产边缘按野草云3 / release-bot：DNS → Nginx Proxy Manager → Docker；本地开发可用 Caddy 或 Compose 直连。

```text
https://kb.agent-mate.ai (:443)
  → 反代（生产 NPM / 本地 Caddy）
       → kb-web（Admin，如 /admin）
       → kb-agent（MCP / 知识 REST，可同域路径）
       →（内网）kb-rag · qdrant · postgres
```

配置项详见 **tech-stack** 环境变量；另含 Pending TTL、源适配器配额等。首位管理员：初始化 **`admin` / `admin`** + 仅种子强制改密（`BOOTSTRAP_ADMIN_EMAIL` 可选）。详见 `specs/release-bot-instruction.md`。

备份：PostgreSQL + Qdrant 卷 + 原文 BlobStore 一致快照。恢复：停写 → 还原 → 启动。

---

## 14. 安全

| 控制 | 实现 |
| --- | --- |
| 传输 | HTTPS |
| 使用者鉴权 | API Key 哈希；一人一把；强制 `user_id` 隔离 |
| 管理员鉴权 | 用户名/邮箱+密码会话；种子 admin/admin + 仅种子强制改密；邀请/重置设密不强制改密；Resend 短时一次性链接 |
| 写入知识 | 仅 confirm |
| 越界 | 稳定拒绝码 + 工具描述约束 |
| SSRF / 出站 | fetch 校验；预算 |
| 提示注入 | 外部正文当数据 |
| 隔离 | DB/Qdrant 不暴露公网 |
| 密钥与邮件 | 环境变量；Key 明文不入日志；Resend 仅发事务邮 |

---

## 15. 可观测性

- 结构化日志：路由决策、`source_id`、检索命中、提案/确认、越界拒绝码、延迟、`user_id` / `key_prefix`（非明文 Key）
- 管理员操作审计：签发 / 吊销 / 邀请 / **删除管理员**（谁、对谁、何时）
- `/healthz`：应用、Qdrant、存储可写
- 指标（可选）：工具调用量、外部检索次数、确认转化、按源入库率

---

## 16. 质量与测试（扩展 common-test-strategy）

完整策略见 **[`specs/test-strategy.md`](./test-strategy.md)**（扩展公共基线，不削弱）。摘要：

| 层级 | 重点 |
| --- | --- |
| 单元 | 分块、哈希幂等、RRF、路由预算、越界码、SSRF 拒绝、提案状态机、Key 哈希与一人一 Key 约束；Admin 改密/删管理员门禁 |
| 集成 | 真实 Qdrant+PostgreSQL：search、propose→confirm→再 search；批量导入→提案→confirm batch；跨 `user_id` 不可见；Admin 签发/吊销；管理员列表与删除约束 |
| 契约 | MCP 工具 schema 与 REST 对齐；越界示例必须拒绝策略部分；禁止无确认自动索引 |
| E2E | Playwright Admin 旅程；知识 confirm→search；外部搜索 CI 打桩；可选 online 套件 |

关键路径不得仅靠假检索冒充有知识；CI 使用本地 Qdrant。外部搜索与 DashScope 在 CI 默认打桩，另设可选在线套件。

---

## 17. 关键决策

| 决策 | 选择 | 原因 |
| --- | --- | --- |
| LLM 边界 | 方案 2：调用方消费，kb 做 KM + 补给 | 与 Cursor/ChatBox/HCP 形态一致；避免业务中台化 |
| 主接入 | MCP + REST 共领域层 | ChatBox 支持自定义 MCP；HCP 要结构化 API |
| 获新知 | 注册表 + 库内优先 + 小并行/级联 + 证据排序 | 「最优源」来自路由与验证，非单引擎 |
| 写入 | propose / confirm；批量导入同确认态 | 需求强制确认；禁止静默进库 |
| 内部 LLM | Qwen 仅 KM | 控制职责与成本 |
| 存储 | PostgreSQL（元数据）+ Qdrant（向量）+ 本地 Blob（原文）；排除 Gist | 对齐 tech-stack；热路径自持 |
| 多用户 | 一人一库一 Key；`user_id` 隔离 | 最简；不按调用方拆 Key |
| 管理员 | Web + Resend；种子 **`admin`/`admin`** + 仅种子强制改密；其后 **R2 邀请制**（邀请/重置设密不再强制改密） | 可多人管理；避免开放注册与长期默认密码 |

---

## 18. 待决配置项（非排期）

以下不影响架构形状，实现时选定即可：

- ~~公网域名~~ — 已定为 `kb.agent-mate.ai`（TLS 由生产 NPM / Let’s Encrypt 办理）
- DashScope embedding 模型 ID 与维度
- 默认 Web / 语义发现供应商账号与配额数值
- Pending TTL、库内「命中不足」阈值
- 批量导入限额（每批文件数、单文件/批次字节上限）
- 薄 OpenAI 兼容门面是否启用
- Resend 发件域名与邀请/重置链接 TTL
- 管理员会话时长与 Cookie 策略细节
