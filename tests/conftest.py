"""
Pytest configuration and fixtures for AgentHire tests.

This module provides:
- Database fixtures with transaction rollback
- Test client fixtures
- Authentication fixtures
- Mock fixtures for LLM and external services
- Sample data fixtures
"""

import asyncio
import json
import os
import uuid
from datetime import datetime, timedelta
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio


# =============================================================================
# Configuration Fixtures
# =============================================================================

@pytest.fixture(scope="session")
def test_settings():
    """Return test configuration settings."""
    return {
        "database_url": os.getenv("TEST_DATABASE_URL", "sqlite+aiosqlite:///:memory:"),
        "redis_url": os.getenv("TEST_REDIS_URL", "redis://localhost:6379/1"),
        "secret_key": "test-secret-key-for-testing-only",
        "access_token_expire_minutes": 30,
        "algorithm": "HS256",
    }


# =============================================================================
# Database Fixtures
# =============================================================================

@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator:
    """
    Create a database session with transaction rollback.

    This fixture ensures test isolation by rolling back all changes
    after each test function.
    """
    # Import here to avoid circular imports when app is available
    try:
        from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
        from sqlalchemy.orm import sessionmaker

        # Create async engine for testing
        engine = create_async_engine(
            "sqlite+aiosqlite:///:memory:",
            echo=False,
            future=True,
        )

        # Create session factory
        async_session = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )

        # Create tables
        async with engine.begin() as conn:
            # Import models here when available
            # from app.models import Base
            # await conn.run_sync(Base.metadata.create_all)
            pass

        # Create session
        async with async_session() as session:
            yield session
            # Rollback all changes
            await session.rollback()

        # Clean up
        await engine.dispose()

    except ImportError:
        # Fallback when SQLAlchemy is not installed or app models not available
        mock_session = MagicMock()
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        mock_session.close = AsyncMock()
        yield mock_session


@pytest_asyncio.fixture(scope="function")
async def db_engine():
    """Create a database engine for testing."""
    try:
        from sqlalchemy.ext.asyncio import create_async_engine

        engine = create_async_engine(
            "sqlite+aiosqlite:///:memory:",
            echo=False,
            future=True,
        )
        yield engine
        await engine.dispose()
    except ImportError:
        yield None


# =============================================================================
# HTTP Client Fixtures
# =============================================================================

@pytest_asyncio.fixture(scope="function")
async def async_client() -> AsyncGenerator:
    """
    Create an async HTTP client for API testing.

    Uses httpx.AsyncClient with FastAPI app when available.
    """
    try:
        from httpx import AsyncClient

        # Import FastAPI app when available
        try:
            from app.main import app
            async with AsyncClient(app=app, base_url="http://test") as client:
                yield client
        except ImportError:
            # Fallback when app is not yet available
            async with AsyncClient(base_url="http://test") as client:
                yield client
    except ImportError:
        pytest.skip("httpx not installed")


@pytest.fixture(scope="function")
def client():
    """
    Create a synchronous HTTP client for API testing.

    Uses FastAPI TestClient when available.
    """
    try:
        from fastapi.testclient import TestClient
        from app.main import app
        with TestClient(app) as client:
            yield client
    except ImportError as e:
        pytest.skip(f"FastAPI TestClient or app not available: {e}")


# =============================================================================
# Authentication Fixtures
# =============================================================================

@pytest.fixture(scope="function")
def auth_token() -> str:
    """Generate a test JWT token."""
    try:
        import jwt

        payload = {
            "sub": "test_user_001",
            "exp": datetime.utcnow() + timedelta(minutes=30),
            "iat": datetime.utcnow(),
            "type": "access",
            "role": "seeker",
        }
        return jwt.encode(payload, "test-secret-key", algorithm="HS256")
    except ImportError:
        return "test-jwt-token-placeholder"


@pytest.fixture(scope="function")
def enterprise_auth_token() -> str:
    """Generate a test enterprise JWT token."""
    try:
        import jwt

        payload = {
            "sub": "ent_001",
            "exp": datetime.utcnow() + timedelta(minutes=30),
            "iat": datetime.utcnow(),
            "type": "access",
            "role": "enterprise",
            "permissions": ["job:post", "match:query", "profile:view"],
        }
        return jwt.encode(payload, "test-secret-key", algorithm="HS256")
    except ImportError:
        return "test-enterprise-jwt-token"


@pytest.fixture(scope="function")
def auth_headers(auth_token: str) -> dict:
    """Return authentication headers with Bearer token."""
    return {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json",
    }


@pytest.fixture(scope="function")
def enterprise_auth_headers(enterprise_auth_token: str) -> dict:
    """Return enterprise authentication headers."""
    return {
        "Authorization": f"Bearer {enterprise_auth_token}",
        "Content-Type": "application/json",
    }


# =============================================================================
# Mock Fixtures
# =============================================================================

