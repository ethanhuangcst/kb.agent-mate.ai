# Story Mapping — kb-agent

来源：`specs/req.md`（辅以 `specs/architecture.md`、`specs/mcp-design.md` 能力边界）。  
ATDD：用户故事 + Gherkin AC；实现前可据此写失败验收测试。

模块约定：

| 模块 | 含义 |
| --- | --- |
| **Web** | Admin 管理面（账号、Key、i18n） |
| **Agent** | 知识领域能力：鉴权语义、REST、检索/提案/确认/越界/补给编排（`KbService`） |
| **MCP** | MCP 门面：Streamable HTTP `/mcp`、遗留 SSE `/sse`、工具注册、与 REST 契约、Cursor/ChatBox 接入 |
| **RAG** | 确认后索引与库内检索 |

编号约定：功能编号前缀 = 模块小写（`web-*` / `agent-*` / `mcp-*` / `rag-*`）。原 `agent-mcp-01` 已拆入 **MCP** 模块（`mcp-01`…），勿再引用旧编号。

---

## 第一部分：Product Backlog

| 序号 | 模块 | 功能编号 | 功能名称 | 说明 | MVP批次 | 状态 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Web | web-acct-01 | 初始化默认管理员 | 无管理员时种子 `admin`/`admin`，默认邮箱 `me@ethanhuang.com`；关闭开放注册 | MVP-1 | Done |
| 2 | Web | web-acct-02 | 管理员登录 / 登出 | 用户名或邮箱+密码；联系管理员微信二维码；密码显示/隐藏 | MVP-1 | Done |
| 3 | Web | web-acct-03 | 忘记密码 / 重置 | Resend 短时一次性链接设新密 | MVP-3 | ToDo |
| 4 | Web | web-acct-04 | 邀请管理员（R2） | 已登录且已改密管理员邀请邮箱 → 对方设密成为管理员 | MVP-3 | ToDo |
| 5 | Web | web-acct-05 | 接受邀请设密 | 邀请链接落地；设英文姓名 + 密码后可登录 | MVP-3 | ToDo |
| 6 | Web | web-acct-06 | 种子账号强制改密 | 仅默认 `admin`/`admin`（`must_change_password`）；邀请/重置设密不走此门禁 | MVP-1 | Done |
| 7 | Web | web-acct-07 | 管理员列表 | 查看管理员（用户名/邮箱、状态、创建时间） | MVP-3 | ToDo |
| 8 | Web | web-acct-08 | 删除管理员 | 删除其他管理员；禁止删自己、禁止删光最后一名 | MVP-3 | ToDo |
| 9 | Web | web-keys-01 | 使用者列表 | 管理台查看已签发使用者（姓名、Key 前缀、状态） | MVP-1 | Done |
| 10 | Web | web-keys-02 | 签发 API Key | 英文姓名；明文单行可复制并密文入库；一人一把有效 Key | MVP-1 | Done |
| 11 | Web | web-keys-03 | 吊销 API Key | 确认后立即失效；列表移除该行；知识数据保留 | MVP-1 | Done |
| 12 | Web | web-keys-04 | 重签 API Key | 吊销旧 Key、发新 Key；同一使用者与库；不改姓名 | MVP-1 | Done |
| 12a | Web | web-keys-05 | 查看 API Key | 列表「查看」：姓名 + 完整明文可复制（密文存库） | MVP-1 | Done |
| 13 | Web | web-i18n-01 | 管理面文案 i18n | 用户可见文案走 i18n（默认 `zh-CN`，可扩展 `en`） | MVP-1 | Done |
| 14 | Agent | agent-auth-01 | Bearer 鉴权 | REST/MCP 统一 `Authorization: Bearer`；解析 `user_id`（实现可共用校验） | MVP-1 | Done |
| 15 | Agent | agent-auth-02 | 身份不可覆盖 | 请求体 / 工具参数中的用户标识不能覆盖 Key 身份 | MVP-1 | Done |
| 16 | Agent | agent-auth-03 | 租户隔离 | 各使用者数据强制隔离；默认无跨用户共享 | MVP-1 | Done |
| 17 | Agent | agent-auth-04 | 一人一库一 Key | 同一 Key 可用于 Cursor / ChatBox / HCP；不按调用方拆 Key | MVP-1 | Done |
| 18 | Agent | agent-search-01 | 库内检索 | 按输入检索已有知识；返回可引用片段 / 结构化命中 | MVP-1 | Done |
| 19 | Agent | agent-list-01 | 知识列表 | 按项目 / 标签等过滤列出知识条目 | MVP-2 | Done |
| 20 | Agent | agent-org-01 | 体系整理 | 归纳分类、标签、项目归属（重大变更可走确认） | MVP-3 | ToDo |
| 21 | Agent | agent-ingest-01 | 粘贴 / 单文件提案 | 材料 → 提案（摘要、分类、查重）；确认前不入库 | MVP-2 | Done |
| 22 | Agent | agent-ingest-02 | URL 拉取提案 | 指定 URL 拉取正文后进入提案 | MVP-4 | ToDo |
| 23 | Agent | agent-ingest-03 | 确认单条入库 | 显式 confirm 后持久化并触发索引 | MVP-2 | Done |
| 24 | Agent | agent-import-01 | 批量文档上传 | 多文件 → ImportBatch + 每文件提案；禁止静默进库 | MVP-3 | ToDo |
| 25 | Agent | agent-import-02 | 批次逐条 / 一键确认 | 逐条 confirm 或一键确认全部有效提案 | MVP-3 | ToDo |
| 26 | Agent | agent-import-03 | 批量格式与限额 | `.md` / `.txt` / 可抽文本 PDF；大小与个数上限；失败不阻塞同批 | MVP-3 | ToDo |
| 27 | Agent | agent-source-01 | 外部搜索候选 | 源路由搜索；返回候选列表；不自动落库 | MVP-4 | ToDo |
| 28 | Agent | agent-source-02 | 库内优先补给 | 优先库内；不足或显式要求时才外部 | MVP-4 | ToDo |
| 29 | Agent | agent-scope-01 | 拒绝业务策略越界 | 拒绝代劳投放策略 / 业务结论；可降级为公开资料候选 | MVP-3 | ToDo |
| 30 | Agent | agent-scope-02 | 拒绝开放式决策 | 只给证据与来源；不给「该怎么做」的最终决策 | MVP-3 | ToDo |
| 31 | Agent | agent-scope-03 | 拒绝无确认自动入库 | 拒绝「网上相关都自动进库」 | MVP-2 | Done |
| 32 | Agent | agent-scope-04 | 拒绝伪造库内引用 | 库内无据时明确不足；禁止捏造引用 | MVP-2 | Done |
| 33 | Agent | agent-rest-01 | 知识 REST | 与 MCP 工具语义对齐的结构化 API（HCP 等） | MVP-1 | Done |
| 34 | Agent | agent-chat-01 | 可选 OpenAI 兼容门面 | 薄封装同一工具集；同等越界规则；非业务中台 | MVP-4 | ToDo |
| 35 | Agent | agent-km-01 | 内部 Qwen 仅 KM | 归类 / 摘要提案 / 去重辅助；不做调用方业务洞察 | MVP-2 | Done |
| 35a | Agent | agent-summary-01 | 内容概述 ≤400 字 | propose 生成长概述；`kb_knowledge_summary` 读/刷新；list/search 可带 summary | MVP-2+ | Done |
| 36 | MCP | mcp-01 | Streamable HTTP 与 `/mcp` | 同进程挂载；路径固定 `/mcp`；主传输 Streamable HTTP | MVP-2 | Done |
| 37 | MCP | mcp-02 | MCP Bearer 鉴权 | 与 REST 同 Key / pepper；禁 query 传 Key；context 注入 `user_id` | MVP-2 | Done |
| 38 | MCP | mcp-03 | 最小工具集注册 | `kb_internal_search` / `kb_propose_add` / `kb_confirm_add`（可选 `kb_list_knowledge`）+ `kb_knowledge_summary` | MVP-2 | Done |
| 39 | MCP | mcp-04 | 与 REST 领域一致 | 同 `KbService`；`contracts/mcp-tools.json`；无第二套业务逻辑 | MVP-2 | Done |
| 40 | MCP | mcp-05 | Cursor / ChatBox 手测 | URL+Bearer 配置；propose→confirm→search 可手验 | MVP-2 | Done |
| 41 | MCP | mcp-06 | 工具面扩展 | 随领域交付注册 import / org 等；不重写门面 | MVP-3 | ToDo |
| 42 | RAG | rag-index-01 | 确认后分块索引 | confirm 后分块、向量化、写入向量库 | MVP-2 | Done |
| 43 | RAG | rag-index-02 | 禁止未确认索引 | 提案态不写向量、不建正式条目 | MVP-1 | Done |
| 44 | RAG | rag-retrieve-01 | 混合检索与引用 | 库内混合检索；命中带可引用 chunk / item | MVP-2 | Done |
| 45 | RAG | rag-isolate-01 | 检索租户过滤 | 向量与元数据查询强制 `user_id` | MVP-1 | Done |
| 46 | RAG | rag-store-01 | 原文与元数据存储 | 原文 Blob + PostgreSQL 元数据；排除 Gist | MVP-1 | Done |

