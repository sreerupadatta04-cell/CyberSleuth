from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean, Text, JSON
from app.core.database import Base

class Evidence(Base):
    __tablename__ = "evidence"

    id = Column(String, primary_key=True, index=True) # EVI-XXXX
    investigation_id = Column(String, nullable=False, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    evidence_type = Column(String, nullable=False) # EVENT | ENTITY | ARTIFACT | IOC
    source_event_id = Column(String, nullable=True, index=True)
    
    # Forensic context
    entity_type = Column(String, nullable=True) # user, host, ip, process, file, domain
    entity_value = Column(String, nullable=True)
    confidence = Column(Float, default=1.0) # 0.0 to 1.0
    category = Column(String, default="OBSERVED") # OBSERVED | INFERRED
    details = Column(JSON, default=dict)
    
    is_demo = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class EvidenceRelationship(Base):
    __tablename__ = "evidence_relationships"

    id = Column(Integer, primary_key=True, autoincrement=True)
    investigation_id = Column(String, nullable=False, index=True)
    source_node = Column(String, nullable=False, index=True)
    target_node = Column(String, nullable=False, index=True)
    source_type = Column(String, nullable=False) # user, host, ip, process, alert, event
    target_type = Column(String, nullable=False)
    relationship_type = Column(String, nullable=False) # AUTHENTICATED_TO, SPAWNED_PROCESS, CONNECTED_TO, RESOLVED_DOMAIN, TRIGGERED
    relationship_category = Column(String, default="OBSERVED") # OBSERVED | INFERRED
    confidence = Column(Float, default=1.0)
    supporting_event_id = Column(String, nullable=True)
    details = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
