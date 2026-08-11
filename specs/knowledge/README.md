# Knowledge Base（仓库备忘）

可复用的研究结论、运维教训、领域笔记（**不是**代码真源）。  
产品需求 / 设计规格：[`specs/README.md`](../README.md)。架构决策：[`specs/adr/`](../adr/)。

## 产品知识库入库

面向 `kb_propose_add` 的**整理正文**在：

**[`for-kb/`](./for-kb/)** — 6 篇可直接提案确认；说明见该目录 README。

工程碎片笔记仍放在下方主题目录，供开发检索；已合并进 `for-kb` 的条目不必再单独灌库。

---

## 索引（仓库备忘）

### 可入库主题（已导出到 for-kb）

| 备忘原文 | for-kb | 主题 |
| --- | --- | --- |
| [ops/chatbox-mcp-sse.md](ops/chatbox-mcp-sse.md)、[ops/mcp-stdio-auth.md](ops/mcp-stdio-auth.md) | [01](for-kb/01-mcp-clients.md) | MCP 客户端接入 |
| [security/api-key-ciphertext.md](security/api-key-ciphertext.md) | [02](for-kb/02-api-key-storage-and-view.md) | Key 密文 / 查看 / 吊销 |
| [ops/local-postgres-5434.md](ops/local-postgres-5434.md)、[ops/local-apps-keep-dying.md](ops/local-apps-keep-dying.md)、[ops/seed-admin-email.md](ops/seed-admin-email.md) | [03](for-kb/03-local-dev-stack.md) | 本地开发栈 |
| [frontend/macos-contacts-autofill.md](frontend/macos-contacts-autofill.md)、[frontend/noncontact-input-e2e.md](frontend/noncontact-input-e2e.md) | [04](for-kb/04-admin-forms-autofill.md) | 签发表单与 Contacts |
| [frontend/guide-figure-full-bleed.md](frontend/guide-figure-full-bleed.md) | [05](for-kb/05-guide-layout-figures.md) | 指南截图全宽 |
| [design/logo-optical-alignment.md](design/logo-optical-alignment.md) | [06](for-kb/06-logo-optical-align.md) | Logo 光学对齐 |

### 仅仓库（不建议入库）

| Doc | Topic | Updated |
| --- | --- | --- |
| [ops/adr-numbering.md](ops/adr-numbering.md) | 新建 ADR 前取最大编号；避免撞号 | 2026-08-11 |
| [ops/mcp-mount-trailing-slash.md](ops/mcp-mount-trailing-slash.md) | 裸 `/mcp` 404；须改写为 `/mcp/` | 2026-08-11 |
| [ops/mvp2-true-stack.md](ops/mvp2-true-stack.md) | MVP-2 真栈旅程（含本机密钥操作提示，宜留仓库） | 2026-08-11 |
| [ops/content-overview.md](ops/content-overview.md) | 内容概述字段与工具约定（规格向，见 `knowledge-summary.md`） | 2026-08-11 |

### 全量主题目录（按路径）

| Doc | Topic | Updated |
|-----|--------|---------|
| [design/logo-optical-alignment.md](design/logo-optical-alignment.md) | Logo 黄泡光学对齐与资产几何 | 2026-08-11 |
| [frontend/macos-contacts-autofill.md](frontend/macos-contacts-autofill.md) | macOS Contacts；禁止可见 honeypot | 2026-08-11 |
| [frontend/noncontact-input-e2e.md](frontend/noncontact-input-e2e.md) | NonContactTextInput：click 再 fill | 2026-08-11 |
| [frontend/guide-figure-full-bleed.md](frontend/guide-figure-full-bleed.md) | 指南截图与 code 同宽（ol padding） | 2026-08-11 |
| [ops/mvp2-true-stack.md](ops/mvp2-true-stack.md) | MVP-2 真栈旅程 | 2026-08-11 |
| [ops/chatbox-mcp-sse.md](ops/chatbox-mcp-sse.md) | ChatBox → `/sse` | 2026-08-11 |
| [ops/mcp-stdio-auth.md](ops/mcp-stdio-auth.md) | stdio：`KB_API_KEY` ≠ pepper | 2026-08-11 |
| [ops/mcp-mount-trailing-slash.md](ops/mcp-mount-trailing-slash.md) | 裸 `/mcp` → 改写 `/mcp/`（Starlette Mount） | 2026-08-11 |
| [ops/local-apps-keep-dying.md](ops/local-apps-keep-dying.md) | Agent 回收进程 → `up-daemon` | 2026-08-11 |
| [ops/content-overview.md](ops/content-overview.md) | 概述 ≤400 字 | 2026-08-11 |
| [ops/local-postgres-5434.md](ops/local-postgres-5434.md) | 本地 Postgres `:5434` | 2026-08-11 |
| [ops/seed-admin-email.md](ops/seed-admin-email.md) | 种子邮箱默认 | 2026-08-11 |
| [ops/adr-numbering.md](ops/adr-numbering.md) | ADR 编号防撞 | 2026-08-11 |
| [security/api-key-ciphertext.md](security/api-key-ciphertext.md) | Key 密文 + 查看（ADR-007） | 2026-08-11 |
| [for-kb/](for-kb/) | **产品库入库正文包** | 2026-08-11 |
