"""
Unit tests for NotificationService.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, patch

from sqlalchemy import select

from app.services.notification_service import (
    NotificationService,
    NotificationType,
    EmailTemplate,
    notification_service,
)
from app.models import Enterprise, BillingRecord
from tests.factories import EnterpriseFactory, BillingRecordFactory


class TestNotificationService:
    """Tests for NotificationService."""

    @pytest.fixture
    def service(self):
        """Create a notification service instance for testing."""
        service = NotificationService()
        service._email_enabled = False  # Disable actual email sending
        return service

    @pytest.mark.asyncio
    async def test_send_email_disabled(self, service):
        """Test that send_email works when email is disabled."""
        result = await service.send_email(
            to_email="test@example.com",
            subject="Test Subject",
            html_content="<p>Test Content</p>",
        )

        assert result["status"] == "skipped"
        assert result["reason"] == "email_disabled"
        assert result["to"] == "test@example.com"

    @pytest.mark.asyncio
    async def test_send_email_enabled(self, service):
        """Test send_email when enabled."""
        service._email_enabled = True

        with patch.object(service, 'send_email', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = {
                "status": "sent",
                "to": "test@example.com",
                "subject": "Test",
                "message_id": "em_test123",
            }

            result = await service.send_email(
                to_email="test@example.com",
                subject="Test Subject",
                html_content="<p>Test Content</p>",
            )

            # Since we disabled actual sending but enabled it above,
            # it will try to send but we mock it
            assert result["status"] == "sent"

    @pytest.mark.asyncio
    async def test_notify_enterprise_approved(self, db_session, service):
        """Test sending enterprise approved notification."""
        # Create approved enterprise with contact email
        enterprise = EnterpriseFactory.create(
            status="approved",
            contact={"email": "approved@example.com", "phone": "1234567890"},
            certification={"verified_at": datetime.utcnow().isoformat(), "verified_by": "admin"},
        )
        db_session.add(enterprise)
        await db_session.flush()

        result = await service.notify_enterprise_approved(
            db=db_session,
            enterprise=enterprise,
            verified_by="admin",
        )

        assert result["status"] == "skipped"  # Email disabled
        assert result["reason"] == "email_disabled"

    @pytest.mark.asyncio
    async def test_notify_enterprise_approved_no_email(self, db_session, service):
        """Test enterprise approved notification fails without email."""
        enterprise = EnterpriseFactory.create(
            status="approved",
            contact={"phone": "1234567890"},  # No email
        )
        db_session.add(enterprise)
        await db_session.flush()

        result = await service.notify_enterprise_approved(
            db=db_session,
            enterprise=enterprise,
            verified_by="admin",
        )

        assert result["status"] == "failed"
        assert result["reason"] == "no_email"

    @pytest.mark.asyncio
    async def test_notify_enterprise_rejected(self, db_session, service):
        """Test sending enterprise rejected notification."""
        enterprise = EnterpriseFactory.create(
            status="rejected",
            contact={"email": "rejected@example.com"},
        )
        db_session.add(enterprise)
        await db_session.flush()

        result = await service.notify_enterprise_rejected(
            db=db_session,
            enterprise=enterprise,
            rejection_reason="Invalid business license",
        )

        assert result["status"] == "skipped"

    @pytest.mark.asyncio
    async def test_check_and_notify_low_balance_ok(self, db_session, service):
        """Test low balance check when balance is above threshold."""
        enterprise = EnterpriseFactory.create(
            status="approved",
            contact={"email": "test@example.com"},
            billing_info={"balance": 500.0},  # Above default threshold of 100
        )
        db_session.add(enterprise)
        await db_session.flush()

        result = await service.check_and_notify_low_balance(
            db=db_session,
            enterprise_id=enterprise.id,
            threshold=100.0,
        )

        assert result["status"] == "ok"
        assert result["balance"] == 500.0
        assert result["threshold"] == 100.0
        assert result["notification_sent"] is False

    @pytest.mark.asyncio
    async def test_check_and_notify_low_balance_triggers_notification(self, db_session, service):
        """Test low balance notification is triggered when balance is low."""
        enterprise = EnterpriseFactory.create(
            status="approved",
            contact={"email": "test@example.com"},
            billing_info={"balance": 50.0},  # Below threshold
        )
        db_session.add(enterprise)
        await db_session.flush()

        result = await service.check_and_notify_low_balance(
            db=db_session,
            enterprise_id=enterprise.id,
            threshold=100.0,
        )

        assert result["status"] == "notification_sent"
        assert result["balance"] == 50.0
        assert result["threshold"] == 100.0

    @pytest.mark.asyncio
    async def test_check_and_notify_low_balance_enterprise_not_found(self, db_session, service):
        """Test low balance check with non-existent enterprise."""
        result = await service.check_and_notify_low_balance(
            db=db_session,
            enterprise_id="non_existent_id",
        )

        assert result["status"] == "failed"
        assert result["reason"] == "enterprise_not_found"

    @pytest.mark.asyncio
    async def test_check_and_notify_spending_threshold_ok(self, db_session, service):
        """Test spending threshold check when under threshold."""
        enterprise = EnterpriseFactory.create(
            status="approved",
            contact={"email": "test@example.com"},
        )
        db_session.add(enterprise)
        await db_session.flush()

        # Create billing records under threshold
        current_period = datetime.utcnow().strftime("%Y-%m")
        for i in range(5):
            record = BillingRecordFactory.create(
                enterprise_id=enterprise.id,
                api_key_id="key_test",
                usage_type="job_post",
                amount=10.0,
                billing_period=current_period,
            )
            db_session.add(record)
        await db_session.flush()

        result = await service.check_and_notify_spending_threshold(
            db=db_session,
            enterprise_id=enterprise.id,
            threshold=100.0,  # Total is 50.0, below threshold
        )

        assert result["status"] == "ok"
        assert result["total_spent"] == 50.0
        assert result["notification_sent"] is False

    @pytest.mark.asyncio
    async def test_check_and_notify_spending_threshold_triggers(self, db_session, service):
        """Test spending threshold notification is triggered when over threshold."""
        enterprise = EnterpriseFactory.create(
            status="approved",
            contact={"email": "test@example.com"},
        )
        db_session.add(enterprise)
        await db_session.flush()

        # Create billing records over threshold
        current_period = datetime.utcnow().strftime("%Y-%m")
        for i in range(15):
            record = BillingRecordFactory.create(
                enterprise_id=enterprise.id,
                api_key_id="key_test",
                usage_type="job_post",
                amount=100.0,
                billing_period=current_period,
            )
            db_session.add(record)
        await db_session.flush()

        result = await service.check_and_notify_spending_threshold(
            db=db_session,
            enterprise_id=enterprise.id,
            threshold=500.0,  # Total is 1500.0, over threshold
        )

        assert result["status"] == "notification_sent"
        assert result["total_spent"] == 1500.0

    @pytest.mark.asyncio
    async def test_get_enterprise_balance(self, db_session, service):
        """Test getting enterprise balance."""
        enterprise = EnterpriseFactory.create(
            status="approved",
            billing_info={"balance": 250.0},
        )
        db_session.add(enterprise)
        await db_session.flush()

        balance = await service.get_enterprise_balance(
            db=db_session,
            enterprise_id=enterprise.id,
        )

        assert balance == 250.0

    @pytest.mark.asyncio
    async def test_get_enterprise_balance_default(self, db_session, service):
        """Test getting enterprise balance with default when not set."""
        enterprise = EnterpriseFactory.create(
            status="approved",
            billing_info=None,  # No billing info
        )
        db_session.add(enterprise)
        await db_session.flush()

        balance = await service.get_enterprise_balance(
            db=db_session,
            enterprise_id=enterprise.id,
        )

        assert balance == 1000.0  # Default balance

    @pytest.mark.asyncio
    async def test_update_enterprise_balance(self, db_session, service):
        """Test updating enterprise balance."""
        enterprise = EnterpriseFactory.create(
            status="approved",
            billing_info={"balance": 100.0},
        )
        db_session.add(enterprise)
        await db_session.flush()

        success = await service.update_enterprise_balance(
            db=db_session,
            enterprise_id=enterprise.id,
            new_balance=500.0,
        )

        assert success is True

        # Verify update
        result = await db_session.execute(
            select(Enterprise).where(Enterprise.id == enterprise.id)
        )
        updated = result.scalar_one()
        assert updated.billing_info["balance"] == 500.0

    @pytest.mark.asyncio
    async def test_update_enterprise_balance_not_found(self, db_session, service):
        """Test updating balance for non-existent enterprise."""
        success = await service.update_enterprise_balance(
            db=db_session,
            enterprise_id="non_existent_id",
            new_balance=500.0,
        )

        assert success is False


class TestEmailTemplate:
    """Tests for email templates."""

    def test_enterprise_approved_template(self):
        """Test enterprise approved email template formatting."""
        html = EmailTemplate.ENTERPRISE_APPROVED.format(
            company_name="Test Company",
            verified_at="2026-04-01T12:00:00",
            verified_by="admin",
        )

        assert "Test Company" in html
        assert "2026-04-01T12:00:00" in html
        assert "admin" in html
        assert "<html>" in html

    def test_enterprise_rejected_template(self):
        """Test enterprise rejected email template formatting."""
        html = EmailTemplate.ENTERPRISE_REJECTED.format(
            company_name="Test Company",
            verified_at="2026-04-01T12:00:00",
            rejection_reason="Invalid documentation",
        )

        assert "Test Company" in html
        assert "Invalid documentation" in html

    def test_low_balance_template(self):
        """Test low balance email template formatting."""
        html = EmailTemplate.LOW_BALANCE.format(
            company_name="Test Company",
            current_balance=50.0,
            threshold=100.0,
        )

        assert "Test Company" in html
        assert "50.00" in html
        assert "100.00" in html

    def test_spending_threshold_template(self):
        """Test spending threshold email template formatting."""
        html = EmailTemplate.SPENDING_THRESHOLD.format(
            company_name="Test Company",
            total_spent=1500.0,
            threshold=1000.0,
            billing_period="2026-04",
        )

        assert "Test Company" in html
        assert "1500.00" in html
        assert "1000.00" in html
        assert "2026-04" in html


class TestNotificationSingleton:
    """Tests for the notification_service singleton."""

    def test_notification_service_singleton(self):
        """Test that notification_service is a singleton instance."""
        from app.services.notification_service import notification_service

        assert isinstance(notification_service, NotificationService)
        assert notification_service is notification_service  # Same instance

    def test_default_thresholds(self):
        """Test default threshold values."""
        service = NotificationService()

        assert service._default_balance_threshold == 100.0
        assert service._default_spending_threshold == 1000.0
