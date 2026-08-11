import Image from "next/image";
import Link from "next/link";
import { getLocale, getTranslations } from "next-intl/server";
import { BrandLockup, SiteFooter } from "../site-chrome";
import { LocaleSwitcher } from "../locale-switcher";

/** Product path: remote Streamable HTTP — no Tavily on the client (ADR-018). */
const MCP_REMOTE_SNIPPET = `{
  "mcpServers": {
    "kb-agent": {
      "url": "https://<PUBLIC_HOST>/mcp",
      "headers": {
        "Authorization": "Bearer <paste_plaintext_user_api_key>"
      }
    }
  }
}`;

/** Optional contributor path: local stdio. No TAVILY_API_KEY — use remote for external search. */
const MCP_STDIO_SNIPPET = `{
  "mcpServers": {
    "kb-agent": {
      "command": "<REPO>/.venv/bin/python",
      "args": ["-m", "app.mcp_stdio"],
      "cwd": "<REPO>/services/kb-agent",
      "env": {
        "KB_API_KEY": "<paste_plaintext_user_api_key>",
        "API_KEY_PEPPER": "<same_as_agent_and_admin_dotenv>",
        "DATABASE_URL": "postgresql+psycopg://kb:<password>@<PG_HOST>:<PG_PORT>/kb_agent",
        "RAG_BASE_URL": "http://<RAG_HOST>:<RAG_PORT>",
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
      ["自有应用", "如 MyPoke.Trade"],
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
      "远程 MCP 工具面（检索、提案、确认、列表、内容概述 ≤400 字、外部候选）。IDE 与第三方客户端传输不同，见第 3–4 节。",
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
    tavilyTitle: "外部搜索（Tavily）",
    tavilyBody:
      "kb_external_search 所需的 TAVILY_API_KEY 只配在 kb-agent 服务端（生产由本站运维）。IDE、ChatBox 等客户端一律不配置、不申请 Tavily；只需使用者 API Key。",
    tavilyNote: "请用远程 MCP（§3）或 ChatBox SSE（§4）接入，即可使用库内与外部工具。",
    keyTitle: "2. 获取 API Key",
    keyIntro: "管理员在管理台签发使用者 Key；列表可再次「查看」完整明文。MCP 与 REST 使用同一把 Key。",
    keyRevoke: "吊销立即失效；重签换密钥，知识库保留。",
    ideTitle: "3. IDE 接入",
    ideLead:
      "推荐远程 Streamable HTTP（与生产一致，无需任何 Tavily）。以 Cursor 为例；CodeBuddy 字段相同。",
    ideCursor: "Cursor · 远程（推荐）",
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
        body: "筛选 MCPs，点击 New MCP Server / Add a Custom MCP Server，打开 mcp.json。",
        img: "/guide/cursor-03-new-mcp.png",
        alt: "Customize 中 MCPs 分类与 New MCP Server",
      },
      {
        title: "填写远程 URL 与 Bearer",
        body: "用下方远程模板：url 指向 /mcp（本地或生产），headers 里 Authorization: Bearer <使用者 Key>。不要填 /sse，不要加 TAVILY_API_KEY。",
        img: "/guide/cursor-04-mcp-json.png",
        alt: "mcp.json 编辑界面（远程配置用 url + headers）",
      },
    ],
    ideRemoteCaption:
      "远程 mcp.json 模板（将 <PUBLIC_HOST> 换成实际主机；本地可用 http://<HOST>:<AGENT_PORT>/mcp）",
    ideLocalTitle: "可选：本地 stdio（贡献者 / 本机全栈）",
    ideLocalLead:
      "仅在本机已拉起 Postgres / RAG、需要不经 HTTP 调试时使用。客户端仍不配 Tavily；外部搜索请改用上方远程，或由运维在 kb-agent .env 配置后走远程。",
    ideLocalCaption: "stdio 模板（勿提交密钥；无 TAVILY_API_KEY）",
    ideCodeBuddy:
      "CodeBuddy：优先 Remote MCP → /mcp + Bearer；本地 stdio 字段与上表可选模板相同。",
    toolsTitle: "4. 第三方工具接入",
    toolsLead: "以 ChatBox 为例。须使用 Remote (http/sse) 与 /sse 路径，不能填 /mcp。同样不配置 Tavily。",
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
        body: "Type = Remote (http/sse)。URL 本地 http://<HOST>:<AGENT_PORT>/sse，生产 https://<PUBLIC_HOST>/sse。HTTP Header：Authorization=Bearer <api_key>。",
        img: "/guide/chatbox-03-server-form.png",
        alt: "ChatBox Add MCP Server 表单，Type 为 Remote http/sse，URL 以 /sse 结尾",
      },
    ],
    chatboxSave: "点 Test，通过后再 Save；在会话中启用该 MCP。",
    chatboxWarn: "不要填 /mcp。ChatBox 会对 URL 发 SSE GET，/mcp 会报 404。",
    chatboxTavily: "只需 Bearer 使用者 Key；Tavily 由 kb-agent 服务端提供。",
    connectCheck:
      "连通后可试：kb_list_knowledge → kb_internal_search →（可选）propose / confirm → kb_external_search。",
    diagramAria: "调用方经 MCP 或 REST，用同一把 Bearer Key 进入 kb.agent-mate.ai，再访问按用户隔离的私人知识库",
    flowMcpClients: "IDE · ChatBox",
    flowRestClients: "MyPoke.Trade",
    flowAuth: "Bearer API Key",
    flowHub: "kb.agent-mate.ai",
    flowHubOps: "检索 · 提案 · 确认入库",
    flowStore: "私人知识库",
    flowIsolate: "user 隔离",
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
      ["Your apps", "e.g. MyPoke.Trade"],
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
      "Remote MCP tools (search, propose, confirm, list, ≤400-char overview, external candidates). IDE vs third-party transports differ — see §§3–4.",
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
    tavilyTitle: "External search (Tavily)",
    tavilyBody:
      "TAVILY_API_KEY for kb_external_search lives only on the kb-agent server (production ops). IDE, ChatBox, and other clients never configure or apply for Tavily — only the user API Key.",
    tavilyNote: "Use remote MCP (§3) or ChatBox SSE (§4) for in-library and external tools.",
    keyTitle: "2. Get an API key",
    keyIntro:
      "Ask an admin to issue a user key; the list View action can show the full plaintext again. MCP and REST use the same key.",
    keyRevoke: "Revoke fails immediately; reissue rotates the secret, library kept.",
    ideTitle: "3. IDE setup",
    ideLead:
      "Prefer remote Streamable HTTP (production path; no Tavily on the client). Cursor example; CodeBuddy uses the same fields.",
    ideCursor: "Cursor · remote (recommended)",
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
        body: "Filter MCPs, then New MCP Server / Add a Custom MCP Server to open mcp.json.",
        img: "/guide/cursor-03-new-mcp.png",
        alt: "Customize MCPs chip and New MCP Server control",
      },
      {
        title: "Set remote URL and Bearer",
        body: "Use the remote template below: url ends with /mcp (local or prod); headers Authorization: Bearer <user key>. Do not use /sse. Do not add TAVILY_API_KEY.",
        img: "/guide/cursor-04-mcp-json.png",
        alt: "mcp.json editor (remote uses url + headers)",
      },
    ],
    ideRemoteCaption:
      "Remote mcp.json template (replace <PUBLIC_HOST>; local may use http://<HOST>:<AGENT_PORT>/mcp)",
    ideLocalTitle: "Optional: local stdio (contributors / full local stack)",
    ideLocalLead:
      "Only when Postgres/RAG are local and you need non-HTTP debugging. Still no Tavily in the client; use remote above for external search, or point remote at an agent whose .env already has the key.",
    ideLocalCaption: "stdio template (never commit secrets; no TAVILY_API_KEY)",
    ideCodeBuddy:
      "CodeBuddy: prefer Remote MCP → /mcp + Bearer; optional local stdio matches the secondary template.",
    toolsTitle: "4. Third-party tools",
    toolsLead: "Example: ChatBox. Use Remote (http/sse) and /sse — not /mcp. No Tavily on the client.",
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
        body: "Type = Remote (http/sse). URL local http://<HOST>:<AGENT_PORT>/sse, prod https://<PUBLIC_HOST>/sse. HTTP Header: Authorization=Bearer <api_key>.",
        img: "/guide/chatbox-03-server-form.png",
        alt: "ChatBox Add MCP Server form with Remote http/sse and /sse URL",
      },
    ],
    chatboxSave: "Click Test, then Save when it passes; enable the MCP in the chat session.",
    chatboxWarn: "Do not use /mcp. ChatBox SSE-GETs the URL; /mcp returns 404.",
    chatboxTavily: "Bearer user key only; Tavily is provided by the kb-agent host.",
    connectCheck:
      "Smoke: kb_list_knowledge → kb_internal_search → (optional) propose / confirm → kb_external_search.",
    diagramAria: "Callers use MCP or REST with the same Bearer key into kb.agent-mate.ai, then a user-isolated library",
    flowMcpClients: "IDE · ChatBox",
    flowRestClients: "MyPoke.Trade",
    flowAuth: "Bearer API Key",
    flowHub: "kb.agent-mate.ai",
    flowHubOps: "search · propose · confirm",
    flowStore: "Private KB",
    flowIsolate: "user isolate",
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
        <div className="header-end">
          <Link className="btn-text" href="/">
            {t("back")}
          </Link>
          <LocaleSwitcher />
        </div>
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
          <figure className="guide-flow" aria-label={c.diagramAria}>
            <div className="guide-flow-lanes" aria-hidden="true">
              <div className="guide-flow-lane">
                <p className="guide-flow-clients">{c.flowMcpClients}</p>
                <p className="guide-flow-proto">MCP</p>
              </div>
              <div className="guide-flow-lane">
                <p className="guide-flow-clients">{c.flowRestClients}</p>
                <p className="guide-flow-proto">REST</p>
              </div>
            </div>
            <div className="guide-flow-merge" aria-hidden="true">
              <span className="guide-flow-auth">{c.flowAuth}</span>
            </div>
            <div className="guide-flow-hub" aria-hidden="true">
              <p className="guide-flow-hub-name">{c.flowHub}</p>
              <p className="guide-flow-hub-ops">{c.flowHubOps}</p>
            </div>
            <div className="guide-flow-store" aria-hidden="true">
              <p className="guide-flow-store-name">{c.flowStore}</p>
              <p className="guide-flow-store-meta">{c.flowIsolate}</p>
            </div>
            <figcaption className="sr-only">{c.diagramAria}</figcaption>
          </figure>
          <div className="guide-modes">
            <div className="guide-mode">
              <p className="guide-mode-label">MCP</p>
              <p className="guide-mode-who">IDE · ChatBox</p>
              <p>{c.mcpDesc}</p>
            </div>
            <div className="guide-mode">
              <p className="guide-mode-label">REST</p>
              <p className="guide-mode-who">MyPoke.Trade · App</p>
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

          <h3 id="tavily" className="guide-sub">
            {c.tavilyTitle}
          </h3>
          <p>{c.tavilyBody}</p>
          <p className="guide-note">{c.tavilyNote}</p>
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
          <p className="guide-code-label">{c.ideRemoteCaption}</p>
          <pre className="guide-code">
            <code>{MCP_REMOTE_SNIPPET}</code>
          </pre>
          <h3 className="guide-sub">{c.ideLocalTitle}</h3>
          <p className="guide-note">{c.ideLocalLead}</p>
          <p className="guide-code-label">{c.ideLocalCaption}</p>
          <pre className="guide-code">
            <code>{MCP_STDIO_SNIPPET}</code>
          </pre>
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
          <p className="guide-note">{c.chatboxTavily}</p>
          <p className="guide-note">{c.connectCheck}</p>
        </section>
      </article>

      <SiteFooter />
    </div>
  );
}