### MVP 规划（三批闭环）

每批须**独立闭环交付**：真实栈可测；DoD **禁用** Fake Embedder / 假 KM / mock RAG HTTP / 假邮件 Outbox。细则见 `specs/mvp-2-3-delivery.md`。  
（MVP-4：URL / 外部源 / Chat 门面 — 延后，不列入下表。）

#### MVP-1 — 地基（17）· Done

目标：可登录、可发 Key、可鉴权空检索（**REST**；MCP 门面在 MVP-2）。  
验收日期：2026-08-11。证据：`make test`（schema 2 + rag 7 + agent 9 + vitest 9）+ Playwright Admin E2E 5/5；ADR-002 / ADR-003；知识笔记见 `specs/knowledge/`。  
**用户确认可用：** 2026-08-11（DoD User Acceptance）。

| 模块 | 功能编号 | 功能名称 | 状态 |
| --- | --- | --- | --- |
| Web | web-acct-01 | 初始化默认管理员 | Done |
| Web | web-acct-02 | 管理员登录 / 登出 | Done |
| Web | web-acct-06 | 种子账号强制改密 | Done |
| Web | web-keys-01 | 使用者列表 | Done |
| Web | web-keys-02 | 签发 API Key | Done |
| Web | web-keys-03 | 吊销 API Key | Done |
| Web | web-keys-04 | 重签 API Key | Done |
| Web | web-keys-05 | 查看 API Key | Done |
| Web | web-i18n-01 | 管理面文案 i18n | Done |
| Agent | agent-auth-01 | Bearer 鉴权 | Done |
| Agent | agent-auth-02 | 身份不可覆盖 | Done |
| Agent | agent-auth-03 | 租户隔离 | Done |
| Agent | agent-auth-04 | 一人一库一 Key | Done |
| Agent | agent-search-01 | 库内检索 | Done |
| Agent | agent-rest-01 | 知识 REST | Done |
| RAG | rag-index-02 | 禁止未确认索引 | Done |
| RAG | rag-isolate-01 | 检索租户过滤 | Done |
| RAG | rag-store-01 | 原文与元数据存储 | Done |

#### MVP-2 — 知识闭环 + MCP 门面（13）· Done

目标：抽出/共用 `KbService`；真索引检索闭环；**MCP 模块**可挂 Cursor 手测。  
路径：粘贴 → 提案（真 KM）→ 确认 → 真向量索引 → 可引用检索；不可自动入库、不可伪造引用。  
约束：`USE_FAKE_EMBEDDER=false`；agent↔rag 真 HTTP；MCP 与 REST 同 `KbService`。  
本批 MCP 工具：`kb_internal_search` / `kb_propose_add` / `kb_confirm_add` / `kb_list_knowledge` / `kb_knowledge_summary`（概述 ≤400 字，方案 1+2；[`knowledge-summary.md`](./knowledge-summary.md)、`agent-summary-01`）。  
专文：[`mcp-design.md`](./mcp-design.md)；契约：[`contracts/mcp-tools.json`](../contracts/mcp-tools.json)。  
验收日期：2026-08-11。证据：`scripts/mvp2_true_stack_journey.py`（真 DashScope KM + `text-embedding-v3` + Qdrant `kb_chunks_v3`）全绿；MCP `initialize` + Bearer（含裸 `/mcp` 路径）；fixture 车道 `make test`。  
**用户确认可用：** 已确认（2026-08-11）。

| 模块 | 功能编号 | 功能名称 | 状态 |
| --- | --- | --- | --- |
| MCP | mcp-01 | Streamable HTTP 与 `/mcp` | Done |
| MCP | mcp-02 | MCP Bearer 鉴权 | Done |
| MCP | mcp-03 | 最小工具集注册 | Done |
| MCP | mcp-04 | 与 REST 领域一致 | Done |
| MCP | mcp-05 | Cursor / ChatBox 手测 | Done |
| Agent | agent-ingest-01 | 粘贴 / 单文件提案 | Done |
| Agent | agent-km-01 | 内部 Qwen 仅 KM | Done |
| Agent | agent-summary-01 | 内容概述 ≤400 字 | Done |
| Agent | agent-ingest-03 | 确认单条入库 | Done |
| RAG | rag-index-01 | 确认后分块索引 | Done |
| RAG | rag-retrieve-01 | 混合检索与引用 | Done |
| Agent | agent-list-01 | 知识列表 | Done |
| Agent | agent-scope-03 | 拒绝无确认自动入库 | Done |
| Agent | agent-scope-04 | 拒绝伪造库内引用 | Done |

