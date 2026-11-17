from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

class ResponseActionCreate(BaseModel):
    investigation_id: str
    action_type: str
    target_entity: str
    rationale: str
    risk_assessment: Optional[str] = None
    is_demo: bool = False

class ResponseApprovalRequest(BaseModel):
    decided_by: str = "analyst"
    comments: Optional[str] = None

class ResponseActionResponse(BaseModel):
    id: str
    investigation_id: str
    action_type: str
    target_entity: str
    status: str
    rationale: str
    risk_assessment: Optional[str] = None
    is_simulated: bool
    decided_by: Optional[str] = None
    decision_reason: Optional[str] = None
    decision_timestamp: Optional[datetime] = None
    execution_result: Dict[str, Any] = {}
    execution_log: Optional[str] = None
    is_demo: bool
    created_at: datetime

    class Config:
        from_attributes = True

class ApprovalHistoryResponse(BaseModel):
    id: int
    action_id: str
    investigation_id: str
    action: str
    decided_by: str
    comments: Optional[str] = None
    timestamp: datetime

    class Config:
        from_attributes = True
