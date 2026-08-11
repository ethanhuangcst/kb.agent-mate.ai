"""External source adapters for kb_external_search."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

import httpx

from app.kb_service import DomainError


@dataclass
class ExternalCandidate:
    title: str
    url: str
    snippet: str
    source_id: str
    score: float | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "url": self.url,
            "snippet": self.snippet,
            "source_id": self.source_id,
            "score": self.score,
        }


class SourceAdapter(Protocol):
    source_id: str

    def search(self, query: str, *, top_k: int = 5) -> list[ExternalCandidate]: ...


class FixtureSourceAdapter:
    """Deterministic adapter for tests / local without API keys."""

    source_id = "fixture_web"

    def search(self, query: str, *, top_k: int = 5) -> list[ExternalCandidate]:
        q = (query or "").strip() or "query"
        out: list[ExternalCandidate] = []
        for i in range(min(max(top_k, 1), 5)):
            out.append(
                ExternalCandidate(
                    title=f"Fixture result {i + 1} for {q[:40]}",
                    url=f"https://example.com/fixture/{i + 1}",
                    snippet=f"Synthetic candidate about {q[:80]}",
                    source_id=self.source_id,
                    score=1.0 - i * 0.1,
                )
            )
        return out


class TavilyAdapter:
    source_id = "web_tavily"

    def __init__(self, api_key: str, *, client: httpx.Client | None = None) -> None:
        self.api_key = api_key
        self._client = client

    def search(self, query: str, *, top_k: int = 5) -> list[ExternalCandidate]:
        http = self._client or httpx.Client(timeout=30.0)
        owns = self._client is None
        try:
            resp = http.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": self.api_key,
                    "query": query,
                    "max_results": min(max(top_k, 1), 10),
                    "include_answer": False,
                },
            )
        except httpx.HTTPError as exc:
            raise DomainError("SOURCE_UNAVAILABLE", f"tavily error: {exc}", status_code=502) from exc
        finally:
            if owns:
                http.close()
        if resp.status_code != 200:
            raise DomainError(
                "SOURCE_UNAVAILABLE",
                f"tavily HTTP {resp.status_code}: {resp.text[:200]}",
                status_code=502,
            )
        data = resp.json()
        results = data.get("results") or []
        out: list[ExternalCandidate] = []
        for r in results[:top_k]:
            out.append(
                ExternalCandidate(
                    title=str(r.get("title") or "untitled"),
                    url=str(r.get("url") or ""),
                    snippet=str(r.get("content") or r.get("snippet") or "")[:500],
                    source_id=self.source_id,
                    score=float(r["score"]) if r.get("score") is not None else None,
                )
            )
        return out


def build_source_adapter(
    *,
    tavily_api_key: str | None,
    use_fixture: bool = False,
    http_client: httpx.Client | None = None,
) -> SourceAdapter:
    if use_fixture:
        return FixtureSourceAdapter()
    if tavily_api_key:
        return TavilyAdapter(tavily_api_key, client=http_client)
    raise DomainError(
        "SOURCE_UNAVAILABLE",
        "external search not configured (set TAVILY_API_KEY or KB_SOURCE_USE_FIXTURE=true)",
        status_code=503,
    )
