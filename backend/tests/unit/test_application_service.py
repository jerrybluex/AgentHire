"""
Application Service 状态机单元测试
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.services.application_service import (
    VALID_TRANSITIONS,
    ApplicationService,
    InvalidTransitionError,
)


# ============================================================
# 测试状态转换有效性
# ============================================================
class TestApplicationStateTransitions:
    """测试申请状态机"""

    def test_draft_to_submitted_valid(self):
        """draft 可以转换为 submitted"""
        assert "submitted" in VALID_TRANSITIONS["draft"]

    def test_submitted_to_viewed_valid(self):
        """submitted 可以转换为 viewed"""
        assert "viewed" in VALID_TRANSITIONS["submitted"]

    def test_submitted_to_rejected_valid(self):
        """submitted 可以直接转换为 rejected"""
        assert "rejected" in VALID_TRANSITIONS["submitted"]

    def test_viewed_to_shortlisted_valid(self):
        """viewed 可以转换为 shortlisted"""
        assert "shortlisted" in VALID_TRANSITIONS["viewed"]

    def test_viewed_to_interview_requested_valid(self):
        """viewed 可以转换为 interview_requested"""
        assert "interview_requested" in VALID_TRANSITIONS["viewed"]

    def test_shortlisted_to_interview_requested_valid(self):
        """shortlisted 可以转换为 interview_requested"""
        assert "interview_requested" in VALID_TRANSITIONS["shortlisted"]

    def test_interview_scheduled_is_valid_target(self):
        """interview_scheduled 是合法的目标状态"""
        assert "interview_scheduled" in VALID_TRANSITIONS

    def test_rejected_is_terminal(self):
        """rejected 是终态"""
        assert VALID_TRANSITIONS["rejected"] == []

    def test_closed_is_terminal(self):
        """closed 是终态"""
        assert VALID_TRANSITIONS["closed"] == []

    def test_invalid_transition_rejected_to_submitted(self):
        """rejected 不能转换回 submitted"""
        assert "submitted" not in VALID_TRANSITIONS["rejected"]

    def test_invalid_transition_draft_to_viewed(self):
        """draft 不能直接跳到 viewed"""
        assert "viewed" not in VALID_TRANSITIONS["draft"]

    def test_all_states_defined(self):
        """所有状态都在 VALID_TRANSITIONS 中定义"""
        expected_states = [
            "draft", "submitted", "viewed", "shortlisted",
            "interview_requested", "interview_scheduled", "closed", "rejected"
        ]
        for state in expected_states:
            assert state in VALID_TRANSITIONS, f"State {state} not defined"


# ============================================================
# 测试状态转换合法性（业务逻辑验证）
# ============================================================
class TestApplicationTransitionValidation:
    """测试状态转换验证"""

    @pytest.fixture
    def service(self):
        return ApplicationService()

    @pytest.mark.asyncio
    async def test_create_application_initial_status_is_draft(self, service, db_session):
        """创建申请时初始状态为 draft"""
        result = await service.create_application(
            db=db_session,
            profile_id="prof_test_001",
            job_id="job_test_001",
            applicant_principal_id="usr_test_001",
            cover_letter="Test cover letter",
        )
        assert result.status == "draft"

    @pytest.mark.asyncio
    async def test_submit_transitions_to_submitted(self, service, db_session):
        """submit 后状态变为 submitted"""
        app = await service.create_application(
            db=db_session,
            profile_id="prof_test_002",
            job_id="job_test_002",
            applicant_principal_id="usr_test_002",
        )
        assert app.status == "draft"

        updated = await service.submit_application(
            db=db_session,
            application_id=app.id,
            actor_type="agent",
            actor_id="usr_test_002",
        )
        assert updated.status == "submitted"

    @pytest.mark.asyncio
    async def test_invalid_transition_raises_error(self, service, db_session):
        """无效转换应抛出 InvalidTransitionError"""
        app = await service.create_application(
            db=db_session,
            profile_id="prof_test_003",
            job_id="job_test_003",
            applicant_principal_id="usr_test_003",
        )
        # draft -> shortlisted 是无效转换
        with pytest.raises(InvalidTransitionError):
            await service.transition_status(
                db=db_session,
                application_id=app.id,
                new_status="shortlisted",
                actor_type="agent",
                actor_id="usr_test_003",
            )

    @pytest.mark.asyncio
    async def test_valid_transition_draft_to_submitted(self, service, db_session):
        """draft -> submitted 是有效转换"""
        app = await service.create_application(
            db=db_session,
            profile_id="prof_test_004",
            job_id="job_test_004",
            applicant_principal_id="usr_test_004",
        )
        updated = await service.transition_status(
            db=db_session,
            application_id=app.id,
            new_status="submitted",
            actor_type="agent",
            actor_id="usr_test_004",
        )
        assert updated.status == "submitted"

    @pytest.mark.asyncio
    async def test_application_not_found_returns_none(self, service, db_session):
        """申请不存在应返回 None"""
        result = await service.get_application(db=db_session, application_id="app_nonexistent")
        assert result is None
