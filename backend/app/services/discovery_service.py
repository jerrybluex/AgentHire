"""
Discovery Service
结构化搜索和过滤 - Agent 自主发现 API

平台不做匹配算法，由 Agent 自己判断是否匹配
支持按技能、城市、远程策略、薪资、工作年限等条件过滤
"""

from typing import Optional
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import SeekerProfile, JobPosting


class DiscoveryService:
    """
    Agent 自主发现服务
    平台只提供搜索/过滤 API，Agent 自己判断是否匹配

    支持的过滤条件：
    - skills: 技能列表（AND 匹配，即包含所有技能的职位）
    - city: 城市
    - remote_strategy: 远程策略 (remote/hybrid/onsite)
    - min_salary/max_salary: 薪资范围
    - experience_years: 工作年限
    """

    async def discover_jobs(
        self,
        db: AsyncSession,
        skills: Optional[list[str]] = None,
        city: Optional[str] = None,
        min_salary: Optional[int] = None,
        max_salary: Optional[int] = None,
        experience_years: Optional[int] = None,
        remote_strategy: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[dict]:
        """
        求职 Agent 发现职位
        Agent 根据条件自主筛选，平台返回所有符合条件的职位列表

        Args:
            db: Database session
            skills: 技能过滤（AND 匹配，即包含所有技能的职位）
            city: 城市过滤
            min_salary: 最低薪资（月薪，单位分或元，根据系统配置）
            max_salary: 最高薪资
            experience_years: 经验年限
            remote_strategy: 远程策略 (remote/hybrid/onsite)
            limit: 返回数量
            offset: 分页偏移

        Returns:
            符合条件的职位列表（平台不做匹配打分）
        """
        query = select(JobPosting).where(JobPosting.status == "active")

        # 城市过滤
        if city:
            query = query.where(
                JobPosting.location.op("->>")("city").ilike(f"%{city}%")
            )

        # 技能过滤（使用 JSON contains，AND 匹配）
        # requirements 格式: {"skills_required": ["Python", "Go"], "experience_years_min": 3}
        if skills:
            for skill in skills:
                query = query.where(
                    JobPosting.requirements.contains(skill)
                )

        # 远程策略过滤
        # location 格式: {"city": "上海", "remote_strategy": "hybrid"}
        if remote_strategy:
            query = query.where(
                JobPosting.location.op("->>")("remote_strategy").ilike(f"%{remote_strategy}%")
            )

        # 薪资过滤
        # compensation 格式: {"salary_range": {"min": 30000, "max": 50000, "currency": "CNY"}}
        if min_salary:
            query = query.where(
                JobPosting.compensation.contains({"salary_range": {"min": min_salary}})
            )
        if max_salary:
            query = query.where(
                JobPosting.compensation.contains({"salary_range": {"max": max_salary}})
            )

        # 经验年限过滤
        if experience_years:
            query = query.where(
                JobPosting.requirements.contains({"experience_years_min": experience_years})
            )

        query = query.offset(offset).limit(limit)
        result = await db.execute(query)
        jobs = result.scalars().all()

        # 返回原始数据，Agent 自己判断是否匹配
        return [job_to_dict(job) for job in jobs]

    async def discover_profiles(
        self,
        db: AsyncSession,
        skills: Optional[list[str]] = None,
        city: Optional[str] = None,
        min_experience: Optional[int] = None,
        max_salary_expectation: Optional[int] = None,
        remote_strategy: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[dict]:
        """
        企业 Agent 发现人才
        Agent 根据条件自主筛选，平台返回所有符合条件的求职者列表

        Args:
            db: Database session
            skills: 技能过滤
            city: 城市偏好
            min_experience: 最低工作经验（年）
            max_salary_expectation: 最高期望薪资
            remote_strategy: 远程策略偏好 (remote/hybrid/onsite)
            limit: 返回数量
            offset: 分页偏移

        Returns:
            符合条件的求职者列表
        """
        query = select(SeekerProfile).where(SeekerProfile.status == "active")

        # 技能过滤
        # job_intent 格式: {"skills": ["Python", "Go"], "preferred_cities": ["上海"], ...}
        if skills:
            for skill in skills:
                query = query.where(
                    SeekerProfile.job_intent.contains(skill)
                )

        # 城市偏好过滤
        if city:
            query = query.where(
                SeekerProfile.job_intent.contains(city)
            )

        # 远程策略过滤
        if remote_strategy:
            query = query.where(
                SeekerProfile.job_intent.contains(remote_strategy)
            )

        # 经验年限过滤
        if min_experience:
            query = query.where(
                SeekerProfile.job_intent.contains({"experience_years": min_experience})
            )

        # 期望薪资过滤
        if max_salary_expectation:
            query = query.where(
                SeekerProfile.job_intent.contains({"salary_range": {"max": max_salary_expectation}})
            )

        query = query.offset(offset).limit(limit)
        result = await db.execute(query)
        profiles = result.scalars().all()

        # 返回原始数据，Agent 自己判断是否匹配
        return [profile_to_dict(profile) for profile in profiles]


def job_to_dict(job: JobPosting) -> dict:
    """
    Convert JobPosting model to dictionary for API response.

    Returns structured job data including:
    - Basic info: id, title, enterprise_id, department
    - Structured fields: requirements, compensation, location
    - Timestamps: published_at, expires_at
    """
    return {
        "id": job.id,
        "title": job.title,
        "enterprise_id": job.enterprise_id,
        "department": job.department,
        "description": job.description,
        "responsibilities": job.responsibilities,
        "requirements": job.requirements,
        "compensation": job.compensation,
        "location": job.location,
        "status": job.status,
        "published_at": job.published_at.isoformat() if job.published_at else None,
        "expires_at": job.expires_at.isoformat() if job.expires_at else None,
        # 提取常用字段方便 Agent 使用
        "skills_required": job.requirements.get("skills_required", []) if isinstance(job.requirements, dict) else [],
        "city": job.location.get("city", "") if isinstance(job.location, dict) else "",
        "remote_strategy": job.location.get("remote_strategy", "") if isinstance(job.location, dict) else "",
        "salary_range": job.compensation.get("salary_range", {}) if isinstance(job.compensation, dict) else {},
    }


def profile_to_dict(profile: SeekerProfile) -> dict:
    """
    Convert SeekerProfile model to dictionary for API response.

    Returns structured profile data including:
    - Basic info: id, agent_id, nickname
    - Job intent: skills, preferred_cities, remote_strategy, experience_years, education_level, salary_range, job_types
    - Timestamps: last_active_at
    """
    # 从 job_intent 提取常用字段
    job_intent = profile.job_intent or {}
    return {
        "id": profile.id,
        "agent_id": profile.agent_id,
        "agent_type": profile.agent_type,
        "nickname": profile.nickname,
        "avatar_url": profile.avatar_url,
        "job_intent": job_intent,
        # 提取常用字段方便 Agent 使用
        "skills": job_intent.get("skills", []) if isinstance(job_intent, dict) else [],
        "preferred_cities": job_intent.get("preferred_cities", []) if isinstance(job_intent, dict) else [],
        "remote_strategy": job_intent.get("remote_strategy", "") if isinstance(job_intent, dict) else "",
        "experience_years": job_intent.get("experience_years", 0) if isinstance(job_intent, dict) else 0,
        "education_level": job_intent.get("education_level", "") if isinstance(job_intent, dict) else "",
        "salary_range": job_intent.get("salary_range", {}) if isinstance(job_intent, dict) else {},
        "job_types": job_intent.get("job_types", []) if isinstance(job_intent, dict) else [],
        "status": profile.status,
        "last_active_at": profile.last_active_at.isoformat() if profile.last_active_at else None,
    }


# Singleton instance
discovery_service = DiscoveryService()
