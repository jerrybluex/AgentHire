from datetime import datetime
from typing import Optional
from sqlalchemy import String, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base
from nanoid import generate as nanoid

def generate_credential_id() -> str:
    return f"cred_{nanoid(size=12)}"

class Credential(Base):
    """凭证 - 认证凭据（API Key / Agent Secret / Password）"""
    __tablename__ = "credentials"
    
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=generate_credential_id)
    principal_id: Mapped[str] = mapped_column(String(64), ForeignKey("principals.id"), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(32), nullable=False)  # api_key | agent_secret | password
    key_hash: Mapped[str] = mapped_column(String(256), nullable=False)  # 存储哈希而非明文
    name: Mapped[Optional[str]] = mapped_column(String(128))  # 凭证名称
    status: Mapped[str] = mapped_column(String(16), default="active")  # active | revoked | expired
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
