"""
Usage Statistics API endpoints.
Provides detailed usage statistics and analytics for enterprises.
"""

from typing import Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models import BillingRecord, Enterprise, EnterpriseAPIKey
from app.services.enterprise_service import enterprise_service

router = APIRouter()


class TimeSeriesDataPoint(BaseModel):
    """Single data point in time series."""
    period: str
    count: int
    amount: float


class UsageTypeStats(BaseModel):
    """Statistics for a specific usage type."""
    type: str
    count: int
    amount: float
    percentage: float


class DailyStats(BaseModel):
    """Daily usage statistics."""
    date: str
    total_count: int
    total_amount: float


class MonthlyStats(BaseModel):
    """Monthly usage statistics."""
    month: str
    total_count: int
    total_amount: float
    by_type: dict


class StatsSummary(BaseModel):
    """Summary statistics."""
    total_api_calls: int
    total_spend: float
    current_month_calls: int
    current_month_spend: float
    average_daily_calls: float
    peak_day: Optional[str]
    peak_day_calls: int


class UsageTrendResponse(BaseModel):
    """Usage trend response."""
    success: bool = True
    data: dict = Field(default_factory=dict)


class UsageDetailResponse(BaseModel):
    """Detailed usage statistics response."""
    success: bool = True
    data: dict = Field(default_factory=dict)


async def get_enterprise_from_header(
    x_enterprise_id: str = Query(..., alias="X-Enterprise-ID"),
    db: AsyncSession = Depends(get_db),
) -> str:
    """Get enterprise ID from header and validate."""
    enterprise = await enterprise_service.get_enterprise(db, x_enterprise_id)
    if not enterprise:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Enterprise not found",
        )
    return x_enterprise_id


@router.get(
    "/summary",
    response_model=UsageTrendResponse,
    status_code=200,
    summary="Get usage summary",
    description="Get overall usage summary for the authenticated enterprise",
)
async def get_usage_summary(
    db: AsyncSession = Depends(get_db),
    enterprise_id: str = Depends(get_enterprise_from_header),
) -> UsageTrendResponse:
    """
    Get usage summary statistics.

    Returns overall totals and current month stats.
    """
    now = datetime.utcnow()
    current_month = now.strftime("%Y-%m")

    # Get all billing records for enterprise
    result = await db.execute(
        select(BillingRecord).where(BillingRecord.enterprise_id == enterprise_id)
    )
    records = result.scalars().all()

    # Calculate totals
    total_calls = sum(r.quantity for r in records)
    total_spend = sum(r.amount or 0 for r in records)

    # Current month stats
    current_month_records = [r for r in records if r.billing_period == current_month]
    current_month_calls = sum(r.quantity for r in current_month_records)
    current_month_spend = sum(r.amount or 0 for r in current_month_records)

    # Calculate average daily calls (current month)
    days_in_month = now.day
    average_daily = current_month_calls / days_in_month if days_in_month > 0 else 0

    # Find peak day
    daily_stats = {}
    for r in records:
        date_key = r.created_at.strftime("%Y-%m-%d") if r.created_at else "unknown"
        if date_key not in daily_stats:
            daily_stats[date_key] = 0
        daily_stats[date_key] += r.quantity

    peak_day = max(daily_stats.keys(), key=lambda k: daily_stats[k]) if daily_stats else None
    peak_day_calls = daily_stats.get(peak_day, 0) if peak_day else 0

    return UsageTrendResponse(
        success=True,
        data={
            "total_api_calls": total_calls,
            "total_spend": round(total_spend, 2),
            "current_month_calls": current_month_calls,
            "current_month_spend": round(current_month_spend, 2),
            "average_daily_calls": round(average_daily, 2),
            "peak_day": peak_day,
            "peak_day_calls": peak_day_calls,
        },
    )


@router.get(
    "/trend",
    response_model=UsageTrendResponse,
    status_code=200,
    summary="Get usage trend",
    description="Get usage trend over time for the authenticated enterprise",
)
async def get_usage_trend(
    period: str = Query("daily", description="Aggregation period: daily, weekly, monthly"),
    days: int = Query(30, ge=1, le=365, description="Number of days to include"),
    db: AsyncSession = Depends(get_db),
    enterprise_id: str = Depends(get_enterprise_from_header),
) -> UsageTrendResponse:
    """
    Get usage trend over time.

    Supports daily, weekly, and monthly aggregation.
    """
    now = datetime.utcnow()
    start_date = now - timedelta(days=days)

    # Get billing records in date range
    result = await db.execute(
        select(BillingRecord)
        .where(BillingRecord.enterprise_id == enterprise_id)
        .where(BillingRecord.created_at >= start_date)
        .order_by(BillingRecord.created_at)
    )
    records = result.scalars().all()

    # Aggregate by period
    trend_data = {}

    for r in records:
        if r.created_at is None:
            continue

        if period == "daily":
            period_key = r.created_at.strftime("%Y-%m-%d")
        elif period == "weekly":
            # Get start of week (Monday)
            week_start = r.created_at - timedelta(days=r.created_at.weekday())
            period_key = week_start.strftime("%Y-%m-%d")
        else:  # monthly
            period_key = r.created_at.strftime("%Y-%m")

        if period_key not in trend_data:
            trend_data[period_key] = {"count": 0, "amount": 0.0}

        trend_data[period_key]["count"] += r.quantity
        trend_data[period_key]["amount"] += r.amount or 0.0

    # Convert to list sorted by period
    sorted_periods = sorted(trend_data.keys())
    trend_list = [
        {
            "period": p,
            "count": trend_data[p]["count"],
            "amount": round(trend_data[p]["amount"], 2),
        }
        for p in sorted_periods
    ]

    return UsageTrendResponse(
        success=True,
        data={
            "period": period,
            "days": days,
            "trend": trend_list,
        },
    )


