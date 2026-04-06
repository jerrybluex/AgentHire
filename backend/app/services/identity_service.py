"""
Identity & Access Service
管理 Tenant / Principal / Credential 的生命周期
"""

import hashlib
import secrets
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tenant import Tenant, generate_tenant_id
from app.models.principal import Principal, generate_principal_id
from app.models.credential import Credential, generate_credential_id


class IdentityService:
    """身份与访问服务 - PRD v2 核心服务"""

    async def create_tenant(
        self,
        db: AsyncSession,
        name: str,
        tenant_type: str,  # "enterprise" | "individual"
    ) -> Tenant:
        """
        创建租户。

        Args:
            db: 数据库会话
            name: 租户名称
            tenant_type: 租户类型

        Returns:
            创建的 Tenant 实例
        """
        tenant = Tenant(
            id=generate_tenant_id(),
            name=name,
            type=tenant_type,
            status="active",
        )
        db.add(tenant)
        await db.flush()
        return tenant

    async def create_principal(
        self,
        db: AsyncSession,
        tenant_id: str,
        principal_type: str,  # "human" | "agent" | "service"
        name: Optional[str] = None,
        email: Optional[str] = None,
    ) -> Principal:
        """
        创建主体。

        Args:
            db: 数据库会话
            tenant_id: 所属租户 ID
            principal_type: 主体类型
            name: 名称
            email: 邮箱

        Returns:
            创建的 Principal 实例
        """
        principal = Principal(
            id=generate_principal_id(),
            tenant_id=tenant_id,
            type=principal_type,
            name=name,
            email=email,
            status="active",
        )
        db.add(principal)
        await db.flush()
        return principal

    async def create_api_key_credential(
        self,
        db: AsyncSession,
        principal_id: str,
        name: Optional[str] = None,
        expires_in_days: Optional[int] = None,
    ) -> tuple[Credential, str]:
        """
        创建 API Key 凭证。

        Args:
            db: 数据库会话
            principal_id: 所属主体 ID
            name: 凭证名称
            expires_in_days: 过期天数，None 表示永不过期

        Returns:
            (Credential 实例, 明文 API Key) - 明文仅返回一次
        """
        # 生成 API Key
        api_key = f"ak_{secrets.token_urlsafe(32)}"
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()

        expires_at = None
        if expires_in_days:
            from datetime import timedelta
            expires_at = datetime.now(timezone.utc) + timedelta(days=expires_in_days)

        credential = Credential(
            id=generate_credential_id(),
            principal_id=principal_id,
            type="api_key",
            key_hash=key_hash,
            name=name,
            status="active",
            expires_at=expires_at,
        )
        db.add(credential)
        await db.flush()

        return credential, api_key

    async def create_agent_secret_credential(
        self,
        db: AsyncSession,
        principal_id: str,
        name: Optional[str] = None,
    ) -> tuple[Credential, str]:
        """
        创建 Agent Secret 凭证。

        Args:
            db: 数据库会话
            principal_id: 所属主体 ID
            name: 凭证名称

        Returns:
            (Credential 实例, 明文 Secret) - 明文仅返回一次
        """
        # 生成 Agent Secret
        secret = f"as_{secrets.token_urlsafe(32)}"
        key_hash = hashlib.sha256(secret.encode()).hexdigest()

        credential = Credential(
            id=generate_credential_id(),
            principal_id=principal_id,
            type="agent_secret",
            key_hash=key_hash,
            name=name,
            status="active",
        )
        db.add(credential)
        await db.flush()

        return credential, secret

    async def verify_api_key(
        self,
        db: AsyncSession,
        api_key: str,
    ) -> Optional[tuple[Credential, Principal]]:
        """
        验证 API Key。

        Args:
            db: 数据库会话
            api_key: 明文 API Key

        Returns:
            (Credential, Principal) 如果验证成功，None 如果失败
        """
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()

        result = await db.execute(
            select(Credential)
            .where(Credential.key_hash == key_hash)
            .where(Credential.type == "api_key")
            .where(Credential.status == "active")
        )
        credential = result.scalar_one_or_none()

        if not credential:
            return None

        # 检查过期
        if credential.expires_at and credential.expires_at < datetime.now(timezone.utc):
            return None

        # 获取 Principal
        prinicpal_result = await db.execute(
            select(Principal).where(Principal.id == credential.principal_id)
        )
        principal = prinicpal_result.scalar_one_or_none()

        if not principal or principal.status != "active":
            return None

        # 更新最后使用时间
        credential.last_used_at = datetime.now(timezone.utc)

        return credential, principal

    async def verify_agent_secret(
        self,
        db: AsyncSession,
        agent_secret: str,
    ) -> Optional[tuple[Credential, Principal]]:
        """
        验证 Agent Secret。

        Args:
            db: 数据库会话
            agent_secret: 明文 Agent Secret

        Returns:
            (Credential, Principal) 如果验证成功，None 如果失败
        """
        key_hash = hashlib.sha256(agent_secret.encode()).hexdigest()

        result = await db.execute(
            select(Credential)
            .where(Credential.key_hash == key_hash)
            .where(Credential.type == "agent_secret")
            .where(Credential.status == "active")
        )
        credential = result.scalar_one_or_none()

        if not credential:
            return None

        # 获取 Principal
        principal_result = await db.execute(
            select(Principal).where(Principal.id == credential.principal_id)
        )
        principal = principal_result.scalar_one_or_none()

        if not principal or principal.status != "active":
            return None

        # 更新最后使用时间
        credential.last_used_at = datetime.now(timezone.utc)

        return credential, principal

    async def revoke_credential(
        self,
        db: AsyncSession,
        credential_id: str,
    ) -> bool:
        """
        撤销凭证。

        Args:
            db: 数据库会话
            credential_id: 凭证 ID

        Returns:
            True 如果成功，False 如果凭证不存在
        """
        result = await db.execute(
            select(Credential).where(Credential.id == credential_id)
        )
        credential = result.scalar_one_or_none()

        if not credential:
            return False

        credential.status = "revoked"
        await db.flush()
        return True


# Singleton instance
identity_service = IdentityService()
