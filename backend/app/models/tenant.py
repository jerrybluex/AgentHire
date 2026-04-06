from datetime import datetime
from typing import Optional
from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from nanoid import generate as nanoid

def generate_tenant_id() -> str:
    return f"tenant_{nanoid(size=12)}"

class Tenant(Base):
    """租户 - 企业或个人的数据隔离空间"""
    __tablename__ = "tenants"
    
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=generate_tenant_id)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    type: Mapped[str] = mapped_column(String(32), nullable=False)  # enterprise | individual
    status: Mapped[str] = mapped_column(String(16), default="active")  # active | suspended | deleted
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
