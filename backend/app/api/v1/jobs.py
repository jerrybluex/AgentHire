"""
Job posting API endpoints.
Provides CRUD operations for job postings.
"""

from typing import Optional

from fastapi import APIRouter, Depends, Header, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.cache import get_cache, CacheManager
from app.models import Job
from app.services.job_service import job_service
from app.services.enterprise_service import enterprise_service
from app.services.discovery_service import discovery_service
from app.services.metering_service import metering_service

router = APIRouter()


class JobCreateRequest(BaseModel):
    """Job creation request."""

    job: dict = Field(..., description="Job posting data")
    publish_options: dict = Field(default_factory=dict, description="Publishing options")


class JobUpdateRequest(BaseModel):
    """Job update request."""

    job: dict = Field(..., description="Job data to update")


class JobResponse(BaseModel):
    """Job response wrapper."""

    success: bool = True
    data: dict = Field(default_factory=dict)
    message: str | None = None


class JobListResponse(BaseModel):
    """Paginated job list response."""

    success: bool = True
    data: list = Field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 20
    has_next: bool = False
    has_prev: bool = False


class JobSearchResponse(BaseModel):
    """Job search response (PRD v2 /jobs/search alias)."""

    success: bool = True
    data: list = Field(default_factory=list)
    total: int = 0


async def get_api_key_enterprise(
    x_api_key: str = Header(..., description="API Key"),
    db: AsyncSession = Depends(get_db),
) -> tuple[str, str]:
    """
    Validate API key and return (enterprise_id, api_key_id).
    """
    result = await enterprise_service.validate_api_key(db, x_api_key)
    if not result:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )
    return result


@router.post(
    "",
    response_model=JobResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create job",
    description="Create a new job posting",
)
async def create_job(
    request: JobCreateRequest,
    db: AsyncSession = Depends(get_db),
    api_key_info: tuple = Depends(get_api_key_enterprise),
) -> JobResponse:
    """Create a new job posting for an approved enterprise."""
    enterprise_id, api_key_id = api_key_info

    try:
        job = await job_service.create_job(
            db=db,
            enterprise_id=enterprise_id,
            api_key_id=api_key_id,
            job_data=request.job,
            publish_options=request.publish_options,
        )

        if not job:
            return JobResponse(
                success=False,
                data={},
                message="Enterprise not found or not approved",
            )

        # Record billing for job post
        await enterprise_service.record_usage(
            db=db,
            enterprise_id=enterprise_id,
            api_key_id=api_key_id,
            usage_type="job_post",
            quantity=1,
            reference_id=job.id,
        )

        # Record metering event for PRD v2 usage tracking
        await metering_service.record_usage(
            db=db,
            enterprise_id=enterprise_id,
            usage_type="job_posted",
            metadata={"job_id": job.id},
        )

        return JobResponse(
            success=True,
            data={
                "job_id": job.id,
                "status": job.status,
                "published_at": job.published_at.isoformat() if job.published_at else None,
                "expires_at": job.expires_at.isoformat() if job.expires_at else None,
            },
            message="Job posted successfully",
        )
    except Exception as e:
        return JobResponse(
            success=False,
            data={},
            message=f"Failed to create job: {str(e)}",
        )


# NOTE: /search must be before /{job_id} to avoid route conflict
# FastAPI matches routes in definition order

