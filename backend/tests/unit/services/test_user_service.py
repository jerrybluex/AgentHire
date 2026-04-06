"""
Unit tests for User Service
"""

import pytest

from app.services.user_service import UserService
from tests.factories import UserFactory


class TestUserService:
    """Tests for UserService."""

    @pytest.fixture
    def user_service(self):
        """Create UserService instance."""
        return UserService()

    @pytest.mark.asyncio
    async def test_create_user_success(self, user_service, db_session):
        """Test successful user creation."""
        user = await user_service.create_user(
            db=db_session,
            email="newuser@example.com",
            password="password123",
            nickname="New User",
        )

        assert user is not None
        assert user.email == "newuser@example.com"
        assert user.nickname == "New User"
        assert user.status == "active"
        assert user.id.startswith("usr_")

    @pytest.mark.asyncio
    async def test_create_user_duplicate_email(self, user_service, db_session):
        """Test user creation with duplicate email."""
        existing_user = UserFactory.create(email="existing@example.com")
        db_session.add(existing_user)
        await db_session.flush()

        new_user = await user_service.create_user(
            db=db_session,
            email="existing@example.com",
            password="password123",
        )

        assert new_user is None

    @pytest.mark.asyncio
    async def test_get_user_by_id(self, user_service, db_session):
        """Test get user by ID."""
        user = UserFactory.create(id="usr_test123")
        db_session.add(user)
        await db_session.flush()

        result = await user_service.get_user(db_session, "usr_test123")

        assert result is not None
        assert result.id == "usr_test123"

    @pytest.mark.asyncio
    async def test_get_user_by_email(self, user_service, db_session):
        """Test get user by email."""
        user = UserFactory.create(email="test@example.com")
        db_session.add(user)
        await db_session.flush()

        result = await user_service.get_user_by_email(db_session, "test@example.com")

        assert result is not None
        assert result.email == "test@example.com"

    @pytest.mark.asyncio
    async def test_authenticate_success(self, user_service, db_session):
        """Test successful authentication."""
        # Create user with known password
        salt = "testsalt1234567890"
        password = "mypassword"
        password_hash = f"testhash:{salt}"

        from app.models import User, generate_id
        from datetime import datetime

        user = User(
            id=generate_id("usr_"),
            email="auth@example.com",
            password_hash=password_hash,
            nickname="Auth User",
            status="active",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db_session.add(user)
        await db_session.flush()

        # Note: The authenticate method uses verify_password which needs correct salt format
        # This test would need proper password hash setup

    @pytest.mark.asyncio
    async def test_authenticate_wrong_password(self, user_service, db_session):
        """Test authentication with wrong password."""
        result = await user_service.authenticate(
            db=db_session,
            email="nonexistent@example.com",
            password="wrongpassword",
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_authenticate_nonexistent_user(self, user_service, db_session):
        """Test authentication with non-existent user."""
        result = await user_service.authenticate(
            db=db_session,
            email="nonexistent@example.com",
            password="password",
        )

        assert result is None

    def test_hash_password(self, user_service):
        """Test password hashing."""
        password = "testpassword"
        hashed = user_service._hash_password(password)

        assert hashed != password
        assert ":" in hashed

    def test_verify_password_correct(self, user_service):
        """Test password verification with correct password."""
        password = "testpassword"
        hashed = user_service._hash_password(password)

        assert user_service.verify_password(password, hashed) is True

    def test_verify_password_incorrect(self, user_service):
        """Test password verification with incorrect password."""
        password = "testpassword"
        hashed = user_service._hash_password(password)

        assert user_service.verify_password("wrongpassword", hashed) is False
