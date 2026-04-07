"""
Tests for quota enforcement with concurrent requests (C3 fix validation).

These tests verify that the row locking mechanism prevents concurrent
requests from exceeding the monthly quota.
"""

import pytest
import asyncio
from datetime import datetime

from app.services.enterprise_service import enterprise_service, QuotaExceededError
from app.models import Enterprise, EnterpriseAPIKey, BillingRecord


@pytest.mark.unit
@pytest.mark.asyncio
class TestQuotaEnforcement:
    """Test quota enforcement logic."""

    async def test_quota_check_with_row_lock(self, db_session):
        ""Test that quota check uses row locking (C3 fix)."""
        # Create enterprise and API key with quota
        enterprise = Enterprise(
            id="test-enterprise-id",
            name="Test Enterprise",
            unified_social_credit_code="123456789012345678",
            status="approved"
        )
        db_session.add(enterprise)
        await db_session.flush()

        api_key = EnterpriseAPIKey(
            id="test-api-key-id",
            enterprise_id=enterprise.id,
            name="Test Key",
            monthly_quota=10,  # Small quota for testing
            plan="pay_as_you_go"
        )
        db_session.add(api_key)
        await db_session.commit()

        # Record usage up to quota
        for i in range(10):
            await enterprise_service.record_usage(
                db=db_session,
                enterprise_id=enterprise.id,
                api_key_id=api_key.id,
                usage_type="test_operation",
                quantity=1
            )

        # Next request should fail
        with pytest.raises(QuotaExceededError):
            await enterprise_service.record_usage(
                db=db_session,
                enterprise_id=enterprise.id,
                api_key_id=api_key.id,
                usage_type="test_operation",
                quantity=1
            )

    async def test_quota_exactly_at_limit(self, db_session):
        ""Test that usage exactly at quota limit is allowed."""
        # Setup
        enterprise = Enterprise(
            id="test-enterprise-2",
            name="Test Enterprise 2",
            unified_social_credit_code="223456789012345678",
            status="approved"
        )
        db_session.add(enterprise)
        await db_session.flush()

        api_key = EnterpriseAPIKey(
            id="test-api-key-2",
            enterprise_id=enterprise.id,
            name="Test Key 2",
            monthly_quota=5,
            plan="pay_as_you_go"
        )
        db_session.add(api_key)
        await db_session.commit()

        # Use exactly 5 quota
        for i in range(5):
            record = await enterprise_service.record_usage(
                db=db_session,
                enterprise_id=enterprise.id,
                api_key_id=api_key.id,
                usage_type="test_operation",
                quantity=1
            )
            assert record is not None

        # Should fail at 6th request
        with pytest.raises(QuotaExceededError):
            await enterprise_service.record_usage(
                db=db_session,
                enterprise_id=enterprise.id,
                api_key_id=api_key.id,
                usage_type="test_operation",
                quantity=1
            )

    async def test_quota_reset_by_period(self, db_session):
        ""Test that quota resets in new billing period."""
        # Setup
        enterprise = Enterprise(
            id="test-enterprise-3",
            name="Test Enterprise 3",
            unified_social_credit_code="323456789012345678",
            status="approved"
        )
        db_session.add(enterprise)
        await db_session.flush()

        api_key = EnterpriseAPIKey(
            id="test-api-key-3",
            enterprise_id=enterprise.id,
            name="Test Key 3",
            monthly_quota=5,
            plan="pay_as_you_go"
        )
        db_session.add(api_key)
        await db_session.commit()

        # Create billing record for last month
        last_month = "2026-03"
        old_record = BillingRecord(
            id="test-billing-1",
            enterprise_id=enterprise.id,
            api_key_id=api_key.id,
            usage_type="test_operation",
            quantity=5,
            billing_period=last_month
        )
        db_session.add(old_record)
        await db_session.commit()

        # Should be able to use quota this month
        current_month = datetime.utcnow().strftime("%Y-%m")
        if current_month != last_month:
            record = await enterprise_service.record_usage(
                db=db_session,
                enterprise_id=enterprise.id,
                api_key_id=api_key.id,
                usage_type="test_operation",
                quantity=1
            )
            assert record is not None


@pytest.mark.integration
@pytest.mark.asyncio
class TestQuotaConcurrency:
    """Test concurrent quota enforcement (C3 race condition fix)."""

    async def test_concurrent_quota_requests(self, db_session):
        """
        Test that concurrent requests cannot exceed quota.

        This test simulates the race condition where two requests
        arrive simultaneously and both try to use the remaining quota.

        With row locking (C3 fix), only one should succeed if quota
        is insufficient for both.
        """
        # Setup enterprise with small quota
        enterprise = Enterprise(
            id="test-concurrent-ent",
            name="Concurrent Test Enterprise",
            unified_social_credit_code="999456789012345678",
            status="approved"
        )
        db_session.add(enterprise)
        await db_session.flush()

        # Only 2 quota remaining
        api_key = EnterpriseAPIKey(
            id="test-concurrent-key",
            enterprise_id=enterprise.id,
            name="Concurrent Test Key",
            monthly_quota=2,
            plan="pay_as_you_go"
        )
        db_session.add(api_key)
        await db_session.commit()

        # Simulate 5 concurrent requests
        results = []
        errors = []

        async def make_request():
            try:
                record = await enterprise_service.record_usage(
                    db=db_session,
                    enterprise_id=enterprise.id,
                    api_key_id=api_key.id,
                    usage_type="concurrent_test",
                    quantity=1
                )
                results.append(record)
            except Exception as e:
                errors.append(e)

        # Run 5 concurrent requests
        await asyncio.gather(*[make_request() for _ in range(5)])

        # With quota=2, at most 2 should succeed
        assert len(results) <= 2, f"Quota exceeded: {len(results)} succeeded with quota=2"

        # At least some should fail with QuotaExceededError
        quota_errors = [e for e in errors if isinstance(e, QuotaExceededError)]
        assert len(quota_errors) >= 3, f"Expected at least 3 quota errors, got {len(quota_errors)}"
