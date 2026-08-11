# MCP 客户端接入：Cursor、CodeBuddy、ChatBox

一把使用者 API Key，多客户端共用同一知识库。传输与 URL 不同，填错会 404。  
**客户端不配置 `TAVILY_API_KEY`**（外部搜索由 kb-agent 服务端提供，见 ADR-018）。

## 获取 Key

管理员在管理台签发英文姓名使用者 Key。签发结果页与列表「查看」均可复制完整明文（库内另存可解密密文；鉴权仍用哈希）。请求头形态：`Authorization: Bearer <api_key>`。吊销后立即失效；重签换密钥、知识库保留。

## IDE（Cursor / CodeBuddy）— 推荐远程

### 远程 Streamable HTTP（产品默认）

- Transport：Streamable HTTP / Remote MCP  
- URL：本地 `http://<HOST>:<AGENT_PORT>/mcp`；生产 `https://<PUBLIC_HOST>/mcp`  
- 鉴权：`Authorization: Bearer <api_key>`  
- 不要填 ChatBox 的 `/sse`。  
- 不要填写 `TAVILY_API_KEY`。

示例：

```json
{
  "mcpServers": {
    "kb-agent": {
      "url": "https://<PUBLIC_HOST>/mcp",
      "headers": {
        "Authorization": "Bearer <paste_plaintext_user_api_key>"
      }
    }
  }
}
```

### 可选：本地 stdio（贡献者）

路径概要：Cursor Settings → Customize → MCPs → New MCP Server → 编辑 `mcp.json`。

要点：

- `command` / `args`：`python -m app.mcp_stdio`（venv 路径与 `cwd` 指向 kb-agent）。
- `KB_API_KEY`：管理台签发的使用者 Key 明文（不要加 `Bearer `）。
- `API_KEY_PEPPER`：必须与签发时 agent/管理台 `.env` 中的 pepper **逐字相同**；**绝不要**把 `kb_live_…` 填进 pepper。
- `DATABASE_URL` 等须指向持有该 Key 的同一库（本地 Postgres 常见端口 5434）。
- **不要**在客户端模板加 `TAVILY_API_KEY`；需要 `kb_external_search` 时改用远程 MCP。

CodeBuddy：优先 Remote MCP；stdio 字段与上表可选模板相同。

## ChatBox（第三方）

- Type：Remote (http/sse)，不是 Local stdio。  
- URL：本地 `http://<HOST>:<AGENT_PORT>/sse`；生产 `https://<PUBLIC_HOST>/sse`。  
- HTTP Header：`Authorization=Bearer <api_key>`。  
- Test 通过后再 Save，并在会话中启用 MCP。  
- **不要填 `/mcp`**：ChatBox 会对 URL 发 SSE GET，`/mcp` 会 404。  
- **不要**配置 Tavily。

## 连通自检

`kb_list_knowledge` → `kb_internal_search` →（可选）propose / confirm → `kb_external_search`。

## 对照表

| 客户端 | 传输 | 路径 | 客户端是否配 Tavily |
| --- | --- | --- | --- |
| Cursor / CodeBuddy **远程（推荐）** | Streamable HTTP | `/mcp` | 否 |
| Cursor 本地 stdio（可选） | stdio + mcp.json | 本机进程 | 否（外部搜索请用远程） |
| ChatBox | SSE | `/sse` | 否 |
