"""Rate limiting middleware for FastAPI using Redis backend."""

from __future__ import annotations

import logging
import os
import time
from typing import Callable, Optional

import redis.asyncio as redis
from fastapi import HTTPException, Request, Response, status
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

# How many proxies in front of us append to X-Forwarded-For (Cloud Run's front end adds one).
TRUSTED_PROXY_HOPS = int(os.getenv("TRUSTED_PROXY_HOPS", "1" if os.getenv("K_SERVICE") else "0"))


def client_ip(request: Request) -> str:
    """Real client IP. The left of X-Forwarded-For is whatever the client sent, so only the
    entry added by our own trusted proxy (counting from the right) can be believed."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded and TRUSTED_PROXY_HOPS > 0:
        hops = [h.strip() for h in forwarded.split(",") if h.strip()]
        if len(hops) >= TRUSTED_PROXY_HOPS:
            return hops[-TRUSTED_PROXY_HOPS]
    return request.client.host if request.client else "unknown"


def user_id_from_token(request: Request) -> Optional[str]:
    """Verified user id from the Bearer token, or None (bad or missing tokens count as anonymous)."""
    header = request.headers.get("Authorization", "")
    if not header.lower().startswith("bearer "):
        return None
    try:
        from app.core.auth import token_validator

        claims = token_validator.verify_token(header[7:].strip())
        return claims.get("sub") or claims.get("uid")
    except Exception:
        return None


class RateLimiter:
    """
    Rate limiter using Redis for distributed rate limiting.

    Implements token bucket algorithm with sliding window for accurate rate limiting.
    """

    def __init__(
        self,
        redis_url: str,
        default_limit: int = 100,
        window_seconds: int = 60,
        enabled: bool = True,
    ):
        """
        Initialize rate limiter.

        Args:
            redis_url: Redis connection URL
            default_limit: Default number of requests allowed per window
            window_seconds: Time window in seconds
            enabled: Whether rate limiting is enabled
        """
        self.redis_url = redis_url
        self.default_limit = default_limit
        self.window_seconds = window_seconds
        self.enabled = enabled
        self.redis_client: Optional[redis.Redis] = None

    async def init(self):
        """Initialize Redis connection."""
        if self.enabled:
            try:
                self.redis_client = redis.from_url(
                    self.redis_url, encoding="utf-8", decode_responses=True
                )
                await self.redis_client.ping()
                logger.info("Rate limiter Redis connection established")
            except Exception as e:
                logger.error(f"Failed to connect to Redis for rate limiting: {e}")
                self.enabled = False

    async def close(self):
        """Close Redis connection."""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Rate limiter Redis connection closed")

    def _get_identifier(self, request: Request) -> str:
        """
        Get unique identifier for rate limiting.

        Priority:
        1. User ID from auth token (if authenticated)
        2. IP address (for public endpoints)

        Args:
            request: FastAPI request object

        Returns:
            Unique identifier string
        """
        # Try to get user ID from request state (set by auth middleware)
        user_id = getattr(request.state, "user_id", None)
        if user_id:
            return f"user:{user_id}"

        return f"ip:{client_ip(request)}"

    def _get_rate_limit_key(self, identifier: str, endpoint: str) -> str:
        """
        Generate Redis key for rate limiting.

        Args:
            identifier: User/IP identifier
            endpoint: API endpoint path

        Returns:
            Redis key string
        """
        return f"rate_limit:{identifier}:{endpoint}"

    async def check_rate_limit(
        self, request: Request, limit: Optional[int] = None, window: Optional[int] = None
    ) -> tuple[bool, dict]:
        """
        Check if request is within rate limit.

        Args:
            request: FastAPI request object
            limit: Custom limit (overrides default)
            window: Custom window in seconds (overrides default)

        Returns:
            Tuple of (is_allowed, rate_limit_info)
        """
        if not self.enabled or not self.redis_client:
            return True, {}

        limit = limit or self.default_limit
        window = window or self.window_seconds

        identifier = self._get_identifier(request)
        endpoint = request.url.path
        key = self._get_rate_limit_key(identifier, endpoint)

        try:
            current_time = int(time.time())
            window_start = current_time - window

            # Use Redis pipeline for atomic operations
            pipe = self.redis_client.pipeline()

            # Remove old entries outside the window
            pipe.zremrangebyscore(key, 0, window_start)

            # Count requests in current window
            pipe.zcard(key)

            # Add current request
            pipe.zadd(key, {str(current_time): current_time})

            # Set expiry on the key
            pipe.expire(key, window + 10)

            # Execute pipeline
            results = await pipe.execute()
            request_count = results[1]  # Count from zcard

            # Check if limit exceeded
            is_allowed = request_count < limit

            # Calculate reset time
            reset_time = current_time + window

            rate_limit_info = {
                "limit": limit,
                "remaining": max(0, limit - request_count - 1),
                "reset": reset_time,
                "window": window,
            }

            return is_allowed, rate_limit_info

        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            # On error, allow the request (fail open)
            return True, {}

    def get_middleware(
        self,
        limit: Optional[int] = None,
        window: Optional[int] = None,
        public_limit: Optional[int] = None,
    ) -> Callable:
        """
        Create rate limiting middleware.

        Args:
            limit: Rate limit for authenticated users
            window: Time window in seconds
            public_limit: Rate limit for public/unauthenticated requests

        Returns:
            Middleware function
        """

        async def rate_limit_middleware(request: Request, call_next: Callable) -> Response:
            """Rate limiting middleware function."""

            # Skip rate limiting for health check endpoints
            if request.url.path in ["/health", "/", "/docs", "/redoc", "/openapi.json"]:
                return await call_next(request)

            # Middleware runs before route auth, so identify signed-in users from the token here.
            if getattr(request.state, "user_id", None) is None:
                request.state.user_id = user_id_from_token(request)
            user_id = request.state.user_id
            is_authenticated = user_id is not None

            # Use different limits for authenticated vs public
            effective_limit = limit if is_authenticated else (public_limit or 20)

            # Check rate limit
            is_allowed, rate_info = await self.check_rate_limit(
                request, limit=effective_limit, window=window
            )

            if not is_allowed:
                # Rate limit exceeded
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "detail": "Rate limit exceeded. Please try again later.",
                        "limit": rate_info.get("limit"),
                        "reset": rate_info.get("reset"),
                        "window": rate_info.get("window"),
                    },
                    headers={
                        "X-RateLimit-Limit": str(rate_info.get("limit", "")),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(rate_info.get("reset", "")),
                        "Retry-After": str(rate_info.get("window", 60)),
                    },
                )

            # Add rate limit headers to response
            response = await call_next(request)

            if rate_info:
                response.headers["X-RateLimit-Limit"] = str(rate_info.get("limit", ""))
                response.headers["X-RateLimit-Remaining"] = str(rate_info.get("remaining", ""))
                response.headers["X-RateLimit-Reset"] = str(rate_info.get("reset", ""))

            return response

        return rate_limit_middleware


# Global rate limiter instance
_rate_limiter: Optional[RateLimiter] = None


def init_rate_limiter(
    redis_url: str, default_limit: int = 100, window_seconds: int = 60, enabled: bool = True
) -> RateLimiter:
    """
    Initialize global rate limiter instance.

    Args:
        redis_url: Redis connection URL
        default_limit: Default requests per window
        window_seconds: Time window in seconds
        enabled: Whether rate limiting is enabled

    Returns:
        RateLimiter instance
    """
    global _rate_limiter
    _rate_limiter = RateLimiter(
        redis_url=redis_url,
        default_limit=default_limit,
        window_seconds=window_seconds,
        enabled=enabled,
    )
    return _rate_limiter


def get_rate_limiter() -> Optional[RateLimiter]:
    """Get global rate limiter instance."""
    return _rate_limiter
