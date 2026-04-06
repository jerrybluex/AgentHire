"""
Matching Task
职位与候选人匹配逻辑
"""

from typing import Optional
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import JobPosting, SeekerProfile, JobMatch, Application


class MatchingService:
    """匹配服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def calculate_match_score(
        self,
        profile: SeekerProfile,
        job: JobPosting,
    ) -> float:
        """
        计算候选人与职位的匹配度（0-100）。

        计算逻辑：
        1. 技能匹配度（40%）
        2. 城市匹配度（20%）
        3. 薪资匹配度（20%）
        4. 经验匹配度（20%）
        """
        score = 0.0

        # 1. 技能匹配度
        job_skills = set(job.requirements.get("skills_required", []))
        profile_skills = set(profile.job_intent.get("skills", []))
        if job_skills and profile_skills:
            skill_match = len(job_skills & profile_skills) / len(job_skills)
            score += skill_match * 40

        # 2. 城市匹配度
        job_city = job.location.get("city", "") if job.location else ""
        profile_cities = profile.job_intent.get("preferred_cities", [])
        if job_city in profile_cities or not profile_cities:
            score += 20

        # 3. 薪资匹配度（简化）
        job_salary = job.compensation.get("salary_range", {}).get("min", 0) if job.compensation else 0
        profile_salary = profile.job_intent.get("salary_range", {}).get("min", 0)
        if profile_salary <= job_salary:
            score += 20

        # 4. 经验匹配度（简化）
        job_exp = job.requirements.get("experience_years_min", 0)
        profile_exp = profile.job_intent.get("experience_years", 0)
        if profile_exp >= job_exp:
            score += 20

        return min(score, 100.0)

    async def find_matching_jobs(
        self,
        profile: SeekerProfile,
        limit: int = 10,
    ) -> list[tuple[JobPosting, float]]:
        """为候选人查找匹配的职位"""
        # 获取所有活跃职位
        result = await self.db.execute(
            select(JobPosting).where(JobPosting.status == "active")
        )
        jobs = result.scalars().all()

        # 计算每个职位的匹配度
        matches = []
        for job in jobs:
            score = await self.calculate_match_score(profile, job)
            if score > 30:  # 只返回匹配度 > 30%
                matches.append((job, score))

        # 按匹配度排序
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches[:limit]

    async def find_matching_profiles(
        self,
        job: JobPosting,
        limit: int = 10,
    ) -> list[tuple[SeekerProfile, float]]:
        """为职位查找匹配的候选人"""
        result = await self.db.execute(
            select(SeekerProfile).where(SeekerProfile.status == "active")
        )
        profiles = result.scalars().all()

        matches = []
        for profile in profiles:
            score = await self.calculate_match_score(profile, job)
            if score > 30:
                matches.append((profile, score))

        matches.sort(key=lambda x: x[1], reverse=True)
        return matches[:limit]

    async def create_job_match(
        self,
        profile: SeekerProfile,
        job: JobPosting,
        score: float,
    ) -> Optional[JobMatch]:
        """创建匹配记录"""
        # 检查是否已存在匹配记录
        result = await self.db.execute(
            select(JobMatch).where(
                and_(
                    JobMatch.seeker_id == profile.id,
                    JobMatch.job_id == job.id,
                )
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            # 更新分数
            existing.match_score = score
            await self.db.flush()
            return existing

        # 创建新匹配
        match = JobMatch(
            seeker_id=profile.id,
            job_id=job.id,
            match_score=score,
            status="pending",
        )
        self.db.add(match)
        await self.db.flush()
        return match


# Factory function for dependency injection
def get_matching_service(db: AsyncSession) -> MatchingService:
    return MatchingService(db)
