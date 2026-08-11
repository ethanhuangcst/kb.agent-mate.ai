# Web UI Design — kb.agent-mate.ai Admin

管理面视觉与交互规格。实现以本文件为准；静态稿见 `specs/mockup/`。产品行为见 `specs/req.md` / `specs/story-mapping.md`。

**品牌展示名（UI）：** `kb.agent-mate.ai`（顶栏 / 登录 / 首页锁头；勿再用 `kb-agent` 作为可见词标）。  
**主体：** 公网首页 + 私人知识库管理台（签发 Key、管理员邀请/删除）。  
**受众：** 调用方开发者（读接入指南）与受邀管理员。  
**单页任务：** 首页二选一（指南 / 登录）；管理列表页「看清状态 → 点主操作」。

---

## 1. 方向（签名）

**性冷淡操作台：** 浅灰底、纯黑字、零圆角、发丝分割线；主操作是实心黑块，不用彩色强调、不用卡片堆叠、不用胶囊 pill。

签名记忆点：

1. **公网壳（首页 + auth）**：同一灰白氛围底、内容**水平居中且垂直偏上**、大锁头（灯泡 + 站名左对齐）+ 页脚右下版权。  
2. **管理壳**：全宽顶栏左侧品牌、右侧 `Hello, {姓名}`；侧栏仅导航；底栏全站页脚。

刻意不做：奶油底 + 衬线大标题、暗底霓虹强调、报纸多栏密排、侧栏底部 ADMIN 角标、顶栏「会话有效」芯片、公网/登录页死垂直居中。

---

## 2. 色板

| Token | Hex | 用途 |
| --- | --- | --- |
| `--bg` | `#fafafa` | 管理壳页面底 |
| `--bg-elevated` | `#ffffff` | 侧栏 / 顶栏 |
| `--ink` | `#0a0a0a` | 主文字、主按钮底 |
| `--ink-2` | `#1f1f1f` | 次级强调、按钮 hover |
| `--mute` | `#525252` | 说明、导航未选中、页脚 |
| `--mute-soft` | `#6b6b6b` | 更弱提示 |
| `--line` | `#e0e0e0` | 分割线 |
| `--line-strong` | `#bdbdbd` | 输入底边、表头底边 |
| `--fill` | `#f0f0f0` | 代码块等轻底 |

**公网 / auth 氛围底（非第二品牌色）：**

```text
radial-gradient(100% 70% at 50% -20%, #ffffff → transparent)
+ linear-gradient(180deg, #f7f7f7 → #fafafa → #f0f0f0)
```

禁止：紫系渐变、彩色状态点（状态用 mono 大写词 + 墨色/灰色区分即可）。首页与 auth **共用**上列氛围，不引入第二品牌色。

---

## 3. 字体

| 角色 | 字体 | 用法 |
| --- | --- | --- |
| UI / 英文标题 | Outfit 400–600（Google Fonts，与 mockup `@import` 同源） | `h1`、主按钮、logo 词、Hello |
| 中文正文 | Noto Sans SC 400–600 | 正文、表格、表单值 |
| 元数据 | JetBrains Mono | eyebrow、表头、状态、Key 前缀 |

实现：`apps/kb-web` 与 `specs/mockup/styles.css` 共用同一套 `--font-ui` / `--font-cn` / `--font-mono` 与 Google Fonts URL；**不**用 `next/font` 以免子集/度量偏差。

根字号：桌面 `17px`，≤720px `16px`。行高正文约 `1.65`。  
顶栏站名约 `1.2rem`；首页 / auth 锁头站名约 `1.35rem`（≤720px 约 `1.1rem`）。

---

## 4. 布局

### 4.1 公网首页 `index.html`

| 项 | 规格 |
| --- | --- |
| 壳 | `.home-shell` + `.home-main` + `.home-card` |
| 垂直 | `align-items: flex-start`；顶距 `clamp(4.5rem, 14vh, 7.5rem)`（偏上，非死居中） |
| 水平 | 内容块居中；卡内全部左对齐 |
| 锁头 | logo 56×56 + 站名；**黄色灯泡左缘**与说明文左缘光学对齐（射线可伸出；`--logo-optical-shift`，见 ADR-001） |
| 操作 | 「接入指南」文字链 +「管理员登录」`.btn.btn-page` |
| 页脚 | 见 §4.4 |

```text
┌─────────────────────────────────────┐
│                                     │
│     [logo] kb.agent-mate.ai         │  ← 偏上居中
│     一句产品说明                     │
│     ───────────                     │
│     接入指南                         │
│     [管理员登录]                     │
│                                     │
│           copyright ® Ethan Huang   │  ← 页脚右对齐
└─────────────────────────────────────┘
```

### 4.2 Auth 页（登录 / 改密 / 忘记密码 / 接受邀请）

与首页**同一视觉效果**，禁止另起居中或另一套背景。

