"""MCP Streamable HTTP facade — tools call KbService only (mcp 2.x MCPServer)."""

from __future__ import annotations

import contextvars
import json
import logging
from contextlib import asynccontextmanager
from typing import Any

from app.auth import AuthContext, AuthError, authenticate_bearer
from app.config import get_settings
from app.kb_service import DomainError, KbService
from kb_schema import get_session

logger = logging.getLogger("kb-agent.mcp")

_auth_ctx: contextvars.ContextVar[AuthContext | None] = contextvars.ContextVar(
    "mcp_auth", default=None
)

KB_INSTRUCTIONS = (
    "kb-agent private knowledge tools. Search returns citable fragments only. "
    "Writes require propose then explicit confirm — never auto-ingest. "
    "Do not generate business strategy or campaign conclusions. "
    "Operates only on the library bound to the Bearer API key."
)


def current_auth() -> AuthContext:
    ctx = _auth_ctx.get()
    if ctx is None:
        raise RuntimeError("MCP auth context missing")
    return ctx


def _svc() -> KbService:
    settings = get_settings()
    SessionLocal = get_session(settings.database_url)
    return KbService(SessionLocal(), settings)


def _tool_error(exc: DomainError) -> str:
    return json.dumps({"code": exc.code, "message": exc.message}, ensure_ascii=False)


def _register_tools(mcp: Any) -> None:
    @mcp.tool(
        name="kb_internal_search",
        description=(
            "Search the user's private knowledge base. Returns citable hits + sufficiency. "
            "Host model composes the user-facing answer. Does not invent citations."
        ),
    )
    def kb_internal_search(query: str, top_k: int = 8) -> str:
        auth = current_auth()
        svc = _svc()
        try:
            out = svc.search(user_id=auth.user_id, query=query, top_k=top_k)
            payload = {
                "hits": [h.__dict__ for h in out.hits],
                "sufficiency": {"enough": out.enough, "reason": out.reason},
            }
            return json.dumps(payload, ensure_ascii=False)
        except DomainError as exc:
            return _tool_error(exc)
        finally:
            svc.close()

    @mcp.tool(
        name="kb_propose_add",
        description=(
            "Propose adding pasted text to the knowledge base. Creates a pending proposal only — "
            "will not auto-add; requires kb_confirm_add. KM writes a content overview (summary, "
            "max 400 chars). Does not generate business strategy. "
            "Operates only on this API key's library."
        ),
    )
    def kb_propose_add(
        text: str,
        title: str | None = None,
        project: str | None = None,
        tags: list[str] | None = None,
    ) -> str:
        auth = current_auth()
        svc = _svc()
        try:
            return json.dumps(
                svc.propose_ingest(
                    user_id=auth.user_id,
                    text=text,
                    title=title,
                    project=project,
                    tags=tags,
                ),
                ensure_ascii=False,
            )
        except DomainError as exc:
            return _tool_error(exc)
        finally:
            svc.close()

    @mcp.tool(
        name="kb_confirm_add",
        description=(
            "Confirm a pending add proposal and index it. Will not auto-add without this call. "
            "Does not generate business strategy. Operates only on this API key's library."
        ),
    )
    def kb_confirm_add(pending_id: str) -> str:
        auth = current_auth()
        svc = _svc()
        try:
            return json.dumps(
                svc.confirm_ingest(user_id=auth.user_id, pending_id=pending_id),
                ensure_ascii=False,
            )
        except DomainError as exc:
            return _tool_error(exc)
        finally:
            svc.close()

    @mcp.tool(
        name="kb_list_knowledge",
        description=(
            "List confirmed knowledge items for this API key's library (includes summary overview). "
            "Optional filters: project, tag, knowledge_type, limit."
        ),
    )
    def kb_list_knowledge(
        project: str | None = None,
        tag: str | None = None,
        knowledge_type: str | None = None,
        limit: int = 50,
    ) -> str:
        auth = current_auth()
        svc = _svc()
        try:
            items = svc.list_knowledge(
                user_id=auth.user_id,
                project=project,
                tag=tag,
                knowledge_type=knowledge_type,
                limit=limit,
            )
            return json.dumps({"items": items}, ensure_ascii=False)
        except DomainError as exc:
            return _tool_error(exc)
        finally:
            svc.close()

    @mcp.tool(
        name="kb_knowledge_summary",
        description=(
            "Read the content overview (summary, max 400 chars) for one item by knowledge_id or "
            "pending_id. Set refresh=true to regenerate from body via KM and write back. "
            "Does not change index status. Does not generate business strategy."
        ),
    )
    def kb_knowledge_summary(
        knowledge_id: str | None = None,
        pending_id: str | None = None,
        refresh: bool = False,
    ) -> str:
        auth = current_auth()
        svc = _svc()
        try:
            return json.dumps(
                svc.get_knowledge_summary(
                    user_id=auth.user_id,
                    knowledge_id=knowledge_id,
                    pending_id=pending_id,
                    refresh=refresh,
                ),
                ensure_ascii=False,
            )
        except DomainError as exc:
            return _tool_error(exc)
        finally:
            svc.close()


