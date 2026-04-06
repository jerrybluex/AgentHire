"""
Webhook API endpoints
提供 Webhook 注册和管理功能
"""

from typing import Optional

from fastapi import APIRouter, Depends, Header, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.webhook_service import webhook_service

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


class WebhookRegisterRequest(BaseModel):
    """Webhook 注册请求"""

    url: str = Field(..., description="Webhook URL")
    events: list[str] = Field(..., description="订阅的事件类型")
    secret: Optional[str] = Field(None, description="签名密钥（可选，自动生成）")


class WebhookResponse(BaseModel):
    """Webhook 响应"""

    success: bool = True
    data: dict = Field(default_factory=dict)
    message: str | None = None


class WebhookListResponse(BaseModel):
    """Webhook 列表响应"""

    success: bool = True
    data: list = Field(default_factory=list)


@router.post(
    "",
    response_model=WebhookResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register webhook",
    description="Register a webhook URL to receive event notifications",
)
async def register_webhook(
    request: WebhookRegisterRequest,
    enterprise_id: str = Header(..., alias="X-Enterprise-ID"),
    db: AsyncSession = Depends(get_db),
) -> WebhookResponse:
    """
    注册 Webhook

    支持的事件类型:
    - job.new: 新职位发布
    - profile.new: 新求职者注册
    - enterprise.approved: 企业审核通过
    - enterprise.rejected: 企业审核拒绝
    - *: 订阅所有事件
    """
    webhook = await webhook_service.register_webhook(
        db=db,
        enterprise_id=enterprise_id,
        url=request.url,
        events=request.events,
        secret=request.secret,
    )

    return WebhookResponse(
        success=True,
        data={
            "webhook_id": webhook["id"],
            "url": webhook["url"],
            "events": webhook["events"],
            "secret": webhook["secret"],
            "created_at": webhook["created_at"],
        },
        message="Webhook registered successfully. Save the secret for signature verification.",
    )


@router.get(
    "",
    response_model=WebhookListResponse,
    status_code=status.HTTP_200_OK,
    summary="List webhooks",
    description="List all registered webhooks for an enterprise",
)
async def list_webhooks(
    enterprise_id: str = Header(..., alias="X-Enterprise-ID"),
    db: AsyncSession = Depends(get_db),
) -> WebhookListResponse:
    """获取企业的所有 Webhook"""
    webhooks = await webhook_service.get_webhooks(db, enterprise_id)

    return WebhookListResponse(
        success=True,
        data=webhooks,
    )


@router.delete(
    "/{webhook_id}",
    response_model=WebhookResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete webhook",
    description="Delete a registered webhook",
)
async def delete_webhook(
    webhook_id: str,
    enterprise_id: str = Header(..., alias="X-Enterprise-ID"),
    db: AsyncSession = Depends(get_db),
) -> WebhookResponse:
    """删除 Webhook"""
    deleted = await webhook_service.unregister_webhook(db, enterprise_id, webhook_id)

    if not deleted:
        return WebhookResponse(
            success=False,
            data={},
            message="Webhook not found",
        )

    return WebhookResponse(
        success=True,
        data={"webhook_id": webhook_id},
        message="Webhook deleted successfully",
    )


# Webhook 事件触发端点（内部使用，供其他服务调用）
async def trigger_webhook_event(
    db: AsyncSession,
    enterprise_id: str,
    event: str,
    data: dict,
):
    """
    触发 Webhook 事件（供内部服务调用）

    用法:
    from app.api.v1.webhook import trigger_webhook_event
    await trigger_webhook_event(db, "ent_xxx", "job.new", {"job_id": "job_yyy"})
    """
    return await webhook_service.notify(db, enterprise_id, event, data)