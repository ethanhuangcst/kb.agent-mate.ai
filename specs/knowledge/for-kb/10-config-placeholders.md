# 客户端配置示例用占位符，勿写死主机

接入指南、部署说明、`mcp.json` 等 **可复制模板** 里，不要写死 `127.0.0.1`、具体端口或生产域名。用尖括号占位符，由读者换成实际值。

## 常用占位符

| 占位符 | 含义 |
| --- | --- |
| `<REPO>` | 本机仓库根目录 |
| `<HOST>` / `<AGENT_PORT>` | Agent 地址（`/mcp`、`/sse`） |
| `<PUBLIC_HOST>` | 公网 TLS 主机名 |
| `<PG_HOST>` / `<PG_PORT>` | stdio 用的 Postgres |
| `<RAG_HOST>` / `<RAG_PORT>` | stdio 用的 RAG |
| `<password>`、Key / pepper 类 | 密钥，勿提交到 Git |

## 例外

运行时默认值、本地/生产对照表、Playwright `baseURL`、Compose 端口表等 **说明真实栈** 的文档可以写具体地址；与「给人粘贴的配置模板」分开。

远程 Cursor：`http://<HOST>:<AGENT_PORT>/mcp` 或 `https://<PUBLIC_HOST>/mcp`。ChatBox：对应路径用 `/sse`，不要填 `/mcp`。
