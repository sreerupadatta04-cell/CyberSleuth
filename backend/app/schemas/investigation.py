from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

class FindingItem(BaseModel):
    id: str
    statement: str
    status: str # OBSERVED | INFERRED | UNKNOWN
    confidence: float
    supporting_events: List[str] = []
    rationale: str

class HypothesisItem(BaseModel):
    id: str
    hypothesis: str
    likelihood: str # LOW | MEDIUM | HIGH
    tested: bool = False
    supported: Optional[bool] = None

class MitreMappingItem(BaseModel):
    technique_id: str
    tactic: str
    name: str
    supporting_events: List[str] = []
    explanation: str

class InvestigationStepResponse(BaseModel):
    id: int
    stage_name: str
    status: str
    step_order: int
    details: Dict[str, Any] = {}
    output_summary: Optional[str] = None
    timestamp: datetime

    class Config:
        from_attributes = True

class InvestigationCreate(BaseModel):
    alert_id: str

class InvestigationResponse(BaseModel):
    id: str
    alert_id: str
    status: str
    current_stage: str
    progress: int
    hypotheses: List[Any] = []
    findings: List[Any] = []
    missing_evidence: List[Any] = []
    sufficiency_reached: bool = False
    iteration_count: int = 1
    attack_reconstruction: Dict[str, Any] = {}
    mitre_mappings: List[Any] = []
    risk_assessment: Dict[str, Any] = {}
    executive_summary: Optional[str] = None
    llm_invoked: bool = False
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None
    degraded_mode: bool = False
    is_demo: bool = False
    created_at: datetime
    updated_at: datetime
    steps: List[InvestigationStepResponse] = []

    class Config:
        from_attributes = True

class InvestigationProgressResponse(BaseModel):
    id: str
    status: str
    current_stage: str
    progress: int
    updated_at: datetime
    latest_step: Optional[InvestigationStepResponse] = None
