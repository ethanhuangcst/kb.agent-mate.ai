"""Optional OpenAI-compatible chat facade — same KbService tools + scope guard."""

from __future__ import annotations

import json
import logging
from typing import Any
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.auth import AuthContext, require_bearer
from app.config import Settings, get_settings
from app.kb_service import DomainError, KbService
from app.scope_guard import check_business_scope
from kb_schema import get_session

logger = logging.getLogger("kb-agent.chat")

SYSTEM_PROMPT = (
    "You are a thin knowledge harness for a private KB. "
    "Use tools to search/list/propose/confirm/fetch/external-search. "
    "Prefer internal search before external. "
    "Never invent citations. Never give business strategy or campaign decisions. "
    "Never auto-ingest; writes need confirm. "
    "Answer only from tool observations."
)

TOOL_DEFS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "kb_internal_search",
            "description": "Search private knowledge base",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "top_k": {"type": "integer"},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "kb_list_knowledge",
            "description": "List knowledge items",
            "parameters": {
                "type": "object",
                "properties": {
                    "project": {"type": "string"},
                    "tag": {"type": "string"},
                    "limit": {"type": "integer"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "kb_propose_add",
            "description": "Propose text for ingest (pending only)",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "title": {"type": "string"},
                    "project": {"type": "string"},
                },
                "required": ["text"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "kb_confirm_add",
            "description": "Confirm pending proposal",
            "parameters": {
                "type": "object",
                "properties": {"pending_id": {"type": "string"}},
                "required": ["pending_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "kb_fetch_url",
            "description": "Fetch URL into pending proposal",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string"},
                    "title": {"type": "string"},
                },
                "required": ["url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "kb_external_search",
            "description": "External candidates (no ingest)",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "top_k": {"type": "integer"},
                },
                "required": ["query"],
            },
        },
    },
]


class ChatMessage(BaseModel):
    role: str
    content: str | None = None
    tool_calls: list[dict[str, Any]] | None = None
    tool_call_id: str | None = None
    name: str | None = None


class ChatCompletionRequest(BaseModel):
    model: str | None = None
    messages: list[ChatMessage] = Field(min_length=1)
    stream: bool = False
    max_completion_tokens: int | None = None


def _get_db(settings: Settings = Depends(get_settings)):
    SessionLocal = get_session(settings.database_url)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def _get_kb(
    session: Session = Depends(_get_db),
    settings: Settings = Depends(get_settings),
):
    svc = KbService(session, settings)
    try:
        yield svc
    finally:
        svc.close()


def _truncate(s: str, n: int = 4000) -> str:
    return s if len(s) <= n else s[:n] + "…"


def _run_tool(svc: KbService, user_id: UUID, name: str, args: dict[str, Any]) -> str:
    try:
        if name == "kb_internal_search":
            out = svc.search(
                user_id=user_id,
                query=str(args.get("query") or ""),
                top_k=int(args.get("top_k") or 8),
            )
            return json.dumps(
                {
                    "hits": [h.__dict__ for h in out.hits],
                    "sufficiency": {"enough": out.enough, "reason": out.reason},
                },
                ensure_ascii=False,
            )
        if name == "kb_list_knowledge":
            items = svc.list_knowledge(
                user_id=user_id,
                project=args.get("project"),
                tag=args.get("tag"),
                limit=int(args.get("limit") or 50),
            )
            return json.dumps({"items": items}, ensure_ascii=False)
        if name == "kb_propose_add":
            return json.dumps(
                svc.propose_ingest(
                    user_id=user_id,
                    text=str(args.get("text") or ""),
                    title=args.get("title"),
                    project=args.get("project"),
                ),
                ensure_ascii=False,
            )
        if name == "kb_confirm_add":
            return json.dumps(
                svc.confirm_ingest(
                    user_id=user_id,
                    pending_id=str(args.get("pending_id") or ""),
                ),
                ensure_ascii=False,
            )
        if name == "kb_fetch_url":
            return json.dumps(
                svc.fetch_url(
                    user_id=user_id,
                    url=str(args.get("url") or ""),
                    title=args.get("title"),
                    propose=True,
                ),
                ensure_ascii=False,
            )
        if name == "kb_external_search":
            return json.dumps(
                svc.external_search(
                    user_id=user_id,
                    query=str(args.get("query") or ""),
                    top_k=int(args.get("top_k") or 5),
                ),
                ensure_ascii=False,
            )
        return json.dumps({"code": "UNKNOWN_TOOL", "message": name})
    except DomainError as exc:
        payload: dict[str, Any] = {"code": exc.code, "message": exc.message}
        if exc.degrade_hint:
            payload["degrade_hint"] = exc.degrade_hint
        return json.dumps(payload, ensure_ascii=False)


def _last_user_text(messages: list[ChatMessage]) -> str:
    for m in reversed(messages):
        if m.role == "user" and m.content:
            return m.content
    return ""


