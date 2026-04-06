from datetime import datetime
from typing import Optional
from sqlalchemy import String, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from nanoid import generate as nanoid

def generate_principal_id() -> str:
    return f"prin_{nanoid(size=12)}"

class Principal(Base):
    """主体 - 租户下的用户/人/操作员"""
    __tablename__ = "principals"
    
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=generate_principal_id)
    tenant_id: Mapped[str] = mapped_column(String(64), ForeignKey("tenants.id"), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(16), nullable=False)  # human | agent | service
    name: Mapped[Optional[str]] = mapped_column(String(128))
    email: Mapped[Optional[str]] = mapped_column(String(256))
    status: Mapped[str] = mapped_column(String(16), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    tenant = relationship("Tenant", backref="principals")