建议实现顺序：`KbService` + 领域闭环（ingest/km/index/retrieve）→ **mcp-01…04** → **mcp-05** 手测。

#### MVP-3 — 操作面与 MCP 工具扩展（12）· ToDo

目标：批量导入确认；体系整理；多管理员（真 Resend）；对话向越界（scope-01/02）；**mcp-06** 扩展 MCP 工具面（import/org），不重写门面。

| 模块 | 功能编号 | 功能名称 | 状态 |
| --- | --- | --- | --- |
| MCP | mcp-06 | 工具面扩展 | ToDo |
| Agent | agent-import-01 | 批量文档上传 | ToDo |
| Agent | agent-import-02 | 批次逐条 / 一键确认 | ToDo |
| Agent | agent-import-03 | 批量格式与限额 | ToDo |
| Agent | agent-org-01 | 体系整理 | ToDo |
| Agent | agent-scope-01 | 拒绝业务策略越界 | ToDo |
| Agent | agent-scope-02 | 拒绝开放式决策 | ToDo |
| Web | web-acct-03 | 忘记密码 / 重置 | ToDo |
| Web | web-acct-04 | 邀请管理员（R2） | ToDo |
| Web | web-acct-05 | 接受邀请设密 | ToDo |
| Web | web-acct-07 | 管理员列表 | ToDo |
| Web | web-acct-08 | 删除管理员 | ToDo |

---

## 第二部分：用户故事与验收标准（AC）

### 模块：Web

#### 功能 web-acct-01 — 初始化默认管理员

**用户故事**  
As an 运维人员，  
I want Web 初始化时自动创建默认管理员账号，  
So that 无需开放注册即可首次登录管理台。

**AC**

```gherkin
Scenario: 空库初始化种子账号 admin/admin
  Given 应用数据库中尚无任何管理员
  When Web / Admin 完成初始化
  Then 存在登录名为 admin、初始密码为 admin 的管理员账号
  And 该账号联系邮箱为 me@ethanhuang.com（可由 BOOTSTRAP_ADMIN_EMAIL 覆盖）
  And 该账号标记为必须修改密码
  And 开放自助注册入口不可用

Scenario: 已有管理员时不重复种子
  Given 系统中至少已有一名管理员
  When 应用再次启动或初始化
  Then 不创建第二个默认 admin 种子账号
  And 新管理员只能通过邀请产生
```

#### 功能 web-acct-02 — 管理员登录 / 登出

**用户故事**  
As an 管理员，  
I want 使用用户名或邮箱和密码登录管理台并安全登出，  
So that 我能管理使用者 Key 且会话可控。

**AC**

```gherkin
Scenario: 正确凭证登录成功
  Given 存在已设密的管理员账号且无需强制改密
  And 管理员在登录页
  When 管理员输入正确用户名或邮箱与密码并提交
  Then 管理员进入管理台
  And 会话已建立

Scenario: 默认账号可用 admin/admin 登录
  Given 种子管理员仍为初始密码 admin
  When 管理员以用户名 admin 与密码 admin 提交登录
  Then 登录凭证校验通过
  And 会话进入必须修改密码状态

Scenario: 可用种子邮箱登录
  Given 种子管理员邮箱为 me@ethanhuang.com
  When 管理员以该邮箱与正确密码提交登录
  Then 登录凭证校验通过

Scenario: 登录页联系管理员展示微信二维码
  Given 访客在登录页
  When 访客悬停或聚焦「联系管理员」
  Then 浮层展示管理员微信二维码（EthanWeChat.png）

Scenario: 错误密码登录失败
  Given 存在已设密的管理员账号
  When 管理员输入正确登录名与错误密码并提交
  Then 系统显示登录失败提示
  And 不建立管理员会话
  And 管理员仍停留在可登录状态

Scenario: 登出清除会话
  Given 管理员已登录
  When 管理员登出
  Then 会话失效
  And 未登录时无法访问需鉴权的管理能力
```

#### 功能 web-acct-03 — 忘记密码 / 重置

**用户故事**  
As an 管理员，  
I want 通过邮件重置密码，  
So that 忘记密码时仍能恢复访问。

**AC**

```gherkin
Scenario: 请求重置并收到邮件链接
  Given 存在管理员账号
  When 管理员提交忘记密码请求且邮箱正确
  Then 系统经 Resend 发出重置链接
  And 链接为短时且一次性

Scenario: 使用有效链接设新密码
  Given 管理员持有未过期的重置链接
  When 管理员设置新密码并确认
  Then 新密码可用于登录
  And 旧重置链接不可再次使用
  And must_change_password 为 false
  And 下次登录不进入强制改密门禁

Scenario: 过期或已用链接无效
  Given 重置链接已过期或已使用
  When 管理员尝试用该链接设密
  Then 系统拒绝设密
  And 提示链接无效或已过期
```

#### 功能 web-acct-04 — 邀请管理员（R2）

**用户故事**  
As an 已登录且已完成改密的管理员，  
I want 邀请新管理员邮箱，  
So that 团队可多人管理且无开放注册风险。

**AC**

```gherkin
Scenario: 已登录管理员发送邀请
  Given 管理员已登录且不处于强制改密状态
  When 管理员输入有效邮箱并发送邀请
  Then 系统经 Resend 向该邮箱发送邀请链接
  And 被邀请人尚未设密前不能以管理员身份登录业务管理台

Scenario: 未登录者不能邀请
  Given 访客未登录管理台
  When 访客尝试发起管理员邀请
  Then 系统拒绝该操作

Scenario: 强制改密未完成不能邀请
  Given 管理员已登录但仍必须修改密码
  When 管理员尝试发送邀请
  Then 系统拒绝该操作
```

#### 功能 web-acct-05 — 接受邀请设密

**用户故事**  
As an 被邀请人，  
I want 通过邀请链接设置英文姓名与密码，  
So that 我成为管理员并可登录，且顶栏显示我的姓名。

**AC**

