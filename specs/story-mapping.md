# Story Mapping — kb-agent

来源：`specs/req.md`（辅以 `specs/architecture.md` 能力边界）。  
ATDD：用户故事 + Gherkin AC；实现前可据此写失败验收测试。

模块约定：**Web** = Admin 管理面；**Agent** = MCP / REST / 越界与补给编排；**RAG** = 确认后索引与库内检索。

---

## 第一部分：Product Backlog

| 序号 | 模块 | 功能编号 | 功能名称 | 说明 | MVP批次 | 状态 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Web | web-acct-01 | 初始化默认管理员 | 无管理员时种子账号 `admin`/`admin`；关闭开放注册 | MVP-1 | ToDo |
| 2 | Web | web-acct-02 | 管理员登录 / 登出 | 用户名或邮箱+密码会话；Cookie | MVP-1 | ToDo |
| 3 | Web | web-acct-03 | 忘记密码 / 重置 | Resend 短时一次性链接设新密 | MVP-3 | ToDo |
| 4 | Web | web-acct-04 | 邀请管理员（R2） | 已登录且已改密管理员邀请邮箱 → 对方设密成为管理员 | MVP-3 | ToDo |
| 5 | Web | web-acct-05 | 接受邀请设密 | 邀请链接落地；设英文姓名 + 密码后可登录 | MVP-3 | ToDo |
| 6 | Web | web-acct-06 | 种子账号强制改密 | 仅默认 `admin`/`admin`（`must_change_password`）；邀请/重置设密不走此门禁 | MVP-1 | ToDo |
| 7 | Web | web-acct-07 | 管理员列表 | 查看管理员（用户名/邮箱、状态、创建时间） | MVP-3 | ToDo |
| 8 | Web | web-acct-08 | 删除管理员 | 删除其他管理员；禁止删自己、禁止删光最后一名 | MVP-3 | ToDo |
| 9 | Web | web-keys-01 | 使用者列表 | 管理台查看已签发使用者（姓名、Key 前缀、状态） | MVP-1 | ToDo |
| 10 | Web | web-keys-02 | 签发 API Key | 填姓名；明文仅显示一次；一人一把有效 Key | MVP-1 | ToDo |
| 11 | Web | web-keys-03 | 吊销 API Key | 立即失效；知识数据保留 | MVP-1 | ToDo |
| 12 | Web | web-keys-04 | 重签 API Key | 吊销旧 Key、发新 Key；同一使用者与库；不改姓名 | MVP-1 | ToDo |
| 13 | Web | web-i18n-01 | 管理面文案 i18n | 用户可见文案走 i18n（默认 `zh-CN`，可扩展 `en`） | MVP-1 | ToDo |
| 14 | Agent | agent-auth-01 | Bearer 鉴权 | MCP/REST 统一 `Authorization: Bearer`；解析 `user_id` | MVP-1 | ToDo |
| 15 | Agent | agent-auth-02 | 身份不可覆盖 | 请求体中的用户标识不能覆盖 Key 身份 | MVP-1 | ToDo |
| 16 | Agent | agent-auth-03 | 租户隔离 | 各使用者数据强制隔离；默认无跨用户共享 | MVP-1 | ToDo |
| 17 | Agent | agent-auth-04 | 一人一库一 Key | 同一 Key 可用于 Cursor / ChatBox / HCP；不按调用方拆 Key | MVP-1 | ToDo |
| 18 | Agent | agent-search-01 | 库内检索 | 按输入检索已有知识；返回可引用片段 / 结构化命中 | MVP-1 | ToDo |
| 19 | Agent | agent-list-01 | 知识列表 | 按项目 / 标签等过滤列出知识条目 | MVP-3 | ToDo |
| 20 | Agent | agent-org-01 | 体系整理 | 归纳分类、标签、项目归属（重大变更可走确认） | MVP-3 | ToDo |
| 21 | Agent | agent-ingest-01 | 粘贴 / 单文件提案 | 材料 → 提案（摘要、分类、查重）；确认前不入库 | MVP-2 | ToDo |
| 22 | Agent | agent-ingest-02 | URL 拉取提案 | 指定 URL 拉取正文后进入提案 | MVP-4 | ToDo |
| 23 | Agent | agent-ingest-03 | 确认单条入库 | 显式 confirm 后持久化并触发索引 | MVP-2 | ToDo |
| 24 | Agent | agent-import-01 | 批量文档上传 | 多文件 → ImportBatch + 每文件提案；禁止静默进库 | MVP-3 | ToDo |
| 25 | Agent | agent-import-02 | 批次逐条 / 一键确认 | 逐条 confirm 或一键确认全部有效提案 | MVP-3 | ToDo |
| 26 | Agent | agent-import-03 | 批量格式与限额 | `.md` / `.txt` / 可抽文本 PDF；大小与个数上限；失败不阻塞同批 | MVP-3 | ToDo |
| 27 | Agent | agent-source-01 | 外部搜索候选 | 源路由搜索；返回候选列表；不自动落库 | MVP-4 | ToDo |
| 28 | Agent | agent-source-02 | 库内优先补给 | 优先库内；不足或显式要求时才外部 | MVP-4 | ToDo |
| 29 | Agent | agent-scope-01 | 拒绝业务策略越界 | 拒绝代劳投放策略 / 业务结论；可降级为公开资料候选 | MVP-2 | ToDo |
| 30 | Agent | agent-scope-02 | 拒绝开放式决策 | 只给证据与来源；不给「该怎么做」的最终决策 | MVP-2 | ToDo |
| 31 | Agent | agent-scope-03 | 拒绝无确认自动入库 | 拒绝「网上相关都自动进库」 | MVP-2 | ToDo |
| 32 | Agent | agent-scope-04 | 拒绝伪造库内引用 | 库内无据时明确不足；禁止捏造引用 | MVP-2 | ToDo |
| 33 | Agent | agent-mcp-01 | MCP 一等接入 | Cursor / ChatBox 自定义 MCP；工具与领域层一致 | MVP-3 | ToDo |
| 34 | Agent | agent-rest-01 | 知识 REST | 与 MCP 工具语义对齐的结构化 API（HCP 等） | MVP-1 | ToDo |
| 35 | Agent | agent-chat-01 | 可选 OpenAI 兼容门面 | 薄封装同一工具集；同等越界规则；非业务中台 | MVP-4 | ToDo |
| 36 | Agent | agent-km-01 | 内部 Qwen 仅 KM | 归类 / 摘要提案 / 去重辅助；不做调用方业务洞察 | MVP-2 | ToDo |
| 37 | RAG | rag-index-01 | 确认后分块索引 | confirm 后分块、向量化、写入向量库 | MVP-2 | ToDo |
| 38 | RAG | rag-index-02 | 禁止未确认索引 | 提案态不写向量、不建正式条目 | MVP-1 | ToDo |
| 39 | RAG | rag-retrieve-01 | 混合检索与引用 | 库内混合检索；命中带可引用 chunk / item | MVP-2 | ToDo |
| 40 | RAG | rag-isolate-01 | 检索租户过滤 | 向量与元数据查询强制 `user_id` | MVP-1 | ToDo |
| 41 | RAG | rag-store-01 | 原文与元数据存储 | 原文 Blob + PostgreSQL 元数据；排除 Gist | MVP-1 | ToDo |

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
  And 不展示完整 Key 明文
