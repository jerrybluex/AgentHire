"""
Agent API endpoints.
Handles agent registration and authentication.
"""

from typing import Optional

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field

from app.services.agent_service import agent_service
from app.api.deps import verify_agent_signature

router = APIRouter()


# =============================================================================
# Request/Response Models
# =============================================================================


class RegisterRequest(BaseModel):
    """Agent registration request."""

    name: str = Field(..., description="Agent name")
    type: str = Field(..., description="Agent type: seeker or employer")
    platform: Optional[str] = Field(None, description="Source platform")
    contact: Optional[dict] = Field(None, description="Contact information")


class RegisterResponse(BaseModel):
    """Agent registration response."""

    success: bool = True
    data: Optional[dict] = None
    message: Optional[str] = None


class AuthenticateRequest(BaseModel):
    """Agent authentication request."""

    agent_id: str = Field(..., description="Agent ID")
    signature: str = Field(..., description="HMAC signature")
    timestamp: int = Field(..., description="Request timestamp")


class AuthenticateResponse(BaseModel):
    """Agent authentication response."""

    success: bool = True
    data: Optional[dict] = None
    message: Optional[str] = None


class AgentInfoResponse(BaseModel):
    """Agent information response."""

    success: bool = True
    data: Optional[dict] = None
    message: Optional[str] = None


# =============================================================================
# Endpoints
# =============================================================================


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_200_OK,
    summary="Register a new agent",
    description="Register a new agent (seeker or employer) and get credentials",
)
async def register_agent(request: RegisterRequest) -> RegisterResponse:
    """
    Register a new agent.

    - **name**: Agent name
    - **type**: 'seeker' or 'employer'
    - **platform**: Source platform (e.g., 'openclaw')
    - **contact**: Optional contact information
    """
    if request.type not in ["seeker", "employer"]:
        return RegisterResponse(
            success=False,
            data=None,
            message="type must be 'seeker' or 'employer'",
        )

    from app.core.database import get_db_context

    async with get_db_context() as db:
        try:
            result = await agent_service.register(
                db=db,
                name=request.name,
                agent_type=request.type,
                platform=request.platform,
                contact=request.contact,
            )

            return RegisterResponse(
                success=True,
                data=result,
                message="Agent registered successfully",
            )
        except Exception as e:
            await db.rollback()
            return RegisterResponse(
                success=False,
                data=None,
                message=f"Registration failed: {str(e)}",
            )


@router.post(
    "/authenticate",
    response_model=AuthenticateResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate an agent",
    description="Verify agent signature and timestamp",
)
async def authenticate_agent(request: AuthenticateRequest) -> AuthenticateResponse:
    """
    Authenticate an agent request.

    The signature is calculated as:
    HMAC-SHA256(agent_secret, agent_id + timestamp)
    """
    from app.core.database import get_db_context

    async with get_db_context() as db:
        authenticated_agent_id = await agent_service.authenticate(
            db=db,
            agent_id=request.agent_id,
            timestamp=request.timestamp,
            signature=request.signature,
        )

        if authenticated_agent_id:
            return AuthenticateResponse(
                success=True,
                data={"agent_id": authenticated_agent_id, "authenticated": True},
                message="Authentication successful",
            )
        else:
            return AuthenticateResponse(
                success=False,
                data=None,
                message="Authentication failed. Check agent_id, timestamp, and signature.",
            )


@router.get(
    "/me",
    response_model=AgentInfoResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current agent info",
    description="Get information about the authenticated agent",
)
async def get_agent_info(
    agent_id: str = Depends(verify_agent_signature),
) -> AgentInfoResponse:
    """
    Get current agent information.

    Requires valid authentication headers:
    - X-Agent-ID
    - X-Timestamp
    - X-Signature
    """
    from app.core.database import get_db_context

    async with get_db_context() as db:
        agent_info = await agent_service.get_agent(db, agent_id)

        if agent_info:
            return AgentInfoResponse(
                success=True,
                data=agent_info,
                message="Agent info retrieved",
            )
        else:
            return AgentInfoResponse(
                success=False,
                data=None,
                message="Agent not found",
            )