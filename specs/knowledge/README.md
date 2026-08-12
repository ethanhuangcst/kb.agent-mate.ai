# Knowledge Base（仓库备忘）

可复用的研究结论、运维教训、领域笔记（**不是**代码真源）。  
产品需求 / 设计规格：[`specs/README.md`](../README.md)。架构决策：[`specs/adr/`](../adr/)。

## 产品知识库入库

面向 `kb_propose_add` 的**整理正文**在：

**[`for-kb/`](./for-kb/)** — 整理正文可直接提案确认；说明见该目录 README。

工程碎片笔记仍放在下方主题目录，供开发检索；已合并进 `for-kb` 的条目不必再单独灌库。

---

## 索引（仓库备忘）

### 可入库主题（已导出到 for-kb）

| 备忘原文 | for-kb | 主题 |
| --- | --- | --- |
| [ops/chatbox-mcp-sse.md](ops/chatbox-mcp-sse.md)、[ops/mcp-stdio-auth.md](ops/mcp-stdio-auth.md)、[ops/tavily-key-placement.md](ops/tavily-key-placement.md) | [01](for-kb/01-mcp-clients.md) | MCP 客户端接入；Tavily 仅服务端 |
| [security/api-key-ciphertext.md](security/api-key-ciphertext.md) | [02](for-kb/02-api-key-storage-and-view.md) | Key 密文 / 查看 / 吊销 |
| [ops/local-postgres-5434.md](ops/local-postgres-5434.md)、[ops/local-apps-keep-dying.md](ops/local-apps-keep-dying.md)、[ops/seed-admin-email.md](ops/seed-admin-email.md) | [03](for-kb/03-local-dev-stack.md) | 本地开发栈 |
| [ops/safari-localhost-email-links.md](ops/safari-localhost-email-links.md) | [07](for-kb/07-safari-email-localhost.md) | 重置/邀请邮件与 Safari |
| [frontend/admin-username-vs-display-name.md](frontend/admin-username-vs-display-name.md) | [08](for-kb/08-admin-username.md) | 邀请用户名 |
| [frontend/locale-switcher-header.md](frontend/locale-switcher-header.md) | [09](for-kb/09-locale-switcher.md) | 语言切换 |
| [ops/config-snippet-placeholders.md](ops/config-snippet-placeholders.md) | [10](for-kb/10-config-placeholders.md) | 配置占位符 |
| — | [11](for-kb/11-product-positioning.md) | 产品定位 |
| [ops/content-overview.md](ops/content-overview.md) | [12](for-kb/12-content-overview.md) | 内容概述 ≤400 |
| [ops/mcp-mount-trailing-slash.md](ops/mcp-mount-trailing-slash.md) | [13](for-kb/13-mcp-bare-path.md) | 裸 `/mcp` 改写 |
| [security/clickfix-html-inject-2026-08-12.md](security/clickfix-html-inject-2026-08-12.md)、[security/csp-and-next-cve.md](security/csp-and-next-cve.md) | [14](for-kb/14-security-clickfix-and-csp.md) | ClickFix / CSP / Next CVE |
| [ops/prod-yecaoyun3.md](ops/prod-yecaoyun3.md) | [15](for-kb/15-prod-release-health-checks.md) | 生产发版健康检查 |
| [frontend/macos-contacts-autofill.md](frontend/macos-contacts-autofill.md)、[frontend/noncontact-input-e2e.md](frontend/noncontact-input-e2e.md) | [04](for-kb/04-admin-forms-autofill.md) | 签发与登录：Contacts / NonContactTextInput |
| [frontend/guide-figure-full-bleed.md](frontend/guide-figure-full-bleed.md) | [05](for-kb/05-guide-layout-figures.md) | 指南截图全宽 |
| [design/logo-optical-alignment.md](design/logo-optical-alignment.md) | [06](for-kb/06-logo-optical-align.md) | Logo 光学对齐 |

### 仅仓库（不建议入库）

| Doc | Topic | Updated |
| --- | --- | --- |
| [ops/adr-numbering.md](ops/adr-numbering.md) | 新建 ADR 前取最大编号；避免撞号 | 2026-08-11 |
| [ops/outbound-fetch-ssrf-quota.md](ops/outbound-fetch-ssrf-quota.md) | fetch SSRF、RPM 配额、Chat 开关 | 2026-08-11 |
| [ops/mvp2-true-stack.md](ops/mvp2-true-stack.md) | MVP-2 真栈旅程（含本机密钥操作提示，宜留仓库） | 2026-08-11 |
| [ops/admin-resend-mail.md](ops/admin-resend-mail.md) | 邀请/重置邮件：Resend vs EMAIL_TRANSPORT=log | 2026-08-11 |

