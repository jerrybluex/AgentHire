"""
Unit tests for EnterpriseService.
"""

import pytest
from datetime import datetime

from app.services.enterprise_service import EnterpriseService
from app.models import Enterprise, EnterpriseAPIKey, BillingRecord
from tests.factories import EnterpriseFactory, EnterpriseAPIKeyFactory


class TestEnterpriseService:
    """Tests for EnterpriseService."""

    @pytest.mark.asyncio
    async def test_create_application(self, db_session):
        """Test creating a new enterprise application."""
        service = EnterpriseService()

        enterprise = await service.create_application(
            db=db_session,
            company_name="Test Company",
            unified_social_credit_code="USCC123456789",
            contact={"email": "test@example.com", "phone": "1234567890"},
            certification={},
            company_info={"industry": "Tech", "website": "https://test.com"},
        )

        assert enterprise is not None
        assert enterprise.name == "Test Company"
        assert enterprise.status == "pending"
        assert enterprise.id.startswith("ent_")

    @pytest.mark.asyncio
    async def test_approve_enterprise(self, db_session):
        """Test approving an enterprise."""
        service = EnterpriseService()

        # Create enterprise
        enterprise = EnterpriseFactory.create(status="pending")
        db_session.add(enterprise)
        await db_session.flush()

        # Approve
        approved = await service.approve_enterprise(
            db=db_session,
            enterprise_id=enterprise.id,
            approved_by="admin",
        )

        assert approved is not None
        assert approved.status == "approved"
        assert approved.certification["verified_by"] == "admin"
        assert "verified_at" in approved.certification

    @pytest.mark.asyncio
    async def test_create_api_key(self, db_session):
        """Test creating an API key for approved enterprise."""
        service = EnterpriseService()

        # Create and approve enterprise
        enterprise = EnterpriseFactory.create(status="approved")
        db_session.add(enterprise)
        await db_session.flush()

        # Create API key
        result = await service.create_api_key(
            db=db_session,
            enterprise_id=enterprise.id,
            name="Production Key",
            plan="pay_as_you_go",
            rate_limit=100,
        )

        assert result is not None
        assert "api_key" in result
        assert result["api_key"].startswith("ah_")
        assert result["name"] == "Production Key"

    @pytest.mark.asyncio
    async def test_create_api_key_fails_for_pending_enterprise(self, db_session):
        """Test that API key creation fails for non-approved enterprise."""
        service = EnterpriseService()

        # Create pending enterprise
        enterprise = EnterpriseFactory.create(status="pending")
        db_session.add(enterprise)
        await db_session.flush()

        # Try to create API key - should fail
        result = await service.create_api_key(
            db=db_session,
            enterprise_id=enterprise.id,
            name="Test Key",
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_validate_api_key(self, db_session):
        """Test API key validation."""
        service = EnterpriseService()

        # Create approved enterprise and API key
        enterprise = EnterpriseFactory.create(status="approved")
        db_session.add(enterprise)
        await db_session.flush()

        api_key_obj, raw_key = EnterpriseAPIKeyFactory.create(
            enterprise_id=enterprise.id,
            status="active",
        )
        db_session.add(api_key_obj)
        await db_session.flush()

        # Validate
        result = await service.validate_api_key(db_session, raw_key)

        assert result is not None
        assert result[0] == enterprise.id
        assert result[1] == api_key_obj.id

    @pytest.mark.asyncio
    async def test_validate_invalid_api_key(self, db_session):
        """Test that invalid API key returns None."""
        service = EnterpriseService()

        result = await service.validate_api_key(db_session, "invalid_key")

        assert result is None

    @pytest.mark.asyncio
    async def test_validate_expired_api_key(self, db_session):
        """Test that expired API key returns None."""
        service = EnterpriseService()

        # Create enterprise
        enterprise = EnterpriseFactory.create(status="approved")
        db_session.add(enterprise)
        await db_session.flush()

        # Create expired API key
        api_key_obj, raw_key = EnterpriseAPIKeyFactory.create(
            enterprise_id=enterprise.id,
            status="active",
        )
        api_key_obj.expires_at = datetime.utcnow()
        db_session.add(api_key_obj)
        await db_session.flush()

        # Validate - should fail
        result = await service.validate_api_key(db_session, raw_key)

        assert result is None

    @pytest.mark.asyncio
    async def test_record_usage(self, db_session):
        """Test recording API usage."""
        service = EnterpriseService()

        # Create enterprise and API key
        enterprise = EnterpriseFactory.create(status="approved")
        db_session.add(enterprise)
        await db_session.flush()

        api_key_obj, _ = EnterpriseAPIKeyFactory.create(enterprise_id=enterprise.id)
        db_session.add(api_key_obj)
        await db_session.flush()

        # Record usage
        record = await service.record_usage(
            db=db_session,
            enterprise_id=enterprise.id,
            api_key_id=api_key_obj.id,
            usage_type="job_post",
            quantity=1,
            reference_id="job_123",
        )

        assert record is not None
        assert record.usage_type == "job_post"
        assert record.quantity == 1
        assert record.unit_price == 0.5  # From _get_unit_price
        assert record.amount == 0.5

    @pytest.mark.asyncio
    async def test_get_billing_records(self, db_session):
        """Test retrieving billing records."""
        service = EnterpriseService()

        # Create enterprise
        enterprise = EnterpriseFactory.create(status="approved")
        db_session.add(enterprise)
        await db_session.flush()

        # Create billing records
        from tests.factories import BillingRecordFactory

        for i in range(3):
            record = BillingRecordFactory.create(
                enterprise_id=enterprise.id,
                api_key_id="key_test",
                usage_type="job_post",
                amount=0.5,
            )
            db_session.add(record)
        await db_session.flush()

        # Get records
        records, total = await service.get_billing_records(
            db=db_session,
            enterprise_id=enterprise.id,
        )

        assert len(records) == 3
        assert total == 1.5

    def test_get_unit_price(self):
        """Test unit pricing for different usage types."""
        service = EnterpriseService()

        assert service._get_unit_price("job_post") == 0.5
        assert service._get_unit_price("match_query") == 0.1
        assert service._get_unit_price("match_success") == 1.0
        assert service._get_unit_price("profile_view") == 0.1
        assert service._get_unit_price("unknown") == 0.0
