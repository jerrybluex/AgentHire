"""
Claim Service
Agent 认领服务 - C端用户认领 Agent
"""

import secrets
from typing import Optional
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Agent, AgentClaim, generate_id


class ClaimService:
    """Service for managing Agent claims."""

    async def initiate_claim(
        self,
        db: AsyncSession,
        user_id: str,
        agent_id: str,
    ) -> Optional[dict]:
        """
        Initiate an Agent claim request.

        Args:
            db: Database session
            user_id: User ID
            agent_id: Agent ID to claim

        Returns:
            Dict with claim_id and verification_code, or None if Agent not found
        """
        # Verify Agent exists
        agent_result = await db.execute(select(Agent).where(Agent.id == agent_id))
        agent = agent_result.scalar_one_or_none()

        if not agent:
            return None

        # Check if already claimed
        existing_claim = await self.get_active_claim(db, user_id, agent_id)
        if existing_claim:
            # Return existing claim info
            return {
                "claim_id": existing_claim.id,
                "agent_id": agent_id,
                "status": existing_claim.status,
                "expires_at": existing_claim.expires_at.isoformat(),
            }

        # Generate 6-digit verification code
        verification_code = "".join([str(secrets.randbelow(10)) for _ in range(6)])

        # Create claim record
        claim = AgentClaim(
            id=generate_id("clm_"),
            user_id=user_id,
            agent_id=agent_id,
            verification_code=verification_code,
            status="pending",
            expires_at=datetime.utcnow() + timedelta(hours=24),
        )

        db.add(claim)
        await db.flush()

        return {
            "claim_id": claim.id,
            "agent_id": agent_id,
            "verification_code": verification_code,  # In production, send via email/SMS
            "status": claim.status,
            "expires_at": claim.expires_at.isoformat(),
        }

    async def verify_claim(
        self,
        db: AsyncSession,
        user_id: str,
        agent_id: str,
        verification_code: str,
    ) -> Optional[dict]:
        """
        Verify and complete an Agent claim.

        Args:
            db: Database session
            user_id: User ID
            agent_id: Agent ID
            verification_code: 6-digit verification code

        Returns:
            Dict with claim result, or None if claim not found/invalid
        """
        result = await db.execute(
            select(AgentClaim).where(
                AgentClaim.user_id == user_id,
                AgentClaim.agent_id == agent_id,
                AgentClaim.status == "pending",
            )
        )
        claim = result.scalar_one_or_none()

        if not claim:
            return None

        # Check if expired
        if claim.expires_at < datetime.utcnow():
            claim.status = "expired"
            await db.flush()
            return {"success": False, "error": "Verification code expired"}

        # Verify code
        if claim.verification_code != verification_code:
            return {"success": False, "error": "Invalid verification code"}

        # Complete the claim
        claim.status = "verified"
        claim.verified_at = datetime.utcnow()
        claim.claimed_at = datetime.utcnow()

        # Update Agent's user_id
        agent_result = await db.execute(select(Agent).where(Agent.id == agent_id))
        agent = agent_result.scalar_one_or_none()
        if agent:
            agent.user_id = user_id

        await db.flush()

        return {
            "success": True,
            "agent_id": agent_id,
            "claimed_at": claim.claimed_at.isoformat(),
        }

    async def get_active_claim(
        self,
        db: AsyncSession,
        user_id: str,
        agent_id: str,
    ) -> Optional[AgentClaim]:
        """Get active claim for user and agent."""
        result = await db.execute(
            select(AgentClaim).where(
                AgentClaim.user_id == user_id,
                AgentClaim.agent_id == agent_id,
                AgentClaim.status.in_(["pending", "verified"]),
            )
        )
        return result.scalar_one_or_none()

    async def get_claim_status(
        self,
        db: AsyncSession,
        user_id: str,
        agent_id: str,
    ) -> Optional[dict]:
        """
        Get claim status for user and agent.

        Args:
            db: Database session
            user_id: User ID
            agent_id: Agent ID

        Returns:
            Claim status dict or None
        """
        claim = await self.get_active_claim(db, user_id, agent_id)

        if not claim:
            # Check if Agent is already bound to this user
            agent_result = await db.execute(select(Agent).where(Agent.id == agent_id))
            agent = agent_result.scalar_one_or_none()

            if agent and agent.user_id == user_id:
                return {
                    "status": "verified",
                    "agent_id": agent_id,
                    "message": "Agent is already bound to your account",
                }

            return None

        return {
            "claim_id": claim.id,
            "agent_id": agent_id,
            "status": claim.status,
            "expires_at": claim.expires_at.isoformat(),
            "claimed_at": claim.claimed_at.isoformat() if claim.claimed_at else None,
            "verified_at": claim.verified_at.isoformat() if claim.verified_at else None,
        }

    async def list_user_claims(
        self,
        db: AsyncSession,
        user_id: str,
    ) -> list[dict]:
        """
        List all claims for a user.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            List of claim status dicts
        """
        result = await db.execute(
            select(AgentClaim).where(AgentClaim.user_id == user_id)
        )
        claims = result.scalars().all()

        return [
            {
                "claim_id": claim.id,
                "agent_id": claim.agent_id,
                "status": claim.status,
                "claimed_at": claim.claimed_at.isoformat() if claim.claimed_at else None,
                "verified_at": claim.verified_at.isoformat() if claim.verified_at else None,
            }
            for claim in claims
        ]


# Singleton instance
claim_service = ClaimService()
