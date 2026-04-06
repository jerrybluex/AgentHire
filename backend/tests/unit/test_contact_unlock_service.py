"""
Contact Unlock Service 单元测试
"""

import pytest
from datetime import datetime, timezone

from app.services.contact_unlock_service import (
    CONTACT_UNLOCK_TRANSITIONS,
    ContactUnlockService,
    InvalidTransitionError,
    ContactUnlockNotFoundError,
)


# ============================================================
# 测试联系方式解锁状态机
# ============================================================
class TestContactUnlockTransitions:
    """测试联系方式解锁状态机"""

    def test_locked_to_candidate_authorized_valid(self):
        """locked 可以转换为 candidate_authorized"""
        assert "candidate_authorized" in CONTACT_UNLOCK_TRANSITIONS["locked"]

    def test_candidate_authorized_to_unlocked_valid(self):
        """candidate_authorized 可以转换为 unlocked"""
        assert "unlocked" in CONTACT_UNLOCK_TRANSITIONS["candidate_authorized"]

    def test_candidate_authorized_to_revoked_valid(self):
        """candidate_authorized 可以被撤销"""
        assert "revoked" in CONTACT_UNLOCK_TRANSITIONS["candidate_authorized"]

    def test_unlocked_to_revoked_valid(self):
        """unlocked 可以被撤销"""
        assert "revoked" in CONTACT_UNLOCK_TRANSITIONS["unlocked"]

    def test_revoked_is_terminal(self):
        """revoked 是终态"""
        assert CONTACT_UNLOCK_TRANSITIONS["revoked"] == []

    def test_locked_is_not_terminal(self):
        """locked 不是终态"""
        assert len(CONTACT_UNLOCK_TRANSITIONS["locked"]) > 0

    def test_all_states_defined(self):
        """所有状态都在 CONTACT_UNLOCK_TRANSITIONS 中定义"""
        expected_states = ["locked", "candidate_authorized", "unlocked", "revoked"]
        for state in expected_states:
            assert state in CONTACT_UNLOCK_TRANSITIONS, f"State {state} not defined"


# ============================================================
# 测试 Contact Unlock 业务逻辑
# ============================================================
class TestContactUnlockLogic:
    """测试联系方式解锁业务逻辑"""

    @pytest.fixture
    def service(self):
        return ContactUnlockService()

    @pytest.fixture
    async def sample_unlock(self, service, db_session):
        """创建一个解锁请求（locked 状态）"""
        return await service.create_unlock_request(
            db=db_session,
            application_id="app_unlock_test_001",
            requester_type="employer",
            requester_id="emp_test_001",
        )

    @pytest.mark.asyncio
    async def test_create_unlock_request_initial_status_is_locked(self, service, db_session):
        """创建解锁请求时初始状态为 locked"""
        result = await service.create_unlock_request(
            db=db_session,
            application_id="app_unlock_test_002",
            requester_type="employer",
            requester_id="emp_test_002",
        )
        assert result.status == "locked"

    @pytest.mark.asyncio
    async def test_candidate_authorize_transitions_to_candidate_authorized(self, service, db_session):
        """candidate_authorize 后状态变为 candidate_authorized"""
        unlock = await service.create_unlock_request(
            db=db_session,
            application_id="app_unlock_test_003",
            requester_type="employer",
            requester_id="emp_test_003",
        )
        assert unlock.status == "locked"

        updated = await service.candidate_authorize(
            db=db_session,
            unlock_id=unlock.id,
            candidate_id="cand_test_003",
            reason="Interested in position",
        )
        assert updated.status == "candidate_authorized"

    @pytest.mark.asyncio
    async def test_employer_unlock_transitions_to_unlocked(self, service, db_session):
        """employer_unlock 后状态变为 unlocked"""
        unlock = await service.create_unlock_request(
            db=db_session,
            application_id="app_unlock_test_004",
            requester_type="employer",
            requester_id="emp_test_004",
        )
        await service.candidate_authorize(
            db=db_session,
            unlock_id=unlock.id,
            candidate_id="cand_test_004",
        )

        updated = await service.employer_unlock(
            db=db_session,
            unlock_id=unlock.id,
            employer_id="emp_test_004",
        )
        assert updated.status == "unlocked"

    @pytest.mark.asyncio
    async def test_invalid_transition_locked_to_unlocked_raises_error(self, service, db_session):
        """locked 不能直接跳到 unlocked（必须先 candidate_authorize）"""
        unlock = await service.create_unlock_request(
            db=db_session,
            application_id="app_unlock_test_005",
            requester_type="employer",
            requester_id="emp_test_005",
        )
        # locked -> unlocked 是无效转换
        with pytest.raises(InvalidTransitionError):
            await service.employer_unlock(
                db=db_session,
                unlock_id=unlock.id,
                employer_id="emp_test_005",
            )

    @pytest.mark.asyncio
    async def test_revoke_from_unlocked_is_valid(self, service, db_session):
        """从 unlocked 状态撤销是有效的"""
        unlock = await service.create_unlock_request(
            db=db_session,
            application_id="app_unlock_test_006",
            requester_type="employer",
            requester_id="emp_test_006",
        )
        await service.candidate_authorize(
            db=db_session, unlock_id=unlock.id, candidate_id="cand_test_006"
        )
        await service.employer_unlock(
            db=db_session, unlock_id=unlock.id, employer_id="emp_test_006"
        )

        revoked = await service.revoke(
            db=db_session,
            unlock_id=unlock.id,
            revoker_id="cand_test_006",
            reason="Changed my mind",
        )
        assert revoked.status == "revoked"

    @pytest.mark.asyncio
    async def test_revoked_is_terminal_cannot_transition(self, service, db_session):
        """revoked 是终态，不能再转换"""
        unlock = await service.create_unlock_request(
            db=db_session,
            application_id="app_unlock_test_007",
            requester_type="employer",
            requester_id="emp_test_007",
        )
        await service.candidate_authorize(
            db=db_session, unlock_id=unlock.id, candidate_id="cand_test_007"
        )
        await service.employer_unlock(
            db=db_session, unlock_id=unlock.id, employer_id="emp_test_007"
        )
        revoked = await service.revoke(
            db=db_session,
            unlock_id=unlock.id,
            revoker_id="cand_test_007",
        )
        assert revoked.status == "revoked"

        # 再尝试任何转换都应该失败
        with pytest.raises(InvalidTransitionError):
            await service._transition(
                db=db_session,
                unlock_id=unlock.id,
                new_status="unlocked",
                actor_id="emp_test_007",
            )