| 项 | 规格 |
| --- | --- |
| 壳 | `.auth-shell` + `.auth-main` + `.auth-card` |
| 背景 / 顶距 / 水平 | 与 §4.1 相同 |
| 锁头 | `.logo-auth`：规格同首页 `.logo-home`（56px、站名 `1.35rem`、黄泡光学左对齐） |
| 说明 | 「开放注册已关闭。」+ 可交互「联系管理员」+「获得 api-key」；hover / focus 浮层显示微信二维码 `EthanWeChat.png`（零圆角、发丝边、上浮） |
| 密码 | 密码框右侧眼睛图标切换显示/隐藏（`.password-field` / `.password-toggle`） |
| 内容宽 | `max-width: 26rem`（与首页卡同宽） |
| 页脚 | 见 §4.4 |

对应静态稿：`login.html`、`change-password.html`、`forgot-password.html`、`accept-invite.html`。

```text
┌─────────────────────────────────────┐
│                                     │
│     [logo] kb.agent-mate.ai         │  ← 同首页偏上
│     ADMIN / 标题 / 说明              │
│     ───────────                     │
│     表单 · 主按钮 · 辅链             │
│                                     │
│           copyright ® Ethan Huang   │
└─────────────────────────────────────┘
```

### 4.3 管理壳（图2）

```text
┌──────────────────────────────────────────┐
│ [logo] kb.agent-mate.ai    Hello, {Name} │  ← 顶栏撑满
├──────────┬───────────────────────────────┤
│ 使用者   │ content max ~760px            │
│ 管理员   │  page-head | title + CTA      │
│ 退出     │  ───────── hairline ──────    │
│          │  table / form                 │
├──────────┴───────────────────────────────┤
│                 copyright ® Ethan Huang  │  ← 全宽页脚
└──────────────────────────────────────────┘
```

- 顶栏品牌：`.logo-header-mark` 36×36 + 站名；与公网锁头共用 `--logo-optical-shift`（黄泡光学对齐）。
- 侧栏**无** logo、**无** ADMIN 角标；宽度约 `200px`。  
- 顶栏右侧：`Hello, {display_name}`（种子账号可用 `Admin`）。  
- 邀请不占侧栏，从管理员页 CTA 进入。  
- 接入指南：独立静态页 `guide.html`（可新标签打开）。  
- 移动：顶栏保留；侧栏改横排；`active` 用底边线而非左侧条。

### 4.5 接入指南 `guide.html`

| 项 | 规格 |
| --- | --- |
| 壳 | `.guide-shell` + 顶栏品牌 + `.guide-body` + 页脚 |
| 内容宽 | `max-width: 42rem` |
| 章节 | 1 架构 → 2 获取 Key → **3 IDE 接入**（Cursor / CodeBuddy）→ **4 第三方工具**（ChatBox）；顶 TOC 锚点 |
| 架构四段 | 调用者是谁 → 提供什么 → 两种调用方式 → 大模型怎么分工 |
| 结构图 | `.guide-arch-diagram`：MCP / REST 汇合 → Bearer → kb → 私人库；左边 3px 墨线 |
| 双栏 | `.guide-modes`：调用方式（MCP \| REST）；模型分工 |
| 步骤图 | `.guide-steps` / `.guide-step-head`（编号+文案）+ `.guide-figure`（**全宽**，与 `.guide-modes` / `.guide-code` 左右对齐）；`ol.guide-steps` 须 `padding-left: 0`（覆盖 `.guide-body ol`） |
| MCP 接入 | §3：Customize → MCPs → `mcp.json` stdio（模板见 `deployment-plan` §7.1 B）；远程备选 `/mcp`。§4：ChatBox Remote (http/sse) **`/sse`**。见 `mcp-design.md` |
| 资产 | `apps/kb-web/public/guide/*.png`（与 `specs/mockup/guide/` 同步） |
| 文风 | 使用者视角、极简；`.guide-note` 收束要点与路径警告 |

```text
┌─ 顶栏 logo · 返回首页 ──────────────┐
│  Connect / 接入指南 / lead           │
│  TOC: 1 架构 · 2 Key · 3 IDE · 4 工具│
│  谁 → 提供什么 → 结构图+双门面       │
│  你的模型 | 本站内嵌模型             │
│  获取 Key                            │
│  §3 Cursor 步骤 + mcp.json + CodeBuddy│
│  §4 ChatBox 步骤（SSE /sse）         │
│              copyright ® Ethan Huang │
└──────────────────────────────────────┘
```

### 4.4 全站页脚

| 项 | 规格 |
| --- | --- |
| 文案 | `copyright ® Ethan Huang`（字面如此；实现走 i18n key） |
| 对齐 | 右对齐 |
| 样式 | `.site-footer`；字号约 `0.78rem`；色 `--mute`；Outfit |
| 位置 | 壳内最后一子节点（`home-shell` / `auth-shell` / `app-shell` / `guide-shell` / `gallery`） |
| 管理壳 | 顶部分割线 + `--bg-elevated` 底 |

所有 mockup 页均须带此页脚；实现时 Admin / 公网布局同样保留。

---

## 5. 控件 — 按钮（必须统一）

所有实心主按钮共用一套几何，**禁止**按文案长短改变高度或 padding。

### 5.1 Token

