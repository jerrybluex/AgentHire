"""
Unit tests for utility functions.

These tests verify helper functions and utilities.
"""

import pytest

from tests.utils import (
    generate_api_key,
    generate_email,
    generate_id,
    generate_phone,
    generate_vector,
    mock_llm_response,
    mock_resume_parse_result,
)


@pytest.mark.unit
class TestIdGenerators:
    """Test ID generation utilities."""

    def test_generate_id_with_prefix(self):
        """Test ID generation with custom prefix."""
        id_value = generate_id("test", length=8)
        assert id_value.startswith("test_")
        assert len(id_value) == 13  # prefix + underscore + 8 chars

    def test_generate_id_unique(self):
        """Test that generated IDs are unique."""
        ids = [generate_id("prof") for _ in range(100)]
        assert len(set(ids)) == 100

    def test_generate_profile_id(self):
        """Test profile ID generation."""
        from tests.utils import generate_profile_id

        profile_id = generate_profile_id()
        assert profile_id.startswith("prof_")

    def test_generate_job_id(self):
        """Test job ID generation."""
        from tests.utils import generate_job_id

        job_id = generate_job_id()
        assert job_id.startswith("job_")

    def test_generate_enterprise_id(self):
        """Test enterprise ID generation."""
        from tests.utils import generate_enterprise_id

        ent_id = generate_enterprise_id()
        assert ent_id.startswith("ent_")


@pytest.mark.unit
class TestDataGenerators:
    """Test data generation utilities."""

    def test_generate_vector_default_dimension(self):
        """Test vector generation with default dimension."""
        vector = generate_vector()
        assert len(vector) == 384
        assert all(-1 <= v <= 1 for v in vector)

    def test_generate_vector_custom_dimension(self):
        """Test vector generation with custom dimension."""
        vector = generate_vector(dim=128)
        assert len(vector) == 128

    def test_generate_phone_format(self):
        """Test phone number generation format."""
        phone = generate_phone()
        assert len(phone) == 11
        assert phone.startswith(("138", "139", "135", "136", "137", "150", "151", "152"))
        assert phone.isdigit()

    def test_generate_email_format(self):
        """Test email generation format."""
        email = generate_email("testuser")
        assert "@" in email
        assert email.startswith("testuser@")

    def test_generate_api_key_format(self):
        """Test API key generation format."""
        api_key = generate_api_key()
        assert api_key.startswith("ak_")
        assert len(api_key) == 35  # ak_ + 32 chars


@pytest.mark.unit
class TestMockHelpers:
    """Test mock data helpers."""

    def test_mock_llm_response_job_search(self):
        """Test mock LLM response for job search intent."""
        response = mock_llm_response("job_search")

        assert response["intent_type"] == "job_search"
        assert "parsed" in response
        assert "location" in response["parsed"]
        assert "salary" in response["parsed"]
        assert "confidence" in response

    def test_mock_llm_response_job_post(self):
        """Test mock LLM response for job post intent."""
        response = mock_llm_response("job_post")

        assert response["intent_type"] == "job_post"
        assert "title" in response["parsed"]
        assert "requirements" in response["parsed"]

    def test_mock_resume_parse_result_structure(self):
        """Test mock resume parse result structure."""
        result = mock_resume_parse_result()

        assert "parse_id" in result
        assert "confidence" in result
        assert "extracted_data" in result
        assert "basic_info" in result["extracted_data"]
        assert "work_experience" in result["extracted_data"]
        assert "skills" in result["extracted_data"]
        assert "career_vector" in result

    def test_mock_resume_parse_result_confidence(self):
        """Test mock resume parse result with custom confidence."""
        result = mock_resume_parse_result(confidence=0.85)
        assert result["confidence"] == 0.85


@pytest.mark.unit
class TestUtilsImports:
    """Test that all utilities can be imported."""

    def test_import_all_utils(self):
        """Test importing all utility functions."""
        from tests.utils import (
            assert_api_error,
            assert_api_success,
            assert_match_score_in_range,
            assert_response_structure,
            assert_valid_timestamp,
            assert_valid_uuid,
            assert_vector_dimension,
            compare_json,
            create_async_mock,
            create_test_enterprise,
            create_test_job,
            create_test_profile,
            generate_job_id,
            generate_match_id,
            generate_timestamp,
            load_json_file,
            mock_llm_response,
            save_json_file,
        )

        # Just verify imports work
        assert callable(generate_job_id)
        assert callable(mock_llm_response)
