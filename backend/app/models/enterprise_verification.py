"""
Enterprise Verification Case Model
企业实名审核案例
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import String, DateTime, Text, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from nanoid import generate as nanoid


def generate_verification_id() -> str:
    return f"evc_{nanoid(size=12)}"


class EnterpriseVerificationCase(Base):
    """
    企业审核案例 - 企业实名审核的状态机
    
    状态转换:
    - draft: 草稿
    - submitted: 已提交，等待审核
    - under_review: 审核中
    - needs_resubmission: 需要补充材料
    - approved: 审核通过
    - rejected: 审核拒绝（终态）
    - suspended: 暂停/吊销（终态）
    """

    __tablename__ = "enterprise_verification_cases"

    id: Mapped[str] = mapped_column(
        String(64), primary_key=True, default=generate_verification_id
    )
    enterprise_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("enterprises.id"), nullable=False, index=True
    )
    
    # 状态
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="draft"
    )
    
    # 提交信息
    submitted_by: Mapped[Optional[str]] = mapped_column(String(64))
    submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # 审核信息
    reviewed_by: Mapped[Optional[str]] = mapped_column(String(64))  # 审核人 principal_id
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    review_comment: Mapped[Optional[str]] = mapped_column(Text)
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text)
    
    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
