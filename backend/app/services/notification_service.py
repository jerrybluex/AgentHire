"""
Notification Service
Handles email notifications for various events including:
- Enterprise audit results (approved/rejected)
- Billing notifications (low balance, spending thresholds)
"""

import logging
import os
from datetime import datetime
from typing import Optional
from enum import Enum

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Enterprise, BillingRecord, EnterpriseAPIKey, generate_id

logger = logging.getLogger(__name__)


class NotificationType(str, Enum):
    """Notification type constants."""
    ENTERPRISE_APPROVED = "enterprise_approved"
    ENTERPRISE_REJECTED = "enterprise_rejected"
    LOW_BALANCE = "low_balance"
    SPENDING_THRESHOLD = "spending_threshold"
    SPENDING_ALERT = "spending_alert"


class EmailTemplate:
    """Email templates for notifications."""

    ENTERPRISE_APPROVED = """
    <html>
    <body>
    <h2>企业认证审核结果</h2>
    <p>您好，{company_name}，</p>
    <p>恭喜！您的企业入驻申请已通过审核。</p>
    <p><strong>企业名称：</strong>{company_name}</p>
    <p><strong>审核时间：</strong>{verified_at}</p>
    <p><strong>审核人：</strong>{verified_by}</p>
    <hr>
    <p>您现在可以：</p>
    <ul>
        <li>创建 API Key 开始使用服务</li>
        <li>发布职位信息</li>
        <li>使用人才发现功能</li>
    </ul>
    <p>如有疑问，请联系客服。</p>
    <hr>
    <p><small>此邮件由 AgentHire 系统自动发送，请勿回复。</small></p>
    </body>
    </html>
    """

    ENTERPRISE_REJECTED = """
    <html>
    <body>
    <h2>企业认证审核结果</h2>
    <p>您好，{company_name}，</p>
    <p>很抱歉，您的企业入驻申请未通过审核。</p>
    <p><strong>企业名称：</strong>{company_name}</p>
    <p><strong>审核时间：</strong>{verified_at}</p>
    <p><strong>拒绝原因：</strong>{rejection_reason}</p>
    <hr>
    <p>您可以：</p>
    <ul>
        <li>修改企业信息后重新提交申请</li>
        <li>联系客服了解更多详情</li>
    </ul>
    <hr>
    <p><small>此邮件由 AgentHire 系统自动发送，请勿回复。</small></p>
    </body>
    </html>
    """

    LOW_BALANCE = """
    <html>
    <body>
    <h2>账户余额不足提醒</h2>
    <p>您好，{company_name}，</p>
    <p>您的账户余额已低于安全阈值，请及时充值以避免影响服务使用。</p>
    <p><strong>当前余额：</strong>¥{current_balance:.2f}</p>
    <p><strong>安全阈值：</strong>¥{threshold:.2f}</p>
    <hr>
    <p>请登录 AgentHire 企业后台进行充值。</p>
    <hr>
    <p><small>此邮件由 AgentHire 系统自动发送，请勿回复。</small></p>
    </body>
    </html>
    """

    SPENDING_THRESHOLD = """
    <html>
    <body>
    <h2>消费达到预警阈值</h2>
    <p>您好，{company_name}，</p>
    <p>您的账户消费已达到预警阈值。</p>
    <p><strong>当前消费总额：</strong>¥{total_spent:.2f}</p>
    <p><strong>预警阈值：</strong>¥{threshold:.2f}</p>
    <p><strong>当前周期：</strong>{billing_period}</p>
    <hr>
    <p>如需调整预警阈值或查看详细账单，请登录 AgentHire 企业后台。</p>
    <hr>
    <p><small>此邮件由 AgentHire 系统自动发送，请勿回复。</small></p>
    </body>
    </html>
    """


