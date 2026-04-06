"""
Enterprise (B2B) API endpoints.
Provides enterprise management, API keys, and billing.
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Header, Query, status, UploadFile, File, Request, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models import Enterprise, EnterpriseAPIKey, EnterpriseVerificationCase, generate_id
from app.services.enterprise_service import enterprise_service, verify_password, hash_password
from app.services.identity_service import identity_service
from app.services.enterprise_verification_service import enterprise_verification_service
from app.api.deps import get_current_user, CurrentUser

router = APIRouter()


class EnterpriseApplyRequest(BaseModel):
    """Enterprise application request."""

    company_name: str = Field(..., description="Company name")
    unified_social_credit_code: str = Field(..., description="Business license code")
    contact: dict = Field(..., description="Contact information")
    company_info: dict = Field(default_factory=dict, description="Additional company info")
    password: str = Field(..., description="Login password (min 6 characters)")
    certification: dict = Field(default_factory=dict, description="Certification documents with URLs")


class EnterpriseResponse(BaseModel):
    """Enterprise response wrapper."""

    success: bool = True
    data: dict = Field(default_factory=dict)
    message: str | None = None


class ApiKeyCreateRequest(BaseModel):
    """API key creation request."""

    name: str = Field(..., description="Key name (e.g., Production Key)")
    plan: str = Field(default="pay_as_you_go", description="Billing plan")
    rate_limit: int = Field(default=100, description="Requests per minute")
    monthly_quota: Optional[int] = Field(None, description="Monthly quota for subscription plans")


class BillingResponse(BaseModel):
    """Billing records response."""

    success: bool = True
    data: list = Field(default_factory=list)
    total: float = 0.0


class EnterpriseLoginRequest(BaseModel):
    """Enterprise login request."""

    email: str = Field(..., description="Contact email")
    password: Optional[str] = Field(None, description="Password")


class EnterpriseVerifyRequest(BaseModel):
    """Enterprise verification request."""

    enterprise_id: str = Field(..., description="Enterprise ID to verify")
    action: str = Field(..., description="Action: approve or reject")
    reason: Optional[str] = Field(None, description="Reason for rejection")


class EnterpriseListResponse(BaseModel):
    """Enterprise list response."""

    success: bool = True
    data: list = Field(default_factory=list)
    total: int = 0


async def get_enterprise_from_header(
    x_enterprise_id: str = Header(..., description="Enterprise ID"),
    db: AsyncSession = Depends(get_db),
) -> tuple[str, AsyncSession]:
    """Get enterprise ID from header."""
    return x_enterprise_id, db


async def get_current_admin(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Administrator authentication (temporary implementation).
    Validates that the X-Admin-Token header matches the ADMIN_TOKEN environment variable.
    """
    import os
    admin_token = request.headers.get("X-Admin-Token")
    expected_token = os.environ.get("ADMIN_TOKEN", "dev-admin-token")

    if not admin_token or admin_token != expected_token:
        raise HTTPException(status_code=403, detail="Admin access required")

    return {"role": "admin", "token": admin_token}


