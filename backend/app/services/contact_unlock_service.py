"""
Contact Unlock Service
联系方式解锁控制
"""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.contact_unlock import ContactUnlock, generate_contact_unlock_id


# PRD v2 定义的状态转换
CONTACT_UNLOCK_TRANSITIONS = {
    "locked": ["candidate_authorized"],  # 候选人授权
    "candidate_authorized": ["unlocked", "revoked"],  # 企业解锁 或 撤销
    "unlocked": ["revoked"],  # 撤销
    "revoked": [],  # 终态
}


class ContactUnlockError(Exception):
    """ContactUnlock 异常基类"""
    pass


class InvalidTransitionError(ContactUnlockError):
    """无效的状态转换"""
    pass


class ContactUnlockNotFoundError(ContactUnlockError):
    """解锁记录不存在"""
    pass


class ContactUnlockService:
    """联系方式解锁服务"""

    async def create_unlock_request(
        self,
        db: AsyncSession,
        application_id: str,
        requester_type: str,  # "candidate" | "employer"
        requester_id: str,
    ) -> ContactUnlock:
        """
        创建解锁请求（初始状态 locked）。
        后续候选人授权后变为 candidate_authorized。
        """
        unlock = ContactUnlock(
            id=generate_contact_unlock_id(),
            application_id=application_id,
            status="locked",
        )
        db.add(unlock)
        await db.flush()
        return unlock

    async def candidate_authorize(
        self,
        db: AsyncSession,
        unlock_id: str,
        candidate_id: str,
        reason: Optional[str] = None,
    ) -> ContactUnlock:
        """
        候选人授权（locked → candidate_authorized）
        候选人同意企业查看联系方式。
        """
        return await self._transition(
            db, unlock_id, "candidate_authorized",
            actor_id=candidate_id, reason=reason
        )

    async def employer_unlock(
        self,
        db: AsyncSession,
        unlock_id: str,
        employer_id: str,
        reason: Optional[str] = None,
    ) -> ContactUnlock:
        """
        企业解锁联系方式（candidate_authorized → unlocked）
        在候选人授权后，企业可以解锁查看联系方式。
        """
        return await self._transition(
            db, unlock_id, "unlocked",
            actor_id=employer_id, reason=reason
        )

    async def revoke(
        self,
        db: AsyncSession,
        unlock_id: str,
        revoker_id: str,
        reason: Optional[str] = None,
    ) -> ContactUnlock:
        """
        撤销解锁（unlocked → revoked 或 candidate_authorized → revoked）
        """
        return await self._transition(
            db, unlock_id, "revoked",
            actor_id=revoker_id, reason=reason
        )

    async def _transition(
        self,
        db: AsyncSession,
        unlock_id: str,
        new_status: str,
        actor_id: str,
        reason: Optional[str] = None,
    ) -> ContactUnlock:
        """内部状态转换"""
        result = await db.execute(
            select(ContactUnlock).where(ContactUnlock.id == unlock_id)
        )
        unlock = result.scalar_one_or_none()

        if not unlock:
            raise ContactUnlockNotFoundError(f"ContactUnlock {unlock_id} not found")

        current_status = unlock.status

        # 验证转换
        allowed = CONTACT_UNLOCK_TRANSITIONS.get(current_status, [])
        if new_status not in allowed:
            raise InvalidTransitionError(
                f"Invalid transition: {current_status} -> {new_status}. "
                f"Allowed: {allowed}"
            )

        # 更新状态
        unlock.status = new_status

        # 设置对应时间戳
        if new_status == "candidate_authorized":
            unlock.authorized_at = datetime.now(timezone.utc)
        elif new_status == "unlocked":
            unlock.unlocked_at = datetime.now(timezone.utc)
        elif new_status == "revoked":
            unlock.revoked_at = datetime.now(timezone.utc)

        if reason:
            unlock.reason = reason

        await db.flush()
        return unlock

    async def get_by_application(
        self,
        db: AsyncSession,
        application_id: str,
    ) -> Optional[ContactUnlock]:
        """获取申请对应的解锁记录"""
        result = await db.execute(
            select(ContactUnlock)
            .where(ContactUnlock.application_id == application_id)
        )
        return result.scalar_one_or_none()

    async def auto_unlock_for_a2a(
        self,
        db: AsyncSession,
        application_id: str,
    ) -> ContactUnlock:
        """
        A2A 双方确认后自动解锁联系方式。
        由于双方已通过 A2A 协议确认，直接设置为 unlocked 状态。
        """
        # 检查是否已有解锁记录
        existing = await self.get_by_application(db, application_id)
        if existing:
            if existing.status == "unlocked":
                return existing
            # 如果已存在但不是 unlocked，尝试转换
            if existing.status == "candidate_authorized":
                return await self.employer_unlock(db, existing.id, employer_id="a2a_system")
            return existing

        # 创建新的解锁记录并直接解锁
        unlock = ContactUnlock(
            id=generate_contact_unlock_id(),
            application_id=application_id,
            status="unlocked",  # A2A 双方确认后直接解锁
            authorized_at=datetime.now(timezone.utc),
            unlocked_at=datetime.now(timezone.utc),
        )
        db.add(unlock)
        await db.flush()
        return unlock


# Singleton
contact_unlock_service = ContactUnlockService()
