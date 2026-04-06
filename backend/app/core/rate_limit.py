"""
API Rate Limiting using Redis-based sliding window algorithm.
Provides enterprise-level rate limiting with different tiers.
"""

import time
from typing import Optional, Tuple
from dataclasses import dataclass

import redis.asyncio as redis
from fastapi import Request, HTTPException, status

from app.config import get_settings


@dataclass
class RateLimitConfig:
    """Rate limit configuration for different enterprise tiers."""
    requests_per_minute: int
    requests_per_hour: int
    requests_per_day: int


# Enterprise tier rate limits
TIER_LIMITS = {
    "pay_as_you_go": RateLimitConfig(
        requests_per_minute=60,
        requests_per_hour=1000,
        requests_per_day=10000,
    ),
    "monthly_basic": RateLimitConfig(
        requests_per_minute=120,
        requests_per_hour=5000,
        requests_per_day=50000,
    ),
    "monthly_pro": RateLimitConfig(
        requests_per_minute=300,
        requests_per_hour=15000,
        requests_per_day=150000,
    ),
}

# Default rate limits for unauthenticated requests
DEFAULT_LIMITS = RateLimitConfig(
    requests_per_minute=20,
    requests_per_hour=200,
    requests_per_day=1000,
)


class RateLimitRedisClient:
    """
    Redis client for rate limiting with sliding window algorithm.
    Uses sorted sets to track request timestamps per client.
    """

    def __init__(self, redis_url: Optional[str] = None):
        settings = get_settings()
        self.redis_url = redis_url or str(settings.redis.url)
        self._client: Optional[redis.Redis] = None

    async def get_client(self) -> redis.Redis:
        """Get or create Redis client."""
        if self._client is None:
            self._client = redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
            )
        return self._client

    async def close(self):
        """Close Redis connection."""
        if self._client:
            await self._client.close()
            self._client = None

    async def is_allowed(
        self,
        key: str,
        limit: int,
        window_seconds: int,
    ) -> Tuple[bool, int]:
        """
        Check if request is allowed using sliding window algorithm.

        Args:
            key: Unique identifier (e.g., "rate:enterprise:ent_xxx")
            limit: Maximum requests allowed in window
            window_seconds: Time window in seconds

        Returns:
            Tuple of (is_allowed, remaining_requests)
        """
        client = await self.get_client()
        now = time.time()
        window_start = now - window_seconds

        pipe = client.pipeline()

        # Remove old entries outside the window
        pipe.zremrangebyscore(key, 0, window_start)

        # Count current requests in window
        pipe.zcard(key)

        # Add current request timestamp
        pipe.zadd(key, {str(now): now})

        # Set expiry on the key
        pipe.expire(key, window_seconds + 1)

        results = await pipe.execute()
        current_count = results[1]

        remaining = max(0, limit - current_count - 1)
        is_allowed = current_count < limit

        return is_allowed, remaining

    async def get_usage(self, key: str, window_seconds: int) -> int:
        """Get current usage count for a key within the window."""
        client = await self.get_client()
        now = time.time()
        window_start = now - window_seconds

        # Remove old entries and count current
        await client.zremrangebyscore(key, 0, window_start)
        return await client.zcard(key)


# Global Redis client instance
_rate_limit_redis: Optional[RateLimitRedisClient] = None


def get_rate_limit_redis() -> RateLimitRedisClient:
    """Get rate limit Redis client singleton."""
    global _rate_limit_redis
    if _rate_limit_redis is None:
        _rate_limit_redis = RateLimitRedisClient()
    return _rate_limit_redis


async def close_rate_limit_redis():
    """Close rate limit Redis connection."""
    global _rate_limit_redis
    if _rate_limit_redis:
        await _rate_limit_redis.close()
        _rate_limit_redis = None


