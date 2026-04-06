"""
Pydantic Schemas for AgentHire API.
Defines request/response models for all endpoints.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


# =============================================================================
# Enums
# =============================================================================


class ProfileStatus(str, Enum):
    """Seeker profile status."""

    ACTIVE = "active"
    PAUSED = "paused"
    DELETED = "deleted"


class EnterpriseStatus(str, Enum):
    """Enterprise verification status."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUSPENDED = "suspended"


class APIKeyStatus(str, Enum):
    """API key status."""

    ACTIVE = "active"
    REVOKED = "revoked"
    EXPIRED = "expired"


class BillingPlan(str, Enum):
    """Billing plan types."""

    PAY_AS_YOU_GO = "pay_as_you_go"
    MONTHLY_BASIC = "monthly_basic"
    MONTHLY_PRO = "monthly_pro"


class JobStatus(str, Enum):
    """Job posting status."""

    ACTIVE = "active"
    PAUSED = "paused"
    FILLED = "filled"
    EXPIRED = "expired"


class ParseStatus(str, Enum):
    """Resume parsing status."""

    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"


class MatchStatus(str, Enum):
    """Match record status."""

    PENDING = "pending"
    SEEKER_RESPONDED = "seeker_responded"
    EMPLOYER_RESPONDED = "employer_responded"
    CONTACT_SHARED = "contact_shared"
    CLOSED = "closed"


class ResponseStatus(str, Enum):
    """Match response type."""

    INTERESTED = "interested"
    NOT_INTERESTED = "not_interested"


class MatchOutcome(str, Enum):
    """Match final outcome."""

    INTERVIEW = "interview"
    HIRED = "hired"
    REJECTED = "rejected"
    NO_RESPONSE = "no_response"


# =============================================================================
# Common Schemas
# =============================================================================


class TimestampMixin(BaseModel):
    """Mixin for timestamp fields."""

    created_at: datetime
    updated_at: Optional[datetime] = None


class SuccessResponse(BaseModel):
    """Standard success response wrapper."""

    success: bool = True
    data: Optional[Any] = None
    message: Optional[str] = None
    error: Optional[str] = None


class PaginatedResponse(BaseModel):
    """Paginated response wrapper."""

    success: bool = True
    data: List[Any] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 20
    has_more: bool = False


# =============================================================================
# Seeker Schemas
# =============================================================================


class BasicInfo(BaseModel):
    """Basic information schema."""

    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    location: Optional[str] = None
    gender: Optional[str] = None
    age: Optional[int] = None


class Skill(BaseModel):
    """Skill schema."""

    name: str
    level: Optional[str] = None  # expert, intermediate, beginner
    years: Optional[float] = None


class WorkExperience(BaseModel):
    """Work experience schema."""

    company: str
    title: str
    duration: Optional[str] = None
    years: Optional[float] = None
    description: Optional[str] = None
    skills_used: List[str] = Field(default_factory=list)
    achievements: List[str] = Field(default_factory=list)


class Education(BaseModel):
    """Education schema."""

    school: str
    major: Optional[str] = None
    degree: Optional[str] = None
    duration: Optional[str] = None


class Project(BaseModel):
    """Project schema."""

    name: str
    description: Optional[str] = None
    technologies: List[str] = Field(default_factory=list)


class Salary(BaseModel):
    """Salary schema."""

    monthly: Optional[float] = None
    currency: str = "CNY"


class JobIntent(BaseModel):
    """Job intent schema."""

    target_roles: List[str] = Field(default_factory=list)
    salary_expectation: Optional[dict] = None
    location_preference: Optional[dict] = None
    skills: List[Skill] = Field(default_factory=list)
    experience_years: Optional[int] = None


class SeekerProfileBase(BaseModel):
    """Base seeker profile schema."""

    nickname: Optional[str] = None
    avatar_url: Optional[str] = None
    job_intent: JobIntent
    privacy: dict = Field(default_factory=dict)
    match_preferences: dict = Field(default_factory=dict)


class SeekerProfileCreate(SeekerProfileBase):
    """Schema for creating a seeker profile."""

    agent_id: str
    agent_type: Optional[str] = None


class SeekerProfileUpdate(BaseModel):
    """Schema for updating a seeker profile."""

    nickname: Optional[str] = None
    avatar_url: Optional[str] = None
    job_intent: Optional[JobIntent] = None
    privacy: Optional[dict] = None
    match_preferences: Optional[dict] = None
    status: Optional[ProfileStatus] = None


class SeekerProfileResponse(SeekerProfileBase, TimestampMixin):
    """Schema for seeker profile response."""

    id: str
    agent_id: str
    agent_type: Optional[str] = None
    status: ProfileStatus
    last_active_at: datetime


