# 本地开发栈：Postgres、进程与种子管理员

## Postgres

本地 Compose 常把 Postgres 映到主机 **5434**（避免与本机 5432 冲突）。`DATABASE_URL` 必须指向同一实例；连错空库会出现「无管理员 / 无 Key」类假故障。

## 起停进程

在 Cursor Agent 会话里直接挂起的 `npm` / `uvicorn` 可能被回收。优先：

- `make up-daemon`：持久拉起依赖与应用  
- 停应用：`make down-apps`；连同依赖：`make down`  
- 迁移：`make migrate`

详细背景见仓库 ADR「durable local up-daemon」。

## 种子管理员

空库种子：用户名 `admin`、初始密码 `admin`、默认联系邮箱常为 `me@ethanhuang.com`（可用 `BOOTSTRAP_ADMIN_EMAIL` 覆盖）。首次登录须强制改密后才能签发 Key / 邀请。

E2E 或脏数据可用测试重置接口（非生产、需开关）回到种子态。

## 环境变量习惯

根目录 `.env`；Web 与 agent 共用 pepper / 库连接。Key 查看另需 `API_KEY_ENCRYPTION_SECRET`（可空则本地回退 pepper）。勿把生产密钥提交进 Git。
