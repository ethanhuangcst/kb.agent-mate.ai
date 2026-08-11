import Image from "next/image";
import Link from "next/link";
import { getLocale, getTranslations } from "next-intl/server";
import { BrandLockup, SiteFooter } from "../site-chrome";

const MCP_JSON_SNIPPET = `{
  "mcpServers": {
    "kb-agent": {
      "command": "<REPO>/.venv/bin/python",
      "args": ["-m", "app.mcp_stdio"],
      "cwd": "<REPO>/services/kb-agent",
      "env": {
        "KB_API_KEY": "<paste_plaintext_user_api_key>",
        "API_KEY_PEPPER": "<same_as_agent_and_admin_dotenv>",
        "DATABASE_URL": "postgresql+psycopg://kb:<password>@127.0.0.1:5434/kb_agent",
        "RAG_BASE_URL": "http://127.0.0.1:8001",
        "RAG_SERVICE_TOKEN": "<same_as_dotenv>",
        "BLOB_ROOT": "<REPO>/data/blob",
        "PYTHONPATH": "<REPO>/services/kb-agent"
      }
    }
  }
}`;

const copy = {
  "zh-CN": {
    tocArch: "1. 架构",
    tocKey: "2. 获取 Key",
    tocIde: "3. IDE 接入",
    tocTools: "4. 第三方工具",
    archTitle: "1. 架构指南",
    who: "调用者是谁",
    whoItems: [
      ["IDE", "如 Cursor、CodeBuddy 里的 Agent / 项目会话"],
      ["聊天客户端", "如 ChatBox"],
      ["自有应用", "如 HCP Engagement Assistant"],
    ],
    whoNote: "以上都须自带大模型（或由宿主接入 LLM），用来理解意图、做业务判断、消费检索结果。",
    services: "kb.agent-mate.ai 提供什么",
    serviceItems: [
      "管理你在各项目中沉淀的知识（一人一库，按 user 隔离）",
      "按输入检索已有知识，返回可引用片段",
      "按需从外部找候选材料；你确认后才入库",
      "归纳整理知识体系（分类、标签、项目归属）",
    ],
    modes: "两种调用方式",
    mcpDesc:
      "远程 MCP 工具面（检索、提案、确认、列表、内容概述 ≤400 字）。IDE 与第三方客户端传输不同，见第 3–4 节。",
    modesNote:
      "MCP 与 REST 共用一把 Key、同一知识库；请求体里的用户标识不能覆盖 Key 身份。",
    llm: "大模型怎么分工",
    yourModel: "你自带的模型",
    yourItems: [
      "理解意图与任务目标",
      "决定要不要外部补给、如何解读命中",
      "按业务逻辑筛选、组合知识",
      "产出洞察、策略、文案等下游结果",
    ],
    ourModel: "本站内嵌模型",
    ourItems: [
      "库内检索、列表、体系整理辅助",
      "外部候选检索与正文拉取",
      "入库提案：≤400 字内容概述、分类建议、查重",
      "确认后的持久化与向量化",
    ],
    llmNoteBefore: "本站帮你",
    llmNoteStrong1: "找到并管好知识",
    llmNoteMid: "，不替你",
    llmNoteStrong2: "做完生意",
    llmNoteAfter: "。要投放策略或业务结论，须由你侧模型结合业务数据完成；外部材料须确认后才入库。",
    keyTitle: "2. 获取 API Key",
    keyIntro: "管理员在管理台签发使用者 Key；列表可再次「查看」完整明文。MCP 与 REST 使用同一把 Key。",
    keyRevoke: "吊销立即失效；重签换密钥，知识库保留。",
    ideTitle: "3. IDE 接入",
    ideLead: "以 Cursor 与 CodeBuddy 为例。本地推荐 stdio（mcp.json）；也可使用远程 Streamable HTTP。",
    ideCursor: "Cursor",
    ideSteps: [
      {
        title: "打开 Cursor Settings",
        body: "菜单 Cursor → Preferences → Cursor Settings（或 ⌘,）。",
        img: "/guide/cursor-01-settings.png",
        alt: "Cursor 菜单打开 Preferences → Cursor Settings",
      },
      {
        title: "进入 Customize",
        body: "左侧栏选择 Customize（Plugins、MCPs、Skills 已迁至此）。",
        img: "/guide/cursor-02-customize.png",
        alt: "Cursor Settings 左侧栏高亮 Customize",
      },
      {
        title: "MCPs → New MCP Server",
        body: "筛选 MCPs，点击 New MCP Server / Add a Custom MCP Server。",
        img: "/guide/cursor-03-new-mcp.png",
        alt: "Customize 中 MCPs 分类与 New MCP Server",
      },
      {
        title: "按模板填写 mcp.json",
        body: "在打开的 mcp.json 中配置 kb-agent（stdio）。KB_API_KEY 填使用者 Key 明文；API_KEY_PEPPER 须与签发环境一致。",
        img: "/guide/cursor-04-mcp-json.png",
        alt: "mcp.json 中 kb-agent stdio 与 env 示例",
      },
    ],
    ideJsonCaption: "mcp.json 模板（占位符换成你本机路径与密钥；勿提交到 Git）",
    ideRemote:
      "远程备选：Transport = Streamable HTTP，URL 本地 http://127.0.0.1:8000/mcp，生产 https://kb.agent-mate.ai/mcp，鉴权 Authorization: Bearer <api_key>。不要填 /sse。",
    ideCodeBuddy:
      "CodeBuddy：在 MCP / 插件设置中新增服务器，字段与上表相同——本地可用同类 mcp.json（command / args / cwd / env），或 Remote MCP 指向 /mcp。",
    toolsTitle: "4. 第三方工具接入",
    toolsLead: "以 ChatBox 为例。须使用 Remote (http/sse) 与 /sse 路径，不能填 /mcp。",
    chatboxSteps: [
      {
        title: "Settings → MCP",
        body: "打开 ChatBox 设置，左侧选择 MCP。",
        img: "/guide/chatbox-01-mcp-settings.png",
        alt: "ChatBox MCP Settings，侧栏 MCP 与 Add Server",
      },
      {
        title: "Add Custom Server",
        body: "Custom MCP Servers → Add Server → 选择 Add Custom Server。",
        img: "/guide/chatbox-02-add-custom.png",
        alt: "ChatBox 选择 Add Custom Server",
      },
      {
        title: "填写服务器（注意 SSE）",
        body: "Type = Remote (http/sse)。URL 本地 http://127.0.0.1:8000/sse，生产 https://kb.agent-mate.ai/sse。HTTP Header：Authorization=Bearer <api_key>。",
        img: "/guide/chatbox-03-server-form.png",
        alt: "ChatBox Add MCP Server 表单，Type 为 Remote http/sse，URL 以 /sse 结尾",
      },
    ],
    chatboxSave: "点 Test，通过后再 Save；在会话中启用该 MCP。",
    chatboxWarn: "不要填 /mcp。ChatBox 会对 URL 发 SSE GET，/mcp 会报 404。",
    connectCheck: "连通后可试：kb_list_knowledge → kb_internal_search →（可选）propose / confirm。",
    diagramAria: "调用方经 MCP 或 REST，用同一把 Bearer Key 进入 kb.agent-mate.ai，再访问按用户隔离的私人知识库",
  },
  en: {
    tocArch: "1. Architecture",
    tocKey: "2. Get a key",
    tocIde: "3. IDE setup",
    tocTools: "4. Third-party tools",
    archTitle: "1. Architecture",
    who: "Who calls",
    whoItems: [
      ["IDE", "e.g. Cursor / CodeBuddy Agent or project chat"],
      ["Chat clients", "e.g. ChatBox"],
      ["Your apps", "e.g. HCP Engagement Assistant"],
    ],
    whoNote: "Callers bring their own LLM (or host-provided) for intent, judgment, and consuming hits.",
    services: "What kb.agent-mate.ai provides",
    serviceItems: [
      "Manage knowledge per project (one library per user)",
      "Search confirmed knowledge; return citable snippets",
      "Optional external candidates; index only after confirm",
      "Organize taxonomy (types, tags, projects)",
    ],
    modes: "Two call paths",
    mcpDesc:
      "Remote MCP tools (search, propose, confirm, list, ≤400-char overview). IDE vs third-party transports differ — see §§3–4.",
    modesNote: "MCP and REST share one key and one library; body user ids cannot override Bearer identity.",
    llm: "LLM split",
    yourModel: "Your model",
    yourItems: [
      "Understand intent and goals",
      "Decide external fetch and interpret hits",
      "Filter and compose knowledge for the task",
      "Produce insights, strategy, copy, and other outcomes",
    ],
    ourModel: "Platform model",
    ourItems: [
      "In-library search, lists, taxonomy helpers",
      "External candidate search and body fetch",
      "Propose: ≤400-char content overview, type hints, dedupe",
      "Persist and embed after confirm",
    ],
    llmNoteBefore: "We help you ",
    llmNoteStrong1: "find and manage knowledge",
    llmNoteMid: ", not ",
    llmNoteStrong2: "run the business for you",
    llmNoteAfter: ". Strategy and conclusions stay on your side; external material indexes only after confirm.",
    keyTitle: "2. Get an API key",
    keyIntro:
      "Ask an admin to issue a user key; the list View action can show the full plaintext again. MCP and REST use the same key.",
    keyRevoke: "Revoke fails immediately; reissue rotates the secret, library kept.",
    ideTitle: "3. IDE setup",
    ideLead:
      "Examples: Cursor and CodeBuddy. Prefer local stdio (mcp.json); Streamable HTTP is the remote alternative.",
    ideCursor: "Cursor",
    ideSteps: [
      {
        title: "Open Cursor Settings",
        body: "Cursor → Preferences → Cursor Settings (or ⌘,).",
        img: "/guide/cursor-01-settings.png",
        alt: "Cursor menu Preferences → Cursor Settings",
      },
      {
        title: "Open Customize",
        body: "In the sidebar, choose Customize (Plugins, MCPs, and Skills live here).",
        img: "/guide/cursor-02-customize.png",
        alt: "Cursor Settings sidebar with Customize highlighted",
      },
      {
        title: "MCPs → New MCP Server",
        body: "Filter MCPs, then New MCP Server / Add a Custom MCP Server.",
        img: "/guide/cursor-03-new-mcp.png",
        alt: "Customize MCPs chip and New MCP Server control",
      },
      {
        title: "Fill mcp.json from the template",
        body: "Configure kb-agent (stdio). KB_API_KEY is the user key plaintext; API_KEY_PEPPER must match the issuing environment.",
        img: "/guide/cursor-04-mcp-json.png",
        alt: "mcp.json kb-agent stdio and env example",
      },
    ],
    ideJsonCaption: "mcp.json template (replace placeholders; never commit secrets)",
    ideRemote:
      "Remote alternative: Transport = Streamable HTTP; URL local http://127.0.0.1:8000/mcp, prod https://kb.agent-mate.ai/mcp; Auth Authorization: Bearer <api_key>. Do not use /sse.",
    ideCodeBuddy:
      "CodeBuddy: add a server in MCP / plugin settings with the same fields — local mcp.json (command / args / cwd / env) or Remote MCP to /mcp.",
    toolsTitle: "4. Third-party tools",
    toolsLead: "Example: ChatBox. Use Remote (http/sse) and the /sse path — not /mcp.",
    chatboxSteps: [
      {
        title: "Settings → MCP",
        body: "Open ChatBox settings and select MCP in the sidebar.",
        img: "/guide/chatbox-01-mcp-settings.png",
        alt: "ChatBox MCP Settings with sidebar MCP and Add Server",
      },
      {
        title: "Add Custom Server",
        body: "Custom MCP Servers → Add Server → Add Custom Server.",
        img: "/guide/chatbox-02-add-custom.png",
        alt: "ChatBox Add Custom Server option",
      },
      {
        title: "Fill the server form (SSE)",
        body: "Type = Remote (http/sse). URL local http://127.0.0.1:8000/sse, prod https://kb.agent-mate.ai/sse. HTTP Header: Authorization=Bearer <api_key>.",
        img: "/guide/chatbox-03-server-form.png",
        alt: "ChatBox Add MCP Server form with Remote http/sse and /sse URL",
      },
    ],
    chatboxSave: "Click Test, then Save when it passes; enable the MCP in the chat session.",
    chatboxWarn: "Do not use /mcp. ChatBox SSE-GETs the URL; /mcp returns 404.",
    connectCheck: "Smoke: kb_list_knowledge → kb_internal_search → (optional) propose / confirm.",
    diagramAria: "Callers use MCP or REST with the same Bearer key into kb.agent-mate.ai, then a user-isolated library",
  },
} as const;

