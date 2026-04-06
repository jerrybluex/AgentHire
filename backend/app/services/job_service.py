"""
Job Service
职位发布的CRUD操作和业务逻辑
"""

from typing import Optional
from datetime import datetime, timedelta

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import JobPosting, Enterprise, EnterpriseAPIKey, generate_id


class JobService:
    """Service for managing job postings."""

    async def create_job(
        self,
        db: AsyncSession,
        enterprise_id: str,
        api_key_id: str,
        job_data: dict,
        publish_options: dict,
    ) -> Optional[JobPosting]:
        """
        Create a new job posting.

        Args:
            db: Database session
            enterprise_id: Enterprise ID
            api_key_id: API key ID used for this operation
            job_data: Job posting data
            publish_options: Publishing options

        Returns:
            Created JobPosting or None if enterprise not found
        """
        # Verify enterprise exists and is approved
        result = await db.execute(
            select(Enterprise).where(Enterprise.id == enterprise_id)
        )
        enterprise = result.scalar_one_or_none()

        if not enterprise or enterprise.status != "approved":
            return None

        # Extract job data
        title = job_data.get("title", "")
        requirements = job_data.get("requirements", {})
        compensation = job_data.get("compensation", {})
        location = job_data.get("location", {})
        description = job_data.get("description")
        responsibilities = job_data.get("responsibilities", [])
        department = job_data.get("department")

        # Calculate expiration
        active_days = publish_options.get("active_days", 30)
        expires_at = datetime.utcnow() + timedelta(days=active_days)

        # Create job posting
        job = JobPosting(
            id=generate_id("job_"),
            enterprise_id=enterprise_id,
            api_key_id=api_key_id,
            title=title,
            department=department,
            description=description,
            responsibilities=responsibilities if isinstance(responsibilities, list) else [],
            requirements=requirements,
            compensation=compensation,
            location=location,
            status="active",
            published_at=datetime.utcnow(),
            expires_at=expires_at,
        )

        db.add(job)
        await db.flush()

        return job

    async def get_job(
        self,
        db: AsyncSession,
        job_id: str,
    ) -> Optional[JobPosting]:
        """Get a job posting by ID."""
        result = await db.execute(
            select(JobPosting).where(JobPosting.id == job_id)
        )
        return result.scalar_one_or_none()

    async def update_job(
        self,
        db: AsyncSession,
        job_id: str,
        job_data: dict,
    ) -> Optional[JobPosting]:
        """Update an existing job posting."""
        job = await self.get_job(db, job_id)
        if not job:
            return None

        # Update fields
        if "title" in job_data:
            job.title = job_data["title"]
        if "description" in job_data:
            job.description = job_data["description"]
        if "requirements" in job_data:
            job.requirements = job_data["requirements"]
        if "compensation" in job_data:
            job.compensation = job_data["compensation"]
        if "location" in job_data:
            job.location = job_data["location"]
        if "status" in job_data:
            job.status = job_data["status"]

        job.updated_at = datetime.utcnow()
        await db.flush()

        return job

    async def delete_job(
        self,
        db: AsyncSession,
        job_id: str,
    ) -> bool:
        """Mark a job as expired/deleted."""
        job = await self.get_job(db, job_id)
        if not job:
            return False

        job.status = "expired"
        job.updated_at = datetime.utcnow()
        await db.flush()
        return True

    async def list_jobs(
        self,
        db: AsyncSession,
        enterprise_id: Optional[str] = None,
        status: Optional[str] = None,
        city: Optional[str] = None,
        skills: Optional[list[str]] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[JobPosting], int]:
        """List job postings with filters."""
        query = select(JobPosting)

        if enterprise_id:
            query = query.where(JobPosting.enterprise_id == enterprise_id)

        if status:
            query = query.where(JobPosting.status == status)
        else:
            # Default to active jobs
            query = query.where(JobPosting.status == "active")

        if city:
            # Filter by city in location JSON
            query = query.where(
                JobPosting.location.op("->>")("city").ilike(f"%{city}%")
            )

        # Get total count
        from sqlalchemy import func

        count_result = await db.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar() or 0

        # Apply pagination
        query = query.offset(offset).limit(limit)
        result = await db.execute(query)
        jobs = result.scalars().all()

        return list(jobs), total


# Singleton instance
job_service = JobService()
