from typing import Optional, List, Dict, Any
from pydantic import BaseModel

class SystemHealthResponse(BaseModel):
    status: str
    backend_health: str
    database_connected: bool
    detection_engine_status: str
    langgraph_workflow_status: str
    
    # Dual LLM Provider Status
    llm_provider: str # Active mode: "gemini" | "openai" | "auto"
    llm_fallback_provider: str
    llm_model: str
    llm_provider_status: str
    degraded_mode: bool
    live_reasoning_enabled: bool
    deterministic_fallback_allowed: bool
    
    # Individual Provider Metrics (Keys never exposed)
    gemini_configured: bool
    gemini_model: str
    gemini_status: str
    openai_configured: bool
    openai_model: str
    openai_status: str
    
    # Workload Counts
    events_count_live: int
    events_count_demo: int
    alerts_count: int
    investigations_count: int
    environment_mode: str # LIVE | DEMO | HYBRID

class LLMConfigUpdateRequest(BaseModel):
    provider: str # "gemini" | "openai" | "auto"
    fallback_provider: Optional[str] = "openai"
    gemini_model: Optional[str] = None
    gemini_api_key: Optional[str] = None
    openai_model: Optional[str] = None
    openai_api_key: Optional[str] = None
    live_reasoning: Optional[bool] = None
    allow_fallback: Optional[bool] = None
