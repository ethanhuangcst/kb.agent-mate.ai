# kb-web（Admin）

Next.js 管理面：登录、强制改密、使用者 Key、i18n、接入指南。

## 本地运行

根目录先起依赖并迁移：

```bash
make up-deps && make migrate
cd apps/kb-web && npm run dev
```

打开 [http://127.0.0.1:3000](http://127.0.0.1:3000)（与 `localhost` 勿混用 Cookie）。

种子账号：`admin` / `admin`（须强制改密）。若 E2E 改过密，可 `POST /api/admin/test/reset-seed`（非生产）。

环境变量从仓库根 `.env` 加载（见 `next.config.ts` + `specs/keys.md`）。Postgres 本地常为 `127.0.0.1:5434`。

## 测试

```bash
npm test          # vitest
npm run test:e2e  # Playwright（需 Postgres + ENABLE_TEST_RESET）
```

## 文档

- UI：`specs/web-ui-design.md`、`specs/mockup/`
- 故事与批次：`specs/story-mapping.md`
- MVP-2/3 闭环：`specs/mvp-2-3-delivery.md`