```

#### 功能 web-keys-02 — 签发 API Key

**用户故事**  
As an 管理员，  
I want 为使用者填写姓名并签发一把 API Key，  
So that 该使用者能用同一把 Key 访问全局知识库。

**AC**

```gherkin
Scenario: 签发成功且明文仅一次可见
  Given 管理员已登录
  When 管理员填写使用者姓名并签发 Key
  Then 系统创建该使用者与一把有效 Key
  And 完整 Key 明文仅在本次数展示
  And 之后列表仅可见前缀等信息

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
Scenario: 吊销后知识面立即拒绝
  Given 使用者持有有效 Key
  And 管理员已登录
  When 管理员吊销该 Key
  Then 使用原 Key 的知识面请求被拒绝
  And 该使用者知识数据仍保留
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
  And 新 Key 明文展示一次
  And 使用者姓名不变
  And 用新 Key 仍可检索到原有知识
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

#### 功能 agent-mcp-01 — MCP 一等接入

**用户故事**  
As a Cursor / ChatBox 用户，  
I want 通过自定义 MCP 调用知识工具，  
So that 宿主模型能管知识而不被 kb-agent 取代。

**AC**

```gherkin
Scenario: MCP 工具与领域能力一致
  Given 使用者配置了有效 Key 的远程 MCP
  When 宿主通过 MCP 调用检索或提案类工具
  Then 行为与对应知识领域能力一致
  And 越界请求同样被拒绝
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
  Then 结果语义与 MCP 对应工具一致
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

- **MVP 批次（已确认）**
  - **MVP-1**（17）：可登录、可发 Key、可鉴权空检索 — 地基  
  - **MVP-2**（9）：单条提案→确认→可引用检索 + 越界 + KM  
  - **MVP-3**（11）：MCP + 批量导入 + 列表/整理 + 多管理员  
  - **MVP-4**（4）：外部补给 + URL 拉取 + 可选薄 Chat 门面  
- 划批只改 Backlog「MVP批次」列，不改功能编号。  
- **状态**：实现并通过对应 AC / 自动化后改为 `Done`。  
- 部署域名、香港 VPS、tech-stack 等属运行约束，不单独拆功能行；见 `specs/deployment-plan.md` / `specs/architecture.md`。  
- `agent-chat-01` 为可选能力，排在 MVP-4。
