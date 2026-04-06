"""
Audit Service
Business logic for audit logging.
"""

from datetime import datetime
from typing import Optional, Sequence

from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog, AuditEventType, AuditActorType, AuditAction
from app.models import generate_id


class AuditService:
    """Service for creating and querying audit logs."""

    async def create_log(
        self,
        db: AsyncSession,
        event_type: str,
        actor_type: str,
        action: str,
        actor_id: Optional[str] = None,
        target_type: Optional[str] = None,
        target_id: Optional[str] = None,
        request_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        changes: Optional[dict] = None,
        metadata: Optional[dict] = None,
        status: str = "success",
        error_message: Optional[str] = None,
    ) -> AuditLog:
        """
        Create a new audit log entry.

        Args:
            db: Database session
            event_type: Type of event (from AuditEventType)
            actor_type: Type of actor (from AuditActorType)
            action: Action performed
            actor_id: ID of the actor
            target_type: Type of target entity
            target_id: ID of target entity
            request_id: HTTP request ID
            ip_address: Client IP address
            user_agent: Client user agent
            resource_type: Type of resource affected
            resource_id: ID of resource affected
            changes: Before/after changes
            metadata: Additional context
            status: Operation status
            error_message: Error message if failed

        Returns:
            Created AuditLog instance
        """
        log = AuditLog(
            id=generate_id("aud_"),
            event_type=event_type,
            actor_type=actor_type,
            actor_id=actor_id,
            target_type=target_type,
            target_id=target_id,
            request_id=request_id,
            ip_address=ip_address,
            user_agent=user_agent,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            changes=changes,
            metadata=metadata,
            status=status,
            error_message=error_message,
        )

        db.add(log)
        await db.flush()

        return log

    async def log_enterprise_event(
        self,
        db: AsyncSession,
        action: str,
        enterprise_id: str,
        actor_id: Optional[str] = None,
        request_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        metadata: Optional[dict] = None,
        status: str = "success",
        error_message: Optional[str] = None,
    ) -> AuditLog:
        """Log an enterprise-related event."""
        event_type_map = {
            AuditAction.CREATE: AuditEventType.ENTERPRISE_APPLIED,
            AuditAction.APPROVE: AuditEventType.ENTERPRISE_APPROVED,
            AuditAction.REJECT: AuditEventType.ENTERPRISE_REJECTED,
            AuditAction.UPDATE: AuditEventType.ENTERPRISE_APPROVED,  # Status change
        }
        event_type = event_type_map.get(action, AuditEventType.ENTERPRISE_APPLIED)

        return await self.create_log(
            db=db,
            event_type=event_type,
            actor_type=AuditActorType.ENTERPRISE,
            action=action,
            actor_id=actor_id or enterprise_id,
            target_type="enterprise",
            target_id=enterprise_id,
            resource_type="enterprise",
            resource_id=enterprise_id,
            request_id=request_id,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=metadata,
            status=status,
            error_message=error_message,
        )

    async def log_agent_claim_event(
        self,
        db: AsyncSession,
        action: str,
        agent_id: str,
        user_id: str,
        request_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        metadata: Optional[dict] = None,
        status: str = "success",
        error_message: Optional[str] = None,
    ) -> AuditLog:
        """Log an agent claiming event."""
        event_type = AuditEventType.AGENT_CLAIMED if action == AuditAction.VERIFY else AuditEventType.AGENT_REGISTERED

        return await self.create_log(
            db=db,
            event_type=event_type,
            actor_type=AuditActorType.USER,
            action=action,
            actor_id=user_id,
            target_type="agent",
            target_id=agent_id,
            resource_type="agent",
            resource_id=agent_id,
            request_id=request_id,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=metadata,
            status=status,
            error_message=error_message,
        )

    async def log_api_key_event(
        self,
        db: AsyncSession,
        action: str,
        api_key_id: str,
        enterprise_id: str,
        request_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        metadata: Optional[dict] = None,
        status: str = "success",
        error_message: Optional[str] = None,
    ) -> AuditLog:
        """Log an API key event."""
        event_type_map = {
            AuditAction.CREATE: AuditEventType.API_KEY_CREATED,
            AuditAction.REVOKE: AuditEventType.API_KEY_REVOKED,
            AuditAction.ROTATE: AuditEventType.API_KEY_ROTATED,
        }
        event_type = event_type_map.get(action, AuditEventType.API_KEY_CREATED)

        return await self.create_log(
            db=db,
            event_type=event_type,
            actor_type=AuditActorType.ENTERPRISE,
            action=action,
            actor_id=enterprise_id,
            target_type="api_key",
            target_id=api_key_id,
            resource_type="api_key",
            resource_id=api_key_id,
            request_id=request_id,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=metadata,
            status=status,
            error_message=error_message,
        )

    async def log_billing_event(
        self,
        db: AsyncSession,
        enterprise_id: str,
        billing_record_id: str,
        usage_type: str,
        amount: float,
        request_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        metadata: Optional[dict] = None,
        status: str = "success",
        error_message: Optional[str] = None,
    ) -> AuditLog:
        """Log a billing event."""
        return await self.create_log(
            db=db,
            event_type=AuditEventType.BILLING_RECORDED,
            actor_type=AuditActorType.SYSTEM,
            action="record",
            actor_id=enterprise_id,
            target_type="billing_record",
            target_id=billing_record_id,
            resource_type="billing",
            resource_id=billing_record_id,
            request_id=request_id,
            ip_address=ip_address,
            user_agent=user_agent,
            changes={"usage_type": usage_type, "amount": amount},
            metadata=metadata,
            status=status,
            error_message=error_message,
        )

    async def log_login_event(
        self,
        db: AsyncSession,
        actor_type: str,
        actor_id: str,
        success: bool,
        request_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> AuditLog:
        """Log a login attempt."""
        event_type = AuditEventType.LOGIN_SUCCESS if success else AuditEventType.LOGIN_FAILED

        return await self.create_log(
            db=db,
            event_type=event_type,
            actor_type=actor_type,
            action=AuditAction.LOGIN,
            actor_id=actor_id,
            target_type=actor_type,
            target_id=actor_id,
            request_id=request_id,
            ip_address=ip_address,
            user_agent=user_agent,
            status="success" if success else "failure",
            error_message=error_message,
        )

    async def query_logs(
        self,
        db: AsyncSession,
        event_type: Optional[str] = None,
        actor_type: Optional[str] = None,
        actor_id: Optional[str] = None,
        target_type: Optional[str] = None,
        target_id: Optional[str] = None,
        status: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[Sequence[AuditLog], int]:
        """
        Query audit logs with filters.

        Returns:
            Tuple of (logs, total_count)
        """
        conditions = []

        if event_type:
            conditions.append(AuditLog.event_type == event_type)
        if actor_type:
            conditions.append(AuditLog.actor_type == actor_type)
        if actor_id:
            conditions.append(AuditLog.actor_id == actor_id)
        if target_type:
            conditions.append(AuditLog.target_type == target_type)
        if target_id:
            conditions.append(AuditLog.target_id == target_id)
        if status:
            conditions.append(AuditLog.status == status)
        if start_date:
            conditions.append(AuditLog.created_at >= start_date)
        if end_date:
            conditions.append(AuditLog.created_at <= end_date)

        # Count query
        count_query = select(func.count(AuditLog.id))
        if conditions:
            count_query = count_query.where(and_(*conditions))
        count_result = await db.execute(count_query)
        total = count_result.scalar()

        # Data query
        query = select(AuditLog)
        if conditions:
            query = query.where(and_(*conditions))
        query = query.order_by(AuditLog.created_at.desc()).limit(limit).offset(offset)

        result = await db.execute(query)
        logs = result.scalars().all()

        return logs, total

    async def get_enterprise_logs(
        self,
        db: AsyncSession,
        enterprise_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[Sequence[AuditLog], int]:
        """Get all audit logs for an enterprise."""
        return await self.query_logs(
            db=db,
            actor_id=enterprise_id,
            limit=limit,
            offset=offset,
        )

    async def get_agent_logs(
        self,
        db: AsyncSession,
        agent_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[Sequence[AuditLog], int]:
        """Get all audit logs for an agent."""
        return await self.query_logs(
            db=db,
            target_id=agent_id,
            target_type="agent",
            limit=limit,
            offset=offset,
        )

    async def get_user_logs(
        self,
        db: AsyncSession,
        user_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[Sequence[AuditLog], int]:
        """Get all audit logs for a user."""
        return await self.query_logs(
            db=db,
            actor_id=user_id,
            actor_type=AuditActorType.USER,
            limit=limit,
            offset=offset,
        )


# Singleton instance
audit_service = AuditService()
