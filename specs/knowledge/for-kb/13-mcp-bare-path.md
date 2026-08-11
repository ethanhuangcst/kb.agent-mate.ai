# MCP 路径：裸 `/mcp` 须能通（勿只认 `/mcp/`）

Streamable HTTP 的挂载在部分框架下只会匹配 `/mcp/...`，对 **恰好** `/mcp`（无尾斜杠）的 POST 会 404。Cursor 等客户端常配置 `…/mcp`（无尾斜杠）。

## 正确行为

服务端在鉴权中间件里把路径 `/mcp` 改写为 `/mcp/` 再交给路由。客户端配置可继续写：

- 本地：`http://<HOST>:<AGENT_PORT>/mcp`
- 生产：`https://<PUBLIC_HOST>/mcp`

## 自检

- 对 `/mcp` 与 `/mcp/` 的初始化/POST 均应 200（需有效 Bearer）。
- ChatBox 仍用 `/sse`，不要把本条与 SSE 路径混淆。

若出现 `{"detail":"Not Found"}` 且 URL 正好是 `/mcp`，先查是否缺少上述改写。
