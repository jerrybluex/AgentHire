from datetime import datetime
from typing import Optional
from sqlalchemy import String, DateTime, Integer, Text, ForeignKey, JSON, func
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base
from nanoid import generate as nanoid

def generate_app_event_id() -> str:
    return f"appevt_{nanoid(size=12)}"

class ApplicationEvent(Base):
    """申请事件 - Application 状态变更的完整事件流"""
    __tablename__ = "application_events"
    
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=generate_app_event_id)
    application_id: Mapped[str] = mapped_column(String(64), ForeignKey("applications.id"), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(32), nullable=False)  # submitted | viewed | status_changed | etc
    from_status: Mapped[Optional[str]] = mapped_column(String(32))
    to_status: Mapped[str] = mapped_column(String(32), nullable=False)
    actor_type: Mapped[str] = mapped_column(String(16), nullable=False)  # employer | agent | system
    actor_id: Mapped[Optional[str]] = mapped_column(String(64))
    comment: Mapped[Optional[str]] = mapped_column(Text)
    event_metadata: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
