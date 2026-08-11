# kb-web（Admin）

Next.js 管理面：登录、强制改密、使用者 Key、i18n、接入指南。

## 本地运行

推荐（durable，可在 Cursor Agent 内执行）：

```bash
make up-daemon
```

仅起依赖 + 自己跑 web：

```bash
make up-deps && make migrate
cd apps/kb-web && npm run dev
```

打开 [http://127.0.0.1:3000](http://127.0.0.1:3000)（与 `localhost` 勿混用 Cookie）。  
停应用：`make down-apps`；连同依赖：`make down`。  
若进程常被停：见 `specs/knowledge/ops/local-apps-keep-dying.md`。

种子账号：`admin` / `admin`（须强制改密）。若 E2E 改过密，可 `POST /api/admin/test/reset-seed`（非生产）。

环境变量从仓库根 `.env` 加载（见 `next.config.ts` + `specs/keys.md`）。Postgres 本地常为 `127.0.0.1:5434`。  
Key 查看需 `API_KEY_ENCRYPTION_SECRET`（或本地回退 pepper，见 ADR-007）。

## 测试

```bash
npm test          # vitest
npm run test:e2e  # Playwright（需 Postgres + ENABLE_TEST_RESET）
```

## 文档

- UI：`specs/web-ui-design.md`、`specs/mockup/`（含 `guide/` 截图）
- 接入指南页：`/guide`（§3 IDE Cursor/CodeBuddy；§4 ChatBox SSE）
- 故事与批次：`specs/story-mapping.md`（含 web-keys-05 查看 Key）
- MVP-2/3 闭环：`specs/mvp-2-3-delivery.md`
- MCP 接入：`specs/mcp-design.md`（Cursor `/mcp` 或 stdio；ChatBox `/sse`）
- 内容概述：`specs/knowledge-summary.md`（`kb_knowledge_summary`，≤400 字）
- 规格索引：`specs/README.md`