class _EnsureMountRootPath:
    """Starlette Mount leaves path '' for exact `/mcp`; Streamable HTTP expects `/`."""

    def __init__(self, app: Any) -> None:
        self.app = app

    async def __call__(self, scope: Any, receive: Any, send: Any) -> None:
        if scope.get("type") == "http" and scope.get("path") == "":
            scope = dict(scope)
            scope["path"] = "/"
            if "raw_path" in scope:
                scope["raw_path"] = b"/"
        await self.app(scope, receive, send)


def _build_mcp_asgi() -> tuple[Any, Any, Any]:
    from mcp.server import MCPServer
    from mcp.server.transport_security import TransportSecuritySettings

    mcp = MCPServer("kb-agent", instructions=KB_INSTRUCTIONS)
    _register_tools(mcp)
    security = TransportSecuritySettings(enable_dns_rebinding_protection=False)
    # Path "/" inside mount → public URL /mcp (not /mcp/mcp)
    streamable = _EnsureMountRootPath(
        mcp.streamable_http_app(
            streamable_http_path="/",
            stateless_http=True,
            transport_security=security,
        )
    )
    # Legacy SSE for ChatBox "Remote (http/sse)": GET /sse + POST /messages/
    sse = mcp.sse_app(
        sse_path="/sse",
        message_path="/messages/",
        transport_security=security,
    )
    return mcp, streamable, sse


def _replace_mcp_mount(fastapi_app: Any, asgi: Any) -> None:
    from starlette.routing import Mount

    for route in fastapi_app.router.routes:
        if isinstance(route, Mount) and route.path == "/mcp":
            route.app = asgi
            return
    fastapi_app.mount("/mcp", asgi)


def _is_mcp_path(path: str) -> bool:
    return (
        path == "/mcp"
        or path.startswith("/mcp/")
        or path == "/sse"
        or path.startswith("/messages")
    )


def mount_mcp(fastapi_app: Any) -> None:
    """Mount Streamable HTTP (/mcp) + legacy SSE (/sse) with Bearer auth."""
    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.requests import Request
    from starlette.responses import JSONResponse

    class BearerAuthMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request: Request, call_next):  # type: ignore[no-untyped-def]
            # Starlette Mount("/mcp") regex is ^/mcp/(?P<path>.*)$ — bare `/mcp` does not match.
            if request.scope.get("path") == "/mcp":
                request.scope["path"] = "/mcp/"
                if "raw_path" in request.scope:
                    request.scope["raw_path"] = b"/mcp/"
            path = request.url.path
            if path == "/mcp":
                path = "/mcp/"
            if _is_mcp_path(path):
                auth_header = request.headers.get("authorization") or ""
                settings = get_settings()
                try:
                    ctx = authenticate_bearer(auth_header, settings)
                except AuthError as exc:
                    return JSONResponse(
                        {"code": exc.code, "message": exc.code},
                        status_code=exc.status_code,
                    )
                token = _auth_ctx.set(ctx)
                try:
                    return await call_next(request)
                finally:
                    _auth_ctx.reset(token)
            return await call_next(request)

    state: dict[str, Any] = {}
    mcp, streamable, sse = _build_mcp_asgi()
    state["mcp"] = mcp

    existing = getattr(fastapi_app.router, "lifespan_context", None)

    @asynccontextmanager
    async def lifespan(app: Any):
        # Session manager is one-shot; rebuild ASGI if a prior TestClient already exited.
        current = state["mcp"]
        sm = current.session_manager
        if getattr(sm, "_has_started", False):
            current, streamable_new, sse_new = _build_mcp_asgi()
            state["mcp"] = current
            _replace_mcp_mount(fastapi_app, streamable_new)
            _replace_sse_routes(fastapi_app, sse_new)
        async with state["mcp"].session_manager.run():
            if existing is not None:
                async with existing(app):
                    yield
            else:
                yield

    fastapi_app.router.lifespan_context = lifespan
    fastapi_app.add_middleware(BearerAuthMiddleware)
    fastapi_app.mount("/mcp", streamable)
    _attach_sse_routes(fastapi_app, sse)
    logger.info("MCP Streamable HTTP at /mcp; legacy SSE at /sse (ChatBox)")


def _attach_sse_routes(fastapi_app: Any, sse_app: Any) -> None:
    """Register SSE Starlette routes on the FastAPI app (GET /sse, POST /messages/)."""
    for route in sse_app.routes:
        fastapi_app.router.routes.append(route)


def _replace_sse_routes(fastapi_app: Any, sse_app: Any) -> None:
    """Drop prior /sse and /messages mounts, then re-attach (TestClient lifespan rebuild)."""
    from starlette.routing import Mount, Route

    kept = []
    for route in fastapi_app.router.routes:
        path = getattr(route, "path", None)
        if path in ("/sse", "/messages", "/messages/") or (
            isinstance(route, Mount) and path in ("/messages", "/messages/")
        ):
            continue
        if isinstance(route, Route) and path == "/sse":
            continue
        kept.append(route)
    fastapi_app.router.routes[:] = kept
    _attach_sse_routes(fastapi_app, sse_app)
