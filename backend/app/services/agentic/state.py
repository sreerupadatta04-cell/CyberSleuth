from typing import TypedDict, List, Dict, Any, Optional

class InvestigationState(TypedDict):
    investigation_id: str
    alert_id: str
    is_demo: bool
    current_stage: str
    progress: int
    iteration_count: int
    max_iterations: int
    
    # Context
    alert_data: Dict[str, Any]
    target_entities: List[Dict[str, Any]]
    
    # Evidence & Telemetry
    collected_events: List[Dict[str, Any]]
    evidence_items: List[Dict[str, Any]]
    graph_nodes: List[Dict[str, Any]]
    graph_edges: List[Dict[str, Any]]
    
    # Hypotheses & Validation
    hypotheses: List[Dict[str, Any]]
    findings: List[Dict[str, Any]]
    missing_evidence: List[Dict[str, Any]]
    sufficiency_reached: bool
    
    # Synthesis
    attack_reconstruction: Dict[str, Any]
    mitre_mappings: List[Dict[str, Any]]
    risk_assessment: Dict[str, Any]
    executive_summary: Optional[str]
    response_recommendations: List[Dict[str, Any]]
    
    # Execution Provenance & Dual LLM Failover
    llm_invoked: bool
    llm_provider: Optional[str]
    llm_model: Optional[str]
    degraded_mode: bool
    provider_switches: List[Dict[str, Any]]
    failover_reason: Optional[str]
    status: str
    errors: List[str]
