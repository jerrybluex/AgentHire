"""
Unit tests for WebhookService.
"""

import pytest
import hmac
import hashlib
import json
from datetime import datetime

from app.services.webhook_service import WebhookService
from app.models import Webhook, WebhookDelivery
from tests.factories import EnterpriseFactory, WebhookFactory


class TestWebhookService:
    """Tests for WebhookService."""

    @pytest.mark.asyncio
    async def test_register_webhook(self, db_session):
        """Test registering a webhook."""
        service = WebhookService()

        # Create enterprise
        enterprise = EnterpriseFactory.create()
        db_session.add(enterprise)
        await db_session.flush()

        # Register webhook
        result = await service.register_webhook(
            db=db_session,
            enterprise_id=enterprise.id,
            url="https://example.com/webhook",
            events=["job.new", "profile.new"],
            secret=None,  # Auto-generate
        )

        assert result is not None
        assert result["url"] == "https://example.com/webhook"
        assert "job.new" in result["events"]
        assert "profile.new" in result["events"]
        assert result["secret"] is not None
        assert result["active"] is True

    @pytest.mark.asyncio
    async def test_register_webhook_with_custom_secret(self, db_session):
        """Test registering webhook with custom secret."""
        service = WebhookService()

        enterprise = EnterpriseFactory.create()
        db_session.add(enterprise)
        await db_session.flush()

        result = await service.register_webhook(
            db=db_session,
            enterprise_id=enterprise.id,
            url="https://example.com/webhook",
            events=["*"],
            secret="custom_secret_123",
        )

        assert result["secret"] == "custom_secret_123"

    @pytest.mark.asyncio
    async def test_unregister_webhook(self, db_session):
        """Test unregistering a webhook."""
        service = WebhookService()

        # Create enterprise and webhook
        enterprise = EnterpriseFactory.create()
        db_session.add(enterprise)
        await db_session.flush()

        webhook = WebhookFactory.create(enterprise_id=enterprise.id)
        db_session.add(webhook)
        await db_session.flush()

        # Unregister
        result = await service.unregister_webhook(
            db=db_session,
            enterprise_id=enterprise.id,
            webhook_id=webhook.id,
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_unregister_webhook_not_found(self, db_session):
        """Test unregistering non-existent webhook."""
        service = WebhookService()

        enterprise = EnterpriseFactory.create()
        db_session.add(enterprise)
        await db_session.flush()

        result = await service.unregister_webhook(
            db=db_session,
            enterprise_id=enterprise.id,
            webhook_id="nonexistent",
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_get_webhooks(self, db_session):
        """Test getting webhooks for an enterprise."""
        service = WebhookService()

        # Create enterprise and webhooks
        enterprise = EnterpriseFactory.create()
        db_session.add(enterprise)
        await db_session.flush()

        webhook1 = WebhookFactory.create(enterprise_id=enterprise.id)
        webhook2 = WebhookFactory.create(enterprise_id=enterprise.id)
        db_session.add(webhook1)
        db_session.add(webhook2)
        await db_session.flush()

        # Get webhooks
        result = await service.get_webhooks(db_session, enterprise.id)

        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_get_active_webhooks_for_event(self, db_session):
        """Test getting active webhooks for a specific event."""
        service = WebhookService()

        # Create enterprise
        enterprise = EnterpriseFactory.create()
        db_session.add(enterprise)
        await db_session.flush()

        # Create webhooks
        webhook1 = WebhookFactory.create(
            enterprise_id=enterprise.id,
            events=["job.new", "profile.new"],
            active=True,
        )
        webhook2 = WebhookFactory.create(
            enterprise_id=enterprise.id,
            events=["enterprise.approved"],
            active=True,
        )
        webhook3 = WebhookFactory.create(
            enterprise_id=enterprise.id,
            events=["job.new"],
            active=False,
        )
        db_session.add(webhook1)
        db_session.add(webhook2)
        db_session.add(webhook3)
        await db_session.flush()

        # Get active webhooks for job.new
        result = await service.get_active_webhooks_for_event(
            db_session, enterprise.id, "job.new"
        )

        assert len(result) == 1
        assert result[0].id == webhook1.id

    @pytest.mark.asyncio
    async def test_get_active_webhooks_for_event_wildcard(self, db_session):
        """Test that wildcard (*) matches all events."""
        service = WebhookService()

        # Create enterprise
        enterprise = EnterpriseFactory.create()
        db_session.add(enterprise)
        await db_session.flush()

        # Create webhook with wildcard
        webhook = WebhookFactory.create(
            enterprise_id=enterprise.id,
            events=["*"],
            active=True,
        )
        db_session.add(webhook)
        await db_session.flush()

        # Should match any event
        result = await service.get_active_webhooks_for_event(
            db_session, enterprise.id, "any_event"
        )

        assert len(result) == 1

    def test_build_payload(self):
        """Test building webhook payload."""
        service = WebhookService()

        payload = service._build_payload(
            event="job.new",
            data={"job_id": "job_123", "title": "Engineer"},
        )

        assert payload["event"] == "job.new"
        assert "timestamp" in payload
        assert payload["data"]["job_id"] == "job_123"

    def test_sign_payload(self):
        """Test signing webhook payload."""
        service = WebhookService()

        payload = {"event": "job.new", "timestamp": "2026-04-01T00:00:00", "data": {}}
        secret = "test_secret"

        signature = service._sign_payload(payload, secret)

        # Verify signature
        expected = hmac.new(
            secret.encode(),
            json.dumps(payload, sort_keys=True).encode(),
            hashlib.sha256,
        ).hexdigest()

        assert signature == expected

    def test_verify_signature(self):
        """Test signature verification."""
        service = WebhookService()

        payload = {"event": "job.new", "timestamp": "2026-04-01T00:00:00", "data": {}}
        secret = "test_secret"

        # Create signature
        body = json.dumps(payload, sort_keys=True)
        signature = "sha256=" + hmac.new(
            secret.encode(),
            body.encode(),
            hashlib.sha256,
        ).hexdigest()

        # Verify
        result = service.verify_signature(
            payload=body.encode(),
            signature=signature,
            secret=secret,
        )

        assert result is True

    def test_verify_signature_invalid(self):
        """Test that invalid signature fails verification."""
        service = WebhookService()

        payload = {"event": "job.new", "timestamp": "2026-04-01T00:00:00", "data": {}}
        secret = "test_secret"

        # Create wrong signature
        signature = "sha256=invalid_signature"

        result = service.verify_signature(
            payload=json.dumps(payload, sort_keys=True).encode(),
            signature=signature,
            secret=secret,
        )

        assert result is False

    def test_event_constants(self):
        """Test event type constants."""
        service = WebhookService()

        assert service.EVENT_JOB_NEW == "job.new"
        assert service.EVENT_PROFILE_NEW == "profile.new"
        assert service.EVENT_ENTERPRISE_APPROVED == "enterprise.approved"
        assert service.EVENT_ENTERPRISE_REJECTED == "enterprise.rejected"
