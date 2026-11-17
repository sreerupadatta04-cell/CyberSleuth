from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

class EvidenceItemResponse(BaseModel):
    id: str
    investigation_id: str
    title: str
    description: Optional[str] = None
    evidence_type: str
    source_event_id: Optional[str] = None
    entity_type: Optional[str] = None
    entity_value: Optional[str] = None
    confidence: float
    category: str
    details: Dict[str, Any] = {}
    is_demo: bool
    created_at: datetime

    class Config:
        from_attributes = True

class GraphNode(BaseModel):
    id: str
    label: str
    node_type: str # user | host | ip | process | alert | event | domain
    category: str = "OBSERVED" # OBSERVED | INFERRED
    details: Dict[str, Any] = {}

class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    relationship_type: str
    relationship_category: str = "OBSERVED" # OBSERVED | INFERRED
    confidence: float = 1.0
    supporting_event_id: Optional[str] = None

class EvidenceGraphResponse(BaseModel):
    investigation_id: str
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    stats: Dict[str, int]