```gherkin
Scenario: 有效邀请链接设姓名与密码成功
  Given 被邀请人打开未过期的邀请链接
  When 被邀请人填写符合规则的英文姓名与密码并提交
  Then 该邮箱成为管理员
  And must_change_password 为 false
  And 可用该邮箱密码直接登录管理台并使用管理能力
  And 顶栏问候显示 Hello, {英文姓名}
  And 不进入种子账号的强制改密流程

Scenario: 拒绝非英文姓名
  Given 被邀请人打开未过期的邀请链接
  When 被邀请人提交含非英文字符的姓名
  Then 系统拒绝提交
  And 提示姓名仅限英文

Scenario: 无效邀请链接被拒绝
  Given 邀请链接无效、过期或已使用
  When 被邀请人尝试设密
  Then 系统拒绝设密
  And 不创建新的管理员会话
```

#### 功能 web-acct-06 — 种子账号强制改密

**用户故事**  
As an 使用默认种子账号的管理员，  
I want 用 `admin` / `admin` 登录后必须修改密码，  
So that 公开默认口令不会长期处于可管理状态。

**范围（与邀请/重置无冲突）**  
- **适用**：仅初始化种子账号（及仍标记 `must_change_password=true` 的账号，例如仍为默认口令时）。  
- **不适用**：经邀请链接设密（web-acct-05）、经忘记密码重置设密（web-acct-03）——当事人已自选密码，设密成功即 `must_change_password=false`，登录后**不再**强制改密。

**AC**

```gherkin
Scenario: 种子账号登录后进入强制改密
  Given 种子管理员仍标记为必须修改密码
  When 管理员以 admin / admin 登录成功
  Then 系统要求立即修改密码
  And 在完成改密前不能访问使用者列表、签发 Key 或邀请管理员

Scenario: 改密成功后解除限制
  Given 管理员处于必须修改密码状态
  When 管理员设置符合要求的新密码并确认（新密码不得与 admin 相同）
  Then must_change_password 被清除
  And 管理员可使用完整管理台能力
  And 之后须用新密码登录

Scenario: 未改密时拒绝管理写操作
  Given 管理员已登录但仍必须修改密码
  When 管理员尝试签发 API Key 或发送管理员邀请
  Then 系统拒绝该操作
  And 提示须先修改密码

Scenario: 邀请设密的管理员不走强制改密
  Given 管理员通过邀请链接已设密且 must_change_password 为 false
  When 该管理员用自设密码登录
  Then 系统不要求再次修改密码
  And 可直接使用管理台能力
```

#### 功能 web-acct-07 — 管理员列表

**用户故事**  
As an 已登录且已完成改密的管理员，  
I want 查看管理员列表，  
So that 我知道谁可以管理本系统。

**AC**

```gherkin
Scenario: 已登录管理员看到管理员列表
  Given 管理员已登录且不处于强制改密状态
  And 系统中存在至少两名管理员
  When 管理员打开管理员列表
  Then 列表展示各管理员的用户名或邮箱、状态与创建时间
  And 不展示密码哈希或会话密钥

Scenario: 未改密不能查看管理员列表
  Given 管理员已登录但仍必须修改密码
  When 管理员尝试打开管理员列表
  Then 系统拒绝或引导先修改密码
```

#### 功能 web-acct-08 — 删除管理员

**用户故事**  
As an 已登录且已完成改密的管理员，  
I want 删除其他管理员账号，  
So that 离职或误邀账号无法继续登录管理台。

**AC**

```gherkin
Scenario: 删除其他管理员成功
  Given 系统中存在管理员 A 与管理员 B
  And 管理员 A 已登录且不处于强制改密状态
  When 管理员 A 删除管理员 B
  Then 管理员 B 不能再登录管理台
  And 管理员列表不再包含管理员 B 为有效管理员
  And 使用者 API Key 与知识库数据不受影响

Scenario: 禁止删除自己
  Given 管理员 A 已登录
  When 管理员 A 尝试删除自己的管理员账号
  Then 系统拒绝该操作
  And 管理员 A 仍可登录

Scenario: 禁止删除最后一名管理员
  Given 系统中仅剩一名有效管理员
  When 该管理员尝试删除这名管理员（无论是否本人）
  Then 系统拒绝该操作
  And 系统中仍至少保留一名有效管理员

Scenario: 未登录或未改密不能删除
  Given 访客未登录，或管理员仍必须修改密码
  When 其尝试删除某管理员
  Then 系统拒绝该操作
```

#### 功能 web-keys-01 — 使用者列表

**用户故事**  
As an 管理员，  
I want 查看已签发的使用者列表，  
So that 我知道谁持有 Key 及状态。

**AC**

```gherkin
Scenario: 已登录管理员看到使用者列表
  Given 管理员已登录
  And 系统中存在至少一名已签发使用者
  When 管理员打开使用者列表
  Then 列表展示使用者姓名、Key 前缀与状态
  And 每行提供「查看」入口（完整明文不在列表内联展示）
```

#### 功能 web-keys-02 — 签发 API Key

**用户故事**  
As an 管理员，  
I want 为使用者填写姓名并签发一把 API Key，  
So that 该使用者能用同一把 Key 访问全局知识库。

**AC**

```gherkin
Scenario: 签发成功展示明文并可再次查看
  Given 管理员已登录
  When 管理员填写符合规则的英文使用者姓名（如 Daniel Foster）并签发 Key
  Then 系统创建该使用者与一把有效 Key
  And 完整 Key 明文在结果页单行展示且可复制
  And 库内保存 key_hash 与可解密的 key_ciphertext
  And 之后可从列表「查看」再次取得同一明文

Scenario: 非英文姓名拒签
  Given 管理员已登录并打开签发表单
  When 管理员提交含非拉丁字母的姓名
  Then 系统拒绝签发并提示仅允许英文

Scenario: 同一使用者不能同时有两把有效 Key
  Given 某使用者已有一把有效 Key
  When 管理员试图再签发第二把有效 Key 给同一使用者而不先吊销或重签
  Then 系统拒绝或要求走重签流程
  And 仍最多一把有效 Key
```

#### 功能 web-keys-03 — 吊销 API Key

**用户故事**  
As an 管理员，  
I want 吊销使用者的 API Key，  
So that 泄露或离职时立即切断访问。

**AC**

```gherkin
Scenario: 吊销后知识面立即拒绝且列表移除
  Given 使用者持有有效 Key
  And 管理员已登录
  When 管理员确认吊销该秘钥
  Then 使用原 Key 的知识面请求被拒绝
  And 该使用者知识数据仍保留但无法再经该 Key 访问
  And 使用者列表不再显示该行
```

#### 功能 web-keys-04 — 重签 API Key

**用户故事**  
As an 管理员，  
I want 为同一使用者重签 Key，  
So that 轮换密钥后知识库不断、姓名不变。

**AC**

