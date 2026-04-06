"""
Application Service
管理申请状态机和事件流
"""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.application import Application
from app.models.application_event import ApplicationEvent, generate_app_event_id


# PRD v2 定义的状态转换
VALID_TRANSITIONS = {
    "draft": ["submitted"],
    "submitted": ["viewed", "rejected"],
    "viewed": ["shortlisted", "rejected", "interview_requested"],
    "shortlisted": ["rejected", "interview_requested", "closed"],
    "interview_requested": ["rejected", "interview_scheduled", "closed"],
    "interview_scheduled": ["rejected", "closed"],
    "closed": [],
    "rejected": [],  # 终态
}


class ApplicationServiceError(Exception):
    """Application Service 异常基类"""
    pass


class InvalidTransitionError(ApplicationServiceError):
    """无效的状态转换"""
    pass


class ApplicationNotFoundError(ApplicationServiceError):
    """申请不存在"""
    pass


class ApplicationService:
    """申请服务 - PRD v2 核心服务"""

    async def create_application(
        self,
        db: AsyncSession,
        profile_id: str,
        job_id: str,
        applicant_principal_id: str,
        cover_letter: Optional[str] = None,
    ) -> Application:
        """
        创建申请（初始状态为 draft）。

        Args:
            db: 数据库会话
            profile_id: 求职者 Profile ID
            job_id: 职位 ID
            applicant_principal_id: 申请人的 Principal ID
            cover_letter: 求职信

        Returns:
            创建的 Application 实例
        """
        from app.models.application import Application, generate_application_id

        application = Application(
            id=generate_application_id(),
            profile_id=profile_id,
            job_id=job_id,
            applicant_principal_id=applicant_principal_id,
            status="draft",
            cover_letter=cover_letter,
        )
        db.add(application)
        await db.flush()

        # 记录创建事件
        event = ApplicationEvent(
            id=generate_app_event_id(),
            application_id=application.id,
            event_type="created",
            from_status=None,
            to_status="draft",
            actor_type="system",
            actor_id=None,
            event_metadata={},
        )
        db.add(event)
        await db.flush()

        return application

    async def submit_application(
        self,
        db: AsyncSession,
        application_id: str,
        actor_type: str,  # "agent" | "human"
        actor_id: str,
    ) -> Application:
        """
        提交申请（draft → submitted）。

        Args:
            db: 数据库会话
            application_id: 申请 ID
            actor_type: 操作者类型
            actor_id: 操作者 ID

        Returns:
            更新后的 Application
        """
        return await self._transition_status(
            db, application_id, "submitted", actor_type, actor_id
        )

    async def transition_status(
        self,
        db: AsyncSession,
        application_id: str,
        new_status: str,
        actor_type: str,
        actor_id: str,
        comment: Optional[str] = None,
    ) -> Application:
        """
        状态转换（内部方法）。

        Args:
            db: 数据库会话
            application_id: 申请 ID
            new_status: 新状态
            actor_type: 操作者类型
            actor_id: 操作者 ID
            comment: 备注

        Returns:
            更新后的 Application
        """
        return await self._transition_status(
            db, application_id, new_status, actor_type, actor_id, comment
        )

    async def _transition_status(
        self,
        db: AsyncSession,
        application_id: str,
        new_status: str,
        actor_type: str,
        actor_id: str,
        comment: Optional[str] = None,
    ) -> Application:
        """内部状态转换逻辑"""
        # 获取申请
        result = await db.execute(
            select(Application).where(Application.id == application_id)
        )
        application = result.scalar_one_or_none()

        if not application:
            raise ApplicationNotFoundError(f"Application {application_id} not found")

        current_status = application.status

        # 验证转换合法性
        allowed = VALID_TRANSITIONS.get(current_status, [])
        if new_status not in allowed:
            raise InvalidTransitionError(
                f"Invalid transition: {current_status} -> {new_status}. "
                f"Allowed: {allowed}"
            )

        # 更新状态
        application.status = new_status
        application.updated_at = datetime.now(timezone.utc)

        # 记录事件
        event = ApplicationEvent(
            id=generate_app_event_id(),
            application_id=application_id,
            event_type="status_changed",
            from_status=current_status,
            to_status=new_status,
            actor_type=actor_type,
            actor_id=actor_id,
            comment=comment,
            event_metadata={},
        )
        db.add(event)
        await db.flush()

        return application

    async def get_application(
        self,
        db: AsyncSession,
        application_id: str,
    ) -> Optional[Application]:
        """获取申请"""
        result = await db.execute(
            select(Application).where(Application.id == application_id)
        )
        return result.scalar_one_or_none()

    async def get_application_events(
        self,
        db: AsyncSession,
        application_id: str,
    ) -> list[ApplicationEvent]:
        """获取申请的所有事件"""
        result = await db.execute(
            select(ApplicationEvent)
            .where(ApplicationEvent.application_id == application_id)
            .order_by(ApplicationEvent.created_at)
        )
        return list(result.scalars().all())

    def is_terminal_status(self, status: str) -> bool:
        """判断是否为终态"""
        return len(VALID_TRANSITIONS.get(status, [])) == 0


# Singleton instance
application_service = ApplicationService()
