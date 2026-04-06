"""
Unit tests for Audit Service functionality.
Tests audit logging creation and querying.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime


class TestAuditEventTypes:
    """Tests for audit event type constants."""

    def test_enterprise_event_types_defined(self):
        """Test enterprise event types are defined."""
        from app.models.audit_log import AuditEventType

        assert AuditEventType.ENTERPRISE_APPLIED is not None
        assert AuditEventType.ENTERPRISE_APPROVED is not None
        assert AuditEventType.ENTERPRISE_REJECTED is not None

    def test_api_key_event_types_defined(self):
        """Test API key event types are defined."""
        from app.models.audit_log import AuditEventType

        assert AuditEventType.API_KEY_CREATED is not None
        assert AuditEventType.API_KEY_REVOKED is not None

    def test_agent_event_types_defined(self):
        """Test agent event types are defined."""
        from app.models.audit_log import AuditEventType

        assert AuditEventType.AGENT_REGISTERED is not None
        assert AuditEventType.AGENT_CLAIMED is not None


class TestAuditActorType:
    """Tests for audit actor type constants."""

    def test_actor_types_defined(self):
        """Test all actor types are defined."""
        from app.models.audit_log import AuditActorType

        assert AuditActorType.ENTERPRISE is not None
        assert AuditActorType.AGENT is not None
        assert AuditActorType.USER is not None
        assert AuditActorType.ADMIN is not None
        assert AuditActorType.SYSTEM is not None


class TestAuditAction:
    """Tests for audit action constants."""

    def test_actions_defined(self):
        """Test action constants are defined."""
        from app.models.audit_log import AuditAction

        assert AuditAction.CREATE is not None
        assert AuditAction.UPDATE is not None
        assert AuditAction.DELETE is not None
        assert AuditAction.APPROVE is not None
        assert AuditAction.REJECT is not None


class TestAuditLogModel:
    """Tests for AuditLog model structure."""

    def test_audit_log_has_required_fields(self):
        """Test that AuditLog model has all required fields."""
        from app.models.audit_log import AuditLog

        # Check the class has the expected columns defined
        columns = [c.name for c in AuditLog.__table__.columns]

        assert "id" in columns
        assert "event_type" in columns
        assert "actor_type" in columns
        assert "action" in columns
        assert "actor_id" in columns
        assert "target_type" in columns
        assert "target_id" in columns
        assert "request_id" in columns
        assert "ip_address" in columns
        assert "user_agent" in columns
        assert "changes" in columns
        assert "metadata" in columns
        assert "status" in columns
        assert "error_message" in columns
        assert "created_at" in columns


class TestAuditServiceCreateLog:
    """Tests for AuditService.create_log method."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = AsyncMock()
        db.add = MagicMock()
        db.flush = AsyncMock()
        return db

    @pytest.fixture
    def audit_service(self):
        """Create AuditService instance."""
        from app.services.audit_service import AuditService
        return AuditService()

    @pytest.mark.asyncio
    async def test_create_log_basic(self, audit_service, mock_db):
        """Test basic log creation."""
        log = await audit_service.create_log(
            db=mock_db,
            event_type="test_event",
            actor_type="user",
            action="create",
        )

        assert log is not None
        assert log.event_type == "test_event"
        assert log.actor_type == "user"
        assert log.action == "create"
        mock_db.add.assert_called_once()
        mock_db.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_log_with_all_fields(self, audit_service, mock_db):
        """Test log creation with all fields."""
        log = await audit_service.create_log(
            db=mock_db,
            event_type="enterprise_approved",
            actor_type="admin",
            action="approve",
            actor_id="admin_123",
            target_type="enterprise",
            target_id="ent_456",
            request_id="req_789",
            ip_address="192.168.1.1",
            user_agent="TestClient/1.0",
            resource_type="enterprise",
            resource_id="ent_456",
            changes={"status": {"old": "pending", "new": "approved"}},
            metadata={"verified_by": "admin_123"},
            status="success",
        )

        assert log.actor_id == "admin_123"
        assert log.target_id == "ent_456"
        assert log.request_id == "req_789"
        assert log.ip_address == "192.168.1.1"
        assert log.changes is not None
        assert log.metadata is not None

    @pytest.mark.asyncio
    async def test_create_log_with_error(self, audit_service, mock_db):
        """Test log creation with error status."""
        log = await audit_service.create_log(
            db=mock_db,
            event_type="login_failed",
            actor_type="user",
            action="login",
            actor_id="user_123",
            status="failure",
            error_message="Invalid credentials",
        )

        assert log.status == "failure"
        assert log.error_message == "Invalid credentials"


