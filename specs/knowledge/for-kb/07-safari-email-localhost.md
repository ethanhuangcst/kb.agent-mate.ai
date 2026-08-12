# 重置/邀请邮件链接：用 localhost，勿用 127.0.0.1

管理台发出的密码重置、管理员邀请邮件，链接基址来自 `PUBLIC_BASE_URL`（`publicAppBaseUrl()`）。本地与生产必须分开配置。

## 现象（本地 + Safari）

邮件 HTML 里写的是 `http://127.0.0.1:3000/reset-password?...`（或 accept-invite），在 Safari 中点开却变成 `https://127.0.0.1`（无端口），无法连接。

## 原因

Safari 的 HTTPS-First / HTTPS 升级对 **`127.0.0.1`** 与 **`localhost`** 待遇不同：可能把 HTTP 升成 HTTPS，并丢掉非默认端口（如 `:3000`）。这不是 Resend 改写正文；用 API 查到的邮件 HTML 往往仍带正确端口。

## 正确配置

| 环境 | `PUBLIC_BASE_URL` / `NEXT_PUBLIC_APP_URL` |
| --- | --- |
| 本地 | `http://localhost:3000`（不要写 `127.0.0.1`） |
| 生产 | `https://kb.agent-mate.ai`（禁止 loopback；须 HTTPS） |

代码侧：`publicAppBaseUrl()` 会把 `127.0.0.1` 改写为 `localhost` 并保留端口；生产若仍是 loopback 或非 HTTPS，发送邮件时会报错，避免发出错误链接。

邮件链接优先读 **`PUBLIC_BASE_URL`**（服务端权威），不要只依赖可能过期的 `NEXT_PUBLIC_APP_URL`。

## 自检

1. Resend 控制台或 `EMAIL_TRANSPORT=log`：链接以 `http://localhost:3000/`（本地）或 `https://kb.agent-mate.ai/`（生产）开头。  
2. Safari 打开后应进入重置/接受邀请页，而不是「无法连接服务器」。  
3. 生产 compose / Portainer 同时写入 `PUBLIC_BASE_URL` 与 `NEXT_PUBLIC_APP_URL`，二者同域。
