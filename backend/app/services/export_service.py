"""
Export Service
数据导出服务 - 支持 Profile 和简历数据导出为 JSON/PDF
"""

import json
from typing import Optional
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import SeekerProfile, ResumeFile, Agent, generate_id


class ExportService:
    """Service for exporting profile and resume data."""

    async def export_profile_json(
        self,
        db: AsyncSession,
        profile_id: str,
        include_resume: bool = True,
    ) -> Optional[dict]:
        """
        Export profile data as JSON.

        Args:
            db: Database session
            profile_id: Profile ID to export
            include_resume: Whether to include resume data

        Returns:
            Profile data as dict or None if not found
        """
        result = await db.execute(
            select(SeekerProfile).where(SeekerProfile.id == profile_id)
        )
        profile = result.scalar_one_or_none()

        if not profile:
            return None

        # Get agent info
        agent_result = await db.execute(
            select(Agent).where(Agent.id == profile.agent_id)
        )
        agent = agent_result.scalar_one_or_none()

        # Get current resume
        resume_data = None
        if include_resume:
            resume_result = await db.execute(
                select(ResumeFile).where(
                    ResumeFile.profile_id == profile_id,
                    ResumeFile.is_current == True,
                )
            )
            resume = resume_result.scalar_one_or_none()
            if resume:
                resume_data = {
                    "id": resume.id,
                    "original_filename": resume.original_filename,
                    "file_type": resume.file_type,
                    "parse_status": resume.parse_status,
                    "parse_result": resume.parse_result,
                    "parse_confidence": resume.parse_confidence,
                    "parsed_at": resume.parsed_at.isoformat() if resume.parsed_at else None,
                }

        export_data = {
            "exported_at": datetime.utcnow().isoformat(),
            "profile": {
                "id": profile.id,
                "nickname": profile.nickname,
                "avatar_url": profile.avatar_url,
                "status": profile.status,
                "job_intent": profile.job_intent,
                "privacy": profile.privacy,
                "match_preferences": profile.match_preferences,
                "created_at": profile.created_at.isoformat(),
                "updated_at": profile.updated_at.isoformat(),
                "last_active_at": profile.last_active_at.isoformat() if profile.last_active_at else None,
            },
            "agent": {
                "id": agent.id if agent else None,
                "name": agent.name if agent else None,
                "type": agent.type if agent else None,
                "platform": agent.platform if agent else None,
            } if agent else None,
            "resume": resume_data,
        }

        return export_data

    async def export_resume_json(
        self,
        db: AsyncSession,
        resume_id: str,
    ) -> Optional[dict]:
        """
        Export resume data as JSON.

        Args:
            db: Database session
            resume_id: Resume file ID to export

        Returns:
            Resume data as dict or None if not found
        """
        result = await db.execute(
            select(ResumeFile).where(ResumeFile.id == resume_id)
        )
        resume = result.scalar_one_or_none()

        if not resume:
            return None

        # Get profile info
        profile_result = await db.execute(
            select(SeekerProfile).where(SeekerProfile.id == resume.profile_id)
        )
        profile = profile_result.scalar_one_or_none()

        export_data = {
            "exported_at": datetime.utcnow().isoformat(),
            "resume": {
                "id": resume.id,
                "profile_id": resume.profile_id,
                "original_filename": resume.original_filename,
                "file_size": resume.file_size,
                "file_type": resume.file_type,
                "mime_type": resume.mime_type,
                "parse_status": resume.parse_status,
                "parse_result": resume.parse_result,
                "parse_confidence": resume.parse_confidence,
                "parsed_at": resume.parsed_at.isoformat() if resume.parsed_at else None,
                "version": resume.version,
                "created_at": resume.created_at.isoformat(),
            },
            "profile": {
                "id": profile.id if profile else None,
                "nickname": profile.nickname if profile else None,
                "job_intent": profile.job_intent if profile else None,
            } if profile else None,
        }

        return export_data

    async def export_profile_history(
        self,
        db: AsyncSession,
        profile_id: str,
        limit: int = 10,
    ) -> Optional[dict]:
        """
        Get profile export history.

        Args:
            db: Database session
            profile_id: Profile ID
            limit: Maximum number of history records

        Returns:
            Export history data
        """
        result = await db.execute(
            select(SeekerProfile).where(SeekerProfile.id == profile_id)
        )
        profile = result.scalar_one_or_none()

        if not profile:
            return None

        # Get all resumes for this profile
        resumes_result = await db.execute(
            select(ResumeFile)
            .where(ResumeFile.profile_id == profile_id)
            .order_by(ResumeFile.created_at.desc())
            .limit(limit)
        )
        resumes = resumes_result.scalars().all()

        history = {
            "exported_at": datetime.utcnow().isoformat(),
            "profile_id": profile_id,
            "profile_updated_at": profile.updated_at.isoformat(),
            "resume_count": len(resumes),
            "resumes": [
                {
                    "id": r.id,
                    "original_filename": r.original_filename,
                    "version": r.version,
                    "is_current": r.is_current,
                    "parse_status": r.parse_status,
                    "created_at": r.created_at.isoformat(),
                }
                for r in resumes
            ],
        }

        return history

    def generate_export_filename(self, profile_id: str, export_type: str = "profile") -> str:
        """
        Generate export filename.

        Args:
            profile_id: Profile ID
            export_type: Type of export (profile, resume)

        Returns:
            Generated filename
        """
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        return f"agenthire_{export_type}_{profile_id}_{timestamp}.json"


# Singleton instance
export_service = ExportService()
