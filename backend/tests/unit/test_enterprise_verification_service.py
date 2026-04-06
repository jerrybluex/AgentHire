"""
Enterprise Verification Service 单元测试
"""

import pytest
from datetime import datetime, timezone

from app.services.enterprise_verification_service import (
    VERIFICATION_TRANSITIONS,
    EnterpriseVerificationService,
    InvalidVerificationTransitionError,
    VerificationCaseNotFoundError,
)


# ============================================================
# 测试企业审核状态机
# ============================================================
class TestVerificationStateTransitions:
    """测试企业审核状态机"""

    def test_draft_to_submitted_valid(self):
        """draft 可以转换为 submitted"""
        assert "submitted" in VERIFICATION_TRANSITIONS["draft"]

    def test_submitted_to_under_review_valid(self):
        """submitted 可以转换为 under_review"""
        assert "under_review" in VERIFICATION_TRANSITIONS["submitted"]

    def test_submitted_to_rejected_valid(self):
        """submitted 可以直接转换为 rejected"""
        assert "rejected" in VERIFICATION_TRANSITIONS["submitted"]

    def test_under_review_to_approved_valid(self):
        """under_review 可以转换为 approved"""
        assert "approved" in VERIFICATION_TRANSITIONS["under_review"]

    def test_under_review_to_needs_resubmission_valid(self):
        """under_review 可以转换为 needs_resubmission"""
        assert "needs_resubmission" in VERIFICATION_TRANSITIONS["under_review"]

    def test_needs_resubmission_to_submitted_valid(self):
        """needs_resubmission 可以重新提交"""
        assert "submitted" in VERIFICATION_TRANSITIONS["needs_resubmission"]

    def test_approved_to_suspended_valid(self):
        """approved 可以被暂停"""
        assert "suspended" in VERIFICATION_TRANSITIONS["approved"]

    def test_rejected_is_terminal(self):
        """rejected 是终态"""
        assert VERIFICATION_TRANSITIONS["rejected"] == []

    def test_suspended_is_terminal(self):
        """suspended 是终态"""
        assert VERIFICATION_TRANSITIONS["suspended"] == []

    def test_invalid_transition_rejected_to_submitted(self):
        """rejected 不能转换回 submitted"""
        assert "submitted" not in VERIFICATION_TRANSITIONS["rejected"]

    def test_all_states_defined(self):
        """所有状态都在 VERIFICATION_TRANSITIONS 中定义"""
        expected_states = [
            "draft", "submitted", "under_review",
            "needs_resubmission", "approved", "rejected", "suspended"
        ]
        for state in expected_states:
            assert state in VERIFICATION_TRANSITIONS, f"State {state} not defined"


# ============================================================
# 测试企业审核业务逻辑
# ============================================================
class TestEnterpriseVerificationLogic:
    """测试企业审核业务逻辑"""

    @pytest.fixture
    def service(self):
        return EnterpriseVerificationService()

    @pytest.mark.asyncio
    async def test_create_verification_case_initial_status_is_draft(self, service, db_session):
        """创建审核案例时初始状态为 draft"""
        result = await service.create_verification_case(
            db=db_session,
            enterprise_id="ent_test_001",
            submitted_by="usr_test_001",
        )
        assert result.status == "draft"

    @pytest.mark.asyncio
    async def test_submit_for_review_transitions_to_submitted(self, service, db_session):
        """submit_for_review 后状态变为 submitted"""
        case = await service.create_verification_case(
            db=db_session,
            enterprise_id="ent_test_002",
            submitted_by="usr_test_002",
        )
        assert case.status == "draft"

        updated = await service.submit_for_review(
            db=db_session,
            case_id=case.id,
        )
        assert updated.status == "submitted"

    @pytest.mark.asyncio
    async def test_approve_case(self, service, db_session):
        """approve 后状态变为 approved"""
        case = await service.create_verification_case(
            db=db_session,
            enterprise_id="ent_test_003",
            submitted_by="usr_test_003",
        )
        await service.submit_for_review(db=db_session, case_id=case.id)
        await service.start_review(db=db_session, case_id=case.id, reviewer_id="reviewer_001")

        approved = await service.approve(
            db=db_session,
            case_id=case.id,
            reviewer_id="reviewer_001",
            comment="Looks good",
        )
        assert approved.status == "approved"

    @pytest.mark.asyncio
    async def test_invalid_transition_raises_error(self, service, db_session):
        """无效转换应抛出 InvalidVerificationTransitionError"""
        case = await service.create_verification_case(
            db=db_session,
            enterprise_id="ent_test_004",
            submitted_by="usr_test_004",
        )
        # draft -> approved 是无效转换
        with pytest.raises(InvalidVerificationTransitionError):
            await service._transition(
                db=db_session,
                case_id=case.id,
                new_status="approved",
                actor_id="usr_test_004",
            )

    @pytest.mark.asyncio
    async def test_reject_is_terminal(self, service, db_session):
        """rejected 后不能继续转换"""
        case = await service.create_verification_case(
            db=db_session,
            enterprise_id="ent_test_005",
            submitted_by="usr_test_005",
        )
        await service.submit_for_review(db=db_session, case_id=case.id)
        await service.start_review(db=db_session, case_id=case.id, reviewer_id="reviewer_002")

        rejected = await service.reject(
            db=db_session,
            case_id=case.id,
            reviewer_id="reviewer_002",
            reason="Invalid documents",
        )
        assert rejected.status == "rejected"

        # rejected 是终态，再次转换应该失败
        with pytest.raises(InvalidVerificationTransitionError):
            await service._transition(
                db=db_session,
                case_id=case.id,
                new_status="approved",
                actor_id="reviewer_002",
            )
