"""
Test factories for creating test data.
"""

import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional

from app.models import (
    Agent,
    Enterprise,
    EnterpriseAPIKey,
    SeekerProfile,
    JobPosting,
    A2AInterest,
    A2ASession,
    Webhook,
    BillingRecord,
    ResumeFile,
    User,
    AgentClaim,
    generate_id,
)


def hash_secret(secret: str) -> str:
    """Hash a secret for storage."""
    return hashlib.sha256(secret.encode()).hexdigest()


class AgentFactory:
    """Factory for creating test Agent instances."""

    @staticmethod
    def create(
        id: Optional[str] = None,
        name: str = "Test Agent",
        type: str = "seeker",
        platform: Optional[str] = "test",
        user_id: Optional[str] = None,
        status: str = "active",
    ) -> Agent:
        """Create a test Agent."""
        return Agent(
            id=id or generate_id("agt_"),
            name=name,
            type=type,
            platform=platform,
            user_id=user_id or generate_id("usr_"),
            agent_secret_hash=hash_secret("test_secret"),
            contact={"email": "test@example.com"},
            status=status,
            created_at=datetime.utcnow(),
        )


class EnterpriseFactory:
    """Factory for creating test Enterprise instances."""

    @staticmethod
    def create(
        id: Optional[str] = None,
        name: str = "Test Company",
        status: str = "approved",
        contact: Optional[dict] = None,
        certification: Optional[dict] = None,
        billing_info: Optional[dict] = None,
        **kwargs,
    ) -> Enterprise:
        """Create a test Enterprise."""
        return Enterprise(
            id=id or generate_id("ent_"),
            name=name,
            unified_social_credit_code=f"USCC{secrets.token_hex(8)}",
            certification=certification or {"verified": True},
            contact=contact or {"email": "contact@test.com", "phone": "1234567890"},
            billing_info=billing_info,
            status=status,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )


class EnterpriseAPIKeyFactory:
    """Factory for creating test API Key instances."""

    @staticmethod
    def create(
        enterprise_id: str,
        id: Optional[str] = None,
        name: str = "Test Key",
        plan: str = "pay_as_you_go",
        status: str = "active",
        raw_key: Optional[str] = None,
    ) -> tuple[EnterpriseAPIKey, str]:
        """Create a test API Key. Returns (key, raw_key)."""
        raw_key = raw_key or f"ah_{secrets.token_urlsafe(32)}"
        return (
            EnterpriseAPIKey(
                id=id or generate_id("key_"),
                enterprise_id=enterprise_id,
                name=name,
                api_key_hash=hashlib.sha256(raw_key.encode()).hexdigest(),
                api_key_prefix=raw_key[:12],
                plan=plan,
                rate_limit=100,
                status=status,
                created_at=datetime.utcnow(),
            ),
            raw_key,
        )


class SeekerProfileFactory:
    """Factory for creating test SeekerProfile instances."""

    @staticmethod
    def create(
        agent_id: str,
        id: Optional[str] = None,
        nickname: str = "Test User",
        status: str = "active",
    ) -> SeekerProfile:
        """Create a test SeekerProfile."""
        return SeekerProfile(
            id=id or generate_id("prof_"),
            agent_id=agent_id,
            agent_type="seeker",
            status=status,
            nickname=nickname,
            avatar_url=None,
            job_intent={
                "target_roles": ["Engineer"],
                "salary_expectation": {"min_monthly": 30000, "max_monthly": 50000},
                "location_preference": {"cities": ["北京", "上海"]},
            },
            privacy={},
            match_preferences={},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )


class JobPostingFactory:
    """Factory for creating test JobPosting instances."""

    @staticmethod
    def create(
        enterprise_id: str,
        api_key_id: str,
        id: Optional[str] = None,
        title: str = "Software Engineer",
        status: str = "active",
    ) -> JobPosting:
        """Create a test JobPosting."""
        return JobPosting(
            id=id or generate_id("job_"),
            enterprise_id=enterprise_id,
            api_key_id=api_key_id,
            title=title,
            department="Engineering",
            description="Test job description",
            responsibilities=["Coding", "Review"],
            requirements={
                "skills": ["Python", "Go"],
                "experience_min": 2,
            },
            compensation={
                "salary_min": 30000,
                "salary_max": 50000,
            },
            location={"city": "上海", "remote_policy": "hybrid"},
            status=status,
            published_at=datetime.utcnow() if status == "active" else None,
            expires_at=datetime.utcnow() + timedelta(days=30),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )


class A2AInterestFactory:
    """Factory for creating test A2AInterest instances."""

    @staticmethod
    def create(
        id: Optional[str] = None,
        profile_id: str = None,
        job_id: str = None,
        seeker_agent_id: str = None,
        employer_agent_id: str = None,
        status: str = "pending",
    ) -> A2AInterest:
        """Create a test A2AInterest."""
        return A2AInterest(
            id=id or generate_id("int_"),
            profile_id=profile_id or generate_id("prof_"),
            job_id=job_id or generate_id("job_"),
            seeker_agent_id=seeker_agent_id or generate_id("agt_"),
            employer_agent_id=employer_agent_id or generate_id("agt_"),
            status=status,
            message="I'm interested",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )


