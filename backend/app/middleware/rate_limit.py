"""Lightweight in-memory rate limiting middleware.

This is a pragmatic, single-process limiter suitable for development and a single
backend instance. It is intentionally structured so the storage backend can be
swapped for Redis when the app is scaled horizontally (replace `_Bucket` access
with Redis INCR + EXPIRE behind the same interface).
"""
from __future__ import annotations

import time
from collections import defaultdict

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.responses import err


class _Bucket:
    __slots__ = ("tokens", "updated")

    def __init__(self, tokens: float, updated: float):
        self.tokens = tokens
        self.updated = updated


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Token-bucket limiter keyed by client IP for a path prefix."""

    def __init__(self, app, *, limit: int, window_seconds: int, path_prefix: str = "/api/"):
        super().__init__(app)
        self.limit = limit
        self.window = window_seconds
        self.rate = limit / window_seconds
        self.path_prefix = path_prefix
        self._buckets: dict[str, _Bucket] = defaultdict(lambda: _Bucket(limit, time.monotonic()))

    async def dispatch(self, request: Request, call_next) -> Response:
        if not request.url.path.startswith(self.path_prefix):
            return await call_next(request)

        ip = getattr(request.state, "client_ip", None) or (request.client.host if request.client else "unknown")
        now = time.monotonic()
        bucket = self._buckets[ip]
        # Refill
        bucket.tokens = min(self.limit, bucket.tokens + (now - bucket.updated) * self.rate)
        bucket.updated = now

        if bucket.tokens < 1:
            retry_after = int(1 / self.rate) + 1
            resp = JSONResponse(
                status_code=429,
                content=err("RATE_LIMITED", "Too many requests, please slow down"),
            )
            resp.headers["Retry-After"] = str(retry_after)
            return resp

        bucket.tokens -= 1
        return await call_next(request)
