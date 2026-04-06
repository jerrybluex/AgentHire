"""
User Service
用户服务 - 用户注册、登录、认证
"""

import secrets
import hashlib
from typing import Optional
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User, generate_id


class UserService:
    """Service for managing users."""

    async def create_user(
        self,
        db: AsyncSession,
        email: str,
        password: str,
        nickname: Optional[str] = None,
    ) -> Optional[User]:
        """
        Create a new user.

        Args:
            db: Database session
            email: User email
            password: Plain text password
            nickname: Optional nickname

        Returns:
            Created User or None if email exists
        """
        # Check if email already exists
        existing = await self.get_user_by_email(db, email)
        if existing:
            return None

        user = User(
            id=generate_id("usr_"),
            email=email,
            password_hash=self._hash_password(password),
            nickname=nickname,
            status="active",
        )

        db.add(user)
        await db.flush()

        return user

    async def get_user(
        self,
        db: AsyncSession,
        user_id: str,
    ) -> Optional[User]:
        """Get a user by ID."""
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_user_by_email(
        self,
        db: AsyncSession,
        email: str,
    ) -> Optional[User]:
        """Get a user by email."""
        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def authenticate(
        self,
        db: AsyncSession,
        email: str,
        password: str,
    ) -> Optional[User]:
        """
        Authenticate a user with email and password.

        Args:
            db: Database session
            email: User email
            password: Plain text password

        Returns:
            User if authenticated, None otherwise
        """
        user = await self.get_user_by_email(db, email)
        if not user:
            return None

        if user.status != "active":
            return None

        if not self.verify_password(password, user.password_hash):
            return None

        return user

    def _hash_password(self, password: str) -> str:
        """Hash a password using SHA-256 with salt."""
        salt = secrets.token_hex(16)
        return hashlib.sha256(f"{salt}{password}".encode()).hexdigest() + ":" + salt

    def verify_password(self, password: str, stored_hash: str) -> bool:
        """Verify a password against stored hash."""
        try:
            hash_part, salt = stored_hash.rsplit(":", 1)
            return hashlib.sha256(f"{salt}{password}".encode()).hexdigest() == hash_part
        except ValueError:
            return False


# Singleton instance
user_service = UserService()
