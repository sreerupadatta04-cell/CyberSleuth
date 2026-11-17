from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text, JSON
from app.core.database import Base

class TelemetryEvent(Base):
    __tablename__ = "telemetry_events"

    id = Column(String, primary_key=True, index=True) # e.g. EVT-1234
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    event_type = Column(String, index=True, nullable=False) # AUTH_FAILURE, PROCESS_CREATE, etc.
    severity = Column(String, default="INFO", index=True) # INFO, LOW, MEDIUM, HIGH, CRITICAL
    
    # Entities
    user = Column(String, index=True, nullable=True)
    host = Column(String, index=True, nullable=True)
    source_ip = Column(String, index=True, nullable=True)
    destination_ip = Column(String, index=True, nullable=True)
    source_port = Column(Integer, nullable=True)
    destination_port = Column(Integer, nullable=True)
    protocol = Column(String, nullable=True)
    
    # Process / Execution context
    process_name = Column(String, index=True, nullable=True)
    process_path = Column(String, nullable=True)
    parent_process = Column(String, nullable=True)
    command_line = Column(Text, nullable=True)
    domain = Column(String, index=True, nullable=True)
    hash = Column(String, nullable=True)
    
    raw_payload = Column(JSON, nullable=True)
    is_demo = Column(Boolean, default=False, nullable=False, index=True)
    dataset_source = Column(String, default="manual_upload", index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