@router.post(
    "/register",
    response_model=EnterpriseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register enterprise (PRD v2)",
    description="Register enterprise with Identity Service integration",
)
async def register_enterprise(
    request: EnterpriseApplyRequest,
    db: AsyncSession = Depends(get_db),
) -> EnterpriseResponse:
    """
    Register enterprise with full PRD v2 integration:
    1. Create tenant via identity_service
    2. Create principal via identity_service
    3. Create API Key credential via identity_service
    4. Create Enterprise record with tenant_id
    5. Create verification case via enterprise_verification_service
    """
    try:
        # Step 1: Create tenant
        tenant = await identity_service.create_tenant(
            db=db,
            name=request.company_name,
            tenant_type="enterprise",
        )

        # Step 2: Create principal (enterprise admin)
        contact_email = request.contact.get("email", "") if isinstance(request.contact, dict) else ""
        principal = await identity_service.create_principal(
            db=db,
            tenant_id=tenant.id,
            principal_type="human",
            name=request.company_name,
            email=contact_email,
        )

        # Step 3: Create API Key credential via identity_service
        credential, api_key_plain = await identity_service.create_api_key_credential(
            db=db,
            principal_id=principal.id,
            name=f"{request.company_name} API Key",
        )

        # Step 4: Create Enterprise record with tenant_id linkage
        enterprise = Enterprise(
            id=generate_id("ent_"),
            name=request.company_name,
            unified_social_credit_code=request.unified_social_credit_code,
            certification=request.certification,
            contact=request.contact,
            tenant_id=tenant.id,  # PRD v2 linkage
            website=request.company_info.get("website") if isinstance(request.company_info, dict) else None,
            industry=request.company_info.get("industry") if isinstance(request.company_info, dict) else None,
            company_size=request.company_info.get("company_size") if isinstance(request.company_info, dict) else None,
            description=request.company_info.get("description") if isinstance(request.company_info, dict) else None,
            status="pending",
            password_hash=hash_password(request.password) if request.password else None,
        )
        db.add(enterprise)
        await db.flush()

        # Step 5: Create verification case (initial status: draft)
        verification_case = await enterprise_verification_service.create_verification_case(
            db=db,
            enterprise_id=enterprise.id,
            submitted_by=principal.id,
        )

        # Return response with API key (shown only once!)
        return EnterpriseResponse(
            success=True,
            data={
                "enterprise_id": enterprise.id,
                "tenant_id": tenant.id,
                "principal_id": principal.id,
                "api_key": api_key_plain,
                "api_key_id": credential.id,
                "verification_case_id": verification_case.id,
                "status": enterprise.status,
                "message": "Save the API key. It will not be shown again.",
            },
            message="Enterprise registered. Verification case created. Awaiting approval.",
        )
    except Exception as e:
        return EnterpriseResponse(
            success=False,
            data={},
            message=f"Registration failed: {str(e)}",
        )


@router.post(
    "/apply",
    response_model=EnterpriseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Apply for enterprise account (legacy)",
    description="Submit enterprise verification application",
)
async def apply_enterprise(
    request: EnterpriseApplyRequest,
    db: AsyncSession = Depends(get_db),
) -> EnterpriseResponse:
    """Apply for enterprise verification (pending approval) - legacy endpoint."""
    try:
        enterprise = await enterprise_service.create_application(
            db=db,
            company_name=request.company_name,
            unified_social_credit_code=request.unified_social_credit_code,
            contact=request.contact,
            certification=request.certification,
            company_info=request.company_info,
            password=request.password,
        )

        return EnterpriseResponse(
            success=True,
            data={
                "enterprise_id": enterprise.id,
                "status": enterprise.status,
            },
            message="Application submitted. Awaiting approval.",
        )
    except Exception as e:
        return EnterpriseResponse(
            success=False,
            data={},
            message=f"Application failed: {str(e)}",
        )


@router.post(
    "/api-keys",
    response_model=EnterpriseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create API key",
    description="Create a new API key for enterprise access",
)
async def create_api_key(
    request: ApiKeyCreateRequest,
    db: AsyncSession = Depends(get_db),
    enterprise_id: str = Header(..., alias="X-Enterprise-ID"),
) -> EnterpriseResponse:
    """Create a new API key for an approved enterprise."""
    result = await enterprise_service.create_api_key(
        db=db,
        enterprise_id=enterprise_id,
        name=request.name,
        plan=request.plan,
        rate_limit=request.rate_limit,
        monthly_quota=request.monthly_quota,
    )

    if not result:
        return EnterpriseResponse(
            success=False,
            data={},
            message="Enterprise not found or not approved",
        )

    return EnterpriseResponse(
        success=True,
        data={
            "api_key": result["api_key"],  # Only shown once!
            "api_key_prefix": result["api_key_prefix"],
            "name": result["name"],
            "plan": result["plan"],
            "message": "Save this API key. It will not be shown again.",
        },
        message="API key created successfully",
    )


