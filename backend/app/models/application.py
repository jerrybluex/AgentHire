"""
Application Model
申请 - 求职者对职位的申请记录
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import String, DateTime, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from nanoid import generate as nanoid


def generate_application_id() -> str:
    """Generate a unique application ID."""
    return f"app_{nanoid(size=12)}"


class Application(Base):
    """
    Application - 求职者对职位的申请记录。

    状态机：
    - draft: 草稿（Agent 创建，未提交）
    - submitted: 已提交
    - viewed: 已查看
    - shortlisted: 列入候选
    - rejected: 已拒绝
    - interview_requested: 请求面试
    - interview_scheduled: 面试已安排
    - closed: 已关闭
    """

    __tablename__ = "applications"

    id: Mapped[str] = mapped_column(
        String(64), primary_key=True, default=generate_application_id
    )

    # 关联信息
    profile_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("seeker_profiles.id"), nullable=False, index=True
    )
    job_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("job_postings.id"), nullable=False, index=True
    )

    # 申请人身份（Principal ID，用于跨系统追踪）
    applicant_principal_id: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True, index=True
    )

    # 求职信
    cover_letter: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # 状态
    status: Mapped[str] = mapped_column(
        String(32), default="draft", index=True
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    profile = relationship("SeekerProfile", lazy="selectin")
    job = relationship("JobPosting", lazy="selectin")

    __table_args__ = (
        # 同一求职者对同一职位只能有一条申请
        # Unique constraint is handled at DB level via migration
    )
