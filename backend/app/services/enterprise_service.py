"""
Enterprise Service
企业管理、API密钥和计费的业务逻辑
"""

import secrets
import hashlib
from typing import Optional
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Enterprise, EnterpriseAPIKey, BillingRecord, generate_id


class QuotaExceededError(Exception):
    """Raised when an enterprise's monthly quota is exceeded."""
    pass


def hash_password(password: str) -> str:
    """Hash a password using PBKDF2."""
    import bcrypt
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against its hash."""
    import bcrypt
    return bcrypt.checkpw(password.encode(), password_hash.encode())


# Default page size for paginated queries
DEFAULT_PAGE_SIZE = 20


class EnterpriseService:
    """Service for managing enterprises, API keys, and billing."""

    async def create_application(
        self,
        db: AsyncSession,
        company_name: str,
        unified_social_credit_code: str,
        contact: dict,
        certification: dict,
        company_info: dict,
        password: Optional[str] = None,
    ) -> Enterprise:
        """
        Create a new enterprise application.

        Args:
            db: Database session
            company_name: Company name
            unified_social_credit_code: Business license code
            contact: Contact information
            certification: Certification documents
            company_info: Additional company information
            password: Plain text password (will be hashed)

        Returns:
            Created Enterprise instance (status='pending')
        """
        enterprise = Enterprise(
            id=generate_id("ent_"),
            name=company_name,
            unified_social_credit_code=unified_social_credit_code,
            certification=certification,
            contact=contact,
            website=company_info.get("website"),
            industry=company_info.get("industry"),
            company_size=company_info.get("company_size"),
            description=company_info.get("description"),
            status="pending",  # Requires approval
            password_hash=hash_password(password) if password else None,
        )

        db.add(enterprise)
        await db.flush()

        return enterprise

    async def get_enterprise(
        self,
        db: AsyncSession,
        enterprise_id: str,
    ) -> Optional[Enterprise]:
        """Get an enterprise by ID."""
        result = await db.execute(
            select(Enterprise).where(Enterprise.id == enterprise_id)
        )
        return result.scalar_one_or_none()

    async def get_enterprise_by_email(
        self,
        db: AsyncSession,
        email: str,
    ) -> Optional[Enterprise]:
        """Get an enterprise by contact email."""
        result = await db.execute(
            select(Enterprise).where(Enterprise.contact["email"].as_string() == email.lower())
        )
        return result.scalar_one_or_none()

    async def approve_enterprise(
        self,
        db: AsyncSession,
        enterprise_id: str,
        approved_by: str,
    ) -> Optional[Enterprise]:
        """Approve an enterprise application."""
        enterprise = await self.get_enterprise(db, enterprise_id)
        if not enterprise:
            return None

        enterprise.status = "approved"
        enterprise.certification = enterprise.certification or {}
        enterprise.certification["verified_at"] = datetime.utcnow().isoformat()
        enterprise.certification["verified_by"] = approved_by

        await db.flush()
        return enterprise

    async def create_api_key(
        self,
        db: AsyncSession,
        enterprise_id: str,
        name: str,
        plan: str = "pay_as_you_go",
        rate_limit: int = 100,
        monthly_quota: Optional[int] = None,
    ) -> Optional[dict]:
        """
        Create a new API key for an enterprise.

        Returns:
            Dict with api_key (full key, shown only once) and api_key_id
        """
        enterprise = await self.get_enterprise(db, enterprise_id)
        if not enterprise or enterprise.status != "approved":
            return None

        # Generate API key
        raw_key = f"ah_{secrets.token_urlsafe(32)}"
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        key_prefix = raw_key[:12]

        api_key = EnterpriseAPIKey(
            id=generate_id("key_"),
            enterprise_id=enterprise_id,
            name=name,
            api_key_hash=key_hash,
            api_key_prefix=key_prefix,
            plan=plan,
            rate_limit=rate_limit,
            monthly_quota=monthly_quota,
            status="active",
        )

        db.add(api_key)
        await db.flush()

        return {
            "id": api_key.id,
            "api_key": raw_key,  # Only shown once!
            "api_key_prefix": key_prefix,
            "name": name,
            "plan": plan,
        }

    async def validate_api_key(
        self,
        db: AsyncSession,
        raw_key: str,
    ) -> Optional[tuple[str, str]]:
        """
        Validate an API key.

        Returns:
            Tuple of (enterprise_id, api_key_id) if valid, None otherwise
        """
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

        result = await db.execute(
            select(EnterpriseAPIKey).where(
                EnterpriseAPIKey.api_key_hash == key_hash,
                EnterpriseAPIKey.status == "active",
            )
        )
        api_key = result.scalar_one_or_none()

        if not api_key:
            return None

        # Check expiration
        if api_key.expires_at and api_key.expires_at < datetime.utcnow():
            return None

        return api_key.enterprise_id, api_key.id

    async def record_usage(
        self,
        db: AsyncSession,
        enterprise_id: str,
        api_key_id: str,
        usage_type: str,
        quantity: int = 1,
        reference_id: Optional[str] = None,
    ) -> BillingRecord:
        """Record API usage for billing."""
        from sqlalchemy import func

        # Check monthly quota enforcement
        api_key_result = await db.execute(
            select(EnterpriseAPIKey).where(EnterpriseAPIKey.id == api_key_id).with_for_update()
        )
        api_key = api_key_result.scalar_one_or_none()
        if api_key and api_key.monthly_quota is not None:
            current_period = datetime.utcnow().strftime("%Y-%m")
            usage_result = await db.execute(
                select(func.coalesce(func.sum(BillingRecord.quantity), 0)).where(
                    BillingRecord.api_key_id == api_key_id,
                    BillingRecord.billing_period == current_period,
                )
            )
            current_usage = usage_result.scalar()
            if current_usage + quantity > api_key.monthly_quota:
                raise QuotaExceededError(
                    f"Monthly quota exceeded: {current_usage}/{api_key.monthly_quota} "
                    f"(period: {current_period})"
                )

        # Get pricing
        unit_price = self._get_unit_price(usage_type)

        record = BillingRecord(
            id=generate_id("bil_"),
            enterprise_id=enterprise_id,
            api_key_id=api_key_id,
            usage_type=usage_type,
            quantity=quantity,
            unit_price=unit_price,
            amount=unit_price * quantity if unit_price else None,
            reference_id=reference_id,
            billing_period=datetime.utcnow().strftime("%Y-%m"),
        )

        db.add(record)
        await db.flush()

        return record

    def _get_unit_price(self, usage_type: str) -> float:
        """Get unit price for usage type."""
        prices = {
            "job_post": 0.5,
            "match_query": 0.1,
            "match_success": 1.0,
            "profile_view": 0.1,
        }
        return prices.get(usage_type, 0.0)

    async def get_billing_records(
        self,
        db: AsyncSession,
        enterprise_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        usage_type: Optional[str] = None,
        limit: int = 100,
    ) -> tuple[list[BillingRecord], float]:
        """Get billing records for an enterprise."""
        query = select(BillingRecord).where(
            BillingRecord.enterprise_id == enterprise_id
        )

        if start_date:
            query = query.where(BillingRecord.created_at >= start_date)
        if end_date:
            # Include the entire end date by adding one day
            end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
            query = query.where(BillingRecord.created_at < end_dt)
        if usage_type:
            query = query.where(BillingRecord.usage_type == usage_type)

        query = query.order_by(BillingRecord.created_at.desc()).limit(limit)

        result = await db.execute(query)
        records = result.scalars().all()

        total = sum(r.amount or 0 for r in records)

        return list(records), total


# Singleton instance
enterprise_service = EnterpriseService()
