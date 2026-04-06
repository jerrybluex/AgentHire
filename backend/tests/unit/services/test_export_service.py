"""
Unit tests for Export Service
"""

import pytest
from datetime import datetime

from app.services.export_service import ExportService
from app.models import Agent, SeekerProfile, ResumeFile
from tests.factories import AgentFactory, SeekerProfileFactory


class TestExportService:
    """Tests for ExportService."""

    @pytest.fixture
    def export_service(self):
        """Create ExportService instance."""
        return ExportService()

    @pytest.fixture
    def sample_agent(self, db_session):
        """Create a sample agent."""
        agent = AgentFactory.create(
            id="agt_test123",
            name="Test Agent",
            type="seeker",
            platform="test",
        )
        db_session.add(agent)
        return agent

    @pytest.fixture
    def sample_profile(self, db_session, sample_agent):
        """Create a sample profile."""
        profile = SeekerProfileFactory.create(
            id="prof_test456",
            agent_id=sample_agent.id,
            nickname="Test User",
            status="active",
        )
        db_session.add(profile)
        db_session.flush()
        return profile

    @pytest.fixture
    def sample_resume(self, db_session, sample_profile):
        """Create a sample resume."""
        resume = ResumeFile(
            id="res_test789",
            profile_id=sample_profile.id,
            original_filename="test_resume.pdf",
            file_path="/uploads/test_resume.pdf",
            file_size=1024,
            file_type="pdf",
            mime_type="application/pdf",
            parse_status="success",
            parse_result={"name": "Test User", "skills": ["Python", "Go"]},
            parse_confidence=0.95,
            is_current=True,
            created_at=datetime.utcnow(),
        )
        db_session.add(resume)
        db_session.flush()
        return resume

    @pytest.mark.asyncio
    async def test_export_profile_json_success(
        self, export_service, db_session, sample_profile, sample_agent
    ):
        """Test successful profile JSON export."""
        result = await export_service.export_profile_json(
            db=db_session,
            profile_id=sample_profile.id,
            include_resume=False,
        )

        assert result is not None
        assert "exported_at" in result
        assert "profile" in result
        assert result["profile"]["id"] == sample_profile.id
        assert result["profile"]["nickname"] == sample_profile.nickname
        assert result["agent"]["id"] == sample_agent.id
        assert result["agent"]["name"] == sample_agent.name
        assert result["resume"] is None

    @pytest.mark.asyncio
    async def test_export_profile_json_with_resume(
        self, export_service, db_session, sample_profile, sample_agent, sample_resume
    ):
        """Test profile JSON export with resume data."""
        result = await export_service.export_profile_json(
            db=db_session,
            profile_id=sample_profile.id,
            include_resume=True,
        )

        assert result is not None
        assert result["resume"] is not None
        assert result["resume"]["id"] == sample_resume.id
        assert result["resume"]["original_filename"] == sample_resume.original_filename
        assert result["resume"]["parse_status"] == sample_resume.parse_status

    @pytest.mark.asyncio
    async def test_export_profile_json_not_found(self, export_service, db_session):
        """Test profile export with non-existent profile ID."""
        result = await export_service.export_profile_json(
            db=db_session,
            profile_id="prof_nonexistent",
            include_resume=False,
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_export_resume_json_success(
        self, export_service, db_session, sample_profile, sample_resume
    ):
        """Test successful resume JSON export."""
        result = await export_service.export_resume_json(
            db=db_session,
            resume_id=sample_resume.id,
        )

        assert result is not None
        assert "exported_at" in result
        assert "resume" in result
        assert result["resume"]["id"] == sample_resume.id
        assert result["resume"]["original_filename"] == sample_resume.original_filename
        assert result["profile"] is not None
        assert result["profile"]["id"] == sample_profile.id

    @pytest.mark.asyncio
    async def test_export_resume_json_not_found(self, export_service, db_session):
        """Test resume export with non-existent resume ID."""
        result = await export_service.export_resume_json(
            db=db_session,
            resume_id="res_nonexistent",
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_export_profile_history(
        self, export_service, db_session, sample_profile, sample_resume
    ):
        """Test profile export history."""
        result = await export_service.export_profile_history(
            db=db_session,
            profile_id=sample_profile.id,
            limit=10,
        )

        assert result is not None
        assert "exported_at" in result
        assert result["profile_id"] == sample_profile.id
        assert result["resume_count"] == 1
        assert len(result["resumes"]) == 1
        assert result["resumes"][0]["id"] == sample_resume.id

    @pytest.mark.asyncio
    async def test_export_profile_history_not_found(self, export_service, db_session):
        """Test profile history with non-existent profile ID."""
        result = await export_service.export_profile_history(
            db=db_session,
            profile_id="prof_nonexistent",
            limit=10,
        )

        assert result is None

    def test_generate_export_filename_profile(self, export_service):
        """Test export filename generation for profile."""
        filename = export_service.generate_export_filename("prof_test123", "profile")

        assert filename.startswith("agenthire_profile_prof_test123_")
        assert filename.endswith(".json")
        assert "prof_test123" in filename

    def test_generate_export_filename_resume(self, export_service):
        """Test export filename generation for resume."""
        filename = export_service.generate_export_filename("res_test456", "resume")

        assert filename.startswith("agenthire_resume_res_test456_")
        assert filename.endswith(".json")
        assert "res_test456" in filename
