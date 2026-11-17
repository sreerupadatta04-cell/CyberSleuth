from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, Boolean, Text, JSON
from app.core.database import Base

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(String, primary_key=True, index=True) # ALT-XXXX
    title = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=False)
    detection_method = Column(String, nullable=False, index=True) # RULE_BASED | ISOLATION_FOREST
    rule_name = Column(String, nullable=True, index=True)
    anomaly_score = Column(Float, nullable=True) # Isolation forest score
    severity = Column(String, default="MEDIUM", index=True) # LOW | MEDIUM | HIGH | CRITICAL
    status = Column(String, default="NEW", index=True) # NEW | INVESTIGATING | RESOLVED | FALSE_POSITIVE
    
    primary_event_id = Column(String, nullable=True, index=True)
    affected_entities = Column(JSON, default=list) # e.g. [{"type": "user", "value": "a.martinez"}]
    explanation = Column(Text, nullable=True)
    
    investigation_id = Column(String, nullable=True, index=True)
    is_demo = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