class RateLimiter:
    """
    Rate limiter with sliding window algorithm.
    Supports per-enterprise and per-endpoint rate limiting.
    """

    def __init__(self):
        self.redis_client = get_rate_limit_redis()

    def _get_client_key(self, request: Request, enterprise_id: Optional[str] = None) -> str:
        """Generate rate limit key for client."""
        if enterprise_id:
            return f"rate:enterprise:{enterprise_id}"

        # Fallback to IP-based limiting
        client_ip = request.client.host if request.client else "unknown"
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            client_ip = forwarded.split(",")[0].strip()

        return f"rate:ip:{client_ip}"

    async def check_rate_limit(
        self,
        request: Request,
        enterprise_id: Optional[str] = None,
        plan: str = "pay_as_you_go",
    ) -> Tuple[bool, int, int]:
        """
        Check rate limit for a request.

        Args:
            request: FastAPI request
            enterprise_id: Enterprise ID if authenticated
            plan: Enterprise plan for rate limit tier

        Returns:
            Tuple of (is_allowed, remaining_requests, retry_after_seconds)
        """
        config = TIER_LIMITS.get(plan, DEFAULT_LIMITS)
        if not enterprise_id:
            config = DEFAULT_LIMITS

        key = self._get_client_key(request, enterprise_id)

        # Check minute limit first (most restrictive for burst protection)
        is_allowed, remaining = await self.redis_client.is_allowed(
            key + ":minute",
            config.requests_per_minute,
            60,
        )

        if not is_allowed:
            return False, 0, 60

        # Check hour limit
        is_allowed_hour, remaining_hour = await self.redis_client.is_allowed(
            key + ":hour",
            config.requests_per_hour,
            3600,
        )

        if not is_allowed_hour:
            return False, 0, 3600 - (time.time() % 3600)

        # Check day limit
        is_allowed_day, remaining_day = await self.redis_client.is_allowed(
            key + ":day",
            config.requests_per_day,
            86400,
        )

        if not is_allowed_day:
            return False, 0, 86400 - (time.time() % 86400)

        return True, min(remaining, remaining_hour, remaining_day), 0

    async def get_current_usage(
        self,
        request: Request,
        enterprise_id: Optional[str] = None,
    ) -> dict:
        """Get current rate limit usage for a client."""
        key = self._get_client_key(request, enterprise_id)

        minute_usage = await self.redis_client.get_usage(key + ":minute", 60)
        hour_usage = await self.redis_client.get_usage(key + ":hour", 3600)
        day_usage = await self.redis_client.get_usage(key + ":day", 86400)

        return {
            "minute": {"used": minute_usage, "limit": 60, "reset_in": 60},
            "hour": {"used": hour_usage, "limit": 3600, "reset_in": 3600 - int(time.time() % 3600)},
            "day": {"used": day_usage, "limit": 86400, "reset_in": 86400 - int(time.time() % 86400)},
        }


# Global rate limiter instance
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """Get rate limiter singleton."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter


async def rate_limit_dependency(
    request: Request,
    enterprise_id: Optional[str] = None,
    plan: str = "pay_as_you_go",
) -> Tuple[bool, int, int]:
    """
    FastAPI dependency for rate limiting.

    Usage:
        @app.get("/api/v1/jobs")
        async def get_jobs(
            request: Request,
            rate_limit: Tuple[bool, int, int] = Depends(rate_limit_dependency)
        ):
            is_allowed, remaining, retry_after = rate_limit
            ...
    """
    limiter = get_rate_limiter()
    return await limiter.check_rate_limit(request, enterprise_id, plan)


class RateLimitMiddleware:
    """
    FastAPI middleware for automatic rate limiting.
    Requires enterprise_id and plan to be set on request state.
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Let FastAPI handle this via dependency instead
        await self.app(scope, receive, send)


def raise_rate_limit_error(retry_after: int):
    """Raise HTTPException for rate limit exceeded."""
    raise HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail={
            "error": "rate_limit_exceeded",
            "message": "Too many requests. Please try again later.",
            "retry_after": retry_after,
        },
        headers={"Retry-After": str(retry_after)},
    )
