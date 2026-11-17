from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

class TelemetryEventCreate(BaseModel):
    event_id: Optional[str] = None
    timestamp: Optional[datetime] = None
    event_type: str
    severity: Optional[str] = "INFO"
    user: Optional[str] = None
    host: Optional[str] = None
    source_ip: Optional[str] = None
    destination_ip: Optional[str] = None
    source_port: Optional[int] = None
    destination_port: Optional[int] = None
    protocol: Optional[str] = None
    process_name: Optional[str] = None
    process_path: Optional[str] = None
    parent_process: Optional[str] = None
    command_line: Optional[str] = None
    domain: Optional[str] = None
    hash: Optional[str] = None
    raw_payload: Optional[Dict[str, Any]] = None
    is_demo: Optional[bool] = False

class TelemetryEventResponse(BaseModel):
    id: str
    timestamp: datetime
    event_type: str
    severity: str
    user: Optional[str] = None
    host: Optional[str] = None
    source_ip: Optional[str] = None
    destination_ip: Optional[str] = None
    source_port: Optional[int] = None
    destination_port: Optional[int] = None
    protocol: Optional[str] = None
    process_name: Optional[str] = None
    process_path: Optional[str] = None
    parent_process: Optional[str] = None
    command_line: Optional[str] = None
    domain: Optional[str] = None
    hash: Optional[str] = None
    is_demo: bool
    created_at: datetime

    class Config:
        from_attributes = True

class IngestionResult(BaseModel):
    total_received: int
    valid_count: int
    invalid_count: int
    errors: List[str] = []
    is_demo: bool = False
