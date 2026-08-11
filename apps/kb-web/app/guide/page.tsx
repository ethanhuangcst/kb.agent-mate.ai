import Link from "next/link";
import { getLocale, getTranslations } from "next-intl/server";
import { BrandLockup, SiteFooter } from "../site-chrome";

const copy = {
  "zh-CN": {
    tocArch: "1. 架构",
    tocKey: "2. 获取 Key",
    archTitle: "1. 架构指南",
    who: "调用者是谁",
    whoItems: [
      ["IDE", "如 Cursor 里的 Agent / 项目会话"],
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
    mcpDesc: "远程 MCP 接入；你的宿主模型按工具描述调用检索 / 提案 / 确认等。",
    restDesc: "HTTP 调 /api/v1/kb/*；与 MCP 同一套能力语义。",
    modesNote: "两种方式共用一把 Key、同一知识库；请求体里的用户标识不能覆盖 Key 身份。",
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
      "入库提案：摘要、分类建议、查重",
      "确认后的持久化与向量化",
    ],
    llmNoteBefore: "本站帮你",
    llmNoteStrong1: "找到并管好知识",
    llmNoteMid: "，不替你",
    llmNoteStrong2: "做完生意",
    llmNoteAfter: "。要投放策略或业务结论，须由你侧模型结合业务数据完成；外部材料须确认后才入库。",
    keyTitle: "2. 获取 API Key",
    keySteps: [
      "请管理员在管理台签发使用者 Key（明文仅显示一次）。",
      "请求头：Authorization: Bearer <api_key>",
      "吊销立即失效；重签换密钥，知识库保留。",
    ],
    diagramAria: "调用方经 MCP 或 REST，用同一把 Bearer Key 进入 kb.agent-mate.ai，再访问按用户隔离的私人知识库",
  },
  en: {
    tocArch: "1. Architecture",
    tocKey: "2. Get a key",
    archTitle: "1. Architecture",
    who: "Who calls",
    whoItems: [
      ["IDE", "e.g. Cursor Agent / project chat"],
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
    mcpDesc: "Remote MCP; your host model invokes search / propose / confirm tools.",
    restDesc: "HTTP to /api/v1/kb/*; same capability semantics as MCP.",
    modesNote: "Both share one key and one library; body user ids cannot override Bearer identity.",
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
      "Propose: summary, type hints, dedupe",
      "Persist and embed after confirm",
    ],
    llmNoteBefore: "We help you ",
    llmNoteStrong1: "find and manage knowledge",
    llmNoteMid: ", not ",
    llmNoteStrong2: "run the business for you",
    llmNoteAfter: ". Strategy and conclusions stay on your side; external material indexes only after confirm.",
    keyTitle: "2. Get an API key",
    keySteps: [
      "Ask an admin to issue a user key (plaintext once).",
      "Header: Authorization: Bearer <api_key>",
      "Revoke fails immediately; reissue rotates the secret, library kept.",
    ],
    diagramAria: "Callers use MCP or REST with the same Bearer key into kb.agent-mate.ai, then a user-isolated library",
  },
} as const;

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
              <span className="arch-muted">Cursor / ChatBox</span>
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
              <p className="guide-mode-who">Cursor · ChatBox</p>
              <p>{c.mcpDesc}</p>
            </div>
            <div className="guide-mode">
              <p className="guide-mode-label">REST</p>
              <p className="guide-mode-who">HCP · App</p>
              <p>
                {c.restDesc.includes("/api/") ? (
                  <>
                    HTTP <span className="mono">/api/v1/kb/*</span>
                    {locale === "en" ? "; same semantics as MCP." : "；与 MCP 同一套能力语义。"}
                  </>
                ) : (
                  c.restDesc
                )}
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
          <ol>
            <li>{c.keySteps[0]}</li>
            <li>
              {locale === "en" ? "Header: " : "请求头："}
              <span className="mono">Authorization: Bearer &lt;api_key&gt;</span>
            </li>
            <li>{c.keySteps[2]}</li>
          </ol>
        </section>
      </article>

      <SiteFooter />
    </div>
  );
}
