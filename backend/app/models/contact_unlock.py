from datetime import datetime
from typing import Optional
from sqlalchemy import String, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base
from nanoid import generate as nanoid

def generate_contact_unlock_id() -> str:
    return f"ctunl_{nanoid(size=12)}"

class ContactUnlock(Base):
    """联系方式解锁 - 候选人联系方式的解锁控制"""
    __tablename__ = "contact_unlocks"
    
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=generate_contact_unlock_id)
    application_id: Mapped[str] = mapped_column(String(64), ForeignKey("applications.id"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False)  # locked | candidate_authorized | unlocked | revoked
    authorized_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    unlocked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    reason: Mapped[Optional[str]] = mapped_column(String(256))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
