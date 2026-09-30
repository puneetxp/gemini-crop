"""
Sliding window rate limiter using Redis with memory fallback.
Fails open on cache connection drop to ensure service continuity.
"""
from __future__ import annotations

import logging
import time
from collections import defaultdict
from typing import Callable, DefaultDict, List, Optional

try:
    from fastapi import HTTPException, Request, status
except ImportError:
    class HTTPException(Exception):  # type: ignore
        def __init__(self, status_code: int = 400, detail: str = "", headers: Optional[Dict[str, str]] = None):
            self.status_code = status_code
            self.detail = detail
            self.headers = headers
            super().__init__(detail)

    class status:  # type: ignore
        HTTP_429_TOO_MANY_REQUESTS = 429

    class Request:  # type: ignore
        def __init__(self) -> None:
            self.client = None
            self.state = None
            self.url = type("URL", (), {"path": "/"})()

from app.core.config import settings

logger = logging.getLogger("cropsense.rate_limiter")


class SlidingWindowRateLimiter:
    """Sliding window rate limiter with Redis and in-memory fallback."""

    def __init__(self) -> None:
        self._redis_client: Any = None
        self._memory_store: DefaultDict[str, List[float]] = defaultdict(list)
        self._init_redis()

    def _init_redis(self) -> None:
        try:
            import redis

            self._redis_client = redis.Redis.from_url(
                settings.REDIS_URL,
                socket_connect_timeout=2,
                socket_timeout=2,
                decode_responses=True,
            )
            # Ping test
            self._redis_client.ping()
            logger.info("Connected to Redis for rate limiting at %s", settings.REDIS_URL)
        except Exception as err:
            logger.debug("Redis unavailable (%s), using in-memory rate limiter fallback", err)
            self._redis_client = None

    def is_rate_limited(self, key: str, max_requests: int, window_seconds: int = 60) -> bool:
        """Check if request exceeds rate limit. Fails open on errors."""
        now = time.time()
        cutoff = now - window_seconds

        # 1. Try Redis sliding window
        if self._redis_client is not None:
            try:
                pipe = self._redis_client.pipeline()
                pipe.zremrangebyscore(key, 0, cutoff)
                pipe.zadd(key, {str(now): now})
                pipe.zcard(key)
                pipe.expire(key, window_seconds + 5)
                _, _, current_count, _ = pipe.execute()
                return current_count > max_requests
            except Exception as err:
                logger.warning("Redis rate limit check failed (%s); failing open", err)
                # Continue to memory check

        # 2. In-memory sliding window fallback
        timestamps = self._memory_store[key]
        # Purge expired timestamps
        self._memory_store[key] = [ts for ts in timestamps if ts > cutoff]
        if len(self._memory_store[key]) >= max_requests:
            return True

        self._memory_store[key].append(now)
        return False

    def get_middleware(
        self,
        limit: int = 100,
        window: int = 60,
        public_limit: int = 20,
    ):
        """Generate ASGI middleware callback for Starlette/FastAPI."""
        async def rate_limit_middleware(request: Request, call_next):
            client_ip = request.client.host if request.client else "127.0.0.1"
            auth_header = request.headers.get("Authorization")
            max_req = limit if auth_header else public_limit
            key = f"rate_limit:{client_ip}"

            if self.is_rate_limited(key, max_requests=max_req, window_seconds=window):
                from fastapi.responses import JSONResponse
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={"detail": "Rate limit exceeded. Please try again later."},
                    headers={"Retry-After": str(window)},
                )

            response = await call_next(request)
            return response

        return rate_limit_middleware


# Singleton rate limiter
limiter = SlidingWindowRateLimiter()
RateLimiter = SlidingWindowRateLimiter
_rate_limiter: Optional[SlidingWindowRateLimiter] = None


def init_rate_limiter(
    redis_url: str = None, default_limit: int = 100, window_seconds: int = 60, enabled: bool = True
) -> SlidingWindowRateLimiter:
    """Initialize global rate limiter instance."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = SlidingWindowRateLimiter()
    return _rate_limiter


def get_rate_limiter() -> Optional[SlidingWindowRateLimiter]:
    """Get global rate limiter instance."""
    return _rate_limiter or limiter


def rate_limit(
    max_requests: Optional[int] = None,
    window_seconds: int = 60,
    by_user: bool = True,
) -> Callable[[Request], None]:
    """FastAPI route dependency generator for rate limiting."""
    limit = max_requests or settings.RATE_LIMIT_PUBLIC

    async def _rate_limiter_dependency(request: Request) -> None:
        client_ip = request.client.host if request.client else "unknown"
        user_id = getattr(request.state, "user_id", None) if by_user else None
        ident = f"rl:{user_id or client_ip}:{request.url.path}"

        if limiter.is_rate_limited(ident, max_requests=limit, window_seconds=window_seconds):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Request rate limit exceeded. Please wait before making more requests.",
                headers={"Retry-After": str(window_seconds)},
            )

    return _rate_limiter_dependency

