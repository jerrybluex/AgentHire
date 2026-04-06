"""
Application API endpoints.
管理申请状态机和事件流。
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models import Application, Job
from app.services.application_service import (
    application_service,
    ApplicationServiceError,
    ApplicationNotFoundError,
    InvalidTransitionError,
)
from app.services.contact_unlock_service import contact_unlock_service
from app.api.deps import verify_agent, get_current_employer, get_current_user

router = APIRouter()


# =============================================================================
# Request/Response Models
# =============================================================================


class ApplicationCreateResponse(BaseModel):
    """Application creation response."""

    success: bool = True
    data: dict = Field(default_factory=dict)
    message: str | None = None


class ApplicationSubmitResponse(BaseModel):
    """Application submit response."""

    success: bool = True
    data: dict = Field(default_factory=dict)
    message: str | None = None


class ApplicationTransitionResponse(BaseModel):
    """Application status transition response."""

    success: bool = True
    data: dict = Field(default_factory=dict)
    message: str | None = None


class ApplicationEventsResponse(BaseModel):
    """Application events response."""

    success: bool = True
    data: dict = Field(default_factory=dict)
    message: str | None = None


class ErrorResponse(BaseModel):
    """Error response."""

    success: bool = False
    data: dict = Field(default_factory=dict)
    message: str | None = None


class ContactUnlockResponse(BaseModel):
    """Contact unlock endpoint response."""

    success: bool = True
    data: dict = Field(default_factory=dict)
    message: str | None = None


# =============================================================================
# Endpoints
# =============================================================================


@router.post(
    "",
    response_model=ApplicationCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建申请",
    description="创建新申请（初始状态为 draft）",
)
async def create_application(
    profile_id: str,
    job_id: str,
    cover_letter: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_agent: dict = Depends(verify_agent),
) -> ApplicationCreateResponse:
    """
    创建申请（初始状态为 draft）。

    - **profile_id**: 求职者 Profile ID
    - **job_id**: 职位 ID
    - **cover_letter**: 求职信（可选）
    """
    try:
        application = await application_service.create_application(
            db=db,
            profile_id=profile_id,
            job_id=job_id,
            applicant_principal_id=current_agent["principal_id"],
            cover_letter=cover_letter,
        )
        await db.commit()

        return ApplicationCreateResponse(
            success=True,
            data={
                "application_id": application.id,
                "status": application.status,
                "created_at": application.created_at.isoformat(),
            },
            message="Application created successfully",
        )
    except ApplicationServiceError as e:
        await db.rollback()
        return ApplicationCreateResponse(
            success=False,
            data={},
            message=str(e),
        )
    except Exception as e:
        await db.rollback()
        return ApplicationCreateResponse(
            success=False,
            data={},
            message=f"Failed to create application: {str(e)}",
        )


@router.post(
    "/{application_id}/submit",
    response_model=ApplicationSubmitResponse,
    status_code=status.HTTP_200_OK,
    summary="提交申请",
    description="提交申请（draft → submitted）",
)
async def submit_application(
    application_id: str,
    db: AsyncSession = Depends(get_db),
    current_agent: dict = Depends(verify_agent),
) -> ApplicationSubmitResponse:
    """
    提交申请（draft → submitted）。

    - **application_id**: 申请 ID
    """
    try:
        application = await application_service.submit_application(
            db=db,
            application_id=application_id,
            actor_type="agent",
            actor_id=current_agent["principal_id"],
        )
        await db.commit()

        return ApplicationSubmitResponse(
            success=True,
            data={
                "application_id": application.id,
                "status": application.status,
                "updated_at": application.updated_at.isoformat(),
            },
            message="Application submitted successfully",
        )
    except ApplicationNotFoundError as e:
        await db.rollback()
        return ApplicationSubmitResponse(
            success=False,
            data={},
            message=str(e),
        )
    except InvalidTransitionError as e:
        await db.rollback()
        return ApplicationSubmitResponse(
            success=False,
            data={},
            message=str(e),
        )
    except Exception as e:
        await db.rollback()
        return ApplicationSubmitResponse(
            success=False,
            data={},
            message=f"Failed to submit application: {str(e)}",
        )


@router.post(
    "/{application_id}/view",
    response_model=ApplicationTransitionResponse,
    status_code=status.HTTP_200_OK,
    summary="标记为已查看",
    description="标记申请为已查看（submitted → viewed）",
)
async def mark_as_viewed(
    application_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_employer),
) -> ApplicationTransitionResponse:
    """
    标记为已查看（submitted → viewed）。

    - **application_id**: 申请 ID
    """
    # 验证企业所有权
    result = await db.execute(
        select(Application).where(Application.id == application_id)
    )
    application = result.scalar_one_or_none()
    if not application:
        return ApplicationTransitionResponse(
            success=False,
            data={},
            message=f"Application not found: {application_id}",
        )
    job_result = await db.execute(
        select(Job).where(Job.id == application.job_id)
    )
    job = job_result.scalar_one_or_none()
    if not job or job.enterprise_id != current_user["enterprise_id"]:
        return ApplicationTransitionResponse(
            success=False,
            data={},
            message="Not authorized to access this application",
        )
    try:
        application = await application_service.transition_status(
            db=db,
            application_id=application_id,
            new_status="viewed",
            actor_type="employer",
            actor_id=current_user["principal_id"],
        )
        await db.commit()

        return ApplicationTransitionResponse(
            success=True,
            data={
                "application_id": application.id,
                "status": application.status,
            },
            message="Application marked as viewed",
        )
    except ApplicationNotFoundError as e:
        await db.rollback()
        return ApplicationTransitionResponse(
            success=False,
            data={},
            message=str(e),
        )
    except InvalidTransitionError as e:
        await db.rollback()
        return ApplicationTransitionResponse(
            success=False,
            data={},
            message=str(e),
        )
    except Exception as e:
        await db.rollback()
        return ApplicationTransitionResponse(
            success=False,
            data={},
            message=f"Failed to mark application as viewed: {str(e)}",
        )


@router.post(
    "/{application_id}/shortlist",
    response_model=ApplicationTransitionResponse,
    status_code=status.HTTP_200_OK,
    summary="列入候选",
    description="将候选人列入候选名单（viewed → shortlisted）",
)
async def shortlist_candidate(
    application_id: str,
    comment: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_employer),
) -> ApplicationTransitionResponse:
    """
    列入候选（viewed → shortlisted）。

    - **application_id**: 申请 ID
    - **comment**: 备注（可选）
    """
    # 验证企业所有权
    result = await db.execute(
        select(Application).where(Application.id == application_id)
    )
    application = result.scalar_one_or_none()
    if not application:
        return ApplicationTransitionResponse(
            success=False,
            data={},
            message=f"Application not found: {application_id}",
        )
    job_result = await db.execute(
        select(Job).where(Job.id == application.job_id)
    )
    job = job_result.scalar_one_or_none()
    if not job or job.enterprise_id != current_user["enterprise_id"]:
        return ApplicationTransitionResponse(
            success=False,
            data={},
            message="Not authorized to access this application",
        )
    try:
        application = await application_service.transition_status(
            db=db,
            application_id=application_id,
            new_status="shortlisted",
            actor_type="employer",
            actor_id=current_user["principal_id"],
            comment=comment,
        )
        await db.commit()

        return ApplicationTransitionResponse(
            success=True,
            data={
                "application_id": application.id,
                "status": application.status,
            },
            message="Candidate shortlisted",
        )
    except ApplicationNotFoundError as e:
        await db.rollback()
        return ApplicationTransitionResponse(
            success=False,
            data={},
            message=str(e),
        )
    except InvalidTransitionError as e:
        await db.rollback()
        return ApplicationTransitionResponse(
            success=False,
            data={},
            message=str(e),
        )
    except Exception as e:
        await db.rollback()
        return ApplicationTransitionResponse(
            success=False,
            data={},
            message=f"Failed to shortlist candidate: {str(e)}",
        )


@router.post(
    "/{application_id}/reject",
    response_model=ApplicationTransitionResponse,
    status_code=status.HTTP_200_OK,
    summary="拒绝申请",
    description="拒绝申请",
)
async def reject_application(
    application_id: str,
    comment: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_employer),
) -> ApplicationTransitionResponse:
    """
    拒绝申请。

    - **application_id**: 申请 ID
    - **comment**: 拒绝原因（可选）
    """
    # 验证企业所有权
    result = await db.execute(
        select(Application).where(Application.id == application_id)
    )
    application = result.scalar_one_or_none()
    if not application:
        return ApplicationTransitionResponse(
            success=False,
            data={},
            message=f"Application not found: {application_id}",
        )
    job_result = await db.execute(
        select(Job).where(Job.id == application.job_id)
    )
    job = job_result.scalar_one_or_none()
    if not job or job.enterprise_id != current_user["enterprise_id"]:
        return ApplicationTransitionResponse(
            success=False,
            data={},
            message="Not authorized to access this application",
        )
    try:
        application = await application_service.transition_status(
            db=db,
            application_id=application_id,
            new_status="rejected",
            actor_type="employer",
            actor_id=current_user["principal_id"],
            comment=comment,
        )
        await db.commit()

        return ApplicationTransitionResponse(
            success=True,
            data={
                "application_id": application.id,
                "status": application.status,
            },
            message="Application rejected",
        )
    except ApplicationNotFoundError as e:
        await db.rollback()
        return ApplicationTransitionResponse(
            success=False,
            data={},
            message=str(e),
        )
    except InvalidTransitionError as e:
        await db.rollback()
        return ApplicationTransitionResponse(
            success=False,
            data={},
            message=str(e),
        )
    except Exception as e:
        await db.rollback()
        return ApplicationTransitionResponse(
            success=False,
            data={},
            message=f"Failed to reject application: {str(e)}",
        )


@router.get(
    "/{application_id}/events",
    response_model=ApplicationEventsResponse,
    status_code=status.HTTP_200_OK,
    summary="获取申请事件历史",
    description="获取申请的所有事件（状态变更历史）",
)
async def get_application_events(
    application_id: str,
    db: AsyncSession = Depends(get_db),
) -> ApplicationEventsResponse:
    """
    获取申请的所有事件（状态变更历史）。

    - **application_id**: 申请 ID
    """
    try:
        events = await application_service.get_application_events(db, application_id)

        return ApplicationEventsResponse(
            success=True,
            data={
                "application_id": application_id,
                "events": [
                    {
                        "id": e.id,
                        "event_type": e.event_type,
                        "from_status": e.from_status,
                        "to_status": e.to_status,
                        "actor_type": e.actor_type,
                        "actor_id": e.actor_id,
                        "comment": e.comment,
                        "created_at": e.created_at.isoformat(),
                    }
                    for e in events
                ],
            },
            message="Application events retrieved",
        )
    except Exception as e:
        return ApplicationEventsResponse(
            success=False,
            data={},
            message=f"Failed to get application events: {str(e)}",
        )


# =============================================================================
# Contact Unlock Endpoints
# =============================================================================


@router.post("/applications/{application_id}/contact-unlock", response_model=ContactUnlockResponse)
async def request_contact_unlock(
    application_id: str,
    db: AsyncSession = Depends(get_db),
    current_agent: dict = Depends(verify_agent),
) -> ContactUnlockResponse:
    """候选人请求解锁联系方式"""
    # Idempotency: return existing unlock if already created
    existing = await contact_unlock_service.get_by_application(db, application_id)
    if existing:
        return ContactUnlockResponse(
            success=True,
            data={"unlock_id": existing.id, "status": existing.status},
            message="Unlock request already exists",
        )

    unlock = await contact_unlock_service.create_unlock_request(
        db=db,
        application_id=application_id,
        requester_type="candidate",
        requester_id=current_agent["principal_id"],
    )
    await db.commit()
    return ContactUnlockResponse(
        success=True,
        data={"unlock_id": unlock.id, "status": unlock.status},
        message="Unlock request created",
    )


@router.post("/applications/{application_id}/contact-unlock/authorize", response_model=ContactUnlockResponse)
async def authorize_contact_unlock(
    application_id: str,
    reason: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_agent: dict = Depends(verify_agent),
) -> ContactUnlockResponse:
    """候选人授权查看联系方式"""
    unlock = await contact_unlock_service.get_by_application(db, application_id)
    if not unlock:
        raise HTTPException(status_code=404, detail="Unlock request not found")
    unlock = await contact_unlock_service.candidate_authorize(
        db=db,
        unlock_id=unlock.id,
        candidate_id=current_agent["principal_id"],
        reason=reason,
    )
    await db.commit()
    return ContactUnlockResponse(
        success=True,
        data={"unlock_id": unlock.id, "status": unlock.status},
        message="Candidate authorized",
    )


@router.post("/applications/{application_id}/contact-unlock/unlock", response_model=ContactUnlockResponse)
async def do_unlock_contact(
    application_id: str,
    reason: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_employer: dict = Depends(get_current_employer),
) -> ContactUnlockResponse:
    """企业解锁联系方式"""
    unlock = await contact_unlock_service.get_by_application(db, application_id)
    if not unlock:
        raise HTTPException(status_code=404, detail="Unlock request not found")
    unlock = await contact_unlock_service.employer_unlock(
        db=db,
        unlock_id=unlock.id,
        employer_id=current_employer["principal_id"],
        reason=reason,
    )
    await db.commit()
    return ContactUnlockResponse(
        success=True,
        data={"unlock_id": unlock.id, "status": unlock.status},
        message="Contact unlocked",
    )


@router.get("/applications/{application_id}/contact-unlock", response_model=ContactUnlockResponse)
async def get_contact_unlock_status(
    application_id: str,
    db: AsyncSession = Depends(get_db),
) -> ContactUnlockResponse:
    """获取联系方式解锁状态"""
    unlock = await contact_unlock_service.get_by_application(db, application_id)
    if not unlock:
        return ContactUnlockResponse(
            success=False,
            data={},
            message="No unlock request",
        )
    return ContactUnlockResponse(
        success=True,
        data={
            "unlock_id": unlock.id,
            "status": unlock.status,
            "authorized_at": unlock.authorized_at.isoformat() if unlock.authorized_at else None,
            "unlocked_at": unlock.unlocked_at.isoformat() if unlock.unlocked_at else None,
        },
        message="Unlock status retrieved",
    )