@router.get(
    "",
    response_model=JobListResponse,
    status_code=status.HTTP_200_OK,
    summary="List jobs",
    description="List job postings with filters",
)
async def list_jobs(
    enterprise_id: Optional[str] = Query(None, description="Filter by enterprise"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    city: Optional[str] = Query(None, description="Filter by city"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
) -> JobListResponse:
    """List job postings with pagination and filters."""
    offset = (page - 1) * page_size

    jobs, total = await job_service.list_jobs(
        db=db,
        enterprise_id=enterprise_id,
        status=status_filter,
        city=city,
        limit=page_size,
        offset=offset,
    )

    has_next = (page * page_size) < total
    has_prev = page > 1

    return JobListResponse(
        success=True,
        data=[
            {
                "id": j.id,
                "enterprise_id": j.enterprise_id,
                "title": j.title,
                "department": j.department,
                "requirements": j.requirements,
                "compensation": j.compensation,
                "location": j.location,
                "status": j.status,
                "published_at": j.published_at.isoformat() if j.published_at else None,
            }
            for j in jobs
        ],
        total=total,
        page=page,
        page_size=page_size,
        has_next=has_next,
        has_prev=has_prev,
    )


@router.get(
    "/search",
    response_model=JobSearchResponse,
    summary="Search jobs (PRD v2)",
    description="Search jobs by skills, city, salary, etc. Alias for /discover/jobs (PRD v2 compliant)",
)
async def search_jobs(
    skills: str = Query(None, description="Skills filter, comma-separated"),
    city: str = Query(None, description="City filter"),
    remote_strategy: str = Query(None, description="Remote strategy (remote/hybrid/onsite)"),
    min_salary: int = Query(None, description="Minimum monthly salary"),
    max_salary: int = Query(None, description="Maximum monthly salary"),
    experience_years: int = Query(None, description="Required experience years"),
    limit: int = Query(20, ge=1, le=100, description="Number of results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    db: AsyncSession = Depends(get_db),
    cache: CacheManager = Depends(get_cache),
) -> JobSearchResponse:
    """
    Search jobs by various criteria.
    PRD v2 compliant endpoint at /jobs/search (alias for /discover/jobs).
    """
    skill_list = [s.strip() for s in skills.split(",")] if skills else None

    # Try cache first
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
        return JobSearchResponse(success=True, data=cached_jobs, total=len(cached_jobs))

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

    return JobSearchResponse(success=True, data=jobs, total=len(jobs))


# /{job_id} routes MUST be after /search to avoid route conflict
# (e.g., /jobs/search would match /{job_id}="search" otherwise)

@router.get(
    "/{job_id}",
    response_model=JobResponse,
    status_code=status.HTTP_200_OK,
    summary="Get job",
    description="Get a job posting by ID",
)
async def get_job(
    job_id: str,
    db: AsyncSession = Depends(get_db),
) -> JobResponse:
    """Get a job posting by ID."""
    job = await job_service.get_job(db, job_id)

    if not job:
        return JobResponse(
            success=False,
            data={},
            message=f"Job not found: {job_id}",
        )

    return JobResponse(
        success=True,
        data={
            "id": job.id,
            "enterprise_id": job.enterprise_id,
            "title": job.title,
            "department": job.department,
            "description": job.description,
            "responsibilities": job.responsibilities,
            "requirements": job.requirements,
            "compensation": job.compensation,
            "location": job.location,
            "status": job.status,
            "published_at": job.published_at.isoformat() if job.published_at else None,
            "expires_at": job.expires_at.isoformat() if job.expires_at else None,
        },
        message="Job retrieved successfully",
    )


@router.put(
    "/{job_id}",
    response_model=JobResponse,
    status_code=status.HTTP_200_OK,
    summary="Update job",
    description="Update a job posting",
)
async def update_job(
    job_id: str,
    request: JobUpdateRequest,
    db: AsyncSession = Depends(get_db),
    api_key_info: tuple = Depends(get_api_key_enterprise),
) -> JobResponse:
    """Update an existing job posting."""
    enterprise_id, api_key_id = api_key_info
    # 验证企业所有权
    result = await db.execute(
        select(Job).where(Job.id == job_id)
    )
    job = result.scalar_one_or_none()
    if not job:
        return JobResponse(
            success=False,
            data={},
            message=f"Job not found: {job_id}",
        )
    if job.enterprise_id != enterprise_id:
        return JobResponse(
            success=False,
            data={},
            message="Not authorized to update this job",
        )
    updated_job = await job_service.update_job(
        db=db,
        job_id=job_id,
        job_data=request.job,
    )

    if not job:
        return JobResponse(
            success=False,
            data={},
            message=f"Job not found: {job_id}",
        )

    return JobResponse(
        success=True,
        data={
            "job_id": job.id,
            "updated_at": job.updated_at.isoformat() if job.updated_at else None,
        },
        message="Job updated successfully",
    )


@router.delete(
    "/{job_id}",
    response_model=JobResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete job",
    description="Expire a job posting",
)
async def delete_job(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    api_key_info: tuple = Depends(get_api_key_enterprise),
) -> JobResponse:
    """Expire a job posting (soft delete)."""
    enterprise_id, api_key_id = api_key_info
    # 验证企业所有权
    result = await db.execute(
        select(Job).where(Job.id == job_id)
    )
    job = result.scalar_one_or_none()
    if not job:
        return JobResponse(
            success=False,
            data={},
            message=f"Job not found: {job_id}",
        )
    if job.enterprise_id != enterprise_id:
        return JobResponse(
            success=False,
            data={},
            message="Not authorized to delete this job",
        )
    deleted = await job_service.delete_job(db, job_id)

    if not deleted:
        return JobResponse(
            success=False,
            data={},
            message=f"Job not found: {job_id}",
        )

    return JobResponse(
        success=True,
        data={"job_id": job_id},
        message="Job expired successfully",
    )