type Step = (typeof copy)["zh-CN"]["ideSteps"][number];

function GuideStep({ step, index }: { step: Step; index: number }) {
  return (
    <li className="guide-step">
      <div className="guide-step-head">
        <p className="guide-step-index">{String(index + 1).padStart(2, "0")}</p>
        <div className="guide-step-copy">
          <h3 className="guide-step-title">{step.title}</h3>
          <p>{step.body}</p>
        </div>
      </div>
      <figure className="guide-figure">
        <Image
          src={step.img}
          alt={step.alt}
          width={1200}
          height={750}
          className="guide-figure-img"
          sizes="(max-width: 720px) 100vw, 42rem"
          style={{ width: "100%", height: "auto" }}
        />
        <figcaption>{step.alt}</figcaption>
      </figure>
    </li>
  );
}

export default async function GuidePage() {
  const t = await getTranslations("guide");
  const locale = await getLocale();
  const c = copy[locale === "en" ? "en" : "zh-CN"];

  return (
    <div className="guide-shell">
      <header className="guide-header">
        <BrandLockup size="header" href="/" />
        <Link className="btn-text" href="/">
          {t("back")}
        </Link>
      </header>

      <article className="guide-body">
        <p className="eyebrow">{t("eyebrow")}</p>
        <h1>{t("title")}</h1>
        <p className="lead">{t("lead")}</p>

        <nav className="guide-toc" aria-label="toc">
          <a href="#architecture">{c.tocArch}</a>
          <a href="#key">{c.tocKey}</a>
          <a href="#ide">{c.tocIde}</a>
          <a href="#tools">{c.tocTools}</a>
        </nav>

        <section id="architecture" className="guide-section">
          <h2>{c.archTitle}</h2>

          <h3 id="who" className="guide-sub">
            {c.who}
          </h3>
          <ul className="guide-list">
            {c.whoItems.map(([k, v]) => (
              <li key={k}>
                <strong>{k}</strong> — {v}
              </li>
            ))}
          </ul>
          <p className="guide-note">{c.whoNote}</p>

          <h3 id="services" className="guide-sub">
            {c.services}
          </h3>
          <ul className="guide-list">
            {c.serviceItems.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>

          <h3 id="modes" className="guide-sub">
            {c.modes}
          </h3>
          <figure className="guide-arch" aria-label="architecture">
            <pre className="guide-arch-diagram" role="img" aria-label={c.diagramAria}>
              <span className="arch-muted">IDE / ChatBox</span>
              {"          "}
              <span className="arch-muted">HCP / App</span>
              {"\n      │ "}
              <span className="arch-accent">MCP</span>
              {"                     │ "}
              <span className="arch-accent">REST</span>
              {"\n      └───────────┬───────────────┘\n                  │ "}
              <span className="arch-accent">Bearer API Key</span>
              {"\n                  ▼\n         "}
              <span className="arch-box">kb.agent-mate.ai</span>
              {"\n         search · propose · confirm\n                  │\n                  ▼\n         "}
              <span className="arch-box">{locale === "en" ? "Private KB" : "私人知识库"}</span>
              {"  "}
              <span className="arch-muted">user isolate</span>
            </pre>
          </figure>
          <div className="guide-modes">
            <div className="guide-mode">
              <p className="guide-mode-label">MCP</p>
              <p className="guide-mode-who">IDE · ChatBox</p>
              <p>{c.mcpDesc}</p>
            </div>
            <div className="guide-mode">
              <p className="guide-mode-label">REST</p>
              <p className="guide-mode-who">HCP · App</p>
              <p>
                HTTP <span className="mono">/api/v1/kb/*</span>
                {locale === "en" ? "; same semantics as MCP." : "；与 MCP 同一套能力语义。"}
              </p>
            </div>
          </div>
          <p className="guide-note">{c.modesNote}</p>

          <h3 id="llm-boundary" className="guide-sub">
            {c.llm}
          </h3>
          <div className="guide-modes guide-roles">
            <div className="guide-mode">
              <p className="guide-mode-label">{c.yourModel}</p>
              <ul>
                {c.yourItems.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
            <div className="guide-mode">
              <p className="guide-mode-label">{c.ourModel}</p>
              <ul>
                {c.ourItems.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
          </div>
          <p className="guide-note">
            {c.llmNoteBefore}
            <strong>{c.llmNoteStrong1}</strong>
            {c.llmNoteMid}
            <strong>{c.llmNoteStrong2}</strong>
            {c.llmNoteAfter}
          </p>
        </section>

        <section id="key" className="guide-section">
          <h2>{c.keyTitle}</h2>
          <p>{c.keyIntro}</p>
          <p>
            {locale === "en" ? "Header: " : "请求头："}
            <span className="mono">Authorization: Bearer &lt;api_key&gt;</span>
          </p>
          <p className="guide-note">{c.keyRevoke}</p>
        </section>

        <section id="ide" className="guide-section">
          <h2>{c.ideTitle}</h2>
          <p className="guide-note">{c.ideLead}</p>
          <h3 className="guide-sub">{c.ideCursor}</h3>
          <ol className="guide-steps">
            {c.ideSteps.map((step, i) => (
              <GuideStep key={step.img} step={step} index={i} />
            ))}
          </ol>
          <p className="guide-code-label">{c.ideJsonCaption}</p>
          <pre className="guide-code">
            <code>{MCP_JSON_SNIPPET}</code>
          </pre>
          <p className="guide-note">{c.ideRemote}</p>
          <p className="guide-note">{c.ideCodeBuddy}</p>
          <p className="guide-note">{c.connectCheck}</p>
        </section>

        <section id="tools" className="guide-section">
          <h2>{c.toolsTitle}</h2>
          <p className="guide-note">{c.toolsLead}</p>
          <ol className="guide-steps">
            {c.chatboxSteps.map((step, i) => (
              <GuideStep key={step.img} step={step} index={i} />
            ))}
          </ol>
          <p>{c.chatboxSave}</p>
          <p className="guide-note">{c.chatboxWarn}</p>
          <p className="guide-note">{c.connectCheck}</p>
        </section>
      </article>

      <SiteFooter />
    </div>
  );
}