```gherkin
Scenario: 重签保留同一知识库
  Given 使用者已有知识条目与有效 Key
  And 管理员已登录
  When 管理员对该使用者执行重签
  Then 旧 Key 立即失效
  And 新 Key 明文展示且密文入库
  And 使用者姓名不变
  And 用新 Key 仍可检索到原有知识
```

#### 功能 web-keys-05 — 查看 API Key

**用户故事**  
As an 管理员，  
I want 从使用者列表打开某把有效 Key 的查看页，  
So that 我能再次看到姓名与完整明文并复制。

**AC**

```gherkin
Scenario: 查看有效 Key
  Given 管理员已登录
  And 存在带 key_ciphertext 的有效 Key
  When 管理员点击该行「查看」
  Then 页面展示使用者姓名与完整 Key 明文
  And 提供一键复制
  And 不展示「仅此一次」类文案

Scenario: 无密文的历史 Key
  Given 管理员已登录
  And 某有效 Key 无 key_ciphertext（迁移前签发）
  When 管理员打开查看
  Then 系统提示无法展示明文并建议重签
```

#### 功能 web-i18n-01 — 管理面文案 i18n

**用户故事**  
As an 管理员，  
I want 管理台文案通过语言包展示，  
So that 界面不硬编码单一语言且可扩展 locale。

**AC**

```gherkin
Scenario: 默认 locale 解析文案
  Given 管理台默认 locale 为 zh-CN
  When 管理员打开登录或使用者列表页
  Then 可见文案来自 i18n 词条而非散落硬编码业务句
  And 页脚 copyright 文案亦走 i18n key
  And 缺少词条时有明确回退行为而不白屏崩溃
```

---

### 模块：Agent

知识领域能力与 REST / 越界 / 补给。**MCP 协议门面**见下一节「模块：MCP」。

#### 功能 agent-auth-01 — Bearer 鉴权

**用户故事**  
As a 调用方应用，  
I want 用 Bearer API Key 调用 MCP 与 REST，  
So that 鉴权方式统一、配置简单。

**AC**

```gherkin
Scenario: 有效 Key 可访问知识能力
  Given 使用者持有有效 API Key
  When 调用方携带 Authorization Bearer 该 Key 请求知识检索
  Then 请求被接受并按该使用者身份执行

Scenario: 缺失或无效 Key 被拒绝
  Given 请求未带 Key 或 Key 无效
  When 调用方请求受保护的知识能力
  Then 系统拒绝访问
  And 不返回其他使用者的知识
```

#### 功能 agent-auth-02 — 身份不可覆盖

**用户故事**  
As a 安全负责方，  
I want 请求体中的用户标识不能覆盖 Key 身份，  
So that 无法冒充其他使用者。

**AC**

```gherkin
Scenario: 请求体伪造 user_id 无效
  Given 调用方持有使用者 A 的有效 Key
  When 调用方在请求体中声称自己是使用者 B 并检索
  Then 系统仍仅以 Key 解析的使用者 A 执行
  And 不返回使用者 B 的知识
```

#### 功能 agent-auth-03 — 租户隔离

**用户故事**  
As a 使用者，  
I want 我的知识默认不被其他使用者看到，  
So that 私人知识库真正隔离。

**AC**

```gherkin
Scenario: 跨使用者检索不可见
  Given 使用者 A 与使用者 B 各自库中有不同知识
  When 使用者 A 用自己的 Key 检索本应只属于 B 的内容
  Then 结果中不出现使用者 B 的知识条目或片段
```

#### 功能 agent-auth-04 — 一人一库一 Key

**用户故事**  
As a 使用者，  
I want 同一把 Key 用于 Cursor、ChatBox 与 HCP，  
So that 我不必按调用方管理多把密钥。

**AC**

```gherkin
Scenario: 同一 Key 跨调用方面生效
  Given 使用者持有一把有效 Key 且库中已有知识
  When 分别经 MCP 与 REST 使用同一 Key 检索
  Then 两次均可访问同一全局知识库
  And 系统不要求按调用方拆分 Key
```

#### 功能 agent-search-01 — 库内检索

**用户故事**  
As a 调用方（及其 LLM），  
I want 按输入检索知识库，  
So that 我能基于可引用片段继续业务推理。

**AC**

```gherkin
Scenario: 命中时返回可引用结构化结果
  Given 使用者库中存在与查询相关的已确认知识
  When 调用方发起库内检索
  Then 返回结构化命中
  And 命中包含可引用的条目或片段信息

Scenario: 无命中时明确不足
  Given 使用者库中无相关已确认知识
  When 调用方发起库内检索
  Then 系统表明证据不足或空命中
  And 不捏造库内引用
```

#### 功能 agent-list-01 — 知识列表

**用户故事**  
As a 调用方，  
I want 按项目或标签列出知识，  
So that 我能浏览与管理知识体系。

**AC**

```gherkin
Scenario: 按过滤条件列出本用户知识
  Given 使用者库中有带不同项目或标签的条目
  When 调用方按某一项目或标签列出
  Then 仅返回符合条件且属于该使用者的条目
```

#### 功能 agent-org-01 — 体系整理

**用户故事**  
As a 调用方，  
I want 请求归纳分类、标签或项目归属，  
So that 知识结构更清晰。

**AC**

```gherkin
Scenario: 整理建议不越界做业务策略
  Given 使用者库中存在可整理的知识
  When 调用方请求归纳分类或标签
  Then 系统返回分类 / 标签 / 项目归属类整理结果或提案
  And 不生成投放策略或业务决策结论
```

#### 功能 agent-ingest-01 — 粘贴 / 单文件提案

**用户故事**  
As a 调用方，  
I want 粘贴或上传单份材料生成入库提案，  
So that 确认前知识不会静默进库。

**AC**

```gherkin
Scenario: 材料进入提案态
  Given 使用者持有有效 Key
  When 调用方提交可解析的粘贴正文或单文件要求入库
  Then 系统生成含摘要、分类建议与查重信息的提案
  And 此时知识库正式条目与向量索引尚未写入该材料

Scenario: 确认前检索不到该材料为已入库知识
  Given 某材料仅处于提案态
  When 调用方按该材料主题做库内检索
  Then 结果不以「已确认入库知识」形式返回该材料
```

#### 功能 agent-ingest-02 — URL 拉取提案

**用户故事**  
As a 调用方，  
I want 指定 URL 拉取正文再提案，  
So that 我能把公开网页材料纳入确认流。

**AC**

```gherkin
Scenario: 合法 URL 拉取后生成提案
  Given 使用者持有有效 Key
  And 目标 URL 可在出站策略内访问并抽取正文
  When 调用方请求按该 URL 补给并入库提案
  Then 系统拉取正文并生成提案
  And 不在确认前写入正式条目与向量

Scenario: 不安全或失败的 URL 被拒绝
  Given 目标 URL 违反出站策略或无法抽取正文
  When 调用方请求拉取该 URL
  Then 系统返回明确失败
  And 不假装已入库
```