class NotificationService:
    """Service for sending notifications."""

    def __init__(self):
        """Initialize notification service."""
        self._email_enabled = os.getenv("EMAIL_ENABLED", "true").lower() == "true"
        self._email_backend = os.getenv("EMAIL_BACKEND", "smtp")  # smtp, console
        self._default_balance_threshold = 100.0  # RMB
        self._default_spending_threshold = 1000.0  # RMB

    async def _send_email_resend(
        self,
        to_email: str,
        subject: str,
        html_content: str,
    ) -> dict:
        """Send email via Resend API."""
        try:
            import httpx

            # Resend configuration from environment
            resend_api_key = os.getenv("RESEND_API_KEY", "")
            from_email = os.getenv("FROM_EMAIL", "onboarding@resend.dev")

            if not resend_api_key:
                logger.error("Resend API key not configured")
                return {
                    "status": "failed",
                    "to": to_email,
                    "error": "Resend API key not configured",
                }

            # Call Resend API
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.resend.com/emails",
                    headers={
                        "Authorization": f"Bearer {resend_api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "from": from_email,
                        "to": [to_email],
                        "subject": subject,
                        "html": html_content,
                    },
                    timeout=30.0,
                )

                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"Email sent successfully to {to_email}: {subject}")
                    return {
                        "status": "sent",
                        "to": to_email,
                        "subject": subject,
                        "message_id": result.get("id", generate_id("em_")),
                        "backend": "resend",
                    }
                else:
                    error_msg = response.text
                    logger.error(f"Resend API error: {error_msg}")
                    return {
                        "status": "failed",
                        "to": to_email,
                        "error": f"Resend API error: {error_msg}",
                    }

        except Exception as exc:
            logger.error(f"Failed to send email via Resend to {to_email}: {exc}")
            return {
                "status": "failed",
                "to": to_email,
                "error": str(exc),
            }

    async def _send_email_smtp(
        self,
        to_email: str,
        subject: str,
        html_content: str,
    ) -> dict:
        """Send email via SMTP (Gmail, etc.)."""
        try:
            import aiosmtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart

            # SMTP configuration from environment
            smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
            smtp_port = int(os.getenv("SMTP_PORT", "587"))
            smtp_user = os.getenv("SMTP_USER", "")
            smtp_password = os.getenv("SMTP_PASSWORD", "")
            from_email = os.getenv("FROM_EMAIL", smtp_user)

            if not smtp_user or not smtp_password:
                logger.error("SMTP credentials not configured")
                return {
                    "status": "failed",
                    "to": to_email,
                    "error": "SMTP credentials not configured",
                }

            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = from_email
            message["To"] = to_email

            # Attach HTML content
            html_part = MIMEText(html_content, "html", "utf-8")
            message.attach(html_part)

            # Send email
            await aiosmtplib.send(
                message,
                hostname=smtp_host,
                port=smtp_port,
                start_tls=True,
                username=smtp_user,
                password=smtp_password,
            )

            logger.info(f"Email sent successfully to {to_email}: {subject}")
            return {
                "status": "sent",
                "to": to_email,
                "subject": subject,
                "message_id": generate_id("em_"),
                "backend": "smtp",
            }

        except Exception as exc:
            logger.error(f"Failed to send email via SMTP to {to_email}: {exc}")
            return {
                "status": "failed",
                "to": to_email,
                "error": str(exc),
            }

    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
    ) -> dict:
        """
        Send an email notification.

        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: Email content in HTML format

        Returns:
            Dict with sending result
        """
        if not self._email_enabled:
            logger.info(f"Email disabled, would send to {to_email}: {subject}")
            return {
                "status": "skipped",
                "reason": "email_disabled",
                "to": to_email,
                "subject": subject,
            }

        # Use Resend backend (recommended, no domain needed)
        if self._email_backend == "resend":
            return await self._send_email_resend(to_email, subject, html_content)

        # Use SMTP backend
        if self._email_backend == "smtp":
            return await self._send_email_smtp(to_email, subject, html_content)

        # Console backend (for testing)
        logger.info(f"[CONSOLE EMAIL] To: {to_email}, Subject: {subject}")
        logger.debug(f"Content: {html_content[:200]}...")
        return {
            "status": "sent",
            "to": to_email,
            "subject": subject,
            "message_id": generate_id("em_"),
            "backend": "console",
        }

    async def notify_enterprise_approved(
        self,
        db: AsyncSession,
        enterprise: Enterprise,
        verified_by: str,
    ) -> dict:
        """
        Send notification when enterprise is approved.

        Args:
            db: Database session
            enterprise: Approved enterprise instance
            verified_by: Admin who approved the application

        Returns:
            Notification result
        """
        contact_email = enterprise.contact.get("email") if enterprise.contact else None

        if not contact_email:
            logger.warning(f"No email for enterprise {enterprise.id}")
            return {
                "status": "failed",
                "reason": "no_email",
                "enterprise_id": enterprise.id,
            }

        verified_at = (
            enterprise.certification.get("verified_at")
            if enterprise.certification
            else datetime.utcnow().isoformat()
        )

        html_content = EmailTemplate.ENTERPRISE_APPROVED.format(
            company_name=enterprise.name,
            verified_at=verified_at,
            verified_by=verified_by,
        )

        subject = f"【AgentHire】企业认证审核通过 - {enterprise.name}"

        return await self.send_email(
            to_email=contact_email,
            subject=subject,
            html_content=html_content,
        )

    async def notify_enterprise_rejected(
        self,
        db: AsyncSession,
        enterprise: Enterprise,
        rejection_reason: str,
    ) -> dict:
        """
        Send notification when enterprise is rejected.

        Args:
            db: Database session
            enterprise: Rejected enterprise instance
            rejection_reason: Reason for rejection

        Returns:
            Notification result
        """
        contact_email = enterprise.contact.get("email") if enterprise.contact else None

        if not contact_email:
            logger.warning(f"No email for enterprise {enterprise.id}")
            return {
                "status": "failed",
                "reason": "no_email",
                "enterprise_id": enterprise.id,
            }

        html_content = EmailTemplate.ENTERPRISE_REJECTED.format(
            company_name=enterprise.name,
            verified_at=datetime.utcnow().isoformat(),
            rejection_reason=rejection_reason,
        )

        subject = f"【AgentHire】企业认证审核结果 - {enterprise.name}"

        return await self.send_email(
            to_email=contact_email,
            subject=subject,
            html_content=html_content,
        )

    async def check_and_notify_low_balance(
        self,
        db: AsyncSession,
        enterprise_id: str,
        threshold: Optional[float] = None,
    ) -> dict:
        """
        Check enterprise balance and send low balance notification if needed.

        Args:
            db: Database session
            enterprise_id: Enterprise ID
            threshold: Balance threshold (uses default if not provided)

        Returns:
            Dict with check result and notification status
        """
        threshold = threshold or self._default_balance_threshold

        # Get enterprise
        result = await db.execute(
            select(Enterprise).where(Enterprise.id == enterprise_id)
        )
        enterprise = result.scalar_one_or_none()

        if not enterprise:
            return {
                "status": "failed",
                "reason": "enterprise_not_found",
                "enterprise_id": enterprise_id,
            }

        # Calculate current balance from billing_info or use default
        billing_info = enterprise.billing_info or {}
        current_balance = billing_info.get("balance", 1000.0)  # Default virtual balance

        if current_balance >= threshold:
            return {
                "status": "ok",
                "balance": current_balance,
                "threshold": threshold,
                "notification_sent": False,
            }

        # Send low balance notification
        contact_email = enterprise.contact.get("email") if enterprise.contact else None

        if not contact_email:
            return {
                "status": "failed",
                "reason": "no_email",
                "enterprise_id": enterprise_id,
            }

        html_content = EmailTemplate.LOW_BALANCE.format(
            company_name=enterprise.name,
            current_balance=current_balance,
            threshold=threshold,
        )

        subject = f"【AgentHire】账户余额不足提醒 - {enterprise.name}"

        email_result = await self.send_email(
            to_email=contact_email,
            subject=subject,
            html_content=html_content,
        )

        return {
            "status": "notification_sent",
            "balance": current_balance,
            "threshold": threshold,
            "email_result": email_result,
        }

    async def check_and_notify_spending_threshold(
        self,
        db: AsyncSession,
        enterprise_id: str,
        threshold: Optional[float] = None,
    ) -> dict:
        """
        Check enterprise spending and send alert if threshold reached.

        Args:
            db: Database session
            enterprise_id: Enterprise ID
            threshold: Spending threshold (uses default if not provided)

        Returns:
            Dict with check result and notification status
        """
        threshold = threshold or self._default_spending_threshold

        # Get enterprise
        result = await db.execute(
            select(Enterprise).where(Enterprise.id == enterprise_id)
        )
        enterprise = result.scalar_one_or_none()

        if not enterprise:
            return {
                "status": "failed",
                "reason": "enterprise_not_found",
                "enterprise_id": enterprise_id,
            }

        # Calculate total spending for current period
        current_period = datetime.utcnow().strftime("%Y-%m")

        result = await db.execute(
            select(func.coalesce(func.sum(BillingRecord.amount), 0.0))
            .where(BillingRecord.enterprise_id == enterprise_id)
            .where(BillingRecord.billing_period == current_period)
        )
        total_spent = result.scalar() or 0.0

        if total_spent < threshold:
            return {
                "status": "ok",
                "total_spent": total_spent,
                "threshold": threshold,
                "billing_period": current_period,
                "notification_sent": False,
            }

        # Send spending threshold notification
        contact_email = enterprise.contact.get("email") if enterprise.contact else None

        if not contact_email:
            return {
                "status": "failed",
                "reason": "no_email",
                "enterprise_id": enterprise_id,
            }

        html_content = EmailTemplate.SPENDING_THRESHOLD.format(
            company_name=enterprise.name,
            total_spent=total_spent,
            threshold=threshold,
            billing_period=current_period,
        )

        subject = f"【AgentHire】消费达到预警阈值 - {enterprise.name}"

        email_result = await self.send_email(
            to_email=contact_email,
            subject=subject,
            html_content=html_content,
        )

        return {
            "status": "notification_sent",
            "total_spent": total_spent,
            "threshold": threshold,
            "billing_period": current_period,
            "email_result": email_result,
        }

    async def get_enterprise_balance(
        self,
        db: AsyncSession,
        enterprise_id: str,
    ) -> float:
        """
        Get enterprise current balance.

        Args:
            db: Database session
            enterprise_id: Enterprise ID

        Returns:
            Current balance
        """
        result = await db.execute(
            select(Enterprise).where(Enterprise.id == enterprise_id)
        )
        enterprise = result.scalar_one_or_none()

        if not enterprise:
            return 0.0

        billing_info = enterprise.billing_info or {}
        return billing_info.get("balance", 1000.0)

    async def update_enterprise_balance(
        self,
        db: AsyncSession,
        enterprise_id: str,
        new_balance: float,
    ) -> bool:
        """
        Update enterprise balance.

        Args:
            db: Database session
            enterprise_id: Enterprise ID
            new_balance: New balance value

        Returns:
            True if updated successfully
        """
        result = await db.execute(
            select(Enterprise).where(Enterprise.id == enterprise_id)
        )
        enterprise = result.scalar_one_or_none()

        if not enterprise:
            return False

        billing_info = enterprise.billing_info or {}
        billing_info["balance"] = new_balance
        enterprise.billing_info = billing_info

        await db.flush()
        return True


# Singleton instance
notification_service = NotificationService()