# =============================================================================
# Resume Schemas
# =============================================================================


class ResumeFileBase(BaseModel):
    """Base resume file schema."""

    original_filename: str
    file_type: Optional[str] = None
    mime_type: Optional[str] = None


class ResumeFileCreate(ResumeFileBase):
    """Schema for creating a resume file record."""

    profile_id: str
    file_path: str
    file_size: Optional[int] = None


class ResumeFileResponse(ResumeFileBase, TimestampMixin):
    """Schema for resume file response."""

    id: str
    profile_id: str
    file_path: str
    file_size: Optional[int] = None
    parse_status: ParseStatus
    parse_confidence: Optional[float] = None
    parsed_at: Optional[datetime] = None
    is_current: bool


class ParseOptions(BaseModel):
    """Resume parsing options."""

    extract_projects: bool = True
    extract_skills_detail: bool = True
    language_hint: str = "auto"  # zh, en, auto


class ResumeParseRequest(BaseModel):
    """Request schema for resume parsing."""

    parse_options: Optional[ParseOptions] = None


class ParsedResumeData(BaseModel):
    """Parsed resume data schema."""

    basic_info: Optional[BasicInfo] = None
    work_experience: List[WorkExperience] = Field(default_factory=list)
    education: List[Education] = Field(default_factory=list)
    skills: List[Skill] = Field(default_factory=list)
    projects: List[Project] = Field(default_factory=list)
    self_evaluation: Optional[str] = None
    total_work_years: Optional[float] = None
    current_salary: Optional[Salary] = None
    expected_salary: Optional[Salary] = None


class ResumeParseResponse(BaseModel):
    """Response schema for resume parsing."""

    parse_id: str
    confidence: float
    extracted_data: ParsedResumeData
    summary: dict
    missing_or_unclear: List[str] = Field(default_factory=list)


# =============================================================================
# Job Schemas
# =============================================================================


class JobRequirements(BaseModel):
    """Job requirements schema."""

    skills: List[str] = Field(default_factory=list)
    skill_weights: Optional[Dict[str, float]] = None
    experience_min: Optional[int] = None
    experience_max: Optional[int] = None
    education: Optional[str] = None


class JobCompensation(BaseModel):
    """Job compensation schema."""

    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    currency: str = "CNY"
    stock_options: bool = False
    benefits: List[str] = Field(default_factory=list)


class JobLocation(BaseModel):
    """Job location schema."""

    city: Optional[str] = None
    district: Optional[str] = None
    address: Optional[str] = None
    remote_policy: Optional[str] = None  # remote, hybrid, onsite


class JobPostingBase(BaseModel):
    """Base job posting schema."""

    title: str
    department: Optional[str] = None
    description: Optional[str] = None
    responsibilities: List[str] = Field(default_factory=list)
    requirements: JobRequirements
    compensation: Optional[JobCompensation] = None
    location: Optional[JobLocation] = None


class JobPostingCreate(JobPostingBase):
    """Schema for creating a job posting."""

    match_threshold: float = 0.7
    auto_match: bool = True
    active_days: Optional[int] = 30


class JobPostingUpdate(BaseModel):
    """Schema for updating a job posting."""

    title: Optional[str] = None
    department: Optional[str] = None
    description: Optional[str] = None
    responsibilities: Optional[List[str]] = None
    requirements: Optional[JobRequirements] = None
    compensation: Optional[JobCompensation] = None
    location: Optional[JobLocation] = None
    status: Optional[JobStatus] = None


class CompanyInfo(BaseModel):
    """Simplified company information for job listings."""

    name: str
    verified: bool = False
    logo_url: Optional[str] = None


class JobPostingResponse(JobPostingBase, TimestampMixin):
    """Schema for job posting response."""

    id: str
    enterprise_id: str
    api_key_id: str
    status: JobStatus
    published_at: datetime
    expires_at: Optional[datetime] = None
    company: Optional[CompanyInfo] = None


class JobListResponse(PaginatedResponse):
    """Schema for job listing with pagination."""

    data: List[JobPostingResponse] = Field(default_factory=list)


# =============================================================================
# Match Schemas
# =============================================================================


class MatchFactors(BaseModel):
    """Match scoring factors."""

    skill_match: float
    experience_match: float
    location_match: float = 1.0
    salary_match: float = 1.0
    overall: float


class MatchResponse(BaseModel):
    """Schema for match response."""

    match_id: str
    job: JobPostingResponse
    match_score: float
    match_factors: MatchFactors
    status: MatchStatus
    created_at: datetime


