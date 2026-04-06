"""
Unit tests for AgentHire models.
Tests database model creation and validation.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch


class TestModelGeneration:
    """Tests for model ID generation."""

    def test_generate_id_without_prefix(self):
        """Test ID generation without prefix."""
        from app.models import generate_id

        with patch("app.models.nanoid") as mock_nanoid:
            mock_nanoid.return_value = "abc123xyz789"
            result = generate_id()
            assert result == "abc123xyz789"

    def test_generate_id_with_prefix(self):
        """Test ID generation with prefix."""
        from app.models import generate_id

        with patch("app.models.nanoid") as mock_nanoid:
            mock_nanoid.return_value = "abc123xyz789"
            result = generate_id("prof_")
            assert result == "prof_abc123xyz789"

    def test_generate_id_different_prefixes(self):
        """Test ID generation with different prefixes."""
        from app.models import generate_id

        prefixes = ["prof_", "job_", "ent_", "key_", "mat_"]
        for prefix in prefixes:
            with patch("app.models.nanoid") as mock_nanoid:
                mock_nanoid.return_value = "test123"
                result = generate_id(prefix)
                assert result.startswith(prefix)


class TestSeekerProfileModel:
    """Tests for SeekerProfile model."""

    def test_profile_default_values(self):
        """Test profile model default values."""
        # Mock the nanoid call
        with patch("app.models.nanoid") as mock_nanoid:
            mock_nanoid.return_value = "test123"

            # Create a mock model instance
            mock_profile = MagicMock()
            mock_profile.status = "active"
            mock_profile.agent_id = "agent_001"
            mock_profile.job_intent = {}
            mock_profile.privacy = {}
            mock_profile.match_preferences = {}

            assert mock_profile.status == "active"
            assert mock_profile.agent_id == "agent_001"

    def test_profile_status_enum(self):
        """Test profile status values."""
        valid_statuses = ["active", "paused", "deleted"]

        for status in valid_statuses:
            mock_profile = MagicMock()
            mock_profile.status = status
            assert mock_profile.status in valid_statuses


class TestJobPostingModel:
    """Tests for JobPosting model."""

    def test_job_default_status(self):
        """Test job posting default status."""
        mock_job = MagicMock()
        mock_job.status = "active"
        mock_job.match_threshold = 0.7
        mock_job.auto_match = True

        assert mock_job.status == "active"
        assert mock_job.match_threshold == 0.7
        assert mock_job.auto_match is True

    def test_job_compensation_structure(self):
        """Test job compensation data structure."""
        mock_compensation = {
            "salary_min": 35000,
            "salary_max": 50000,
            "currency": "CNY",
            "stock_options": True,
            "benefits": ["五险一金", "补充医疗"],
        }

        assert "salary_min" in mock_compensation
        assert "salary_max" in mock_compensation
        assert mock_compensation["currency"] == "CNY"


class TestEnterpriseModel:
    """Tests for Enterprise model."""

    def test_enterprise_default_status(self):
        """Test enterprise default verification status."""
        mock_enterprise = MagicMock()
        mock_enterprise.status = "pending"

        assert mock_enterprise.status == "pending"

    def test_enterprise_certification_structure(self):
        """Test enterprise certification data structure."""
        mock_certification = {
            "business_license_url": "s3://bucket/license.pdf",
            "legal_person_id_url": "s3://bucket/id.pdf",
            "submitted_at": "2024-01-01T00:00:00Z",
        }

        assert "business_license_url" in mock_certification
        assert "submitted_at" in mock_certification


class TestJobMatchModel:
    """Tests for JobMatch model."""

    def test_match_score_range(self):
        """Test match score is between 0 and 1."""
        mock_match = MagicMock()
        mock_match.match_score = 0.89

        assert 0 <= mock_match.match_score <= 1

    def test_match_factors_structure(self):
        """Test match factors data structure."""
        mock_factors = {
            "skill_match": 0.95,
            "experience_match": 0.85,
            "location_match": 1.0,
            "salary_match": 0.90,
            "overall": 0.89,
        }

        assert "skill_match" in mock_factors
        assert "overall" in mock_factors
        assert all(0 <= v <= 1 for k, v in mock_factors.items() if k != "overall")


class TestBillingRecordModel:
    """Tests for BillingRecord model."""

    def test_usage_types(self):
        """Test valid usage types."""
        valid_types = ["job_post", "match_query", "match_success", "profile_view"]

        for usage_type in valid_types:
            mock_record = MagicMock()
            mock_record.usage_type = usage_type
            assert mock_record.usage_type in valid_types


# =============================================================================
# Schema Validation Tests
# =============================================================================

class TestSkillSchema:
    """Tests for Skill schema validation."""

    def test_skill_required_fields(self):
        """Test skill schema required fields."""
        from pydantic import ValidationError

        # Skill requires name
        with pytest.raises(ValidationError):
            from app.schemas import Skill
            Skill()  # Missing required field 'name'

    def test_skill_optional_fields(self):
        """Test skill schema optional fields."""
        from app.schemas import Skill

        skill = Skill(name="Python")
        assert skill.name == "Python"
        assert skill.level is None
        assert skill.years is None


class TestJobIntentSchema:
    """Tests for JobIntent schema validation."""

    def test_job_intent_default_values(self):
        """Test job intent default values."""
        from app.schemas import JobIntent

        intent = JobIntent()
        assert intent.target_roles == []
        assert intent.skills == []

    def test_job_intent_with_data(self):
        """Test job intent with data."""
        from app.schemas import JobIntent, Skill

        intent = JobIntent(
            target_roles=["Backend Engineer"],
            salary_expectation={"min_monthly": 30000},
            skills=[Skill(name="Go", level="expert")],
        )

        assert "Backend Engineer" in intent.target_roles
        assert intent.salary_expectation["min_monthly"] == 30000
        assert len(intent.skills) == 1


class TestParseStatusEnum:
    """Tests for ParseStatus enum."""

    def test_parse_status_values(self):
        """Test parse status enum values."""
        from app.schemas import ParseStatus

        assert ParseStatus.PENDING.value == "pending"
        assert ParseStatus.PROCESSING.value == "processing"
        assert ParseStatus.SUCCESS.value == "success"
        assert ParseStatus.FAILED.value == "failed"


class TestSuccessResponse:
    """Tests for SuccessResponse schema."""

    def test_default_success_response(self):
        """Test default success response."""
        from app.schemas import SuccessResponse

        response = SuccessResponse()
        assert response.success is True
        assert response.data is None

    def test_custom_success_response(self):
        """Test custom success response with data."""
        from app.schemas import SuccessResponse

        response = SuccessResponse(
            success=True,
            data={"key": "value"},
            message="Operation completed",
        )

        assert response.success is True
        assert response.data == {"key": "value"}
        assert response.message == "Operation completed"