@pytest.fixture(scope="function")
def mock_llm_client():
    """
    Mock LLM client for testing without external API calls.

    Returns a mock that simulates LLM responses for resume parsing
    and intent parsing.
    """
    mock = MagicMock()

    # Mock resume parsing response
    mock.parse_resume = AsyncMock(return_value={
        "basic_info": {
            "name": "张三",
            "phone": "138****8000",
            "email": "zhangsan@example.com",
            "location": "上海",
            "gender": "男",
            "age": 28,
        },
        "work_experience": [
            {
                "company": "字节跳动",
                "title": "高级后端工程师",
                "duration": "2021.06 - 至今",
                "years": 2.5,
                "description": "负责抖音电商核心服务开发",
                "skills_used": ["Go", "微服务", "Kubernetes"],
            }
        ],
        "education": [
            {
                "school": "上海交通大学",
                "major": "计算机科学与技术",
                "degree": "本科",
                "duration": "2015.09 - 2019.06",
            }
        ],
        "skills": [
            {"name": "Go", "level": "expert", "years": 2.5},
            {"name": "Java", "level": "intermediate", "years": 3},
        ],
        "total_work_years": 4.3,
        "parse_confidence": 0.94,
    })

    # Mock intent parsing response
    mock.parse_intent = AsyncMock(return_value={
        "intent_type": "job_search",
        "parsed": {
            "location": {"city": "上海", "remote": False},
            "role": {"title": "后端工程师", "category": "backend"},
            "salary": {"min_monthly": 30000, "currency": "CNY"},
            "experience": {"min_years": 3, "max_years": None},
            "skills": ["Java", "Go", "微服务"],
        },
        "confidence": 0.92,
        "missing_fields": [],
    })

    # Mock embedding generation
    mock.generate_embedding = AsyncMock(return_value=[0.1] * 384)

    return mock


@pytest.fixture(scope="function")
def mock_embedding_model():
    """Mock embedding model for vector generation."""
    mock = MagicMock()
    mock.encode = MagicMock(return_value=[0.1] * 384)
    mock.encode_batch = MagicMock(return_value=[[0.1] * 384, [0.2] * 384])
    return mock


@pytest.fixture(scope="function")
def mock_file_storage():
    """Mock file storage (S3/MinIO) for testing."""
    mock = MagicMock()
    mock.upload_file = AsyncMock(return_value="s3://test-bucket/resumes/test.pdf")
    mock.download_file = AsyncMock(return_value=b"mock file content")
    mock.delete_file = AsyncMock(return_value=True)
    mock.get_presigned_url = AsyncMock(return_value="https://test-url.com/file.pdf")
    return mock


@pytest.fixture(scope="function")
def mock_redis():
    """Mock Redis client for caching and rate limiting tests."""
    mock = MagicMock()
    mock.get = AsyncMock(return_value=None)
    mock.set = AsyncMock(return_value=True)
    mock.setex = AsyncMock(return_value=True)
    mock.delete = AsyncMock(return_value=1)
    mock.exists = AsyncMock(return_value=0)
    mock.incr = AsyncMock(return_value=1)
    mock.expire = AsyncMock(return_value=True)
    mock.pipeline = MagicMock(return_value=mock)
    mock.execute = AsyncMock(return_value=[])
    return mock


# =============================================================================
# Sample Data Fixtures
# =============================================================================

@pytest.fixture(scope="function")
def sample_seeker_profile() -> dict:
    """Return a sample seeker profile for testing."""
    return {
        "id": f"prof_{uuid.uuid4().hex[:8]}",
        "agent_id": "agent_test_001",
        "agent_type": "openclaw",
        "status": "active",
        "nickname": "测试用户",
        "basic_info": {
            "location": "上海",
            "gender": "男",
            "age": 28,
        },
        "job_intent": {
            "target_roles": ["后端工程师", "架构师"],
            "salary_expectation": {
                "min_monthly": 30000,
                "max_monthly": 45000,
                "currency": "CNY",
            },
            "location_preference": {
                "cities": ["上海", "杭州"],
                "remote_acceptable": True,
            },
            "skills": [
                {"name": "Go", "level": "expert", "years": 3},
                {"name": "Kubernetes", "level": "intermediate", "years": 2},
            ],
            "experience_years": 3,
        },
        "intent_vector": [0.1] * 384,
        "privacy": {
            "contact_encrypted": "encrypted_contact_info",
            "public_fields": ["skills", "experience_years"],
            "reveal_on_match": True,
        },
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }


