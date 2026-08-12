# 生产发布后健康检查（kb.agent-mate.ai）

## 适用

每次 Portainer 更新镜像或 recreate 容器之后，在浏览器冒烟之外做一次快速确认。

## 必查

1. **首页** `https://kb.agent-mate.ai/` 能打开，无假验证码弹层。  
2. **CSP**：响应头含 `content-security-policy`，且 `script-src` 带 `nonce-` 与 `strict-dynamic`。  
3. **无注入串**：页面 HTML 不含 `data:text/javascript;base64`。  
4. **Agent 健康**：`https://kb.agent-mate.ai/healthz` → `{"status":"ok"}`。  
5. **MCP 路由**：未带 Key 时 `/mcp` 或 `/sse` 应为鉴权失败（如 401），而不是整站 502。

## 502 而首页 200

多半是 Nginx Proxy Manager 上游未指向新容器：对该域名的 Proxy Host **再保存一次**（可不改字段），然后重测 `/healthz`。

## 镜像约定

- 生产只用 GHCR 上**真实存在**的 tag（如 `v0.1.3`），不要用分支名当 `IMAGE_TAG`。  
- 更新后确认 Portainer 中 `kb-web` / `kb-agent` / `kb-rag` 镜像 tag 一致。

## 客户端

- Cursor / CodeBuddy：`https://kb.agent-mate.ai/mcp`  
- ChatBox：`https://kb.agent-mate.ai/sse`  
- 单 `Authorization: Bearer <key>`；客户端不配 Tavily Key。
