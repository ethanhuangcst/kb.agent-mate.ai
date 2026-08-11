"""stdio MCP entry for Cursor (local spawn — no HTTP :8000 required).

Auth: set env ``KB_API_KEY`` (raw key) or ``AUTHORIZATION=Bearer …``.
Identity is resolved once at startup into the same auth context tools use.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys

from app.auth import AuthError, authenticate_bearer
from app.config import get_settings
from app.kb_service import DomainError, KbService
from app.mcp_server import KB_INSTRUCTIONS, _auth_ctx, _tool_error
from kb_schema import get_session


def _resolve_auth():
    settings = get_settings()
    raw = (os.environ.get("KB_API_KEY") or "").strip()
    header = (os.environ.get("AUTHORIZATION") or "").strip()
    if raw and not header:
        header = f"Bearer {raw}"
    if not header.lower().startswith("bearer "):
        print(
            "kb-agent mcp stdio: set KB_API_KEY or AUTHORIZATION=Bearer <key>",
            file=sys.stderr,
        )
        raise SystemExit(2)
    try:
        return authenticate_bearer(header, settings)
    except AuthError as exc:
        print(f"kb-agent mcp stdio: auth failed ({exc.code})", file=sys.stderr)
        raise SystemExit(2) from exc


def _svc() -> KbService:
    settings = get_settings()
    SessionLocal = get_session(settings.database_url)
    return KbService(SessionLocal(), settings)


def main() -> None:
    from mcp.server import MCPServer

    auth = _resolve_auth()
    _auth_ctx.set(auth)

    mcp = MCPServer("kb-agent", instructions=KB_INSTRUCTIONS)

    @mcp.tool(
        name="kb_internal_search",
        description=(
            "Search the user's private knowledge base. Returns citable hits + sufficiency. "
            "Host model composes the user-facing answer. Does not invent citations."
        ),
    )
    def kb_internal_search(query: str, top_k: int = 8) -> str:
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

    asyncio.run(mcp.run_stdio_async())


if __name__ == "__main__":
    main()