### 全量主题目录（按路径）

| Doc | Topic | Updated |
|-----|--------|---------|
| [design/logo-optical-alignment.md](design/logo-optical-alignment.md) | Logo 黄泡光学对齐与资产几何 | 2026-08-11 |
| [frontend/macos-contacts-autofill.md](frontend/macos-contacts-autofill.md) | macOS Contacts；登录+签发；禁止可见 honeypot | 2026-08-12 |
| [frontend/home-cta-width-stretch.md](frontend/home-cta-width-stretch.md) | 首页 CTA：`width:100%`+max-content 塌宽 | 2026-08-12 |
| [frontend/noncontact-input-e2e.md](frontend/noncontact-input-e2e.md) | NonContactTextInput：click 再 fill | 2026-08-11 |
| [frontend/guide-figure-full-bleed.md](frontend/guide-figure-full-bleed.md) | 指南截图与 code 同宽（ol padding） | 2026-08-11 |
| [frontend/locale-switcher-header.md](frontend/locale-switcher-header.md) | 语言切换：顶栏灰色链，非墨盒 | 2026-08-11 |
| [frontend/admin-username-vs-display-name.md](frontend/admin-username-vs-display-name.md) | 邀请须用户名；UI 不用「登录名」（ADR-014） | 2026-08-11 |
| [ops/mvp2-true-stack.md](ops/mvp2-true-stack.md) | MVP-2 真栈旅程 | 2026-08-11 |
| [ops/chatbox-mcp-sse.md](ops/chatbox-mcp-sse.md) | ChatBox → `/sse`；SSE 勿用 BaseHTTPMiddleware（ADR-017） | 2026-08-11 |
| [ops/mcp-stdio-auth.md](ops/mcp-stdio-auth.md) | stdio：`KB_API_KEY` ≠ pepper | 2026-08-11 |
| [ops/tavily-key-placement.md](ops/tavily-key-placement.md) | `TAVILY_API_KEY` 仅服务端；客户端不配（ADR-018） | 2026-08-11 |
| [ops/mcp-mount-trailing-slash.md](ops/mcp-mount-trailing-slash.md) | 裸 `/mcp` → 改写 `/mcp/`（Starlette Mount） | 2026-08-11 |
| [ops/local-apps-keep-dying.md](ops/local-apps-keep-dying.md) | Agent 回收进程 → `up-daemon` | 2026-08-11 |
| [ops/content-overview.md](ops/content-overview.md) | 概述 ≤400 字 | 2026-08-11 |
| [ops/local-postgres-5434.md](ops/local-postgres-5434.md) | 本地 Postgres `:5434` | 2026-08-11 |
| [ops/seed-admin-email.md](ops/seed-admin-email.md) | 种子邮箱默认 | 2026-08-11 |
| [ops/adr-numbering.md](ops/adr-numbering.md) | ADR 编号防撞（含双 012 → 013） | 2026-08-11 |
| [ops/admin-resend-mail.md](ops/admin-resend-mail.md) | Admin 邮件 Resend / log transport | 2026-08-11 |
| [ops/safari-localhost-email-links.md](ops/safari-localhost-email-links.md) | Safari + `127.0.0.1` 邮件链接（ADR-012） | 2026-08-11 |
| [ops/config-snippet-placeholders.md](ops/config-snippet-placeholders.md) | 配置示例占位符约定 | 2026-08-11 |
| [ops/prod-yecaoyun3.md](ops/prod-yecaoyun3.md) | 野草云3 生产交接：`v0.1.3`、端口、Aliyun `kb_agent` | 2026-08-12 |
| [security/api-key-ciphertext.md](security/api-key-ciphertext.md) | Key 密文 + 查看（ADR-007） | 2026-08-11 |
| [security/clickfix-html-inject-2026-08-12.md](security/clickfix-html-inject-2026-08-12.md) | 2026-08-12 ClickFix 事故（工程备忘） | 2026-08-12 |
| [security/csp-and-next-cve.md](security/csp-and-next-cve.md) | nonce CSP + Next CVE-2025-66478 运维 | 2026-08-12 |
| [for-kb/](for-kb/) | **产品库入库正文包**（含 14–15 安全/发版检查） | 2026-08-12 |
