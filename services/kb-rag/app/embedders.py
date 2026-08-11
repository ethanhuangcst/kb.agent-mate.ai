"""Embedding backends: Fake (CI) and DashScope OpenAI-compatible."""

from __future__ import annotations

import hashlib
import math
import os
import re
from typing import Protocol


class Embedder(Protocol):
    def embed(self, texts: list[str]) -> list[list[float]]: ...


class FakeEmbedder:
    """Deterministic bag-of-tokens embedder for CI (no external API)."""

    def __init__(self, dim: int = 64) -> None:
        self.dim = dim

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._one(t) for t in texts]

    def _one(self, text: str) -> list[float]:
        vec = [0.0] * self.dim
        tokens = re.findall(r"\w+", text.lower())
        if not tokens:
            return vec
        for tok in tokens:
            digest = hashlib.sha256(tok.encode("utf-8")).digest()
            idx = digest[0] % self.dim
            sign = 1.0 if digest[1] % 2 == 0 else -1.0
            vec[idx] += sign
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [v / norm for v in vec]


class DashScopeEmbedder:
    """Qwen embedding via OpenAI-compatible DashScope endpoint."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        dim: int = 1024,
    ) -> None:
        from openai import OpenAI

        self.dim = dim
        self.model = model or os.environ.get("QWEN_EMBED_MODEL") or "text-embedding-v3"
        key = api_key or os.environ.get("QWEN_API_KEY") or ""
        if not key:
            raise ValueError("QWEN_API_KEY required when USE_FAKE_EMBEDDER=false")
        base = base_url or os.environ.get("QWEN_BASE_URL") or "https://dashscope.aliyuncs.com/compatible-mode/v1"
        self._client = OpenAI(api_key=key, base_url=base.rstrip("/"))

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        resp = self._client.embeddings.create(model=self.model, input=texts)
        # Sort by index to preserve order
        data = sorted(resp.data, key=lambda d: d.index)
        return [list(d.embedding) for d in data]


def build_embedder(*, use_fake: bool, dim: int) -> Embedder:
    if use_fake:
        return FakeEmbedder(dim=dim)
    return DashScopeEmbedder(dim=dim)
