from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

class AlertResponse(BaseModel):
    id: str
    title: str
    description: str
    detection_method: str
    rule_name: Optional[str] = None
    anomaly_score: Optional[float] = None
    severity: str
    status: str
    primary_event_id: Optional[str] = None
    affected_entities: List[Dict[str, Any]] = []
    explanation: Optional[str] = None
    investigation_id: Optional[str] = None
    is_demo: bool
    created_at: datetime

    class Config:
        from_attributes = True

class AlertCreate(BaseModel):
    title: str
    description: str
    detection_method: str
    rule_name: Optional[str] = None
    anomaly_score: Optional[float] = None
    severity: str = "MEDIUM"
    primary_event_id: Optional[str] = None
    affected_entities: List[Dict[str, Any]] = []
    explanation: Optional[str] = None
    is_demo: bool = False
