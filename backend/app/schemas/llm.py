from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field

class HypothesisSchema(BaseModel):
    id: str = Field(description="Unique identifier, e.g. H1, H2")
    hypothesis: str = Field(description="Forensic hypothesis statement")
    likelihood: Literal["HIGH", "MEDIUM", "LOW"] = Field(default="MEDIUM", description="Assessed likelihood")
    tested: bool = Field(default=True, description="Whether hypothesis was evaluated against telemetry")
    supported: Optional[bool] = Field(default=None, description="Whether telemetry supports the hypothesis")
    rationale: Optional[str] = Field(default=None, description="Forensic explanation of assessment")

class FindingSchema(BaseModel):
    id: str = Field(description="Unique finding identifier, e.g. F1, F2")
    statement: str = Field(description="Forensic observation or deduction statement")
    status: Literal["OBSERVED", "INFERRED"] = Field(
        description="OBSERVED for direct telemetry facts; INFERRED for deductive connections"
    )
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score between 0.0 and 1.0 (inferences <= 0.95)")
    supporting_events: List[str] = Field(
        default_factory=list,
        description="IDs of real telemetry events supporting this finding, e.g. ['EVT-AUTH-101']"
    )
    rationale: str = Field(description="Forensic reasoning connecting the telemetry to this finding")

class AttackReconstructionSchema(BaseModel):
    narrative: str = Field(description="Chronological forensic reconstruction of the attack sequence")
    timeline: List[str] = Field(default_factory=list, description="Ordered event IDs showing progression")
    phases: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Attack progression phases with timestamps and entities"
    )

class ResponseRecommendationSchema(BaseModel):
    action_type: str = Field(
        description="Forensic containment action: ISOLATE_HOST, RESET_CREDENTIALS, BLOCK_IP, TERMINATE_PROCESS"
    )
    target_entity: str = Field(description="Host, user account, IP address, or process target")
    rationale: str = Field(description="Forensic justification for staging this action")
    risk_assessment: str = Field(description="Analysis of potential operational disruption or efficacy")

class MitreObservationSchema(BaseModel):
    technique_id: str = Field(description="MITRE ATT&CK technique ID, e.g. T1110, T1059.001")
    tactic: str = Field(description="MITRE ATT&CK tactic, e.g. Credential Access, Execution")
    name: str = Field(description="Technique name, e.g. Brute Force, PowerShell")
    supporting_events: List[str] = Field(default_factory=list, description="Events demonstrating this technique")
    explanation: str = Field(description="Forensic mapping rationale")

class InvestigationReasoningOutput(BaseModel):
    hypotheses: List[HypothesisSchema] = Field(default_factory=list)
    findings: List[FindingSchema] = Field(default_factory=list)
    missing_evidence: List[str] = Field(default_factory=list)
    attack_reconstruction: AttackReconstructionSchema
    executive_summary: str = Field(description="Concise forensic summary for SOC leadership")
    response_recommendations: List[ResponseRecommendationSchema] = Field(default_factory=list)
    mitre_mappings: List[MitreObservationSchema] = Field(default_factory=list)
    recommended_next_steps: List[str] = Field(default_factory=list)
    sufficiency_reached: bool = Field(default=True, description="Whether available telemetry is forensically sufficient")

# Diagnostic & Connection Test Schemas
class LLMConnectionTestRequest(BaseModel):
    provider: Literal["gemini", "openai"]
    api_key: Optional[str] = None
    model: Optional[str] = None

class LLMConnectionTestResult(BaseModel):
    provider: str
    model: str
    status: Literal["HEALTHY", "UNCONFIGURED", "INVALID_KEY", "MODEL_NOT_FOUND", "QUOTA_EXCEEDED", "CONNECTION_FAILED", "SERVER_BUSY"]
    available: bool
    latency_ms: Optional[float] = None
    message: str
    tested_at: str
