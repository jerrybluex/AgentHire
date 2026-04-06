"""
API dependencies for dependency injection.
Provides common dependencies like database sessions and authentication.
"""

import os
from typing import AsyncGenerator, Optional

from fastapi import Depends, Header, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db


class CurrentUser(BaseModel):
    """Current authenticated user model."""

    user_id: Optional[str] = None
    is_authenticated: bool = False
    api_key: Optional[str] = None


# Security scheme for JWT tokens (future implementation)
security = HTTPBearer(auto_error=False)


# async def get_db() -> AsyncGenerator[AsyncSession, None]:
#     """Get database session."""
#     async with async_session_maker() as session:
#         try:
#             yield session
#         except Exception:
#             await session.rollback()
#             raise
#         finally:
#             await session.close()


async def get_current_user(
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> CurrentUser:
    """
    Get current user from authentication header or API key.

    This is a placeholder implementation. Full authentication will be implemented
    after the security module is set up.
    """
    # TODO: Implement proper JWT token validation and API key verification
    # For now, return anonymous user
    return CurrentUser(
        user_id=None,
        is_authenticated=False,
        api_key=x_api_key,
    )


async def require_auth(
    user: CurrentUser = Depends(get_current_user),
) -> CurrentUser:
    """Require authentication."""
    if not user.is_authenticated and not user.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def get_pagination(
    page: int = 1,
    limit: int = 20,
) -> dict:
    """
    Get pagination parameters.

    Args:
        page: Page number (1-indexed)
        limit: Items per page

    Returns:
        Dictionary with pagination parameters
    """
    # Validate and clamp values
    page = max(1, page)
    limit = min(max(1, limit), 100)  # Max 100 items per page

    return {
        "page": page,
        "limit": limit,
        "offset": (page - 1) * limit,
    }


# =============================================================================
# Agent Authentication Dependency
# =============================================================================


async def verify_agent_signature(
    x_agent_id: str = Header(..., description="Agent ID"),
    x_timestamp: str = Header(..., description="Request timestamp"),
    x_signature: str = Header(..., description="HMAC signature"),
) -> str:
    """
    Dependency to verify agent HMAC signature.

    The signature is calculated as:
    HMAC-SHA256(agent_secret, agent_id + timestamp)
    """
    from app.core.database import get_db_context
    from app.services.agent_service import agent_service

    try:
        timestamp_int = int(x_timestamp)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid timestamp format",
        )

    async with get_db_context() as db:
        authenticated_agent_id = await agent_service.authenticate(
            db, x_agent_id, timestamp_int, x_signature
        )

        if not authenticated_agent_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication failed",
            )

        return authenticated_agent_id


async def verify_agent(
    x_agent_id: str = Header(..., description="Agent ID"),
    x_timestamp: str = Header(..., description="Request timestamp"),
    x_signature: str = Header(..., description="HMAC signature"),
) -> dict:
    """
    Dependency to verify agent and return agent info dict.

    Returns a dict with:
    - agent_id: Agent ID
    - principal_id: Agent's linked principal ID
    - type: Agent type (seeker/employer)
    """
    from app.core.database import get_db_context
    from app.services.agent_service import agent_service

    try:
        timestamp_int = int(x_timestamp)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid timestamp format",
        )

    async with get_db_context() as db:
        authenticated_agent_id = await agent_service.authenticate(
            db, x_agent_id, timestamp_int, x_signature
        )

        if not authenticated_agent_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication failed",
            )

        # Get full agent info
        agent = await agent_service.get_agent(db, x_agent_id)
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Agent not found",
            )

        return {
            "agent_id": agent["id"],
            "principal_id": agent.get("principal_id"),
            "type": agent.get("type"),
        }


async def get_current_admin(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Administrator authentication (temporary implementation).
    Validates that the X-Admin-Token header matches the ADMIN_TOKEN environment variable.
    """
    admin_token = request.headers.get("X-Admin-Token")
    expected_token = os.environ.get("ADMIN_TOKEN")
    if not expected_token:
        raise RuntimeError("ADMIN_TOKEN environment variable must be set in production")

    if not admin_token or admin_token != expected_token:
        raise HTTPException(status_code=403, detail="Admin access required")

    return {"role": "admin", "token": admin_token}


async def get_current_employer(
    x_enterprise_id: str = Header(..., description="Enterprise ID"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Dependency to get current employer from Enterprise-ID header.

    Returns a dict with:
    - enterprise_id: Enterprise ID
    - principal_id: Enterprise's linked principal ID
    """
    from sqlalchemy import select
    from app.models import Enterprise

    result = await db.execute(
        select(Enterprise).where(Enterprise.id == x_enterprise_id)
    )
    enterprise = result.scalar_one_or_none()

    if not enterprise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Enterprise not found",
        )

    if enterprise.status != "approved":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Enterprise not approved",
        )

    return {
        "enterprise_id": enterprise.id,
        "principal_id": enterprise.tenant_id,  # tenant_id as principal linkage
    }
