"""
SQLAlchemy ORM Models for AgentHire.
Defines all database tables for the recruitment platform.
"""

from datetime import datetime
from typing import Optional

from nanoid import generate as nanoid
from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
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


def generate_id(prefix: str = "") -> str:
    """Generate a unique ID with optional prefix."""
    return f"{prefix}{nanoid(size=12)}"


# =============================================================================
# Agent Models
# =============================================================================


class Agent(Base):
    """
    Agent - Registered agents (job seekers or employers).
    Agents authenticate using HMAC signatures.
    """

    __tablename__ = "agents"

    id: Mapped[str] = mapped_column(
        String(32), primary_key=True, default=lambda: generate_id("agt_")
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    type: Mapped[str] = mapped_column(
        String(16), nullable=False, index=True
    )  # seeker | employer
    platform: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    user_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)

    # Authentication - 存储加密后的 API secret
    # 注册时用 Fernet 加密存储，认证时解密后用于 HMAC 验证
    api_secret_encrypted: Mapped[str] = mapped_column(String(512), nullable=False)

    # PRD v2: Identity linkage
    tenant_id: Mapped[Optional[str]] = mapped_column(String(64), ForeignKey("tenants.id"), nullable=True)
    principal_id: Mapped[Optional[str]] = mapped_column(String(64), ForeignKey("principals.id"), nullable=True)

    # Contact info
    contact: Mapped[dict] = mapped_column(JSON, default=dict)

    # Status
    status: Mapped[str] = mapped_column(
        String(16), default="active", index=True
    )  # active, suspended, deleted

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        Index("idx_agent_type", "type"),
        Index("idx_agent_user_id", "user_id"),
    )


# =============================================================================
# Seeker Models
# =============================================================================


class SeekerProfile(Base):
    """
    Seeker Profile - Job seeker's structured profile.
    Contains job intent, skills, experience, and privacy settings.
    """

    __tablename__ = "seeker_profiles"

    id: Mapped[str] = mapped_column(
        String(32), primary_key=True, default=lambda: generate_id("prof_")
    )
    agent_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    agent_type: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    status: Mapped[str] = mapped_column(
        String(16), default="active", index=True
    )  # active, paused, deleted

    # Basic info (user can choose what to make public)
    nickname: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Job intent (JSON structured)
    job_intent: Mapped[dict] = mapped_column(JSON, nullable=False)

    # Privacy settings
    privacy: Mapped[dict] = mapped_column(JSON, default=dict)

    # Match preferences
    match_preferences: Mapped[dict] = mapped_column(JSON, default=dict)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    last_active_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    resume_files = relationship("ResumeFile", back_populates="profile", lazy="dynamic")
    matches = relationship("JobMatch", back_populates="seeker", lazy="dynamic")

    __table_args__ = (
        Index("idx_seeker_status", "status"),
        Index("idx_seeker_agent_id", "agent_id"),
    )


class ResumeFile(Base):
    """
    Resume File - Stores uploaded resume files and parsing results.
    """

    __tablename__ = "resume_files"

    id: Mapped[str] = mapped_column(
        String(32), primary_key=True, default=lambda: generate_id("res_")
    )
    profile_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("seeker_profiles.id", ondelete="CASCADE"), nullable=False
    )

    # File information
    original_filename: Mapped[str] = mapped_column(String(256), nullable=False)
    file_path: Mapped[str] = mapped_column(Text, nullable=False)  # S3/MinIO path
    file_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # bytes
    file_type: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    mime_type: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    # Parsing results
    parse_status: Mapped[str] = mapped_column(
        String(16), default="pending", index=True
    )  # pending, processing, success, failed
    parse_result: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    parse_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    parsed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Raw text (optional, for debugging and optimization)
    raw_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Version control
    version: Mapped[int] = mapped_column(Integer, default=1)
    is_current: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    profile = relationship("SeekerProfile", back_populates="resume_files")
    parse_jobs = relationship("ResumeParseJob", back_populates="resume_file", lazy="dynamic")

    __table_args__ = (
        Index("idx_resume_profile", "profile_id"),
        Index("idx_resume_status", "parse_status"),
    )