@pytest.fixture(scope="function")
def sample_job_posting() -> dict:
    """Return a sample job posting for testing."""
    return {
        "id": f"job_{uuid.uuid4().hex[:8]}",
        "enterprise_id": "ent_001",
        "api_key_id": "key_001",
        "title": "高级后端工程师",
        "department": "技术部",
        "description": "负责微服务架构设计和开发",
        "responsibilities": [
            "设计和开发高并发后端服务",
            "优化系统性能和稳定性",
        ],
        "requirements": {
            "skills": ["Go", "微服务", "Kubernetes"],
            "skill_weights": {"Go": 1.0, "微服务": 0.9, "Kubernetes": 0.8},
            "experience_min": 3,
            "experience_max": 5,
            "education": "bachelor",
        },
        "compensation": {
            "salary_min": 35000,
            "salary_max": 50000,
            "currency": "CNY",
            "stock_options": True,
            "benefits": ["五险一金", "补充医疗", "弹性工作"],
        },
        "location": {
            "city": "上海",
            "district": "浦东新区",
            "address": "张江高科技园区",
            "remote_policy": "hybrid",
        },
        "job_vector": [0.15] * 384,
        "status": "active",
        "match_threshold": 0.7,
        "auto_match": True,
        "published_at": datetime.utcnow().isoformat(),
        "expires_at": (datetime.utcnow() + timedelta(days=30)).isoformat(),
    }


@pytest.fixture(scope="function")
def sample_enterprise() -> dict:
    """Return a sample enterprise for testing."""
    return {
        "id": f"ent_{uuid.uuid4().hex[:8]}",
        "name": "测试科技有限公司",
        "unified_social_credit_code": "91310000XXXXXXXXXX",
        "certification": {
            "business_license_url": "s3://test/business_license.pdf",
            "legal_person_id_url": "s3://test/legal_id.pdf",
            "authorization_letter_url": "s3://test/auth_letter.pdf",
            "submitted_at": datetime.utcnow().isoformat(),
            "verified_at": datetime.utcnow().isoformat(),
            "verified_by": "admin_001",
        },
        "contact": {
            "name": "张三",
            "phone": "13800138000",
            "email": "hr@test.com",
        },
        "website": "https://test-company.com",
        "industry": "互联网",
        "company_size": "100-500",
        "description": "一家专注于AI技术的创新公司",
        "status": "approved",
        "billing_info": {
            "plan": "monthly_pro",
            "monthly_quota": 10000,
        },
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }


@pytest.fixture(scope="function")
def sample_job_match() -> dict:
    """Return a sample job match for testing."""
    return {
        "id": f"match_{uuid.uuid4().hex[:8]}",
        "seeker_id": "prof_001",
        "job_id": "job_001",
        "match_score": 0.89,
        "match_factors": {
            "skill_match": 0.95,
            "experience_match": 0.85,
            "location_match": 1.0,
            "salary_match": 0.90,
            "overall": 0.89,
        },
        "status": "pending",
        "seeker_response": None,
        "seeker_message": None,
        "employer_response": None,
        "employer_message": None,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }


@pytest.fixture(scope="function")
def sample_resume_parse_result() -> dict:
    """Return a sample resume parse result for testing."""
    return {
        "parse_id": f"parse_{uuid.uuid4().hex[:8]}",
        "confidence": 0.94,
        "extracted_data": {
            "basic_info": {
                "name": "张三",
                "phone": "138****8000",
                "email": "zhangsan@example.com",
                "location": "上海",
                "gender": "男",
                "age": 28,
            },
            "work_experience": [
                {
                    "company": "字节跳动",
                    "title": "高级后端工程师",
                    "duration": "2021.06 - 至今",
                    "years": 2.5,
                    "description": "负责抖音电商核心服务开发",
                    "skills_used": ["Go", "微服务", "Kubernetes"],
                    "achievements": ["主导重构订单系统，QPS提升300%"],
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
            "projects": [
                {
                    "name": "高并发订单系统",
                    "description": "设计并实现支撑10万QPS的订单系统",
                    "technologies": ["Go", "Redis", "Kafka", "etcd"],
                },
            ],
            "total_work_years": 4.3,
        },
        "summary": {
            "text": "5年后端经验，字节跳动高工，Go/Java专家",
            "keywords": ["Go", "高并发", "微服务", "电商"],
            "job_intent_inferred": {
                "target_roles": ["后端工程师", "架构师"],
                "preferred_industries": ["互联网", "电商"],
                "career_stage": "高级/资深",
            },
        },
        "missing_or_unclear": ["当前是否在职"],
    }


# =============================================================================
# Utility Fixtures
# =============================================================================

@pytest.fixture(scope="function")
def fixtures_dir() -> str:
    """Return the path to the test fixtures directory."""
    return os.path.join(os.path.dirname(__file__), "fixtures")


@pytest.fixture(scope="function")
def load_fixture(fixtures_dir: str):
    """Load a fixture file from the fixtures directory."""
    def _load(filename: str) -> dict:
        filepath = os.path.join(fixtures_dir, filename)
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Fixture file not found: {filepath}")

        with open(filepath, "r", encoding="utf-8") as f:
            if filename.endswith(".json"):
                return json.load(f)
            else:
                return f.read()

    return _load


# =============================================================================
# Event Loop Fixture (for async tests)
# =============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
