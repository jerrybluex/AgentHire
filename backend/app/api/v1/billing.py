"""
Billing API endpoints.
Provides billing records and usage statistics for enterprises.
"""

from typing import Optional

from fastapi import APIRouter, Depends, Header, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.enterprise_service import enterprise_service
from app.api.deps import require_enterprise_api_key

router = APIRouter()


class BillingRecordResponse(BaseModel):
    """单条计费记录响应"""
    id: str
    usage_type: str
    quantity: int
    unit_price: Optional[float]
    amount: Optional[float]
    reference_id: Optional[str]
    billing_period: Optional[str]
    created_at: str


class BillingResponse(BaseModel):
    """账单响应"""
    success: bool = True
    data: list = Field(default_factory=list)
    total: float = 0.0
    current_period_usage: dict = Field(default_factory=dict)


class UsageStatsResponse(BaseModel):
    """使用统计响应"""
    success: bool = True
    data: dict = Field(default_factory=dict)


async def get_enterprise_from_header(
    auth_context: dict = Depends(require_enterprise_api_key),
    db: AsyncSession = Depends(get_db),
) -> str:
    """Get enterprise ID from validated API key context."""
    enterprise_id = auth_context["enterprise_id"]
    enterprise = await enterprise_service.get_enterprise(db, enterprise_id)
    if not enterprise:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Enterprise not found",
        )
    return enterprise_id


@router.get(
    "",
    response_model=BillingResponse,
    status_code=200,
    summary="Get billing records",
    description="Get billing records for the authenticated enterprise",
)
async def get_billing_records(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    usage_type: Optional[str] = Query(None, description="Filter by usage type"),
    limit: int = Query(100, ge=1, le=500, description="Number of records"),
    db: AsyncSession = Depends(get_db),
    enterprise_id: str = Depends(get_enterprise_from_header),
) -> BillingResponse:
    """
    获取企业的所有计费记录
    """
    records, total = await enterprise_service.get_billing_records(
        db=db,
        enterprise_id=enterprise_id,
        start_date=start_date,
        end_date=end_date,
        usage_type=usage_type,
        limit=limit,
    )

    # Calculate current period usage by type
    current_period_usage = {}
    for r in records:
        period = r.billing_period or "unknown"
        if period not in current_period_usage:
            current_period_usage[period] = {
                "job_post": {"count": 0, "amount": 0.0},
                "profile_view": {"count": 0, "amount": 0.0},
                "match_query": {"count": 0, "amount": 0.0},
                "match_success": {"count": 0, "amount": 0.0},
            }
        if r.usage_type in current_period_usage[period]:
            current_period_usage[period][r.usage_type]["count"] += r.quantity
            current_period_usage[period][r.usage_type]["amount"] += r.amount or 0.0

    return BillingResponse(
        success=True,
        data=[
            {
                "id": r.id,
                "usage_type": r.usage_type,
                "quantity": r.quantity,
                "unit_price": r.unit_price,
                "amount": r.amount,
                "reference_id": r.reference_id,
                "billing_period": r.billing_period,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in records
        ],
        total=total,
        current_period_usage=current_period_usage,
    )


@router.get(
    "/stats",
    response_model=UsageStatsResponse,
    status_code=200,
    summary="Get usage statistics",
    description="Get usage statistics for the authenticated enterprise",
)
async def get_usage_stats(
    db: AsyncSession = Depends(get_db),
    enterprise_id: str = Depends(get_enterprise_from_header),
) -> UsageStatsResponse:
    """
    获取企业的使用统计
    """
    from datetime import datetime
    from app.models import BillingRecord
    from sqlalchemy import select, func

    # Get all records for this enterprise
    result = await db.execute(
        select(BillingRecord).where(BillingRecord.enterprise_id == enterprise_id)
    )
    records = result.scalars().all()

    # Calculate statistics
    stats = {
        "total_jobs_posted": 0,
        "total_profile_views": 0,
        "total_match_queries": 0,
        "total_match_successes": 0,
        "total_spend": 0.0,
        "by_period": {},
    }

    for r in records:
        if r.usage_type == "job_post":
            stats["total_jobs_posted"] += r.quantity
        elif r.usage_type == "profile_view":
            stats["total_profile_views"] += r.quantity
        elif r.usage_type == "match_query":
            stats["total_match_queries"] += r.quantity
        elif r.usage_type == "match_success":
            stats["total_match_successes"] += r.quantity

        stats["total_spend"] += r.amount or 0.0

        period = r.billing_period or "unknown"
        if period not in stats["by_period"]:
            stats["by_period"][period] = {"count": 0, "amount": 0.0}
        stats["by_period"][period]["count"] += r.quantity
        stats["by_period"][period]["amount"] += r.amount or 0.0

    return UsageStatsResponse(
        success=True,
        data=stats,
    )


@router.get(
    "/pricing",
    response_model=UsageStatsResponse,
    status_code=200,
    summary="Get pricing information",
    description="Get current pricing rates",
)
async def get_pricing() -> UsageStatsResponse:
    """
    获取计费价格信息
    """
    return UsageStatsResponse(
        success=True,
        data={
            "pricing": {
                "job_post": {"unit_price": 0.5, "description": "发布职位"},
                "profile_view": {"unit_price": 0.1, "description": "查看人才列表"},
                "match_query": {"unit_price": 0.1, "description": "查询匹配"},
                "match_success": {"unit_price": 1.0, "description": "成功匹配"},
            },
            "currency": "CNY",
        },
    )
