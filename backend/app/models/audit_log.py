"""
Audit Log Model
Records critical operations for security and compliance.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models import generate_id


class AuditLog(Base):
    """
    Audit Log - Records of critical operations for security and compliance.

    Tracks:
        - Enterprise certification events
        - Agent claiming events
        - API key operations
        - Billing events
        - Login events
        - Data access events
    """

    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(
        String(32), primary_key=True, default=lambda: generate_id("aud_")
    )

    # Event category
    event_type: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True
    )
    # e.g., enterprise_certified, agent_claimed, api_key_created, billing_recorded

    # Actor information
    actor_type: Mapped[str] = mapped_column(
        String(32), nullable=False, index=True
    )
    # e.g., enterprise, agent, user, admin, system

    actor_id: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True, index=True
    )

    # Target information
    target_type: Mapped[Optional[str]] = mapped_column(
        String(32), nullable=True
    )
    # e.g., enterprise, agent, api_key, profile

    target_id: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True, index=True
    )

    # Request context
    request_id: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True, index=True
    )
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(45), nullable=True
    )
    user_agent: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )

    # Event details
    action: Mapped[str] = mapped_column(
        String(64), nullable=False
    )
    # e.g., create, update, delete, verify, approve, reject

    resource_type: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True
    )
    resource_id: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True
    )

    # Change details (JSON for flexible data)
    changes: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True
    )
    # Before/after values, affected fields, etc.

    extra_data: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True
    )
    # Additional context: plan info, rate limit, etc.

    # Result
    status: Mapped[str] = mapped_column(
        String(16), default="success", index=True
    )
    # success, failure, partial

    error_message: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    __table_args__ = (
        Index("idx_audit_event_type_created", "event_type", "created_at"),
        Index("idx_audit_actor_created", "actor_type", "actor_id", "created_at"),
        Index("idx_audit_target_created", "target_type", "target_id", "created_at"),
        Index("idx_audit_status_created", "status", "created_at"),
    )


# Event type constants
class AuditEventType:
    """Audit event type constants."""

    # Enterprise events
    ENTERPRISE_APPLIED = "enterprise_applied"
    ENTERPRISE_APPROVED = "enterprise_approved"
    ENTERPRISE_REJECTED = "enterprise_rejected"
    ENTERPRISE_SUSPENDED = "enterprise_suspended"

    # API Key events
    API_KEY_CREATED = "api_key_created"
    API_KEY_REVOKED = "api_key_revoked"
    API_KEY_ROTATED = "api_key_rotated"

    # Agent events
    AGENT_REGISTERED = "agent_registered"
    AGENT_CLAIMED = "agent_claimed"
    AGENT_VERIFIED = "agent_verified"

    # Authentication events
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILED = "login_failed"
    LOGOUT = "logout"

    # Billing events
    BILLING_RECORDED = "billing_recorded"
    BILLING_QUOTA_EXCEEDED = "billing_quota_exceeded"

    # Data access events
    DATA_EXPORTED = "data_exported"
    DATA_DELETED = "data_deleted"

    # A2A events
    A2A_INTEREST_EXPRESSED = "a2a_interest_expressed"
    A2A_SESSION_CREATED = "a2a_session_created"
    A2A_NEGOTIATION_COMPLETED = "a2a_negotiation_completed"

    # Profile events
    PROFILE_CREATED = "profile_created"
    PROFILE_UPDATED = "profile_updated"
    PROFILE_DELETED = "profile_deleted"

    # Job events
    JOB_POSTED = "job_posted"
    JOB_UPDATED = "job_updated"
    JOB_DELETED = "job_deleted"
    JOB_EXPIRED = "job_expired"


class AuditActorType:
    """Audit actor type constants."""

    ENTERPRISE = "enterprise"
    AGENT = "agent"
    USER = "user"
    ADMIN = "admin"
    SYSTEM = "system"


class AuditAction:
    """Audit action constants."""

    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    VERIFY = "verify"
    APPROVE = "approve"
    REJECT = "reject"
    REVOKE = "revoke"
    ROTATE = "rotate"
    LOGIN = "login"
    LOGOUT = "logout"
    EXPORT = "export"
    ACCESS = "access"
