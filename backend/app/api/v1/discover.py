"""
Discovery API - Agent 自主发现
提供职位/人才搜索 API，由 Agent 自己判断是否匹配

原 matching.py 重构：
- 移除 /profile/{id} 和 /job/{id} 的匹配打分
- 改为 /jobs 和 /profiles 搜索 API
- 平台不做匹配，只返回原始数据

缓存策略：
- Discovery 结果默认缓存 60 秒
- 当 Job/Profile 数据变更时主动失效缓存
"""

import logging
from fastapi import APIRouter, Depends, Header, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.cache import get_cache, CacheManager
from app.services.discovery_service import discovery_service
from app.services.enterprise_service import enterprise_service

logger = logging.getLogger(__name__)
router = APIRouter()


class DiscoverJobsResponse(BaseModel):
    """职位发现响应"""
    success: bool = True
    data: list = Field(default_factory=list)
    total: int = 0


class DiscoverProfilesResponse(BaseModel):
    """人才发现响应"""
    success: bool = True
    data: list = Field(default_factory=list)
    total: int = 0


async def get_api_key_optional(
    x_api_key: str = Header(None, description="API Key (optional)"),
    db: AsyncSession = Depends(get_db),
) -> tuple[str, str] | None:
    """
    Validate API key if provided, return (enterprise_id, api_key_id) or None.
    Used for B端 endpoints that support optional API Key.
    """
    if not x_api_key:
        return None
    result = await enterprise_service.validate_api_key(db, x_api_key)
    if not result:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )
    return result


@router.get(
    "/jobs",
    response_model=DiscoverJobsResponse,
    summary="发现职位",
    description="求职 Agent 搜索职位，平台返回符合条件的职位列表（不做匹配打分）",
)
async def discover_jobs(
    skills: str = Query(None, description="技能列表，逗号分隔"),
    city: str = Query(None, description="城市"),
    remote_strategy: str = Query(None, description="远程策略 (remote/hybrid/onsite)"),
    min_salary: int = Query(None, description="最低月薪"),
    max_salary: int = Query(None, description="最高月薪"),
    experience_years: int = Query(None, description="工作年限"),
    limit: int = Query(20, ge=1, le=100, description="返回数量"),
    offset: int = Query(0, ge=0, description="分页偏移"),
    db: AsyncSession = Depends(get_db),
    cache: CacheManager = Depends(get_cache),
) -> DiscoverJobsResponse:
    """
    职位发现 API (C端)
    Agent 根据条件自主筛选，平台返回所有符合条件的职位

    缓存说明：
    - 查询参数作为缓存 key 的一部分
    - TTL 60 秒
    - 技能列表排序后参与 hash 计算
    """
    skill_list = [s.strip() for s in skills.split(",")] if skills else None

    # Try to get from cache first
    cached_jobs = await cache.get_discover_jobs(
        skills=skill_list,
        city=city,
        min_salary=min_salary,
        max_salary=max_salary,
        experience_years=experience_years,
        limit=limit,
        offset=offset,
    )

    if cached_jobs is not None:
        logger.debug(f"Cache hit for discover_jobs, returning {len(cached_jobs)} jobs")
        return DiscoverJobsResponse(
            success=True,
            data=cached_jobs,
            total=len(cached_jobs),
        )

    # Cache miss - fetch from database
    jobs = await discovery_service.discover_jobs(
        db=db,
        skills=skill_list,
        city=city,
        remote_strategy=remote_strategy,
        min_salary=min_salary,
        max_salary=max_salary,
        experience_years=experience_years,
        limit=limit,
        offset=offset,
    )

    # Cache the result
    await cache.set_discover_jobs(
        data=jobs,
        skills=skill_list,
        city=city,
        min_salary=min_salary,
        max_salary=max_salary,
        experience_years=experience_years,
        limit=limit,
        offset=offset,
    )

    return DiscoverJobsResponse(
        success=True,
        data=jobs,
        total=len(jobs),
    )


@router.get(
    "/profiles",
    response_model=DiscoverProfilesResponse,
    summary="发现人才",
    description="企业 Agent 搜索人才，平台返回符合条件的求职者列表（不做匹配打分）",
)
async def discover_profiles(
    skills: str = Query(None, description="技能列表，逗号分隔"),
    city: str = Query(None, description="城市"),
    remote_strategy: str = Query(None, description="远程策略偏好 (remote/hybrid/onsite)"),
    min_experience: int = Query(None, description="最低工作经验"),
    max_salary_expectation: int = Query(None, description="最高期望薪资"),
    limit: int = Query(20, ge=1, le=100, description="返回数量"),
    offset: int = Query(0, ge=0, description="分页偏移"),
    db: AsyncSession = Depends(get_db),
    api_key_info: tuple = Depends(get_api_key_optional),
    cache: CacheManager = Depends(get_cache),
) -> DiscoverProfilesResponse:
    """
    人才发现 API (B端)
    Agent 根据条件自主筛选，平台返回所有符合条件的求职者
    需要 API Key 认证，会记录计费

    缓存说明：
    - 查询参数作为缓存 key 的一部分
    - TTL 60 秒
    - 技能列表排序后参与 hash 计算
    - 不缓存需要计费的请求
    """
    skill_list = [s.strip() for s in skills.split(",")] if skills else None

    # Try to get from cache first (only for non-authenticated or cached results)
    # Note: authenticated requests are not cached to ensure accurate billing
    if not api_key_info:
        cached_profiles = await cache.get_discover_profiles(
            skills=skill_list,
            city=city,
            min_experience=min_experience,
            max_salary_expectation=max_salary_expectation,
            limit=limit,
            offset=offset,
        )

        if cached_profiles is not None:
            logger.debug(f"Cache hit for discover_profiles, returning {len(cached_profiles)} profiles")
            return DiscoverProfilesResponse(
                success=True,
                data=cached_profiles,
                total=len(cached_profiles),
            )

    # Cache miss or authenticated request - fetch from database
    profiles = await discovery_service.discover_profiles(
        db=db,
        skills=skill_list,
        city=city,
        remote_strategy=remote_strategy,
        min_experience=min_experience,
        max_salary_expectation=max_salary_expectation,
        limit=limit,
        offset=offset,
    )

    # Record billing for profile discovery (if authenticated)
    if api_key_info:
        enterprise_id, api_key_id = api_key_info
        await enterprise_service.record_usage(
            db=db,
            enterprise_id=enterprise_id,
            api_key_id=api_key_id,
            usage_type="profile_view",
            quantity=len(profiles),
            reference_id=None,
        )
    else:
        # Cache unauthenticated results (no billing required)
        await cache.set_discover_profiles(
            data=profiles,
            skills=skill_list,
            city=city,
            min_experience=min_experience,
            max_salary_expectation=max_salary_expectation,
            limit=limit,
            offset=offset,
        )

    return DiscoverProfilesResponse(
        success=True,
        data=profiles,
        total=len(profiles),
    )