class A2ASessionFactory:
    """Factory for creating test A2ASession instances."""

    @staticmethod
    def create(
        id: Optional[str] = None,
        interest_id: str = None,
        profile_id: str = None,
        job_id: str = None,
        seeker_agent_id: str = None,
        employer_agent_id: str = None,
        status: str = "negotiating",
        seeker_confirmed: bool = False,
        employer_confirmed: bool = False,
    ) -> A2ASession:
        """Create a test A2ASession."""
        return A2ASession(
            id=id or generate_id("ses_"),
            interest_id=interest_id or generate_id("int_"),
            profile_id=profile_id or generate_id("prof_"),
            job_id=job_id or generate_id("job_"),
            seeker_agent_id=seeker_agent_id or generate_id("agt_"),
            employer_agent_id=employer_agent_id or generate_id("agt_"),
            status=status,
            current_offer={"salary": 40000, "start_date": "2026-05-01"},
            messages=[],
            seeker_confirmed=seeker_confirmed,
            employer_confirmed=employer_confirmed,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )


class WebhookFactory:
    """Factory for creating test Webhook instances."""

    @staticmethod
    def create(
        enterprise_id: str,
        id: Optional[str] = None,
        url: str = "https://example.com/webhook",
        events: list = None,
        active: bool = True,
    ) -> Webhook:
        """Create a test Webhook."""
        return Webhook(
            id=id or generate_id("whk_"),
            enterprise_id=enterprise_id,
            url=url,
            events=events or ["job.new", "profile.new"],
            secret=secrets.token_urlsafe(32),
            active=active,
            success_count=0,
            failure_count=0,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )


class BillingRecordFactory:
    """Factory for creating test BillingRecord instances."""

    @staticmethod
    def create(
        id: Optional[str] = None,
        enterprise_id: str = None,
        api_key_id: str = None,
        usage_type: str = "job_post",
        quantity: int = 1,
        unit_price: float = 0.5,
        amount: Optional[float] = None,
        reference_id: Optional[str] = None,
        billing_period: Optional[str] = None,
    ) -> BillingRecord:
        """Create a test BillingRecord."""
        return BillingRecord(
            id=id or generate_id("bil_"),
            enterprise_id=enterprise_id or generate_id("ent_"),
            api_key_id=api_key_id or generate_id("key_"),
            usage_type=usage_type,
            quantity=quantity,
            unit_price=unit_price,
            amount=amount or (unit_price * quantity if unit_price else None),
            reference_id=reference_id,
            billing_period=billing_period or datetime.utcnow().strftime("%Y-%m"),
            created_at=datetime.utcnow(),
        )


class ResumeFileFactory:
    """Factory for creating test ResumeFile instances."""

    @staticmethod
    def create(
        id: Optional[str] = None,
        profile_id: str = None,
        original_filename: str = "test_resume.pdf",
        file_path: str = "/uploads/test_resume.pdf",
        file_size: int = 1024,
        file_type: str = "pdf",
        mime_type: str = "application/pdf",
        parse_status: str = "success",
        parse_result: Optional[dict] = None,
        parse_confidence: float = 0.95,
        is_current: bool = True,
    ) -> ResumeFile:
        """Create a test ResumeFile."""
        return ResumeFile(
            id=id or generate_id("res_"),
            profile_id=profile_id or generate_id("prof_"),
            original_filename=original_filename,
            file_path=file_path,
            file_size=file_size,
            file_type=file_type,
            mime_type=mime_type,
            parse_status=parse_status,
            parse_result=parse_result or {"name": "Test User", "skills": ["Python"]},
            parse_confidence=parse_confidence,
            is_current=is_current,
            version=1,
            created_at=datetime.utcnow(),
        )


class UserFactory:
    """Factory for creating test User instances."""

    @staticmethod
    def create(
        id: Optional[str] = None,
        email: str = "test@example.com",
        nickname: Optional[str] = None,
        status: str = "active",
    ) -> User:
        """Create a test User."""
        # Create a simple password hash
        salt = secrets.token_hex(16)
        password_hash = hashlib.sha256(f"{salt}password".encode()).hexdigest() + ":" + salt

        return User(
            id=id or generate_id("usr_"),
            email=email,
            password_hash=password_hash,
            nickname=nickname,
            status=status,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )


class AgentClaimFactory:
    """Factory for creating test AgentClaim instances."""

    @staticmethod
    def create(
        id: Optional[str] = None,
        user_id: str = None,
        agent_id: str = None,
        verification_code: str = "123456",
        status: str = "pending",
    ) -> AgentClaim:
        """Create a test AgentClaim."""
        return AgentClaim(
            id=id or generate_id("clm_"),
            user_id=user_id or generate_id("usr_"),
            agent_id=agent_id or generate_id("agt_"),
            verification_code=verification_code,
            status=status,
            expires_at=datetime.utcnow() + timedelta(hours=24),
            created_at=datetime.utcnow(),
        )