class TestAuditServiceEnterpriseEvents:
    """Tests for AuditService enterprise event logging."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = AsyncMock()
        db.add = MagicMock()
        db.flush = AsyncMock()
        return db

    @pytest.fixture
    def audit_service(self):
        """Create AuditService instance."""
        from app.services.audit_service import AuditService
        return AuditService()

    @pytest.mark.asyncio
    async def test_log_enterprise_event_approve(self, audit_service, mock_db):
        """Test logging enterprise approval."""
        log = await audit_service.log_enterprise_event(
            db=mock_db,
            action="approve",
            enterprise_id="ent_123",
            actor_id="admin_456",
        )

        assert log.event_type == "enterprise_approved"
        assert log.action == "approve"
        assert log.actor_type == "enterprise"

    @pytest.mark.asyncio
    async def test_log_enterprise_event_reject(self, audit_service, mock_db):
        """Test logging enterprise rejection."""
        log = await audit_service.log_enterprise_event(
            db=mock_db,
            action="reject",
            enterprise_id="ent_123",
            error_message="Invalid documentation",
        )

        assert log.event_type == "enterprise_rejected"
        assert log.status == "failure"


class TestAuditServiceAgentEvents:
    """Tests for AuditService agent event logging."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = AsyncMock()
        db.add = MagicMock()
        db.flush = AsyncMock()
        return db

    @pytest.fixture
    def audit_service(self):
        """Create AuditService instance."""
        from app.services.audit_service import AuditService
        return AuditService()

    @pytest.mark.asyncio
    async def test_log_agent_claim_event(self, audit_service, mock_db):
        """Test logging agent claim event."""
        log = await audit_service.log_agent_claim_event(
            db=mock_db,
            action="verify",
            agent_id="agt_123",
            user_id="usr_456",
        )

        assert log.event_type == "agent_claimed"
        assert log.actor_type == "user"
        assert log.target_id == "agt_123"


class TestAuditServiceApiKeyEvents:
    """Tests for AuditService API key event logging."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = AsyncMock()
        db.add = MagicMock()
        db.flush = AsyncMock()
        return db

    @pytest.fixture
    def audit_service(self):
        """Create AuditService instance."""
        from app.services.audit_service import AuditService
        return AuditService()

    @pytest.mark.asyncio
    async def test_log_api_key_created(self, audit_service, mock_db):
        """Test logging API key creation."""
        log = await audit_service.log_api_key_event(
            db=mock_db,
            action="create",
            api_key_id="key_123",
            enterprise_id="ent_456",
        )

        assert log.event_type == "api_key_created"
        assert log.resource_id == "key_123"

    @pytest.mark.asyncio
    async def test_log_api_key_revoked(self, audit_service, mock_db):
        """Test logging API key revocation."""
        log = await audit_service.log_api_key_event(
            db=mock_db,
            action="revoke",
            api_key_id="key_123",
            enterprise_id="ent_456",
        )

        assert log.event_type == "api_key_revoked"


class TestAuditServiceLoginEvents:
    """Tests for AuditService login event logging."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = AsyncMock()
        db.add = MagicMock()
        db.flush = AsyncMock()
        return db

    @pytest.fixture
    def audit_service(self):
        """Create AuditService instance."""
        from app.services.audit_service import AuditService
        return AuditService()

    @pytest.mark.asyncio
    async def test_log_login_success(self, audit_service, mock_db):
        """Test logging successful login."""
        log = await audit_service.log_login_event(
            db=mock_db,
            actor_type="enterprise",
            actor_id="ent_123",
            success=True,
        )

        assert log.event_type == "login_success"
        assert log.status == "success"

    @pytest.mark.asyncio
    async def test_log_login_failure(self, audit_service, mock_db):
        """Test logging failed login."""
        log = await audit_service.log_login_event(
            db=mock_db,
            actor_type="agent",
            actor_id="agt_123",
            success=False,
            error_message="Invalid credentials",
        )

        assert log.event_type == "login_failed"
        assert log.status == "failure"
        assert log.error_message == "Invalid credentials"


