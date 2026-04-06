"""
Agent Service
处理 Agent 注册和认证
"""

import hashlib
import hmac
import secrets
from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decrypt_value, encrypt_value
from app.models import Agent, generate_id
from app.services.identity_service import identity_service


# Maximum allowed timestamp drift (seconds) for agent signature verification
MAX_TIMESTAMP_DRIFT = 60  # 1 minute


class AgentService:
    """Service for managing agents (job seekers and employers)."""

    async def register(
        self,
        db: AsyncSession,
        name: str,
        agent_type: str,
        platform: Optional[str] = None,
        contact: Optional[dict] = None,
    ) -> dict:
        """
        Register a new agent.

        Args:
            db: Database session
            name: Agent name
            agent_type: 'seeker' or 'employer'
            platform: Source platform (e.g., 'openclaw')
            contact: Contact information dict

        Returns:
            dict with agent_id and agent_secret
        """
        # 1. Create Tenant via IdentityService
        tenant = await identity_service.create_tenant(
            db, name=name, tenant_type="individual"
        )

        # 2. Create Principal via IdentityService
        principal = await identity_service.create_principal(
            db,
            tenant_id=tenant.id,
            principal_type="agent",
            name=name,
        )

        # 3. Create Agent Secret Credential via IdentityService
        # This returns (Credential, plaintext_secret)
        credential, agent_secret = await identity_service.create_agent_secret_credential(
            db, principal_id=principal.id, name=f"agent-{name}"
        )

        # 4. Create Agent record
        agent_id = generate_id("agt_")
        agent = Agent(
            id=agent_id,
            tenant_id=tenant.id,
            principal_id=principal.id,
            name=name,
            type=agent_type,
            platform=platform,
            contact=contact or {},
            # Store encrypted secret for HMAC verification (backward compatibility)
            api_secret_encrypted=encrypt_value(agent_secret, purpose="agent_secret"),
            status="active",
        )

        db.add(agent)
        await db.flush()

        return {
            "agent_id": agent_id,
            "agent_secret": agent_secret,  # Only shown once!
            "tenant_id": tenant.id,
            "principal_id": principal.id,
            "credential_id": credential.id,
            "created_at": agent.created_at.isoformat(),
        }

    async def authenticate(
        self,
        db: AsyncSession,
        agent_id: str,
        timestamp: int,
        signature: str,
    ) -> Optional[str]:
        """
        Authenticate an agent request.

        Args:
            db: Database session
            agent_id: Agent ID
            timestamp: Request timestamp
            signature: HMAC signature

        Returns:
            agent_id if valid, None otherwise
        """
        # Check timestamp (within MAX_TIMESTAMP_DRIFT)
        current_time = int(datetime.utcnow().timestamp())
        if abs(current_time - timestamp) > MAX_TIMESTAMP_DRIFT:
            return None

        # Get agent
        result = await db.execute(
            select(Agent).where(Agent.id == agent_id, Agent.status == "active")
        )
        agent = result.scalar_one_or_none()

        if not agent:
            return None

        # Verify signature
        message = f"{agent_id}{timestamp}"
        decrypted_secret = decrypt_value(agent.api_secret_encrypted, purpose="agent_secret")
        expected_signature = hmac.new(
            decrypted_secret.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(signature, expected_signature):
            return None

        return agent_id

    async def get_agent(
        self,
        db: AsyncSession,
        agent_id: str,
    ) -> Optional[dict]:
        """
        Get agent information.

        Args:
            db: Database session
            agent_id: Agent ID

        Returns:
            Agent info dict or None
        """
        result = await db.execute(
            select(Agent).where(Agent.id == agent_id)
        )
        agent = result.scalar_one_or_none()

        if not agent:
            return None

        return {
            "id": agent.id,
            "name": agent.name,
            "type": agent.type,
            "platform": agent.platform,
            "tenant_id": agent.tenant_id,
            "principal_id": agent.principal_id,
            "contact": agent.contact,
            "status": agent.status,
            "created_at": agent.created_at.isoformat(),
        }


# Singleton instance
agent_service = AgentService()