class ResumeParseJob(Base):
    """
    Resume Parse Job - Async task for resume parsing.
    """

    __tablename__ = "resume_parse_jobs"

    id: Mapped[str] = mapped_column(
        String(32), primary_key=True, default=lambda: generate_id("pjs_")
    )
    resume_file_id: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("resume_files.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Task status
    status: Mapped[str] = mapped_column(
        String(16), default="queued", index=True
    )  # queued, processing, completed, failed

    # Processing result
    result: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Processing metadata
    processor_node: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    resume_file = relationship("ResumeFile", back_populates="parse_jobs")

    __table_args__ = (Index("idx_parse_job_status", "status"),)


# =============================================================================
# Job Models
# =============================================================================


class JobPosting(Base):
    """
    Job Posting - Published job positions by enterprises.
    """

    __tablename__ = "job_postings"

    id: Mapped[str] = mapped_column(
        String(32), primary_key=True, default=lambda: generate_id("job_")
    )
    enterprise_id: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("enterprises.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    api_key_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("enterprise_api_keys.id"), nullable=False
    )

    # Job information
    title: Mapped[str] = mapped_column(String(128), nullable=False)
    department: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    responsibilities: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)

    # Requirements (structured JSON)
    requirements: Mapped[dict] = mapped_column(JSON, nullable=False)

    # Compensation
    compensation: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Location
    location: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Status
    status: Mapped[str] = mapped_column(
        String(16), default="active", index=True
    )  # active, paused, filled, expired

    published_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Match settings
    match_threshold: Mapped[float] = mapped_column(Float, default=0.7)
    auto_match: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    enterprise = relationship("Enterprise", back_populates="job_postings")
    api_key = relationship("EnterpriseAPIKey", back_populates="job_postings")
    matches = relationship("JobMatch", back_populates="job", lazy="dynamic")

    __table_args__ = (
        Index("idx_job_enterprise", "enterprise_id"),
        Index("idx_job_status_expires", "status", "expires_at"),
    )


class JobMatch(Base):
    """
    Job Match - Matching records between seekers and jobs.
    """

    __tablename__ = "job_matches"

    id: Mapped[str] = mapped_column(
        String(32), primary_key=True, default=lambda: generate_id("mat_")
    )
    seeker_id: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("seeker_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    job_id: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("job_postings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Match details
    match_score: Mapped[float] = mapped_column(Float, nullable=False)  # 0-1
    match_factors: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Status flow
    status: Mapped[str] = mapped_column(
        String(16), default="pending", index=True
    )  # pending -> seeker_responded -> employer_responded -> contact_shared -> closed

    seeker_response: Mapped[Optional[str]] = mapped_column(
        String(16), nullable=True
    )  # interested, not_interested
    seeker_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    seeker_responded_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    employer_response: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    employer_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    employer_responded_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    contact_shared_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Feedback (for algorithm optimization)
    outcome: Mapped[Optional[str]] = mapped_column(
        String(16), nullable=True
    )  # interview, hired, rejected, no_response
    feedback_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    seeker = relationship("SeekerProfile", back_populates="matches")
    job = relationship("JobPosting", back_populates="matches")

    __table_args__ = (
        Index("idx_match_seeker_status", "seeker_id", "status"),
        Index("idx_match_job_status", "job_id", "status"),
        Index("idx_match_score", "match_score"),
    )


# =============================================================================
# Enterprise Models
# =============================================================================


class Enterprise(Base):
    """
    Enterprise - Company profile with verification status.
    """

    __tablename__ = "enterprises"

    id: Mapped[str] = mapped_column(
        String(32), primary_key=True, default=lambda: generate_id("ent_")
    )

    # Basic information
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    unified_social_credit_code: Mapped[Optional[str]] = mapped_column(
        String(32), nullable=True, unique=True
    )

    # Certification materials
    certification: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Contact information
    contact: Mapped[dict] = mapped_column(JSON, nullable=False)

    # Password for login
    password_hash: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)

    # Company info
    website: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    industry: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    company_size: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    logo_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # PRD v2: Identity linkage
    tenant_id: Mapped[Optional[str]] = mapped_column(
        String(64), ForeignKey("tenants.id"), nullable=True
    )

    # Verification status
    status: Mapped[str] = mapped_column(
        String(16), default="pending", index=True
    )  # pending, approved, rejected, suspended

    # Billing settings
    billing_info: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    api_keys = relationship(
        "EnterpriseAPIKey", back_populates="enterprise", lazy="dynamic"
    )
    job_postings = relationship(
        "JobPosting", back_populates="enterprise", lazy="dynamic"
    )

    __table_args__ = (
        Index("idx_enterprise_status", "status"),
        Index("idx_enterprise_credit_code", "unified_social_credit_code"),
    )