@router.get(
    "/billing",
    response_model=BillingResponse,
    status_code=status.HTTP_200_OK,
    summary="Get billing info",
    description="Get enterprise billing information",
)
async def get_billing(
    enterprise_id: str = Header(..., alias="X-Enterprise-ID"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    limit: int = Query(100, ge=1, le=500, description="Number of records"),
    db: AsyncSession = Depends(get_db),
) -> BillingResponse:
    """Get billing records for an enterprise."""
    records, total = await enterprise_service.get_billing_records(
        db=db,
        enterprise_id=enterprise_id,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
    )

    return BillingResponse(
        success=True,
        data=[
            {
                "id": r.id,
                "usage_type": r.usage_type,
                "quantity": r.quantity,
                "amount": r.amount,
                "billing_period": r.billing_period,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in records
        ],
        total=total,
    )


@router.post(
    "/login",
    response_model=EnterpriseResponse,
    status_code=status.HTTP_200_OK,
    summary="Enterprise login",
    description="Login with email",
)
async def enterprise_login(
    request: EnterpriseLoginRequest,
    db: AsyncSession = Depends(get_db),
) -> EnterpriseResponse:
    """Login with email (simplified)."""
    enterprise = await enterprise_service.get_enterprise_by_email(db, request.email)

    if not enterprise:
        return EnterpriseResponse(
            success=False,
            data={},
            message="该邮箱未注册企业账户",
        )

    # Check if approved
    if enterprise.status != "approved":
        return EnterpriseResponse(
            success=False,
            data={"status": enterprise.status},
            message=f"企业状态：{enterprise.status}，等待审核",
        )

    # Verify password
    if enterprise.password_hash:
        if not request.password:
            return EnterpriseResponse(
                success=False,
                data={},
                message="请输入密码",
            )
        if not verify_password(request.password, enterprise.password_hash):
            return EnterpriseResponse(
                success=False,
                data={},
                message="密码错误",
            )

    # Get API keys
    result = await db.execute(
        select(EnterpriseAPIKey).where(
            EnterpriseAPIKey.enterprise_id == enterprise.id,
            EnterpriseAPIKey.status == "active",
        )
    )
    api_keys = result.scalars().all()

    return EnterpriseResponse(
        success=True,
        data={
            "enterprise_id": enterprise.id,
            "company_name": enterprise.name,
            "status": enterprise.status,
            "api_keys": [
                {
                    "id": k.id,
                    "name": k.name,
                    "api_key_prefix": k.api_key_prefix,
                    "plan": k.plan,
                }
                for k in api_keys
            ],
        },
        message="登录成功",
    )


@router.get(
    "",
    response_model=EnterpriseListResponse,
    status_code=status.HTTP_200_OK,
    summary="List enterprises",
    description="List all enterprises (admin only)",
)
async def list_enterprises(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
) -> EnterpriseListResponse:
    """List all enterprises (for admin dashboard)."""
    offset = (page - 1) * page_size

    query = select(Enterprise)
    if status_filter:
        query = query.where(Enterprise.status == status_filter)

    from sqlalchemy import func
    # Count query - use a separate select instead of subquery
    count_query = select(func.count()).select_from(Enterprise)
    if status_filter:
        count_query = count_query.where(Enterprise.status == status_filter)
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    query = query.offset(offset).limit(page_size)
    result = await db.execute(query)
    enterprises = result.scalars().all()

    return EnterpriseListResponse(
        success=True,
        data=[
            {
                "id": e.id,
                "name": e.name,
                "unified_social_credit_code": e.unified_social_credit_code,
                "contact": e.contact,
                "status": e.status,
                "certification": e.certification,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            }
            for e in enterprises
        ],
        total=total,
    )


@router.post(
    "/upload",
    response_model=EnterpriseResponse,
    status_code=status.HTTP_200_OK,
    summary="Upload enterprise file",
    description="Upload business license or other certification files",
)
async def upload_enterprise_file(
    file: UploadFile = File(..., description="File to upload"),
) -> EnterpriseResponse:
    """Upload a file for enterprise certification."""
    try:
        import uuid
        from pathlib import Path

        # Create upload directory
        upload_dir = Path("./uploads/enterprise")
        upload_dir.mkdir(parents=True, exist_ok=True)

        # Generate unique filename
        file_ext = Path(file.filename).suffix
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        file_path = upload_dir / unique_filename

        # Save file
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)

        # Generate URL (in production, this would be a CDN URL)
        file_url = f"/uploads/enterprise/{unique_filename}"

        return EnterpriseResponse(
            success=True,
            data={
                "url": file_url,
                "filename": file.filename,
                "size": len(content),
            },
            message="File uploaded successfully",
        )
    except Exception as e:
        return EnterpriseResponse(
            success=False,
            data={},
            message=f"Upload failed: {str(e)}",
        )


@router.post(
    "/verify",
    response_model=EnterpriseResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify enterprise",
    description="Approve or reject an enterprise application (admin only)",
)
async def verify_enterprise(
    request: EnterpriseVerifyRequest,
    db: AsyncSession = Depends(get_db),
) -> EnterpriseResponse:
    """Approve or reject an enterprise application."""
    enterprise = await enterprise_service.get_enterprise(db, request.enterprise_id)

    if not enterprise:
        return EnterpriseResponse(
            success=False,
            data={},
            message="Enterprise not found",
        )

    if request.action == "approve":
        approved = await enterprise_service.approve_enterprise(
            db=db,
            enterprise_id=request.enterprise_id,
            approved_by="admin",
        )
        return EnterpriseResponse(
            success=True,
            data={
                "enterprise_id": approved.id,
                "status": approved.status,
            },
            message="Enterprise approved successfully",
        )
    elif request.action == "reject":
        enterprise.status = "rejected"
        enterprise.certification = enterprise.certification or {}
        enterprise.certification["rejected_at"] = datetime.utcnow().isoformat()
        enterprise.certification["rejection_reason"] = request.reason
        await db.flush()

        return EnterpriseResponse(
            success=True,
            data={
                "enterprise_id": enterprise.id,
                "status": enterprise.status,
            },
            message="Enterprise rejected",
        )
    else:
        return EnterpriseResponse(
            success=False,
            data={},
            message="Invalid action. Use 'approve' or 'reject'",
        )


async def _get_verification_case_by_enterprise(
    db: AsyncSession,
    enterprise_id: str,
) -> Optional[EnterpriseVerificationCase]:
    """Helper: Get the latest verification case for an enterprise."""
    from sqlalchemy import select, desc
    result = await db.execute(
        select(EnterpriseVerificationCase)
        .where(EnterpriseVerificationCase.enterprise_id == enterprise_id)
        .order_by(desc(EnterpriseVerificationCase.created_at))
        .limit(1)
    )
    return result.scalar_one_or_none()


@router.post(
    "/{enterprise_id}/verification/submit",
    response_model=EnterpriseResponse,
    status_code=status.HTTP_200_OK,
    summary="Submit enterprise for verification review",
    description="Submit a draft verification case for review (admin only)",
)
async def submit_enterprise_verification(
    enterprise_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_admin),
) -> EnterpriseResponse:
    """Submit enterprise verification case for review."""
    case = await _get_verification_case_by_enterprise(db, enterprise_id)
    if not case:
        return EnterpriseResponse(
            success=False,
            data={},
            message="Verification case not found for this enterprise",
        )
    try:
        updated_case = await enterprise_verification_service.submit_for_review(db, case.id)
        return EnterpriseResponse(
            success=True,
            data={
                "verification_case_id": updated_case.id,
                "status": updated_case.status,
            },
            message="Verification case submitted for review",
        )
    except Exception as e:
        return EnterpriseResponse(
            success=False,
            data={},
            message=f"Submit failed: {str(e)}",
        )