#### 功能 agent-ingest-03 — 确认单条入库

**用户故事**  
As a 调用方，  
I want 显式确认提案后入库，  
So that 只有我同意的材料进入知识库。

**AC**

```gherkin
Scenario: 确认后可被检索
  Given 存在属于该使用者的待确认提案
  When 调用方确认该提案
  Then 材料成为正式知识条目
  And 随后库内检索可以命中并带引用

Scenario: 未确认不能当作已入库
  Given 提案仍待确认
  When 任何路径试图跳过确认直接索引
  Then 系统拒绝或无此能力
```

#### 功能 agent-import-01 — 批量文档上传

**用户故事**  
As a 调用方，  
I want 一次上传多份文档并得到每份提案，  
So that 我能批量整理材料但仍保持确认门禁。

**AC**

```gherkin
Scenario: 批量上传生成批次与多条提案
  Given 使用者持有有效 Key
  When 调用方一次上传多份可解析文档
  Then 系统创建导入批次
  And 每份可解析文档对应一条提案
  And 没有任何文档因上传成功而自动成为已确认知识

Scenario: 拒绝无确认的自动全量入库意图
  Given 使用者持有有效 Key
  When 调用方要求上传后自动全部进库且无需确认
  Then 系统拒绝该越界要求
```

#### 功能 agent-import-02 — 批次逐条 / 一键确认

**用户故事**  
As a 调用方，  
I want 逐条确认或一键确认批次内全部有效提案，  
So that 我能显式完成批量入库。

**AC**

```gherkin
Scenario: 逐条确认批次中的一条
  Given 导入批次中有多条待确认提案
  When 调用方确认其中一条
  Then 仅该条成为正式知识
  And 其余提案仍待确认

Scenario: 一键确认全部有效提案
  Given 导入批次中存在多条可确认提案
  When 调用方对批次执行一键确认全部有效提案
  Then 所有可确认提案被确认入库
  And 该操作是显式批量确认而非跳过确认态
```

#### 功能 agent-import-03 — 批量格式与限额

**用户故事**  
As a 调用方，  
I want 系统支持约定格式并限制批次规模，  
So that 导入可控且坏文件不拖垮整批。

**AC**

```gherkin
Scenario: 支持基线格式
  Given 使用者上传 .md、.txt 与可抽取文本的 PDF
  When 系统解析批次
  Then 可解析文件各自生成提案

Scenario: 无法抽取正文的文件标记失败且不阻塞同批
  Given 批次中混有无法抽取正文的文件与正常文件
  When 系统处理该批次
  Then 无法抽取者标记失败
  And 正常文件仍可生成提案

Scenario: 超过文件数或体积上限被拒绝
  Given 上传超过单文件或批次限额
  When 调用方提交该批次
  Then 系统拒绝超额部分或整批并返回明确错误
```

#### 功能 agent-source-01 — 外部搜索候选

**用户故事**  
As a 调用方，  
I want 按源路由获得外部搜索候选列表，  
So that 我能挑选证据再决定是否提案入库。

**AC**

```gherkin
Scenario: 外部搜索返回候选且不落库
  Given 使用者获准进行外部搜索
  When 调用方发起外部知识候选检索
  Then 返回含标题、URL、摘要、来源类型等信号的候选列表
  And 候选不会自动写入正式知识库或向量索引
```

#### 功能 agent-source-02 — 库内优先补给

**用户故事**  
As a 调用方，  
I want 系统优先用库内知识、不足时再外部补给，  
So that 减少不必要外呼并复用已有沉淀。

**AC**

```gherkin
Scenario: 库内足够时可不强制外部
  Given 库内检索已足以回答知识查询
  And 调用方未显式要求外部补给
  When 调用方请求获取相关知识
  Then 系统可仅返回库内命中
  And 不强制发起外部搜索

Scenario: 不足或显式要求时启用外部
  Given 库内命中不足或调用方显式要求外部
  When 调用方请求补给
  Then 系统可走源路由外部候选检索
```

#### 功能 agent-scope-01 — 拒绝业务策略越界

**用户故事**  
As a 产品负责人，  
I want kb-agent 拒绝代劳业务策略，  
So that 职责边界清晰、调用方 LLM 自行决策。

**AC**

```gherkin
Scenario: 要求投放策略被拒绝
  Given 调用方持有有效 Key
  When 调用方要求根据业务数据上网查竞品并直接给出投放策略
  Then 系统拒绝生成投放策略或业务结论
  And 返回稳定的越界错误码或明确拒绝说明
  And 可选仅提供公开资料候选与来源供调用方自行推理
```

#### 功能 agent-scope-02 — 拒绝开放式决策

**用户故事**  
As a 产品负责人，  
I want 系统不回答「研究完告诉我该怎么做」，  
So that kb-agent 只提供证据不替做生意。

**AC**

```gherkin
Scenario: 开放式「告诉我该怎么做」被约束
  Given 调用方持有有效 Key
  When 调用方要求研究完毕并直接给出最终行动决策
  Then 系统只提供检索片段或外部候选与来源
  And 不给出最终业务决策
```

#### 功能 agent-scope-03 — 拒绝无确认自动入库

**用户故事**  
As a 产品负责人，  
I want 拒绝无确认的全量自动入库，  
So that 知识库写入始终经确认门禁。

**AC**

```gherkin
Scenario: 「网上相关都自动进库」被拒绝
  Given 调用方持有有效 Key
  When 调用方要求将网上相关内容自动全部入库且无需确认
  Then 系统拒绝
  And 返回与无确认自动入库相关的稳定错误码或说明
```

#### 功能 agent-scope-04 — 拒绝伪造库内引用

**用户故事**  
As a 调用方，  
I want 库中无据时被告知不足，  
So that 我不会被捏造的「知识库说过」误导。

**AC**

```gherkin
Scenario: 无依据时禁止假装库内说过
  Given 使用者库中没有相关依据
  When 调用方要求系统「就当知识库说过」某结论
  Then 系统明确表示证据不足
  And 不捏造库内引用
  And 可建议外部补给或入库提案
```

#### 功能 agent-rest-01 — 知识 REST

**用户故事**  
As a HCP 等应用，  
I want 用结构化 REST 调用同一套知识能力，  
So that 应用侧 LLM 可集成 search / propose / confirm。

**AC**