@router.get(
    "/by-type",
    response_model=UsageDetailResponse,
    status_code=200,
    summary="Get usage by type",
    description="Get usage breakdown by type for the authenticated enterprise",
)
async def get_usage_by_type(
    billing_period: Optional[str] = Query(None, description="Billing period (YYYY-MM)"),
    db: AsyncSession = Depends(get_db),
    enterprise_id: str = Depends(get_enterprise_from_header),
) -> UsageDetailResponse:
    """
    Get usage breakdown by type.

    Optionally filter by billing period.
    """
    query = select(BillingRecord).where(BillingRecord.enterprise_id == enterprise_id)

    if billing_period:
        query = query.where(BillingRecord.billing_period == billing_period)

    result = await db.execute(query)
    records = result.scalars().all()

    # Aggregate by type
    type_stats = {}
    total_count = 0
    total_amount = 0.0

    for r in records:
        usage_type = r.usage_type or "unknown"
        if usage_type not in type_stats:
            type_stats[usage_type] = {"count": 0, "amount": 0.0}

        type_stats[usage_type]["count"] += r.quantity
        type_stats[usage_type]["amount"] += r.amount or 0.0
        total_count += r.quantity
        total_amount += r.amount or 0.0

    # Calculate percentages and format response
    by_type = []
    for usage_type, stats in sorted(type_stats.items()):
        percentage = (stats["count"] / total_count * 100) if total_count > 0 else 0
        by_type.append({
            "type": usage_type,
            "count": stats["count"],
            "amount": round(stats["amount"], 2),
            "percentage": round(percentage, 1),
        })

    return UsageDetailResponse(
        success=True,
        data={
            "billing_period": billing_period or "all",
            "total_count": total_count,
            "total_amount": round(total_amount, 2),
            "by_type": by_type,
        },
    )


@router.get(
    "/api-keys",
    response_model=UsageDetailResponse,
    status_code=200,
    summary="Get usage by API key",
    description="Get usage breakdown by API key for the authenticated enterprise",
)
async def get_usage_by_api_key(
    billing_period: Optional[str] = Query(None, description="Billing period (YYYY-MM)"),
    db: AsyncSession = Depends(get_db),
    enterprise_id: str = Depends(get_enterprise_from_header),
) -> UsageDetailResponse:
    """
    Get usage breakdown by API key.

    Shows usage statistics for each API key.
    """
    # Get all API keys for enterprise
    result = await db.execute(
        select(EnterpriseAPIKey).where(EnterpriseAPIKey.enterprise_id == enterprise_id)
    )
    api_keys = result.scalars().all()

    key_stats = []

    for key in api_keys:
        query = select(BillingRecord).where(BillingRecord.api_key_id == key.id)

        if billing_period:
            query = query.where(BillingRecord.billing_period == billing_period)

        result = await db.execute(query)
        records = result.scalars().all()

        total_count = sum(r.quantity for r in records)
        total_amount = sum(r.amount or 0 for r in records)

        key_stats.append({
            "api_key_id": key.id,
            "api_key_name": key.name,
            "api_key_prefix": key.api_key_prefix,
            "status": key.status,
            "total_count": total_count,
            "total_amount": round(total_amount, 2),
        })

    # Sort by total amount descending
    key_stats.sort(key=lambda x: x["total_amount"], reverse=True)

    return UsageDetailResponse(
        success=True,
        data={
            "billing_period": billing_period or "all",
            "api_keys": key_stats,
        },
    )


@router.get(
    "/monthly",
    response_model=UsageDetailResponse,
    status_code=200,
    summary="Get monthly statistics",
    description="Get monthly usage statistics for the authenticated enterprise",
)
async def get_monthly_stats(
    months: int = Query(12, ge=1, le=24, description="Number of months to include"),
    db: AsyncSession = Depends(get_db),
    enterprise_id: str = Depends(get_enterprise_from_header),
) -> UsageDetailResponse:
    """
    Get monthly usage statistics.

    Returns aggregated monthly data.
    """
    # Get all billing records
    result = await db.execute(
        select(BillingRecord).where(BillingRecord.enterprise_id == enterprise_id)
    )
    records = result.scalars().all()

    # Aggregate by month
    monthly_data = {}

    for r in records:
        period = r.billing_period or "unknown"
        if period not in monthly_data:
            monthly_data[period] = {
                "total_count": 0,
                "total_amount": 0.0,
                "by_type": {},
            }

        monthly_data[period]["total_count"] += r.quantity
        monthly_data[period]["total_amount"] += r.amount or 0.0

        usage_type = r.usage_type or "unknown"
        if usage_type not in monthly_data[period]["by_type"]:
            monthly_data[period]["by_type"][usage_type] = {"count": 0, "amount": 0.0}
        monthly_data[period]["by_type"][usage_type]["count"] += r.quantity
        monthly_data[period]["by_type"][usage_type]["amount"] += r.amount or 0.0

    # Format response
    sorted_months = sorted(monthly_data.keys(), reverse=True)[:months]
    monthly_stats = []

    for month in sorted_months:
        stats = monthly_data[month]
        monthly_stats.append({
            "month": month,
            "total_count": stats["total_count"],
            "total_amount": round(stats["total_amount"], 2),
            "by_type": {
                t: {
                    "count": v["count"],
                    "amount": round(v["amount"], 2),
                }
                for t, v in stats["by_type"].items()
            },
        })

    return UsageDetailResponse(
        success=True,
        data={
            "months": months,
            "monthly_stats": monthly_stats,
        },
    )
