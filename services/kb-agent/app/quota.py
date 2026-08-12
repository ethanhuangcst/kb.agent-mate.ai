"""Per-user sliding-window rate limits for outbound KB operations."""

from __future__ import annotations

import threading
import time
from collections import defaultdict, deque
from typing import Callable
from uuid import UUID

from app.kb_service import DomainError

Kind = str  # "fetch" | "external_search"


class QuotaLimiter:
    """Process-local RPM limiter keyed by user_id + kind."""

    def __init__(
        self,
        *,
        fetch_rpm: int = 20,
        external_search_rpm: int = 30,
        clock: Callable[[], float] | None = None,
    ) -> None:
        self.fetch_rpm = max(1, int(fetch_rpm))
        self.external_search_rpm = max(1, int(external_search_rpm))
        self._clock = clock or time.monotonic
        self._lock = threading.Lock()
        self._events: dict[tuple[str, Kind], deque[float]] = defaultdict(deque)

    def _limit_for(self, kind: Kind) -> int:
        if kind == "fetch":
            return self.fetch_rpm
        if kind == "external_search":
            return self.external_search_rpm
        raise ValueError(f"unknown quota kind: {kind}")

    def check_and_consume(self, user_id: UUID | str, kind: Kind) -> None:
        key = (str(user_id), kind)
        limit = self._limit_for(kind)
        window = 60.0
        now = self._clock()
        with self._lock:
            q = self._events[key]
            while q and now - q[0] >= window:
                q.popleft()
            if len(q) >= limit:
                raise DomainError(
                    "RATE_LIMITED",
                    f"{kind} rate limit exceeded ({limit}/min); retry after ~60s",
                    status_code=429,
                    degrade_hint="retry_later",
                )
            q.append(now)


_default: QuotaLimiter | None = None


def get_quota_limiter(
    *,
    fetch_rpm: int | None = None,
    external_search_rpm: int | None = None,
) -> QuotaLimiter:
    global _default
    if _default is None:
        _default = QuotaLimiter(
            fetch_rpm=fetch_rpm or 20,
            external_search_rpm=external_search_rpm or 30,
        )
    return _default


def reset_quota_limiter_for_tests() -> None:
    global _default
    _default = None