class FakeChatClient:
    """Deterministic client for tests — one search tool call then final answer."""

    def __init__(self) -> None:
        self._turn = 0

    def chat_completions_create(self, **kwargs: Any) -> Any:
        self._turn += 1
        if self._turn == 1:
            return {
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": None,
                            "tool_calls": [
                                {
                                    "id": "call_1",
                                    "type": "function",
                                    "function": {
                                        "name": "kb_internal_search",
                                        "arguments": json.dumps(
                                            {"query": "test", "top_k": 3}
                                        ),
                                    },
                                }
                            ],
                        }
                    }
                ]
            }
        return {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": "Based on tool results: grounded answer.",
                    }
                }
            ]
        }


def _build_llm_client(settings: Settings):
    if settings.use_fake_km:
        return FakeChatClient()
    from openai import OpenAI

    api_key = settings.qwen_api_key or ""
    if not api_key:
        raise DomainError(
            "CHAT_UNAVAILABLE",
            "chat facade requires QWEN_API_KEY when USE_FAKE_KM=false",
            status_code=503,
        )
    base = settings.qwen_base_url or "https://dashscope.aliyuncs.com/compatible-mode/v1"
    client = OpenAI(api_key=api_key, base_url=base)

    class _Wrapper:
        def chat_completions_create(self, **kwargs: Any) -> Any:
            return client.chat.completions.create(**kwargs)

    return _Wrapper()


def run_chat_loop(
    *,
    svc: KbService,
    user_id: UUID,
    messages: list[dict[str, Any]],
    settings: Settings,
    llm: Any | None = None,
) -> dict[str, Any]:
    client = llm or _build_llm_client(settings)
    model = settings.qwen_chat_model or "qwen-plus"
    working = [{"role": "system", "content": SYSTEM_PROMPT}] + list(messages)
    max_iter = max(1, int(settings.chat_max_tool_iterations))

    for _ in range(max_iter):
        raw = client.chat_completions_create(
            model=model,
            messages=working,
            tools=TOOL_DEFS,
            max_completion_tokens=settings.chat_max_tool_iterations and 1024 or 1024,
        )
        # Support both dict (fake) and OpenAI object
        if hasattr(raw, "model_dump"):
            data = raw.model_dump()
        elif isinstance(raw, dict):
            data = raw
        else:
            data = json.loads(raw.model_dump_json()) if hasattr(raw, "model_dump_json") else {}

        choice = (data.get("choices") or [{}])[0]
        msg = choice.get("message") or {}
        tool_calls = msg.get("tool_calls") or []
        if not tool_calls:
            content = msg.get("content") or ""
            return {
                "id": "chatcmpl-kb",
                "object": "chat.completion",
                "model": model,
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": content},
                        "finish_reason": "stop",
                    }
                ],
            }

        working.append(
            {
                "role": "assistant",
                "content": msg.get("content"),
                "tool_calls": tool_calls,
            }
        )
        for tc in tool_calls:
            fn = tc.get("function") or {}
            name = fn.get("name") or ""
            try:
                args = json.loads(fn.get("arguments") or "{}")
            except json.JSONDecodeError:
                args = {}
            result = _truncate(_run_tool(svc, user_id, name, args))
            working.append(
                {
                    "role": "tool",
                    "tool_call_id": tc.get("id") or "call",
                    "name": name,
                    "content": result,
                }
            )

    return {
        "id": "chatcmpl-kb",
        "object": "chat.completion",
        "model": model,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "Stopped after max tool iterations.",
                },
                "finish_reason": "length",
            }
        ],
    }


def mount_chat_facade(app: FastAPI) -> None:
    @app.post("/v1/chat/completions")
    def chat_completions(
        body: ChatCompletionRequest,
        auth: AuthContext = Depends(require_bearer),
        kb: KbService = Depends(_get_kb),
        settings: Settings = Depends(get_settings),
    ) -> dict[str, Any]:
        if not settings.chat_facade_enabled:
            raise HTTPException(
                status_code=404,
                detail={"code": "CHAT_DISABLED", "message": "chat facade disabled"},
            )
        if body.stream:
            raise HTTPException(
                status_code=400,
                detail={"code": "STREAM_UNSUPPORTED", "message": "stream=false only"},
            )
        user_text = _last_user_text(body.messages)
        try:
            check_business_scope(user_text, None)
        except DomainError as exc:
            raise HTTPException(
                status_code=exc.status_code,
                detail={
                    "code": exc.code,
                    "message": exc.message,
                    **({"degrade_hint": exc.degrade_hint} if exc.degrade_hint else {}),
                },
            ) from exc

        msgs = [m.model_dump(exclude_none=True) for m in body.messages]
        try:
            return run_chat_loop(
                svc=kb,
                user_id=auth.user_id,
                messages=msgs,
                settings=settings,
            )
        except DomainError as exc:
            raise HTTPException(
                status_code=exc.status_code,
                detail={"code": exc.code, "message": exc.message},
            ) from exc
