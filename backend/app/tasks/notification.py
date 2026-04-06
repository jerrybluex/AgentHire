"""
Notification Task
Webhook 通知服务
"""

import httpx
import logging
from datetime import datetime
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class WebhookService:
    """Webhook 通知服务"""

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=10.0)

    async def send_webhook(
        self,
        webhook_url: str,
        event_type: str,
        payload: Dict[str, Any],
    ) -> bool:
        """
        发送 Webhook 通知。

        Args:
            webhook_url: Webhook 地址
            event_type: 事件类型
            payload: 事件数据

        Returns:
            True 如果发送成功
        """
        try:
            response = await self.client.post(
                webhook_url,
                json={
                    "event": event_type,
                    "data": payload,
                    "timestamp": datetime.utcnow().isoformat(),
                },
                headers={
                    "Content-Type": "application/json",
                    "X-AgentHire-Event": event_type,
                },
            )
            response.raise_for_status()
            logger.info(f"Webhook sent: {event_type} to {webhook_url}")
            return True
        except Exception as e:
            logger.error(f"Webhook failed: {event_type} to {webhook_url}: {e}")
            return False

    async def notify_application_status_changed(
        self,
        webhook_url: str,
        application_id: str,
        old_status: str,
        new_status: str,
        actor_type: str,
    ):
        """通知申请状态变更"""
        return await self.send_webhook(
            webhook_url,
            event_type="application.status_changed",
            payload={
                "application_id": application_id,
                "old_status": old_status,
                "new_status": new_status,
                "actor_type": actor_type,
            },
        )

    async def notify_contact_unlocked(
        self,
        webhook_url: str,
        application_id: str,
        contact_type: str,
    ):
        """通知联系方式已解锁"""
        return await self.send_webhook(
            webhook_url,
            event_type="contact.unlocked",
            payload={
                "application_id": application_id,
                "contact_type": contact_type,
            },
        )

    async def notify_match_created(
        self,
        webhook_url: str,
        match_id: str,
        seeker_id: str,
        job_id: str,
        match_score: float,
    ):
        """通知新的匹配已创建"""
        return await self.send_webhook(
            webhook_url,
            event_type="match.created",
            payload={
                "match_id": match_id,
                "seeker_id": seeker_id,
                "job_id": job_id,
                "match_score": match_score,
            },
        )


# Singleton instance
webhook_service = WebhookService()
