"""
A2A Protocol API
Agent to Agent 通信协议端点

实现 Agent 之间的直接协商：
1. ExpressInterest - 表达意向
2. RespondInterest - 回应意向
3. NegotiateSalary - 薪资谈判
4. Confirm - 双向确认
"""

from typing import Optional

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.a2a_service import a2a_service
from app.services.enterprise_service import enterprise_service

router = APIRouter(prefix="/a2a", tags=["a2a"])


class ExpressInterestRequest(BaseModel):
    """表达意向请求"""
    profile_id: str = Field(..., description="求职者 Profile ID")
    job_id: str = Field(..., description="职位 ID")
    seeker_agent_id: str = Field(..., description="求职 Agent ID")
    employer_agent_id: str = Field(..., description="雇主 Agent ID")
    message: Optional[str] = Field(None, description="附加消息")


class RespondInterestRequest(BaseModel):
    """回应意向请求"""
    profile_id: str = Field(..., description="求职者 Profile ID")
    job_id: str = Field(..., description="职位 ID")
    action: str = Field(..., description="动作: accept 或 reject")
    employer_agent_id: str = Field(..., description="雇主 Agent ID")


class NegotiateSalaryRequest(BaseModel):
    """薪资谈判请求"""
    session_id: str = Field(..., description="协商会话 ID")
    offer: dict = Field(..., description="报价: {salary, start_date, notes}")
    from_agent_id: str = Field(..., description="发送方 Agent ID")


class ConfirmRequest(BaseModel):
    """确认请求"""
    session_id: str = Field(..., description="协商会话 ID")
    agent_id: str = Field(..., description="确认方 Agent ID")


class RejectRequest(BaseModel):
    """拒绝请求"""
    session_id: str = Field(..., description="协商会话 ID")
    agent_id: str = Field(..., description="拒绝方 Agent ID")
    reason: Optional[str] = Field(None, description="拒绝原因")


class A2AResponse(BaseModel):
    """A2A 响应"""
    success: bool = True
    data: dict = Field(default_factory=dict)
    message: str | None = None


# ==================== 意向表达 ====================

@router.post(
    "/interest",
    response_model=A2AResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Express interest",
    description="求职 Agent 表达对某职位的意向",
)
async def express_interest(
    request: ExpressInterestRequest,
    db: AsyncSession = Depends(get_db),
) -> A2AResponse:
    """
    表达意向 (ExpressInterest)

    求职 Agent 调用此接口向企业表达对职位的兴趣。
    企业 Agent 会收到通知。
    """
    result = await a2a_service.express_interest(
        db=db,
        profile_id=request.profile_id,
        job_id=request.job_id,
        seeker_agent_id=request.seeker_agent_id,
        employer_agent_id=request.employer_agent_id,
        message=request.message,
    )

    # Record billing: match_query - enterprise is notified of interest in their job
    from app.models import JobPosting
    job_result = await db.execute(
        select(JobPosting).where(JobPosting.id == request.job_id)
    )
    job = job_result.scalar_one_or_none()
    if job:
        await enterprise_service.record_usage(
            db=db,
            enterprise_id=job.enterprise_id,
            api_key_id=job.api_key_id,
            usage_type="match_query",
            quantity=1,
            reference_id=result.get("id") if isinstance(result, dict) else None,
        )

    return A2AResponse(
        success=True,
        data=result,
        message="Interest expressed successfully",
    )


@router.post(
    "/interest/respond",
    response_model=A2AResponse,
    status_code=status.HTTP_200_OK,
    summary="Respond to interest",
    description="企业 Agent 回应求职者的意向",
)
async def respond_to_interest(
    request: RespondInterestRequest,
    db: AsyncSession = Depends(get_db),
) -> A2AResponse:
    """
    回应意向

    企业 Agent 接受或拒绝求职者的意向。
    接受后会创建协商会话。
    """
    result = await a2a_service.respond_to_interest(
        db=db,
        profile_id=request.profile_id,
        job_id=request.job_id,
        action=request.action,
        employer_agent_id=request.employer_agent_id,
    )

    if not result.get("success"):
        return A2AResponse(success=False, data={}, message=result.get("error"))

    return A2AResponse(
        success=True,
        data=result,
        message=result.get("message"),
    )


