# Web UI Design — kb.agent-mate.ai Admin

管理面视觉与交互规格。实现以本文件为准；静态稿见 `specs/mockup/`。产品行为见 `specs/req.md` / `specs/story-mapping.md`。

**品牌展示名（UI）：** `kb.agent-mate.ai`（侧栏 / 登录锁头文案；勿再用 `kb-agent` 作为可见词标）。  
**主体：** 私人知识库管理台（签发 Key、管理员邀请/删除）。  
**受众：** 受邀管理员。  
**单页任务：** 列表页一眼完成「看清状态 → 点主操作」；表单页完成一项写操作。

---

## 1. 方向（签名）

**性冷淡操作台：** 浅灰底、纯黑字、零圆角、发丝分割线；主操作是实心黑块，不用彩色强调、不用卡片堆叠、不用胶囊 pill。

签名记忆点：页眉下沿一条分割线，右侧一枚**等高、等内边距**的黑底主按钮（页级 CTA）。

刻意不做：奶油底 + 衬线大标题、暗底霓虹强调、报纸多栏密排。

---

## 2. 色板

| Token | Hex | 用途 |
| --- | --- | --- |
| `--bg` | `#fafafa` | 页面底 |
| `--bg-elevated` | `#ffffff` | 侧栏 / 顶栏 |
| `--ink` | `#0a0a0a` | 主文字、主按钮底 |
| `--ink-2` | `#1f1f1f` | 次级强调、按钮 hover |
| `--mute` | `#525252` | 说明、导航未选中 |
| `--mute-soft` | `#6b6b6b` | 更弱提示 |
| `--line` | `#e0e0e0` | 分割线 |
| `--line-strong` | `#bdbdbd` | 输入底边、表头底边 |
| `--fill` | `#f0f0f0` | 代码块等轻底 |

禁止：紫系渐变、彩色状态点（状态用 mono 大写词 + 墨色/灰色区分即可）。

---

## 3. 字体

| 角色 | 字体 | 用法 |
| --- | --- | --- |
| UI / 英文标题 | Outfit 400–600 | `h1`、主按钮、logo 词 |
| 中文正文 | Noto Sans SC 400–600 | 正文、表格、表单值 |
| 元数据 | JetBrains Mono | eyebrow、crumb、表头、状态、Key 前缀 |

根字号：桌面 `17px`，≤720px `16px`。行高正文约 `1.65`。

---

## 4. 布局

```text
┌──────────┬─────────────────────────────┐
│ sidebar  │ topbar (crumb · chip)       │
│ ~248px   ├─────────────────────────────┤
│ 词标     │ content max ~760px          │
│ 使用者   │  page-head | title + CTA    │
│ 管理员   │  ───────── hairline ──────  │
│ 退出     │  table / form               │
└──────────┴─────────────────────────────┘
```

- 可见品牌词标：**`kb.agent-mate.ai`**（灯泡图标 + 词标；技术服务名 `kb-agent` 仅用于容器/栈，不出现在 UI 词标）。
- 侧栏三项：**使用者 · 管理员 · 退出**（邀请不占侧栏，从管理员页 CTA 进入）。
- `page-head`：左文案、右**唯一**页级主按钮；`align-items: flex-end`；底部分割线。
- 移动：侧栏改顶栏横排；主按钮可折行到标题下方，仍用同一尺寸规格。

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
- 表头：mono 大写；行操作右对齐文本按钮。
- Key 明文：`.code-block` + 右上角复制图标；警告句用 `--mute`。

---

## 7. 文案（界面）

- 用户可见字符串走 i18n（见 `web-i18n-01`）；本规格英文仅作设计参考。
- 按钮动词稳定：签发 / 邀请 / 删除 / 吊销 / 重签 / 登录。
- 空态与错误说明下一步，不道歉套话。

---

## 8. 无障碍与动效

- 可见 `:focus-visible` 轮廓（墨色 2px + offset）。
- `prefers-reduced-motion: reduce` 时关闭过渡。
- 主按钮对比度：白字 / 黑底满足正文对比。

---

## 9. 与 mockup / 实现对照

| 产物 | 路径 |
| --- | --- |
| 静态稿 + CSS | `specs/mockup/` |
| 设计 token 落地 | `specs/mockup/styles.css` 的 `:root` 与 `.btn` / `.btn-page` |
| 实现（未来） | Admin Next.js；样式对齐本文件，不另起一套紫色/圆角体系 |

**验收（本缺陷）：** 使用者页「签发新 Key」与管理员页「邀请管理员」在桌面宽度下测量，高度差 ≤ 1px，宽度均 ≥ `10.5rem`（或同为内容撑开但高度与 padding 完全一致）。推荐采用 `.btn-page` 同高同 min-width。