@router.post(
    "/{enterprise_id}/verification/approve",
    response_model=EnterpriseResponse,
    status_code=status.HTTP_200_OK,
    summary="Approve enterprise verification",
    description="Approve an enterprise verification case (admin only)",
)
async def approve_enterprise_verification(
    enterprise_id: str,
    comment: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_admin),
) -> EnterpriseResponse:
    """Approve enterprise verification case."""
    case = await _get_verification_case_by_enterprise(db, enterprise_id)
    if not case:
        return EnterpriseResponse(
            success=False,
            data={},
            message="Verification case not found for this enterprise",
        )
    try:
        updated_case = await enterprise_verification_service.approve(
            db, case.id, current_user["token"], comment
        )
        # Also update enterprise status
        enterprise = await enterprise_service.get_enterprise(db, enterprise_id)
        if enterprise:
            enterprise.status = "approved"
            enterprise.certification = enterprise.certification or {}
            enterprise.certification["verified_at"] = datetime.utcnow().isoformat()
            enterprise.certification["verified_by"] = current_user["token"]
            await db.flush()
        return EnterpriseResponse(
            success=True,
            data={
                "verification_case_id": updated_case.id,
                "status": updated_case.status,
                "enterprise_id": enterprise_id,
            },
            message="Enterprise verification approved",
        )
    except Exception as e:
        return EnterpriseResponse(
            success=False,
            data={},
            message=f"Approval failed: {str(e)}",
        )


