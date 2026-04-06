"""
Enterprise Verification Service
企业实名审核状态机
"""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enterprise_verification import EnterpriseVerificationCase


# PRD v2 定义的状态转换
VERIFICATION_TRANSITIONS = {
    "draft": ["submitted"],
    "submitted": ["under_review", "rejected"],
    "under_review": ["approved", "needs_resubmission", "rejected"],
    "needs_resubmission": ["submitted"],
    "approved": ["suspended"],
    "rejected": [],  # 终态
    "suspended": [],  # 终态
}


class EnterpriseVerificationError(Exception):
    """企业审核异常基类"""
    pass


class InvalidVerificationTransitionError(EnterpriseVerificationError):
    """无效的审核状态转换"""
    pass


class VerificationCaseNotFoundError(EnterpriseVerificationError):
    """审核案例不存在"""
    pass


class EnterpriseVerificationService:
    """企业审核服务"""

    async def create_verification_case(
        self,
        db: AsyncSession,
        enterprise_id: str,
        submitted_by: str,  # 提交人的 principal_id
    ) -> EnterpriseVerificationCase:
        """
        创建审核案例（初始状态为 draft）。
        """
        case = EnterpriseVerificationCase(
            enterprise_id=enterprise_id,
            status="draft",
            submitted_by=submitted_by,
        )
        db.add(case)
        await db.flush()
        return case

    async def submit_for_review(
        self,
        db: AsyncSession,
        case_id: str,
    ) -> EnterpriseVerificationCase:
        """提交审核（draft → submitted）"""
        return await self._transition(
            db, case_id, "submitted", actor_id=None
        )

    async def start_review(
        self,
        db: AsyncSession,
        case_id: str,
        reviewer_id: str,
    ) -> EnterpriseVerificationCase:
        """开始审核（submitted → under_review）"""
        return await self._transition(
            db, case_id, "under_review", actor_id=reviewer_id
        )

    async def approve(
        self,
        db: AsyncSession,
        case_id: str,
        reviewer_id: str,
        comment: Optional[str] = None,
    ) -> EnterpriseVerificationCase:
        """审核通过（under_review → approved）"""
        return await self._transition(
            db, case_id, "approved", actor_id=reviewer_id, comment=comment
        )

    async def reject(
        self,
        db: AsyncSession,
        case_id: str,
        reviewer_id: str,
        reason: str,
    ) -> EnterpriseVerificationCase:
        """审核拒绝（under_review → rejected）"""
        return await self._transition(
            db, case_id, "rejected", actor_id=reviewer_id, comment=reason
        )

    async def request_resubmission(
        self,
        db: AsyncSession,
        case_id: str,
        reviewer_id: str,
        reason: str,
    ) -> EnterpriseVerificationCase:
        """需要补充材料（under_review → needs_resubmission）"""
        return await self._transition(
            db, case_id, "needs_resubmission", actor_id=reviewer_id, comment=reason
        )

    async def suspend(
        self,
        db: AsyncSession,
        case_id: str,
        reviewer_id: str,
        reason: str,
    ) -> EnterpriseVerificationCase:
        """吊销/暂停（approved → suspended）"""
        return await self._transition(
            db, case_id, "suspended", actor_id=reviewer_id, comment=reason
        )

    async def _transition(
        self,
        db: AsyncSession,
        case_id: str,
        new_status: str,
        actor_id: Optional[str],
        comment: Optional[str] = None,
    ) -> EnterpriseVerificationCase:
        """内部状态转换"""
        result = await db.execute(
            select(EnterpriseVerificationCase).where(
                EnterpriseVerificationCase.id == case_id
            )
        )
        case = result.scalar_one_or_none()

        if not case:
            raise VerificationCaseNotFoundError(f"Case {case_id} not found")

        current_status = case.status

        # 验证转换
        allowed = VERIFICATION_TRANSITIONS.get(current_status, [])
        if new_status not in allowed:
            raise InvalidVerificationTransitionError(
                f"Invalid transition: {current_status} -> {new_status}. "
                f"Allowed: {allowed}"
            )

        # 更新状态
        case.status = new_status
        case.reviewed_by = actor_id
        case.reviewed_at = datetime.now(timezone.utc)

        if comment:
            case.review_comment = comment

        await db.flush()
        return case


# Singleton
enterprise_verification_service = EnterpriseVerificationService()
