"""
Unit tests for Rate Limiting functionality.
Tests the sliding window algorithm and rate limit configuration.
"""

import pytest
import time
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Tuple


class TestRateLimitConfig:
    """Tests for rate limit configuration."""

    def test_tier_limits_defined(self):
        """Test that all enterprise tiers have rate limits defined."""
        from app.core.rate_limit import TIER_LIMITS, DEFAULT_LIMITS

        assert "pay_as_you_go" in TIER_LIMITS
        assert "monthly_basic" in TIER_LIMITS
        assert "monthly_pro" in TIER_LIMITS

    def test_pay_as_you_go_limits(self):
        """Test pay-as-you-go tier limits."""
        from app.core.rate_limit import TIER_LIMITS

        config = TIER_LIMITS["pay_as_you_go"]
        assert config.requests_per_minute == 60
        assert config.requests_per_hour == 1000
        assert config.requests_per_day == 10000

    def test_monthly_pro_limits(self):
        """Test monthly pro tier has highest limits."""
        from app.core.rate_limit import TIER_LIMITS

        config = TIER_LIMITS["monthly_pro"]
        assert config.requests_per_minute == 300
        assert config.requests_per_hour == 15000
        assert config.requests_per_day == 150000

    def test_default_limits_for_unauthenticated(self):
        """Test default limits for unauthenticated requests."""
        from app.core.rate_limit import DEFAULT_LIMITS

        assert DEFAULT_LIMITS.requests_per_minute == 20
        assert DEFAULT_LIMITS.requests_per_hour == 200
        assert DEFAULT_LIMITS.requests_per_day == 1000


class TestRateLimitRedisClient:
    """Tests for Redis client operations."""

    @pytest.fixture
    def mock_redis(self):
        """Create a mock Redis client."""
        with patch("app.core.rate_limit.redis") as mock:
            yield mock

    @pytest.fixture
    def rate_limit_redis(self, mock_redis):
        """Create RateLimitRedisClient with mocked Redis."""
        from app.core.rate_limit import RateLimitRedisClient

        client = RateLimitRedisClient(redis_url="redis://localhost:6379/0")
        return client

    @pytest.mark.asyncio
    async def test_is_allowed_under_limit(self, rate_limit_redis):
        """Test that requests under limit are allowed."""
        mock_client = AsyncMock()
        mock_pipe = AsyncMock()
        mock_pipe.execute.return_value = [None, 5, None, None]  # 5 requests so far
        mock_client.pipeline.return_value = mock_pipe

        rate_limit_redis._client = mock_client

        is_allowed, remaining = await rate_limit_redis.is_allowed(
            key="rate:test",
            limit=10,
            window_seconds=60,
        )

        assert is_allowed is True
        assert remaining == 4  # 10 - 5 - 1

    @pytest.mark.asyncio
    async def test_is_allowed_at_limit(self, rate_limit_redis):
        """Test that requests at limit are rejected."""
        mock_client = AsyncMock()
        mock_pipe = AsyncMock()
        mock_pipe.execute.return_value = [None, 10, None, None]  # At limit
        mock_client.pipeline.return_value = mock_pipe

        rate_limit_redis._client = mock_client

        is_allowed, remaining = await rate_limit_redis.is_allowed(
            key="rate:test",
            limit=10,
            window_seconds=60,
        )

        assert is_allowed is False
        assert remaining == 0

    @pytest.mark.asyncio
    async def test_get_usage(self, rate_limit_redis):
        """Test getting current usage count."""
        mock_client = AsyncMock()
        mock_client.zremrangebyscore = AsyncMock()
        mock_client.zcard = AsyncMock(return_value=5)

        rate_limit_redis._client = mock_client

        usage = await rate_limit_redis.get_usage("rate:test", 60)

        assert usage == 5
        mock_client.zremrangebyscore.assert_called_once()


class TestRateLimiter:
    """Tests for RateLimiter class."""

    @pytest.fixture
    def mock_redis_client(self):
        """Create mock Redis client for RateLimiter."""
        with patch("app.core.rate_limit.get_rate_limit_redis") as mock:
            redis_client = MagicMock()
            redis_client.is_allowed = AsyncMock(return_value=(True, 59))
            redis_client.get_usage = AsyncMock(return_value=1)
            mock.return_value = redis_client
            yield redis_client

    @pytest.fixture
    def rate_limiter(self, mock_redis_client):
        """Create RateLimiter with mocked dependencies."""
        from app.core.rate_limit import RateLimiter
        return RateLimiter()

    @pytest.fixture
    def mock_request(self):
        """Create a mock FastAPI request."""
        request = MagicMock()
        request.client.host = "127.0.0.1"
        request.headers.get.return_value = None
        request.state = MagicMock()
        return request

    @pytest.mark.asyncio
    async def test_check_rate_limit_authenticated(
        self, rate_limiter, mock_request, mock_redis_client
    ):
        """Test rate limiting for authenticated enterprise."""
        is_allowed, remaining, retry_after = await rate_limiter.check_rate_limit(
            request=mock_request,
            enterprise_id="ent_123",
            plan="monthly_pro",
        )

        assert is_allowed is True
        assert remaining >= 0
        assert retry_after == 0

    @pytest.mark.asyncio
    async def test_check_rate_limit_unauthenticated(
        self, rate_limiter, mock_request, mock_redis_client
    ):
        """Test rate limiting for unauthenticated requests."""
        is_allowed, remaining, retry_after = await rate_limiter.check_rate_limit(
            request=mock_request,
            enterprise_id=None,
        )

        assert is_allowed is True
        mock_redis_client.is_allowed.assert_called()

    @pytest.mark.asyncio
    async def test_get_client_key_with_enterprise(
        self, rate_limiter, mock_request
    ):
        """Test client key generation with enterprise ID."""
        key = rate_limiter._get_client_key(mock_request, "ent_123")
        assert key == "rate:enterprise:ent_123"

    @pytest.mark.asyncio
    async def test_get_client_key_without_enterprise(
        self, rate_limiter, mock_request
    ):
        """Test client key generation without enterprise ID (IP-based)."""
        key = rate_limiter._get_client_key(mock_request, None)
        assert key.startswith("rate:ip:")

    @pytest.mark.asyncio
    async def test_get_client_key_with_forwarded_header(
        self, rate_limiter, mock_request
    ):
        """Test client key uses X-Forwarded-For when present."""
        mock_request.headers.get.return_value = "203.0.113.195, 70.41.3.18"

        key = rate_limiter._get_client_key(mock_request, None)

        assert "203.0.113.195" in key

    @pytest.mark.asyncio
    async def test_get_current_usage(self, rate_limiter, mock_request):
        """Test getting current usage statistics."""
        usage = await rate_limiter.get_current_usage(mock_request, "ent_123")

        assert "minute" in usage
        assert "hour" in usage
        assert "day" in usage
        assert "used" in usage["minute"]
        assert "limit" in usage["minute"]


class TestRateLimitError:
    """Tests for rate limit error handling."""

    def test_raise_rate_limit_error(self):
        """Test rate limit error exception."""
        from app.core.rate_limit import raise_rate_limit_error
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            raise_rate_limit_error(60)

        assert exc_info.value.status_code == 429
        assert "retry_after" in exc_info.value.detail
        assert exc_info.value.detail["retry_after"] == 60
        assert "Retry-After" in exc_info.value.headers
