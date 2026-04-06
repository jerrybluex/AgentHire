"""
Health check endpoint tests.

Tests for the health check API endpoints.
"""

import pytest
from fastapi import status


@pytest.mark.unit
class TestHealthEndpoints:
    """Test suite for health check endpoints."""

    def test_health_check_returns_200(self, client):
        """
        Test that health check endpoint returns 200 OK.

        This is a basic smoke test to verify the API is running.
        """
        response = client.get("/health")

        assert response.status_code == status.HTTP_200_OK

    def test_health_check_returns_expected_structure(self, client):
        """
        Test that health check returns the expected response structure.

        Verifies the response contains required fields.
        """
        response = client.get("/health")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "status" in data
        assert data["status"] == "healthy"
        assert "version" in data

    def test_root_endpoint_returns_api_info(self, client):
        """
        Test that root endpoint returns API information.

        Verifies the root endpoint returns basic API metadata.
        """
        response = client.get("/")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "name" in data
        assert "version" in data
        assert "environment" in data


@pytest.mark.integration
class TestHealthIntegration:
    """Integration tests for health endpoints."""

    def test_health_api_endpoint(self, client):
        """
        Test the detailed health check API endpoint.

        This endpoint provides more detailed health information
        including service dependencies.
        """
        response = client.get("/api/v1/health")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "success" in data
        assert data["success"] is True
        assert "data" in data

        health_data = data["data"]
        assert "status" in health_data
        assert "version" in health_data
        assert "timestamp" in health_data
        assert "environment" in health_data
        assert "services" in health_data

    def test_health_ready_endpoint(self, client):
        """
        Test the readiness check endpoint.

        Used by Kubernetes to determine if the pod is ready
        to receive traffic.
        """
        response = client.get("/api/v1/health/ready")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "success" in data
        assert "data" in data
        assert data["data"]["status"] in ["ready", "not_ready"]

    def test_health_live_endpoint(self, client):
        """
        Test the liveness check endpoint.

        Used by Kubernetes to determine if the pod should
        be restarted.
        """
        response = client.get("/api/v1/health/live")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "success" in data
        assert "data" in data
        assert data["data"]["status"] == "alive"
