"""
Metering Event Model
用量记录
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import String, DateTime, Float, Integer, JSON, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from nanoid import generate as nanoid


def generate_metering_event_id() -> str:
    return f"mtr_{nanoid(size=12)}"


class MeteringEvent(Base):
    """
    用量记录事件

    PRD v2 MVP 策略：
    - 职位发布: ¥1/条
    - 职位搜索: ¥0.1/次
    - 申请提交: 免费
    - 联系方式解锁: ¥5/次
    """

    __tablename__ = "metering_events"

    id: Mapped[str] = mapped_column(
        String(64), primary_key=True, default=generate_metering_event_id
    )
    enterprise_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    usage_type: Mapped[str] = mapped_column(String(32), nullable=False)  # job_posted | job_search | application_submitted | contact_unlocked
    usage_name: Mapped[str] = mapped_column(String(64))
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    unit_price: Mapped[float] = mapped_column(Float, default=0.0)
    amount: Mapped[float] = mapped_column(Float, default=0.0)  # MVP: 0
    billing_period: Mapped[str] = mapped_column(String(16))  # YYYY-MM
    event_metadata: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
