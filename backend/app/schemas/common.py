"""
AgentHire Common Schemas
通用Pydantic模型定义
"""

from datetime import datetime
from typing import Optional, Generic, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """统一API响应格式"""
    success: bool = True
    data: Optional[T] = None
    message: Optional[str] = None
    error: Optional[dict] = None

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "data": {"id": "prof_abc123"},
                "message": None,
                "error": None
            }
        }


class PaginatedResponse(BaseModel, Generic[T]):
    """分页响应格式"""
    items: list[T]
    total: int
    page: int
    page_size: int
    has_next: bool


class ErrorDetail(BaseModel):
    """错误详情"""
    code: str
    message: str
    field: Optional[str] = None


class TimestampMixin(BaseModel):
    """时间戳混入"""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str = "healthy"
    version: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    services: Optional[dict] = None
