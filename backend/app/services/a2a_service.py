"""
A2A Protocol Service
Agent to Agent 通信协议

实现 Agent 之间的直接协商流程：
1. ExpressInterest - 表达意向
2. NegotiateSalary - 薪资谈判
3. Confirm - 双向确认

平台角色：仅在双方确认后介入，交换联系方式
"""

import hashlib
from typing import Optional
from datetime import datetime
from enum import Enum

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import A2AInterest, A2ASession, generate_id


class A2AService:
    """
    A2A 协议服务
    管理 Agent 之间的通信和协商状态
    """

    async def express_interest(
        self,
        db: AsyncSession,
        profile_id: str,
        job_id: str,
        seeker_agent_id: str,
        employer_agent_id: str,
        message: str = None,
    ) -> dict:
        """
        表达意向 (ExpressInterest)
        求职 Agent 向企业 Agent 表达对某职位的兴趣

        Returns:
            意向记录
        """
        # Check if interest already exists
        existing = await db.execute(
            select(A2AInterest).where(
                A2AInterest.profile_id == profile_id,
                A2AInterest.job_id == job_id,
            )
        )
        existing_interest = existing.scalar_one_or_none()

        if existing_interest:
            return existing_interest.to_dict()

        # Create new interest
        interest = A2AInterest(
            id=generate_id("int_"),
            profile_id=profile_id,
            job_id=job_id,
            seeker_agent_id=seeker_agent_id,
            employer_agent_id=employer_agent_id,
            message=message,
            status="pending",
        )

        db.add(interest)
        await db.flush()

        return interest.to_dict()

    async def respond_to_interest(
        self,
        db: AsyncSession,
        profile_id: str,
        job_id: str,
        action: str,  # "accept" or "reject"
        employer_agent_id: str,
    ) -> dict:
        """
        回应意向 (企业 Agent)
        """
        result = await db.execute(
            select(A2AInterest).where(
                A2AInterest.profile_id == profile_id,
                A2AInterest.job_id == job_id,
            )
        )
        interest = result.scalar_one_or_none()

        if not interest:
            return {"success": False, "error": "Interest not found"}

        # 验证是否是目标 employer
        if interest.employer_agent_id != employer_agent_id:
            return {"success": False, "error": "Unauthorized"}

        if action == "accept":
            interest.status = "accepted"
            interest.updated_at = datetime.utcnow()

            # 自动创建协商会话
            session = A2ASession(
                id=generate_id("ses_"),
                interest_id=interest.id,
                profile_id=profile_id,
                job_id=job_id,
                seeker_agent_id=interest.seeker_agent_id,
                employer_agent_id=employer_agent_id,
                status="negotiating",
                messages=[],
            )

            db.add(session)
            await db.flush()

            return {
                "success": True,
                "status": "accepted",
                "session_id": session.id,
                "message": "Interest accepted. Negotiation session created.",
            }
        else:
            interest.status = "rejected"
            interest.updated_at = datetime.utcnow()
            return {"success": True, "status": "rejected"}

    async def negotiate_salary(
        self,
        db: AsyncSession,
        session_id: str,
        from_agent_id: str,
        offer: dict,  # {salary, start_date, notes}
    ) -> dict:
        """
        薪资谈判 (NegotiateSalary)
        Agent 之间协商薪资和入职时间
        """
        result = await db.execute(
            select(A2ASession).where(A2ASession.id == session_id)
        )
        session = result.scalar_one_or_none()

        if not session:
            return {"success": False, "error": "Session not found"}

        # 验证发送者身份
        if from_agent_id not in [session.seeker_agent_id, session.employer_agent_id]:
            return {"success": False, "error": "Unauthorized"}

        # 更新当前报价
        session.current_offer = offer
        session.status = "negotiating"
        session.updated_at = datetime.utcnow()

        # 记录消息
        messages = session.messages or []
        messages.append({
            "type": "negotiate_salary",
            "from": from_agent_id,
            "offer": offer,
            "timestamp": datetime.utcnow().isoformat(),
        })
        session.messages = messages

        await db.flush()

        return {
            "success": True,
            "session_id": session.id,
            "status": session.status,
            "current_offer": session.current_offer,
        }

    async def confirm(
        self,
        db: AsyncSession,
        session_id: str,
        agent_id: str,
    ) -> dict:
        """
        确认 (Confirm)
        双向确认后，平台介入交换联系方式
        """
        result = await db.execute(
            select(A2ASession).where(A2ASession.id == session_id)
        )
        session = result.scalar_one_or_none()

        if not session:
            return {"success": False, "error": "Session not found"}

        # 验证确认者身份
        if agent_id not in [session.seeker_agent_id, session.employer_agent_id]:
            return {"success": False, "error": "Unauthorized"}

        # 记录确认
        messages = session.messages or []
        messages.append({
            "type": "confirm",
            "from": agent_id,
            "timestamp": datetime.utcnow().isoformat(),
        })
        session.messages = messages

        # 更新确认状态
        if agent_id == session.seeker_agent_id:
            session.seeker_confirmed = True
        elif agent_id == session.employer_agent_id:
            session.employer_confirmed = True

        # 检查是否双方都已确认
        if session.seeker_confirmed and session.employer_confirmed:
            session.status = "confirmed"
            session.contact_exchanged_at = datetime.utcnow()

            await db.flush()

            # 找到对应的application并自动解锁联系方式
            contact_data = await self._exchange_contacts_for_a2a(db, session)

            return {
                "success": True,
                "status": "confirmed",
                "session_id": session.id,
                "contact_exchange": True,
                "contact": contact_data,
                "message": "Both parties confirmed. Contact information exchanged.",
            }

        await db.flush()

        return {
            "success": True,
            "status": "pending",
            "session_id": session.id,
            "message": "Confirmation recorded. Waiting for other party.",
        }

    async def _exchange_contacts_for_a2a(
        self,
        db: AsyncSession,
        session: A2ASession,
    ) -> dict:
        """
        A2A 双方确认后，实际交换联系方式。
        查找对应的application，自动解锁contact。
        决策：如果同一候选人多次申请同一职位，取最新的一条。
        """
        from app.models import Application, SeekerProfile, JobPosting
        from app.services.contact_unlock_service import contact_unlock_service

        # 查找该 profile_id + job_id 对应的 application（取最新一条）
        app_result = await db.execute(
            select(Application)
            .where(
                Application.profile_id == session.profile_id,
                Application.job_id == session.job_id,
            )
            .order_by(Application.created_at.desc())  # 取最新
            .limit(1)
        )
        application = app_result.scalar_one_or_none()

        contact_info = {"seeker": None, "employer": None}

        if application:
            # 自动解锁 contact
            try:
                unlock = await contact_unlock_service.auto_unlock_for_a2a(db, application.id)
                if unlock.status == "unlocked":
                    # 获取求职者和企业的联系信息
                    profile_result = await db.execute(
                        select(SeekerProfile).where(SeekerProfile.id == session.profile_id)
                    )
                    profile = profile_result.scalar_one_or_none()
                    if profile:
                        contact_info["seeker"] = profile.contact

                    job_result = await db.execute(
                        select(JobPosting).where(JobPosting.id == session.job_id)
                    )
                    job = job_result.scalar_one_or_none()
                    if job:
                        # 企业联系信息从 JobPosting 的 enterprise_id 获取
                        from app.models import Enterprise
                        ent_result = await db.execute(
                            select(Enterprise).where(Enterprise.id == job.enterprise_id)
                        )
                        enterprise = ent_result.scalar_one_or_none()
                        if enterprise:
                            contact_info["employer"] = enterprise.contact
            except Exception:
                # contact_unlock 失败不影响 A2A confirm
                pass

        return contact_info

    async def reject(
        self,
        db: AsyncSession,
        session_id: str,
        agent_id: str,
        reason: str = None,
    ) -> dict:
        """
        拒绝 (Reject)
        一方拒绝协商
        """
        result = await db.execute(
            select(A2ASession).where(A2ASession.id == session_id)
        )
        session = result.scalar_one_or_none()

        if not session:
            return {"success": False, "error": "Session not found"}

        if agent_id not in [session.seeker_agent_id, session.employer_agent_id]:
            return {"success": False, "error": "Unauthorized"}

        session.status = "rejected"
        session.updated_at = datetime.utcnow()

        messages = session.messages or []
        messages.append({
            "type": "reject",
            "from": agent_id,
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat(),
        })
        session.messages = messages

        await db.flush()

        return {
            "success": True,
            "status": "rejected",
            "session_id": session.id,
        }

    async def get_session(
        self,
        db: AsyncSession,
        session_id: str,
    ) -> Optional[dict]:
        """获取会话详情"""
        result = await db.execute(
            select(A2ASession).where(A2ASession.id == session_id)
        )
        session = result.scalar_one_or_none()

        if not session:
            return None

        return {
            "session_id": session.id,
            "interest_id": session.interest_id,
            "profile_id": session.profile_id,
            "job_id": session.job_id,
            "seeker_agent_id": session.seeker_agent_id,
            "employer_agent_id": session.employer_agent_id,
            "status": session.status,
            "current_offer": session.current_offer,
            "messages": session.messages,
            "seeker_confirmed": session.seeker_confirmed,
            "employer_confirmed": session.employer_confirmed,
            "contact_exchanged_at": session.contact_exchanged_at.isoformat() if session.contact_exchanged_at else None,
            "created_at": session.created_at.isoformat() if session.created_at else None,
        }

    async def get_interest(
        self,
        db: AsyncSession,
        profile_id: str,
        job_id: str,
    ) -> Optional[dict]:
        """获取意向记录"""
        result = await db.execute(
            select(A2AInterest).where(
                A2AInterest.profile_id == profile_id,
                A2AInterest.job_id == job_id,
            )
        )
        interest = result.scalar_one_or_none()

        if not interest:
            return None

        return interest.to_dict()


# Singleton instance
a2a_service = A2AService()