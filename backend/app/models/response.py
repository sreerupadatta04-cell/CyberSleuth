from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text, JSON
from app.core.database import Base

class ResponseAction(Base):
    __tablename__ = "response_actions"

    id = Column(String, primary_key=True, index=True) # RSP-XXXX
    investigation_id = Column(String, nullable=False, index=True)
    action_type = Column(String, nullable=False) # ISOLATE_HOST | RESET_CREDENTIALS | BLOCK_IP | TERMINATE_PROCESS | REVOKE_TOKEN
    target_entity = Column(String, nullable=False)
    status = Column(String, default="PROPOSED", index=True) # PROPOSED | PENDING_APPROVAL | APPROVED | REJECTED | EXECUTED | FAILED
    
    rationale = Column(Text, nullable=False)
    risk_assessment = Column(Text, nullable=True)
    is_simulated = Column(Boolean, default=True) # Simulated containment only
    
    decided_by = Column(String, nullable=True)
    decision_reason = Column(Text, nullable=True)
    decision_timestamp = Column(DateTime, nullable=True)
    
    execution_result = Column(JSON, default=dict)
    execution_log = Column(Text, nullable=True)
    
    is_demo = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class ApprovalHistory(Base):
    __tablename__ = "approval_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    action_id = Column(String, nullable=False, index=True)
    investigation_id = Column(String, nullable=False, index=True)
    action = Column(String, nullable=False) # APPROVED | REJECTED
    decided_by = Column(String, nullable=False)
    comments = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
