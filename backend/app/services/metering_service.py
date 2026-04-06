"""
Billing & Metering Service
用量记录服务（PRD v2 MVP 阶段只记录，不收费）
"""

from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.metering_event import MeteringEvent, generate_metering_event_id


# PRD v2 定义的计量类型
USAGE_TYPES = {
    "job_posted": {"name": "职位发布", "unit_price": 1.0},  # ¥1/条
    "job_search": {"name": "职位搜索", "unit_price": 0.1},  # ¥0.1/次
    "application_submitted": {"name": "申请提交", "unit_price": 0.0},  # 免费
    "contact_unlocked": {"name": "联系方式解锁", "unit_price": 5.0},  # ¥5/次
}

# 免费额度（PRD v2 MVP）
FREE_TIER_CALLS = 100


class MeteringService:
    """
    计量服务

    PRD v2 策略：
    - MVP 阶段不实际收费，只记录用量
    - 企业白名单试用，平台记录真实用量
    - 试点后验证收费模式
    """

    async def record_usage(
        self,
        db: AsyncSession,
        enterprise_id: str,
        usage_type: str,
        quantity: int = 1,
        metadata: Optional[dict] = None,
    ) -> MeteringEvent:
        """
        记录用量事件。

        Args:
            db: 数据库会话
            enterprise_id: 企业 ID
            usage_type: 用量类型（如 job_posted, job_search）
            quantity: 数量
            metadata: 额外元数据

        Returns:
            创建的 MeteringEvent 实例
        """
        unit_info = USAGE_TYPES.get(usage_type, {"name": "unknown", "unit_price": 0.0})

        # MVP 阶段 amount = 0（不实际收费）
        amount = 0.0

        event = MeteringEvent(
            id=generate_metering_event_id(),
            enterprise_id=enterprise_id,
            usage_type=usage_type,
            usage_name=unit_info["name"],
            quantity=quantity,
            unit_price=unit_info["unit_price"],
            amount=amount,  # MVP: 0
            billing_period=self._get_current_billing_period(),
            event_metadata=metadata or {},
        )

        db.add(event)
        await db.flush()
        return event

    async def get_usage_summary(
        self,
        db: AsyncSession,
        enterprise_id: str,
        billing_period: Optional[str] = None,
    ) -> dict:
        """
        获取企业用量汇总。
        """
        period = billing_period or self._get_current_billing_period()

        result = await db.execute(
            select(MeteringEvent)
            .where(
                MeteringEvent.enterprise_id == enterprise_id,
                MeteringEvent.billing_period == period,
            )
        )
        events = result.scalars().all()

        summary = {
            "enterprise_id": enterprise_id,
            "billing_period": period,
            "total_calls": sum(e.quantity for e in events),
            "total_amount": sum(e.amount for e in events),
            "breakdown": {},
        }

        for event in events:
            if event.usage_type not in summary["breakdown"]:
                summary["breakdown"][event.usage_type] = {
                    "name": event.usage_name,
                    "quantity": 0,
                    "amount": 0.0,
                }
            summary["breakdown"][event.usage_type]["quantity"] += event.quantity
            summary["breakdown"][event.usage_type]["amount"] += event.amount

        return summary

    def _get_current_billing_period(self) -> str:
        """获取当前计费周期（YYYY-MM 格式）"""
        now = datetime.now(timezone.utc)
        return now.strftime("%Y-%m")

    def get_free_tier_info(self) -> dict:
        """获取免费额度信息"""
        return {
            "free_calls": FREE_TIER_CALLS,
            "description": "MVP 阶段每企业免费调用次数",
        }


# Singleton
metering_service = MeteringService()