@router.post(
    "/{enterprise_id}/verification/reject",
    response_model=EnterpriseResponse,
    status_code=status.HTTP_200_OK,
    summary="Reject enterprise verification",
    description="Reject an enterprise verification case (admin only)",
)
async def reject_enterprise_verification(
    enterprise_id: str,
    reason: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_admin),
) -> EnterpriseResponse:
    """Reject enterprise verification case."""
    case = await _get_verification_case_by_enterprise(db, enterprise_id)
    if not case:
        return EnterpriseResponse(
            success=False,
            data={},
            message="Verification case not found for this enterprise",
        )
    try:
        updated_case = await enterprise_verification_service.reject(
            db, case.id, current_user["token"], reason
        )
        # Also update enterprise status
        enterprise = await enterprise_service.get_enterprise(db, enterprise_id)
        if enterprise:
            enterprise.status = "rejected"
            enterprise.certification = enterprise.certification or {}
            enterprise.certification["rejected_at"] = datetime.utcnow().isoformat()
            enterprise.certification["rejection_reason"] = reason
            await db.flush()
        return EnterpriseResponse(
            success=True,
            data={
                "verification_case_id": updated_case.id,
                "status": updated_case.status,
                "enterprise_id": enterprise_id,
            },
            message="Enterprise verification rejected",
        )
    except Exception as e:
        return EnterpriseResponse(
            success=False,
            data={},
            message=f"Rejection failed: {str(e)}",
        )


@router.get(
    "/me",
    response_model=EnterpriseResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current enterprise",
    description="Get enterprise info by ID",
)
async def get_current_enterprise(
    enterprise_id: str = Header(..., alias="X-Enterprise-ID"),
    db: AsyncSession = Depends(get_db),
) -> EnterpriseResponse:
    """Get enterprise info."""
    enterprise = await enterprise_service.get_enterprise(db, enterprise_id)

    if not enterprise:
        return EnterpriseResponse(
            success=False,
            data={},
            message="Enterprise not found",
        )

    # Get API keys
    result = await db.execute(
        select(EnterpriseAPIKey).where(
            EnterpriseAPIKey.enterprise_id == enterprise.id,
            EnterpriseAPIKey.status == "active",
        )
    )
    api_keys = result.scalars().all()

    return EnterpriseResponse(
        success=True,
        data={
            "enterprise_id": enterprise.id,
            "company_name": enterprise.name,
            "status": enterprise.status,
            "contact": enterprise.contact,
            "api_keys": [
                {
                    "id": k.id,
                    "name": k.name,
                    "api_key_prefix": k.api_key_prefix,
                    "plan": k.plan,
                }
                for k in api_keys
            ],
        },
    )
