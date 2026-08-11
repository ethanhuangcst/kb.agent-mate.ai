"""Internal Qwen KM client — title / type / tags + content overview (summary)."""

from __future__ import annotations

import json
import os
import re
from typing import Any, Protocol

from app.config import Settings

# Unicode character cap for KnowledgeItem.summary (content overview).
SUMMARY_MAX_CHARS = 400
SUMMARY_TARGET_MIN = 150


def truncate_summary(text: str | None, *, max_chars: int = SUMMARY_MAX_CHARS) -> str:
    s = (text or "").strip()
    if len(s) <= max_chars:
        return s
    return s[:max_chars].rstrip()


def build_heuristic_overview(text: str, *, title: str | None = None) -> str:
    """Fake / fallback overview: stitch leading paragraphs up to SUMMARY_MAX_CHARS."""
    body = (text or "").strip()
    if not body:
        return truncate_summary(title or "untitled")
    parts: list[str] = []
    if title:
        parts.append(f"主题：{title.strip()}。")
    # Prefer paragraph breaks, then sentences.
    paras = [p.strip() for p in re.split(r"\n\s*\n", body) if p.strip()]
    if not paras:
        paras = [body]
    for p in paras:
        # Collapse internal whitespace for density
        compact = re.sub(r"\s+", " ", p)
        parts.append(compact)
        joined = "".join(parts)
        if len(joined) >= SUMMARY_TARGET_MIN:
            break
    overview = "".join(parts)
    if len(overview) < SUMMARY_TARGET_MIN and len(body) > len(overview):
        overview = re.sub(r"\s+", " ", body)[:SUMMARY_MAX_CHARS]
    return truncate_summary(overview)


class KmClient(Protocol):
    def propose_metadata(self, *, text: str, title: str | None = None) -> dict[str, Any]: ...


class FakeKmClient:
    """CI / local fixture — no network."""

    def propose_metadata(self, *, text: str, title: str | None = None) -> dict[str, Any]:
        overview = build_heuristic_overview(text, title=title)
        first = (text or "").strip().split("\n", 1)[0][:80]
        return {
            "title": title or first or "untitled",
            "summary": overview,
            "knowledge_type": "note",
            "tags": [],
        }


class DashScopeKmClient:
    def __init__(self, settings: Settings) -> None:
        from openai import OpenAI

        key = settings.qwen_api_key or os.environ.get("QWEN_API_KEY") or ""
        if not key:
            raise ValueError("QWEN_API_KEY required for real KM")
        base = settings.qwen_base_url or os.environ.get("QWEN_BASE_URL") or (
            "https://dashscope.aliyuncs.com/compatible-mode/v1"
        )
        self.model = settings.qwen_chat_model or os.environ.get("QWEN_CHAT_MODEL") or "qwen-plus"
        self._client = OpenAI(api_key=key, base_url=base.rstrip("/"))

    def propose_metadata(self, *, text: str, title: str | None = None) -> dict[str, Any]:
        prompt = (
            "You are a knowledge-management assistant. Given document text, return ONLY JSON "
            "with keys: title (string), summary (string), knowledge_type (string), "
            "tags (array of short strings).\n"
            "summary MUST be a content overview of the document (主题、结构要点、适用范围), "
            f"NOT a title restatement. Target length {SUMMARY_TARGET_MIN}–{SUMMARY_MAX_CHARS} "
            f"Unicode characters; hard max {SUMMARY_MAX_CHARS}. Write in the same language as the "
            "document. Do not give business strategy or campaign conclusions."
        )
        user = f"Title hint: {title or ''}\n\nText:\n{text[:8000]}"
        resp = self._client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": user},
            ],
            temperature=0.2,
        )
        raw = (resp.choices[0].message.content or "").strip()
        return _parse_km_json(raw, fallback_title=title, text=text)


def _parse_km_json(raw: str, *, fallback_title: str | None, text: str) -> dict[str, Any]:
    match = re.search(r"\{[\s\S]*\}", raw)
    data: dict[str, Any]
    if match:
        try:
            data = json.loads(match.group(0))
        except json.JSONDecodeError:
            data = {}
    else:
        data = {}
    first = text.strip().split("\n", 1)[0][:80]
    summary_raw = data.get("summary")
    if not summary_raw or not str(summary_raw).strip():
        summary = build_heuristic_overview(text, title=fallback_title or str(data.get("title") or ""))
    else:
        summary = truncate_summary(str(summary_raw))
    return {
        "title": str(data.get("title") or fallback_title or first or "untitled"),
        "summary": summary,
        "knowledge_type": str(data.get("knowledge_type") or "note"),
        "tags": list(data.get("tags") or []) if isinstance(data.get("tags"), list) else [],
    }


def build_km_client(settings: Settings) -> KmClient:
    if settings.use_fake_km:
        return FakeKmClient()
    return DashScopeKmClient(settings)
