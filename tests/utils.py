"""
Test utilities for AgentHire.

This module provides helper functions for testing:
- Database operations
- Mock setup
- Assertion helpers
- Data generation
"""

import json
import random
import string
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock


# =============================================================================
# ID Generators
# =============================================================================

def generate_id(prefix: str, length: int = 8) -> str:
    """Generate a test ID with given prefix."""
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=length))
    return f"{prefix}_{suffix}"


def generate_profile_id() -> str:
    """Generate a test profile ID."""
    return generate_id("prof")


def generate_job_id() -> str:
    """Generate a test job ID."""
    return generate_id("job")


def generate_enterprise_id() -> str:
    """Generate a test enterprise ID."""
    return generate_id("ent")


def generate_match_id() -> str:
    """Generate a test match ID."""
    return generate_id("match")


def generate_api_key() -> str:
    """Generate a test API key."""
    return f"ak_{''.join(random.choices(string.ascii_letters + string.digits, k=32))}"


# =============================================================================
# Data Generators
# =============================================================================

def generate_vector(dim: int = 384) -> List[float]:
    """Generate a random vector of given dimension."""
    return [random.uniform(-1, 1) for _ in range(dim)]


def generate_timestamp(days_offset: int = 0) -> datetime:
    """Generate a timestamp with optional offset from now."""
    return datetime.utcnow() + timedelta(days=days_offset)


def generate_phone() -> str:
    """Generate a random Chinese phone number."""
    prefix = random.choice(["138", "139", "135", "136", "137", "150", "151", "152"])
    suffix = "".join(random.choices(string.digits, k=8))
    return f"{prefix}{suffix}"


def generate_email(name: Optional[str] = None) -> str:
    """Generate a random email address."""
    if name is None:
        name = "".join(random.choices(string.ascii_lowercase, k=8))
    domain = random.choice(["gmail.com", "qq.com", "163.com", "example.com"])
    return f"{name}@{domain}"


# =============================================================================
# Mock Helpers
# =============================================================================

def create_async_mock(return_value: Any = None, side_effect: Any = None) -> MagicMock:
    """Create an async mock with given return value."""
    mock = MagicMock()
    if side_effect:
        mock.side_effect = side_effect
    else:
        mock.return_value = return_value
    return mock


def mock_llm_response(intent_type: str = "job_search", confidence: float = 0.92) -> Dict:
    """Create a mock LLM response for intent parsing."""
    responses = {
        "job_search": {
            "intent_type": "job_search",
            "parsed": {
                "location": {"city": "上海", "remote": False},
                "role": {"title": "后端工程师", "category": "backend"},
                "salary": {"min_monthly": 30000, "currency": "CNY"},
                "experience": {"min_years": 3, "max_years": None},
                "skills": ["Java", "Go", "微服务"],
            },
            "confidence": confidence,
            "missing_fields": [],
        },
        "job_post": {
            "intent_type": "job_post",
            "parsed": {
                "title": "高级后端工程师",
                "department": "技术部",
                "requirements": {
                    "skills": ["Go", "微服务"],
                    "experience_min": 3,
                },
                "compensation": {
                    "salary_min": 35000,
                    "salary_max": 50000,
                },
                "location": {"city": "上海"},
            },
            "confidence": confidence,
            "missing_fields": [],
        },
    }
    return responses.get(intent_type, responses["job_search"])


def mock_resume_parse_result(confidence: float = 0.94) -> Dict:
    """Create a mock resume parse result."""
    return {
        "parse_id": generate_id("parse"),
        "confidence": confidence,
        "extracted_data": {
            "basic_info": {
                "name": "张三",
                "phone": generate_phone(),
                "email": generate_email("zhangsan"),
                "location": "上海",
                "gender": "男",
                "age": random.randint(25, 35),
            },
            "work_experience": [
                {
                    "company": "字节跳动",
                    "title": "高级后端工程师",
                    "duration": "2021.06 - 至今",
                    "years": 2.5,
                    "description": "负责抖音电商核心服务开发",
                    "skills_used": ["Go", "微服务", "Kubernetes"],
                },
            ],
            "education": [
                {
                    "school": "上海交通大学",
                    "major": "计算机科学与技术",
                    "degree": "本科",
                    "duration": "2015.09 - 2019.06",
                },
            ],
            "skills": [
                {"name": "Go", "level": "expert", "years": 2.5},
                {"name": "Java", "level": "intermediate", "years": 3},
            ],
            "total_work_years": 4.3,
        },
        "career_vector": generate_vector(384),
    }


