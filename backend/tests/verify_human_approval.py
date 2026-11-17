import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.database import SessionLocal
from app.models.response import ResponseAction, ApprovalHistory
from app.services.response.response_service import ResponseService

def test_human_approval():
    db = SessionLocal()

    # 1. Create a staged action in PENDING_APPROVAL
    test_act = ResponseAction(
        id="RSP-AUDIT-TEST-01",
        investigation_id="INV-AUDIT-HITL",
        action_type="ISOLATE_HOST",
        target_entity="WS-FIN-09",
        status="PENDING_APPROVAL",
        rationale="Compromised endpoint quarantine",
        is_simulated=True,
        is_demo=True
    )
    db.merge(test_act)
    db.commit()

    # Verify initially PENDING
    act = db.query(ResponseAction).filter(ResponseAction.id == "RSP-AUDIT-TEST-01").first()
    assert act.status == "PENDING_APPROVAL"
    assert act.is_simulated is True
    print("1. Initial state verified: PENDING_APPROVAL, simulated=True")

    # 2. Test Invalid Action ID
    try:
        ResponseService.approve_action("RSP-NON-EXISTENT", "analyst", "test", db)
        assert False, "Expected error on invalid ID"
    except ValueError as e:
        print(f"2. Invalid action ID correctly rejected: {e}")

    # 3. Test Approval
    approved_act = ResponseService.approve_action(
        "RSP-AUDIT-TEST-01",
        decided_by="analyst_bob",
        comments="Approved simulated quarantine following SOC review.",
        db=db
    )
    print(f"3. Action Approved: {approved_act.id} -> {approved_act.status}")
    assert approved_act.status == "EXECUTED"
    assert approved_act.decided_by == "analyst_bob"
    assert approved_act.decision_reason == "Approved simulated quarantine following SOC review."
    assert "SIMULATION" in approved_act.execution_log
    assert approved_act.is_simulated is True

    # 4. Verify Audit History
    audit = db.query(ApprovalHistory).filter(ApprovalHistory.action_id == "RSP-AUDIT-TEST-01").first()
    assert audit is not None
    assert audit.action == "APPROVED"
    assert audit.decided_by == "analyst_bob"
    print(f"4. Audit history verified: Action={audit.action}, Analyst={audit.decided_by}")

    # 5. Test Duplicate Approval Prevention
    try:
        ResponseService.approve_action("RSP-AUDIT-TEST-01", "analyst_bob", "Duplicate try", db)
        assert False, "Expected error on duplicate approval"
    except ValueError as e:
        print(f"5. Duplicate approval blocked: {e}")

    # 6. Test Rejection on a second action
    test_act2 = ResponseAction(
        id="RSP-AUDIT-TEST-02",
        investigation_id="INV-AUDIT-HITL",
        action_type="BLOCK_IP",
        target_entity="10.0.0.1",
        status="PENDING_APPROVAL",
        rationale="Block internal gateway IP",
        is_simulated=True,
        is_demo=True
    )
    db.merge(test_act2)
    db.commit()

    rejected_act = ResponseService.reject_action(
        "RSP-AUDIT-TEST-02",
        decided_by="analyst_alice",
        comments="Rejected: 10.0.0.1 is critical internal gateway.",
        db=db
    )
    print(f"6. Action Rejected: {rejected_act.id} -> {rejected_act.status}")
    assert rejected_act.status == "REJECTED"
    assert rejected_act.decided_by == "analyst_alice"

    # Verify rejection audit
    audit2 = db.query(ApprovalHistory).filter(ApprovalHistory.action_id == "RSP-AUDIT-TEST-02").first()
    assert audit2 is not None
    assert audit2.action == "REJECTED"
    print(f"   Rejection audit recorded: Action={audit2.action}, Analyst={audit2.decided_by}")

    # 7. Test Duplicate Rejection Prevention
    try:
        ResponseService.reject_action("RSP-AUDIT-TEST-02", "analyst_alice", "Duplicate try", db)
        assert False, "Expected error on duplicate rejection"
    except ValueError as e:
        print(f"7. Duplicate rejection blocked: {e}")

    print("Human Approval & Safety Verification: 100% PASSED!")
    db.close()

if __name__ == "__main__":
    test_human_approval()