| Token | 值 | 说明 |
| --- | --- | --- |
| `--control-h` | `2.75rem`（44px @17） | 主/幽灵按钮固定高度 |
| `--control-px` | `1.25rem` | 左右内边距 |
| `--control-border` | `1.5px` | 边框 |
| `--radius-control` | `0` | 直角 |
| `--btn-font-size` | `0.8125rem` | 主按钮字号 |
| `--btn-tracking` | `0.08em` | 字距（中英混排可读） |

### 5.2 主按钮 `.btn`

| 属性 | 规格 |
| --- | --- |
| 高度 | 固定 `var(--control-h)`（`box-sizing: border-box`） |
| 内边距 | `0 var(--control-px)`（**不要**再用纵向 padding 拉高） |
| 边框 | `1.5px solid var(--ink)` |
| 背景 / 字色 | `var(--ink)` / `#fff` |
| 字重 | `500` |
| 文本变换 | **`none`**（中文界面；勿 `uppercase` 拉长英文字母导致视觉块不一致） |
| 白空 | `white-space: nowrap` |
| 对齐 | `inline-flex` + 水平垂直居中 |
| 最小宽度 | **不**按文案设不同 min-width；页级 CTA 可选统一 `min-width: 10.5rem`，使「签发新 Key」与「邀请管理员」外框一致 |

页级 CTA（`page-head` 右侧）必须：

```html
<a class="btn btn-page" href="...">签发新 Key</a>
<a class="btn btn-page" href="...">邀请管理员</a>
```

`.btn-page`：`min-width: 10.5rem` + 同上高度。两枚按钮在各自列表页应对齐为**同高、同 min-width、同字号、同边框**。

### 5.3 幽灵按钮 `.btn-ghost`

与主按钮**同高、同左右 padding、同字号**；透明底、`border-color: var(--line-strong)`；hover 边框变 `ink`。

### 5.4 文本按钮 `.btn-text`

用于行内「重签 / 吊销 / 删除」：无底无框，字号约 `0.95rem`，**高度不与主按钮对齐**（表格密度优先）。

### 5.5 禁止

- 同一层级混用不同高度的黑底按钮  
- 给个别 CTA 单独 `style="padding:..."`  
- 用 `transform: scale` 或字号差冒充层级  

---

## 6. 表单与表格

- 标签：mono 大写追踪；输入为底边线（无盒）。
- 签发姓名：输入框**上方**提示「仅允许输入英文」；placeholder `Daniel Foster`；前后端校验拉丁字母姓名；输入控件须抑制 macOS Contacts 自动填充干扰（勿用可见 honeypot 假字段）。
- 表头：mono 大写；行操作右对齐文本按钮。
- Key 明文：`.code-block` + 右上角复制图标；`white-space: nowrap` + 横向滚动，禁止断行；签发结果页可提示「请立即复制并安全存放」（**不**再写「仅此一次 / 离开后无法查看」）。
- 查看 Key：列表操作「查看」→ 页眉无「仅此一次」；上方 `.key-meta` 显示姓名；下方同款 `.code-block` 展示可复制明文（mockup：`view-key.html`）。
- 吊销：确认对话框文案「确认吊销该秘钥？」→ Key 立即失效 → 列表只保留有效 Key 行；知识数据仍保留，但使用者无法再访问。

---

## 7. 文案（界面）

- 用户可见字符串走 i18n（见 `web-i18n-01`）；本规格英文仅作设计参考。
- 按钮动词稳定：签发 / 邀请 / 删除 / 吊销 / 重签 / 登录。
- 空态与错误说明下一步，不道歉套话。
- 页脚版权文案见 §4.4（实现时用 key，勿散落硬编码多处）。

---

## 8. 无障碍与动效

- 可见 `:focus-visible` 轮廓（墨色 2px + offset）。
- `prefers-reduced-motion: reduce` 时关闭过渡（含首页 / auth `home-rise`）。
- 主按钮对比度：白字 / 黑底满足正文对比。

---

## 9. 与 mockup / 实现对照

| 产物 | 路径 |
| --- | --- |
| 公网首页 | `specs/mockup/index.html` |
| 登录 / 改密 / 重置 / 邀请落地 | `login.html` · `change-password.html` · `forgot-password.html` · `accept-invite.html` |
| 接入指南 | `specs/mockup/guide.html` |
| 管理壳示例 | `specs/mockup/users.html` · `admins.html` · Key / 邀请表单页 |
| 静态稿目录 | `specs/mockup/gallery.html` |
| 设计 token 落地 | `specs/mockup/styles.css`（`.home-*` / `.auth-*` / `.site-footer` / `.btn-page`） |
| 实现（未来） | Admin Next.js；样式对齐本文件，不另起紫色/圆角体系 |

**验收：**

1. 使用者页「签发新 Key」与管理员页「邀请管理员」桌面宽度下高度差 ≤ 1px，宽度均 ≥ `10.5rem`（推荐 `.btn-page`）。  
2. 首页与登录页同顶距档位、同氛围底、同锁头规格；内容非死垂直居中。  
3. 全部页面有右对齐 `copyright ® Ethan Huang` 页脚。
