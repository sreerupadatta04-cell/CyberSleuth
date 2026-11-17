from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class Investigation(Base):
    __tablename__ = "investigations"

    id = Column(String, primary_key=True, index=True) # INV-XXXX
    alert_id = Column(String, nullable=False, index=True)
    status = Column(String, default="INITIALIZING", index=True) # INITIALIZING | IN_PROGRESS | COMPLETED | FAILED | CLOSED
    current_stage = Column(String, default="alert_intake", index=True)
    progress = Column(Integer, default=0) # 0 to 100
    
    # Reasoning & Synthesis
    hypotheses = Column(JSON, default=list)
    findings = Column(JSON, default=list) # List of findings with status: OBSERVED | INFERRED | UNKNOWN
    missing_evidence = Column(JSON, default=list)
    sufficiency_reached = Column(Boolean, default=False)
    iteration_count = Column(Integer, default=1)
    
    # Attack Reconstruction & Mappings
    attack_reconstruction = Column(JSON, default=dict)
    mitre_mappings = Column(JSON, default=list)
    risk_assessment = Column(JSON, default=dict)
    executive_summary = Column(Text, nullable=True)
    
    # Execution Provenance
    llm_invoked = Column(Boolean, default=False)
    llm_provider = Column(String, nullable=True)
    llm_model = Column(String, nullable=True)
    degraded_mode = Column(Boolean, default=False) # True if fallback was used
    
    is_demo = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    steps = relationship("InvestigationStep", back_populates="investigation", cascade="all, delete-orphan")


class InvestigationStep(Base):
    __tablename__ = "investigation_steps"

    id = Column(Integer, primary_key=True, autoincrement=True)
    investigation_id = Column(String, ForeignKey("investigations.id"), nullable=False, index=True)
    stage_name = Column(String, nullable=False, index=True) # e.g. planning, collection, correlation
    status = Column(String, default="RUNNING") # RUNNING | SUCCESS | FAILED
    step_order = Column(Integer, default=0)
    details = Column(JSON, default=dict)
    output_summary = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    investigation = relationship("Investigation", back_populates="steps")