class EnterpriseAPIKey(Base):
    """
    Enterprise API Key - API access credentials for enterprises.
    """

    __tablename__ = "enterprise_api_keys"

    id: Mapped[str] = mapped_column(
        String(32), primary_key=True, default=lambda: generate_id("key_")
    )
    enterprise_id: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("enterprises.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(String(64), nullable=False)
    api_key_hash: Mapped[str] = mapped_column(String(256), nullable=False)
    api_key_prefix: Mapped[str] = mapped_column(String(16), nullable=False)

    # Plan
    plan: Mapped[str] = mapped_column(
        String(32), default="pay_as_you_go", index=True
    )  # pay_as_you_go, monthly_basic, monthly_pro

    # Limits
    rate_limit: Mapped[int] = mapped_column(Integer, default=100)  # per minute
    monthly_quota: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Status
    status: Mapped[str] = mapped_column(
        String(16), default="active", index=True
    )  # active, revoked, expired
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    last_used_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    enterprise = relationship("Enterprise", back_populates="api_keys")
    job_postings = relationship("JobPosting", back_populates="api_key")
    billing_records = relationship("BillingRecord", back_populates="api_key")

    __table_args__ = (
        Index("idx_api_key_hash", "api_key_hash"),
        Index("idx_api_key_enterprise", "enterprise_id"),
    )


class BillingRecord(Base):
    """
    Billing Record - Usage and billing records for enterprises.
    """

    __tablename__ = "billing_records"

    id: Mapped[str] = mapped_column(
        String(32), primary_key=True, default=lambda: generate_id("bil_")
    )
    enterprise_id: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("enterprises.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    api_key_id: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("enterprise_api_keys.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Usage details
    usage_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    # job_post, match_query, match_success, profile_view

    quantity: Mapped[int] = mapped_column(Integer, default=1)
    unit_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Reference
    reference_id: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)

    # Billing period (for monthly plans)
    billing_period: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    enterprise = relationship("Enterprise")
    api_key = relationship("EnterpriseAPIKey", back_populates="billing_records")

    __table_args__ = (
        Index("idx_billing_enterprise_period", "enterprise_id", "billing_period"),
    )


# =============================================================================
# A2A Protocol Models
# =============================================================================


class A2AInterest(Base):
    """
    A2A Interest - Records of interest expression from seeker to employer.
    Part of the Agent-to-Agent negotiation protocol.
    """

    __tablename__ = "a2a_interests"

    id: Mapped[str] = mapped_column(
        String(32), primary_key=True, default=lambda: generate_id("int_")
    )
    profile_id: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("seeker_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    job_id: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("job_postings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    seeker_agent_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    employer_agent_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    # Interest status
    status: Mapped[str] = mapped_column(
        String(16), default="pending", index=True
    )  # pending, accepted, rejected

    # Message
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        Index("idx_interest_profile_job", "profile_id", "job_id", unique=True),
        Index("idx_interest_seeker", "seeker_agent_id"),
        Index("idx_interest_employer", "employer_agent_id"),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "profile_id": self.profile_id,
            "job_id": self.job_id,
            "seeker_agent_id": self.seeker_agent_id,
            "employer_agent_id": self.employer_agent_id,
            "status": self.status,
            "message": self.message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class A2ASession(Base):
    """
    A2A Session - Negotiation sessions between agents.
    Tracks salary negotiation and confirmation status.
    """

    __tablename__ = "a2a_sessions"

    id: Mapped[str] = mapped_column(
        String(32), primary_key=True, default=lambda: generate_id("ses_")
    )
    interest_id: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("a2a_interests.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    profile_id: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("seeker_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    job_id: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("job_postings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    seeker_agent_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    employer_agent_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    # Session status
    status: Mapped[str] = mapped_column(
        String(16), default="negotiating", index=True
    )  # negotiating, confirmed, rejected

    # Current offer
    current_offer: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Negotiation history (list of messages)
    messages: Mapped[Optional[list]] = mapped_column(JSON, default=list)

    # Confirmations
    seeker_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    employer_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)

    # Contact exchange
    contact_exchanged_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        Index("idx_session_interest", "interest_id"),
        Index("idx_session_profile", "profile_id"),
        Index("idx_session_job", "job_id"),
        Index("idx_session_status", "status"),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "interest_id": self.interest_id,
            "profile_id": self.profile_id,
            "job_id": self.job_id,
            "seeker_agent_id": self.seeker_agent_id,
            "employer_agent_id": self.employer_agent_id,
            "status": self.status,
            "current_offer": self.current_offer,
            "messages": self.messages,
            "seeker_confirmed": self.seeker_confirmed,
            "employer_confirmed": self.employer_confirmed,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


# =============================================================================
# Webhook Models
# =============================================================================


class Webhook(Base):
    """
    Webhook - Registered webhook URLs for event notifications.
    """

    __tablename__ = "webhooks"

    id: Mapped[str] = mapped_column(
        String(32), primary_key=True, default=lambda: generate_id("whk_")
    )
    enterprise_id: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("enterprises.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Webhook URL and events
    url: Mapped[str] = mapped_column(Text, nullable=False)
    events: Mapped[list] = mapped_column(JSON, nullable=False)

    # Security
    secret: Mapped[str] = mapped_column(String(256), nullable=False)

    # Status
    active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Stats
    success_count: Mapped[int] = mapped_column(Integer, default=0)
    failure_count: Mapped[int] = mapped_column(Integer, default=0)
    last_triggered_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        Index("idx_webhook_enterprise", "enterprise_id"),
        Index("idx_webhook_active", "active"),
    )


class WebhookDelivery(Base):
    """
    Webhook Delivery - Records of webhook delivery attempts.
    """

    __tablename__ = "webhook_deliveries"

    id: Mapped[str] = mapped_column(
        String(32), primary_key=True, default=lambda: generate_id("whd_")
    )
    webhook_id: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("webhooks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Event info
    event: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)

    # Delivery result
    status: Mapped[str] = mapped_column(
        String(16), default="pending", index=True
    )  # pending, sent, failed
    response_status: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    response_body: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timing
    attempt_count: Mapped[int] = mapped_column(Integer, default=1)
    sent_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        Index("idx_delivery_webhook", "webhook_id"),
        Index("idx_delivery_status", "status"),
        Index("idx_delivery_event", "event"),
    )


# =============================================================================
# User Model (for Agent Claiming)
# =============================================================================


class User(Base):
    """
    User - C端用户，用于认领 Agent。
    """

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String(32), primary_key=True, default=lambda: generate_id("usr_")
    )
    email: Mapped[str] = mapped_column(String(256), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(256), nullable=False)
    nickname: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(
        String(16), default="active", index=True
    )  # active, suspended, deleted

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (Index("idx_user_email", "email"),)


# =============================================================================
# Agent Claim Model
# =============================================================================


class AgentClaim(Base):
    """
    Agent Claim - Records of Agent claiming by users.
    """

    __tablename__ = "agent_claims"

    id: Mapped[str] = mapped_column(
        String(32), primary_key=True, default=lambda: generate_id("clm_")
    )
    user_id: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    agent_id: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    verification_code: Mapped[str] = mapped_column(String(6), nullable=False)
    status: Mapped[str] = mapped_column(
        String(16), default="pending", index=True
    )  # pending, verified, expired

    claimed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    verified_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        Index("idx_claim_user_agent", "user_id", "agent_id", unique=True),
        Index("idx_claim_status", "status"),
    )


# =============================================================================
# Model Exports
# =============================================================================

# Import new PRD v2 models
from app.models.tenant import Tenant
from app.models.principal import Principal
from app.models.credential import Credential
from app.models.job_version import JobVersion
from app.models.application_event import ApplicationEvent
from app.models.application import Application
from app.models.contact_unlock import ContactUnlock
from app.models.enterprise_verification import EnterpriseVerificationCase
from app.models.metering_event import MeteringEvent, generate_metering_event_id

__all__ = [
    "Agent",
    "SeekerProfile",
    "ResumeFile",
    "ResumeParseJob",
    "JobPosting",
    "JobMatch",
    "Enterprise",
    "EnterpriseAPIKey",
    "BillingRecord",
    "A2AInterest",
    "A2ASession",
    "Webhook",
    "WebhookDelivery",
    "User",
    "AgentClaim",
    "Tenant",
    "Principal",
    "Credential",
    "JobVersion",
    "ApplicationEvent",
    "Application",
    "ContactUnlock",
    "EnterpriseVerificationCase",
    "MeteringEvent",
    "generate_id",
    "generate_metering_event_id",
]
