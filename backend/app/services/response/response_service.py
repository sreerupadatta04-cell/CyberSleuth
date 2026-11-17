import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.models.response import ResponseAction, ApprovalHistory

class ResponseService:
    @staticmethod
    def approve_action(action_id: str, decided_by: str, comments: Optional[str], db: Session) -> ResponseAction:
        action = db.query(ResponseAction).filter(ResponseAction.id == action_id).first()
        if not action:
            raise ValueError(f"Response action {action_id} not found")
        if action.status in ["EXECUTED", "APPROVED", "REJECTED"]:
            raise ValueError(f"Response action {action_id} has already been decided (status: {action.status})")

        action.status = "APPROVED"
        action.decided_by = decided_by
        action.decision_reason = comments
        action.decision_timestamp = datetime.utcnow()

        # Execute simulated response
        exec_log = (
            f"[{datetime.utcnow().isoformat()}] SIMULATION: Authorization granted by {decided_by}.\n"
            f"[{datetime.utcnow().isoformat()}] SIMULATION DISPATCH: Dispatching virtual containment command for '{action.action_type}' on '{action.target_entity}'.\n"
            f"[{datetime.utcnow().isoformat()}] SUCCESS: Simulated containment executed successfully. Target '{action.target_entity}' quarantined in test environment.\n"
            f"NOTE: System is in simulated safety sandbox; no production hardware affected."
        )
        action.status = "EXECUTED"
        action.execution_log = exec_log
        action.execution_result = {
            "simulation": True,
            "success": True,
            "target": action.target_entity,
            "action": action.action_type,
            "timestamp": datetime.utcnow().isoformat()
        }

        # Add to audit history
        audit = ApprovalHistory(
            action_id=action.id,
            investigation_id=action.investigation_id,
            action="APPROVED",
            decided_by=decided_by,
            comments=comments,
            timestamp=datetime.utcnow()
        )
        db.add(audit)
        db.commit()
        db.refresh(action)
        return action

    @staticmethod
    def reject_action(action_id: str, decided_by: str, comments: Optional[str], db: Session) -> ResponseAction:
        action = db.query(ResponseAction).filter(ResponseAction.id == action_id).first()
        if not action:
            raise ValueError(f"Response action {action_id} not found")
        if action.status in ["EXECUTED", "APPROVED", "REJECTED"]:
            raise ValueError(f"Response action {action_id} has already been decided (status: {action.status})")

        action.status = "REJECTED"
        action.decided_by = decided_by
        action.decision_reason = comments
        action.decision_timestamp = datetime.utcnow()
        action.execution_log = f"Action rejected by {decided_by}. Reason: {comments or 'No reason provided'}."

        audit = ApprovalHistory(
            action_id=action.id,
            investigation_id=action.investigation_id,
            action="REJECTED",
            decided_by=decided_by,
            comments=comments,
            timestamp=datetime.utcnow()
        )
        db.add(audit)
        db.commit()
        db.refresh(action)
        return action
