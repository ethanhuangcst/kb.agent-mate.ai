# 客户端配置：生产域名写实值；密钥用占位符

产品 MCP / ChatBox 模板**只**使用正式域名（勿写本机地址）：

- Cursor：`https://kb.agent-mate.ai/mcp`
- ChatBox：`https://kb.agent-mate.ai/sse`

密钥类字段仍用尖括号占位符，勿提交真实密钥。

## 常用占位符（密钥）

| 占位符 | 含义 |
| --- | --- |
| `<paste_plaintext_user_api_key>` / `<api_key>` | 管理台签发的使用者 Key |
| 其他密钥类 | 勿提交到 Git |

ChatBox 路径必须是 `/sse`，不要填 `/mcp`。