class MatchListResponse(PaginatedResponse):
    """Schema for match listing."""

    data: List[MatchResponse] = Field(default_factory=list)


class MatchRespondRequest(BaseModel):
    """Request schema for responding to a match."""

    response: ResponseStatus
    message: Optional[str] = None


# =============================================================================
# Enterprise Schemas
# =============================================================================


class EnterpriseContact(BaseModel):
    """Enterprise contact schema."""

    name: str
    phone: str
    email: EmailStr


class EnterpriseCreate(BaseModel):
    """Schema for creating an enterprise."""

    name: str
    unified_social_credit_code: str
    contact: EnterpriseContact
    company_website: Optional[str] = None
    company_size: Optional[str] = None
    industry: Optional[str] = None


class EnterpriseUpdate(BaseModel):
    """Schema for updating an enterprise."""

    contact: Optional[EnterpriseContact] = None
    company_website: Optional[str] = None
    company_size: Optional[str] = None
    industry: Optional[str] = None
    description: Optional[str] = None


class EnterpriseResponse(EnterpriseCreate, TimestampMixin):
    """Schema for enterprise response."""

    id: str
    status: EnterpriseStatus
    certification: Optional[dict] = None


# =============================================================================
# API Key Schemas
# =============================================================================


class APIKeyCreate(BaseModel):
    """Schema for creating an API key."""

    name: str
    plan: BillingPlan = BillingPlan.PAY_AS_YOU_GO
    rate_limit: int = 100


class APIKeyResponse(BaseModel):
    """Schema for API key response."""

    id: str
    name: str
    api_key: str  # Only shown once at creation
    api_key_prefix: str
    plan: BillingPlan
    rate_limit: int
    status: APIKeyStatus
    expires_at: Optional[datetime] = None
    created_at: datetime


# =============================================================================
# Billing Schemas
# =============================================================================


class BillingRecordResponse(BaseModel):
    """Schema for billing record response."""

    id: str
    usage_type: str
    quantity: int
    unit_price: Optional[float] = None
    amount: Optional[float] = None
    reference_id: Optional[str] = None
    billing_period: Optional[str] = None
    created_at: datetime


class BillingSummary(BaseModel):
    """Billing summary for a period."""

    period: str
    total_amount: float
    total_quantity: int
    records: List[BillingRecordResponse]


# =============================================================================
# Intent Parsing Schemas
# =============================================================================


class IntentType(str, Enum):
    """Intent type."""

    JOB_SEARCH = "job_search"
    RECRUITMENT = "recruitment"


class ParsedIntent(BaseModel):
    """Parsed intent schema."""

    intent_type: IntentType
    parsed: dict
    confidence: float
    missing_fields: List[str] = Field(default_factory=list)


class IntentParseRequest(BaseModel):
    """Request schema for intent parsing."""

    text: str
    intent_type: IntentType
    session_id: Optional[str] = None


class IntentParseResponse(SuccessResponse):
    """Response schema for intent parsing."""

    data: ParsedIntent


# =============================================================================
# Schema Exports
# =============================================================================

__all__ = [
    # Enums
    "ProfileStatus",
    "EnterpriseStatus",
    "APIKeyStatus",
    "BillingPlan",
    "JobStatus",
    "ParseStatus",
    "MatchStatus",
    "ResponseStatus",
    "MatchOutcome",
    "IntentType",
    # Common
    "SuccessResponse",
    "PaginatedResponse",
    # Seeker
    "BasicInfo",
    "Skill",
    "WorkExperience",
    "Education",
    "Project",
    "Salary",
    "JobIntent",
    "SeekerProfileCreate",
    "SeekerProfileUpdate",
    "SeekerProfileResponse",
    # Resume
    "ResumeFileCreate",
    "ResumeFileResponse",
    "ParseOptions",
    "ResumeParseRequest",
    "ParsedResumeData",
    "ResumeParseResponse",
    # Job
    "JobRequirements",
    "JobCompensation",
    "JobLocation",
    "JobPostingCreate",
    "JobPostingUpdate",
    "JobPostingResponse",
    "JobListResponse",
    # Match
    "MatchFactors",
    "MatchResponse",
    "MatchListResponse",
    "MatchRespondRequest",
    # Enterprise
    "EnterpriseContact",
    "EnterpriseCreate",
    "EnterpriseUpdate",
    "EnterpriseResponse",
    # API Key
    "APIKeyCreate",
    "APIKeyResponse",
    # Billing
    "BillingRecordResponse",
    "BillingSummary",
    # Intent
    "IntentParseRequest",
    "IntentParseResponse",
    "ParsedIntent",
]
