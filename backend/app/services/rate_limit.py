from __future__ import annotations

import time
from collections import defaultdict, deque
from dataclasses import dataclass

from fastapi import HTTPException


@dataclass
class RateLimitConfig:
    limit: int
    window_seconds: int


_HITS: dict[str, deque[float]] = defaultdict(deque)


def enforce_rate_limit(key: str, config: RateLimitConfig) -> None:
    now = time.time()
    window_start = now - config.window_seconds
    hits = _HITS[key]
    while hits and hits[0] < window_start:
        hits.popleft()
    if len(hits) >= config.limit:
        raise HTTPException(status_code=429, detail="Too many requests")
    hits.append(now)
