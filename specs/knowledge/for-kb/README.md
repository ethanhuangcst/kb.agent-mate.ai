# 可入库知识包（for-kb）

本目录是 **准备写入产品知识库**（`kb_propose_add` → confirm）的正文，与仓库工程备忘 `specs/knowledge/{design,frontend,ops,security}/` 分离。

## 怎么用

1. 管理台签发使用者 Key；Cursor/ChatBox 接好 MCP。  
2. 对下列文件：`kb_propose_add`（title = 文内一级标题；text = 全文）。  
3. 确认后可用 `kb_internal_search` 检索；概述 ≤400 字由 propose 生成，过短可用 `kb_knowledge_summary(..., refresh=true)`。  
4. **不要**把 ADR 原文或含密钥的截图/配置当正文入库。

## 本包清单（建议入库）

| 文件 | 主题 | 适用谁 |
| --- | --- | --- |
| [01-mcp-clients.md](./01-mcp-clients.md) | Cursor / CodeBuddy / ChatBox 接入与路径差异 | 调用方、运维 |
| [02-api-key-storage-and-view.md](./02-api-key-storage-and-view.md) | Key 哈希+密文、查看、吊销按用户 | 管理员、安全 |
| [03-local-dev-stack.md](./03-local-dev-stack.md) | 本地 Postgres、daemon、种子账号 | 开发 |
| [04-admin-forms-autofill.md](./04-admin-forms-autofill.md) | macOS Contacts 与签发表单 | 前端 |
| [05-guide-layout-figures.md](./05-guide-layout-figures.md) | 接入指南截图全宽对齐 | 前端 |
| [06-logo-optical-align.md](./06-logo-optical-align.md) | Logo 黄泡光学对齐 | 设计/前端 |

## 不入库（留在仓库 knowledge/）

| 原因 | 示例 |
| --- | --- |
| 纯流程/编号约定 | `ops/adr-numbering.md` |
| 已与上表合并 | `ops/chatbox-mcp-sse.md`、`ops/mcp-stdio-auth.md` 等 → 见 01/02/03 |
| 决策原文 | `specs/adr/*`（检索决策用 ADR，不重复灌库） |
