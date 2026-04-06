"""
Unit tests for A2AService.
"""

import pytest
from datetime import datetime

from app.services.a2a_service import A2AService
from app.models import A2AInterest, A2ASession
from tests.factories import (
    A2AInterestFactory,
    A2ASessionFactory,
    SeekerProfileFactory,
    JobPostingFactory,
    EnterpriseFactory,
    EnterpriseAPIKeyFactory,
)


class TestA2AService:
    """Tests for A2AService."""

    @pytest.mark.asyncio
    async def test_express_interest(self, db_session):
        """Test expressing interest in a job."""
        service = A2AService()

        # Create related entities first
        enterprise = EnterpriseFactory.create()
        db_session.add(enterprise)
        await db_session.flush()

        api_key, _ = EnterpriseAPIKeyFactory.create(enterprise_id=enterprise.id)
        db_session.add(api_key)
        await db_session.flush()

        seeker_profile = SeekerProfileFactory.create(agent_id="agt_seeker1")
        db_session.add(seeker_profile)
        await db_session.flush()

        job = JobPostingFactory.create(
            enterprise_id=enterprise.id,
            api_key_id=api_key.id,
        )
        db_session.add(job)
        await db_session.flush()

        # Express interest
        result = await service.express_interest(
            db=db_session,
            profile_id=seeker_profile.id,
            job_id=job.id,
            seeker_agent_id="agt_seeker1",
            employer_agent_id="agt_employer1",
            message="I'm very interested in this position",
        )

        assert result is not None
        assert result["status"] == "pending"
        assert result["profile_id"] == seeker_profile.id
        assert result["job_id"] == job.id

    @pytest.mark.asyncio
    async def test_respond_to_interest_accept(self, db_session):
        """Test accepting an interest."""
        service = A2AService()

        # Create entities
        enterprise = EnterpriseFactory.create()
        db_session.add(enterprise)
        await db_session.flush()

        api_key, _ = EnterpriseAPIKeyFactory.create(enterprise_id=enterprise.id)
        db_session.add(api_key)
        await db_session.flush()

        seeker_profile = SeekerProfileFactory.create(agent_id="agt_seeker1")
        db_session.add(seeker_profile)
        await db_session.flush()

        job = JobPostingFactory.create(
            enterprise_id=enterprise.id,
            api_key_id=api_key.id,
        )
        db_session.add(job)
        await db_session.flush()

        # Create interest
        interest = A2AInterestFactory.create(
            profile_id=seeker_profile.id,
            job_id=job.id,
            seeker_agent_id="agt_seeker1",
            employer_agent_id="agt_employer1",
            status="pending",
        )
        db_session.add(interest)
        await db_session.flush()

        # Accept interest
        result = await service.respond_to_interest(
            db=db_session,
            profile_id=seeker_profile.id,
            job_id=job.id,
            action="accept",
            employer_agent_id="agt_employer1",
        )

        assert result["success"] is True
        assert result["status"] == "accepted"
        assert "session_id" in result

    @pytest.mark.asyncio
    async def test_respond_to_interest_reject(self, db_session):
        """Test rejecting an interest."""
        service = A2AService()

        # Create entities
        enterprise = EnterpriseFactory.create()
        db_session.add(enterprise)
        await db_session.flush()

        api_key, _ = EnterpriseAPIKeyFactory.create(enterprise_id=enterprise.id)
        db_session.add(api_key)
        await db_session.flush()

        seeker_profile = SeekerProfileFactory.create(agent_id="agt_seeker1")
        db_session.add(seeker_profile)
        await db_session.flush()

        job = JobPostingFactory.create(
            enterprise_id=enterprise.id,
            api_key_id=api_key.id,
        )
        db_session.add(job)
        await db_session.flush()

        # Create interest
        interest = A2AInterestFactory.create(
            profile_id=seeker_profile.id,
            job_id=job.id,
            seeker_agent_id="agt_seeker1",
            employer_agent_id="agt_employer1",
            status="pending",
        )
        db_session.add(interest)
        await db_session.flush()

        # Reject interest
        result = await service.respond_to_interest(
            db=db_session,
            profile_id=seeker_profile.id,
            job_id=job.id,
            action="reject",
            employer_agent_id="agt_employer1",
        )

        assert result["success"] is True
        assert result["status"] == "rejected"

    @pytest.mark.asyncio
    async def test_negotiate_salary(self, db_session):
        """Test salary negotiation."""
        service = A2AService()

        # Create entities
        enterprise = EnterpriseFactory.create()
        db_session.add(enterprise)
        await db_session.flush()

        api_key, _ = EnterpriseAPIKeyFactory.create(enterprise_id=enterprise.id)
        db_session.add(api_key)
        await db_session.flush()

        seeker_profile = SeekerProfileFactory.create(agent_id="agt_seeker1")
        db_session.add(seeker_profile)
        await db_session.flush()

        job = JobPostingFactory.create(
            enterprise_id=enterprise.id,
            api_key_id=api_key.id,
        )
        db_session.add(job)
        await db_session.flush()

        # Create session
        session = A2ASessionFactory.create(
            profile_id=seeker_profile.id,
            job_id=job.id,
            seeker_agent_id="agt_seeker1",
            employer_agent_id="agt_employer1",
            status="negotiating",
        )
        db_session.add(session)
        await db_session.flush()

        # Negotiate
        offer = {"salary": 45000, "start_date": "2026-06-01", "notes": "Flexible"}
        result = await service.negotiate_salary(
            db=db_session,
            session_id=session.id,
            from_agent_id="agt_employer1",
            offer=offer,
        )

        assert result["success"] is True
        assert result["current_offer"]["salary"] == 45000

    @pytest.mark.asyncio
    async def test_confirm_session(self, db_session):
        """Test confirming a negotiation session."""
        service = A2AService()

        # Create session
        session = A2ASessionFactory.create(
            seeker_agent_id="agt_seeker1",
            employer_agent_id="agt_employer1",
            seeker_confirmed=False,
            employer_confirmed=False,
        )
        db_session.add(session)
        await db_session.flush()

        # Employer confirms
        result = await service.confirm(
            db=db_session,
            session_id=session.id,
            agent_id="agt_employer1",
        )

        assert result["success"] is True
        assert result["status"] == "pending"

    @pytest.mark.asyncio
    async def test_confirm_session_both_confirmed(self, db_session):
        """Test that both parties confirming triggers contact exchange."""
        service = A2AService()

        # Create session with seeker already confirmed
        session = A2ASessionFactory.create(
            seeker_agent_id="agt_seeker1",
            employer_agent_id="agt_employer1",
            seeker_confirmed=True,
            employer_confirmed=False,
        )
        db_session.add(session)
        await db_session.flush()

        # Employer confirms
        result = await service.confirm(
            db=db_session,
            session_id=session.id,
            agent_id="agt_employer1",
        )

        assert result["success"] is True
        assert result["status"] == "confirmed"
        assert result["contact_exchange"] is True

    @pytest.mark.asyncio
    async def test_reject_session(self, db_session):
        """Test rejecting a negotiation session."""
        service = A2AService()

        # Create session
        session = A2ASessionFactory.create(
            seeker_agent_id="agt_seeker1",
            employer_agent_id="agt_employer1",
        )
        db_session.add(session)
        await db_session.flush()

        # Reject
        result = await service.reject(
            db=db_session,
            session_id=session.id,
            agent_id="agt_employer1",
            reason="Position filled",
        )

        assert result["success"] is True
        assert result["status"] == "rejected"

    @pytest.mark.asyncio
    async def test_get_session(self, db_session):
        """Test retrieving a session."""
        service = A2AService()

        # Create session
        session = A2ASessionFactory.create(
            seeker_agent_id="agt_seeker1",
            employer_agent_id="agt_employer1",
        )
        db_session.add(session)
        await db_session.flush()

        # Get session
        result = await service.get_session(db_session, session.id)

        assert result is not None
        assert result["session_id"] == session.id
        assert result["seeker_agent_id"] == "agt_seeker1"

    @pytest.mark.asyncio
    async def test_get_session_not_found(self, db_session):
        """Test that getting non-existent session returns None."""
        service = A2AService()

        result = await service.get_session(db_session, "nonexistent")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_interest(self, db_session):
        """Test retrieving interest."""
        service = A2AService()

        # Create interest
        interest = A2AInterestFactory.create(
            profile_id="prof_test",
            job_id="job_test",
        )
        db_session.add(interest)
        await db_session.flush()

        # Get interest
        result = await service.get_interest(db_session, "prof_test", "job_test")

        assert result is not None
        assert result["profile_id"] == "prof_test"
        assert result["job_id"] == "job_test"
