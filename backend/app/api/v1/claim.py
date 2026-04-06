"""
Claim API
Agent 认领 API - C端用户认领 Agent
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Header
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.claim_service import claim_service


router = APIRouter()


# Request/Response Schemas
class ClaimInitiateRequest(BaseModel):
    agent_id: str


class ClaimVerifyRequest(BaseModel):
    agent_id: str
    verification_code: str


class ClaimStatusResponse(BaseModel):
    claim_id: Optional[str] = None
    agent_id: str
    status: str
    message: Optional[str] = None
    expires_at: Optional[str] = None
    claimed_at: Optional[str] = None
    verified_at: Optional[str] = None


@router.post(
    "/agent",
    summary="发起 Agent 认领",
    description="用户发起对某个 Agent 的认领请求",
    response_model=dict,
)
async def initiate_claim(
    request: ClaimInitiateRequest,
    x_user_id: str = Header(..., description="User ID"),
    db: AsyncSession = Depends(get_db),
):
    """
    Initiate an Agent claim.

    - **agent_id**: The Agent ID to claim
    """
    result = await claim_service.initiate_claim(
        db=db,
        user_id=x_user_id,
        agent_id=request.agent_id,
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent {request.agent_id} not found",
        )

    return {
        "success": True,
        "data": result,
    }


@router.post(
    "/verify",
    summary="验证 Agent 认领",
    description="用户验证认领请求（输入验证码）",
    response_model=dict,
)
async def verify_claim(
    request: ClaimVerifyRequest,
    x_user_id: str = Header(..., description="User ID"),
    db: AsyncSession = Depends(get_db),
):
    """
    Verify and complete an Agent claim.

    - **agent_id**: The Agent ID being claimed
    - **verification_code**: 6-digit verification code
    """
    result = await claim_service.verify_claim(
        db=db,
        user_id=x_user_id,
        agent_id=request.agent_id,
        verification_code=request.verification_code,
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Claim not found or already processed",
        )

    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error"),
        )

    return {
        "success": True,
        "data": result,
    }


@router.get(
    "/status/{agent_id}",
    summary="获取认领状态",
    description="查询用户对某个 Agent 的认领状态",
    response_model=dict,
)
async def get_claim_status(
    agent_id: str,
    x_user_id: str = Header(..., description="User ID"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get claim status for an Agent.

    - **agent_id**: The Agent ID to check
    """
    result = await claim_service.get_claim_status(
        db=db,
        user_id=x_user_id,
        agent_id=agent_id,
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active claim found for this Agent",
        )

    return {
        "success": True,
        "data": result,
    }


@router.get(
    "/list",
    summary="列出所有认领记录",
    description="列出用户所有的 Agent 认领记录",
    response_model=dict,
)
async def list_claims(
    x_user_id: str = Header(..., description="User ID"),
    db: AsyncSession = Depends(get_db),
):
    """
    List all claims for the current user.
    """
    claims = await claim_service.list_user_claims(
        db=db,
        user_id=x_user_id,
    )

    return {
        "success": True,
        "data": claims,
    }