@router.get(
    "/interest/{profile_id}/{job_id}",
    response_model=A2AResponse,
    status_code=status.HTTP_200_OK,
    summary="Get interest",
    description="获取特定 Profile 和 Job 之间的意向",
)
async def get_interest(
    profile_id: str,
    job_id: str,
    db: AsyncSession = Depends(get_db),
) -> A2AResponse:
    """获取意向记录"""
    interest = await a2a_service.get_interest(db, profile_id, job_id)

    if not interest:
        return A2AResponse(
            success=False,
            data={},
            message="Interest not found",
        )

    return A2AResponse(success=True, data=interest)


# ==================== 薪资谈判 ====================

@router.post(
    "/negotiate",
    response_model=A2AResponse,
    status_code=status.HTTP_200_OK,
    summary="Negotiate salary",
    description="Agent 之间协商薪资和入职时间",
)
async def negotiate_salary(
    request: NegotiateSalaryRequest,
    db: AsyncSession = Depends(get_db),
) -> A2AResponse:
    """
    薪资谈判 (NegotiateSalary)

    在协商会话中提出或回应薪资报价。
    """
    result = await a2a_service.negotiate_salary(
        db=db,
        session_id=request.session_id,
        from_agent_id=request.from_agent_id,
        offer=request.offer,
    )

    if not result.get("success"):
        return A2AResponse(success=False, data={}, message=result.get("error"))

    return A2AResponse(success=True, data=result)


@router.post(
    "/counter-offer",
    response_model=A2AResponse,
    status_code=status.HTTP_200_OK,
    summary="Counter offer",
    description="对当前报价提出还价",
)
async def counter_offer(
    request: NegotiateSalaryRequest,
    db: AsyncSession = Depends(get_db),
) -> A2AResponse:
    """还价"""
    return await negotiate_salary(request, db)


# ==================== 确认/拒绝 ====================

@router.post(
    "/confirm",
    response_model=A2AResponse,
    status_code=status.HTTP_200_OK,
    summary="Confirm",
    description="Agent 确认协商结果",
)
async def confirm(
    request: ConfirmRequest,
    db: AsyncSession = Depends(get_db),
) -> A2AResponse:
    """
    确认 (Confirm)

    双方都确认后，平台介入交换联系方式。
    """
    result = await a2a_service.confirm(
        db=db,
        session_id=request.session_id,
        agent_id=request.agent_id,
    )

    if not result.get("success"):
        return A2AResponse(success=False, data={}, message=result.get("error"))

    # Record billing: match_success when both parties confirm and contact is exchanged
    if result.get("status") == "confirmed" and result.get("contact_exchange"):
        from app.models import JobPosting, A2ASession
        session_result = await db.execute(
            select(A2ASession).where(A2ASession.id == request.session_id)
        )
        session = session_result.scalar_one_or_none()
        if session:
            job_result = await db.execute(
                select(JobPosting).where(JobPosting.id == session.job_id)
            )
            job = job_result.scalar_one_or_none()
            if job:
                await enterprise_service.record_usage(
                    db=db,
                    enterprise_id=job.enterprise_id,
                    api_key_id=job.api_key_id,
                    usage_type="match_success",
                    quantity=1,
                    reference_id=session.id,
                )

    return A2AResponse(
        success=True,
        data=result,
        message=result.get("message"),
    )


@router.post(
    "/reject",
    response_model=A2AResponse,
    status_code=status.HTTP_200_OK,
    summary="Reject",
    description="拒绝协商",
)
async def reject(
    request: RejectRequest,
    db: AsyncSession = Depends(get_db),
) -> A2AResponse:
    """拒绝协商"""
    result = await a2a_service.reject(
        db=db,
        session_id=request.session_id,
        agent_id=request.agent_id,
        reason=request.reason,
    )

    if not result.get("success"):
        return A2AResponse(success=False, data={}, message=result.get("error"))

    return A2AResponse(success=True, data=result, message="Rejected")


@router.get(
    "/session/{session_id}",
    response_model=A2AResponse,
    status_code=status.HTTP_200_OK,
    summary="Get session",
    description="获取协商会话详情",
)
async def get_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
) -> A2AResponse:
    """获取会话详情"""
    session = await a2a_service.get_session(db, session_id)

    if not session:
        return A2AResponse(
            success=False,
            data={},
            message="Session not found",
        )

    return A2AResponse(success=True, data=session)