```gherkin
Scenario: REST 与 MCP 语义对齐
  Given 使用者持有有效 Key
  When 应用经 REST 执行检索与确认入库
  Then 结果语义与 MCP 对应工具一致（见 mcp-04）
  And 鉴权同为 Bearer API Key
```

#### 功能 agent-chat-01 — 可选 OpenAI 兼容门面

**用户故事**  
As a 调试或薄集成方，  
I want 可选的 OpenAI 兼容入口调用同一工具集，  
So that 我能调试而不把服务做成业务中台。

**AC**

```gherkin
Scenario: 薄门面执行相同越界规则
  Given 可选 Chat 门面已启用
  When 调用方通过该门面要求生成业务投放策略
  Then 系统按与 MCP 相同的规则拒绝越界
  And 不扩展出无边界业务 Agent 能力
```

#### 功能 agent-km-01 — 内部 Qwen 仅 KM

**用户故事**  
As a 产品负责人，  
I want 内部 Qwen 只做知识管理辅助，  
So that 成本与职责可控。

**AC**

```gherkin
Scenario: 内部模型用于提案摘要与归类
  Given 材料进入提案流程
  When 系统生成摘要或分类建议
  Then 可使用内部 Qwen 完成该类知识管理任务
  And 不把「替调用方完成业务洞察」作为成功路径
```

#### 功能 agent-summary-01 — 内容概述 ≤400 字

**用户故事**  
As a Cursor 用户，  
I want 每条知识有可读的内容概述（≤400 字），并能按需读取或刷新，  
So that 我不必打开全文也能判断条目是否相关。

**AC**

```gherkin
Scenario: propose 写入长概述
  Given 用户提交足够长的正文
  When 调用 kb_propose_add
  Then 返回的 summary 为内容概述且长度 ≤ 400 字
  And 不是仅标题复述一句

Scenario: 读取与刷新概述
  Given 库中已有 knowledge_id 或 pending_id
  When 调用 kb_knowledge_summary 且 refresh=false
  Then 返回已存 summary
  When 调用 kb_knowledge_summary 且 refresh=true
  Then 根据正文重生概述并写回且 ≤ 400 字

Scenario: list / search 暴露概述
  Given 已确认条目带 summary
  When 调用 kb_list_knowledge 或 kb_internal_search
  Then 结果项可包含 summary 字段
```

专文：[`knowledge-summary.md`](./knowledge-summary.md)。

---

### 模块：MCP

设计专文：[`specs/mcp-design.md`](./mcp-design.md)。契约：[`contracts/mcp-tools.json`](../contracts/mcp-tools.json)。  
本模块只做**协议门面**；领域行为由 Agent/RAG 故事覆盖。MCP 与 REST **必须**调用同一 `KbService`。

#### 功能 mcp-01 — Streamable HTTP 与 `/mcp`

**用户故事**  
As a Cursor / ChatBox 用户，  
I want kb-agent 以标准远程 MCP 传输暴露固定路径，  
So that 我可以按文档配置 URL 而无需猜端口协议。

**AC**

```gherkin
Scenario: 固定路径与传输
  Given kb-agent 进程已启动
  When 客户端以 Streamable HTTP 访问 /mcp
  Then MCP 会话可建立（或按 SDK 语义返回可诊断错误，而非静默 404 到错误服务）
  And MCP 与知识 REST 运行在同一 FastAPI 进程
  And 生产反代路径为 https://kb.agent-mate.ai/mcp（本地为 http://127.0.0.1:8000/mcp）

Scenario: healthz 不等于 MCP 可用
  Given GET /healthz 返回成功
  When 仅凭健康检查判断
  Then 不得宣称 MCP 工具已可用；须以 /mcp + 鉴权后 list_tools 或等价为准
```

#### 功能 mcp-02 — MCP Bearer 鉴权

**用户故事**  
As a 使用者，  
I want MCP 使用与 REST 同一把 API Key，  
So that 我只需配置一次密钥。

**AC**

```gherkin
Scenario: 有效 Bearer 可列工具 / 调工具
  Given 管理台签发的有效使用者 Key
  When 客户端在 MCP 请求携带 Authorization: Bearer <key>
  Then 解析出与 REST 相同的 user_id
  And 可执行已注册工具

Scenario: 缺失或吊销 Key
  Given 无 Authorization 或 Key 已吊销
  When 调用 MCP 受保护能力
  Then 拒绝访问（与 REST 稳定 code 对齐：UNAUTHORIZED / KEY_REVOKED 等）
  And 不泄露其他使用者数据

Scenario: 禁止危险传 Key 方式
  Given 客户端尝试把 Key 放进 URL query、路径或工具参数
  When 服务端处理请求
  Then 不以 query/path/tool-arg 作为有效凭证
  And 工具参数中的 user_id（若有）被忽略，身份仅来自 Bearer
```

#### 功能 mcp-03 — 最小工具集注册

**用户故事**  
As a 宿主模型，  
I want 只看到少量清晰工具，  
So that 我能可靠选择检索与确认入库而不被工具表淹没。

**AC**

```gherkin
Scenario: MVP-2 仅注册最小集
  Given MCP 服务器已启动且鉴权成功
  When 客户端 list_tools
  Then 至少包含 kb_internal_search、kb_propose_add、kb_confirm_add
  And 可选包含 kb_list_knowledge
  And 包含 kb_knowledge_summary（内容概述读/刷新；见 agent-summary-01）
  And 不包含 kb_import_*、kb_organize、kb_external_search、kb_fetch_url（属后续批次）

Scenario: 写工具描述含边界
  Given 已注册 kb_propose_add 与 kb_confirm_add
  When 读取其 description
  Then 说明不会自动入库、须 confirm
  And 说明不生成业务策略 / 投放结论
  And 说明仅操作用户 Key 所属知识库

Scenario: 无跳过确认参数
  Given 任意已注册写工具的 input schema
  When 检查参数表
  Then 不存在 skip_confirm / auto_ingest 一类绕过确认的参数
```

#### 功能 mcp-04 — 与 REST 领域一致

**用户故事**  
As a 平台维护者，  
I want MCP 与 REST 共用领域层且契约可对拍，  
So that 双门面不会漂移出第二套业务逻辑。

**AC**

```gherkin
Scenario: 同 Key 同输入同语义
  Given 同一有效 Key 与同一 propose/confirm/search 输入
  When 分别经 MCP 工具与对应 REST 路径执行
  Then 核心 payload 字段一致（允许协议包装层差异）
  And 越界 / 不足时 code 一致

Scenario: 禁止 MCP 旁路
  Given 实现代码审查或架构测试
  When MCP handler 执行检索或确认
  Then 必须调用 KbService（或与 REST 相同的领域入口）
  And 不得在 MCP 内单独直连 RAG/SQL 形成第二路径

Scenario: 契约工件
  Given contracts/mcp-tools.json 与 search-response.schema.json
  When 跑契约检查
  Then 已注册工具名与映射 REST 路径与文档一致
  And forbidden_params 含 user_id（及写工具的 skip_confirm）
```

