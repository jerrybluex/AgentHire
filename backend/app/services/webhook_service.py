"""
Webhook Service
提供 Webhook 注册和事件通知功能
"""

import asyncio
import hashlib
import hmac
import json
from typing import Optional
from datetime import datetime

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Webhook, WebhookDelivery, generate_id


class WebhookService:
    """
    Webhook 管理服务
    - 注册/删除 Webhook URL
    - 发送事件通知
    - 签名验证
    """

    # 事件类型
    EVENT_JOB_NEW = "job.new"
    EVENT_PROFILE_NEW = "profile.new"
    EVENT_ENTERPRISE_APPROVED = "enterprise.approved"
    EVENT_ENTERPRISE_REJECTED = "enterprise.rejected"

    async def register_webhook(
        self,
        db: AsyncSession,
        enterprise_id: str,
        url: str,
        events: list[str],
        secret: Optional[str] = None,
    ) -> dict:
        """
        注册 Webhook

        Args:
            db: Database session
            enterprise_id: 企业ID
            url: Webhook URL
            events: 订阅的事件类型列表
            secret: 签名密钥

        Returns:
            Webhook 注册信息
        """
        # 生成密钥
        if not secret:
            import secrets
            secret = secrets.token_urlsafe(32)

        webhook = Webhook(
            id=generate_id("whk_"),
            enterprise_id=enterprise_id,
            url=url,
            events=events,
            secret=secret,
            active=True,
        )

        db.add(webhook)
        await db.flush()

        return {
            "id": webhook.id,
            "enterprise_id": webhook.enterprise_id,
            "url": webhook.url,
            "events": webhook.events,
            "secret": webhook.secret,
            "active": webhook.active,
            "created_at": webhook.created_at.isoformat() if webhook.created_at else None,
        }

    async def unregister_webhook(
        self,
        db: AsyncSession,
        enterprise_id: str,
        webhook_id: str,
    ) -> bool:
        """删除 Webhook"""
        result = await db.execute(
            select(Webhook).where(
                Webhook.id == webhook_id,
                Webhook.enterprise_id == enterprise_id,
            )
        )
        webhook = result.scalar_one_or_none()

        if not webhook:
            return False

        await db.delete(webhook)
        await db.flush()
        return True

    async def get_webhooks(
        self,
        db: AsyncSession,
        enterprise_id: str,
    ) -> list[dict]:
        """获取企业的所有 Webhook"""
        result = await db.execute(
            select(Webhook).where(Webhook.enterprise_id == enterprise_id)
        )
        webhooks = result.scalars().all()

        return [
            {
                "id": w.id,
                "enterprise_id": w.enterprise_id,
                "url": w.url,
                "events": w.events,
                "active": w.active,
                "success_count": w.success_count,
                "failure_count": w.failure_count,
                "last_triggered_at": w.last_triggered_at.isoformat() if w.last_triggered_at else None,
                "created_at": w.created_at.isoformat() if w.created_at else None,
            }
            for w in webhooks
        ]

    async def get_active_webhooks_for_event(
        self,
        db: AsyncSession,
        enterprise_id: str,
        event: str,
    ) -> list[Webhook]:
        """获取可以接收特定事件的所有活跃 Webhook"""
        result = await db.execute(
            select(Webhook).where(
                Webhook.enterprise_id == enterprise_id,
                Webhook.active == True,
            )
        )
        all_webhooks = result.scalars().all()

        # 过滤订阅了该事件的 webhook
        return [
            w for w in all_webhooks
            if event in w.events or "*" in w.events
        ]

    async def notify(
        self,
        db: AsyncSession,
        enterprise_id: str,
        event: str,
        data: dict,
    ) -> dict:
        """
        发送 Webhook 通知

        Args:
            db: Database session
            enterprise_id: 企业ID
            event: 事件类型
            data: 事件数据

        Returns:
            发送结果
        """
        webhooks = await self.get_active_webhooks_for_event(db, enterprise_id, event)

        if not webhooks:
            return {"sent": 0, "failed": 0, "results": []}

        results = []
        sent = 0
        failed = 0

        payload = self._build_payload(event, data)

        async with httpx.AsyncClient(timeout=10.0) as client:
            for webhook in webhooks:
                try:
                    signature = self._sign_payload(payload, webhook.secret)

                    response = await client.post(
                        webhook.url,
                        json=payload,
                        headers={
                            "Content-Type": "application/json",
                            "X-Webhook-Signature": f"sha256={signature}",
                            "X-Webhook-Event": event,
                            "X-Webhook-ID": webhook.id,
                        },
                    )

                    # 记录发送结果
                    delivery = WebhookDelivery(
                        id=generate_id("whd_"),
                        webhook_id=webhook.id,
                        event=event,
                        payload=payload,
                        status="sent" if response.status_code < 400 else "failed",
                        response_status=response.status_code,
                        response_body=response.text[:1000] if response.text else None,
                        sent_at=datetime.utcnow(),
                    )
                    db.add(delivery)

                    # 更新 webhook 统计
                    if response.status_code < 400:
                        webhook.success_count += 1
                        webhook.last_triggered_at = datetime.utcnow()
                        sent += 1
                        results.append({"webhook_id": webhook.id, "status": "sent"})
                    else:
                        webhook.failure_count += 1
                        failed += 1
                        results.append({
                            "webhook_id": webhook.id,
                            "status": "failed",
                            "error": f"HTTP {response.status_code}",
                        })

                except Exception as e:
                    # 记录失败
                    delivery = WebhookDelivery(
                        id=generate_id("whd_"),
                        webhook_id=webhook.id,
                        event=event,
                        payload=payload,
                        status="failed",
                        error_message=str(e),
                    )
                    db.add(delivery)

                    webhook.failure_count += 1
                    failed += 1
                    results.append({
                        "webhook_id": webhook.id,
                        "status": "failed",
                        "error": str(e),
                    })

        await db.flush()

        return {"sent": sent, "failed": failed, "results": results}

    def _build_payload(self, event: str, data: dict) -> dict:
        """构建 Webhook payload"""
        return {
            "event": event,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data,
        }

    def _sign_payload(self, payload: dict, secret: str) -> str:
        """对 payload 进行签名"""
        body = json.dumps(payload, sort_keys=True)
        return hmac.new(
            secret.encode(),
            body.encode(),
            hashlib.sha256
        ).hexdigest()

    def verify_signature(
        self,
        payload: bytes,
        signature: str,
        secret: str,
    ) -> bool:
        """验证 Webhook 签名"""
        # Validate payload structure before processing
        try:
            data = json.loads(payload)
            if "event" not in data or "timestamp" not in data:
                return False
        except json.JSONDecodeError:
            return False
        expected = self._sign_payload(json.loads(payload), secret)
        return hmac.compare_digest(f"sha256={expected}", signature)


# Singleton instance
webhook_service = WebhookService()