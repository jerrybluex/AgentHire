"""
Profile Service
求职者档案的CRUD操作和业务逻辑
"""

from typing import Optional
from datetime import datetime

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import SeekerProfile, ResumeFile, generate_id


class ProfileService:
    """Service for managing seeker profiles."""

    async def create_profile(
        self,
        db: AsyncSession,
        profile_data: dict,
        agent_metadata: dict,
    ) -> SeekerProfile:
        """
        Create a new seeker profile.

        Args:
            db: Database session
            profile_data: Profile data from request
            agent_metadata: Agent information

        Returns:
            Created SeekerProfile instance
        """
        # Extract nested data
        basic_info = profile_data.get("basic_info", {})
        job_intent = profile_data.get("job_intent", {})
        privacy = profile_data.get("privacy", {})
        match_preferences = profile_data.get("match_preferences", {})

        # Create profile (Agent 自主判断匹配，不依赖平台算法)
        profile = SeekerProfile(
            id=generate_id("prof_"),
            agent_id=agent_metadata.get("agent_id", "unknown"),
            agent_type=agent_metadata.get("agent_type", "openclaw"),
            nickname=basic_info.get("nickname"),
            avatar_url=basic_info.get("avatar_url"),
            job_intent=job_intent,
            privacy=privacy,
            match_preferences=match_preferences,
        )

        db.add(profile)
        await db.flush()

        return profile

    async def get_profile(
        self,
        db: AsyncSession,
        profile_id: str,
    ) -> Optional[SeekerProfile]:
        """
        Get a profile by ID.

        Args:
            db: Database session
            profile_id: Profile ID

        Returns:
            SeekerProfile or None
        """
        result = await db.execute(
            select(SeekerProfile).where(SeekerProfile.id == profile_id)
        )
        return result.scalar_one_or_none()

    async def update_profile(
        self,
        db: AsyncSession,
        profile_id: str,
        profile_data: dict,
    ) -> Optional[SeekerProfile]:
        """
        Update an existing profile.

        Args:
            db: Database session
            profile_id: Profile ID
            profile_data: Updated profile data

        Returns:
            Updated SeekerProfile or None
        """
        profile = await self.get_profile(db, profile_id)
        if not profile:
            return None

        # Update fields
        if "basic_info" in profile_data:
            basic_info = profile_data["basic_info"]
            if "nickname" in basic_info:
                profile.nickname = basic_info["nickname"]
            if "avatar_url" in basic_info:
                profile.avatar_url = basic_info["avatar_url"]

        if "job_intent" in profile_data:
            profile.job_intent = profile_data["job_intent"]

        if "privacy" in profile_data:
            profile.privacy = profile_data["privacy"]

        if "match_preferences" in profile_data:
            profile.match_preferences = profile_data["match_preferences"]

        if "status" in profile_data:
            profile.status = profile_data["status"]

        profile.updated_at = datetime.utcnow()

        await db.flush()
        return profile

    async def delete_profile(
        self,
        db: AsyncSession,
        profile_id: str,
    ) -> bool:
        """
        Soft delete a profile (set status to deleted).

        Args:
            db: Database session
            profile_id: Profile ID

        Returns:
            True if deleted, False if not found
        """
        profile = await self.get_profile(db, profile_id)
        if not profile:
            return False

        profile.status = "deleted"
        profile.updated_at = datetime.utcnow()
        await db.flush()
        return True

    async def list_profiles(
        self,
        db: AsyncSession,
        agent_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[SeekerProfile], int]:
        """
        List profiles with optional filters.

        Args:
            db: Database session
            agent_id: Filter by agent ID
            status: Filter by status
            limit: Result limit
            offset: Result offset

        Returns:
            Tuple of (profiles, total_count)
        """
        query = select(SeekerProfile)

        if agent_id:
            query = query.where(SeekerProfile.agent_id == agent_id)

        if status:
            query = query.where(SeekerProfile.status == status)
        else:
            # Default to active profiles only
            query = query.where(SeekerProfile.status == "active")

        # Get total count
        from sqlalchemy import func

        count_result = await db.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar() or 0

        # Apply pagination
        query = query.offset(offset).limit(limit)
        result = await db.execute(query)
        profiles = result.scalars().all()

        return list(profiles), total

    async def attach_resume(
        self,
        db: AsyncSession,
        profile_id: str,
        resume_file_id: str,
    ) -> Optional[SeekerProfile]:
        """
        Attach a resume file to a profile.

        Args:
            db: Database session
            profile_id: Profile ID
            resume_file_id: Resume file ID

        Returns:
            Updated profile or None
        """
        profile = await self.get_profile(db, profile_id)
        if not profile:
            return None

        # Verify resume exists and belongs to this profile
        result = await db.execute(
            select(ResumeFile).where(
                ResumeFile.id == resume_file_id,
                ResumeFile.profile_id == profile_id,
            )
        )
        resume = result.scalar_one_or_none()
        if not resume:
            return None

        # Mark other resumes as not current
        await db.execute(
            update(ResumeFile)
            .where(
                ResumeFile.profile_id == profile_id,
                ResumeFile.id != resume_file_id,
            )
            .values(is_current=False)
        )

        # Mark this resume as current
        resume.is_current = True
        await db.flush()

        return profile


# Singleton instance
profile_service = ProfileService()
