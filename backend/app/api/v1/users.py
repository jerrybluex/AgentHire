"""
Users API
用户 API - 用户注册、登录、信息查询
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.user_service import user_service


router = APIRouter()


# Request/Response Schemas
class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: str
    nickname: Optional[str] = None


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: str
    email: str
    nickname: Optional[str]
    status: str
    created_at: str


class UserLoginResponse(BaseModel):
    success: bool
    data: Optional[dict] = None
    message: Optional[str] = None


@router.post(
    "/register",
    summary="注册用户",
    description="注册一个新用户账户",
    response_model=dict,
)
async def register_user(
    request: UserRegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Register a new user.

    - **email**: User email (must be unique)
    - **password**: User password (min 6 characters)
    - **nickname**: Optional nickname
    """
    # Validate password length
    if len(request.password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 6 characters",
        )

    user = await user_service.create_user(
        db=db,
        email=request.email,
        password=request.password,
        nickname=request.nickname,
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    return {
        "success": True,
        "data": {
            "user_id": user.id,
            "email": user.email,
            "nickname": user.nickname,
        },
    }


@router.post(
    "/login",
    summary="用户登录",
    description="使用邮箱和密码登录",
    response_model=UserLoginResponse,
)
async def login_user(
    request: UserLoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Login with email and password.

    - **email**: User email
    - **password**: User password
    """
    user = await user_service.authenticate(
        db=db,
        email=request.email,
        password=request.password,
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    return {
        "success": True,
        "data": {
            "user_id": user.id,
            "email": user.email,
            "nickname": user.nickname,
        },
    }


@router.get(
    "/me",
    summary="获取当前用户信息",
    description="获取已登录用户的信息",
    response_model=dict,
)
async def get_current_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Get current user information.

    - **user_id**: User ID from session/auth
    """
    user = await user_service.get_user(db, user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return {
        "success": True,
        "data": {
            "id": user.id,
            "email": user.email,
            "nickname": user.nickname,
            "status": user.status,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        },
    }