class TestAuditServiceBillingEvents:
    """Tests for AuditService billing event logging."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = AsyncMock()
        db.add = MagicMock()
        db.flush = AsyncMock()
        return db

    @pytest.fixture
    def audit_service(self):
        """Create AuditService instance."""
        from app.services.audit_service import AuditService
        return AuditService()

    @pytest.mark.asyncio
    async def test_log_billing_event(self, audit_service, mock_db):
        """Test logging billing event."""
        log = await audit_service.log_billing_event(
            db=mock_db,
            enterprise_id="ent_123",
            billing_record_id="bil_456",
            usage_type="job_post",
            amount=0.50,
        )

        assert log.event_type == "billing_recorded"
        assert log.actor_type == "system"
        assert log.changes["usage_type"] == "job_post"
        assert log.changes["amount"] == 0.50


class TestAuditServiceQueryLogs:
    """Tests for AuditService query methods."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = AsyncMock()
        return db

    @pytest.fixture
    def audit_service(self):
        """Create AuditService instance."""
        from app.services.audit_service import AuditService
        return AuditService()

    @pytest.mark.asyncio
    async def test_query_logs_by_event_type(self, audit_service, mock_db):
        """Test querying logs by event type."""
        mock_result = MagicMock()
        mock_result.scalar.return_value = 5
        mock_db.execute = AsyncMock(return_value=MagicMock(
            scalar=MagicMock(return_value=5),
            scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))
        ))

        logs, total = await audit_service.query_logs(
            db=mock_db,
            event_type="login_success",
        )

        assert total == 5

    @pytest.mark.asyncio
    async def test_query_logs_by_actor_id(self, audit_service, mock_db):
        """Test querying logs by actor ID."""
        mock_db.execute = AsyncMock(return_value=MagicMock(
            scalar=MagicMock(return_value=3),
            scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))
        ))

        logs, total = await audit_service.query_logs(
            db=mock_db,
            actor_id="ent_123",
        )

        assert total == 3

    @pytest.mark.asyncio
    async def test_query_logs_with_date_range(self, audit_service, mock_db):
        """Test querying logs with date range."""
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 12, 31)

        mock_db.execute = AsyncMock(return_value=MagicMock(
            scalar=MagicMock(return_value=10),
            scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))
        ))

        logs, total = await audit_service.query_logs(
            db=mock_db,
            start_date=start_date,
            end_date=end_date,
        )

        assert total == 10

    @pytest.mark.asyncio
    async def test_query_logs_with_pagination(self, audit_service, mock_db):
        """Test querying logs with limit and offset."""
        mock_db.execute = AsyncMock(return_value=MagicMock(
            scalar=MagicMock(return_value=100),
            scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))
        ))

        logs, total = await audit_service.query_logs(
            db=mock_db,
            limit=10,
            offset=20,
        )

        assert total == 100

    @pytest.mark.asyncio
    async def test_get_enterprise_logs(self, audit_service, mock_db):
        """Test getting logs for a specific enterprise."""
        mock_db.execute = AsyncMock(return_value=MagicMock(
            scalar=MagicMock(return_value=15),
            scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))
        ))

        logs, total = await audit_service.get_enterprise_logs(
            db=mock_db,
            enterprise_id="ent_123",
        )

        assert total == 15

    @pytest.mark.asyncio
    async def test_get_agent_logs(self, audit_service, mock_db):
        """Test getting logs for a specific agent."""
        mock_db.execute = AsyncMock(return_value=MagicMock(
            scalar=MagicMock(return_value=8),
            scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))
        ))

        logs, total = await audit_service.get_agent_logs(
            db=mock_db,
            agent_id="agt_123",
        )

        assert total == 8

    @pytest.mark.asyncio
    async def test_get_user_logs(self, audit_service, mock_db):
        """Test getting logs for a specific user."""
        mock_db.execute = AsyncMock(return_value=MagicMock(
            scalar=MagicMock(return_value=12),
            scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))
        ))

        logs, total = await audit_service.get_user_logs(
            db=mock_db,
            user_id="usr_456",
        )

        assert total == 12


class TestAuditServiceSingleton:
    """Tests for audit service singleton."""

    def test_audit_service_singleton_exists(self):
        """Test that audit_service singleton is available."""
        from app.services.audit_service import audit_service

        assert audit_service is not None

    def test_audit_service_isinstance(self):
        """Test that audit_service is an AuditService instance."""
        from app.services.audit_service import audit_service, AuditService

        assert isinstance(audit_service, AuditService)