#### 功能 mcp-05 — Cursor / ChatBox 手测

**用户故事**  
As a Cursor / ChatBox 用户，  
I want 按接入指南手动添加 MCP 并走通最小闭环，  
So that 我确认远程工具在真实宿主里可用。

**AC**

```gherkin
Scenario: Cursor 手测最小闭环（DoD 证据）
  Given 本地或预发 kb-agent 已暴露 /mcp 且 USE_FAKE_EMBEDDER=false（闭环门禁）
  And 使用者持有管理台签发的 Key
  When 在 Cursor 中配置 Streamable HTTP URL=…/mcp 与 Bearer Key
  And 依次 kb_propose_add → kb_confirm_add → kb_internal_search
  Then 提案未确认前 search 无该条正式知识命中
  And 确认后 search 返回可引用命中（含 knowledge_id / chunk_id / text）
  And 手测记录可附配置方式（URL 形态），不得把明文 Key 写入仓库

Scenario: ChatBox SSE 手测
  Given kb-agent 已暴露 GET /sse 与 POST /messages/
  When 在 ChatBox 中配置 Type=Remote (http/sse)、URL=…/sse、Header Authorization=Bearer <key>
  And Test 通过并启用该 MCP
  Then 可调用与 Cursor 相同的工具集（至少 list / search）
  And 不得把 URL 配成 /mcp（会导致 SSE 404）

Scenario: 接入指南文案一致
  Given Admin /guide 或 mockup 接入指南
  When 阅读 MCP 说明
  Then 写明 Cursor=/mcp（Streamable HTTP）与 ChatBox=/sse（http/sse）分节配置步骤
  And 写明 Bearer 与 REST 相同
```

#### 功能 mcp-06 — 工具面扩展

**用户故事**  
As a 使用者，  
I want 批量导入与体系整理也能经 MCP 调用，  
So that 我不必只为这些能力改用另一套协议。

**AC**

```gherkin
Scenario: 随领域故事扩展注册
  Given MVP-3 领域能力 agent-import-* / agent-org-01 已可用
  When 更新 MCP 工具注册与 contracts/mcp-tools.json
  Then 可暴露与 REST 语义一致的 import/org 工具（名称以实现为准）
  And 仍调用同一 KbService
  And 不重写传输 / 鉴权门面（复用 mcp-01/02）

Scenario: 仍无静默入库
  Given MCP 扩展了批确认类工具
  When 检查 schema 与行为
  Then 仍禁止跳过确认直接索引
```

---

### 模块：RAG

#### 功能 rag-index-01 — 确认后分块索引

**用户故事**  
As a 使用者，  
I want 确认后的知识被分块并向量化，  
So that 之后能被语义检索到。

**AC**

```gherkin
Scenario: 确认触发索引成功
  Given 使用者确认了一条含正文的提案
  When 索引流程完成
  Then 正式条目已持久化
  And 对应分块向量已写入向量库
  And 随后检索可命中

Scenario: 索引失败不假装成功
  Given 确认后向量化或写入向量库失败
  When 系统结束该次索引尝试
  Then 调用方收到明确失败
  And 系统不声称已成功写入向量
```

#### 功能 rag-index-02 — 禁止未确认索引

**用户故事**  
As a 产品负责人，  
I want 未确认材料绝不建正式索引，  
So that 写入门禁在存储层也被守住。

**AC**

```gherkin
Scenario: 提案态不写向量
  Given 材料仅处于提案态
  When 检查向量库与正式知识条目
  Then 不存在该材料的正式条目索引
  And 向量库中无将其当作已确认知识的分块
```

#### 功能 rag-retrieve-01 — 混合检索与引用

**用户故事**  
As a 调用方，  
I want 库内混合检索并带回引用，  
So that 宿主 LLM 能 grounded 使用知识。

**AC**

```gherkin
Scenario: 命中带引用
  Given 使用者有已索引知识
  When 发起库内检索且存在相关命中
  Then 返回的命中包含可追溯的条目或分块引用
  And kb 侧默认不代替调用方生成无依据业务长文答案
```

#### 功能 rag-isolate-01 — 检索租户过滤

**用户故事**  
As a 使用者，  
I want 向量检索也按我的身份过滤，  
So that 隔离在检索路径上同样生效。

**AC**

```gherkin
Scenario: 向量命中不含其他用户
  Given 使用者 A 与 B 的知识均已索引
  When 使用者 A 发起检索
  Then 返回命中全部属于使用者 A
  And 不出现使用者 B 的分块
```

#### 功能 rag-store-01 — 原文与元数据存储

**用户故事**  
As a 运维人员，  
I want 原文与元数据落在约定存储且不用 Gist，  
So that 知识自持、可备份、可抽象外置。

**AC**

```gherkin
Scenario: 确认入库后原文可取回
  Given 使用者确认入库一份材料
  When 系统持久化完成
  Then 原文经存储抽象可取回
  And 元数据保存在应用数据库
  And 不使用 GitHub Gist 作为知识主存储
```

---

## 备注

- **MVP 规划表**见上文「MVP 规划（三批闭环）」；闭环细则见 `specs/mvp-2-3-delivery.md`。  
- **模块 MCP**（`mcp-01`…`mcp-06`）：传输 `/mcp`、鉴权、最小工具集、与 REST 契约、Cursor 手测、MVP-3 工具扩展。专文 `specs/mcp-design.md`。  
- **MVP-2**（13）：MCP 门面五条（`mcp-01`…`05`）+ 知识闭环（ingest/km/list/scope + rag-index/retrieve）。  
- **MVP-3**（12）：含 `mcp-06` 工具面扩展 + 批量/org/多管理员/scope-01/02。  
- **MVP-4**（延后，4）：`agent-ingest-02`、`agent-source-01`、`agent-source-02`、`agent-chat-01`。  
- 旧编号 `agent-mcp-01` **已废弃**，由 `mcp-01`…`mcp-05` 取代；跨文档请改引用。  
- 划批改 Backlog「MVP批次」列与规划表；**新增模块行可增功能编号**（`mcp-*`）。  
- **状态**：实现并通过对应 AC / **闭环验收套件**后改为 `Done`（规划表与 Backlog 同步更新）。  
- 部署域名、香港 VPS、tech-stack 等属运行约束，不单独拆功能行；见 `specs/deployment-plan.md` / `specs/architecture.md`。  
- `agent-chat-01` 为可选能力，排在 MVP-4。
