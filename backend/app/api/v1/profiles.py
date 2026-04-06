"""
Profile management API endpoints.
Provides CRUD operations for seeker profiles.
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.profile_service import profile_service
from app.api.deps import verify_agent_signature

router = APIRouter()


class ProfileCreateRequest(BaseModel):
    """Profile creation request."""

    profile: dict = Field(..., description="Profile data")
    agent_metadata: dict = Field(default_factory=dict, description="Agent metadata")


class ProfileUpdateRequest(BaseModel):
    """Profile update request."""

    profile: dict = Field(..., description="Profile data to update")


class ProfileResponse(BaseModel):
    """Profile response wrapper."""

    success: bool = True
    data: dict = Field(default_factory=dict)
    message: str | None = None


class ProfileListResponse(BaseModel):
    """Paginated profile list response."""

    success: bool = True
    data: list = Field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 20
    has_next: bool = False
    has_prev: bool = False


@router.post(
    "",
    response_model=ProfileResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create profile",
    description="Create a new seeker profile (requires agent authentication)",
)
async def create_profile(
    request: ProfileCreateRequest,
    db: AsyncSession = Depends(get_db),
    agent_id: str = Depends(verify_agent_signature),
) -> ProfileResponse:
    """Create a new seeker profile from parsed resume data or manual input."""
    try:
        profile = await profile_service.create_profile(
            db=db,
            profile_data=request.profile,
            agent_metadata={**request.agent_metadata, "authenticated_agent_id": agent_id},
        )

        return ProfileResponse(
            success=True,
            data={
                "profile_id": profile.id,
                "agent_id": agent_id,
                "created_at": profile.created_at.isoformat() if profile.created_at else None,
            },
            message="Profile created successfully",
        )
    except Exception as e:
        return ProfileResponse(
            success=False,
            data={},
            message=f"Failed to create profile: {str(e)}",
        )


@router.get(
    "/{profile_id}",
    response_model=ProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Get profile",
    description="Get a seeker profile by ID",
)
async def get_profile(
    profile_id: str,
    db: AsyncSession = Depends(get_db),
) -> ProfileResponse:
    """Get a seeker profile by ID."""
    profile = await profile_service.get_profile(db, profile_id)

    if not profile:
        return ProfileResponse(
            success=False,
            data={},
            message=f"Profile not found: {profile_id}",
        )

    return ProfileResponse(
        success=True,
        data={
            "id": profile.id,
            "agent_id": profile.agent_id,
            "agent_type": profile.agent_type,
            "status": profile.status,
            "nickname": profile.nickname,
            "avatar_url": profile.avatar_url,
            "job_intent": profile.job_intent,
            "resume_data": profile.resume_data,
            "privacy": profile.privacy,
            "match_preferences": profile.match_preferences,
            "created_at": profile.created_at.isoformat() if profile.created_at else None,
            "updated_at": profile.updated_at.isoformat() if profile.updated_at else None,
            "last_active_at": profile.last_active_at.isoformat() if profile.last_active_at else None,
        },
        message="Profile retrieved successfully",
    )


@router.put(
    "/{profile_id}",
    response_model=ProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Update profile",
    description="Update a seeker profile (requires agent authentication)",
)
async def update_profile(
    profile_id: str,
    request: ProfileUpdateRequest,
    db: AsyncSession = Depends(get_db),
    agent_id: str = Depends(verify_agent_signature),
) -> ProfileResponse:
    """Update an existing seeker profile."""
    # Check ownership
    existing = await profile_service.get_profile(db, profile_id)
    if not existing:
        return ProfileResponse(
            success=False,
            data={},
            message=f"Profile not found: {profile_id}",
        )
    if existing.agent_id != agent_id:
        return ProfileResponse(
            success=False,
            data={},
            message="Unauthorized: you can only update your own profile",
        )

    profile = await profile_service.update_profile(
        db=db,
        profile_id=profile_id,
        profile_data=request.profile,
    )

    return ProfileResponse(
        success=True,
        data={
            "profile_id": profile.id,
            "updated_at": profile.updated_at.isoformat() if profile.updated_at else None,
        },
        message="Profile updated successfully",
    )


@router.delete(
    "/{profile_id}",
    response_model=ProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete profile",
    description="Soft delete a seeker profile (requires agent authentication)",
)
async def delete_profile(
    profile_id: str,
    db: AsyncSession = Depends(get_db),
    agent_id: str = Depends(verify_agent_signature),
) -> ProfileResponse:
    """Soft delete a profile (sets status to 'deleted')."""
    # Check ownership
    existing = await profile_service.get_profile(db, profile_id)
    if not existing:
        return ProfileResponse(
            success=False,
            data={},
            message=f"Profile not found: {profile_id}",
        )
    if existing.agent_id != agent_id:
        return ProfileResponse(
            success=False,
            data={},
            message="Unauthorized: you can only delete your own profile",
        )

    deleted = await profile_service.delete_profile(db, profile_id)

    return ProfileResponse(
        success=True,
        data={"profile_id": profile_id},
        message="Profile deleted successfully",
    )


@router.get(
    "",
    response_model=ProfileListResponse,
    status_code=status.HTTP_200_OK,
    summary="List profiles",
    description="List seeker profiles with optional filters",
)
async def list_profiles(
    agent_id: Optional[str] = Query(None, description="Filter by agent ID"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
) -> ProfileListResponse:
    """List seeker profiles with pagination and filters."""
    offset = (page - 1) * page_size

    profiles, total = await profile_service.list_profiles(
        db=db,
        agent_id=agent_id,
        status=status_filter,
        limit=page_size,
        offset=offset,
    )

    has_next = (page * page_size) < total
    has_prev = page > 1

    return ProfileListResponse(
        success=True,
        data=[
            {
                "id": p.id,
                "agent_id": p.agent_id,
                "status": p.status,
                "nickname": p.nickname,
                "job_intent": p.job_intent,
                "created_at": p.created_at.isoformat() if p.created_at else None,
            }
            for p in profiles
        ],
        total=total,
        page=page,
        page_size=page_size,
        has_next=has_next,
        has_prev=has_prev,
    )