# =============================================================================
# Assertion Helpers
# =============================================================================

def assert_valid_uuid(value: str) -> bool:
    """Check if value is a valid UUID format."""
    import uuid
    try:
        uuid.UUID(str(value))
        return True
    except (ValueError, TypeError):
        return False


def assert_valid_timestamp(value: Any) -> bool:
    """Check if value is a valid timestamp."""
    if isinstance(value, datetime):
        return True
    if isinstance(value, str):
        try:
            datetime.fromisoformat(value.replace("Z", "+00:00"))
            return True
        except ValueError:
            pass
    return False


def assert_vector_dimension(vector: List[float], expected_dim: int = 384) -> None:
    """Assert vector has expected dimension."""
    assert len(vector) == expected_dim, f"Expected vector dimension {expected_dim}, got {len(vector)}"


def assert_response_structure(response: Dict, required_fields: List[str]) -> None:
    """Assert response contains all required fields."""
    for field in required_fields:
        assert field in response, f"Missing required field: {field}"


def assert_api_success(response: Dict) -> None:
    """Assert API response indicates success."""
    assert response.get("success") is True, f"API call failed: {response.get('error', 'Unknown error')}"
    assert "data" in response, "Response missing 'data' field"


def assert_api_error(response: Dict, expected_status_code: int = 400) -> None:
    """Assert API response indicates error."""
    assert response.get("success") is False or "error" in response


def assert_match_score_in_range(score: float, min_val: float = 0.0, max_val: float = 1.0) -> None:
    """Assert match score is within valid range."""
    assert min_val <= score <= max_val, f"Match score {score} not in range [{min_val}, {max_val}]"


# =============================================================================
# Database Helpers
# =============================================================================

async def create_test_profile(db_session, **overrides) -> Dict:
    """Create a test profile in database."""
    profile_data = {
        "id": generate_profile_id(),
        "agent_id": "agent_test_001",
        "status": "active",
        "nickname": "测试用户",
        "job_intent": {
            "target_roles": ["后端工程师"],
            "salary_expectation": {"min_monthly": 30000, "max_monthly": 45000},
            "skills": [{"name": "Go", "level": "expert", "years": 3}],
        },
        "intent_vector": generate_vector(384),
    }
    profile_data.update(overrides)

    # When models are available:
    # from app.models import SeekerProfile
    # profile = SeekerProfile(**profile_data)
    # db_session.add(profile)
    # await db_session.commit()
    # return profile

    return profile_data


async def create_test_job(db_session, **overrides) -> Dict:
    """Create a test job posting in database."""
    job_data = {
        "id": generate_job_id(),
        "enterprise_id": generate_enterprise_id(),
        "title": "高级后端工程师",
        "description": "负责微服务架构设计",
        "requirements": {
            "skills": ["Go", "微服务"],
            "experience_min": 3,
        },
        "job_vector": generate_vector(384),
        "status": "active",
    }
    job_data.update(overrides)
    return job_data


async def create_test_enterprise(db_session, **overrides) -> Dict:
    """Create a test enterprise in database."""
    ent_data = {
        "id": generate_enterprise_id(),
        "name": "测试科技有限公司",
        "unified_social_credit_code": "91310000XXXXXXXXXX",
        "status": "approved",
        "contact": {"name": "张三", "phone": generate_phone(), "email": generate_email()},
    }
    ent_data.update(overrides)
    return ent_data


# =============================================================================
# JSON Helpers
# =============================================================================

def load_json_file(filepath: str) -> Dict:
    """Load JSON file and return parsed data."""
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json_file(filepath: str, data: Dict) -> None:
    """Save data to JSON file."""
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def compare_json(data1: Dict, data2: Dict, ignore_fields: Optional[List[str]] = None) -> bool:
    """Compare two JSON objects, optionally ignoring certain fields."""
    if ignore_fields:
        data1 = {k: v for k, v in data1.items() if k not in ignore_fields}
        data2 = {k: v for k, v in data2.items() if k not in ignore_fields}
    return data1 == data2
