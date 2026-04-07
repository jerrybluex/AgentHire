"""
Real tests for health check endpoints.

These tests verify the basic API functionality and connectivity.
"""

import pytest
from fastapi import status


@pytest.mark.integration
class TestHealthCheckReal:
    """Test health check endpoints with real API calls."""

    async def test_health_endpoint_returns_200(self, async_client):
        ""Test that health endpoint returns HTTP 200."""
        response = await async_client.get("/api/v1/health")
        assert response.status_code == status.HTTP_200_OK

    async def test_health_endpoint_returns_correct_structure(self, async_client):
        """Test that health endpoint returns expected JSON structure."""
        response = await async_client.get("/api/v1/health")
        data = response.json()

        # Check required fields exist
        assert "status" in data
        assert "version" in data
        assert "timestamp" in data

        # Check status is healthy
        assert data["status"] == "healthy"

        # Check version format (semantic versioning)
        version = data["version"]
        assert isinstance(version, str)
        parts = version.split(".")
        assert len(parts) >= 2  # At least major.minor

    async def test_health_endpoint_timestamp_is_recent(self, async_client):
        """Test that health endpoint timestamp is recent (within last minute)."""
        from datetime import datetime, timedelta

        response = await async_client.get("/api/v1/health")
        data = response.json()

        timestamp_str = data["timestamp"]
        timestamp = datetime.fromisoformat(timestamp_str)

        # Check timestamp is within last minute
        now = datetime.utcnow()
        diff = now - timestamp
        assert diff < timedelta(minutes=1), "Timestamp is not recent"


@pytest.mark.integration
class TestAPIErrorHandling:
    """Test API error responses return correct HTTP status codes."""

    async def test_404_endpoint_returns_not_found(self, async_client):
        ""Test that non-existent endpoint returns 404."""
        response = await async_client.get("/api/v1/nonexistent-endpoint-12345")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_invalid_method_returns_method_not_allowed(self, async_client):
        ""Test that invalid HTTP method returns 405."""
        response = await async_client.post("/api/v1/health")
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.unit
class TestRateLimiterConfig:
    """Test rate limit configuration is correct."""

    def test_rate_limit_tiers_defined(self):
        ""Test that rate limit tiers are properly configured."""
        from app.core.rate_limit import TIER_LIMITS, DEFAULT_LIMITS

        # Check default limits are reasonable
        assert DEFAULT_LIMITS.requests_per_minute > 0
        assert DEFAULT_LIMITS.requests_per_hour > 0
        assert DEFAULT_LIMITS.requests_per_day > 0

        # Check tier limits are ordered correctly
        pay_as_you_go = TIER_LIMITS["pay_as_you_go"]
        basic = TIER_LIMITS["monthly_basic"]
        pro = TIER_LIMITS["monthly_pro"]

        # Higher tiers should have higher limits
        assert basic.requests_per_hour > pay_as_you_go.requests_per_hour
        assert pro.requests_per_hour > basic.requests_per_hour

    def test_rate_limit_values_not_seconds(self):
        ""Test that rate limits are not accidentally set to seconds."""
        from app.core.rate_limit import DEFAULT_LIMITS

        # These were previously returning 3600, 86400 (seconds)
        assert DEFAULT_LIMITS.requests_per_hour != 3600
        assert DEFAULT_LIMITS.requests_per_day != 86400

        # Should be actual request counts
        assert DEFAULT_LIMITS.requests_per_hour <= 1000  # Reasonable limit
