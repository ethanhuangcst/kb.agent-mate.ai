"""Fetch public URL body text after SSRF checks."""

from __future__ import annotations

import html
import re
from html.parser import HTMLParser

import httpx

from app.kb_service import DomainError
from app.ssrf import validate_outbound_url

MAX_BYTES = 2 * 1024 * 1024
TIMEOUT_S = 20.0


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._chunks: list[str] = []
        self._skip = False

    def handle_starttag(self, tag: str, attrs) -> None:  # noqa: ANN001
        if tag in {"script", "style", "noscript"}:
            self._skip = True

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript"}:
            self._skip = False
        if tag in {"p", "div", "br", "li", "h1", "h2", "h3", "tr"}:
            self._chunks.append("\n")

    def handle_data(self, data: str) -> None:
        if not self._skip and data:
            self._chunks.append(data)

    def text(self) -> str:
        raw = "".join(self._chunks)
        raw = html.unescape(raw)
        raw = re.sub(r"[ \t]+", " ", raw)
        raw = re.sub(r"\n{3,}", "\n\n", raw)
        return raw.strip()


def html_to_text(content: str) -> str:
    parser = _TextExtractor()
    try:
        parser.feed(content)
        parser.close()
    except Exception:  # noqa: BLE001
        return re.sub(r"<[^>]+>", " ", content)
    return parser.text()


def fetch_url_text(
    url: str,
    *,
    client: httpx.Client | None = None,
    max_bytes: int = MAX_BYTES,
) -> str:
    safe = validate_outbound_url(url)
    owns = client is None
    http = client or httpx.Client(timeout=TIMEOUT_S, follow_redirects=True)
    try:
        resp = http.get(safe)
        final = str(resp.url)
        validate_outbound_url(final)
        if resp.status_code >= 400:
            raise DomainError(
                "FETCH_BLOCKED",
                f"upstream returned HTTP {resp.status_code}",
                status_code=400,
            )
        data = resp.content or b""
        if len(data) > max_bytes:
            raise DomainError(
                "FETCH_BLOCKED",
                f"response exceeds {max_bytes} bytes",
                status_code=400,
            )
        ctype = (resp.headers.get("content-type") or "").lower()
    except DomainError:
        raise
    except httpx.HTTPError as exc:
        raise DomainError("FETCH_BLOCKED", f"fetch failed: {exc}", status_code=400) from exc
    finally:
        if owns:
            http.close()

    if "pdf" in ctype:
        raise DomainError(
            "IMPORT_FILE_REJECTED",
            "pdf fetch via URL not supported; upload via imports",
            status_code=400,
        )
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        text = data.decode("utf-8", errors="replace")
    if (
        "html" in ctype
        or text.lstrip().lower().startswith("<!doctype")
        or "<html" in text[:200].lower()
    ):
        text = html_to_text(text)
    text = text.strip()
    if not text:
        raise DomainError(
            "IMPORT_FILE_REJECTED",
            "fetched document has no extractable text",
            status_code=400,
        )
    return text
