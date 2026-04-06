from datetime import datetime
from typing import Optional
from sqlalchemy import String, DateTime, Integer, Text, ForeignKey, JSON, func
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base
from nanoid import generate as nanoid

def generate_job_version_id() -> str:
    return f"jobv_{nanoid(size=12)}"

class JobVersion(Base):
    """职位版本 - Job 的版本化管理"""
    __tablename__ = "job_versions"
    
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=generate_job_version_id)
    job_id: Mapped[str] = mapped_column(String(64), ForeignKey("job_postings.id"), nullable=False, index=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    department: Mapped[Optional[str]] = mapped_column(String(128))
    description: Mapped[Optional[str]] = mapped_column(Text)
    requirements: Mapped[dict] = mapped_column(JSON, default=dict)  # 结构化技能/年限要求
    compensation: Mapped[dict] = mapped_column(JSON, default=dict)  # 薪资范围
    location: Mapped[dict] = mapped_column(JSON, default=dict)  # 地点/远程策略
    status: Mapped[str] = mapped_column(String(16), default="active")
    created_by: Mapped[Optional[str]] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
