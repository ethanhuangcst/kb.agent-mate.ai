# MCP 客户端接入：Cursor、CodeBuddy、ChatBox

一把使用者 API Key，多客户端共用同一知识库。传输与 URL 不同，填错会 404。  
**产品接入一律走远端 `https://kb.agent-mate.ai`**（勿配本机地址）。  
**客户端不配置 `TAVILY_API_KEY`**（外部搜索由 kb-agent 服务端提供，见 ADR-018）。

## 获取 Key

管理员在管理台签发英文姓名使用者 Key。签发结果页与列表「查看」均可复制完整明文（库内另存可解密密文；鉴权仍用哈希）。请求头形态：`Authorization: Bearer <api_key>`。吊销后立即失效；重签换密钥、知识库保留。

## IDE（Cursor / CodeBuddy）

- Transport：Streamable HTTP / Remote MCP  
- URL：**`https://kb.agent-mate.ai/mcp`**  
- 鉴权：`Authorization: Bearer <api_key>`  
- 不要填 ChatBox 的 `/sse`。  
- 不要填写 `TAVILY_API_KEY`。  
- 不要使用本机地址。

示例：

```json
{
  "mcpServers": {
    "kb-agent": {
      "url": "https://kb.agent-mate.ai/mcp",
      "headers": {
        "Authorization": "Bearer <paste_plaintext_user_api_key>"
      }
    }
  }
}
```

CodeBuddy：字段与上表相同。

## ChatBox（第三方）

- Type：Remote (http/sse)，不是 Local stdio。  
- URL：**`https://kb.agent-mate.ai/sse`**。  
- HTTP Header：`Authorization=Bearer <api_key>`。  
- Test 通过后再 Save，并在会话中启用 MCP。  
- **不要填 `/mcp`**：ChatBox 会对 URL 发 SSE GET，`/mcp` 会 404。  
- **不要**配置 Tavily。  
- **不要**使用本机地址。

## 连通自检

`kb_list_knowledge` → `kb_internal_search` →（可选）propose / confirm → `kb_external_search`。

## 对照表

| 客户端 | 传输 | URL | 客户端是否配 Tavily |
| --- | --- | --- | --- |
| Cursor / CodeBuddy | Streamable HTTP | `https://kb.agent-mate.ai/mcp` | 否 |
| ChatBox | SSE | `https://kb.agent-mate.ai/sse` | 否 |
