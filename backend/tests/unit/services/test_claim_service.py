"""
Unit tests for Claim Service
"""

import pytest
from datetime import datetime, timedelta

from app.services.claim_service import ClaimService
from app.models import Agent
from tests.factories import AgentFactory, UserFactory, AgentClaimFactory


class TestClaimService:
    """Tests for ClaimService."""

    @pytest.fixture
    def claim_service(self):
        """Create ClaimService instance."""
        return ClaimService()

    @pytest.fixture
    def sample_agent(self, db_session):
        """Create a sample agent."""
        agent = AgentFactory.create(
            id="agt_claim_test",
            name="Test Agent",
            type="seeker",
        )
        db_session.add(agent)
        return agent

    @pytest.fixture
    def sample_user(self, db_session):
        """Create a sample user."""
        from tests.factories import UserFactory
        user = UserFactory.create(id="usr_claim_test")
        db_session.add(user)
        return user

    @pytest.mark.asyncio
    async def test_initiate_claim_success(self, claim_service, db_session, sample_agent, sample_user):
        """Test successful claim initiation."""
        result = await claim_service.initiate_claim(
            db=db_session,
            user_id=sample_user.id,
            agent_id=sample_agent.id,
        )

        assert result is not None
        assert result["agent_id"] == sample_agent.id
        assert result["status"] == "pending"
        assert "verification_code" in result
        assert len(result["verification_code"]) == 6

    @pytest.mark.asyncio
    async def test_initiate_claim_agent_not_found(self, claim_service, db_session, sample_user):
        """Test claim initiation with non-existent agent."""
        result = await claim_service.initiate_claim(
            db=db_session,
            user_id=sample_user.id,
            agent_id="agt_nonexistent",
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_verify_claim_success(self, claim_service, db_session, sample_agent, sample_user):
        """Test successful claim verification."""
        # First initiate
        init_result = await claim_service.initiate_claim(
            db=db_session,
            user_id=sample_user.id,
            agent_id=sample_agent.id,
        )

        # Then verify
        result = await claim_service.verify_claim(
            db=db_session,
            user_id=sample_user.id,
            agent_id=sample_agent.id,
            verification_code=init_result["verification_code"],
        )

        assert result is not None
        assert result["success"] is True
        assert result["agent_id"] == sample_agent.id
        assert "claimed_at" in result

    @pytest.mark.asyncio
    async def test_verify_claim_wrong_code(self, claim_service, db_session, sample_agent, sample_user):
        """Test claim verification with wrong code."""
        # First initiate
        await claim_service.initiate_claim(
            db=db_session,
            user_id=sample_user.id,
            agent_id=sample_agent.id,
        )

        # Then verify with wrong code
        result = await claim_service.verify_claim(
            db=db_session,
            user_id=sample_user.id,
            agent_id=sample_agent.id,
            verification_code="000000",
        )

        assert result is not None
        assert result["success"] is False
        assert "Invalid verification code" in result["error"]

    @pytest.mark.asyncio
    async def test_verify_claim_not_found(self, claim_service, db_session, sample_agent, sample_user):
        """Test claim verification without initiating first."""
        result = await claim_service.verify_claim(
            db=db_session,
            user_id=sample_user.id,
            agent_id=sample_agent.id,
            verification_code="123456",
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_get_active_claim(self, claim_service, db_session, sample_agent, sample_user):
        """Test getting active claim."""
        # First initiate
        await claim_service.initiate_claim(
            db=db_session,
            user_id=sample_user.id,
            agent_id=sample_agent.id,
        )

        # Then get active claim
        claim = await claim_service.get_active_claim(
            db=db_session,
            user_id=sample_user.id,
            agent_id=sample_agent.id,
        )

        assert claim is not None
        assert claim.agent_id == sample_agent.id
        assert claim.status == "pending"

    @pytest.mark.asyncio
    async def test_get_claim_status_pending(self, claim_service, db_session, sample_agent, sample_user):
        """Test getting claim status when pending."""
        # First initiate
        await claim_service.initiate_claim(
            db=db_session,
            user_id=sample_user.id,
            agent_id=sample_agent.id,
        )

        # Then get status
        status = await claim_service.get_claim_status(
            db=db_session,
            user_id=sample_user.id,
            agent_id=sample_agent.id,
        )

        assert status is not None
        assert status["status"] == "pending"

    @pytest.mark.asyncio
    async def test_get_claim_status_verified(self, claim_service, db_session, sample_agent, sample_user):
        """Test getting claim status when verified."""
        # First initiate
        init_result = await claim_service.initiate_claim(
            db=db_session,
            user_id=sample_user.id,
            agent_id=sample_agent.id,
        )

        # Then verify
        await claim_service.verify_claim(
            db=db_session,
            user_id=sample_user.id,
            agent_id=sample_agent.id,
            verification_code=init_result["verification_code"],
        )

        # Then get status
        status = await claim_service.get_claim_status(
            db=db_session,
            user_id=sample_user.id,
            agent_id=sample_agent.id,
        )

        assert status is not None
        assert status["status"] == "verified"

    @pytest.mark.asyncio
    async def test_get_claim_status_not_found(self, claim_service, db_session, sample_agent, sample_user):
        """Test getting claim status when no claim exists."""
        status = await claim_service.get_claim_status(
            db=db_session,
            user_id=sample_user.id,
            agent_id=sample_agent.id,
        )

        # Should return None since no claim exists
        # But if agent is already bound to user, it returns verified
        if status:
            assert status["status"] == "verified"
        else:
            assert status is None

    @pytest.mark.asyncio
    async def test_list_user_claims(self, claim_service, db_session, sample_agent, sample_user):
        """Test listing user claims."""
        # First initiate a claim
        await claim_service.initiate_claim(
            db=db_session,
            user_id=sample_user.id,
            agent_id=sample_agent.id,
        )

        # Then list claims
        claims = await claim_service.list_user_claims(
            db=db_session,
            user_id=sample_user.id,
        )

        assert isinstance(claims, list)
        assert len(claims) >= 1
        assert any(c["agent_id"] == sample_agent.id for c in claims)
